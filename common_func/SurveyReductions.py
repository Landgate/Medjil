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
import numpy as np
from common_func.Convert import (
    calibrations_qry2,
    group_list,
    db_std_units)
from math import sqrt, sin, cos, radians, pi
from datetime import date
from statistics import mean
from scipy.stats import t
from sklearn.linear_model import LinearRegression
from geodepy.survey import (
    radiations,
    joins,
    part_h2o_vap_press, mets_partial_differentials)
from baseline_calibration.models import Pillar_Survey
from copy import deepcopy
from django.forms.models import model_to_dict


    #-------------------------------------------------------------------------------#
    #----------------- Functions for SURVEY OBSERVATION REDUCTIONS -----------------#
    #-------------------------------------------------------------------------------#
def reduce_sets_of_obs(raw_edm_obs):
    bays = group_list(raw_edm_obs.values(),
                      group_by='Bay',
                      labels_list=['from_pillar',
                                   'to_pillar'],
                      avg_list=['inst_ht',
                                'tgt_ht',
                                'Temp',
                                'Pres',
                                'Humid',
                                'Mets_Correction',
                                'Calibration_Correction',
                                'raw_slope_dist',
                                'slope_dist',
                                'Est',
                                'Nth'],
                      std_list=['slope_dist'],
                      mask_by='use_for_distance')
    return bays


def adjust_alignment_survey(raw_edm_obs, pillars):
    first_pillar_nme = pillars.first().name
    last_pillar_nme = pillars.last().name
    
    setups = group_list(
        raw_edm_obs.values(),
        group_by='from_pillar',
        avg_list=['Est', 'Nth'],
        mask_by='use_for_alignment')
    
    at_pillar_os=[]
    for p in setups.values():
        pillars_in_setup = set([s['to_pillar']  for s in p['grp_from_pillar']])
        pillars_in_setup.add(p['from_pillar'])
        
        if (first_pillar_nme not in pillars_in_setup 
            or last_pillar_nme not in pillars_in_setup):
            for single_obs in p['grp_from_pillar']:
                single_obs['use_for_alignment'] = False
        else:
            #find Est, Nth of From, To pillars
            Coords = group_list(p['grp_from_pillar'],
                                group_by='to_pillar',
                                avg_list=['Est',
                                          'Nth'],
                                mask_by='use_for_alignment')
            Coords[p['from_pillar']] = {'Est':0, 'Nth':0}
        
            # find the arbitary azimuth from first to last pillar
            d0, rot0 = joins(
                Coords[first_pillar_nme]['Est'],Coords[first_pillar_nme]['Nth'],
                Coords[last_pillar_nme]['Est'],Coords[last_pillar_nme]['Nth'])
            # find the arbitary azimuth from first to each pillar
            # join the difference between the 2 Azimuths to calc Offset
            d1, rot1 = joins(
                Coords[first_pillar_nme]['Est'],Coords[first_pillar_nme]['Nth'],
                0,0)
            at_pillar_os.append(
                {'Bay':p['from_pillar'] + ' - ' + p['from_pillar'],
                 'from_pillar': p['from_pillar'],
                 'to_pillar': p['from_pillar'],
                 'observed_offset':sin(radians(rot1-rot0))*d1,
                 'use_for_alignment': True})

            for tgt in p['grp_from_pillar']:
                d2, rot2 = joins(
                    Coords[first_pillar_nme]['Est'],Coords[first_pillar_nme]['Nth'],
                    tgt['Est'],tgt['Nth'])
                tgt['observed_offset'] = sin(radians(rot2-rot0))*d2

    targets = group_list(list(raw_edm_obs.values()) + at_pillar_os,
                         group_by='to_pillar',
                         avg_list=['observed_offset'],
                         std_list=['observed_offset'],
                         mask_by='use_for_alignment')
    
    offsets = group_list(list(raw_edm_obs.values()) + at_pillar_os,
                         group_by='Bay',
                         avg_list=['observed_offset'],
                         labels_list=['from_pillar',
                                      'to_pillar'],
                         mask_by='use_for_alignment')
    pillars={}
    for ky, tgt in targets.items():
        pillars[ky]={
            'pillar':ky,
            'offset':tgt['observed_offset'],
            'OS_std_dev':tgt['std_observed_offset'],
            'sets':[o for o in offsets.values() if o['to_pillar']==ky]}
    
    return pillars


    #-------------------------------------------------------------------------------#
    #-------------------------- Functions for CORRECTIONS --------------------------#
    #-------------------------------------------------------------------------------#
def apply_calib(obs, applied, calib=[],scf=1,zpc=0,
                c1=0, c2=0, c3=0, c4=0, unit_length=1):

    if applied  == True:
        return obs, None
    else:
        if hasattr(calib,'scale_correction_factor'): scf=calib.scale_correction_factor
        if hasattr(calib,'zero_point_correction'): zpc=calib.zero_point_correction
        if hasattr(calib,'c1'): c1=calib.cyclic_one
        if hasattr(calib,'c2'): c3=calib.cyclic_two
        if hasattr(calib,'c3'): c3=calib.cyclic_three
        if hasattr(calib,'c4'): c4=calib.cyclic_four
        
        two_pi_obs0_unit_length = 2 * pi * obs / unit_length
        four_pi_obs0_unit_length = 4 * pi * obs / unit_length
        obs1 = (zpc + obs*scf
                + c1 * sin(two_pi_obs0_unit_length) 
                + c2 * cos(two_pi_obs0_unit_length)
                + c3 * sin(four_pi_obs0_unit_length)
                + c4 * cos(four_pi_obs0_unit_length))
        correction = obs1 - obs
        
        return obs1, correction


