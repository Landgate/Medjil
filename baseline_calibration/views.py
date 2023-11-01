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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory, modelformset_factory
from django.forms.models import model_to_dict
from django.http import QueryDict
from django.template.loader import render_to_string
from collections import OrderedDict
from django.db.models import Q

from datetime import date
from math import sqrt
import numpy as np
from statistics import mean

from .forms import (
    PillarSurveyForm,
    UploadSurveyFiles,
    ChangeSurveyFiles,
    EDM_ObservationForm,
    Certified_DistanceForm,
    Std_Deviation_MatrixForm,
    PillarSurveyUpdateForm,
    Uncertainty_BudgetForm,
    Uncertainty_Budget_SourceForm,
    AccreditationForm,
    PillarSurveyApprovalsForm)
from .models import (
    Pillar_Survey,
    EDM_Observation,
    Level_Observation,
    Accreditation,
    Uncertainty_Budget,
    Uncertainty_Budget_Source,
    Certified_Distance,
    Std_Deviation_Matrix)
from geodepy.survey import radiations
from common_func.Convert import (
    csv2dict,
    Calibrations_qry, 
    baseline_qry)
from common_func.SurveyReductions import (
    validate_survey,
    apply_calib,
    get_mets_params,
    edm_mets_correction,
    adjust_alignment_survey,
    report_notes_qry,
    uncertainty_qry,
    add_calib_uc,
    reduce_sets_of_obs, 
    edm_std_function, 
    offset_slope_correction, 
    add_surveyed_uc, 
    refline_std_dev, 
    sum_uc_budget,
    get_delta_os,
    add_typeB)
from medjil.settings import *
from common_func.LeastSquares import (
    LSA,
    ISO_test_b,
    ISO_test_c)


@login_required(login_url="/accounts/login") 
def calibration_home(request):
    sqlstring = ("""
        SELECT baseline_calibration_pillar_survey.id,
        survey_date, 
        observer, 
        job_number,
        accredited_company_id,
        baseline_calibration_certified_distance.modified_on
        FROM (baseline_calibration_pillar_survey 
        LEFT JOIN baseline_calibration_accreditation 
        ON  baseline_calibration_accreditation.id = accreditation_id)
        LEFT OUTER JOIN baseline_calibration_certified_distance
        ON baseline_calibration_pillar_survey.id = pillar_survey_id
        WHERE (distance = 0 or distance ISNULL)
        ORDER BY baseline_id ASC, survey_date DESC""")
    if request.user.is_superuser:
        pillar_surveys = Pillar_Survey.objects.raw(sqlstring)
    else:
        sqlstring.replace('ORDER BY ', 'AND accredited_company_id ='
                          + str(request.user.company.id) +' ORDER BY ')
        pillar_surveys = Pillar_Survey.objects.raw(sqlstring)
        
    context = {
        'pillar_surveys': pillar_surveys}
    
    return render(request, 'baseline_calibration/baseline_calibration_home.html', context)


@login_required(login_url="/accounts/login") 
def pillar_survey_del(request, id):
    delete_pillar_survey = Pillar_Survey.objects.get(id=id)
    delete_pillar_survey.delete()
    
    return redirect('baseline_calibration:calibration_home')


