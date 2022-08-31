from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, QueryDict
from django.forms import modelformset_factory
from django.forms.models import model_to_dict

from collections import OrderedDict
from math import pi, sin, cos
from common_func.Convert import *
from common_func.SurveyReductions import *
from .forms import (CalibrateEdmForm,
                    UploadSurveyFiles,
                    ChangeSurveyFiles,
                    EDM_ObservationForm,
                    CalibratedEdmForm
                    )
from .models import (uPillar_Survey,
                     uEDM_Observation
                     )
from common_func.LeastSquares import (
                    LSA,
                    ISO_test_a,
                    ISO_test_b,
                    ISO_test_c)
# Create your views here.
    
@login_required(login_url="/accounts/login")
def edm_calibration_home(request):
    if request.user.is_superuser:
        pillar_surveys = uPillar_Survey.objects.all()
    else:        
        pillar_surveys = uPillar_Survey.objects.select_related('edm').filter(
            edm__edm_specs__edm_owner = request.user.company.id)
        
    context = {
        'pillar_surveys': pillar_surveys}
    
    return render(request, 'edm_calibration/Home.html', context)


def clear_cache(request):
    if 'calibrate_e' in request.session:
        del request.session['calibrate_e']
        
        return redirect('edm_calibration:edm_calibration_home')


@login_required(login_url="/accounts/login") 
def pillar_survey_del(request, id):
    delete_pillar_survey = uPillar_Survey.objects.get(id=id)
    delete_pillar_survey.delete()
    
    return redirect('edm_calibration:edm_calibration_home')


@login_required(login_url="/accounts/login") 
def calibrate1(request, id):
    if id == 'None':
        qs=''
        if 'calibrate_e' in request.session:
            ini_data = request.session['calibrate_e']
        else:
            ini_data = {'computation_date':date.today().isoformat()}

        pillar_survey = CalibrateEdmForm(request.POST or None,
                                request.FILES or None,
                                user=request.user,
                                initial=ini_data)
        upload_survey_files = UploadSurveyFiles(request.POST or None,
                                                request.FILES or None)
    else:
        qs = get_object_or_404(uPillar_Survey, id=id)
        qs.survey_date = qs.survey_date.isoformat()
        qs.computation_date = qs.computation_date.isoformat()
        pillar_survey = CalibrateEdmForm(request.POST or None,
                                         request.FILES or None,
                                         instance = qs,
                                         user = request.user)
        upload_survey_files = ChangeSurveyFiles(request.POST or None,
                                                request.FILES or None)

    if pillar_survey.is_valid() and upload_survey_files.is_valid():
        frm = pillar_survey.cleaned_data
        survey_files = upload_survey_files.cleaned_data
        
    #----------------- Query related fields -----------------#
        calib = Calibrations_qry(frm)
        baseline = baseline_qry(frm)
        
        # read new edm file
        if survey_files['edm_file']:
            edm_clms=['from_pillar',
                      'to_pillar',
                      'inst_ht',
                      'tgt_ht',
                      'raw_slope_dist',
                      'raw_temperature',
                      'raw_pressure',
                      'raw_humidity']
            raw_edm_obs = csv2dict(survey_files['edm_file'],edm_clms)
            for v in raw_edm_obs.values():
                v['use_for_distance'] = True
                                   
            Check_Errors = validate_survey(pillar_survey=frm,
                                        baseline=baseline,
                                        calibrations=calib,
                                        raw_edm_obs=raw_edm_obs)
            
            if len(Check_Errors['Errors']) > 0:
                return render(request, 'baseline_calibration/errors_report.html', 
                              {'Check_Errors':Check_Errors})
        else:
            qs = uEDM_Observation.objects.filter(pillar_survey__pk=id)
            raw_edm_obs = {}
            for o in qs:
                dct = model_to_dict(o)
                dct['from_pillar'] = o.from_pillar.name
                dct['to_pillar'] = o.to_pillar.name
                raw_edm_obs[str(o.id)] = dct
            
        ps_instance = pillar_survey.save()
        id = ps_instance.pk
        if survey_files['edm_file']:
            # Commit all the edm raw observations
            delete_edm_obs = uEDM_Observation.objects.filter(pillar_survey=id)
            delete_edm_obs.delete()
            for o in raw_edm_obs.values():
                this_EDM_Observation = uEDM_Observation.objects.create(
                    pillar_survey = ps_instance,
                    from_pillar = baseline['pillars'].get(name=o['from_pillar']),
                    to_pillar = baseline['pillars'].get(name=o['to_pillar']),
                    inst_ht = o['inst_ht'],
                    tgt_ht = o['tgt_ht'],
                    raw_slope_dist = o['raw_slope_dist'],
                    raw_temperature = o['raw_temperature'],
                    raw_pressure = o['raw_pressure'],
                    raw_humidity = o['raw_humidity'],
                    use_for_distance = o['use_for_distance'])         
                            
        return redirect('edm_calibration:calibrate2', id=id)

    else:
        print(pillar_survey.is_valid())
        for e in pillar_survey.errors:
            print(e)
        for e in upload_survey_files.errors:
            print(e)
            
    headers = {'page0':'Calibrate the Baseline',
                'page1': 'Instrumentation',
                'page2': 'Corrections / Calibrations Applied to Instruments',
                'page3': 'Error Budget and File Uploads',}
    
    return render(request, 'edm_calibration/calibrate.html', {
            'Headers': headers,
            'form': pillar_survey,
            'qs':qs,
            'survey_files':upload_survey_files})