def get_delta_os(alignment_survey,o):
    os1 = float(alignment_survey[o['from_pillar']]['offset'])
    os2 = float(alignment_survey[o['to_pillar']]['offset'])

    return os2 - os1


def get_delta_rl(level_observations,o):
    rl1 = float(level_observations[o['from_pillar']]['reduced_level'])
    if 'inst_ht' in o: rl1+= o['inst_ht']

    rl2 = float(level_observations[o['to_pillar']]['reduced_level'])
    if 'inst_ht' in o: rl2+= o['tgt_ht']
    
    return rl1, rl2, rl2 - rl1


def offset_slope_correction(o, level_observations, alignment_survey, d_radius):
    h_ref = mean([float(o['reduced_level']) for o in level_observations.values()])
    dis = float(o['slope_dist'])

    delta_os = get_delta_os(alignment_survey,o)
    ref_line = sqrt(dis**2-delta_os**2)

    rl1, rl2, delta_rl = get_delta_rl(level_observations,o)
    
    d_height_factor = ((1+(rl1 - h_ref)
                       /(d_radius + h_ref))
                       * (1+(rl2 - h_ref)
                          / (d_radius + h_ref)))
    hoiz_dist = (sqrt((ref_line**2 - delta_rl**2)
                      / d_height_factor))
    o['delta_os'] = delta_os
    o['delta_height'] = delta_rl
    o['Offset_Correction'] = ref_line - dis
    o['Slope_Correction'] = hoiz_dist - ref_line
    
    return o


def slope_certified_dist(o, certified_dist, d_radius):
    h_ref = mean([float(o['reduced_level']) for o in certified_dist.values()])

    rl1, rl2, delta_rl = get_delta_rl(certified_dist, o)
    
    d_r = (certified_dist[o['to_pillar']]['distance'] 
           - certified_dist[o['from_pillar']]['distance'] )
    d_height_factor = ((1+(rl1 - h_ref)
                       /(d_radius + h_ref))
                       * (1+(rl2 - h_ref)
                          / (d_radius + h_ref)))
    
    dx = (sqrt((d_r**2 * d_height_factor + delta_rl**2) + o['delta_os']**2))
     
    return dx


def edm_std_function(edm_observations, stddev_0_adj):
    #y = Ax + B
    dist = []
    std_dev = []
    for o in edm_observations.values():
        dist.append(o['slope_dist'])
        std = o['std_slope_dist'] if o['std_slope_dist'] != 0 else stddev_0_adj
        std_dev.append(std)
    
    # Convert lists to numpy arrays for faster operations
    dist = np.array(dist).reshape((-1, 1))
    std_dev = np.array(std_dev)
    
    # Perform linear regression
    model = LinearRegression()
    model.fit(dist, std_dev)
    
    #y = Ax + B
    A = model.coef_[0]
    B = model.intercept_
    # if B < 0 :
    #     B=0
    #     A=np.average(std_dev)
    
    return {'A':A, 'B':B}


    #-------------------------------------------------------------------------------#
    #---------------------------- Functions for UNCERTAINTY ------------------------#
    #-------------------------------------------------------------------------------#

def refline_std_dev(o, alignment_survey, edm):
    # This function converts all the standard deviations from thier various 
    # units of measurements to (mm) of uncertainty in the direction of the 
    # baseline reference line.
    
    # Convert ratios to m for Groups that allow ratio and constant
    for s in o['uc_sources']:
        if s['group'] != '06':
            s['std_dev'], s['units'] = db_std_units(s['std_dev'], s['units'])
        if (any([s['group'] =='02', s['group'] =='07', s['group'] =='08'])
            and s['units'] == 'x:1'):
            s['units'] = 'm'
            s['std_dev'] = s['std_dev'] * o['Reduced_distance']
            
    uc_budget = subtotal_uc_budget(o['uc_sources'])
        
    # '01' EDM Scale Factor from calibration certificate
    if '01' in uc_budget.keys() and 'Reduced_distance' in o.keys():
        uc_budget['01']['ui'] = o['Reduced_distance'] * uc_budget['01']['std_dev'] 
    
    # '02' EDMI measurement
    if '02' in uc_budget.keys():
        uc_budget['02']['ui'] = uc_budget['02']['std_dev']
        
    # '03' EDM zero offset from LSA
    if '03' in uc_budget.keys():
        uc_budget['03']['ui'] = uc_budget['03']['std_dev']
    
    # Mets #
    if ('Temp' in o.keys() and 'Pres' in o.keys() and 'Humid' in o.keys()):
        K, L, M = mets_partial_differentials(
            edm.edm_specs.manu_ref_refrac_index or 1.000286338,
            o['Temp'] or 15,
            o['Pres'] or 1013.25,
            o['Humid'] or 60)
        # '04' Temperature
        if ('04' in uc_budget.keys() and 'Reduced_distance' in o.keys()):
            uc_budget['04']['ui'] = (o['Reduced_distance'] *
                                   K * uc_budget['04']['std_dev'])*10**-6
            
        # '05' Pressure
        if ('05' in uc_budget.keys() and 'Reduced_distance' in o.keys()):
            uc_budget['05']['ui'] = (o['Reduced_distance'] *
                                   L * uc_budget['05']['std_dev'])*10**-6
        # '06' Humidity (Baseline Eq 4.13, 4.16 and 4.18)
        if ('06' in uc_budget.keys() and 'Reduced_distance' in o.keys()):
            e = part_h2o_vap_press(dry_temp = o['Temp'],
                                   pressure = o['Pres'],
                                   rel_humidity = uc_budget['06']['std_dev'])
            uc_budget['06']['ui'] = M * e * o['Reduced_distance']*10**-6
    
    # '07' uncertianty of certified distances as a constant
    if '07' in uc_budget.keys(): 
        uc_budget['07']['ui'] = uc_budget['07']['std_dev']
        
    # '08' uncertianty of EDMI calibration parameters as a constant
    if '08' in uc_budget.keys():
        uc_budget['08']['ui'] = uc_budget['08']['std_dev']

    # '09' Centering
    if '09' in uc_budget.keys():
        uc_budget['09']['ui'] = uc_budget['09']['std_dev']

    # '10' Heights
    if '10' in uc_budget.keys():        
        if 'delta_rl' in o:
            delta_rl = o['delta_rl']
        else:
            rl1, rl2, delta_rl = get_delta_rl(alignment_survey, o)

        uc_budget['10']['ui']  = abs(uc_budget['10']['std_dev']  *
                              (delta_rl/o['Reduced_distance']))

    # '11 Offsets
    if '11' in uc_budget.keys():
        dx = o['delta_os']/o['Reduced_distance']
        uc_budget['11']['ui'] = abs(uc_budget['11']['std_dev'] * dx)
        
    return uc_budget