@login_required(login_url="/accounts/login") 
def calibrate1(request, id):
    # GET or invalid goto form for Pillar Survey
    # POST will commit form and redirect to Calibrate2
    # if id==None this is a new pillar survey.
    if id == 'None':
        qs=''
        ini_data = {
            'computation_date':date.today().isoformat(),
            'accreditation': Accreditation.objects.filter(
                valid_from_date__lte = date.today().isoformat(),
                valid_to_date__gte = date.today().isoformat(),
                accredited_company = request.user.company).order_by(
                    '-valid_from_date').first()}
    
        pillar_survey = PillarSurveyForm(request.POST or None,
                                         request.FILES or None,
                                         user=request.user,
                                         initial=ini_data)
        upload_survey_files = UploadSurveyFiles(request.POST or None,
                                                request.FILES or None)
    else:
        qs = get_object_or_404(Pillar_Survey, id=id)
        qs.survey_date = qs.survey_date.isoformat()
        qs.computation_date = qs.computation_date.isoformat()
        pillar_survey = PillarSurveyForm(request.POST or None,
                                         request.FILES or None,
                                         instance = qs,
                                         user = request.user)
        upload_survey_files = ChangeSurveyFiles(request.POST or None,
                                         request.FILES or None)
    
    if pillar_survey.is_valid() and upload_survey_files.is_valid():
        frm = pillar_survey.cleaned_data
        survey_files = upload_survey_files.cleaned_data
        
        # read new files or read raw data from database
        if survey_files['edm_file']:
            raw_edm_obs = csv2dict(survey_files['edm_file'])
            for v in raw_edm_obs.values():
                v['use_for_alignment'] = True 
                v['use_for_distance'] = True
        else:
            qs = EDM_Observation.objects.filter(pillar_survey__pk=id)
            raw_edm_obs = {}
            for o in qs:
                dct = model_to_dict(o)
                dct['from_pillar'] = o.from_pillar.name
                dct['to_pillar'] = o.to_pillar.name
                raw_edm_obs[str(o.id)] = dct
        
        if survey_files['lvl_file']:
            raw_lvl_obs = csv2dict(survey_files['lvl_file'],key_names=0)
        else:            
            qs = Level_Observation.objects.filter(pillar_survey__pk=id)
            raw_lvl_obs = {}
            for o in qs:
                dct = model_to_dict(o)
                dct['pillar'] = o.pillar.name
                dct['std_dev'] = dct['rl_standard_deviation']
                del dct['rl_standard_deviation']
                raw_lvl_obs[o.pillar.name] = dct
        
    #----------------- Query related fields -----------------#
        calib = Calibrations_qry(frm)
        baseline = baseline_qry(frm)
        
        if survey_files['edm_file'] or survey_files['lvl_file']:                            
            Check_Errors = validate_survey(pillar_survey=frm,
                                        baseline=baseline,
                                        calibrations=calib,
                                        raw_edm_obs=raw_edm_obs,
                                        raw_lvl_obs=raw_lvl_obs)
            
            if len(Check_Errors['Errors']) > 0:
                return render(request, 'baseline_calibration/errors_report.html', 
                              {'Check_Errors':Check_Errors})
        
        ps_instance = pillar_survey.save()
        # Commit all the edm raw observations
        if survey_files['edm_file']:
            for o in raw_edm_obs.values():
                from_pillar_id = baseline['pillars'].get(name=o['from_pillar'])
                to_pillar_id = baseline['pillars'].get(name=o['to_pillar'])
        
                EDM_Observation.objects.create(
                    pillar_survey=ps_instance,
                    from_pillar=from_pillar_id,
                    to_pillar=to_pillar_id,
                    inst_ht=o['inst_ht'],
                    tgt_ht=o['tgt_ht'],
                    hz_direction=o['hz_direction'],
                    raw_slope_dist=o['raw_slope_dist'],
                    raw_temperature=o['raw_temperature'],
                    raw_pressure=o['raw_pressure'],
                    raw_humidity=o['raw_humidity'],
                    use_for_alignment=o['use_for_alignment'],
                    use_for_distance=o['use_for_distance'],
                )
        # Commit all the reduced levels
        if survey_files['lvl_file']:
            for l in raw_lvl_obs.values():
                pillar_id = baseline['pillars'].get(name=l['pillar'])

                Level_Observation.objects.create(
                    pillar_survey=ps_instance,
                    pillar=pillar_id,
                    reduced_level=l['reduced_level'],
                    rl_standard_deviation=l['std_dev']
                )
        
        return redirect('baseline_calibration:calibrate2', id=ps_instance.pk)
            
    headers = {'page0':'Calibrate the Baseline',
                'page1': 'Instrumentation',
                'page2': 'Corrections / Calibrations Applied to Instruments',
                'page3': 'Error Budget and File Uploads',}
    
    return render(request, 'baseline_calibration/calibrate.html', {
            'Headers': headers,
            'form': pillar_survey,
            'qs':qs,
            'survey_files':upload_survey_files})


