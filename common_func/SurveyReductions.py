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
import numpy as np
from common_func.Convert import (
    group_list,
    db_std_units)
from math import sqrt, sin, cos, radians, pi
from datetime import date
from statistics import mean
from scipy.stats import t
from sklearn.linear_model import LinearRegression
from geodepy.survey import (
    joins, first_vel_corrn, first_vel_params,
    part_h2o_vap_press, mets_partial_differentials)
from baseline_calibration.models import Pillar_Survey
from copy import deepcopy

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
    obs0 = float(obs)
    if applied  == True:
        obs1 = obs0
    else:
        if hasattr(calib,'scale_correction_factor'): scf=calib.scale_correction_factor
        if hasattr(calib,'zero_point_correction'): zpc=calib.zero_point_correction
        if hasattr(calib,'c1'): c1=calib.cyclic_one
        if hasattr(calib,'c2'): c3=calib.cyclic_two
        if hasattr(calib,'c3'): c3=calib.cyclic_three
        if hasattr(calib,'c4'): c4=calib.cyclic_four
        
        two_pi_obs0_unit_length = 2 * pi * obs0 / unit_length
        four_pi_obs0_unit_length = 4 * pi * obs0 / unit_length
        obs1 = (zpc + obs0*scf
                + c1 * sin(two_pi_obs0_unit_length) 
                + c2 * cos(two_pi_obs0_unit_length)
                + c3 * sin(four_pi_obs0_unit_length)
                + c4 * cos(four_pi_obs0_unit_length))
    correction = obs1 - obs0
    
    return obs1, correction


def get_mets_params(edm, mets_applied=True):
    if not mets_applied:
        c = edm.edm_specs.c_term
        d = edm.edm_specs.d_term
        if not c or not d:
            mets_parameters = first_vel_params(
                edm.edm_specs.carrier_wavelength/1000,
                edm.edm_specs.frequency,
                edm.edm_specs.manu_ref_refrac_index)
            if not edm.edm_specs.c_term:
                edm.edm_specs.c_term = mets_parameters[0]
            if not edm.edm_specs.d_term:
                edm.edm_specs.d_term = mets_parameters[1]
        