def subtotal_uc_budget(uc_sources):
    for s in uc_sources:
        #  add an apriori tags to section them out for report.
        if not 'apriori' in s.keys():
            s['apriori'] = True
        
        std_dev = float(s['std_dev'])
        s['ui2'] = std_dev**2
        s['ui4v'] = (((std_dev)**4)
                    /float(s['degrees_of_freedom']))
    
    subtotal = group_list(list(uc_sources),
                            group_by='group',
                            labels_list=['units'],
                            sum_list=['ui2',
                                      'ui4v'])
    
    for uc in subtotal.values():
        if len(uc['grp_group'])>1:
            std_dev = sqrt(uc['sum_ui2'])
            v_eff = ((std_dev**4)
                  /uc['sum_ui4v'])
            t95 = t.ppf(1-0.025,df=v_eff)
            uc['std_dev']=std_dev
            uc['degrees_of_freedom'] = v_eff
            uc['k']= t95
        else:
            uc['k']= uc['grp_group'][0]['k']
            uc['std_dev']= uc['grp_group'][0]['std_dev']
            uc['degrees_of_freedom']= uc['grp_group'][0]['degrees_of_freedom']
        uc.pop('sum_ui2')
        uc.pop('sum_ui4v')
    
    return subtotal


def sum_uc_budget(uc_budget):
    sum_ui2 = 0; sum_ui4v = 0
    for uc in uc_budget.values():
        uc['ui95']=uc['ui']*uc['k']
        sum_ui2 += uc['ui']**2
        sum_ui4v += (uc['ui']**4)/float(uc['degrees_of_freedom'])
    
    uc = sqrt(sum_ui2)
    v_eff = ((uc**4)
          /sum_ui4v)
    t95 = t.ppf(1-0.025,df=v_eff)
    u95 = uc * t95
    combined_uc = {'std_dev':uc,
                  'degrees_of_freedom': v_eff,
                  'k': t95,
                  'uc95': u95}
   
    return combined_uc

 
def add_typeA(d, matrix_y, dof):
    # Only used for calibration of EDMI
    # add on the uncertainty for the calibration parameters
    type_a = deepcopy(d['uc_sources'])
    # '08 calculate uncertainty of instrument correction
    if len(matrix_y)==2:
        s_dev = (matrix_y[0]['std_dev']
                 + matrix_y[1]['std_dev'] * d['Reduced_distance'])
    
    if len(matrix_y)==4:
        s_dev = (matrix_y[0]['std_dev']
                 + matrix_y[1]['std_dev'] * d['Reduced_distance']
                 + matrix_y[2]['std_dev'] * sin(d['d_term'])
                 + matrix_y[3]['std_dev'] * cos(d['d_term']))
    
    if len(matrix_y)==6:
        s_dev = (matrix_y[0]['std_dev']
                 + matrix_y[1]['std_dev'] * d['Reduced_distance']
                 + matrix_y[2]['std_dev'] * sin(d['d_term'])
                 + matrix_y[3]['std_dev'] * cos(d['d_term'])
                 + matrix_y[4]['std_dev'] * sin(2*d['d_term'])
                 + matrix_y[5]['std_dev'] * cos(2*d['d_term']))
    
    type_a.append({'group': '08',
                    'ab_type':'A',
                    'distribution':'N',
                    'units': 'm',
                    'std_dev': s_dev,
                    'degrees_of_freedom':dof,
                    'k':t.ppf(1-0.025,df=dof),
                    'apriori': False,
                    'description':'Uncertainty of LSA EDMI correction'})
    
    return type_a

