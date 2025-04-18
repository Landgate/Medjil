'''

   © 2025 Western Australian Land Information Authority

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
import os
from datetime import datetime
import pandas as pd
import numpy as np
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views import generic
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from formtools.wizard.views import SessionWizardView

# models
from staffcalibration.models import StaffCalibrationRecord
from .models import (RangeCalibrationRecord, 
                    RawDataModel, 
                    AdjustedDataModel, 
                    HeightDifferenceModel, 
                    BarCodeRangeParam,
                    )
from calibrationsites.models import (Pillar, 
                                    CalibrationSite)
# forms
from .forms import RangeParamForm

# functions
from .signals import (update_range_table_current, 
                      update_range_table, 
                      compute_range_site, 
                      compute_range_parameters
                    )


# Home View
class HomeView(SuccessMessageMixin, generic.ListView):
    model = RangeCalibrationRecord
    paginate_by = 25
    template_name = 'rangecalibration/range_calibration_home.html'

    ordering = ['-calibration_date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Retrieve additional queryset for calibration records not updated to Range Param
        try:
            if not BarCodeRangeParam.objects.first():
                compute_range_parameters()
                context['update_param_yes'] = True
            elif RangeCalibrationRecord.objects.filter(valid=True, updated_to = False).first():
                context['update_param_yes'] = True
                compute_range_parameters()
            success_message  =  'Range table successfully updated!'
        except:
            context['update_param_yes'] = False
        # print(context)
        return context
###############################################################################
########################## FILE HANDLING ######################################
###############################################################################
def IsNumber(value):
    "Checks if string is a number"
    try:
        float(value)
        check = True
    except:
        check = False
    return(check)

# Check file type and read the measurements
def check_filetype(dataset):
    readings = dataset.read().decode("utf-8").split("\n")
    fileType = None
    for line in readings:
        # print(line)
        if "BFOD" in line:
            fileType = "BFOD"
        elif "Level Type" in line:
            fileType = "DNA03"
            break

    # return fileType
    if fileType == "BFOD":
        return ImportBFOD_v18(readings)
    elif fileType == "DNA03":
        return ImportDNA(readings)

# File Format produced by LS15
def ImportBFOD_v18(raw_data):
    # Initialise array
    Blocks = []; block = []
    # Read data
    for line in raw_data:# f:
        line = line.strip()
        col = line.split('|')[1:]
        
        # Start level run 
        if line.startswith('|---------|---------|---------|---------|------------'):
            if block:
                Blocks.append(block)
                block = []
        elif len(col) == 11:
            block.append(col)
    if block:
        Blocks.append(block)  
    #----------------------------------------------------------------------
    # Finally store the staff readings into a table/list format and store    
    readings = {}
    j = 0
    for i in range(len(Blocks)):
        block = Blocks[i]
        if len(block)>7:
            j += 1
            tmp = []
            for r in block:
                r = [x.strip() for x in r]
                if (IsNumber(r[0]) or IsNumber(r[1]) or IsNumber(r[2])):
                    if IsNumber(r[0]):
                        pillar = r[8]; reading = r[0]; nreadings = r[6]; stdev = r[7]; 
                    elif IsNumber(r[1]):
                        pillar = r[8]; reading = r[1]; nreadings = r[6]; stdev = r[7]; 
                    elif IsNumber(r[2]):
                        pillar = r[8]; reading = r[2]; nreadings = r[6]; stdev = r[7]; 
                    tmp.append([pillar, float(reading), nreadings, float(stdev)])
            tmp  = pd.DataFrame(tmp, columns=['PILLAR','READING','COUNT','STD_DEVIATION'])
            # Update dictionary
            readings.update({'Set'+str(j):tmp})
    return readings

# File Format produced by DNA03
def ImportDNA(raw_data):
    # Initialise array
    Blocks = []; block = []
    # Read data
    for line in raw_data:
        line = line.strip()
        # print(line)
        col = line.split('|')[1:]
        # Start level run 
        if line.endswith('| MS |___DEV__|___________|'):
            if block:
                Blocks.append(block)
                block = []
        elif len(col) == 10:
            block.append(col)
    if block:
        Blocks.append(block)      
    #----------------------------------------------------------------------
    # Finally store the staff readings into a table/list format and store
    readings = {}
    j = 0
    for i in range(len(Blocks)):
        block = Blocks[i]
        if len(block)>7:
            j += 1
            # Append items
            pillar = []; reading = []; stdev = []; nreadings = None
            tmp = []
            for r in block:
                r = [x.strip() for x in r]
                
                if (IsNumber(r[0]) or IsNumber(r[1]) or IsNumber(r[2])):
                    if IsNumber(r[0]):
                        pillar = r[8]; reading = r[0]; stdev = r[7]; nreadings = r[6]
                    elif IsNumber(r[1]):
                        pillar = r[8]; reading = r[1]; stdev = r[7];
                    elif IsNumber(r[2]):
                        pillar = r[8]; reading = r[2]; stdev = r[7];
                    
                    tmp.append([pillar, float(reading), nreadings, float(stdev)])
            tmp  = pd.DataFrame(tmp, columns=['PILLAR','READING','COUNT','STD_DEVIATION'])
            readings.update({'Set'+str(j):tmp})
    return readings

# Apply Corrections to staff Readings
def calculate_length(dato, sf, coe, t_0, t_ave, oset):
    from math import sqrt

    data_table = []
    pillarlist = []
    for i in range(len(dato)-1):
        pillari, obsi, nmeasi, stdi= dato[i] 
        pillarj, obsj, nmeasj, stdj = dato[i+1]
        if stdi == 0:
            stdi = 10**-5
        if stdj == 0:
            stdj = 10**-5
        dMeasuredLength = obsj- obsi
        dCorrection = (sf)*(1+coe*(float(t_ave)-t_0))
        cMeasuredLength = dMeasuredLength*dCorrection
        dStdDeviation = sqrt(float(stdi)**2 + float(stdj)**2)
        data_table.append([str(oset), pillari+'-'+pillarj, '{:.1f}'.format(float(t_ave)),
                                    '{:.5f}'.format(obsi), '{:.5f}'.format(obsj), '{:.6f}'.format(dStdDeviation),
                                    '{:.5f}'.format(dMeasuredLength), '{:.5f}'.format(cMeasuredLength)])
        if not pillari in pillarlist:
            pillarlist.append(pillari)
        if not pillarj in pillarlist:
            pillarlist.append(pillarj)
    return pillarlist, data_table

# Dictionary to table format - staff readings
def rawdata_to_table(dataset, t_avg1, t_avg2, staff_atrs):
    dCorrectionFactor = staff_atrs['dCorrectionFactor']
    dThermalCoefficient = staff_atrs['dThermalCoefficient']
    dStdTemperature = staff_atrs['dStdTemperature']
    rawReportTable = []
    uniquePillarList = []
    for key, value in dataset.items():
        if key.startswith("Set1"):
            obs_set = 1
            pillar_list1, dataset1 = calculate_length(value.values, dCorrectionFactor, dThermalCoefficient, dStdTemperature, t_avg1, obs_set)
        elif key.startswith("Set2"):
            obs_set = 2
            pillar_list2, dataset2 = calculate_length(value.values, dCorrectionFactor, dThermalCoefficient, dStdTemperature, t_avg2, obs_set)

    rawReportTable = {'headers': ['SET','PILLAR','TEMPERATURE','FROM','TO', 'STD_DEVIATION', 'MEASURED', 'CORRECTED'], 'data': dataset1+dataset2}
    
    # Get the list of pins/pillars
    pillar_list2 = pillar_list1 + pillar_list2
    for pillars in pillar_list2:
        if not pillars in uniquePillarList:
            uniquePillarList.append(pillars)

    return uniquePillarList, rawReportTable
###############################################################################
######################### SessionWizardView ###################################
###############################################################################
TEMPLATES  = {"prefill_form": "rangecalibration/range_calibration_form_1.html",
             "upload_data": "rangecalibration/range_calibration_form_2.html",
             }

class RangeCalibrationWizard(LoginRequiredMixin, SessionWizardView):
    # get the template names and their steps
    def get_template_names(self):                
        return [TEMPLATES[self.steps.current]]
    
    def perm_check(self):
        if not self.request.user.has_perm("monitorings.manage_perm", self.monitoring):
            raise PermissionDenied()

    # directory to store the ascii files
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'media')) #
    
    # get the user
    def get_form_kwargs(self, step=1):
        kwargs = super(RangeCalibrationWizard, self).get_form_kwargs(step)
        kwargs['user'] = self.request.user
        return kwargs

    def done(self, form_list, **kwargs):
        # get the data from the form in a key value format
        data = {k: v for form in form_list for k, v in form.cleaned_data.items()}

        job_number = data['job_number']
        site_id = data['site_id']
        staff_number = data['inst_staff']
        level_number = data['inst_level']
        calibration_date = data['calibration_date']
        isObserver = data['observer_isme']
        # Temperature
        ave_temperature1 = (data['start_temp_1']+data['end_temp_1'])/2
        ave_temperature2 = (data['start_temp_2']+data['end_temp_2'])/2

        # Files - FieldBook
        field_book = data['field_book']
        field_file = data['field_file']

        # Get the observer
        if isObserver:
            field_person = self.request.user
            if field_person.first_name:
                observer = field_person.first_name +' '+ field_person.last_name
            else:
                observer = field_person.email
        else:
            observer = data['observer']

        # Process data & update the databases
        thisMeasurement = {}
        
        if StaffCalibrationRecord.objects.filter(inst_staff=staff_number).exists():
            
            thisStaff = StaffCalibrationRecord.objects.filter(inst_staff=staff_number).order_by('-calibration_date')[0]
            # Attach the staff attributes
            thisStaff_Attributes = {
                            'dStaffLength': thisStaff.inst_staff.staff_length,
                            'dThermalCoefficient': thisStaff.inst_staff.thermal_coefficient*10**-6,
                            'dCorrectionFactor': thisStaff.scale_factor, 
                            'dStdTemperature': thisStaff.standard_temperature,
                        }
            
            # Read & tabulate field data    
            thisStaffReading = check_filetype(field_file)
            
            # Get the Pin information & Tabulate the staff readings
            newPillarList, thisMeasurement = rawdata_to_table(thisStaffReading, 
                                                    ave_temperature1, 
                                                    ave_temperature2, 
                                                    thisStaff_Attributes) # get all the elements together
            # Check Pin/Pillar Numbers
            site_instance = CalibrationSite.objects.get(site_name = site_id.site_name)
            numberOfPillars = site_instance.no_of_pillars
            pillar_numbers = Pillar.objects.filter(site_id = site_id).values_list('name')
            pillar_numbers = [x[0] for x in pillar_numbers]
            pillarList = sorted(pillar_numbers, key=int)

            # Check pins with database
            if (newPillarList == pillarList):
                # Update RangeCalibrationRecord
                obj, created = RangeCalibrationRecord.objects.get_or_create(  job_number = job_number,
                                                        site_id = site_id,
                                                        inst_staff = staff_number,
                                                        inst_level = level_number,
                                                        ave_temperature1 = ave_temperature1,
                                                        ave_temperature2 = ave_temperature2,
                                                        calibration_date = calibration_date, 
                                                        observer = observer,
                                                        field_book = field_book,
                                                        field_file = field_file)
                # Create Raw Data model
                RawDataModel.objects.create(
                                        calibration_id = obj,
                                        observation = thisMeasurement) 

                # build the context to render to the template
                context = {
                        'calibration_id' : obj.id,
                        'job_number': job_number,
                        'staff_number': staff_number,
                        'level_number': level_number,
                        'observer': observer,
                        'calibration_date': calibration_date,
                        'average_temperature': (ave_temperature1+ave_temperature2)/2,
                        'range_measurement': thisMeasurement
                }
                return render(self.request, 'rangecalibration/range_report.html',  context = context)
            else:
                mPillarsInData = [x for x in pillarList if x not in newPillarList]
                missingPillarsDbase = [x for x in newPillarList if x not in pillarList]
                # print('1. Your data contains unverified pillar numbers: '+ ' '.join(missingPillarsDbase) + ' <br> 2. Missing pillar numbers in your data: '+ ' '.join(mPillarsInData))
                # data= abc
                messages.error(self.request, mark_safe('1. Your data contains unverified pillar numbers: '+ ' '.join(missingPillarsDbase) + ' <br> 2. Missing pillar numbers in your data: '+ ' '.join(mPillarsInData)))
                return redirect('rangecalibration:calibrate')
        else:
               messages.error(self.request, f'Opps! Looks like this staff ({ staff_number }) has no calibration parameters. Please enter the staff details and try again.')
               return redirect('rangecalibration:calibrate')
###############################################################################
# adjust view
from math import sqrt
def adjust(request, id):
    # Get the job
    thisRecord = RangeCalibrationRecord.objects.get(id=id)

    # Get the raw data
    thisData = RawDataModel.objects.get(calibration_id = thisRecord)

    rawDataSet = []
    uniquePillarList = []
    for key, value in thisData.observation.items():
        if key == 'headers':
            for items in value:
                continue# print(items) #print(key, value)
        if key == 'data':
            for items in value:
                rawDataSet.append(items)
                if not items[1] in uniquePillarList:
                    uniquePillarList.append(items[1])
    
    # to Array
    rawDataSet = np.array(rawDataSet, dtype=object)
    # print(rawDataSet)
    output_adj = []
    output_hdiff = []
    for i in range(len(uniquePillarList)):
        x = uniquePillarList[i]

        dato = rawDataSet[rawDataSet[:,1]== x]
        if len(dato) == 1:
            interval = dato[0][1]
            obs_hdiff = '{:.5f}'.format(float(dato[0][-1]));
            adj_hdiff = '{:.5f}'.format(float(dato[0][-1]));
            resid = '{:.5f}'.format(0.0)
            std_dev = '{:.2f}'.format(float(dato[0][-3])*1000)
            stdev_resid = '{:.2f}'.format(0.0)
            std_resid = '{:.2f}'.format(0.0)
            unc = '{:.2f}'.format(float(dato[0][-3])*1000*1.96)
            # Construct list
            output_adj.append([
                interval, adj_hdiff, obs_hdiff, resid, std_dev, stdev_resid, std_resid
            ])
            output_hdiff.append([
                interval, adj_hdiff, unc, len(dato)
            ])
        elif len(dato) == 2:
            interval = dato[0][1]
            # Prepare the required arrays
            # W = dato[:,-1].astype(np.float); P = np.diag(1/(dato[:,-3].astype(np.float))**2); A = np.ones(len(W))
            W = dato[:,-1].astype(float); P = np.diag(1/(dato[:,-3].astype(float))**2); A = np.ones(len(W))
            
            # Perform Least squares - Refer to J.Klinge & B. Hugessen document on Calibration of Barcode staffs
            adj_hdiff = (np.matmul(np.transpose(A), np.matmul(P, W)))/(np.matmul(np.transpose(A), np.matmul(P, A))) # (A_T*P*A)^(-1)*A_T*P*W
            resid = np.array(adj_hdiff - W, dtype=float)
            std_dev = np.sqrt(1./np.sqrt(np.diag(P).astype(float))**2)
            stdev_resid = np.sqrt(1./np.sqrt(np.diag(P).astype(float))**2 - 1./sqrt(np.matmul(np.transpose(A), np.matmul(P, A)))**2)
            unc = (sqrt(1/np.matmul(np.transpose(A), np.matmul(P, A)))*1000*1.96)
            std_resid = np.round_(resid/stdev_resid,1)

            # Prepare the outputs - 
            for j in range(len(W)):
                output_adj.append([interval, '{:.5f}'.format(adj_hdiff), '{:.5f}'.format(W[j]), '{:.5f}'.format(resid[j]),
                                '{:.2f}'.format(std_dev[j]*1000), '{:.2f}'.format(stdev_resid[j]*1000), 
                                '{:.1f}'.format(std_resid[j])])
            output_hdiff.append([interval, '{:.5f}'.format(adj_hdiff), '{:.2f}'.format(unc), len(dato)])
        # print(dato)
    
    # Update the database
    output_hdiff = {'headers': ['PILLAR','HEIGHT DIFF','UNCERTAINTY(mm)','OBSERVATION COUNT'], 'data': [list(x) for x in output_hdiff]}
    output_adj = {'headers': ['PILLAR','ADJ HEIGHT DIFF','OBS HEIGHT DIFF','RESIDUAL','STANDARD DEVIATION','STDEV RESIDUAL','STANDARD_RESIDUAL'], 'data':  [list(x) for x in output_adj]} 
    
    if not AdjustedDataModel.objects.filter(calibration_id=thisRecord): 
        AdjustedDataModel.objects.create(
                                    calibration_id = thisRecord,
                                    adustment = output_adj) 
    if not HeightDifferenceModel.objects.filter(calibration_id=thisRecord): 
        HeightDifferenceModel.objects.create(
                                    calibration_id = thisRecord,
                                    height_difference = output_hdiff) 
    
    # Update the RangeParameter database
    try:
        update_range_table_current(thisRecord)
        thisRecord.updated_to = True
        messages(request, 'Successfully updated the Calibration Range.')
    except:
        pass
    # build the context to render to the template
    context = {
            'calibration_id' : thisRecord.id,
            'job_number': thisRecord.job_number,
            'site_id': thisRecord.site_id,
            'staff_number': thisRecord.inst_staff,
            'level_number': thisRecord.inst_level,
            'observer': thisRecord.observer,
            'calibration_date': thisRecord.calibration_date,
            'average_temperature': (thisRecord.ave_temperature1+thisRecord.ave_temperature2)/2,
            'output_raw': thisData.observation,
            'output_hdiff' : output_hdiff,
            'output_adj': output_adj 
        }
    return render(request, 'rangecalibration/adjustment_report.html',  context = context)
###############################################################################
############################### Compute Annual Cycle ##########################
###############################################################################
# check if all BarCodeRangeParam month fields are null
def is_field_blank(thisObj):
    monthCol = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    if any(thisObj.values(mon) for mon in monthCol):
        return True
    else:
        return False

def range_display(dataObj, req_column):
    # Do the calculation if data exists
    [thisList] = list(dataObj.values_list(*req_column))
    # datalist = datalist.items()
    thisList = [x for x in thisList]
    # print(len(thisList))
    monList = req_column[1:]
    pillarList = thisList[0]['from_to']
    dataList = thisList[1:]
    
    # Get the Sum
    monSum = {'month': [], 'mean': [], 'std_dev': []}
    monValues = {'month': [], 'mean': [], 'std_dev': []}

    emptyArr =  np.zeros((1, len(pillarList)))[0]
    mean_value = np.zeros((len(pillarList), len(monList)))
    std_value =  np.zeros((len(pillarList), len(monList)))
    for i in range(len(dataList)):
        m_text = monList[i]
        mon_dat = dataList[i]
        # Calculate mean and standard deviations
        if mon_dat:
            # Values
            monValues['month'].append(m_text)
            mean_value[:,i] = np.array(mon_dat['mean']).astype(object)
            std_value[:,i] = np.array(mon_dat['std_dev']).astype(object)

            # Sum of the range
            monSum['month'].append(m_text)
            monSum['mean'].append(np.array(mon_dat['mean']).astype(float).sum())
            monSum['std_dev'].append(np.array(mon_dat['std_dev']).astype(float).mean())
        else:
            monValues['month'].append(m_text)

            # Sum of the range
            monSum['month'].append(m_text)
            monSum['mean'].append('NaN')
            monSum['std_dev'].append('NaN')

    pillarList = np.array(pillarList, dtype=object).reshape(-1,1)         # to column array

    monValues['mean'] = np.concatenate((pillarList, mean_value), axis=1)
    monValues['std_dev'] = np.concatenate((pillarList, std_value), axis=1)   
    return monValues, monSum

@login_required(login_url="/accounts/login") 
def range_param_process(request):
    if request.method=="POST":
        form = RangeParamForm(request.POST, user=request.user)
        if form.is_valid():
            site_id = form.cleaned_data.get('site_id') # Get the site id
            # List the site info
            site_info = {'site_name': site_id.site_name,
                        'site_type': site_id.get_site_type_display(),
                        'operator': site_id.operator.company_name,
                        'site_address': site_id.site_address + ' ' + site_id.state.statecode + ' ' + str(site_id.locality.postcode)
            }
            # Process Range Parameters
            try:
                compute_range_site(site_id)
            except:
                pass
            rangeObj = BarCodeRangeParam.objects.filter(site_id = site_id)
            # List of fields 
            required_column = ['from_to', 'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
            # if there is data for any of the month
            if is_field_blank(rangeObj): 
                range_values, range_param = range_display(rangeObj, required_column)
                # Compute deviation from mean - range sum
                tmp = np.array(range_param['mean']).astype(float)
                range_param.update({'deviation': []})
                if sum(~np.isnan(tmp)) >= 2:
                    tmp2 = (tmp - np.nanmean(tmp)).tolist()
                    range_param['deviation'] = ['NaN' if np.isnan(x) else round(x*1000,3) for x in tmp2]

                return render(request, 'rangecalibration/range_parameters.html', {
                                                                                'site_info': site_info,
                                                                                'range_values': range_values,
                                                                                'range_param': range_param
                                                                            })
            else:
                messages.warning(request, "There is no range parameters for this Calibration site. Redirecting to the processing page.")
                return redirect('rangecalibration:calibrate')
    else:
        form = RangeParamForm(user=request.user)
    return render(request, 'rangecalibration/range_param_form.html', {'form':form})

@login_required(login_url="/accounts/login")
def range_param_update(request, site_id):
    calibList = RangeCalibrationRecord.objects.filter(site_name = site_id)
    for calib in calibList:
        print(calib.job_number)
    return HttpResponse("Nothing to display yet")
###############################################################################
######################### PRINT REPORT ########################################
###############################################################################
from django_xhtml2pdf.utils import generate_pdf
@login_required(login_url="/accounts/login")
def print_record(request, id):
    resp = HttpResponse(content_type='application/pdf')
    
    # Calibration ID
    thisRecord = RangeCalibrationRecord.objects.get(id=id)
    
    # Range Datasets
    output_raw = RawDataModel.objects.get(calibration_id=thisRecord)
    output_hdiff = HeightDifferenceModel.objects.get(calibration_id=thisRecord)
    output_adj = AdjustedDataModel.objects.get(calibration_id=thisRecord)
    # print(output_hdiff.height_difference)
    # Prepare the context to be rendered
    context = {
            'calibration_id' : thisRecord.id,
            'job_number': thisRecord.job_number,
            'site_id': thisRecord.site_id,
            'staff_number': thisRecord.inst_staff,
            'level_number': thisRecord.inst_level,
            'observer': thisRecord.observer,
            'calibration_date': thisRecord.calibration_date,
            'average_temperature': (thisRecord.ave_temperature1+thisRecord.ave_temperature2)/2,
            'output_raw': output_raw.observation,
            'output_hdiff': output_hdiff.height_difference,
            'output_adj': output_adj.adustment,
            'today': datetime.now().strftime('%d/%m/%Y  %I:%M:%S %p'),
            }
    result = generate_pdf('rangecalibration/pdf_report.html', file_object=resp, context=context)
    return result   
###############################################################################
######################### DELETE RECORD #######################################
###############################################################################
def delete_record(request, id):
    thisRecord = RangeCalibrationRecord.objects.get(id=id)

    # Get month in String - Jan, Feb, so on ....
    m_text = thisRecord.calibration_date.strftime('%b')
    calib_date = thisRecord.calibration_date.strftime('%d-%m-%Y') 

    # Delete the record and update the range param table
    try:
        # Delete associated datasets
        RawDataModel.objects.get(calibration_id=thisRecord).delete()
        HeightDifferenceModel.objects.get(calibration_id=thisRecord).delete()
        AdjustedDataModel.objects.get(calibration_id=thisRecord).delete()

        BarCodeRangeParam.objects.filter(site_id = thisRecord.site_id).update(**{m_text: None})
        update_range_table_current(thisRecord)
        # finally delete the CalibrationRecord
        thisRecord.delete()
        messages.success(request, "Successfully updated the Range for the month of "+ m_text + ". Click on Staff Calibration > Range Parameters to see the updated Range.")
    except ObjectDoesNotExist:
        messages.success(request, "Range calibration record for "+ calib_date + " does not exists. Please check and try again!" )        
        
    return redirect('rangecalibration:home')
###############################################################################