@login_required(login_url="/accounts/login") 
def calibrate2(request,id):
    # If this is a get request:
    #     select or deselect the edm observations for the calibration and offset
    # If this is a post request: and edm_obs_formset.is_valid
    #     calculate and generate the report. 
    # If this is a post request: cd_formset.is_valid() and sdev_mat_formset.is_valid() and pillar_survey_update.is_valid()
    #     commit the calibration and return to home page.
    
    #----------------- Query site, surveys, instruments and calibrations -----------------#
    # Get the pillar_survey in dict like cleaned form data
    ps_qs = Pillar_Survey.objects.get(id=id)
    query_dict = QueryDict('', mutable=True)
    query_dict.update(model_to_dict(ps_qs))
    pillar_survey_form = PillarSurveyForm(query_dict, user=request.user)
    pillar_survey_form.is_valid()
    pillar_survey = pillar_survey_form.cleaned_data
    pillar_survey.update({'pk':id})
    pillar_survey.update({'variance':query_dict['variance']})
        
    # Get the raw_edm_obs and the raw_lvl_obs in dict like cleaned form data
    formset = modelformset_factory(EDM_Observation,
                            form=EDM_ObservationForm, extra=0)
    qs = EDM_Observation.objects.filter(pillar_survey__pk=id)
    edm_obs_formset = formset(request.POST or None, queryset=qs)
    raw_edm_obs = {}
    for o in qs:
        dct = model_to_dict(o)
        dct['from_pillar'] = o.from_pillar.name
        dct['to_pillar'] = o.to_pillar.name
        raw_edm_obs[str(o.id)] = dct

    qs = Level_Observation.objects.filter(pillar_survey__pk=id)
    raw_lvl_obs = {}
    for o in qs:
        dct = model_to_dict(o)
        dct['pillar'] = o.pillar.name
        dct['std_dev'] = dct['rl_standard_deviation']
        del dct['rl_standard_deviation']
        raw_lvl_obs[o.pillar.name] = dct
    
    # Create formsets and forms
    cd_formset = formset_factory(Certified_DistanceForm, extra=0) 
    sdev_mat_formset = formset_factory(Std_Deviation_MatrixForm, extra=0)
    pillar_survey_update = PillarSurveyUpdateForm(
        request.POST or None, instance=ps_qs)
    ps_approvals = PillarSurveyApprovalsForm(
        request.POST or None, instance=ps_qs)
    
    calib = {}
    baseline={}
    uc_budget = {}
    calib = Calibrations_qry(pillar_survey)
    baseline = baseline_qry(pillar_survey)
    
    # Set the C and D terms for atmospheric corrections
    get_mets_params(
        pillar_survey['edm'], 
        pillar_survey['mets_applied'])
    
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
        c, o['Calibration_Correction'] = apply_calib(
            o['raw_slope_dist'],
            pillar_survey['edmi_calib_applied'],
            calib['edmi'].first,
            unit_length = pillar_survey['edm'].edm_specs.unit_length)
        o = edm_mets_correction(o, 
                                pillar_survey['edm'],
                                pillar_survey['mets_applied'],
                                pillar_survey['co2_content'])
        
        o['slope_dist'] = (float(o['raw_slope_dist'] )
                           + o['Calibration_Correction']
                           + o['Mets_Correction'])
        
        # Calculate the Est and Nth for all in raw'
        o['Bay']= o['from_pillar'] + ' - ' + o['to_pillar']
        ht_diff = (
            float(raw_lvl_obs[o['to_pillar']]['reduced_level'])
            - float(raw_lvl_obs[o['from_pillar']]['reduced_level']))
        hz_dist = sqrt(
            ht_diff**2 +
            (float(o['slope_dist']))**2)
        o['Est'], o['Nth'] = radiations(
            0, 0,
            float(o['hz_direction']),
            hz_dist)
        
    if request.method == 'GET':
        # Prepare Page 5 of 5
        alignment_survey = adjust_alignment_survey(
            raw_edm_obs, baseline['pillars'])        
        
        formset = zip(edm_obs_formset,raw_edm_obs.values())
        
        return render(request, 'baseline_calibration/edm_rawdata.html', 
                      {'Page': 'Page 5 of 5',
                       'id': id,
                       'edm_obs_formset':edm_obs_formset,
                       'pillar_survey': pillar_survey,
                       'formset': formset})
    else:
        # This is a POST request
        if edm_obs_formset.is_valid():
            # create signiture block
            ps_approvals = PillarSurveyApprovalsForm(instance=ps_qs)
            # Apply a mask to the raw observations
            # - calculate, check errors and render report
            edm_obs_formset.save()
            for form in edm_obs_formset:
                frm =form.cleaned_data
                raw_edm_obs[str(frm['id'].pk)]['use_for_distance']=frm['use_for_distance']
                raw_edm_obs[str(frm['id'].pk)]['use_for_alignment']=frm['use_for_alignment']
            
        Check_Errors = validate_survey(pillar_survey=pillar_survey,
                                    baseline=baseline,
                                    calibrations=calib,
                                    raw_edm_obs=raw_edm_obs,
                                    raw_lvl_obs=raw_lvl_obs)
        if len(Check_Errors['Errors']) > 0:
           return render(request, 'baseline_calibration/errors_report.html', 
                         {'Check_Errors':Check_Errors})
           
        if edm_obs_formset.is_valid() or not ps_approvals.is_valid():
            #----------------- Query related data -----------------#
            report_notes = report_notes_qry(
                company=request.user.company, report_type='B')                
            uc_budget = uncertainty_qry(pillar_survey)
            uc_budget['sources'] = add_calib_uc(uc_budget['sources'], 
                                                calib,
                                                pillar_survey)
           
            alignment_survey = adjust_alignment_survey(raw_edm_obs,
                                                      baseline['pillars'])
            for k, p in alignment_survey.items():
                p['reduced_level'] = float(raw_lvl_obs[k]['reduced_level'])
                p['rl_uncertainty'] = float(raw_lvl_obs[k]['std_dev'])*2
                p['k_rl_uncertainty'] = 2
            edm_observations = reduce_sets_of_obs(raw_edm_obs)
            
            edm_trend = edm_std_function(edm_observations,
                                         uc_budget['stddev_0_adj'])           #y = Ax + B
            
            pillars = [p.name for p in baseline['pillars']]
               
            matrix_A = []
            matrix_x = []
            matrix_P = []
            for i, o in enumerate(edm_observations.values()):
                o = offset_slope_correction(o,
                                          raw_lvl_obs,
                                          alignment_survey,
                                          baseline['d_radius'])
                  
                o['Reduced_distance'] = (o['slope_dist'] 
                                        + o['Offset_Correction']
                                        + o['Slope_Correction'])
    
                #----------------- Calculate Uncertainties -----------------#
                o['uc_sources'] = add_surveyed_uc(o, edm_trend, 
                                                  uc_budget['sources'],
                                                  alignment_survey)
                      
                o['uc_budget'] = refline_std_dev(o, 
                                                 alignment_survey,
                                                 pillar_survey['edm'])
                  
                o['uc_combined'] = sum_uc_budget(o['uc_budget'])
    
                #----------------- Least Squares -----------------#
                #Build the design matrix 'A' (ISO 17123-4:2012 eq.11)
                o['id']= str(i+1)
                A_row = [0]*len(alignment_survey)
                A_row[len(alignment_survey)-1] = -1
                bay = [pillars.index(o['from_pillar']),
                         pillars.index(o['to_pillar'])]
                A_row[min(bay)-1] = -1
                A_row[max(bay)-1] = 1
                matrix_A.append(A_row)
                  
                matrix_x.append(o['Reduced_distance'])
                  
                P_row = [0]*len(edm_observations)
                P_row[len(matrix_x)-1] = (1/
                                     o['uc_combined']['std_dev']**2)
                matrix_P.append(P_row)
                  
            matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)
            
            for o in edm_observations.values():
                o['residual'] = residuals[o['id']]['residual']
                o['std_residual'] = residuals[o['id']]['std_residual']
    
            ISO_test=[]
            if baseline['history'].count() > 1:
                prev=baseline['history'].last().pillar_survey
                ISO_test.append(ISO_test_b({'dof':prev.degrees_of_freedom,
                                            'Variance': prev.variance},
                                            chi_test))
            ISO_test.append(ISO_test_c(matrix_y[-1]['value'],
                                       matrix_y[-1]['std_dev'],
                                       chi_test))
            
            #-------------- Extract pillar to pillar uncertainties from VCV---------------#
            # Formula 6.10 (6.13) - Adjustment Computation (Ghilani) 4th Edition
            vcv_A = []
            bay = []
            for i0, p0 in enumerate(pillars[:-1]):
                for p1 in pillars[i0+1:]:
                    i1 = pillars.index(p1)
                    A_row = [0]*(len(pillars))
                    if i0!=0: A_row[i0-1] = -1
                    A_row[i1-1] = 1
                    
                    bay.append(p0+' - '+ p1)
                    vcv_A.append(A_row)
            
            vcv_A = np.array(vcv_A, dtype=object)
            sigma_vv = vcv_A @ vcv_matrix @ vcv_A.T
            
            # populate hidden forms to hide and save after commit (form Submit)
            ini_data=[]
            for b, vv in zip(bay, np.diagonal(sigma_vv)):
                p0, p1 = b.split(' - ')
                ini_data.append({'pillar_survey':id,
                                 'from_pillar':baseline['pillars'].get(name=p0),
                                 'to_pillar':baseline['pillars'].get(name=p1),
                                 'std_uncertainty':sqrt(vv)})
            
            sdev_mat_formset = sdev_mat_formset(initial=ini_data, prefix='sdev_mat')
            # -- end populate sdev_mat_formset -- #
            
            #----------------- Extract the certified distances from LSA results -----------------#
            # Calculate the average temp and pressure for survey #
            certified_dists={}
            avg_t = mean([float(o['Temp']) for o in edm_observations.values()])
            avg_p = mean([float(o['Pres']) for o in edm_observations.values()])
            avg_h = mean([float(o['Humid']) for o in edm_observations.values()])
            ini_data =[]
            for i, (p, d) in enumerate(zip(pillars[1:], matrix_y[:-1])):
                cd={}
                ini_cd={}
                cd['pillar_survey'] = id
                cd['date'] = pillar_survey['survey_date'].isoformat()
                cd['slope_dist'] = d['value']
                cd['Reduced_distance'] = d['value']
                cd['Temp'] = avg_t
                cd['Pres'] = avg_p
                cd['Humid'] = avg_h
                cd['to_pillar'] = p
                cd['from_pillar'] = pillars[0]
                cd['delta_os'] = get_delta_os(alignment_survey,cd)
    
                #--------------------- Add Type B --------------------------------------#
                cd['uc_sources'] = add_surveyed_uc(cd, edm_trend, 
                                                uc_budget['sources'],
                                                alignment_survey)
                cd['uc_sources'] = add_typeB(cd['uc_sources'], d, matrix_y, chi_test['dof'])
    
                cd['uc_budget'] = refline_std_dev(cd, 
                                                    alignment_survey,
                                                    pillar_survey['edm'])
                cd['uc_combined'] = sum_uc_budget(cd['uc_budget'])
                certified_dists[p] = cd
                
                # apply LUM if neccessary
                lum = ((pillar_survey['accreditation'].LUM_constant +
                       pillar_survey['accreditation'].LUM_ppm * d['value'] * 10**-6)
                       * 0.001 )
                if pillar_survey['apply_lum'] and cd['uc_combined']['uc95'] < lum:
                    cd['uc_combined']['uc95'] = lum
                    cd['uc_combined']['k'] = 2
                    cd['lum_adopted'] = True
                    if not 'some_lum_adopted' in pillar_survey.keys():
                        pillar_survey['some_lum_adopted'] = True
                        report_notes.append(
                            'The uncertainty of some of the certified distances '
                            'have been smaller than the companies accredited '
                            'least uncertainty of measurement (LUM). In these cases '
                            'the LUM has been published in this report.')
                
                # populate a hidden formset to save after commit (form Submit)
                ini_cd['pillar_survey'] = id
                ini_cd['from_pillar'] = baseline['pillars'].get(name=pillars[0])
                ini_cd['to_pillar'] = baseline['pillars'].get(name=p)
                ini_cd['distance'] = d['value']
                ini_cd['a_uncertainty'] = cd['uc_budget']['07']['ui95']
                ini_cd['k_a_uncertainty'] = cd['uc_budget']['07']['k']
                ini_cd['combined_uncertainty'] = cd['uc_combined']['uc95']
                ini_cd['k_combined_uncertainty'] = cd['uc_combined']['k']
                ini_cd['offset'] = cd['delta_os']
                ini_cd['os_uncertainty'] = (cd['uc_budget']['11']['std_dev'] *
                                            cd['uc_budget']['11']['k'])
                ini_cd['k_os_uncertainty'] =  cd['uc_budget']['11']['k']
                ini_cd['reduced_level'] = float(raw_lvl_obs[p]['reduced_level'])
                ini_cd['rl_uncertainty'] = (cd['uc_budget']['10']['std_dev'] *
                                            cd['uc_budget']['10']['k'])
                ini_cd['k_rl_uncertainty'] = cd['uc_budget']['10']['k']
                ini_data.append(ini_cd)
                # add an extra for the first pillar
                if i==0:
                    ini_cd0 = ini_cd.copy()
                    ini_cd0['to_pillar'] = baseline['pillars'].get(name=pillars[0])
                    ini_cd0['distance'] = 0
                    ini_cd0['offset'] = 0
                    ini_cd0['reduced_level'] = float(raw_lvl_obs[pillars[0]]['reduced_level'])
                    ini_cd0['rl_uncertainty'] = float(raw_lvl_obs[pillars[0]]['std_dev'])
                    ini_data.insert(0,ini_cd0)                
            cd_formset = cd_formset(initial=ini_data)
            # -- end populate cd_formset -- #
            
            #Prepare the context for the template
            od = OrderedDict(sorted(alignment_survey.items()))
            alignment_survey = list(od.values())
            certified_dists = list(certified_dists.values())
            
            back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                            '#00FF00', '#008000', '#00FFFF', '#008080', 
                            '#0000FF', '#000080', '#FF00FF', '#800080']
            for cd, colour in zip(certified_dists, back_colours):
                for uc in cd['uc_budget'].values():
                    uc['chart_colour'] = colour
                    if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                        uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
                for uc in cd['uc_sources']:
                    if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                        uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
                cd['uc_sources']=sorted(cd['uc_sources'], key=lambda x: x['group_verbose'])
                cd['uc_budget'] = OrderedDict(sorted(cd['uc_budget'].items()))
                
            edm_observations = list(edm_observations.values())
            n_rpt_shots = max([len(e['grp_Bay']) for e in edm_observations])
            for o in edm_observations:
                while len(o['grp_Bay'])<n_rpt_shots:
                    o['grp_Bay'].append('')
    
            calib['edmi_drift']['xyValues'] = [
                    {'x':c['calibration_date'].isoformat()[:10],
                    'y':c['scale_correction_factor'],
                    'zpc':c['zero_point_correction']} 
                    for c in calib['edmi'].values()]
    
            #prepare the data for the comparison to history graph
            ini_surv={}
            surveys={}         
            for cd, colour in zip(baseline['history'],back_colours):                
                if cd.from_pillar.name != cd.to_pillar.name:
                    survey = cd.pillar_survey.pk
                    if not survey in surveys.keys():
                        dte = cd.pillar_survey.survey_date.isoformat()
                        surveys[survey] = {'date':dte, 
                                           'bays':[]}
                    #find the initial values
                    if not cd.to_pillar.name in ini_surv:
                        ini_surv[cd.to_pillar.name]=float(cd.distance)
                    
                    surveys[survey]['bays'].append(
                        {'to_pillar':cd.to_pillar.name,
                         'diff_to_initial': ini_surv[cd.to_pillar.name]-float(cd.distance),
                         'chart_colour':colour})
            
            surveys[id] = {'date':pillar_survey['survey_date'].isoformat(),
                            'bays':[]}
            for cd in certified_dists:
                diff = 0
                if baseline['history']: 
                    diff = ini_surv[cd['to_pillar']]-cd['Reduced_distance']
                surveys[id]['bays'].append(
                    {'to_pillar':cd['to_pillar'],
                     'diff_to_initial': diff,
                     'chart_colour':'#808080'}
                    )
            baseline['history'] = surveys
            baseline['pillar_meta'] = []
            for p in baseline['pillars']:
                baseline['pillar_meta'].append(model_to_dict(p))
                baseline['pillar_meta'][-1]['reduced_level'] = (
                    float(raw_lvl_obs[p.name]['reduced_level']))
            
            context = {'pillar_survey':pillar_survey,
                       'calib':calib,
                       'baseline': baseline,
                       'certified_dists': certified_dists,
                       'chi_test':chi_test,
                       'ISO_test':ISO_test,
                       'alignment_survey': alignment_survey,
                       'edm_observations': edm_observations,
                       'report_notes': report_notes,
                       'Check_Errors':Check_Errors}
            
            html_report = render_to_string(
                'baseline_calibration/calibrate_report.html', context)
            
            # create update for pillar survey processing
            ini_data=[]
            n = len(matrix_y)-1
            ini_data = {'zero_point_correction': matrix_y[n]['value'],
                        'zpc_uncertainty': matrix_y[n]['std_dev'],
                        'degrees_of_freedom': chi_test['dof'],
                        'variance': chi_test['Variance'],
                        'html_report': html_report
                        }
            
            pillar_survey_update = PillarSurveyUpdateForm(initial=ini_data)            
            # -- end populating the pillar_survey_update -- #            
            
            context = {'pillar_survey': pillar_survey,
                       'html_report': html_report,
                       'ps_approvals':ps_approvals,
                       'hidden':[cd_formset,
                                 sdev_mat_formset,
                                 pillar_survey_update]}
            return render(request, 'baseline_calibration/display_report.html', context)
        
        #----------------------- code for commiting the calibration and returning to home page -----------------------------#        
        cd_formset = cd_formset(request.POST)
        sdev_mat_formset = sdev_mat_formset(request.POST, prefix='sdev_mat')
        #check to see if distances have been saved before and delete these from the database
        delete_cd = Certified_Distance.objects.filter(pillar_survey__pk=id)
        delete_cd.delete()
        delete_sdev_mat = Std_Deviation_Matrix.objects.filter(pillar_survey__pk=id)
        delete_sdev_mat.delete()
        if (cd_formset.is_valid() and
            sdev_mat_formset.is_valid() and
            pillar_survey_update.is_valid() and
            ps_approvals.is_valid()):
            
            pillar_survey_update.save()
            ps_approvals.save()
            
            for cd_form in cd_formset:
                cd_form.save()
                
            for sdev_mat_form in sdev_mat_formset:
                sdev_mat_form.save()
                
            return redirect('baseline_calibration:calibration_home')
        
        else:
            for e in cd_formset.errors:
                print(e)
            context = {'pillar_survey': pillar_survey,
                       'html_report': html_report,
                       'ps_approvals':ps_approvals,
                       'hidden':[cd_formset,
                                 sdev_mat_formset,
                                 pillar_survey_update]}
            
            return render(request, 'baseline_calibration/display_report.html', context)