@login_required(login_url="/accounts/login") 
def calibrate2(request,id):
    # If this is a get request:
    #     select or deselect the edm observations for the calibration
    # If this is a post request: and edm_obs_formset.is_valid
    #     calculate and generate the report. 
    # If this is a post request: cd_formset.is_valid() and sdev_mat_formset.is_valid() and pillar_survey_update.is_valid()
    #     comit the calibration and return to home page.
    
    #----------------- Query site, surveys, instruments and calibrations -----------------#
    # Get the pillar_survey in dict like cleaned form data
    qs = uPillar_Survey.objects.get(id=id)
    query_dict = QueryDict('', mutable=True)
    query_dict.update(model_to_dict(qs))
    pillar_survey_form = CalibrateEdmForm(query_dict, user=request.user)
    pillar_survey_form.is_valid()
    pillar_survey = pillar_survey_form.cleaned_data
    pillar_survey.update({'pk':id})
    
    # Create form to hide on report and commit when submitted
    pillar_survey_update = CalibratedEdmForm(request.POST or None)
    
    # Get the raw_edm_obs in dict like cleaned form data
    formset = modelformset_factory(uEDM_Observation,
                            form=EDM_ObservationForm, extra=0)
    qs = uEDM_Observation.objects.filter(pillar_survey__pk=id)
    edm_obs_formset = formset(request.POST or None, queryset=qs)
    raw_edm_obs = {}
    for o in qs:
        dct = model_to_dict(o)
        dct['from_pillar'] = o.from_pillar.name
        dct['to_pillar'] = o.to_pillar.name
        raw_edm_obs[str(o.id)] = dct

    if request.method == 'GET':        
        formset = zip(edm_obs_formset,raw_edm_obs.values())
        
        return render(request, 'edm_calibration/edm_rawdata.html', {
                                                    'Page': 'Page 5 of 5',
                                                    'id': id,
                                                    'edm_obs_formset':edm_obs_formset,
                                                    'formset': formset})
    else:
        # This is a POST request
        # Apply a mask to the raw observations and recheck errors
        if edm_obs_formset.is_valid():
            edm_obs_formset.save()
            for form in edm_obs_formset:
                frm =form.cleaned_data
                raw_edm_obs[str(frm['id'].pk)]['use_for_distance']=frm['use_for_distance']
                    
            calib = Calibrations_qry(pillar_survey)
            baseline = baseline_qry(pillar_survey)
                                   
            Check_Errors = validate_survey(pillar_survey=pillar_survey,
                                        baseline=baseline,
                                        calibrations=calib,
                                        raw_edm_obs=raw_edm_obs)
            
            if len(Check_Errors['Errors']) > 0:
                return render(request, 'baseline_calibration/errors_report.html', 
                              {'Check_Errors':Check_Errors})
                              
            #----------------- Query notes and Uncertainty -----------------#
            report_notes = report_notes_qry(company=request.user.company, report_type='E')
            uc_budget = uncertainty_qry(pillar_survey)
            uc_budget['sources'] = add_calib_uc(uc_budget['sources'], 
                                                calib,
                                                pillar_survey)

            for o in raw_edm_obs.values():
                #----------------- Instrument Corrections -----------------#
                o['Temp'],c = apply_calib(o['raw_temperature'],
                                            pillar_survey['thermo_calib_applied'], 
                                            calib['them'])
                o['Pres'],c = apply_calib(o['raw_pressure'],
                                            pillar_survey['baro_calib_applied'],
                                            calib['baro'])
                o['Humid'],c = apply_calib(o['raw_humidity'],
                                            pillar_survey['hygro_calib_applied'],
                                            calib['hygro'])
                o = (edm_mets_correction(o, 
                                         pillar_survey['edm'],
                                         pillar_survey['mets_applied']))
                
                o['slope_dist'] = (float(o['raw_slope_dist'] )
                                   + o['Mets_Correction'])
                o['Bay'] = o['from_pillar'] + ' - ' + o['to_pillar']
            
            edm_observations = group_list(raw_edm_obs.values(),
                                            group_by='Bay',
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
                                            std_list=['slope_dist'])
            
            edm_trend = edm_std_function(edm_observations, 
                                         uc_budget['stddev_0_adj'])           #y = Ax + B
                           
            matrix_A = []
            matrix_x = []
            matrix_P = []
            for i, o in enumerate(edm_observations.values()):
                o['id']=str(i+1)
                o = (offset_slope_correction(o,
                                          baseline['certified_dist'],
                                          baseline['certified_dist'],
                                          baseline['d_radius']))
                  
                o['Reduced_distance'] = (o['slope_dist'] 
                                        + o['Offset_Correction']
                                        + o['Slope_Correction'])

                #----------------- Calculate Uncertainties -----------------#
                o['uc_sources'] = add_certified_dist_uc(o, 
                                                  uc_budget['sources'],
                                                  baseline['std_dev_matrix'],
                                                  baseline['calibrated_baseline'].degrees_of_freedom)
                
                o['uc_sources'] = add_surveyed_uc(o, edm_trend, 
                                                  uc_budget['sources'],
                                                  baseline['certified_dist'])
                      
                o['uc_budget'] = refline_std_dev(o, 
                                                baseline['certified_dist'], 
                                                pillar_survey['edm'])
                  
                o['uc_combined'] = sum_uc_budget(o['uc_budget'])
                
                #----------------- Least Squares -----------------#
                #----------------- 6 Parameter least squares adjustment -----------------#
                if pillar_survey['test_cyclic']:
                    d_term = ((2*pi*o['Reduced_distance'])
                              / pillar_survey['edm'].edm_specs.unit_length)
                    a_row = [1,
                             o['Reduced_distance'],
                             sin(d_term),
                             cos(d_term),
                             sin(2*d_term),
                             cos(2*d_term)]
                    matrix_A.append(a_row)
                  
                frm = baseline['certified_dist'][o['from_pillar']]['distance']
                to = baseline['certified_dist'][o['to_pillar']]['distance']
                matrix_x.append(abs(float(to) - float(frm))
                                -o['Reduced_distance'])
                  
                P_row = [0]*len(edm_observations)
                P_row[len(matrix_x)-1] = (1/
                                     o['uc_combined']['std_dev']**2)
                matrix_P.append(P_row)
            
            if pillar_survey['test_cyclic']:
                matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)
                            
                # Check t-student test results to determine if cyclic errors are significant
                if False not in [t['t_test'] for t in matrix_y[2:]]:
                    matrix_A=[[a[0], a[1]] for a in matrix_A]
                    matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)
            else:
                matrix_A=[[a[0], a[1]] for a in matrix_A]
                matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)
        
            for o in edm_observations.values():
                o['residual'] = residuals[o['id']]['residual']
                o['std_residual'] = residuals[o['id']]['std_residual']
            
            ISO_test=[]
            ISO_test.append(ISO_test_a(pillar_survey,
                                       chi_test,
                                       [{'distance':50},
                                        {'distance':100},
                                        {'distance':200},
                                        {'distance':400}, 
                                        {'distance':600}]))
            
            if len(calib['edmi']) > 0:
                ISO_test.append(ISO_test_b(
                    {'variance':(calib['edmi'][0].standard_deviation)**2,
                    'dof': calib['edmi'][0].degrees_of_freedom},
                    chi_test))
            ISO_test.append(ISO_test_c(matrix_y[0]['value'],
                                       matrix_y[0]['std_dev'],
                                       chi_test))

            #Prepare the context for the template
            back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                            '#00FF00', '#008000', '#00FFFF', '#008080', 
                            '#0000FF', '#000080', '#FF00FF', '#800080']
            edm_observations = list(edm_observations.values())
            n_rpt_shots = max([len(e['grp_Bay']) for e in edm_observations])
            for o, colour in zip(edm_observations, back_colours):
                while len(o['grp_Bay'])<n_rpt_shots:
                    o['grp_Bay'].append('')
                for uc in o['uc_budget'].values():
                    uc['chart_colour'] = colour
                    if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                        uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
                for uc in o['uc_sources']:
                    if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                        uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
                o['uc_sources']=sorted(o['uc_sources'], key=lambda x: x['group_verbose'])
                o['uc_budget'] = OrderedDict(sorted(o['uc_budget'].items()))
            print(edm_observations[0])
            context = {'pillar_survey':pillar_survey,
                       'calib':calib,
                       'baseline': baseline,
                       'ISO_test':ISO_test,
                       'edm_observations': edm_observations,
                       'report_notes': report_notes,
                       'Check_Errors':Check_Errors,
                       'hidden':[]}
            return render(request, 'edm_calibration/calibrate_report.html', context)
    
