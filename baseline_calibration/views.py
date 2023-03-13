from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import formset_factory, modelformset_factory
from django.forms.models import model_to_dict
from collections import OrderedDict
from django.db.models import Q


# Create your views here.
from .forms import (PillarSurveyForm,
                    UploadSurveyFiles,
                    ChangeSurveyFiles,
                    EDM_ObservationForm,
                    Certified_DistanceForm,
                    Std_Deviation_MatrixForm,
                    PillarSurveyUpdateForm,
                    Uncertainty_BudgetForm,
                    Uncertainty_Budget_SourceForm,
                    AccreditationForm,
                    ImportDliDataForm)
from instruments.models import (EDM_Inst,
                    Prism_Inst,
                    DigitalLevel,
                    Staff,
                    Mets_Inst)
from calibrationsites.models import (Pillar,
                    CalibrationSite)
from .models import (Pillar_Survey,
                    EDM_Observation,
                    Level_Observation,
                    Accreditation,
                    Uncertainty_Budget,
                    Uncertainty_Budget_Source,
                    Certified_Distance,
                    Std_Deviation_Matrix)
from geodepy.survey import radiations
from common_func.Convert import *
from common_func.SurveyReductions import *
from instrument_calibrations.settings import *
from common_func.LeastSquares import (LSA,
                                      ISO_test_b,
                                      ISO_test_c)
