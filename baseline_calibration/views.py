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
from collections import OrderedDict
from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.forms import formset_factory, modelformset_factory
from django.forms.models import model_to_dict
from django.http import QueryDict
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
import json
from math import sqrt
from statistics import mean
import numpy as np

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
from common_func.validators import try_delete_protected


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
    # unless staff, only allow delete if record belongs to company
    if request.user.is_staff:
        delete_obj = Pillar_Survey.objects.get(id=id)
    else:
        delete_obj = Pillar_Survey.objects.get(
            id=id,
            accreditation__accredited_company = request.user.company)
    try_delete_protected(request, delete_obj)
    
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
        
        # Check for exceptions that will break the processing
        Check_Errors = validate_survey(pillar_survey=frm,
                                    baseline=baseline,
                                    calibrations=calib,
                                    raw_edm_obs=raw_edm_obs,
                                    raw_lvl_obs=raw_lvl_obs)
        
        if len(Check_Errors['Errors']) > 0:
            return render(request, 'baseline_calibration/errors_report.html', 
                          {'Check_Errors':Check_Errors})
        
        ps_instance = pillar_survey.save()
        id = ps_instance.pk
        # Commit all the edm raw observations
        if survey_files['edm_file']:
            delete_edm_obs = EDM_Observation.objects.filter(pillar_survey=id)
            delete_edm_obs.delete()
            for o in raw_edm_obs.values():
                from_pillar_id = baseline['pillars'].get(name=o['from_pillar'])
                to_pillar_id = baseline['pillars'].get(name=o['to_pillar'])
                if not frm['thermometer2']: o['raw_temperature2']=None
                if not frm['barometer2']: o['raw_pressure2']=None
                if not frm['hygrometer2']: o['raw_humidity2']=None
                
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
                    raw_temperature2=o['raw_temperature2'],
                    raw_pressure2=o['raw_pressure2'],
                    raw_humidity2=o['raw_humidity2'],
                    use_for_alignment=o['use_for_alignment'],
                    use_for_distance=o['use_for_distance'],
                )
        # Commit all the reduced levels
        if survey_files['lvl_file']:
            delete_lvl_obs = Level_Observation.objects.filter(pillar_survey=id)
            delete_lvl_obs.delete()
            for l in raw_lvl_obs.values():
                pillar_id = baseline['pillars'].get(name=l['pillar'])

                Level_Observation.objects.create(
                    pillar_survey=ps_instance,
                    pillar=pillar_id,
                    reduced_level=l['reduced_level'],
                    rl_standard_deviation=l['std_dev']
                )
        
        return redirect('baseline_calibration:calibrate2', id=id)
            
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
    # If this is a post request: and ps_approvals.is_valid()
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
        (o['Temp'], o['Temp1'], o['Temp2']) =  (
            o['raw_temperature'], o['raw_temperature'],o['raw_temperature2'])
        (o['Pres'], o['Pres1'], o['Pres2']) = (
            o['raw_pressure'], o['raw_pressure'], o['raw_pressure2'])
        (o['Humid'], o['Humid1'], o['Humid2']) = (
            o['raw_humidity'], o['raw_humidity'], o['raw_humidity2'])
        if pillar_survey['thermometer2']:
            if calib['them']:
                o['Temp1'], _ = calib['them'].apply_calibration(
                    o['raw_temperature'],
                    pillar_survey['thermo_calib_applied'])
            if calib['them2']:
                o['Temp2'], _ = calib['them2'].apply_calibration(
                    o['raw_temperature2'],
                    pillar_survey['thermo2_calib_applied'])
            o['Temp'] = (o['Temp1']+o['Temp2'])/2
        else:
            if calib['them']:
                o['Temp'], _ = calib['them'].apply_calibration(
                    o['raw_temperature'],
                    pillar_survey['thermo_calib_applied'])
            
        if pillar_survey['barometer2']:
            if calib['baro']:
                o['Pres1'], _ = calib['baro'].apply_calibration(
                    o['raw_pressure'],
                    pillar_survey['baro_calib_applied'])
            if calib['baro2']:
                o['Pres2'], _ = calib['baro2'].apply_calibration(
                    o['raw_pressure2'],
                    pillar_survey['baro2_calib_applied'])
            o['Pres'] = (o['Pres1']+o['Pres2'])/2
        else:
            if calib['baro']:
                o['Pres'], _ = calib['baro'].apply_calibration(
                    o['raw_pressure'],
                    pillar_survey['baro_calib_applied'])
            
        if pillar_survey['hygrometer2']:
            if calib['hygro']:
                o['Humid1'], _ = calib['hygro'].apply_calibration(
                    o['raw_humidity'],
                    pillar_survey['hygro_calib_applied'])
            if calib['hygro2']:
                o['Humid2'], _ = calib['hygro2'].apply_calibration(
                    o['raw_humidity2'],
                    pillar_survey['hygro2_calib_applied'])
            o['Humid'] = (o['Humid1']+o['Humid2'])/2
        else:
            if calib['hygro']:
                o['Humid'], _ = calib['hygro'].apply_calibration(
                    o['raw_humidity'],
                    pillar_survey['hygro_calib_applied'])
            
        c, o['Calibration_Correction'] = apply_calib(
            o['raw_slope_dist'],
            pillar_survey['edmi_calib_applied'],
            calib['edmi'].first(),
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
            uc_budget['sources'] = add_calib_uc(
                uc_budget['sources'],
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
            o_temp = []
            o_pres = []
            o_humi = []
            len_alignment_survey = len(alignment_survey)
            len_edm_observations = len(edm_observations)
            for i, o in enumerate(edm_observations.values()):
                o_temp.append(o['Temp'])
                o_pres.append(o['Pres'])
                o_humi.append(o['Humid'])
                o = offset_slope_correction(o,
                                          raw_lvl_obs,
                                          alignment_survey,
                                          baseline['d_radius'])
                  
                o['Reduced_distance'] = (o['slope_dist'] 
                                        + o['Offset_Correction']
                                        + o['Slope_Correction'])
    
                #----------------- Calculate Uncertainties -----------------#
                o['uc_sources'] = add_surveyed_uc(o, edm_trend,
                                                  pillar_survey,
                                                  uc_budget['sources'],
                                                  alignment_survey)
                      
                o['uc_budget'] = refline_std_dev(o, 
                                                 alignment_survey,
                                                 pillar_survey['edm'])
                  
                o['uc_combined'] = sum_uc_budget(o['uc_budget'])
    
                #----------------- Least Squares -----------------#
                #Build the design matrix 'A' (ISO 17123-4:2012 eq.11)
                o['id']= str(i+1)
                A_row = [0]*len_alignment_survey
                A_row[-1] = -1
                bay = [pillars.index(o['from_pillar']),
                         pillars.index(o['to_pillar'])]
                A_row[min(bay)-1] = -1
                A_row[max(bay)-1] = 1
                matrix_A.append(A_row)
                  
                matrix_x.append(o['Reduced_distance'])
                
                P_row = [0]*len_edm_observations
                P_row[i] = (1/
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
            
            # save data to session and commit form Submit
            request.session['bay_' + str(id)] = bay
            request.session['sigma_vv_' + str(id)] = sigma_vv.diagonal().tolist()
            
            #----------------- Extract the certified distances from LSA results -----------------#
            # Calculate the average temp and pressure for survey #
            certified_dists={}
            avg_t = mean(o_temp)
            avg_p = mean(o_pres)
            avg_h = mean(o_humi)
            sess_data =[]
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
                                                   pillar_survey,
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
                       pillar_survey['accreditation'].LUM_ppm * d['value'] * 10**-3)
                       * 0.001 )
                
                if pillar_survey['apply_lum'] and cd['uc_combined']['uc95'] < lum:
                    cd['uc_combined']['uc95'] = lum
                    cd['uc_combined']['k'] = 2
                    cd['lum_adopted'] = True
                    if not 'some_lum_adopted' in pillar_survey.keys():
                        pillar_survey['some_lum_adopted'] = True
                        report_notes.append(
                            'The uncertainty of some of the certified distances '
                            'are smaller than the companies accredited '
                            'least uncertainty of measurement (LUM). In these cases '
                            'the LUM has been published in this report.')
                
                # populate a hidden formset to save after commit (form Submit)
                ini_cd['from_pillar'] = pillars[0]
                ini_cd['to_pillar'] = p
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
                sess_data.append(ini_cd)
                # add an extra for the first pillar
                if i==0:
                    ini_cd0 = ini_cd.copy()
                    ini_cd0['to_pillar'] = pillars[0]
                    ini_cd0['distance'] = 0
                    ini_cd0['offset'] = 0
                    ini_cd0['reduced_level'] = float(raw_lvl_obs[pillars[0]]['reduced_level'])
                    ini_cd0['rl_uncertainty'] = float(raw_lvl_obs[pillars[0]]['std_dev'])
                    sess_data.insert(0,ini_cd0)                
            request.session['cd_formset_' + str(id)] = sess_data
            
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
                num_to_append = n_rpt_shots - len(o['grp_Bay'])
                if num_to_append > 0:
                    o['grp_Bay'].extend([''] * num_to_append)
    
            if 'edmi_drift' in calib.keys():
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
            n = len(matrix_y)-1
            request.session['pillar_survey_update_' + str(id)] = {
                'zero_point_correction': matrix_y[n]['value'],
                'zpc_uncertainty': matrix_y[n]['std_dev'],
                'degrees_of_freedom': chi_test['dof'],
                'variance': chi_test['Variance'],
                'html_report': html_report
                }           
            
            context = {'pillar_survey': pillar_survey,
                       'html_report': html_report,
                       'ps_approvals':ps_approvals,
                       'hidden':[]}
            
            return render(request, 'baseline_calibration/display_report.html', context)
        
        #----------------------- code for commiting the calibration and returning to home page -----------------------------#        

        if ps_approvals.is_valid():
            # Save signiture block
            ps_obj = ps_approvals.save()
            
            # pillar survey update
            psu = request.session['pillar_survey_update_' + str(id)]
            del request.session['pillar_survey_update_' + str(id)]
            psu_obj = get_object_or_404(Pillar_Survey, id=id)
            psu_obj.zero_point_correction = psu['zero_point_correction']
            psu_obj.zpc_uncertainty = psu['zpc_uncertainty']
            psu_obj.degrees_of_freedom = psu['degrees_of_freedom']
            psu_obj.variance = psu['variance']
            psu_obj.html_report = psu['html_report']
            psu_obj.save()
            
            # Commit the certified distances
            cd_formset = request.session['cd_formset_' + str(id)]
            del request.session['cd_formset_' + str(id)]
            for cd in cd_formset:
                cd['from_pillar'] = baseline['pillars'].get(name=cd['from_pillar'])
                cd['to_pillar'] = baseline['pillars'].get(name=cd['to_pillar'])
                cd_obj, created = Certified_Distance.objects.get_or_create(
                    pillar_survey = ps_obj,
                    from_pillar = cd['from_pillar'],
                    to_pillar = cd['to_pillar'],
                    defaults = cd)
            if not created:
                cd_obj.distance = cd['distance']
                cd_obj.a_uncertainty = cd['a_uncertainty']
                cd_obj.k_a_uncertainty = cd['k_a_uncertainty']
                cd_obj.combined_uncertainty = cd['combined_uncertainty']
                cd_obj.k_combined_uncertainty = cd['k_combined_uncertainty']
                cd_obj.offset = cd['offset']
                cd_obj.os_uncertainty = cd['os_uncertainty']
                cd_obj.k_os_uncertainty = cd['k_os_uncertainty']
                cd_obj.reduced_level = cd['reduced_level']
                cd_obj.rl_uncertainty = cd['rl_uncertainty']
                cd_obj.k_rl_uncertainty = cd['k_rl_uncertainty']
                cd_obj.save()
               
            # Commit the standard deviations
            bay = request.session['bay_' + str(id)]
            sigma_vv = request.session['sigma_vv_' + str(id)]
            del request.session['bay_' + str(id)]
            del request.session['sigma_vv_' + str(id)]
            for b, vv in zip(bay, sigma_vv):
                p0, p1 = b.split(' - ')
                vv_obj, created = Std_Deviation_Matrix.objects.get_or_create(
                    pillar_survey=ps_obj,
                    from_pillar=baseline['pillars'].get(name=p0),
                    to_pillar=baseline['pillars'].get(name=p1),
                    defaults = {
                        'std_uncertainty':sqrt(vv)})
            if not created:
                vv_obj.std_uncertainty = sqrt(vv)
                vv_obj.save()
                                
            return redirect('baseline_calibration:calibration_home')


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
def uc_budget_create(request):    
    uc_sources = formset_factory(Uncertainty_Budget_SourceForm, extra=0)
    if request.method == 'POST':        
        uc_sources = uc_sources(request.POST)
        uc_budget = Uncertainty_BudgetForm(
            request.POST,
            sources = uc_sources,
            user=request.user)
        if uc_budget.is_valid() and uc_sources.is_valid():
            uc_budget.save()
            # Save the pk if this has been called during calibration with add_btn.
            request.session['new_instance'] = uc_budget.instance.pk
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
        ini_sources = Uncertainty_Budget_Source.objects.filter(
                        uncertainty_budget__name = 'Default', 
                        uncertainty_budget__company__company_name = 'Landgate')
        
        uc_sources = uc_sources(initial=[vars(row) for row in ini_sources])
        
        uc_budget = Uncertainty_BudgetForm(
            initial=ini_budget, 
            sources = uc_sources,
            user=request.user)
    
    context = {}
    context['Header'] = 'Create Custom Uncertainty Budget'        
    context['form'] = uc_budget
    context['formset'] = uc_sources
    
    return render(request, 'baseline_calibration/uncertainty_budget_form.html', context)


@login_required(login_url="/accounts/login") 
def uc_budget_edit(request, id=None):
       
    uc_sources = modelformset_factory(
        Uncertainty_Budget_Source,
        form=Uncertainty_Budget_SourceForm, 
        extra=0)
    qs = Uncertainty_Budget_Source.objects.filter(
                            uncertainty_budget = id)
    formset = uc_sources(request.POST or None, queryset=qs)
    
    obj = get_object_or_404(Uncertainty_Budget, id=id)
    uc_budget = Uncertainty_BudgetForm(
        request.POST or None, 
        sources = formset,
        instance=obj)
    
    # Edit the database according to submitted valid form.
    if all([uc_budget.is_valid(), formset.is_valid()]):
        uc_budget.save()
        new_sources_id=[]
        for uc_source in formset:
            new_sources_id.append(uc_source.instance.id)
            source = uc_source.save(commit=False)
            source.uncertainty_budget = uc_budget.instance
        formset.save()
        
        # Delete uc_source if it has been removed
        for orig_source in qs:
            if not orig_source.id in new_sources_id:
                orig_source.delete()
                 
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('baseline_calibration:uc_budgets')

    context = {}
    context['Header'] = 'Edit Uncertainty Budget'
    context['form'] = uc_budget
    context['formset'] = formset
    
    return render(request, 'baseline_calibration/uncertainty_budget_form.html', context)


@login_required(login_url="/accounts/login") 
def uc_budget_delete(request, id):
    # unless staff, only allow delete if record belongs to company
    if request.user.is_staff:
        delete_obj = Uncertainty_Budget.objects.get(id=id)
    else:
        delete_obj = Uncertainty_Budget.objects.get(
            id=id,
            accredited_company = request.user.company)
    try_delete_protected(request, delete_obj)
    
    return redirect('baseline_calibration:uc_budgets')


@login_required(login_url="/accounts/login") 
def accreditations(request):
    # unless staff, only list records that belong to company
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
    # if id==None this is a new accredittion.
    if id == 'None':
        accreditation = AccreditationForm(request.POST or None,
                                          request.FILES or None,
                                          user=request.user)
        context['Header'] = 'Input Accreditation Details'
    else:
        obj = get_object_or_404(Accreditation, id=id)
        obj.valid_from_date = obj.valid_from_date.isoformat()
        obj.valid_to_date = obj.valid_to_date.isoformat()
        accreditation = AccreditationForm(request.POST or None,
                                          request.FILES or None,
                                          instance=obj,
                                          user=request.user)

        context['Header'] = 'Edit Accreditation Details'
    
    if accreditation.is_valid():
        accreditation.save()  
        # Save the pk if this has been called during calibration with add_btn.
        request.session['new_instance'] = accreditation.instance.pk
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('baseline_calibration:accreditations')
        
    context['form'] = accreditation
    
    return render(request, 'baseline_calibration/Accreditation_form.html', context)


@login_required(login_url="/accounts/login") 
def accreditation_delete(request, id):
    # unless staff, only allow delete if record belongs to company
    if request.user.is_staff:
        delete_obj = Accreditation.objects.get(id=id)
    else:
        delete_obj = Accreditation.objects.get(
            id=id,
            accredited_company = request.user.company)

    try_delete_protected(request, delete_obj)
    
    return redirect('baseline_calibration:accreditations')


@login_required(login_url="/accounts/login") 
def certified_distances_home(request, id):
    certified_distances_obj = Certified_Distance.objects.filter(
        pillar_survey__baseline_id = id).order_by('pillar_survey__survey_date')
    
    pillar_surveys = []
    for cd in certified_distances_obj:
        if cd.pillar_survey not in pillar_surveys:
            pillar_surveys.append(cd.pillar_survey)
            
    pillars = list(OrderedDict.fromkeys(cd.to_pillar for cd in certified_distances_obj))
    first_pillar_survey = certified_distances_obj.first().pillar_survey
    
    # Organise into a dictionary grouped by pillar survey
    certified_distances_list = []
    for pillar_survey in pillar_surveys:
        cd=[]
        for pillar in pillars:
            cd.append(
                certified_distances_obj.filter(
                    pillar_survey = pillar_survey.id,
                    to_pillar = pillar))
        certified_distances_list.append(cd)
    
    # Calculate data for graph
    back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                    '#00FF00', '#008000', '#00FFFF', '#008080', 
                    '#0000FF', '#000080', '#FF00FF', '#800080']
    
    labels = [pillar_survey.survey_date for pillar_survey in pillar_surveys]
    dataset1 = []
    dataset2 = []
    dataset3 = []
    i=0
    for pillar in pillars:
        data1 =[]
        data2 =[]
        data3 =[]
        for pillar_survey in pillar_surveys:
            data1.append(
                certified_distances_obj.get(
                pillar_survey = pillar_survey.id,
                to_pillar = pillar).distance
                - certified_distances_obj.get(
                    pillar_survey = first_pillar_survey.id,
                    to_pillar = pillar).distance
                )
            data2.append(
                certified_distances_obj.get(
                pillar_survey = pillar_survey.id,
                to_pillar = pillar).offset
                - certified_distances_obj.get(
                    pillar_survey = first_pillar_survey.id,
                    to_pillar = pillar).offset
                )
            data3.append(
                certified_distances_obj.get(
                pillar_survey = pillar_survey.id,
                to_pillar = pillar).reduced_level
                - certified_distances_obj.get(
                    pillar_survey = first_pillar_survey.id,
                    to_pillar = pillar).reduced_level
                )

        dataset1.append(
             {'borderColor':back_colours[i],
             'borderWidth': 1,
             'data':data1,
             'fill':False,
             'label': pillar.name,
             'pointRadius': 1,
             'showLine': True,
             'tension': 0})
        dataset2.append(
             {'borderColor':back_colours[i],
             'borderWidth': 1,
             'data':data2,
             'fill':False,
             'label': pillar.name,
             'pointRadius': 1,
             'showLine': True,
             'tension': 0})
        dataset3.append(
             {'borderColor':back_colours[i],
             'borderWidth': 1,
             'data':data3,
             'fill':False,
             'label': pillar.name,
             'pointRadius': 1,
             'showLine': True,
             'tension': 0})
        i+=1
        if i>len(back_colours): i=0
    
    graph1_data = {
        'labels':labels,
        'datasets':dataset1}
    graph2_data = {
        'labels':labels,
        'datasets':dataset2}
    graph3_data = {
        'labels':labels,
        'datasets':dataset3}
    
    #convert from python to json
    graph1_data = json.dumps(graph1_data, cls=DjangoJSONEncoder)
    graph2_data = json.dumps(graph2_data, cls=DjangoJSONEncoder)
    graph3_data = json.dumps(graph3_data, cls=DjangoJSONEncoder)
    context = {
        'certified_distances_list': certified_distances_list,
        'graph1_datasets': graph1_data,
        'graph2_datasets': graph2_data,
        'graph3_datasets': graph3_data}
    
    return render(
        request,
        'baseline_calibration/certified_distances_list.html', 
        context)