@login_required(login_url="/accounts/login") 
def report(request, id):    
    # This uses the html report saved to the database to popluate the report
    # It also loads the approvals form that can be edited and saved.
    pillar_survey_qs = get_object_or_404(Pillar_Survey, id=id)
    ps_approvals = PillarSurveyApprovalsForm(
        request.POST or None, instance=pillar_survey_qs)
    if ps_approvals.is_valid():
        ps_approvals.save()
        return redirect('baseline_calibration:calibration_home')
    
    context = {'ps_approvals':ps_approvals,
               'html_report': pillar_survey_qs.html_report}
    return render(request, 'baseline_calibration/display_report.html', context)


@login_required(login_url="/accounts/login") 
def uc_budgets(request):
    if request.user.is_staff:
        uc_budget_list = Uncertainty_Budget.objects.all()
    else:
        uc_budget_list = Uncertainty_Budget.objects.filter(
            Q(name = 'Default', company__company_name = 'Landgate')|
            Q(company = request.user.company))
    
    context = {
        'uc_budget_list': uc_budget_list}
    
    return render(request, 'baseline_calibration/Uncertainty_budgets_list.html', context)


@login_required(login_url="/accounts/login") 
def uc_budget_edit(request, id=None):
    
    obj = get_object_or_404(Uncertainty_Budget, id=id)
    uc_budget = Uncertainty_BudgetForm(request.POST or None, instance=obj)
    uc_sources = modelformset_factory(Uncertainty_Budget_Source,
                            form=Uncertainty_Budget_SourceForm, extra=0)
    qs = Uncertainty_Budget_Source.objects.filter(
                            uncertainty_budget = id)
    formset = uc_sources(request.POST or None, queryset=qs)
    
    if all([uc_budget.is_valid(), formset.is_valid()]):
        uc_budget.save()
        new_sources_id=[]
        for uc_source in formset:
            new_sources_id.append(uc_source.instance.id)
            source = uc_source.save(commit=False)
            source.uncertainty_budget = uc_budget.instance
        formset.save()
        
        for orig_source in qs:
            if not orig_source.id in new_sources_id:
                orig_source.delete()
                 
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('baseline_calibration:uc_budgets')

    context = {}
    context['form'] = uc_budget
    context['formset'] = formset
    
    return render(request, 'baseline_calibration/uncertainty_budget_form.html', context)