from datetime import datetime as dt

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
        ini_data = {'computation_date':date.today().isoformat(),
                    'accreditation': Accreditation.objects.filter(
                            valid_from_date__lte = date.today().isoformat(),
                            valid_to_date__gte = date.today().isoformat(),
                            accredited_company = request.user.company 
                            ).order_by('-valid_from_date').first()}
    
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
            edm_clms=['from_pillar',
                      'to_pillar',
                      'inst_ht',
                      'tgt_ht',
                      'hz_direction',
                      'raw_slope_dist',
                      'raw_temperature',
                      'raw_pressure',
                      'raw_humidity']
            raw_edm_obs = csv2dict(survey_files['edm_file'],edm_clms)
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
            level_clms=['pillar',
                      'reduced_level',
                      'Std_Dev']
            raw_lvl_obs = csv2dict(survey_files['lvl_file'],level_clms,0)
        else:            
            qs = Level_Observation.objects.filter(pillar_survey__pk=id)
            raw_lvl_obs = {}
            for o in qs:
                dct = model_to_dict(o)
                dct['pillar'] = o.pillar.name
                dct['Std_Dev'] = dct['rl_standard_deviation']
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
        id = ps_instance.pk
        # Commit all the edm raw observations
        if survey_files['edm_file']:
            delete_edm_obs = EDM_Observation.objects.filter(pillar_survey=id)
            delete_edm_obs.delete()
            for o in raw_edm_obs.values():
                this_EDM_Observation = EDM_Observation.objects.create(
                    pillar_survey = ps_instance,
                    from_pillar = baseline['pillars'].get(name=o['from_pillar']),
                    to_pillar = baseline['pillars'].get(name=o['to_pillar']),
                    inst_ht = o['inst_ht'],
                    tgt_ht = o['tgt_ht'],
                    hz_direction = o['hz_direction'],
                    raw_slope_dist = o['raw_slope_dist'],
                    raw_temperature = o['raw_temperature'],
                    raw_pressure = o['raw_pressure'],
                    raw_humidity = o['raw_humidity'],
                    use_for_alignment = o['use_for_alignment'],
                    use_for_distance = o['use_for_distance'])

        # Commit all the reduced levels
        if survey_files['lvl_file']:
            # if not id == 'None':
            delete_lvl_obs = Level_Observation.objects.filter(pillar_survey=id)
            delete_lvl_obs.delete()
            for l in raw_lvl_obs.values():
                this_lvl_Observation = Level_Observation.objects.create(
                    pillar_survey = ps_instance,
                    pillar = baseline['pillars'].get(name=l['pillar']),
                    reduced_level = l['reduced_level'],
                    rl_standard_deviation = l['Std_Dev'])
                        
        return redirect('baseline_calibration:calibrate2', id=id)

    else:
        print(upload_survey_files.is_valid())
        for e in pillar_survey.errors:
            print(e)
        for e in upload_survey_files.errors:
            print(e)
            
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
    qs = Pillar_Survey.objects.get(id=id)
    query_dict = QueryDict('', mutable=True)
    query_dict.update(model_to_dict(qs))
    pillar_survey_form = PillarSurveyForm(query_dict, user=request.user)
    pillar_survey_form.is_valid()
    pillar_survey = pillar_survey_form.cleaned_data
    pillar_survey.update({'pk':id})
    pillar_survey.update({'variance':query_dict['variance']})
    
    # Create some forms to hide on report and commit when submitted
    cd_formset = formset_factory(Certified_DistanceForm, extra=0)    
    sdev_mat_formset = formset_factory(Std_Deviation_MatrixForm, extra=0)
    pillar_survey_update = PillarSurveyUpdateForm(request.POST or None)
    
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
        dct['Std_Dev'] = dct['rl_standard_deviation']
        del dct['rl_standard_deviation']
        raw_lvl_obs[o.pillar.name] = dct

    calib = {}
    baseline={}
    uc_budget = {}
    calib = Calibrations_qry(pillar_survey)
    baseline = baseline_qry(pillar_survey)
        
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
        c,o['Calibration_Correction'] = apply_calib(o['raw_slope_dist'],
                                    pillar_survey['edmi_calib_applied'],
                                    calib['edmi'][0])
        o = (edm_mets_correction(o, 
                                   pillar_survey['edm'],
                                   pillar_survey['mets_applied']))
        
        o['slope_dist'] = (float(o['raw_slope_dist'] )
                                     + o['Calibration_Correction']
                                     + o['Mets_Correction'])
        
        # Calculate the Est and Nth for all in raw'
        o['Bay']= o['from_pillar'] + ' - ' + o['to_pillar']
        ht_diff = (float(raw_lvl_obs[o['to_pillar']]['reduced_level'])
          - float(raw_lvl_obs[o['from_pillar']]['reduced_level']))
        hz_dist = sqrt(ht_diff**2 +
                  (float(o['slope_dist']))**2)
        o['Est'], o['Nth'] = radiations(0, 0,
                         float(o['hz_direction']),
                         hz_dist)
        
    if request.method == 'GET':
        alignment_survey = adjust_alignment_survey(raw_edm_obs,
                                                  baseline['pillars'])        
        
        formset = zip(edm_obs_formset,raw_edm_obs.values())
        
        return render(request, 'baseline_calibration/edm_rawdata.html', 
                      {'Page': 'Page 5 of 5',
                       'id': id,
                       'edm_obs_formset':edm_obs_formset,
                       'pillar_survey': pillar_survey,
                       'formset': formset})
    else:
        # This is a POST request
        # Apply a mask to the raw observations and recalulate averages and offsets
        if edm_obs_formset.is_valid():
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
            
            #----------------- Query related data -----------------#
            report_notes = report_notes_qry(company=request.user.company, report_type='B')
            uc_budget = uncertainty_qry(pillar_survey)
            uc_budget['sources'] = add_calib_uc(uc_budget['sources'], 
                                                        calib,
                                                        pillar_survey)
           
            alignment_survey = adjust_alignment_survey(raw_edm_obs,
                                                      baseline['pillars'])
            for k, p in alignment_survey.items():
                p['reduced_level'] = float(raw_lvl_obs[k]['reduced_level'])
                p['rl_uncertainty'] = float(raw_lvl_obs[k]['Std_Dev'])*2
                p['k_rl_uncertainty'] = 2
            edm_observations = reduce_sets_of_obs(raw_edm_obs)
            
            edm_trend = edm_std_function(edm_observations,
                                         uc_budget['stddev_0_adj'])           #y = Ax + B
            
            pillars = [p.name for p in baseline['pillars']]
               
            matrix_A = []
            matrix_x = []
            matrix_P = []
            for i, o in enumerate(edm_observations.values()):
                o = (offset_slope_correction(o,
                                          raw_lvl_obs,
                                          alignment_survey,
                                          baseline['d_radius']))
                  
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
            for p0 in pillars:
                i0 = pillars.index(p0)
                for p1 in pillars[1:]:
                    i1 = pillars.index(p1)
                    A_row = [0]*(len(pillars))
                    if i0!=0: A_row[i0-1] = -1
                    A_row[i1-1] = 1
            
                    if not p1+' - '+ p0 in bay and p1!=p0:
                        bay.append(p0+' - '+ p1)
                        vcv_A.append(A_row)
            
            vcv_A = np.array(vcv_A, dtype=object)
            sigma_vv = vcv_A @ vcv_matrix @ vcv_A.T
            
            # populate a hidden formset to save after commit (form Submit)
            ini_data=[]
            for b, vv in zip(bay, np.diagonal(sigma_vv)):
                p0, p1 = b.split(' - ')
                ini_data.append({'pillar_survey':id,
                                 'from_pillar':baseline['pillars'].get(name=p0),
                                 'to_pillar':baseline['pillars'].get(name=p1),
                                 'std_uncertainty':sqrt(vv)})
            
            sdev_mat_formset = sdev_mat_formset(initial=ini_data, prefix='sdev_mat')
            
            #----------------- Extract the certified distances from LSA results -----------------#
            # Calculate the average temp and pressure for survey #
            certified_dists={}
            avg_t = mean([float(o['Temp']) for o in edm_observations.values()])
            avg_p = mean([float(o['Pres']) for o in edm_observations.values()])
            avg_h = mean([float(o['Humid']) for o in edm_observations.values()])
            ini_data =[]
            i=True
            some_lum_adopted = False
            for p, d in zip(pillars[1:], matrix_y[:-1]):
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
                if i==True:
                    ini_cd0 = ini_cd.copy()
                    ini_cd0['to_pillar'] = baseline['pillars'].get(name=pillars[0])
                    ini_cd0['distance'] = 0
                    ini_cd0['offset'] = 0
                    ini_cd0['reduced_level'] = float(raw_lvl_obs[pillars[0]]['reduced_level'])
                    ini_cd0['rl_uncertainty'] = float(raw_lvl_obs[pillars[0]]['Std_Dev'])
                    ini_data.insert(0,ini_cd0)
                    i=False
                    
            cd_formset = cd_formset(initial=ini_data)
            ini_data=[]
            #create update for pillar survey processing
            n = len(matrix_y)-1
            ini_data = {'zero_point_correction': matrix_y[n]['value'],
                        'zpc_uncertainty': matrix_y[n]['std_dev'],
                        'degrees_of_freedom': chi_test['dof'],
                        'variance': chi_test['Variance']}
            
            pillar_survey_update = PillarSurveyUpdateForm(initial=ini_data)
            
            #Prepare the context for the template
            od = OrderedDict(sorted(alignment_survey.items()))
            alignment_survey = list(od.values())
            certified_dists = list(certified_dists.values())
            
            back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                            '#00FF00', '#008000', '#00FFFF', '#008080', 
                            '#0000FF', '#000080', '#FF00FF', '#800080']
            for cd, colour in zip(certified_dists,back_colours):
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
                       'Check_Errors':Check_Errors,
                       'hidden':[cd_formset,
                                 sdev_mat_formset,
                                 pillar_survey_update]}
            
            return render(request, 'baseline_calibration/calibrate_report.html', context)
        
        #----------------------- code for commiting the calibration and returning to home page -----------------------------#        
        cd_formset = cd_formset(request.POST)
        sdev_mat_formset = sdev_mat_formset(request.POST, prefix='sdev_mat')
        #check to see if distances have been saved before and delete these from the database
        delete_cd = Certified_Distance.objects.filter(pillar_survey__pk=id)
        delete_cd.delete()
        delete_sdev_mat = Std_Deviation_Matrix.objects.filter(pillar_survey__pk=id)
        delete_sdev_mat.delete()
        if cd_formset.is_valid() and sdev_mat_formset.is_valid() and pillar_survey_update.is_valid():
            # this is a POST command asking to commit the hidden calibration 
            # data held on the report page
            ps_update = pillar_survey_update.cleaned_data
            pillar_survey = Pillar_Survey.objects.get(id=id)    
            pillar_survey.zero_point_correction = ps_update['zero_point_correction']
            pillar_survey.zpc_uncertainty = ps_update['zpc_uncertainty']
            pillar_survey.degrees_of_freedom = ps_update['degrees_of_freedom']
            pillar_survey.variance = ps_update['variance']
            pillar_survey.save()
            
            for cd_form in cd_formset:
                cd_form.save()
                
            for sdev_mat_form in sdev_mat_formset:
                sdev_mat_form.save()
                
            return redirect('baseline_calibration:calibration_home')
        
        else:
            for e in cd_formset.errors:
                print(e)
            context = {'pillar_survey':pillar_survey,
                       'hidden':[cd_formset,
                                 sdev_mat_formset,
                                 pillar_survey_update]}
            
            return render(request, 'baseline_calibration/calibrate_report.html', context)
   
    return render(request, 'baseline_calibration/edm_rawdata.html', 
                  {'Page': 'Page 5 of 5',
                   'id': id,
                   'edm_obs_formset':edm_obs_formset,
                   'pillar_survey': pillar_survey,
                   'formset': formset})


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
                 
        if request.POST.get('next'):
            return redirect(request.POST.get('next'))
        else:
            return redirect(request.POST.get('baseline_calibration:uc_budgets'))

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
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect ('baseline_calibration:uc_budgets')
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
    delete_budget = Uncertainty_Budget.objects.get(id=id)
    delete_budget.delete()
    
    return redirect('baseline_calibration:uc_budgets')