def add_typeB(uc_sources, d, matrix_y, dof):
    # Only used for calibration of the baseline
    # '03 LSA The EDM zero offset uncertainty 
    type_b=deepcopy(uc_sources)
    type_b.append({'group': '03',
                    'ab_type':'A',
                    'distribution':'N',
                    'units': 'm',
                    'std_dev': matrix_y[-1]['std_dev'],
                    'degrees_of_freedom':dof,
                    'k':t.ppf(1-0.025,df=dof),
                    'apriori': False,
                    'description':'ZPC uncertainty'})
    
    # '07 LSA type A uncertainty
    type_b.append({'group': '07',
                    'ab_type':'A',
                    'distribution':'N',
                    'units': 'm',
                    'std_dev': d['std_dev'],
                    'degrees_of_freedom':dof,
                    'k':t.ppf(1-0.025,df=dof),
                    'apriori': False,
                    'description':'LSA uncertainty'})
    return type_b


def is_float(n):
    try:
        float(n)
    except:
        return False
    else:
        return True


def float_or_null (n):
    if is_float(n):
        return float(n)
    else:
        return None


def validate_survey2(pillar_survey, baseline=None, calibrations=None,
                     raw_edm_obs=None, raw_lvl_obs=None):
    Errs = []
    Wrns = []

    # Determine calibration type
    calibration_type = 'I' if hasattr(pillar_survey, 'auto_base_calibration') else 'B'

    # Baseline Calibration errors in instrument calibration
    if calibration_type == 'I':
        if pillar_survey.auto_base_calibration:
            site_pk = pillar_survey.site.pk
            site = str(pillar_survey.site)
        else:
            site_pk = pillar_survey.calibrated_baseline.baseline.pk
            site = str(pillar_survey.calibrated_baseline.baseline)

        if pillar_survey.auto_base_calibration:
            qry_obj = (
                Pillar_Survey.objects.filter(
                    baseline=site_pk,
                    results__status='publish',
                    survey_date__lte=pillar_survey.survey_date
                ).order_by('-survey_date')
            )
            if not qry_obj.exists():
                Errs.append(
                    f'There is no calibration of the {site} baseline for the '
                    f'{pillar_survey.survey_date.strftime("%d %b, %Y")} '
                    f'when your EDM Instrumentation calibration survey was observed.'
                )

        # Errors for testing cyclic errors
        if pillar_survey.test_cyclic:
            if not pillar_survey.edm.edm_specs.unit_length:
                Errs.append(
                    'In order for Medjil to test for cyclic errors, the instrument '
                    'unit length must be specified. Insufficient data has been supplied '
                    'for the EDM Instrument Model used for this calibration.'
                )

    # Instrumentation Selection Errors
    ucb = pillar_survey.uncertainty_budget
    if calibrations:
        if calibration_type == 'B':
            if ucb.auto_EDMI_scf or ucb.auto_EDMI_scf_drift:
                if not calibrations.get('edmi', []):    
                    Errs.append(
                        'Uncertainty budget sources that are dependent on EDM Instrumentation calibration certificates '
                        'have been selected in the uncertainty budget.'
                    )
                    Errs.append(
                        f'There are no calibration records for {pillar_survey.edm} '
                        f'with prism {pillar_survey.prism}.'
                    )
                    Errs.append(
                        'EDM Instrumentation calibration certificates need to be current for the date of survey: '
                        f'{pillar_survey.survey_date.strftime("%d %b, %Y")}'
                    )
            if not calibrations.get('staff'):
                Wrns.append(f'There is no calibration record for {pillar_survey.staff}')
        
        if pillar_survey.hygrometer:
            if not calibrations.get('hygro') and ucb.auto_humi_zpc:
                Errs.append(
                    'Uncertainty budget sources that are dependent on hygrometer calibration certificates '
                    'have been selected in the uncertainty budget.'
                )
            if not calibrations.get('hygro') and not pillar_survey.hygro_calib_applied:
                Errs.append(
                    f'There is no calibration record for {pillar_survey.hygrometer}. '
                    'Hygrometer calibration certificates need to be current for the date of survey: '
                    f'{pillar_survey.survey_date.strftime("%d %b, %Y")}'
                )
        
        if not pillar_survey.hygrometer and ucb.auto_humi_zpc:
            Errs.append(
                'Uncertainty budget sources that are dependent on hygrometer calibration certificates '
                'have been selected in the uncertainty budget, but no hygrometer has been selected.'
            )
            
        if not pillar_survey.hygrometer and not pillar_survey.hygro_calib_applied:
            Errs.append(
                'Hygrometer calibration corrections have not been applied prior to input. '
                'A calibration certificate is required to apply calibrations to raw observations, but no hygrometer has been selected.'
            )

        if not calibrations.get('baro') and ucb.auto_pressure_zpc:
            Errs.append(
                'Uncertainty budget sources that are dependent on barometer calibration certificates '
                'have been selected in the uncertainty budget.'
            )
            Errs.append(
                f'There is no calibration record for {pillar_survey.barometer}. '
                'Barometer calibration certificates need to be current for the date of survey: '
                f'{pillar_survey.survey_date.strftime("%d %b, %Y")}'
            )

        if not calibrations.get('them') and ucb.auto_temp_zpc:
            Errs.append(
                'Uncertainty budget sources that are dependent on thermometer calibration certificates '
                'have been selected in the uncertainty budget.'
            )
            Errs.append(
                f'There is no calibration record for {pillar_survey.thermometer}. '
                'Thermometer calibration certificates need to be current for the date of survey: '
                f'{pillar_survey.survey_date.strftime("%d %b, %Y")}'
            )
        
        if not calibrations.get('them') and pillar_survey.thermo_calib_applied:
            Wrns.append(f'There is no calibration record for the thermometer {pillar_survey.thermometer}')
        elif not calibrations.get('them'):
            Errs.append(f'There is no calibration record for {pillar_survey.thermometer}')
            Errs.append(
                'Thermometer calibration certificates need to be current for the date of survey: '
                f'{pillar_survey.survey_date.strftime("%d %b, %Y")}'
            )
            
        if not calibrations.get('baro') and pillar_survey.baro_calib_applied:
            Wrns.append(f'There is no calibration record for the barometer {pillar_survey.barometer}')
        elif not calibrations.get('baro'):
            Errs.append(f'There is no calibration record for {pillar_survey.barometer}')
            Errs.append('Barometer calibration certificates need to be current for the date of survey: '
                        + pillar_survey.survey_date.strftime("%d %b, %Y")
            )
                
        if pillar_survey.hygrometer:
            if not calibrations.get('hygro') and pillar_survey.hygro_calib_applied:
                Errs.append(f'There is no calibration record for the hygrometer {pillar_survey.hygrometer}')
            elif not calibrations.get('hygro'):
                Errs.append(f'There is no calibration record for {pillar_survey.hygrometer}')
                Errs.append('Hygrometer calibration certificates need to be current for the date of survey: '
                            + pillar_survey.survey_date.strftime("%d %b, %Y"))

        if calibration_type == 'B':
            # Check for thermometer2 and its calibration
            if pillar_survey.thermometer2 and calibrations.get('them2') is None:
                if pillar_survey.thermo2_calib_applied:
                    Wrns.append(f'There is no calibration record for the themometer {pillar_survey.thermometer2}')
                elif not calibrations.get('them2'):
                    Errs.append(f'There is no calibration record for {pillar_survey.thermometer2}')
                    Errs.append(
                        'Thermometer calibration certificates need to be current for the date of survey: '
                        + pillar_survey.survey_date.strftime("%d %b, %Y")
                    )
        
            # Check for barometer2 and its calibration
            if pillar_survey.barometer2 and calibrations.get('baro2') is None:
                if pillar_survey.baro2_calib_applied:
                    Wrns.append(f'There is no calibration record for the barometer {pillar_survey.barometer2}')
                elif not calibrations.get('baro2'):
                    Errs.append(f'There is no calibration record for {pillar_survey.barometer2}')
                    Errs.append(
                        'Barometer calibration certificates need to be current for the date of survey: '
                        + pillar_survey.survey_date.strftime("%d %b, %Y")
                    )
        
            # Check for hygrometer2 and its calibration
            if pillar_survey.hygrometer2 and calibrations.get('hygro2') is None:
                if pillar_survey.hygro2_calib_applied:
                    Wrns.append(f'There is no calibration record for the hygrometer {pillar_survey.hygrometer2}')
                elif not calibrations.get('hygro2'):
                    Errs.append(f'There is no calibration record for {pillar_survey.hygrometer2}')
                    Errs.append(
                        'Hygrometer calibration certificates need to be current for the date of survey: '
                        + pillar_survey.survey_date.strftime("%d %b, %Y")
                    )
                    
    # Raw EDM Observations
    if raw_edm_obs and baseline:
        for o in raw_edm_obs.values():
            # create a note for all excluded observations
            if not o['use_for_distance']:
                Wrns.append(
                    f'The observation "{o["from_pillar"]}--{o["to_pillar"]}" '
                    f' with a raw slope distance of "{o["raw_slope_dist"]:.4f}"'
                    ' has been excluded by the user during processing.')
            if 'use_for_alignment' in o:
                if not o['use_for_alignment']:
                    Wrns.append(
                        f'The observation "{o["from_pillar"]}--{o["to_pillar"]}" '
                        f' with a raw slope distance of "{o["raw_slope_dist"]}"'
                        ' has been excluded from the calculation of pillar offsets by the user during processing.')
        
        # Checks for alignment survey
        if calibration_type =='B':
            #'use_for_distance' checks
            # Each pillar must be observed from at least 2 other pillars
            bays=[]
            pillars = [p.name for p in baseline['pillars']]
            pillar_cnt = dict(zip(pillars,[0]*len(pillars)))
            for o in raw_edm_obs.values():
                if o['use_for_distance']:
                    bay=[min([pillars.index(o['from_pillar']), pillars.index(o['to_pillar'])]),
                         max([pillars.index(o['from_pillar']), pillars.index(o['to_pillar'])])]
                    if not bay in bays: 
                        bays.append(bay)
                        pillar_cnt[o['from_pillar']]+=1
                        pillar_cnt[o['to_pillar']]+=1
            
            for p, cnt in pillar_cnt.items():
                if cnt < 2:
                    Errs.append('Pillar "' + str(p) + '" has been observed from ' 
                                + str(cnt) + ' other pillars for determining the certified distance.')
            
            #'use_for_alignment' checks
            # setups used for alignment survey must have first and last pillar
            setups = group_list(raw_edm_obs.values(),
                                group_by='from_pillar',
                                mask_by='use_for_alignment')
            for p in setups.values():
                pillars_in_setup = set([s['to_pillar']  for s in p['grp_from_pillar']])
                pillars_in_setup.add(p['from_pillar'])
                # Look for first to last pillar observation
                if (pillars[0] not in pillars_in_setup 
                    or pillars[-1] not in pillars_in_setup):
                    for single_obs in p['grp_from_pillar']:
                        single_obs['use_for_alignment'] = False
            
            # Each pillar must be observed from a pillar setup the includes the first and last pillar
            bays=[]
            pillar_cnt = dict(zip(pillars,[0]*len(pillars)))
            for o in raw_edm_obs.values():
                if o['use_for_alignment']:
                    bay=[min([pillars.index(o['from_pillar']), pillars.index(o['to_pillar'])]),
                         max([pillars.index(o['from_pillar']), pillars.index(o['to_pillar'])])]
                    if not bay in bays: 
                        bays.append(bay)
                        pillar_cnt[o['from_pillar']]+=1
                        pillar_cnt[o['to_pillar']]+=1
            
            for p, cnt in pillar_cnt.items():
                if cnt < 1:
                    Errs.append(
                        'Pillar "' + str(p) + '" has been observed from ' + str(cnt)
                        + ' other pillar setup that include the first and last'
                        + 'pillar. This is required for determining the offset.')
                        
            # Each baseline calibration pillar survey must have from first to last pillar
            if not [0, len(pillars) - 1] in bays:
                Errs.append('The pillar survey used for the calibration of the baseline'
                            +' must include an observation from the first to the last'
                            +' pillar. The current pillar survey is missing observation'
                            +' Pillar '+ str(pillars[0]) +' to '+ 'Pillar ' 
                            + str(pillars[-1]) +'.')

    # Atmospheric Corrections
    try:
        pillar_survey.edm.edm_specs.atmospheric_correction(
            o={'raw_slope_dist':100, 'Temp':20, 'Pres':1013.25, 'Humid':60},
            null_correction=pillar_survey.mets_applied)
            
    except Exception as e:
        Errs.append(f'Insufficient data has been supplied to apply atmospheric corrections. \
                    The following error occured when trying to use specifications provided for \
                    {pillar_survey.edm.edm_specs}: {e}')

    # Date Warnings
    if pillar_survey.survey_date > pillar_survey.computation_date:
        Wrns.append('The computation date is earlier than the survey date.')

    if hasattr(pillar_survey, 'accreditation'):
        if not (pillar_survey.accreditation.valid_from_date <= pillar_survey.survey_date <= pillar_survey.accreditation.valid_to_date):
            Wrns.append(
                'The company does not have a valid accreditation for the date of the survey used to calibrate the EDM baseline.'
            )

    return {'Errors': Errs, 'Warnings': Wrns}