# def calibrate1(request, id):
#     if 'calibrate_e' in request.session:
#         ini_data = request.session['calibrate_e']
#     else:
#         ini_data = {'computation_date':date.today().isoformat()}
    
#     if request.method == 'POST':
#         form = CalibrateEdmForm1(request.POST or None)
#         if form.is_valid():
#             frm=cache_format(form)
#             ini_data.update(frm)
#             request.session['calibrate_e'] = ini_data
#             return HttpResponseRedirect('/edm_calibration/calibrate2')
#     else:
#         print('Form not Valid')
#         form = CalibrateEdmForm1(initial=ini_data)
#     return render(request, 'edm_calibration/calibrate.html', {
#                 'Header':'Calibrate your Electronic Distance Instrumentation (EDMI)',
#                 'Page': 'Page 1 of 5',
#                 'BackBtn': False,
#                 'form': form})

# def calibrate2(request):
#     if 'calibrate_e' in request.session:
#         ini_data = request.session['calibrate_e']
#     else:
#         ini_data={}
        
#     if request.method == 'POST':
#         form = CalibrateEdmForm2(request.POST or None)
#         if form.is_valid():
#             frm=cache_format(form)
#             ini_data.update(frm)
#             request.session['calibrate_e'] = ini_data
#             return HttpResponseRedirect('/edm_calibration/calibrate3')
#     else:
#         print('Form not Valid')
#         form = CalibrateEdmForm2(initial=ini_data)
#     return render(request, 'edm_calibration/calibrate.html', {
#                 'Header':'Instrumentation',
#                 'Page': 'Page 2 of 5',
#                 'BackBtn': 'calibrate1',
#                 'form': form})