@login_required(login_url="/accounts/login") 
def certified_distances_edit(request, id):
    # only available to staff
    if request.user.is_staff:
        certified_distances = modelformset_factory(
            Certified_Distance,
            form = Certified_DistanceForm, 
            extra = 0)
        
        certified_distances_obj = Certified_Distance.objects.filter(
            pillar_survey = id)
                
        certified_distances_formset = certified_distances(
            request.POST or None,
            prefix='formset1',
            queryset=certified_distances_obj)

        std_deviation_matrix = modelformset_factory(
            Std_Deviation_Matrix,
            form = Std_Deviation_MatrixForm, 
            extra = 0)
        
        std_deviation_matrix_obj = Std_Deviation_Matrix.objects.filter(
            pillar_survey = id)
                       
        std_deviation_matrix_formset = std_deviation_matrix(
            request.POST or None,
            prefix='formset2',
            queryset=std_deviation_matrix_obj)
          
        if certified_distances_formset.is_valid() and std_deviation_matrix_formset.is_valid():
            certified_distances_formset.save()
            std_deviation_matrix_formset.save()
            
            next_url = request.POST.get('next', 'calibrationsites:home')
            return redirect(next_url)
            
        context = {
            'certified_distances_obj':certified_distances_obj,
            'combined': zip(certified_distances_obj, certified_distances_formset),
            'certified_distances_formset': certified_distances_formset,
            'std_deviation_matrix_formset': std_deviation_matrix_formset,
            'std_combined': list(
                zip(std_deviation_matrix_obj, std_deviation_matrix_formset))
            }
        
        return render(request, 'baseline_calibration/certified_distances_form.html', context)