def add_calib_uc2(uc_sources, calib, pillar_survey):
    """
    Add calibration uncertainty contributions based on the pillar survey model instance.
    """
    # Check for EDMI calibration and that this is calibrate the baseline
    if len(calib['edmi']) > 0 and not hasattr(pillar_survey, 'calibrated_baseline'):
        d2 = pillar_survey.survey_date
        calib_edmi = calib['edmi'][0]

        if pillar_survey.uncertainty_budget.auto_EDMI_scf:
            uc_sources.append(
                {
                    'group': '01',
                    'ab_type': 'B',
                    'distribution': 'N',
                    'units': 'x:1',
                    'std_dev': calib_edmi.scf_std_dev,
                    'degrees_of_freedom': calib_edmi.degrees_of_freedom,
                    'k': calib_edmi.scf_coverage_factor,
                    'description': 'EDMI Reg13 Scale correction factor'
                }
            )

        # Calculate the linear trend for EDMI calibration history
        calib_dates = []
        calib_scf = []
        d0 = date(1900, 1, 1)
        for c in calib['edmi']:
            d1 = c.calibration_date
            calib_dates.append((d1 - d0).days)
            calib_scf.append(c.scale_correction_factor)

        calib_dates = np.array(calib_dates, dtype=object).reshape((-1, 1))
        calib_scf = np.array(calib_scf, dtype=object)
        model = LinearRegression().fit(calib_dates, calib_scf)

        # Calculate drift over time
        A = model.coef_[0]
        B = model.intercept_
        scf_d1 = A * ((d1 - d0).days) + B
        scf_d2 = A * ((d2 - d0).days) + B
        xyTrend = [
            {'x': d1.isoformat()[:10], 'y': scf_d1},
            {'x': d2.isoformat()[:10], 'y': scf_d2}
        ]
        calib['edmi_drift'] = {'A': A, 'B': B, 'xyTrend': xyTrend}

        if pillar_survey.uncertainty_budget.auto_EDMI_scf_drift:
            uc_sources.append(
                {
                    'group': '01',
                    'ab_type': 'B',
                    'distribution': 'N',
                    'units': 'x:1',
                    'std_dev': abs(scf_d2 - calib_edmi.scale_correction_factor),
                    'degrees_of_freedom': 30,
                    'k': sqrt(3),
                    'description': 'EDM scale factor (drift over time)'
                }
            )

    # Distance Instrument Rounding
    if pillar_survey.uncertainty_budget.auto_EDMI_round:
        uc_sources.append(
            {
                'group': '02',
                'ab_type': 'B',
                'distribution': 'R',
                'units': 'm',
                'std_dev': (float(pillar_survey.edm.edm_specs.measurement_increments) / 2) / sqrt(3),
                'degrees_of_freedom': 100,
                'k': sqrt(3),
                'description': 'Distance Instrument Rounding'
            }
        )

    # Thermometer Correction Factor
    if pillar_survey.thermometer and pillar_survey.uncertainty_budget.auto_temp_zpc:
        uc_sources.append(
            {
                'group': '04',
                'ab_type': 'B',
                'distribution': 'N',
                'units': '°C',
                'std_dev': calib['them'].zpc_std_dev,
                'degrees_of_freedom': calib['them'].degrees_of_freedom,
                'k': calib['them'].zpc_coverage_factor,
                'description': 'Thermometer calibrated correction factor'
            }
        )

    # Thermometer Rounding
    if pillar_survey.uncertainty_budget.auto_temp_rounding:
        uc_sources.append(
            {
                'group': '04',
                'ab_type': 'B',
                'distribution': 'R',
                'units': '°C',
                'std_dev': (float(pillar_survey.thermometer.mets_specs.measurement_increments) / 2) / sqrt(3),
                'degrees_of_freedom': 100,
                'k': sqrt(3),
                'description': 'Thermometer Rounding'
            }
        )

    # Barometer Correction Factor
    if pillar_survey.barometer and pillar_survey.uncertainty_budget.auto_pressure_zpc:
        uc_sources.append(
            {
                'group': '05',
                'ab_type': 'B',
                'distribution': 'N',
                'units': 'hPa',
                'std_dev': calib['baro'].zpc_std_dev,
                'degrees_of_freedom': calib['baro'].degrees_of_freedom,
                'k': calib['baro'].zpc_coverage_factor,
                'description': 'Barometer calibrated correction factor'
            }
        )

    # Barometer Rounding
    if pillar_survey.uncertainty_budget.auto_pressure_rounding:
        uc_sources.append(
            {
                'group': '05',
                'ab_type': 'B',
                'distribution': 'R',
                'units': 'hPa',
                'std_dev': (float(pillar_survey.barometer.mets_specs.measurement_increments) / 2) / sqrt(3),
                'degrees_of_freedom': 100,
                'k': sqrt(3),
                'description': 'Barometer Rounding'
            }
        )

    # Hygrometer Correction Factor
    if pillar_survey.hygrometer and pillar_survey.uncertainty_budget.auto_humi_zpc:
        uc_sources.append(
            {
                'group': '06',
                'ab_type': 'B',
                'distribution': 'N',
                'units': '%',
                'std_dev': calib['hygro'].zpc_std_dev,
                'degrees_of_freedom': calib['hygro'].degrees_of_freedom,
                'k': calib['hygro'].zpc_coverage_factor,
                'description': 'Hygrometer calibrated correction factor'
            }
        )

    # Hygrometer Rounding
    if pillar_survey.hygrometer and pillar_survey.uncertainty_budget.auto_humi_rounding:
        uc_sources.append(
            {
                'group': '06',
                'ab_type': 'B',
                'distribution': 'R',
                'units': '%',
                'std_dev': (float(pillar_survey.hygrometer.mets_specs.measurement_increments) / 2) / sqrt(3),
                'degrees_of_freedom': 100,
                'k': sqrt(3),
                'description': 'Hygrometer Rounding'
            }
        )

    return uc_sources