# def calibrate3(request):
#     if 'calibrate_e' in request.session:
#         ini_data = request.session['calibrate_e']
#     else:
#         ini_data={}
    
#     if not 'outlier_criterion' in ini_data.keys():
#         ini_data['outlier_criterion']=2.0
    
#     if request.method == 'POST':
#         form = CalibrateEdmForm3(request.POST or None, request.FILES)
#         if form.is_valid():
#             calibrate_e = {}
#             calib = {}
#             baseline={}
#             instruments={}
#             uc_budget = {}
#             frm=form.cleaned_data
#             print(frm)
            
#             edm_clms=['from_pillar',
#         		      'to_pillar',
#         		      'inst_ht',
#         		      'tgt_ht',
#         		      'raw_slope_dist',
#         		      'raw_temperature',
#         		      'raw_pressure',
#         		      'raw_humidity']
#             raw_edm_obs = csv2dict(frm['edm_file'],edm_clms)

#             frm=cache_format(form)
#             ini_data.update(frm)
#             request.session['calibrate_e'] = ini_data
            
#             #----------------- Query appropriate instruments and calibrations -----------------#
#             instruments = Instruments_qry(ini_data)
#             calib = Calibrations_qry(ini_data)
            
#             #----------------- Query Baseline data -----------------#  
#             baseline = baseline_qry(ini_data)
            