@login_required(login_url="/accounts/login") 
def uc_budget_create(request):    
    if request.method == 'POST':
        uc_budget = Uncertainty_BudgetForm(request.POST, user=request.user)
        uc_sources = formset_factory(Uncertainty_Budget_SourceForm, extra=0)
        uc_sources = uc_sources(request.POST)
        if uc_budget.is_valid() and uc_sources.is_valid():
            uc_budget.save()
            for uc_source in uc_sources:
                f = uc_source.save(commit=False)
                f.uncertainty_budget = uc_budget.instance
                f.save()
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('baseline_calibration:uc_budgets')
    else:
        ini_budget={}
        ini_budget['std_dev_of_zero_adjustment'] = (
            Uncertainty_Budget.objects.get(
                        name = 'Default', 
                        company__company_name = 'Landgate')
                        .std_dev_of_zero_adjustment)
        ini_budget['company'] = request.user.company
        ini_sources = Uncertainty_Budget_Source.objects.filter(
                        uncertainty_budget__name = 'Default', 
                        uncertainty_budget__company__company_name = 'Landgate')
        
        uc_sources = formset_factory(Uncertainty_Budget_SourceForm, extra=0)
        uc_sources = uc_sources(initial=[vars(row) for row in ini_sources])
        
        uc_budget = Uncertainty_BudgetForm(initial=ini_budget, user=request.user)
    
    context = {}
    context['Header'] = 'Create Uncertainty Budget from Default'        
    context['form'] = uc_budget
    context['formset'] = uc_sources
    
    return render(request, 'baseline_calibration/uncertainty_budget_form.html', context)


