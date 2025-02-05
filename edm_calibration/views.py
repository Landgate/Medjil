'''

   © 2024 Western Australian Land Information Authority

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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.forms import modelformset_factory
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.db.models import Prefetch

from collections import OrderedDict
from math import pi, sin, cos, sqrt
from datetime import date, timedelta
import json
import pandas as pd


from common_func.Convert import (
    import_csv_to_observations,
    baseline_qry2,
    calibrations_qry2,
    dict_2_html_table,
    get_endnotes,
    uncertainty_qry2,
    group_list)
from common_func.SurveyReductions import (
    validate_survey2,
    apply_calib,
    edm_std_function,
    offset_slope_correction,
    slope_certified_dist,
    add_certified_dist_uc2,
    add_surveyed_uc2,
    add_calib_uc2,
    refline_std_dev,
    sum_uc_budget,
    add_typeA,
    float_or_null
    )
from .forms import (
    uPillarSurveyForm,
    UploadSurveyFilesForm,
    ChangeSurveyFilesForm,
    EDM_ObservationForm,
    PillarSurveyApprovals,
    IntercomparisonForm,
    BulkEDMIReportForm
    )
from .models import (
    EDMI_certificate,
    uPillarSurvey,
    uEdmObservation,
    Intercomparison
    )
from common_func.LeastSquares import (
    LSA,
    ISO_test_a2,
    ISO_test_b,
    ISO_test_c)
from common_func.validators import try_delete_protected
from baseline_calibration.models import (
    Uncertainty_Budget_Source)


def is_staff(user):
    return user.is_staff

    
@login_required(login_url="/accounts/login")
def edm_calibration_home(request):
    locations = list(request.user.locations.values_list('statecode', flat=True))
    pillar_surveys = uPillarSurvey.objects.select_related('edm').filter(
        edm__edm_specs__edm_owner = request.user.company.id,
        site__state__statecode__in = locations)
        
    context = {
        'pillar_surveys': pillar_surveys}
    
    return render(request, 'edm_calibration/edm_calibration_home.html', context)


@login_required(login_url="/accounts/login") 
def certificate(request, id):
    # This uses the html report saved to the database to popluate the certificate
    # It also loads the approvals form that can be edited and saved.    
    edmi_certificate_qs = get_object_or_404(EDMI_certificate, id=id)
    pillar_survey_qs = get_object_or_404(
        uPillarSurvey,
        certificate_id=id,
        edm__edm_specs__edm_owner = request.user.company.id)
    ps_approvals = PillarSurveyApprovals(
        request.POST or None, instance=pillar_survey_qs)
    if ps_approvals.is_valid():
        ps_approvals.save()
        url = reverse('instruments:home', kwargs={'inst_disp': 'edm'})
        return redirect(url)
    
    html_content = edmi_certificate_qs.html_report
    html_content = html_content.replace('// certificate()', 'certificate()')
    context = {'ps_approvals':ps_approvals,
               'html_report': html_content}
    return render(request, 'edm_calibration/display_report.html', context)


@login_required(login_url="/accounts/login") 
def report(request, id):
    # This uses the html report saved to the database to popluate the certificate
    # It also loads the approvals form that can be edited and saved. 
    pillar_survey_qs = get_object_or_404(
        uPillarSurvey,
        certificate_id=id,
        edm__edm_specs__edm_owner = request.user.company.id)
    ps_approvals = PillarSurveyApprovals(
        request.POST or None, instance=pillar_survey_qs)
    if ps_approvals.is_valid():
        ps_approvals.save()
        return redirect('edm_calibration:edm_calibration_home')
    
    html_content = pillar_survey_qs.certificate.html_report
    context = {'ps_approvals':ps_approvals,
               'html_report': html_content}
    return render(request, 'edm_calibration/display_report.html', context)


@login_required(login_url="/accounts/login") 
def intercomparison_home(request):
   
    intercomparisons = Intercomparison.objects.select_related('edm').filter(
        edm__edm_specs__edm_owner = request.user.company.id)
        
    context = {
        'intercomparisons': intercomparisons}
    return render(request, 'edm_calibration/intercomparison_home.html', context)
    

@login_required(login_url="/accounts/login") 
def intercomparison_report(request, id):
    # This uses the html report saved to the database to reload the report
    comparison = get_object_or_404(Intercomparison, pk=id)
    
    html_content = comparison.html_report
    context = {'html_report': html_content}
    return render(request, 'edm_calibration/intercomparison_report_display.html', context)


@login_required(login_url="/accounts/login") 
def intercomparison_del(request, id):
    delete_obj = Intercomparison.objects.get(
        id=id,
        edm__edm_specs__edm_owner = request.user.company.id)
    try_delete_protected(request, delete_obj)
    
    return redirect('edm_calibration:intercomparison_home')


@login_required(login_url="/accounts/login") 
def intercomparison(request, id=None):
    # If id is provided, get the existing else create a new one
    if id=='None':
        ini_data = {'to_date':date.today().isoformat()}
        form = IntercomparisonForm(
            request.POST or None,
            user=request.user,
            initial=ini_data)
    else:
        qs = get_object_or_404(
            Intercomparison,
            pk=id,
            edm__edm_specs__edm_owner = request.user.company.id)
        form = IntercomparisonForm(
            request.POST or None,
            instance = qs,
            user = request.user)
    
    if form.is_valid():
        # If the form is submitted and valid produce the report
        distances = [
            float(d) for d in form.cleaned_data['sample_distances'].split(',')
            ]
        distances = sorted(set(distances))
        comparisons = []
        certificates = EDMI_certificate.objects.filter(
            edm=form.cleaned_data['edm'],
            prism=form.cleaned_data['prism'],
            calibration_date__gte=form.cleaned_data['from_date'],
            calibration_date__lte=form.cleaned_data['to_date']
        )
        
        # raise a warning if there are not enough records to complete a comparison
        if len(certificates) < 2:
            msg = "Your request must return more than one calibration record for an intercomparison. "
            if certificates:                
                msg+= ("Only the following record was returned: " +
                       f"<ul><li> { certificates[0] }</li></ul>")                
            messages.warning(request, msg)
        else:
            # loop through all records and compare each to every other one.
            for i, cert1 in enumerate(certificates):
                for cert2 in certificates[i + 1:]:
                    comparison = {}
                    for dist in distances:
                        (lab, lab_uc) = cert1.apply_calibration(dist)
                        (ref, ref_uc) = cert2.apply_calibration(dist)
                        e = ((lab - ref)/
                             sqrt(lab_uc**2 + ref_uc**2))
                        comparison[dist] = {
                            'lab':lab,
                            'lab_uc':lab_uc,
                            'ref':ref,
                            'ref_uc':ref_uc,
                            'E':e}
                    comparisons.append(
                        {'lab': cert1,
                         'ref': cert2,
                         'comparison': comparison})
            
            # Calculate data for graph
            back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                            '#00FF00', '#008000', '#00FFFF', '#008080', 
                            '#0000FF', '#000080', '#FF00FF', '#800080']
            graph1_datasets = []
            i=0
            for certificate in (certificates):
                dataset = {
                    'backColor': back_colours[i],
                    'borderWidth': 1,
                    'data':[],
                    'fill': False,
                    'label': certificate.calibration_date.strftime('%d-%b-%Y'),
                    'pointRadius': 0,
                    'showLine': True,
                    'tension': 0
                    }
                i+=1
                if i > len(back_colours) : i=0
                dist = min(distances)
                while dist <= max(distances):
                    dataset['data'].append({
                        'x': dist,
                        'y':certificate.apply_calibration(dist)[1]
                        })
                    dist+= form.cleaned_data['edm'].edm_specs.unit_length / 4
                graph1_datasets.append(dataset)
            #convert from python to json
            graph1_datasets = json.dumps(graph1_datasets, cls=DjangoJSONEncoder)
            
            context = {'form': form.cleaned_data,
                       'certificates':certificates,
                       'comparisons' : comparisons,
                       'graph1_datasets':graph1_datasets}
            html_report = render_to_string(
                'edm_calibration/intercomparison_report.html', context)
            instance = form.save(commit=False)
            instance.html_report = html_report
            instance.save()
            
            return render(request, 
                          'edm_calibration/intercomparison_report_display.html',
                          {'html_report': html_report})

    return render(request, 'edm_calibration/intercomparison_edit.html', {'form': form})


@login_required(login_url="/accounts/login")
@user_passes_test(is_staff)
def bulk_report_download(request):
    if request.method == 'POST':
        form = BulkEDMIReportForm(request.POST)
        if form.is_valid():
            baseline = form.cleaned_data['baseline']
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']
            
            # Set default values if dates are not provided
            if not from_date:
                from_date = date(1800, 1, 1)
            if not to_date:
                to_date = date.today() + timedelta(days=1)
            
            # Filter based on date range
            data = uPillarSurvey.objects.filter(
                site=baseline,
                survey_date__range=[from_date, to_date]
            ).select_related('certificate').values('certificate__html_report')
            
            if not data.exists():
                # No data found, return to form with an error message
                return render(request, 'edm_calibration/bulk_report_download.html', {
                    'form': form,
                    'error': 'No data found for the selected baseline and date range.'
                })
            
            baseline_name = baseline.site_name
            df = pd.DataFrame(data)
            # Create a response object and set the appropriate headers
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{baseline_name}_edmi_clibration_reports.html"'
            # Write the DataFrame to the response without the header
            df.to_csv(path_or_buf=response, index=False, header=False)
            return response
    else:
        form = BulkEDMIReportForm()

    return render(request, 'edm_calibration/bulk_report_download.html', {'form': form})


@login_required(login_url="/accounts/login")   
def survey_delete(request, id):
    survey = get_object_or_404(
        uPillarSurvey, 
        id=id,
        edm__edm_specs__edm_owner = request.user.company.id)
    try_delete_protected(request, survey)
    
    return redirect('edm_calibration:edm_calibration_home')


@login_required(login_url="/accounts/login")
def survey_create(request, id=None):
    # Retrieve the existing instance or create a new one
    instance = uPillarSurvey.objects.filter(
        id=id,
        edm__edm_specs__edm_owner = request.user.company.id).first() if id else None

    # Use the appropriate form based on whether there's an instance
    pillar_survey_form = uPillarSurveyForm(
        request.POST or None, 
        request.FILES or None, 
        instance=instance, 
        user=request.user
    )

    if instance:
        survey_files = ChangeSurveyFilesForm(
            request.POST or None,
            request.FILES or None
        )
    else:
        survey_files = UploadSurveyFilesForm(
            request.POST or None,
            request.FILES or None
        )

    # If the main form is valid, save the pillar survey instance
    if pillar_survey_form.is_valid():
        pillar_survey = pillar_survey_form.save()

        # Check if the file upload form is valid
        if survey_files.is_valid():
            # Process the CSV file if it exists and import observations
            if survey_files.cleaned_data.get('edm_file'):
                csv_file = survey_files.cleaned_data.get('edm_file')
                import_errors = import_csv_to_observations(
                    csv_file, pillar_survey)
    
                # Render errors if there are any
                if len(import_errors) > 0:
                    return render(request, 'edm_calibration/errors_report.html', {
                        'Check_Errors': {'Errors': import_errors, 'Warnings': []},
                        'id': pillar_survey.pk
                    })

            return redirect('edm_calibration:edm_observations_update', id=pillar_survey.pk)

    # Render the form if it is invalid
    headers = {
        'page0': 'EDMI Calibration Details',
        'page1': 'Instrumentation Details',
        'page2': 'Error Budget and File Uploads',
    }
    return render(request, 'edm_calibration/uPillarSurvey_form.html', {
        'headers': headers,
        'form': pillar_survey_form,
        'survey_files': survey_files,
    })


@login_required(login_url="/accounts/login")
def edm_observations_update(request, id):
    qs = uEdmObservation.objects.filter(
        pillar_survey__pk=id,
        pillar_survey__edm__edm_specs__edm_owner=request.user.company.id)
    
    # Create the formset
    formset = modelformset_factory(uEdmObservation, form=EDM_ObservationForm, extra=0)
    edm_obs_formset = formset(request.POST or None, queryset=qs)

    if request.method == 'GET':
        return render(request, 'edm_calibration/edm_observations_update.html', {
            'id': id,
            'edm_obs_formset': edm_obs_formset,
        })

    elif request.method == 'POST':
        # Validate and save the formset
        if edm_obs_formset.is_valid():
            edm_obs_formset.save()
            return redirect('edm_calibration:compute_calibration', id=id)
    

@user_passes_test(is_staff)
def compute_calibration(request, id):    
    # Retrieve the Pillar Survey instance and related data
    pillar_survey = get_object_or_404(
        uPillarSurvey.objects.select_related(
            'edm', 'prism', 'uncertainty_budget', 'site'
        ).prefetch_related(
            Prefetch(
                'uedmobservation_set',
                queryset=uEdmObservation.objects.select_related('from_pillar', 'to_pillar')
            )
        ),
        id=id
    )
    try:
    # if 1==1:
        # Prepare data for calculations
        edm_observations = list(pillar_survey.uedmobservation_set.all())
        raw_edm_obs = {
            str(obs.id): {
                **model_to_dict(obs),
                'from_pillar': obs.from_pillar.name if obs.from_pillar else None,
                'to_pillar': obs.to_pillar.name if obs.to_pillar else None,
            }
            for obs in edm_observations
        }
        
        baseline_data = baseline_qry2(pillar_survey)
        calibrations = calibrations_qry2(pillar_survey)
    
        # Validate survey data
        validation_errors = validate_survey2(
            pillar_survey=pillar_survey,
            baseline=baseline_data,
            calibrations=calibrations,
            raw_edm_obs=raw_edm_obs,
        )
        
        if len(validation_errors['Errors']) > 0:
            return render(request, 'edm_calibration/errors_report.html', 
                          {'Check_Errors':validation_errors, 'id':id})
                                  
        #----------------- Query notes and Uncertainty -----------------#
        report_notes = get_endnotes(
            pillar_survey = pillar_survey,
            company=request.user.company, calibration_type='E')
        uc_budget = uncertainty_qry2(pillar_survey)
        uc_budget['sources'] = add_calib_uc2(uc_budget['sources'], 
                                             calibrations,
                                             pillar_survey)
        
        for o in raw_edm_obs.values():
            #----------------- Instrument Calibration Corrections -----------------#            
            o['Temp'], o['temp_calib_corr'] = apply_calib(
                float_or_null(o['raw_temperature']),
                pillar_survey.thermo_calib_applied,
                calibrations['them'])
            o['Pres'], o['pres_calib_corr'] = apply_calib(
                float_or_null(o['raw_pressure']),
                pillar_survey.baro_calib_applied,
                calibrations['baro'])
            o['Humid'], o['humi_calib_corr'] = apply_calib(
                float_or_null(o['raw_humidity']),
                pillar_survey.hygro_calib_applied,
                calibrations['hygro'])
            
            o['Mets_Correction'] = (
                pillar_survey.edm.edm_specs.atmospheric_correction(
                    o=o,
                    null_correction=pillar_survey.mets_applied))
            
            o['slope_dist'] = (float(o['raw_slope_dist'] )
                               + o['Mets_Correction'])
            o['bay'] = o['from_pillar'] + ' - ' + o['to_pillar']
            
        # Group raw data by bays, calc averages and experimental std dev
        edm_observations = group_list(
            raw_edm_obs.values(),
            group_by='bay',
            labels_list=['from_pillar',
                         'to_pillar'],
            avg_list=['inst_ht',
                      'tgt_ht',
                      'Temp',
                      'Pres',
                      'Humid',
                      'Mets_Correction',
                      'raw_slope_dist',
                      'slope_dist',],
            std_list=['slope_dist'],
            mask_by='use_for_distance')
        
        edm_trend = edm_std_function(
            edm_observations, 
            uc_budget['stddev_0_adj'])           #y = Ax + B
                       
        matrix_A = []
        matrix_x = []
        matrix_P = []
        iso_A = []
        iso_x = []
        pillars_used = pillar_survey.get_pillars_used()
        for i, o in enumerate(edm_observations.values()):
            o['id']=str(i+1)
            o = (offset_slope_correction(o,
                                         baseline_data['certified_dist'],
                                         baseline_data['certified_dist'],
                                         baseline_data['d_radius']))
            
            o['certified_slope_dist'] = (slope_certified_dist(o,
                                         baseline_data['certified_dist'],
                                         baseline_data['d_radius']))
            o['diff_to_certified_sd'] = (o['slope_dist']
                                         - o['certified_slope_dist'])
            
            o['Reduced_distance'] = (o['slope_dist'] 
                                    + o['Offset_Correction']
                                    + o['Slope_Correction'])
    
            #----------------- Calculate Uncertainties -----------------#
            o['uc_sources'] = add_certified_dist_uc2(
                o,
                pillar_survey,
                uc_budget['sources'],
                baseline_data['std_dev_matrix'],
                baseline_data['calibrated_baseline'].results.degrees_of_freedom)
            
            o['uc_sources'] = add_surveyed_uc2(o, edm_trend,
                                               pillar_survey,
                                               o['uc_sources'],
                                               baseline_data['certified_dist'])
                  
            o['apriori_uc_budget'] = refline_std_dev(o,
                                            baseline_data['certified_dist'], 
                                            pillar_survey.edm)
               
            o['uc_budget'] = refline_std_dev(o,
                                            baseline_data['certified_dist'], 
                                            pillar_survey.edm)
              
            o['uc_combined'] = sum_uc_budget(o['uc_budget'])
            
            #----------------- Least Squares -----------------#
            #----------------- compile Design matrix, weight Matrix -----------------#
            # Matrix's for ISO 17123-4:2012 Full test procedure
            iso_a = []
            cell_val = 0
            for pillar in pillars_used:
                if o['from_pillar'] == pillar.name or o['to_pillar'] == pillar.name:
                    if cell_val == 0: cell_val = 1
                    elif cell_val == 1: cell_val = 0
                iso_a.append(cell_val)
            
            iso_A.append(iso_a[:-1] + [-1])
            
            iso_x.append(o['Reduced_distance'])
            
            # Matrix's for metrologically traceable measurements
            a_row = [1,
                     o['Reduced_distance']]
            # Do not test for cyclic errors if unit length is not specified
            if pillar_survey.edm.edm_specs.unit_length:
                d_term = ((2*pi*o['Reduced_distance'])
                          / pillar_survey.edm.edm_specs.unit_length)
                o['d_term'] = d_term
                a_row.extend([
                    sin(d_term),
                    cos(d_term),
                    sin(2*d_term),
                    cos(2*d_term)])
            matrix_A.append(a_row)
          
            frm = baseline_data['certified_dist'][o['from_pillar']]['distance']
            to = baseline_data['certified_dist'][o['to_pillar']]['distance']
            matrix_x.append(abs(float(to) - float(frm))
                                 -o['Reduced_distance'])
              
            P_row = [0]*len(edm_observations)
            P_row[len(matrix_x)-1] = (1/
                    (o['uc_combined']['std_dev']*float(pillar_survey.scalar))**2)
            matrix_P.append(P_row)
            
        if not pillar_survey.test_cyclic:
            matrix_A = [a[:2] for a in matrix_A]
            order_cmt = ['zero']
            report_notes.append('User input for this calibration requested that no test for cyclic errors be performed.')
        elif not pillar_survey.edm.edm_specs.unit_length:
            report_notes.append('Testing for cyclic errors during this calibration was not possible because the unit lenght of the Instrument has not been specified in the Instrument Model Specifications.')
        
        # run the LSA for the iso_17123:4 full test
        iso_y, _, iso_chi_test, iso_residuals = LSA(iso_A, iso_x)
        
        if iso_y:
            ini_from_pillar = pillars_used[1].name
            for pillar, parameter in zip(pillars_used[1:], iso_y[:-1]):
                parameter['from_pillar'] = ini_from_pillar
                parameter['to_pillar'] = pillar.name
                ini_from_pillar =pillar.name
            iso_y[-1]['term'] = 'zero-point correction'
        else:
            validation_errors['Warnings'].append(
                'Insufficient survey observations were provided for performing the ISO 17123:4 "full test procedure". The results table for those results has been omitted from this report.')
        
        iso_full_test = {'matrix_y':iso_y,
                         'chi_test':iso_chi_test}
        
        # run LSA for metrologically traceable measurements with 6, 4 then 2 parameters
        # Check t-student test results after each LSA to determine if the end 2 cyclic errors are significant
        testing_terms = [True, True]
        while False not in testing_terms and len(matrix_A[0])!=0:
            matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, 
                                                            matrix_x,
                                                            matrix_P)
            
            matrix_y[0]['term']='zpc'
            matrix_y[1]['term']='scf'
            for i, p in enumerate(matrix_y[2:]):
                p['term'] = f'{i+1}C'
    
            if pillar_survey.test_cyclic:
                testing_terms = [t['t_test'] for t in matrix_y[-2:]]
                if len(matrix_A[0])==6: order_cmt = 'second order cyclic errors (3C, 4C)'
                if len(matrix_A[0])==4: order_cmt = 'first order cyclic errors (1C, 2C)'
                if len(matrix_A[0])!= 2:
                    if False in testing_terms:
                        report_notes.append(
                            f'The t-student test has been used to test and determine that the {order_cmt} ' \
                            f' are statistically significant in this calibration data.')
                    else:
                        notes_tbl = []
                        for y in matrix_y:
                            notes_tbl.append(
                                {'Term':y['term'],
                                 'Value': round(y['value'],5),
                                 'Uncertainty': "{:.2g}".format(y['uncertainty']),
                                 'Null Hypothesis': y['hypothesis'],
                                 'Insignificant':y['t_test']})
                        notes_tbl = dict_2_html_table(notes_tbl)
                        report_notes.append(
                            f'The t-student test has been used to test the significance of the {order_cmt}.' \
                            f' This has determined that these cyclic errors are statistically insignificant in this calibration data.' \
                            f'{notes_tbl}')
                            
            # remove 2 parameters to maybe run again
            matrix_A = [a[:-2] for a in matrix_A]
        
        # populate a dictionary for certificate
        ini_edmi_certificate = {
            'edm':pillar_survey.edm,
            'prism':pillar_survey.prism,
            'calibration_date': pillar_survey.survey_date,
            'zero_point_correction': matrix_y[0]['value'],
            'zpc_uncertainty': matrix_y[0]['uncertainty'],
            'zpc_coverage_factor': chi_test['k'],
            'standard_deviation': chi_test['So'],
            'degrees_of_freedom': chi_test['dof'],
            'scale_correction_factor': matrix_y[1]['value'] + 1,
            'scf_uncertainty': matrix_y[1]['uncertainty'],
            'scf_coverage_factor': chi_test['k']
            }
        if len(matrix_y)>2:
            ini_edmi_certificate.update({
                'has_cyclic_corrections': True,
                'cyclic_one': matrix_y[2]['value'],
                'cyc_1_uncertainty': matrix_y[2]['uncertainty'],
                'cyc_1_coverage_factor': chi_test['k'],
                'cyclic_two': matrix_y[3]['value'],
                'cyc_2_uncertainty': matrix_y[3]['uncertainty'],
                'cyc_2_coverage_factor': chi_test['k']
                })
        if len(matrix_y)>4:
            ini_edmi_certificate.update({
                'cyclic_three': matrix_y[4]['value'],
                'cyc_3_uncertainty': matrix_y[4]['uncertainty'],
                'cyc_3_coverage_factor': chi_test['k'],
                'cyclic_four': matrix_y[4]['value'],
                'cyc_4_uncertainty': matrix_y[4]['uncertainty'],
                'cyc_4_coverage_factor': chi_test['k']
                })
        
        for o in edm_observations.values():
            o['residual'] = residuals[o['id']]['residual']
            o['std_residual'] = residuals[o['id']]['std_residual']
            o['uc_sources'] = add_typeA(o, matrix_y, chi_test['dof'])      
            o['uc_budget'] = refline_std_dev(
                o, 
                baseline_data['certified_dist'], 
                pillar_survey.edm)
              
            o['uc_combined'] = sum_uc_budget(o['uc_budget'])
        
        # Perform ISO statistical tests
        ISO_test=[]
        ISO_test.append(
            ISO_test_a2(
                pillar_survey,
                chi_test,
                [{'distance':50},
                 {'distance':100},
                 {'distance':200},
                 {'distance':400}, 
                 {'distance':600}])
            )
        
        if calibrations['edmi']:
            prev = calibrations['edmi'].first()
            ISO_test.append(
                ISO_test_b(
                    {'So': prev.standard_deviation,
                     'dof': prev.degrees_of_freedom},
                    chi_test)
                )
        else:
            report_notes.append('The ISO 17123:4 Test B statistical test has not been performed due to insufficient historical records.')
      
        ISO_test.append(
            ISO_test_c(
                matrix_y[0]['value'],
                matrix_y[0]['std_dev'],
                chi_test))
    
        #Prepare the context for the template    
        back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                        '#00FF00', '#008000', '#00FFFF', '#008080', 
                        '#0000FF', '#000080', '#FF00FF', '#800080',]
        
        edm_observations = list(edm_observations.values())
        first_to_last = {'Reduced_distance':0}
        residual_chart = []
        n_rpt_shots = max([len(e['grp_bay']) for e in edm_observations])
        i=0
        for o in edm_observations:
            if i == len(back_colours): i=0
            while len(o['grp_bay'])<n_rpt_shots:
                o['grp_bay'].append('')
                
            for uc in o['uc_budget'].values():
                uc['chart_colour'] = back_colours[i]
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            i+=1
            for uc in o['uc_sources']:
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            o['uc_sources']=sorted(o['uc_sources'], key=lambda x: x['group_verbose'])
            o['uc_budget'] = OrderedDict(sorted(o['uc_budget'].items()))
            for uc in o['apriori_uc_budget'].values():
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            
            o['apriori_uc_budget'] = OrderedDict(sorted(o['apriori_uc_budget'].items()))
            
            residual_chart.append({'from_pillar': o['from_pillar'], 
                               'to_pillar':o['to_pillar'],
                               'Reduced_distance': o['Reduced_distance'],
                               'residual': o['residual'],
                               'std_residual': o['std_residual']})
            if o['Reduced_distance'] > first_to_last['Reduced_distance']:
                first_to_last = o
        
        context = {'pillar_survey':pillar_survey,
                   'calib':calibrations,
                   'baseline': baseline_data,
                   'parameters': matrix_y,
                   'chi_test': chi_test,
                   'ISO_test': ISO_test,
                   'iso_full_test':iso_full_test,
                   'edm_observations': edm_observations,
                   'ini_edmi_certificate':ini_edmi_certificate,
                   'residual_chart': residual_chart,
                   'report_notes': report_notes,
                   'Check_Errors': validation_errors,
                   'first_to_last': first_to_last}
    
        html_report = render_to_string(
            'edm_calibration/calibrate_report.html', context)
        
        ini_edmi_certificate['html_report'] = html_report
        
        ps_approvals = PillarSurveyApprovals(
            request.POST or None,
            instance=pillar_survey)
        
        if ps_approvals.is_valid():
            # this is a POST command asking to commit the certificate
            # and signitures
            ps_approvals.save()
            cert_instance, _ = EDMI_certificate.objects.update_or_create(
                pk = pillar_survey.certificate.pk if pillar_survey.certificate else None,
                defaults= ini_edmi_certificate)
            
            pillar_survey.certificate = cert_instance
            pillar_survey.save()
                
            return redirect('edm_calibration:edm_calibration_home')
            
        context = {'pillar_survey':pillar_survey,
                    'html_report': html_report,
                    'ps_approvals':ps_approvals}
        return render(request, 'edm_calibration/display_report.html', context)
    except Exception as e:
        # any missed errors are caught here
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, 'edm_calibration/errors_report.html', 
                      {'id':id})

