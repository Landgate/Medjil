import numpy as np
from statistics import mean, pstdev
from django.db.models import Avg
from django.forms.models import model_to_dict
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import date
from decimal import Decimal
from django.db.models import Q

from instruments.models import (
    EDM_Inst,
    Prism_Inst,
    Staff,
    Mets_Inst,
    EDMI_certificate,
    Mets_certificate)
from staffcalibration.models import StaffCalibrationRecord
from accounts.models import Calibration_Report_Notes
from calibrationsites.models import (
    Pillar,
    CalibrationSite)
from baseline_calibration.models import (
    Uncertainty_Budget,
    Uncertainty_Budget_Source,
    Certified_Distance,
    Pillar_Survey,
    Std_Deviation_Matrix)
from edm_calibration.models import(
    uCalibration_Parameter,
    uPillar_Survey)
from geodepy.geodesy import grid2geo, rho


def csv2dict(csv_file,clms,key_names=-1):
    dct={}
    clms.append('line')
    rows = csv_file.read().decode("utf-8").split("\n")
    for lne, row in enumerate(rows[1:]):
        r = (row+','+str(lne+1)).replace('\r','').split(',')
        if key_names != -1: ky = str(r[key_names])            
        if key_names == -1: ky = str(len(dct)+1)
        if len(clms) == len(r):
            dct[ky] = dict(zip(clms,r))
                    
    return dct


def list2dict(lst,clms,key_names=-1):
    dct={}
    for row in lst:
        if key_names != -1: ky = str(row[clms.index(key_names)])            
        if key_names == -1: ky = str(len(dct)+1)
   
        dct[ky] = dict(zip(clms,row))
                
    return dct


def class2dict(clss,key_names=-1):
    dct={}
    for row in clss:
        if key_names != -1: ky = str(vars(row)[key_names])
        if key_names == -1: ky = str(len(dct)+1)
        dct[ky] = vars(row)
                
    return dct


def dict2np(dct):
    ilist=[]
    for d, v in dct.items():
        ilist.append(list(v.values()))

    return np.array(ilist, dtype=object), list(v.keys())


def format_name(nme):
    num = ''.join([str(s) for s in nme if s.isdigit()])
    return nme.replace(num,num.zfill(3))


def group_list(raw_list, group_by, labels_list=[], avg_list=[], sum_list=[], std_list=[], mask_by=''):
    grouped={}
    group_ky='grp_'+group_by
    for v in raw_list:
        if not v[group_by] in grouped.keys(): 
            grouped[v[group_by]]={group_ky:[],group_by:v[group_by]}
            if len(labels_list)!=0:
                for ky in labels_list:
                    grouped[v[group_by]][ky] = v[ky]
        
        if len(mask_by)==0:
            grouped[v[group_by]][group_ky].append(v)
        else:
            if v[mask_by]:
                grouped[v[group_by]][group_ky].append(v)
    
    pop_list=[]
    if len(avg_list)!=0 or len(std_list)!=0 or len(sum_list)!=0:
        for i, group in grouped.items():
            if len(group[group_ky])==0:
                pop_list.append(i)
            else:
                if len(avg_list)!=0:
                    for ky in avg_list:
                        group[ky] = mean([float(v[ky]) for v in group[group_ky]])
                
                if len(std_list)!=0:
                    for ky in std_list:
                        group['std_'+ky] = pstdev([float(v[ky]) for v in group[group_ky]])
                
                if len(sum_list)!=0:
                    for ky in sum_list:
                        group['sum_'+ky] = sum([float(v[ky]) for v in group[group_ky]])
    for i in pop_list:
        grouped.pop(i)
    
    return grouped

def Instruments_qry(cache_data):
    instruments={}
    instruments['edm'] = EDM_Inst.objects.select_related().get(pk=cache_data['edm'])
    instruments['prism'] = Prism_Inst.objects.select_related().get(pk=cache_data['prism'])
    if 'staff' in cache_data:
        instruments['staff'] = Staff.objects.select_related().get(pk=cache_data['staff'])
    instruments['thermometer'] = Mets_Inst.objects.select_related().get(pk=cache_data['thermometer'])
    instruments['barometer'] = Mets_Inst.objects.select_related().get(pk=cache_data['barometer'])
    if 'hygrometer' in cache_data:
        instruments['hygrometer'] = Mets_Inst.objects.select_related().get(pk=cache_data['hygrometer'])
            
    return instruments