#             #----------------- Query the default Uncertainty -----------------#
#             uc_budget = uncertainty_qry(ini_data)
#             uc_budget['sources'] = add_calib_uc(uc_budget['sources'], 
#                                                        calib,
#                                                        instruments,
#                                                        ini_data['survey_date'])

#             for o in raw_edm_obs.values():
#                 #----------------- Instrument Corrections -----------------#
#                 o['Temp'],c = apply_calib(o['raw_temperature'],
#                                             ini_data['thermo_calib_applied'], 
#                                             calib['them'])
#                 o['Pres'],c = apply_calib(o['raw_pressure'],
#                                             ini_data['baro_calib_applied'],
#                                             calib['baro'])
#                 o['Humid'],c = apply_calib(o['raw_humidity'],
#                                             ini_data['hygro_calib_applied'],
#                                             calib['hygro'])
#                 o = (edm_mets_correction(o, 
#                                            instruments['edm'],
#                                            ini_data['mets_applied']))
                
#                 o['slope_dist'] = (float(o['raw_slope_dist'] )
#                                              + o['Mets_Correction'])
#                 o['Bay'] = o['from_pillar'] + ' - ' + o['to_pillar']
            
#             edm_observations = group_list(raw_edm_obs.values(),
#                                             group_by='Bay',
#                                             labels_list=['from_pillar',
#                                                          'to_pillar'],
#                                             avg_list=['inst_ht',
#                                                       'tgt_ht',
#                                                       'Temp',
#                                                       'Pres',
#                                                       'Humid',
#                                                       'Mets_Correction',
#                                                       'raw_slope_dist',
#                                                       'slope_dist',],
#                                             std_list=['slope_dist'])
            
#             edm_trend = edm_std_function(edm_observations, 
#                                          uc_budget['stddev_0_adj'])           #y = Ax + B
                           
#             matrix_A = []
#             matrix_x = []
#             matrix_P = []
#             for i, o in enumerate(edm_observations.values()):
#                 o['id']=str(i+1)
#                 o = (offset_slope_correction(o,
#                                           baseline['certifed_dist'],
#                                           baseline['certifed_dist'],
#                                           baseline['d_radius']))
                  
#                 o['Reduced_distance'] = (o['slope_dist'] 
#                                         + o['Offset_Correction']
#                                         + o['Slope_Correction'])

#                 #----------------- Calculate Uncertainties -----------------#
#                 o['uc_sources'] = add_certified_dist_uc(o, 
#                                                   uc_budget['sources'],
#                                                   baseline['std_dev_matrix'],
#                                                   baseline['calibrated_baseline'].degrees_of_freedom)
                
#                 o['uc_sources'] = add_surveyed_uc(o, edm_trend, 
#                                                   uc_budget['sources'],
#                                                   baseline['certifed_dist'])
                      
#                 o['uc_budget'] = refline_std_dev(o, 
#                                                 baseline['certifed_dist'], 
#                                                 instruments['edm'])
                  
#                 o['uc_combined'] = sum_uc_budget(o['uc_budget'])
                
#                 #----------------- Least Squares -----------------#
#                 #----------------- 6 Parameter least squares adjustment -----------------#
#                 d_term = ((2*pi*o['Reduced_distance'])
#                           / instruments['edm'].edm_specs.unit_length)
#                 a_row = [1,
#                          o['Reduced_distance'],
#                          sin(d_term),
#                          cos(d_term),
#                          sin(2*d_term),
#                          cos(2*d_term)]
#                 matrix_A.append(a_row)
                  
#                 frm = baseline['certifed_dist'][o['from_pillar']]['distance']
#                 to = baseline['certifed_dist'][o['to_pillar']]['distance']
#                 matrix_x.append(abs(float(to) - float(frm))
#                                 -o['Reduced_distance'])
                  
#                 P_row = [0]*len(edm_observations)
#                 P_row[len(matrix_x)-1] = (1/
#                                      o['uc_combined']['std_dev']**2)
#                 matrix_P.append(P_row)
                  