@login_required(login_url="/accounts/login") 
def uc_budget_delete(request, id):
    if request.user.is_staff:
        delete_budget = Uncertainty_Budget.objects.get(id=id)
    else:
        delete_budget = Uncertainty_Budget.objects.get(
            id=id,
            accredited_company = request.user.company)
    delete_budget.delete()
    
    return redirect('baseline_calibration:uc_budgets')


@login_required(login_url="/accounts/login") 
def accreditations(request):
    if request.user.is_staff:
        accreditation_list = Accreditation.objects.all()
    else:
        accreditation_list = Accreditation.objects.filter(
            accredited_company = request.user.company)
    
    context = {
        'accreditation_list': accreditation_list}
    
    return render(request, 'baseline_calibration/Accreditation_list.html', context)


@login_required(login_url="/accounts/login") 
def accreditation_edit(request, id=None):
    context = {}
    # if id==None this is a new pillar survey.
    if id == 'None':
        ini ={'accredited_company': request.user.company}
        accreditation = AccreditationForm(request.POST or None,
                                          request.FILES or None,
                                          user=request.user,
                                          initial = ini)
        context['Header'] = 'Input Accreditation Details'
    else:
        obj = get_object_or_404(Accreditation, id=id)
        obj.valid_from_date = obj.valid_from_date.isoformat()
        obj.valid_to_date = obj.valid_to_date.isoformat()
        accreditation = AccreditationForm(request.POST or None,
                                          request.FILES or None,
                                          instance=obj)

        context['Header'] = 'Edit Accreditation Details'
    
    if accreditation.is_valid():
        accreditation.save()            
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('baseline_calibration:accreditations')
        
    context['form'] = accreditation
    
    return render(request, 'baseline_calibration/Accreditation_form.html', context)


@login_required(login_url="/accounts/login") 
def accreditation_delete(request, id):
    if request.user.is_staff:
        accreditation = Accreditation.objects.get(id=id)
    else:
        accreditation = Accreditation.objects.get(
            id=id,
            accredited_company = request.user.company)
    accreditation.delete()
    
    return redirect('baseline_calibration:accreditations')