def Calibrations_qry(frm_data):
    calib = {}
        
    #test if it is a baseline or EDMI calibration
    if 'staff' in frm_data:
        calib['edmi'] = EDMI_certificate.objects.filter(
            calibration_date__lte = frm_data['survey_date'],
            edm__pk = frm_data['edm'].pk, prism__pk = frm_data['prism'].pk
            ).order_by('-calibration_date')
        calib['staff'] = StaffCalibrationRecord.objects.filter(
                    calibration_date__lte = frm_data['survey_date'] ,
                    inst_staff__pk = frm_data['staff'].pk
                    ).order_by('-calibration_date').first()
    else:
        cp = uCalibration_Parameter.objects.select_related().filter(
            pillar_survey__survey_date__lte = frm_data['survey_date'],
            pillar_survey__edm__pk = frm_data['edm'].pk, 
            pillar_survey__prism__pk = frm_data['prism'].pk
            ).order_by('-pillar_survey__survey_date', '-term')
        cp = group_list(cp.values(),
                        group_by = 'pillar_survey_id')
        
        calib['edmi'] = uPillar_Survey.objects.filter(
            survey_date__lte = frm_data['survey_date'],
            edm__pk = frm_data['edm'].pk, 
            prism__pk = frm_data['prism'].pk
            ).order_by('-survey_date').values()
        
        for ps in calib['edmi']:
            if ps['id'] in cp.keys():
                ps['parameters'] = cp[ps['id']]['grp_pillar_survey_id']
            else:
                ps['parameters'] = []
    
    calib['them'] = Mets_certificate.objects.filter(
                calibration_date__lte = frm_data['survey_date'] ,
                instrument__pk = frm_data['thermometer'].pk
                ).order_by('-calibration_date').first()
    calib['baro'] = Mets_certificate.objects.filter(
                calibration_date__lte = frm_data['survey_date'] ,
                instrument__pk = frm_data['barometer'].pk
                ).order_by('-calibration_date').first()
    if 'hygrometer' in frm_data:
        calib['hygro'] = Mets_certificate.objects.filter(
                    calibration_date__lte = frm_data['survey_date'] ,
                    instrument__pk = frm_data['hygrometer'].pk
                    ).order_by('-calibration_date').first()
    
    return calib

def baseline_qry(frm_data):
    baseline={}
    if 'baseline' in frm_data:
        baseline['site'] = frm_data['baseline']
        baseline['history'] = (Certified_Distance.objects.select_related().filter(
                pillar_survey__baseline__pk = frm_data['baseline'].pk)
                .order_by('pillar_survey__survey_date','to_pillar__order'))
    
    if 'auto_base_calibration' in frm_data:
        if frm_data['auto_base_calibration']:
            baseline['site'] = frm_data['site']
            baseline['calibrated_baseline'] = (
                Pillar_Survey.objects.filter(baseline = frm_data['site'].pk,                
                            survey_date__lte = frm_data['survey_date'])
                    .exclude(variance__isnull = True)
                    .order_by('-survey_date'))[0]
        else:
            baseline['calibrated_baseline'] = frm_data['calibrated_baseline']
            baseline['site'] = baseline['calibrated_baseline'].baseline
    
        sd_m = (Std_Deviation_Matrix.objects
                .select_related('from_pillar', 'to_pillar')
                .filter(pillar_survey__pk = baseline['calibrated_baseline'].pk))
        baseline['std_dev_matrix'] = ({s.from_pillar.name + ' - ' + s.to_pillar.name:
                                        model_to_dict(s) for s in sd_m})

        cd = (Certified_Distance.objects
                .select_related('from_pillar', 'to_pillar')
                .filter(pillar_survey__pk = baseline['calibrated_baseline'].pk))
        baseline['certified_dist'] ={d.to_pillar.name:model_to_dict(d) for d in cd}
        
    baseline['pillars'] = Pillar.objects.filter(
                            site_id__pk = baseline['site'].pk
                            ).order_by('order')
    
    baseline_enz = Pillar.objects.filter(
                            site_id__pk = baseline['site'].pk).aggregate(
                                Avg('easting'), Avg('northing'), Avg('zone'))
    baseline_llh = grid2geo(float(baseline_enz['zone__avg']),
                            float(baseline_enz['easting__avg']),
                            float(baseline_enz['northing__avg']))
    baseline['d_radius'] = rho(baseline_llh[0])
    
    return baseline
        
    
def uncertainty_qry(frm_data):
    uc_budget={}
    uc_sources = (Uncertainty_Budget_Source.objects.filter(
                            uncertainty_budget__pk = frm_data['uncertainty_budget'].pk ,
                            ))

    uc_budget['sources'] = list(uc_sources.values())

    uc_budget['stddev_0_adj'] = float(frm_data['uncertainty_budget']
                                      .std_dev_of_zero_adjustment)
    return uc_budget

def report_notes_qry(company, report_type):
    rpt_notes = Calibration_Report_Notes.objects.filter(
                    Q(report_type = report_type, note_type = 'M') |
                    Q(report_type = report_type, note_type = 'C',company = company)
                    ).order_by('-note_type','pk')
    report_notes = []
    for n in rpt_notes:
        report_notes = report_notes + (n.note.split('\n'))

    return report_notes

def decrypt(en_str):
    NORMAL_CHARS =  r'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 abcdefghijklmnopqrstuvwxyz.|(),;"!@#$%^&*()_-+={}[]\<>?/:'
    ENCRYPT_CHARS = r'962XRLD7YJS1AHBQ5NCO3M08EKGIWUPTVZ4F qwertyuiopasdfghjklzxcvbnm|.(),;"!@#$%^&*()_-=+{}[]\<>?/:'
    
    dct=dict(zip(ENCRYPT_CHARS,NORMAL_CHARS))
    decripted_str = ''
    
    for s in en_str:
        decripted_str += dct[s]
    
    return decripted_str