#             matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)
#             # Check t-student test results to determine if cyclic errors are significant
#             if False not in [t['t_test'] for t in matrix_y[2:]]:
#                 matrix_A=[[a[0], a[1]] for a in matrix_A]
#                 matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)
            
#             for o in edm_observations.values():
#                 o['residual'] = residuals[o['id']]['residual']
#                 o['std_residual'] = residuals[o['id']]['std_residual']
            
#             ISO_test=[]
#             ISO_test.append(ISO_test_a(instruments,
#                                        chi_test,
#                                        [{'distance':50},
#                                         {'distance':100},
#                                         {'distance':200},
#                                         {'distance':400}, 
#                                         {'distance':600}]))
#             ISO_test.append(ISO_test_c(matrix_y[0]['value'],
#                                        matrix_y[0]['std_dev'],
#                                        chi_test))

#             #Prepare the context for the template
#             edm_observations = list(edm_observations.values())
#             context = {'frm':ini_data,
#                        'instruments':instruments,
#                        'calib':calib,
#                        # 'residual_chart':residual_chart,
#                        'baseline': baseline,
#                        'ISO_test':ISO_test,
#                        'edm_observations': edm_observations,
#                        # 'Check_Errors':Check_Errors
#                        }
            
#             return render(request, 'baseline_calibration/calibrate_report.html', context)
#     else:
#         print('Form not Valid')
#         form = CalibrateEdmForm3(initial=ini_data)
#     return render(request, 'edm_calibration/calibrate.html', {'Header':'File Uploads',
#   	                                                             'Page': 'Page 3 of 5',
#   	                                                             'BackBtn': 'calibrate2',
#   	                                                             'form': form})
    
# @login_required(login_url="/accounts/login")
# def calibrate(request):
#     ini_data = {'computation_date':date.today().isoformat()}
#     form = CalibrateEdmForm(request.POST or None,
#                             user=request.user,
#                             initial=ini_data)    
    
#     if request.method == 'POST':
#         form = CalibrateEdmForm(request.POST, request.FILES, user=request.user)
#         if form.is_valid():
#             frm=form.cleaned_data
#             calib = {}
#             baseline={}
#             instruments={}
#             uc_budget = {}
#             edm_clms=['from_pillar',
#         		      'to_pillar',
#         		      'inst_ht',
#         		      'tgt_ht',
#         		      'raw_slope_dist',
#         		      'raw_temperature',
#         		      'raw_pressure',
#         		      'raw_humidity']
#             raw_edm_obs = csv2dict(frm['edm_file'],edm_clms)
                    
#             #----------------- Query appropriate instruments and calibrations -----------------#
#             instruments = Instruments_qry(frm)
#             calib = Calibrations_qry(frm)
            
#             #----------------- Query Baseline data -----------------#  
#             baseline = baseline_qry(frm)
            
#             #----------------- Query the default Uncertainty -----------------#
#             uc_budget = uncertainty_qry(frm)
#             uc_budget['sources'] = add_calib_uc(uc_budget['sources'], 
#                                                        calib,
#                                                        instruments,
#                                                        frm['survey_date'])
            
#             Check_Errors = validate_survey(frm=frm, 
#                                            baseline=baseline,
#                                            instruments=instruments,
#                                            calibrations=calib,
#                                            raw_edm_obs=raw_edm_obs)
            
#             if len(Check_Errors['Errors']) > 0:
#                msg="<h4>The following errors have been detected:</h4>"
#                msg+="<p>"
#                for e in Check_Errors['Errors']:
#                   msg+="   "+ e +"<br>"
#                msg+="</p>"
#                msg+="<h4>The following warnings have been detected:</h4>"
#                msg+="<p>"
#                for w in Check_Errors['Warnings']:
#                   msg+="   "+ w +"<br>"
#                msg+="</p>"
#                return HttpResponse(msg)
#             else:
#                form.save()
#             return redirect('edm_calibration:view_edm_observations')
        
#     headers = {'page0':'Pillar Survey Information',
#                'page1': 'Instrumentation',
#                'page2': 'Error Budget and File Uploads',}
#     return render(request, 'edm_calibration/calibrate.html', {
#             'Headers': headers,
#             'Cancelurl': 'edm_calibration_home',
#             'form': form})