def add_certified_dist_uc2(o, pillar_survey, uc_sources, std_dev_matrix, dof):
    """
    Adds certified distance uncertainty to the uncertainty budget for the pillar survey.
    """
    # Deep copy of existing uncertainty contributions
    cd_uc = deepcopy(uc_sources)

    # Add certified distance uncertainty if enabled
    if pillar_survey.uncertainty_budget.auto_cd:
        # switch the from and to pillar if obs is reverse direction
        if o['bay'] in std_dev_matrix.keys():
            bay = o['bay']
        else:
            bay = o['to_pillar'] + ' - ' + o['from_pillar']
        cd_uc.append(
            {
                'group': '07',
                'ab_type': 'A',
                'distribution': 'N',
                'units': 'm',
                'std_dev': std_dev_matrix[bay]['std_uncertainty'],
                'degrees_of_freedom': dof,
                'k': t.ppf(1 - 0.025, df=dof),  # 95% confidence interval
                'description': 'Uncertainty of Certified Distance'
            }
        )

    return cd_uc

def add_surveyed_uc2(o, edm_trend, pillar_survey, uc_sources, alignment_survey):
    """
    Adds surveyed uncertainties to the uncertainty budget based on the pillar survey model instance.
    :param o: Observation data dictionary.
    :param edm_trend: Linear regression coefficients for EDM uncertainties.
    :param pillar_survey: uPillarSurvey model instance.
    :param uc_sources: List of existing uncertainty contributions.
    :param alignment_survey: Dictionary containing alignment survey data.
    :return: Updated uncertainty contributions.
    """
    # Deep copy of the existing uncertainty contributions
    surveyed_uc = deepcopy(uc_sources)

    # '02' - Linear Regression on EDM Distance Standard Deviations
    if pillar_survey.uncertainty_budget.auto_EDMI_lr:
        surveyed_uc.append(
            {
                'group': '02',
                'ab_type': 'B',
                'distribution': 'N',
                'units': 'm',
                'std_dev': o['slope_dist'] * edm_trend['A'] + edm_trend['B'],
                'k': t.ppf(1 - 0.025, df=30),
                'degrees_of_freedom': 30,
                'description': (
                    'Linear regression on EDM distance standard deviations '
                    f'UC = k x ({edm_trend["A"] * 1000:.6f} x L + {edm_trend["B"] * 1000:.2f}) mm'
                )
            }
        )

    # '10' - Pillar Certified Height Differences
    if pillar_survey.uncertainty_budget.auto_hgts:
        frm_rl = alignment_survey[o['from_pillar']]
        to_rl = alignment_survey[o['to_pillar']]

        frm_rl['std_dev'] = (
            float(frm_rl['rl_uncertainty']) / float(frm_rl['k_rl_uncertainty'])
        )
        to_rl['std_dev'] = (
            float(to_rl['rl_uncertainty']) / float(to_rl['k_rl_uncertainty'])
        )
        km = abs((to_rl['std_dev']/12)**2 - (frm_rl['std_dev']/12)**2) #Even if it is not 12rootK this should still work,
        comb_std = sqrt(km * 12)

        surveyed_uc.append(
            {
                'group': '10',
                'ab_type': 'B',
                'distribution': 'N',
                'units': 'm',
                'std_dev': comb_std,
                'degrees_of_freedom': 30,
                'k': t.ppf(1 - 0.025, df=30),
                'description': 'Pillar certified height differences'
            }
        )

    # '11' - Pillar Alignment Survey Offset Uncertainty
    if pillar_survey.uncertainty_budget.auto_os:
        frm_os = alignment_survey[o['from_pillar']]
        to_os = alignment_survey[o['to_pillar']]

        if 'OS_std_dev' not in frm_os:
            frm_os['OS_std_dev'] = (
                float(frm_os['os_uncertainty']) / float(frm_os['k_os_uncertainty'])
            )
        if 'OS_std_dev' not in to_os:
            to_os['OS_std_dev'] = (
                float(to_os['os_uncertainty']) / float(to_os['k_os_uncertainty'])
            )

        comb_std = sqrt(
            frm_os['OS_std_dev']**2 + to_os['OS_std_dev']**2
        )

        surveyed_uc.append(
            {
                'group': '11',
                'ab_type': 'B',
                'distribution': 'N',
                'units': 'm',
                'std_dev': comb_std,
                'degrees_of_freedom': 30,
                'k': t.ppf(1 - 0.025, df=30),
                'description': 'Pillar alignment survey offset uncertainty'
            }
        )

    return surveyed_uc
    
