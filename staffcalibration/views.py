'''

   © 2023 Western Australian Land Information Authority

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

'''
import csv
from math import sqrt
import numpy as np
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.db.models import Case, When, Value, IntegerField, Max, OuterRef, Subquery
from django.db.models import Q
# Import Models
from common_func.validators import try_delete_protected
from calibrationsites.models import (Pillar, 
                                    CalibrationSite)
from rangecalibration.models import BarCodeRangeParam
from .models import (StaffCalibrationRecord, 
                    AdjustedDataModel)
# Import Forms
from staffcalibration.forms import (StaffCalibrationRecordForm, 
                                    StaffCalibrationForm)

################################################################################
# Home View
@method_decorator(login_required(login_url="/accounts/login"), name='dispatch')
class HomeView(generic.ListView, LoginRequiredMixin):
    model = StaffCalibrationRecord
    paginate_by = 25
    template_name = 'staffcalibration/staff_calibration_home.html'

    # ordering = ['--calibration_date']
    def get_queryset(self):
        queryset = StaffCalibrationRecord.objects.all()
        if self.request.user.is_staff:
            queryset = queryset.filter(~Q(inst_staff__staff_type = 'invar'))
        else:
            queryset = queryset.filter(Q(inst_staff__staff_owner = self.request.user.company))
       
        # Annotate the queryset so that staffs can see their records at the top
        queryset = queryset.annotate(
            is_top=Case(
                When(inst_staff__staff_owner = self.request.user.company, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        # Order by 'is_top' (descending) and then by 'date' (descending)
        queryset = queryset.order_by('-is_top', '-calibration_date')
        return queryset

@login_required(login_url="/accounts/login")
def user_staff_registry(request):
    queryset_refs = StaffCalibrationRecord.objects.none()
    if request.user.is_staff:
        # all staffs excluding reference staves
        queryset = StaffCalibrationRecord.objects.filter(~Q(inst_staff__staff_type = 'invar'))
        queryset = queryset.annotate(
            is_top=Case(
                When(inst_staff__staff_owner = request.user.company, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        queryset = queryset.order_by('-is_top', '-calibration_date')
        # only reference staves
        queryset_refs = StaffCalibrationRecord.objects.filter(Q(inst_staff__staff_type = 'invar'))
    else:
        queryset = StaffCalibrationRecord.objects.filter(inst_staff__staff_owner = request.user.company)
    
    subQuery = queryset.filter(inst_staff = OuterRef('inst_staff')).order_by('-calibration_date').values('calibration_date')[:1]
    queryset = queryset.filter(calibration_date = Subquery(subQuery)) #(latest_date=Max('calibration_date')).filter(calibration_date=F('latest_date')).order_by('inst_staff__number')
    
    subQueryRef = queryset_refs.filter(inst_staff = OuterRef('inst_staff')).order_by('-calibration_date').values('calibration_date')[:1]
    queryset_refs = queryset_refs.filter(calibration_date = Subquery(subQueryRef)) #(latest_date=Max('calibration_date')).filter(calibration_date=F('latest_date')).order_by('inst_staff__number')
    context = {
        'queryset': queryset,
        'queryset_refs': queryset_refs,
    }
    return render(request, 'staffcalibration/staff_calibration_record.html', context)
################################################################################    
def create_record(request):
    if request.method=="POST":
        form = StaffCalibrationRecordForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()

            return redirect('staffcalibration:staff_registry')#redirect('blog:post_detail', pk= post.pk)
    else:
        form = StaffCalibrationRecordForm(user=request.user)
    return render(request, 'staffcalibration/staff_calibration_record_form.html', {'form':form})
################################################################################
############################## STAFF FILE READING ##############################
################################################################################
# Handle Data
def reading_data(csv_file):
    message = ''
    data = []

    csv_file = csv_file.read().decode('utf-8').splitlines()
    reader = csv.reader(csv_file)
    #loop over the lines and save them in db. If error , store as string and then display
    for row in reader:                    
        if row[0].isdigit():
            data.append(row)
        else: 
            continue
    return data, message

# Preprocess staff readings to calculate the height differences between pins
def preprocess_reading(dataset):
    obs_set = []
    for i in range(len(dataset)-1):
        pini, obsi, nmeasi, stdi = dataset[i] 
        pinj, obsj, nmeasj, stdj = dataset[i+1]
        if float(stdi) == 0:
            stdi = 10**-5
        if float(stdj) == 0:
            stdj = 10**-5
        dMeasuredLength = float(obsj)- float(obsi)
        dStdDeviation = sqrt(float(stdi)**2 + float(stdj)**2)
        obs_set.append([str(pini)+'-'+str(pinj), 
                            '{:.5f}'.format(float(obsi)), '{:.5f}'.format(float(obsj)), 
                            '{:.5f}'.format(dMeasuredLength), 
                            '{:.7f}'.format(dStdDeviation)])
    return np.array(obs_set, dtype=object)
###############################################################################
######################### STAFF ERRORS REPORT #################################
###############################################################################
def staff_errors_at_regular_intervals(calib_id):
    '''
        staff_reading: adjusted staff reading stored in the Adj Model 
    '''
    thisAdj = AdjustedDataModel.objects.get(calibration_id = calib_id)
    # Get the staff readings
    staff_reading = np.array([value for value in thisAdj.staff_reading.values()], dtype=object).T
    # Convert to floats where applicable - col 2 to end
    staff_reading[:,1:] = [[float(x) for x in y] for y in staff_reading[:,1:]]
    
    # Get Staff Length from data
    dStaffLength = round(float(staff_reading[:,2][-1]), 1)
    # Prepare Interval
    dFrom = 0.1; dTo = 0.2; 
    dInterval = dTo- dFrom

    fromToInterval = []
    while dTo < dStaffLength:
        try:
            tmp = staff_reading[(staff_reading[:,1] <= dTo) & (staff_reading[:,2] >= dFrom)]
            dValue = 0
            if len(tmp) > 1:
                dSumValue = 0
                dSumWeight = 0
                for i in range(len(tmp)):
                    dMeasuredInterval = tmp[i][2] - tmp[i][1] 
                    dValue = dInterval/dMeasuredInterval * (tmp[i][3]-tmp[i][4])
            
                    dTop = 0
                    dBottom = 0
                    
                    dTop = tmp[i][2] - dTo
                    dBottom =dFrom - tmp[i][1]
                    
                    dInsideInterval = dMeasuredInterval - dTop - dBottom
                    dWeight = (dInsideInterval*dInsideInterval)/(dMeasuredInterval*dInterval);
                    
                    dSumValue = dSumValue + dValue*dWeight;
                    dSumWeight = dSumWeight+dWeight;
                dValue = dSumValue/dSumWeight    
                
            else:
                dMeasuredInterval = tmp[0][2] - tmp[0][1] 
                dValue = dInterval/dMeasuredInterval * (tmp[0][3]-tmp[0][4])
            fromToInterval.append(['{:3.2f}'.format(dFrom), '{:3.2f}'.format(dTo), '{:3.2f}'.format((dFrom+dTo)/2), '{:4.2f}'.format(dValue * 1000), '{:7.5f}'.format(dInterval + dValue,5)])
        except Exception:
            pass
        
        dFrom = round(dFrom + dInterval,1)
        dTo = round(dTo + dInterval,1)    
    return np.array(fromToInterval, dtype=float)

# Generate graph
def save_render_figure(staff_interval, tmp_sf1, calib_id):
    # Import libraries
    from io import BytesIO
    import matplotlib.pyplot as plt
    from matplotlib.ticker import AutoMinorLocator, MultipleLocator, FormatStrFormatter
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    if not calib_id.calibration_error:
        # Plot figure
        buffer = BytesIO()
        xs = staff_interval[:,0:2].mean(axis=1)
        ys = staff_interval[:,3]
        fig, ax = plt.subplots(figsize=(15,5))
        ax.bar(xs, ys, label=xs, width=0.1, color='#DB1111', edgecolor = 'black')
        ax.set_ylabel('Staff Errors (mm)')
        ax.set_xlabel('Staff Length (m)')
        ax.set_title('Staff Errors at ' + '{:3.1f}'.format(tmp_sf1) + '$^\circ$C', fontsize=14)     
        ax.set_xlim(0, xs[-1] + 0.5)
        ax.set_ylim(-0.1, 0.1)
        ax.grid(color='green', linestyle = '--', linewidth = 0.3)
        # Axis Locator
        ax.xaxis.set_minor_locator(MultipleLocator(0.1))
        ax.yaxis.set_major_formatter(FormatStrFormatter('% 1.2f'))
        fig.savefig(buffer, bbox_inches='tight', format='svg', dpi=300)
        buffer.seek(0)
        image_file = SimpleUploadedFile('StaffError', buffer.read(), content_type = 'image/svg+xml')
        # Save the figure to model
        calib_id.calibration_error = image_file
        # calib_id.calibration_error.content_type = 'image/svg+xml'
        calib_id.save()
###############################################################################
######################### STAFF CALIBRATION ###################################
###############################################################################
# Calculate the correction factor
def compute_correction_factor(newdataset, refdataset, coef, ave_temp, std_temp):

    W = np.zeros([len(newdataset[:,0])])
    W_corr = np.zeros([len(newdataset[:,0])])
    A = np.ones([len(newdataset[:,0])])
    sum_sq_diff = np.zeros([len(newdataset[:,0])])
    variance = np.zeros([len(newdataset[:,0])])
    
    adj_correction = []
    for i in range (len(newdataset)):
        pin, frm, to, diff, std = newdataset[i]
        diff = float(diff)
        ref_diff = float(refdataset[i,1])

        corr_diff = diff * (((ave_temp-std_temp)*coef)+1) # correction at standard temperature
        corr = ref_diff - corr_diff

        # Append array
        sum_sq_diff[i,] = corr**2
        variance[i,] = float(std)

        W[i,] = ref_diff/diff                   # Uncorrected
        W_corr[i,] = ref_diff/corr_diff         # Corrected for temp

        adj_correction.append([pin, frm, to, '{:.5f}'.format(ref_diff), '{:.5f}'.format(diff),'{:.5f}'.format(corr)])
    # Compute Lease Squares Solution
    P = np.diag(1/variance**2)
    sf_0 = (np.matmul(np.transpose(A), np.matmul(P, W)))/(np.matmul(np.transpose(A), np.matmul(P, A)))
    sf_1 = (np.matmul(np.transpose(A), np.matmul(P, W_corr)))/(np.matmul(np.transpose(A), np.matmul(P, A))) # at 25degC
    
    grad_uncertainty = sqrt(np.sum(sum_sq_diff)/(len(W)-1))*1.96

    adj_correction = {'headers': ['PIN','FROM','TO', 'REFERENCE', 'MEASURED', 'CORRECTIONS'], 
                        'data': adj_correction}
    return round(sf_0,8), round(sf_1,7), round(grad_uncertainty,5), adj_correction

# Generate scale factors for various temperatures
def compute_factor_corrections(coef, ave_temp, sf_0):
    start_temp = 0.
    end_temp = 50.
    interval = 2.
    listOfScaleFactors = []
    while start_temp <= end_temp:
        scale_factor = (((start_temp-ave_temp)*coef)+1)*sf_0
        correction = (scale_factor-1)*1000.
        listOfScaleFactors.append([str(int(start_temp)), '{:.7f}'.format(scale_factor), '{:.2f}'.format(correction)])
        
        start_temp += interval

    return {'headers': ['Temperature','Correction Factor','Correction/metre [mm]'], 
                            'data':listOfScaleFactors}  

@login_required(login_url="/accounts/login")
def calibrate(request):
    if request.method=="POST":
        form = StaffCalibrationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save(commit=False)
            data = form.cleaned_data
            
            # Metadata
            site_id = data['site_id']
            job_number = data['job_number']
            staff_number = data['inst_staff']
            level_number = data['inst_level']
            isObserver = data['observer_isme']
            # Get the observer
            if isObserver:
                field_person = request.user
                if field_person.first_name:
                    observer = field_person.first_name +' '+ field_person.last_name
                else:
                    observer = field_person.email
            else:
                observer = data['observer']

            # temperature
            average_temperature = (float(data['start_temperature']) + float(data['end_temperature']))/2
            standard_temperature = 25.0

            # Thermal Coefficient
            thermal_coefficient = staff_number.thermal_coefficient * 10**-6
            
            # observation date
            calibration_date = data['calibration_date']
            [mon_text, mon_number] = [calibration_date.strftime('%b'), calibration_date.month]

            # Field files
            field_book = data['field_book']
            field_file = data['field_file']
            
            # Read data and start computing
            staff_reading, message = reading_data(field_file)
            if len(staff_reading) > 0:
                # Get the reference data from BarCodeRangeParam
                if BarCodeRangeParam.objects.filter(site_id = site_id).exists():
                    # Check Pin Numbers
                    site_instance = CalibrationSite.objects.get(site_name = site_id.site_name)
                    numberOfPins = site_instance.no_of_pillars
                    pin_numbers = Pillar.objects.filter(site_id = site_id).values_list('name')
                    pin_numbers = [x[0] for x in pin_numbers]
                    pinList = sorted(pin_numbers, key=int)
                    # Get reference dataset
                    range_param = BarCodeRangeParam.objects.filter(site_id = site_id).values_list('from_to', mon_text)[0] # pin_from_to = range_param[0]['from_to']
                    if range_param[1]:
                        data_ref = np.array([range_param[0]['from_to'], range_param[1]['mean']], dtype=object).T   # [Pin Diff]
                        
                        # Staff reading 
                        staff_reading = np.array(staff_reading, dtype=object)
                        data_new = preprocess_reading(staff_reading)                               # An array
                        # checking for missing/new pins
                        missingPins = np.setdiff1d(data_ref[:,0], data_new[:,0]) # find any pin ranges that are not in the reference data
                        newPins = np.setdiff1d(data_new[:,0], data_ref[:,0])
                        # print(missingPins)
                        # print(newPins)
                        if len(missingPins)>0 or len(newPins)>0:
                            # Get the indices of common data point
                            common_pins, data_ind, ref_ind = np.intersect1d(data_new[:,0], data_ref[:,0], return_indices=True)
                            data_new = data_new[np.sort(data_ind), :]                            # Extract & sort data
                            data_ref = data_ref[np.sort(data_ind),:]                              # Extract & sort reference 

                            scaleFactor0, scaleFactor1, grad_uncertainty, diff_correction = compute_correction_factor(data_new, 
                                                                                            data_ref, 
                                                                                            thermal_coefficient, 
                                                                                            average_temperature,
                                                                                            standard_temperature)
                            # check 
                            # if round((((standard_temperature-average_temperature)*coeff)+1)*scaleFactor0,7) == scaleFactor1:
                            #     print("Well Done")
                            messages.warning(request, mark_safe('1. Your data contains unverified pin numbers: '+ ' '.join(newPins) + ' <br> 2. Missing pin numbers in your data: '+ ' '.join(missingPins)))
                        else: 
                            scaleFactor0, scaleFactor1, grad_uncertainty, diff_correction = compute_correction_factor(data_new, 
                                                                                            data_ref, 
                                                                                            thermal_coefficient, 
                                                                                            average_temperature,
                                                                                            standard_temperature)
                            # check 
                            # if round((((standard_temperature-average_temperature)*coeff*10**-6)+1)*scaleFactor0,7) == scaleFactor1:
                            #     print("Well Done")
                            messages.success(request, 'Congratulations! You have successfully calibrated your staff.') 
                        # List of scale factors at various tempertaures
                        temp_correction_factors = compute_factor_corrections(thermal_coefficient, average_temperature, scaleFactor0) 
                        # Temperature at which scale factor is 1 
                        temp_at_sf1 = ((1/scaleFactor0)-1)/(thermal_coefficient)+average_temperature
                        # reformat adjusted data
                        data_adj = np.array(diff_correction['data'], dtype=object)
                        # Update Calibration Record
                        thisRecord, created = StaffCalibrationRecord.objects.update_or_create(
                                                                    job_number = job_number,
                                                                    site_id = site_id,
                                                                    inst_staff = staff_number,
                                                                    inst_level = level_number,
                                                                    scale_factor = scaleFactor1,
                                                                    grad_uncertainty = grad_uncertainty,
                                                                    observed_temperature = average_temperature,
                                                                    observer = observer,
                                                                    calibration_date = calibration_date, 
                                                                    field_book = field_book,
                                                                    field_file = field_file
                                                                )
                        # Update Adjustment Record
                        thisAdj, created = AdjustedDataModel.objects.update_or_create(
                            calibration_id = thisRecord,
                            uscale_factor = scaleFactor0,
                            temp_at_sf1 = temp_at_sf1,
                            staff_reading = {
                                        'pin': data_adj[:,0].tolist(),
                                        'from': data_adj[:,1].tolist(),
                                        'to': data_adj[:,2].tolist(),
                                        'reference': data_adj[:,3].tolist(),
                                        'measured': data_adj[:,4].tolist(),
                                        'correction': data_adj[:,5].tolist(),
                            }
                        )
                        # Calculate Staff Errors
                        staff_errors_intervals = staff_errors_at_regular_intervals(thisRecord)
                        save_render_figure(staff_errors_intervals, temp_at_sf1, thisRecord)
                        staff_errors_intervals = {'headers': ['FROM','TO', 'LENGHT', 'ERROR', 'CORRECTED_INTERVAL'], 
                                        'data': staff_errors_intervals}
                        context = {
                            'calibration': thisRecord,
                            'calib_adj': thisAdj,
                            'diff_correction': diff_correction,
                            'temp_correction_factors':temp_correction_factors,
                            'staff_errors_intervals': staff_errors_intervals,
                        }
                            
                        return render(request, 'staffcalibration/staff_calibration_report.html', context)
                    else:
                        messages.warning(request, 'The range parameter for the month of '+ mon_text + ' does not exist. Please contact Landgate')    
                        return redirect('staffcalibration:calibrate')
                else:
                    messages.warning(request, 'The calibration site - ' + site_id.site_name + ' does not exist. Please contact the site operator to add it.' )    
                    return redirect('staffcalibration:calibrate')
            else:
                messages.warning(request, 'Opps! Looks like you data is invalid. Please format your data as per the guidelines.' )    
                return redirect('staffcalibration:calibrate')
    else:
        form = StaffCalibrationForm(user=request.user)
    return render(request, 'staffcalibration/staff_calibration_form.html', {'form':form})
###############################################################################
########################## VIEW REPORT ########################################
###############################################################################
@login_required(login_url="/accounts/login")
def view_report(request, id):
    # Calibration ID
    thisRecord = StaffCalibrationRecord.objects.get(id=id)
    
    # Print the report using the adjusted data, if it exists, else print loaded pdf
    if AdjustedDataModel.objects.filter(calibration_id=thisRecord).exists():
    # try:
        thisAdj = AdjustedDataModel.objects.get(calibration_id=thisRecord)
        average_temperature = thisRecord.observed_temperature
        thermal_coefficient = thisRecord.inst_staff.thermal_coefficient*10**-6

        pin_from_to = thisAdj.staff_reading['pin']
        from_reading = thisAdj.staff_reading['from']
        to_reading = thisAdj.staff_reading['to']
        known_length = thisAdj.staff_reading['reference']
        measured_length = thisAdj.staff_reading['measured']
        correction = thisAdj.staff_reading['correction']

        diff_correction = np.array([pin_from_to, from_reading, to_reading, known_length, measured_length, correction], dtype=object).T
        diff_correction = {'headers': ['PIN','FROM','TO', 'REFERENCE', 'MEASURED', 'CORRECTIONS'], 
                        'data': diff_correction}
        # Temperature Corrections
        scaleFactor0 = thisAdj.uscale_factor
        temp_correction_factors = compute_factor_corrections(thermal_coefficient, average_temperature, scaleFactor0) 
        # Staff Errors
        staff_errors_intervals = staff_errors_at_regular_intervals(thisRecord)
        save_render_figure(staff_errors_intervals, thisAdj.temp_at_sf1, thisRecord)
        staff_errors_intervals = {'headers': ['FROM','TO', 'LENGHT', 'ERROR', 'CORRECTED_INTERVAL'], 
                        'data': staff_errors_intervals}
        # Build Context
        context = {
                'calibration': thisRecord,
                'calib_adj': thisAdj,
                'diff_correction': diff_correction,
                'temp_correction_factors':temp_correction_factors,
                'staff_errors_intervals': staff_errors_intervals,
        }
        return render(request, 'staffcalibration/staff_calibration_report.html', context)
###############################################################################
######################### PRINT REPORT ########################################
###############################################################################
from django_xhtml2pdf.utils import generate_pdf
# from django.utils.path import join 
import os
@login_required(login_url="/accounts/login")
def print_report(request, id):
    resp = HttpResponse(content_type='application/pdf')
    
    # Calibration ID
    thisRecord = StaffCalibrationRecord.objects.get(id=id)
    
    # Print the report using the adjusted data, if it exists, else print loaded pdf
    if AdjustedDataModel.objects.filter(calibration_id=thisRecord).exists():
    # try:
        thisAdj = AdjustedDataModel.objects.get(calibration_id=thisRecord)
        average_temperature = thisRecord.observed_temperature
        thermal_coefficient = thisRecord.inst_staff.thermal_coefficient*10**-6

        pin_from_to = thisAdj.staff_reading['pin']
        from_reading = thisAdj.staff_reading['from']
        to_reading = thisAdj.staff_reading['to']
        known_length = thisAdj.staff_reading['reference']
        measured_length = thisAdj.staff_reading['measured']
        correction = thisAdj.staff_reading['correction']

        adj_correction = np.array([pin_from_to, from_reading, to_reading, known_length, measured_length, correction], dtype=object).T
        adj_correction = {'headers': ['PIN','FROM','TO', 'REFERENCE', 'MEASURED', 'CORRECTIONS'], 
                        'data': adj_correction}
        # Temperature Corrections
        scaleFactor0 = thisAdj.uscale_factor
        temp_correction_factors = compute_factor_corrections(thermal_coefficient, average_temperature, scaleFactor0) 
        # Staff Errors
        staff_errors_intervals = staff_errors_at_regular_intervals(thisRecord)
        save_render_figure(staff_errors_intervals, thisAdj.temp_at_sf1, thisRecord)
        staff_errors_intervals = {'headers': ['FROM','TO', 'LENGHT', 'ERROR', 'CORRECTED_INTERVAL'], 
                        'data': staff_errors_intervals}
        
        # Prepare the context to be rendered
        context = {
                'calibration': thisRecord,
                'calib_adj': thisAdj,
                'adj_correction': adj_correction,
                'temp_correction_factors':temp_correction_factors,
                'staff_errors_intervals': staff_errors_intervals,
        }
        result = generate_pdf('staffcalibration/pdf_staff_report.html', file_object=resp, context=context)
        return result 
###############################################################################
######################### DELETE RECORD #######################################
###############################################################################
def delete_record(request, id):
    thisRecord = StaffCalibrationRecord.objects.get(id=id)
    try_delete_protected(request, thisRecord)

    # current_page_url = request.build_absolute_uri()
    previous_page_url = request.META.get('HTTP_REFERER')
    # return redirect('staffcalibration:home')
    return redirect(previous_page_url)
###############################################################################