def edm_mets_correction(o, edm, mets_applied, co2_content=None):
    if not mets_applied:
        o['Mets_Correction'] = first_vel_corrn(
            dist = float(o['raw_slope_dist']),
            first_vel_param = (float(edm.edm_specs.c_term),
                               float(edm.edm_specs.d_term)),
            temp = o['Temp'],
            pressure = o['Pres'],
            rel_humidity = o['Humid'],
            CO2_ppm = co2_content,
            wavelength = edm.edm_specs.carrier_wavelength/1000)
    else:
        o['Mets_Correction'] = 0
    return o


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
        K, L, M = mets_partial_differentials(edm.edm_specs.manu_ref_refrac_index,
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


def add_surveyed_uc(o, edm_trend, pillar_survey, uc_sources, alignment_survey):
    # '02'
    surveyed_uc = deepcopy(uc_sources)
    if pillar_survey['uncertainty_budget'].auto_EDMI_lr:
        surveyed_uc.append(
            {'group': '02',
            'ab_type':'B',
            'distribution':'N',
            'units': 'm',
            'std_dev': o['slope_dist']*edm_trend['A'] + edm_trend['B'],
            'k':t.ppf(1-0.025,df=30),
            'degrees_of_freedom':30,
            'description':('Linear regression on EDM distance standard deviations' +
                           f' UC = k x ({edm_trend["A"]*1000:.6f} x L + {edm_trend["B"]*1000:.2f}) mm')})
    
    # '10'
    if pillar_survey['uncertainty_budget'].auto_hgts:
        frm_rl= alignment_survey[o['from_pillar']]
        to_rl = alignment_survey[o['to_pillar']]
        frm_rl['std_dev']= (float(frm_rl['rl_uncertainty'])/
                            float(frm_rl['k_rl_uncertainty']))
        to_rl['std_dev'] = (float(to_rl['rl_uncertainty'])/
                            float(to_rl['k_rl_uncertainty']))
    
        comb_std = sqrt(float(frm_rl['std_dev'])**2
                        + float(to_rl['std_dev'])**2)
            
        surveyed_uc.append(
            {'group': '10',
            'ab_type':'B',
            'distribution':'N',
            'units': 'm',
            'std_dev': comb_std,
            'degrees_of_freedom':30,
            'k':t.ppf(1-0.025,df=30),
            'description':'Pillar certified height differences'})
       
    # '11'
    if pillar_survey['uncertainty_budget'].auto_os:
        frm_os= alignment_survey[o['from_pillar']]
        to_os = alignment_survey[o['to_pillar']]
        if 'OS_std_dev' not in frm_os:
            frm_os['OS_std_dev']= (float(frm_os['os_uncertainty'])/
                                   float(frm_os['k_os_uncertainty']))
        if 'OS_std_dev' not in to_os:
            to_os['OS_std_dev']= (float(to_os['os_uncertainty'])/
                                  float(to_os['k_os_uncertainty']))
        
        comb_std = sqrt(frm_os['OS_std_dev']**2 +
                        frm_os['OS_std_dev']**2)
    
        surveyed_uc.append(
            {'group': '11',
            'ab_type':'B',
            'distribution':'N',
            'units': 'm',
            'std_dev': comb_std,
            'degrees_of_freedom':30,
            'k':t.ppf(1-0.025,df=30),
            'description':'Pillar alignment survey offset uncertainty'})

    return surveyed_uc


def add_certified_dist_uc(o, pillar_survey, uc_sources, std_dev_matrix, dof):
    # Only used for calibration of EDMI
    cd_uc = deepcopy(uc_sources)
    # '07'
    if pillar_survey['uncertainty_budget'].auto_cd:
        if o['Bay'] in std_dev_matrix.keys():
            bay = o['Bay']
        else:
            bay = o['to_pillar'] + ' - ' + o['from_pillar']
        
        cd_uc.append(
            {'group': '07',
            'ab_type':'A',
            'distribution':'N',
            'units': 'm',
            'std_dev': std_dev_matrix[bay]['std_uncertainty'],
            'degrees_of_freedom':dof,
            'k':t.ppf(1-0.025,df=dof),
            'description':'Uncertainty of Certified Distance'})

    return cd_uc
    
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


def add_calib_uc(uc_sources, calib, pillar_survey):

    if len(calib['edmi'])>0 and 'calibrated_baseline' not in pillar_survey.keys():
        d2=pillar_survey['survey_date']
        calib_edmi = calib['edmi'][0]
     
        if pillar_survey['uncertainty_budget'].auto_EDMI_scf:
            uc_sources.append(
                {'group': '01',
                 'ab_type':'B',
                 'distribution':'N',
                 'units': 'x:1',
                 'std_dev': calib_edmi.scf_std_dev,
                 'degrees_of_freedom':calib_edmi.degrees_of_freedom,
                 'k':calib_edmi.scf_coverage_factor,
                 'description':'EDMI Reg13 Scale correction factor'})
        
        # calculate the linear trend for edmi calibration history #
        calib_dates=[]
        calib_scf=[]
        d0 = date(1900,1,1)
        for c in calib['edmi']:
            d1 = c.calibration_date
            calib_dates.append((d1-d0).days)
            calib_scf.append(c.scale_correction_factor)
        
        calib_dates=np.array(calib_dates, dtype=object).reshape((-1, 1))
        calib_scf=np.array(calib_scf, dtype=object)
        model = LinearRegression().fit(calib_dates, calib_scf)
        #y = Ax + B
        A = model.coef_[0]
        B = model.intercept_
        scf_d1 = A*((d1-d0).days) + B
        scf_d2 = A*((d2-d0).days) + B
        xyTrend = [
                 {'x':d1.isoformat()[:10], 'y':scf_d1},
                 {'x':d2.isoformat()[:10], 'y':scf_d2}
                ]
        calib['edmi_drift'] = {'A':A,'B':B, 'xyTrend':xyTrend}
        
        if pillar_survey['uncertainty_budget'].auto_EDMI_scf_drift:
            uc_sources.append(
                {'group': '01',
                'ab_type':'B',
                'distribution':'N',
                'units': 'x:1',
                'std_dev': abs(scf_d2-calib_edmi.scale_correction_factor),
                'degrees_of_freedom':30,
                'k':sqrt(3),
                'description':'EDM scale factor (drift over time)'})
    
    if pillar_survey['uncertainty_budget'].auto_EDMI_round:
        uc_sources.append(
            {'group': '02',
            'ab_type':'B',
            'distribution':'R',
            'units': 'm',
            'std_dev': (float(pillar_survey['edm'].edm_specs.measurement_increments)/2)
                        /sqrt(3),
            'degrees_of_freedom':100,
            'k':sqrt(3),
            'description':'Distance Instrument Rounding'})
    
    if pillar_survey['thermometer'] and pillar_survey['uncertainty_budget'].auto_temp_zpc:
        uc_sources.append(
            {'group': '04',
            'ab_type':'B',
            'distribution':'N',
            'units': '°C',
            'std_dev': calib['them'].zpc_std_dev,
            'degrees_of_freedom':calib['them'].degrees_of_freedom,
            'k':calib['them'].zpc_coverage_factor,
            'description':'Thermometer calibrated correction factor'})
 
    if pillar_survey['uncertainty_budget'].auto_temp_rounding:
        uc_sources.append(
            {'group': '04',
            'ab_type':'B',
            'distribution':'R',
            'units': '°C',
            'std_dev': (float(pillar_survey['thermometer'].mets_specs.measurement_increments)/2)
                        /sqrt(3),
            'degrees_of_freedom':100,
            'k':sqrt(3),
            'description':'Thermometer Rounding'})

        
    if pillar_survey['barometer'] and pillar_survey['uncertainty_budget'].auto_pressure_zpc:
        uc_sources.append(
            {'group': '05',
            'ab_type':'B',
            'distribution':'N',
            'units': 'hPa',
            'std_dev': calib['baro'].zpc_std_dev,
            'degrees_of_freedom':calib['baro'].degrees_of_freedom,
            'k':calib['baro'].zpc_coverage_factor,
            'description':'Barometer calibrated correction factor'})

    if pillar_survey['uncertainty_budget'].auto_pressure_rounding:
        uc_sources.append(
            {'group': '05',
            'ab_type':'B',
            'distribution':'R',
            'units': 'hPa',
            'std_dev': (float(pillar_survey['barometer'].mets_specs.measurement_increments)/2)
                        /sqrt(3),
            'degrees_of_freedom':100,
            'k':sqrt(3),
            'description':'Barometer Rounding'})
    
    if pillar_survey['hygrometer'] and pillar_survey['uncertainty_budget'].auto_humi_zpc:
        uc_sources.append(
            {'group': '06',
            'ab_type':'B',
            'distribution':'N',
            'units': '%',
            'std_dev': calib['hygro'].zpc_std_dev,
            'degrees_of_freedom':calib['hygro'].degrees_of_freedom,
            'k':calib['hygro'].zpc_coverage_factor,
            'description':'Hygrometer calibrated correction factor'})
    
    if pillar_survey['hygrometer'] and pillar_survey['uncertainty_budget'].auto_humi_rounding:
        uc_sources.append(
            {'group': '06',
            'ab_type':'B',
            'distribution':'R',
            'units': '%',
            'std_dev': (float(pillar_survey['hygrometer'].mets_specs.measurement_increments)/2)
                        /sqrt(3),
            'degrees_of_freedom':100,
            'k':sqrt(3),
            'description':'Hygrometer Rounding'})
    
    return uc_sources


def is_float(n):
    try:
        float(n)
    except ValueError as e:
        print(e)
        return False
    else:
        return True


def float_or_null (n):
    try:
        return float(n)
    except ValueError:
        return None
    
    
def validate_survey(pillar_survey, baseline=None, calibrations=None,
                    raw_edm_obs=None, raw_lvl_obs=None):
    Errs=[]
    Wrns=[]
    lvl_file_checked = False
    edm_file_checked = False
    if 'accreditation' in pillar_survey.keys(): calibration_type = 'B'
    else: calibration_type = 'I'
    
    # Baseline Calibration errors in instrument calibration
    if calibration_type == 'I':
        if pillar_survey['auto_base_calibration']:
            site_pk = pillar_survey['site'].pk
            site = str(pillar_survey['site'])
        else:
            site_pk = pillar_survey['calibrated_baseline'].baseline.pk
            site = str(pillar_survey['calibrated_baseline'].baseline)
        
        if pillar_survey['auto_base_calibration']:
            qry_obj = (
                Pillar_Survey.objects.filter(
                    baseline = site_pk ,
                    survey_date__lte = pillar_survey['survey_date'])
                .exclude(experimental_std_dev__isnull = True)
                .order_by('-survey_date'))
            if len(qry_obj) == 0:
                Errs.append(
                    'There is no calibration of the ' + site
                    + ' baseline for the ' + pillar_survey['survey_date'].strftime("%d %b, %Y")
                    + ' when your EDMI calibration survey was observed.')
    
    # Instrumentation Selection Errors
    ucb = pillar_survey['uncertainty_budget']
    if calibrations:
        if calibration_type =='B':
            if ucb.auto_EDMI_scf or ucb.auto_EDMI_scf_drift:
                if len(calibrations['edmi']) == 0:    
                       Errs.append('Uncertainty budget sources that are dependant on EDMI calibration certificates have been selected in the uncertainty budget.')
                       Errs.append('There are no calibration records for ' +
                                   str(pillar_survey['edm']) + ' with prism ' + str(pillar_survey['prism']))
                       Errs.append('EDMI calibration certificates need to be current for the date of survey: '
                                   + pillar_survey['survey_date'].strftime("%d %b, %Y"))
            if calibrations['staff'] is None: 
                Wrns.append('There is no calibration record for ' + str(pillar_survey['staff']))
        
        if pillar_survey['hygrometer']:
            if calibrations['hygro'] is None and ucb.auto_humi_zpc:
                   Errs.append('Uncertainty budget sources that are dependant on hygrometer calibration certificates have been selected in the uncertainty budget.')
            if calibrations['hygro'] is None and not pillar_survey['hygro_calib_applied']:
                   Errs.append('There is no calibration record for ' + str(pillar_survey['hygrometer']))
                   Errs.append('Hygrometer calibration certificates need to be current for the date of survey: '
                               + pillar_survey['survey_date'].strftime("%d %b, %Y"))
        
        if not pillar_survey['hygrometer'] and ucb.auto_humi_zpc:
            Errs.append('Uncertainty budget sources that are dependant on hygrometer calibration certificates have been selected in the uncertainty budget, but no hygrometer has been selected.')
            
        if not pillar_survey['hygrometer'] and not pillar_survey['hygro_calib_applied']:
            Errs.append('Hygrometer calibration corrections have not been applied prior to input. A calibration certificate is required to apply calibrations to raw observations, but no hygrometer has been selected.')

        if calibrations['baro'] is None and ucb.auto_pressure_zpc:
               Errs.append('Uncertainty budget sources that are dependant on barometer calibration certificates have been selected in the uncertainty budget.')
               Errs.append('There is no calibration record for ' + str(pillar_survey['barometer']))
               Errs.append('Barometer calibration certificates need to be current for the date of survey: '
                           + pillar_survey['survey_date'].strftime("%d %b, %Y"))

        if calibrations['them'] is None and ucb.auto_temp_zpc:
               Errs.append('Uncertainty budget sources that are dependant on thermometer calibration certificates have been selected in the uncertainty budget.')
               Errs.append('There is no calibration record for ' + str(pillar_survey['thermometer']))
               Errs.append('Thermometer calibration certificates need to be current for the date of survey: '
                           + pillar_survey['survey_date'].strftime("%d %b, %Y"))
        
        
        if calibrations['them'] is None:
            if pillar_survey['thermo_calib_applied']:
                Wrns.append('There is no calibration record for ' + str(pillar_survey['thermometer']))
            else:
                Errs.append('There is no calibration record for ' + str(pillar_survey['thermometer']))
                Errs.append('Thermometer calibration certificates need to be current for the date of survey: '
                            + pillar_survey['survey_date'].strftime("%d %b, %Y"))
                
        if calibrations['baro'] is None:
            if pillar_survey['baro_calib_applied']:
                Wrns.append('There is no calibration record for ' + str(pillar_survey['barometer']))
            else:
                Errs.append('There is no calibration record for ' + str(pillar_survey['barometer']))
                Errs.append('Barometer calibration certificates need to be current for the date of survey: '
                            + pillar_survey['survey_date'].strftime("%d %b, %Y"))
        if pillar_survey['hygrometer']:
            if calibrations['hygro'] is None: 
                if pillar_survey['hygro_calib_applied']:
                    Wrns.append('There is no calibration record for ' + str(pillar_survey['hygrometer']))
                else:
                    Errs.append('There is no calibration record for ' + str(pillar_survey['hygrometer']))
                    Errs.append('Hygrometer calibration certificates need to be current for the date of survey: '
                                + pillar_survey['survey_date'].strftime("%d %b, %Y"))
        
        if calibration_type =='B':
            if pillar_survey['thermometer2'] and calibrations['them2'] is None:
                if pillar_survey['thermo2_calib_applied']:
                    Wrns.append('There is no calibration record for ' + str(pillar_survey['thermometer2']))
                else:
                    Errs.append('There is no calibration record for ' + str(pillar_survey['thermometer2']))
                    Errs.append('Thermometer calibration certificates need to be current for the date of survey: '
                                + pillar_survey['survey_date'].strftime("%d %b, %Y"))
        
            if pillar_survey['barometer2'] and calibrations['baro2'] is None:
                if pillar_survey['baro2_calib_applied']:
                    Wrns.append('There is no calibration record for ' + str(pillar_survey['barometer2']))
                else:
                    Errs.append('There is no calibration record for ' + str(pillar_survey['barometer2']))
                    Errs.append('Barometer calibration certificates need to be current for the date of survey: '
                                + pillar_survey['survey_date'].strftime("%d %b, %Y"))
        
            if pillar_survey['hygrometer2'] and calibrations['hygro2'] is None:
                if pillar_survey['hygro2_calib_applied']:
                    Wrns.append('There is no calibration record for ' + str(pillar_survey['hygrometer2']))
                else:
                    Errs.append('There is no calibration record for ' + str(pillar_survey['hygrometer2']))
                    Errs.append('Hygrometer calibration certificates need to be current for the date of survey: '
                                + pillar_survey['survey_date'].strftime("%d %b, %Y"))

    if raw_edm_obs:
        # check all the upload file headings are correct
        required_clms = ['from_pillar','to_pillar','inst_ht', 'tgt_ht', 
                         'raw_slope_dist',
                         'raw_temperature', 'raw_pressure', 'raw_humidity']
        if calibration_type =='B': 
            required_clms.append('hz_direction')
            if pillar_survey['thermometer2']: required_clms.append('raw_temperature2')
            if pillar_survey['barometer2']: required_clms.append('raw_pressure2')
            if pillar_survey['hygrometer2']: required_clms.append('raw_humidity2')
                
        first_o = next(iter(raw_edm_obs.values()))
        file_clms = [k for k, v in first_o.items() if v is not None]
        if all(key in file_clms for key in required_clms):
            edm_file_checked = True
        else:
            Errs.append(
                'The column headings in the "EDM File  file csv"'
                + ' are either incorrect or missing. This file must'
                + ' contain the headings ' + ', '.join(required_clms))
                        
            if calibration_type =='I': 
                Errs[-1].replace(' Horizontal_direction(dd),','')
    
    if raw_lvl_obs:
        # check all the upload file headings are correct
        required_clms = ['pillar', 'reduced_level', 'std_dev']
        file_clms = list(raw_lvl_obs.values())[0] 
        if all(key in file_clms for key in required_clms):
            lvl_file_checked = True
        else:
            Errs.append(
                'The column headings in the "Reduced Levels file csv"'
                + ' are either incorrect or missing. This file must'
                + ' contain the headings ' + ', '.join(required_clms))
        
    # EDM upload File
    if baseline:
        if 'pillars' in baseline.keys():
            pillars = [p.name for p in baseline['pillars']]
    if raw_edm_obs and baseline and edm_file_checked:
        pop_list=[]
        for k, o in raw_edm_obs.items():
            #check the values of all data
            if not is_float(o['inst_ht']):
                Errs.append(f'instrument height "{o["inst_ht"]}" is invalid')
            if not is_float(o['tgt_ht']):
                Errs.append(f'target height "{o["tgt_ht"]}" is invalid')
            if 'hz_direction' in o:
                if not is_float(o['hz_direction']):
                    Errs.append(f'Horizontal Direction text "{o["hz_direction"]}" is invalid')
                else: 
                    if float(o['hz_direction']) < 0 or float(o['hz_direction']) > 360:
                        Errs.append(f'Horizontal Direction "{o["hz_direction"]}" is invalid')
            if not is_float(o['raw_slope_dist']):
                Errs.append(f"Slope distance {o['raw_slope_dist']} is invalid")
            if not is_float(o['raw_temperature']):
                Errs.append(f"Temperature reading {o['raw_temperature']} is invalid")
            if not is_float(o['raw_pressure']):
                Errs.append(f"Pressure reading {o['raw_pressure']} is invalid")
            if not is_float(o['raw_humidity']):
                Errs.append(f"Humidity reading {o['raw_humidity']} is invalid")
            
            # Check pillar names are valid
            if not o['from_pillar'] in pillars:
                pop_list.append(k)
                Errs.append(f'Pillar "{o["from_pillar"]}" is not a valid pillar name.'
                            f'The observation "{o["from_pillar"]}--{o["to_pillar"]}" '
                            'has been removed from the data')
            if not o['to_pillar'] in pillars:
                pop_list.append(k)
                Errs.append(f'Pillar "{o["to_pillar"]}" is not a valid pillar name.'
                            f'The observation "{o["from_pillar"]}--{o["to_pillar"]}" '
                            'has been removed from the data')
        for pop_it in pop_list:
            raw_edm_obs.pop(pop_it, None)
    
        if calibration_type =='B':
            #'use_for_distance' checks
            # Each pillar must be observed from at least 2 other pillars
            bays=[]
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
                        
            #Each baseline calibration pillar survey must have from first to last pillar
            if not [0, len(pillars) - 1] in bays:
                Errs.append('The pillar survey used for the calibration of the baseline'
                            +' must include an observation from the first to the last'
                            +' pillar. The current pillar survey is missing observation'
                            +' Pillar '+ str(pillars[0]) +' to '+ 'Pillar ' 
                            + str(pillars[-1]) +'.')
    # level upload File
    if raw_lvl_obs and lvl_file_checked:
        lvl_nmes =[]
        for k, o in raw_lvl_obs.items():
            if not is_float(o['reduced_level']):
                 Errs.append(f"Reduced Level reading {o['reduced_level']} is invalid")
            
            if not o['pillar'] in lvl_nmes:
                lvl_nmes.append(o['pillar'])
                    
            if not o['pillar'] in pillars:
                o.pop(k, None)
                Wrns.append('Pillar "' + o['pillar'] + '" is not a valid pillar name.'
                            + 'The level data for "' +  o['pillar'] 
                            + '" has been removed from the data')
        
        for n in pillars:
            if not n in lvl_nmes: Errs.append('Pillar "' + n + '" is not listed in the level file.')


    if not pillar_survey['mets_applied']:
        c = pillar_survey['edm'].edm_specs.c_term
        d = pillar_survey['edm'].edm_specs.d_term
        w = pillar_survey['edm'].edm_specs.carrier_wavelength
        if any(x is None for x in [c,d,w]) == None:
            inputs = [
                pillar_survey['edm'].edm_specs.frequency,
                pillar_survey['edm'].edm_specs.manu_ref_refrac_index]
            if any(x is None for x in inputs) == None:
                Errs.append(
                    'In order for Medjil to apply atmospheric corrections,'
                    ' either the carrier wavelength, C-term and D-term must be specified'
                    ' or the carrier wavelength, modulation frequency and'
                    ' manufacturers refractive index must be specified'
                    ' insufficient data has been supplied for the EDM'
                    'Instrument used for this calibration')
                
    
    # Date Warnings
    if pillar_survey['mets_applied']:
        t = pillar_survey['thermo_calib_applied']
        b = pillar_survey['baro_calib_applied']
        h = pillar_survey['hygro_calib_applied']
        if not t or not b or not h:
            Wrns.append('No calibration correction has been applied for one or more ' +
                        'of the Metrological Instruments. These calibration corrections have ' +
                        'not been accounted of in the atmospheric corrections of EDM observations ' +
                        'as atmospheric corrections were applied prior to data upload.')
        
    if pillar_survey['survey_date'] > pillar_survey['computation_date']:
        Wrns.append('The date of computation entered is before the date of survey.')
        
    if 'accreditation' in pillar_survey:
        if (pillar_survey['survey_date'] < pillar_survey['accreditation'].valid_from_date
            or pillar_survey['survey_date'] > pillar_survey['accreditation'].valid_to_date):
            Wrns.append('The company does not have a current accreditaion for the ' +
                        'date of the survey used to calibrate the EDM baseline')
    
    return {'Errors':Errs,'Warnings':Wrns}