def raw_edm_obs_reductions(pillar_survey):
    edm_observations_qs = pillar_survey.edm_observation_set.all()
    calib = calibrations_qry2(pillar_survey)
    
    # Get the raw_edm_obs and the raw_lvl_obs in dict like cleaned form data
    edm_observations = list(edm_observations_qs)
    raw_edm_obs = {
        str(obs.id): {
            **model_to_dict(obs),
            'from_pillar': obs.from_pillar.name if obs.from_pillar else None,
            'to_pillar': obs.to_pillar.name if obs.to_pillar else None,
        }
        for obs in edm_observations
    }    
    lvl_obs = list(pillar_survey.level_observation_set.all())
    raw_lvl_obs = {
        str(obs.pillar.name): {
            **model_to_dict(obs),
            'pillar': obs.pillar.name,
            'std_dev': obs.rl_standard_deviation
        }
        for obs in lvl_obs
    }
    
    def calibrate_value(cal_cert, raw_value, calibration_applied):
        """Applies calibration if the cal_cert is present, else returns raw value."""
        if cal_cert:
            return cal_cert.apply_calibration(raw_value, calibration_applied)
        return raw_value, 0

    def compute_average(cal_cert1, cal_cert2, raw_value1, raw_value2, calibration_applied1, calibration_applied2):
        """Computes the calibrated value, averaging if both cal_certs exist."""
        calibrated1, _ = calibrate_value(cal_cert1, raw_value1, calibration_applied1)
        if not cal_cert2 or not raw_value2:
            return calibrated1
        calibrated2, _ = calibrate_value(cal_cert2, raw_value2, calibration_applied2)
        return (calibrated1 + calibrated2) / 2
    
    for o in raw_edm_obs.values():
        o['Temp'] = compute_average(
            calib['them'], calib.get('them2'), o['raw_temperature'], o['raw_temperature2'], 
            pillar_survey.thermo_calib_applied, pillar_survey.thermo2_calib_applied)
    
        o['Pres'] = compute_average(
            calib['baro'], calib.get('baro2'), o['raw_pressure'], o['raw_pressure2'],
            pillar_survey.baro_calib_applied, pillar_survey.baro2_calib_applied)
        
        o['Humid'] = compute_average(
            calib['hygro'], calib.get('hygro2'), o['raw_humidity'], o['raw_humidity2'],
            pillar_survey.hygro_calib_applied, pillar_survey.hygro2_calib_applied)
            
        #  Calculate calibration correction for EDM Instrumentation
        _, o['Calibration_Correction'] = apply_calib(
            float(o['raw_slope_dist']),
            pillar_survey.edmi_calib_applied,
            calib['edmi'].first(),
            unit_length = pillar_survey.edm.edm_specs.unit_length)
        if not o['Calibration_Correction']:o['Calibration_Correction']=0

        o['Mets_Correction'] = (
            pillar_survey.edm.edm_specs.atmospheric_correction(
                o = o,
                null_correction=pillar_survey.mets_applied,
                co2_content=pillar_survey.co2_content)
        )
        
        o['slope_dist'] = (float(o['raw_slope_dist'] )
                           + o['Calibration_Correction']
                           + o['Mets_Correction'])
        
        # Calculate the Est and Nth for all in raw'
        o['Bay']= o['from_pillar'] + ' - ' + o['to_pillar']
        ht_diff = (
            float(raw_lvl_obs[o['to_pillar']]['reduced_level'])
            - float(raw_lvl_obs[o['from_pillar']]['reduced_level']))
        hz_dist = sqrt(
            (float(o['slope_dist']))**2
            - ht_diff**2)
        o['Est'], o['Nth'] = radiations(
            0, 0,
            float(o['hz_direction']),
            hz_dist)
    
    return raw_edm_obs, raw_lvl_obs, calib