@login_required(login_url="/accounts/login") 
def accreditations(request):
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
        if 'next' in request.POST:
            accreditation.save()
            return redirect(request.POST.get('next'))
        else:
            return redirect ('baseline_calibration:accreditations')
        
    context['form'] = accreditation
    
    return render(request, 'baseline_calibration/Accreditation_form.html', context)


@login_required(login_url="/accounts/login") 
def accreditation_delete(request, id):
    accreditation = Accreditation.objects.get(id=id)
    accreditation.delete()
    
    return redirect('baseline_calibration:accreditations')

@login_required(login_url="/accounts/login") 
def import_dli(request):
    importForm = ImportDliDataForm(
        request.POST or None,
        request.FILES or None)
    
    if importForm.is_valid():
        files = request.FILES.getlist('inst_make_file')
        
        for f in files:
            if f.name == 'rxBaseline.db':
                clms = ['pk', 'name', 'location',
                        'operator', 'calibrated_date', 'reference',
                        'ellipsoid_fk', 'confidence_level', 'reference_height',
                        'StdICConstant', 'StdICPPM', 'humidity', 'ArchiveFlag']
                rxBaseline = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxBaseline))
                
            if f.name == 'rxBaselineX.db':
                clms = ['pk', 'name', 'location',
                        'operator', 'calibrated_date', 'reference',
                        'ellipsoid_fk', 'confidence_level', 'reference_height',
                        'StdICConstant', 'StdICPPM', 'humidity', 'ArchiveFlag',
                        'operator_address']
                rxBaselineX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxBaselineX))
            
            if f.name == 'rxBaselineAccuracy.db':
                clms = ['baseline_fk', 'UncertaintyConstant', 'UncertaintyScale']
                rxBaselineAccuracy = list2dict(decrypt_file(f), clms, 'baseline_fk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxBaselineAccuracy))
            
            if f.name == 'rxBaselineAccuracyX.db':
                clms = ['baseline_fk', 'UncertaintyConstant', 'UncertaintyScale']
                rxBaselineAccuracyX = list2dict(decrypt_file(f), clms, 'baseline_fk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxBaselineAccuracyX))
            
            if f.name == 'rxDistance.db':
                clms = ['pk', 'baseline_fk', 'from_pillar_fk',
                        'to_pillar_fk', 'certified_distance', 'DistSigma']
                rxDistance = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxDistance))
            
            if f.name == 'rxDistanceX.db':
                clms = ['pk', 'baseline_fk', 'from_pillar_fk',
                        'to_pillar_fk', 'certified_distance', 'DistSigma']
                rxDistanceX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxDistanceX))
            
            if f.name == 'rxEDMObs.db':
                clms = ['pk', 'MeasID', 'EDMObsDistance',
                        'MeasDryTemp', 'MeasHumidity', 'MeasPressure']
                rxEDMObs = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxEDMObs))
            
            if f.name == 'rxEDMObsX.db':
                clms = ['pk', 'MeasID', 'EDMObsDistance',
                        'MeasDryTemp', 'MeasHumidity', 'MeasPressure']
                rxEDMObsX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxEDMObsX))
            
            if f.name == 'rxInstrument.db':
                clms = ['pk', 'inst_type', 'InstrumentModel_fk',
                        'serial_number', 'manu_unc_const', 'manu_unc_ppm',
                        'AntennaModelID', 'InstAntennaSerialNo', 
                        'InstConstant', 'InstScaleFact', 'comments']
                rxInstrument = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxInstrument))
            
            if f.name == 'rxInstrumentX.db':
                clms = ['pk', 'inst_type', 'InstrumentModel_fk',
                        'serial_number', 'manu_unc_const', 'manu_unc_ppm',
                        'AntennaModelID', 'InstAntennaSerialNo', 
                        'InstConstant', 'InstScaleFact', 'comments']
                rxInstrumentX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxInstrumentX))
            
            if f.name == ('rxInstrumentMake.db'):
                clms = ['pk', 'manufacturer', 'country']
                rxInstrumentMake = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxInstrumentMake))
            
            if f.name == ('rxInstrumentMakeX.db'):
                clms = ['pk', 'manufacturer', 'country']
                rxInstrumentMakeX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxInstrumentMakeX))
                
            if f.name == 'rxInstrumentModel.db':
                clms = ['pk', 'InstrumentMake_fk', 'name', 'type',
                        'manu_unc_const', 'manu_unc_ppm',
                        'unit_length', 'frequency', 'carrier_wavelength',
                        'comments', 'is_pulse', 'manu_ref_refrac_index' ]
                rxInstrumentModel = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxInstrumentModel))
                
            if f.name == 'rxInstrumentModelX.db':
                clms = ['pk', 'InstrumentMake_fk', 'name', 'type',
                        'manu_unc_const', 'manu_unc_ppm',
                        'unit_length', 'frequency', 'carrier_wavelength',
                        'comments', 'is_pulse', 'manu_ref_refrac_index' ]
                rxInstrumentModelX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxInstrumentModelX))
            
            if f.name == 'rxJob.db':
                clms = ['pk', 'name', 'instrument_edm_fk','instrument_prism_fk',
                        'edm_owner', 'prism_owner', 'ProcessingSoftware',
                        'survey_date', 'survey_time', 'computation_date',
                        'computation_time', 'observer_name', 'baseline_fk',
                        'weather', 'TempCorr', 'PressureCorr', 'StdDevTemp', 
                        'StdDevPressure', 'InstCentringStdDev', 'InstLevellingStdDev',
                        'calibration_type', 'JobComments', 'edm_owner_address', 'Thermometer1',
                        'Thermometer2','Barometer1','Barometer2','ThermometerCorr1',
                        'ThermometerCorr2','BarometerCorr1','BarometerCorr2',
                        'NumberThermometers','NumberBarometers']
                rxJob = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxJob))
            
            if f.name == 'rxJMeasure.db':
                clms = ['pk', 'MeasType', 'job_fk','from_pillar_fk', 'to_pillar_fk',
                        'from_ht', 'to_ht', 'raw_dry_temp', 'raw_humidity', 'humidity_type',
                        'raw_pressure', 'mets_flag', 'wet_temp', 'humidity',
                        'raw_dry_temp2', 'raw_pressure2', 'raw_humidity2']
                rxJMeasure = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxJMeasure))
            
            if f.name == 'rxJMeasureX.db':
                clms = ['pk', 'MeasType', 'job_fk','from_pillar_fk', 'to_pillar_fk',
                        'from_ht', 'to_ht', 'raw_dry_temp', 'raw_humidity', 'humidity_type',
                        'raw_pressure', 'mets_flag', 'wet_temp', 'humidity',
                        'raw_dry_temp2', 'raw_pressure2', 'raw_humidity2']
                rxJMeasureX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxJMeasureX))
            
            if f.name == 'rxPillar.db':
                clms = ['pk', 'baseline_fk', 'order','name', 'height', 'offset',
                        'latitude', 'longitude', 'EllipsARadius', 'EllipsBRadius',
                        'EllipsOrient', 'HtStdDev']
                rxPillar = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxPillar))
            
            if f.name == 'rxPillarX.db':
                clms = ['pk', 'baseline_fk', 'order','name', 'height', 'offset',
                        'latitude', 'longitude', 'EllipsARadius', 'EllipsBRadius',
                        'EllipsOrient', 'HtStdDev']
                rxPillarX = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxPillarX))
            
            if f.name == 'rxStandard.db':
                clms = ['Type', 'StandardConstant', 'StandardScale','Authority',
                        'Description', 'LUMUnits', 'AlternateConstant',
                        'AlternateScale']
                rxStandard = list2dict(decrypt_file(f), clms, 'Type')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxStandard))
                
            # print(str(f.name.replace('.db','')) + ' = ' )
            # print(decrypt_file(f))
    
    medjil_baseline_calibration = apps.get_model(
        'baseline_calibration', 'Pillar_Survey')
    medjil_accreditation = apps.get_model(
        'baseline_calibration', 'Accreditation')

    for job in rxJob.values():
        if job['calibration_type'] == 'B':
            if rxBaselineX[job['baseline_fk']]['name'].lower().find('curtin') != -1:
                baseline_id = calibrationsites.objects.get(site_name = 'Curtin')
            elif rxBaselineX[job['baseline_fk']]['name'].lower().find('kalgoorlie') != -1:
                baseline_id = calibrationsites.objects.get(site_name = 'Kalgoorlie')        
            elif rxBaselineX[job['baseline_fk']]['name'].lower().find('busselton') != -1:
                baseline_id = calibrationsites.objects.get(site_name = 'Busselton')
            
            medjil_accreditation.objects.get_or_create(
                accredited_company = request.user.company,
                valid_from_date = dt(1900,1,1).isoformat(),
                valid_to_date = dt(2020,1,1).isoformat(),
                LUM_constant = 0,
                LUM_ppm = 0,
                statement = 'Unknown accreditation from BaselineDLI backcaptured data')    
            
            pillars =(
                [p for p in rxPillar.values() if p['baseline_fk'] == job['baseline_fk']])
            
            job_measurements =(
                [meas for meas in rxJMeasure.values() if meas['job_fk'] == job['pk']])
            mets_applied = False
            if job_measurements[0]['mets_flag'] == 'N': mets_applied = True
            
            thermo_calib_applied = all([job['ThermometerCorr1'] == '0', job['ThermometerCorr2'] == '0'])
            if mets_applied: thermo_calib_applied = True
            
            baro_calib_applied = all([job['BarometerCorr1'] == '0', job['BarometerCorr2'] == '0'])
            if mets_applied: baro_calib_applied = True
            
            edm = rxInstrument[job['instrument_edm_fk']]
            edm_model = rxInstrumentModel[edm['InstrumentModel_fk']]
            edm_make = rxInstrumentMake[edm_model['InstrumentMake_fk']]
            
            prism = rxInstrument[job['instrument_prism_fk']]
            prism_model = rxInstrumentModel[prism['InstrumentModel_fk']]
            prism_make = rxInstrumentMake[prism_model['InstrumentMake_fk']]
            
            # medjil_baseline_calibration.objects.get_or_create(
            #     baseline = baseline_id,
            #     survey_date = dt.strptime(job['survey_date'],'%d/%m/%Y').isoformat(),
            #     computation_date = dt.strptime(job['computation_date'],'%d/%m/%Y').isoformat(),
            #     accreditation = medjil_accreditation.instance,
            #     apply_lum = False,
            #     observer = job['observer_name'],
            #     weather = 'Sunny/Clear',
            #     job_number = rxBaselineX[job['baseline_fk']]['reference'],
            #     edm = ,
            #     prism = ,
            #     mets_applied = mets_applied,
            #     edmi_calib_applied = True,
            #     level = ,
            #     staff = ,
            #     staff_calib_applied = True,
            #     thermometer = ,
            #     thermo_calib_applied = thermo_calib_applied,
            #     barometer = ,
            #     baro_calib_applied = baro_calib_applied,
            #     hygrometer = ,
            #     hygro_calib_applied = True,
            #     psychrometer = None,
            #     psy_calib_applied = True,
            #     uncertainty_budget = ,
            #     outlier_criterion = 3,
            #     fieldnotes_upload = None,
            #     zero_point_correction = float(rxBaselineX[job['baseline_fk']]['StdICConstant']),
            #     zpc_uncertainty = float(rxBaselineAccuracyX[job['baseline_fk']]['UncertaintyConstant']),
            #     variance = 1,
            #     degrees_of_freedom = len(job_measurements) - len(pillars),
            #     )
    
    context ={
        'Header': 'Import BaselineDLI Database Records',
        'form': importForm}
    
    return render(request, 'baseline_calibration/Accreditation_form.html', context)