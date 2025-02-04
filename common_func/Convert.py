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

from collections import defaultdict
import csv
from io import TextIOWrapper
import numpy as np
from statistics import mean, pstdev
from django.db.models import Avg
from django.forms.models import model_to_dict
from django.db.models import Q
from django.db import transaction

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
    Pillar)
from baseline_calibration.models import (
    Uncertainty_Budget_Source,
    Certified_Distance,
    Pillar_Survey,
    Std_Deviation_Matrix,
    EDM_Observation,
    Level_Observation)
from edm_calibration.models import uEdmObservation
from geodepy.geodesy import grid2geo, rho, nu


def db_std_units(orig_val, orig_unit):
    # function converts all values to scalar, m, Hz, °C or hPa    
    if orig_val:
        orig_val = float(orig_val)
        new_val = orig_val
        new_unit = orig_unit

        if orig_unit == 'ppm': new_val = round(orig_val / 1e6, 20)
        if orig_unit == '%': new_val = orig_val / 100
        if orig_unit == 'nm': new_val = round(orig_val / 1e9, 20)
        if orig_unit == 'µm': new_val = round(orig_val / 1e6, 20)
        if orig_unit == 'mm': new_val = round(orig_val / 1000, 20)
        if orig_unit == 'mmHg': 
            new_val = round(float(orig_val) * 1.33322387415, 13)
        if orig_unit == 'inHg': 
            new_val = round(float(orig_val) * 33.8639, 13)
        if orig_unit == 'MHz': 
            new_val = orig_val * 1e6
            new_unit = 'Hz'
        if orig_unit == '°F': 
            new_val = (orig_val -32) * (5/9)
            new_unit = '°C'
            
        if any([orig_unit == 'nm', orig_unit == 'mm', orig_unit == 'µm']): 
            new_unit = 'm'
        if any([orig_unit == 'ppm', orig_unit == '%']):
            new_unit = 'a.x'
        if any([orig_unit == 'inHg', orig_unit == 'mmHg']):
            new_unit = 'hPa'
        
        return new_val, new_unit
    else:
        return orig_val, orig_unit


def convert_headings(raw_headings):
    conversion_dict = {
        'height_of_instrument': 'inst_ht',
        'height_of_target': 'tgt_ht',
        'horizontal_direction(dd)': 'hz_direction',
        'slope_distance': 'raw_slope_dist',
        'temperature': 'raw_temperature',
        'pressure': 'raw_pressure',
        'humidity': 'raw_humidity',
        'temperature2': 'raw_temperature2',
        'pressure2': 'raw_pressure2',
        'humidity2': 'raw_humidity2',
        'pillar_rl': 'reduced_level',
        'pillar_name': 'pillar'
    }
    
    return [conversion_dict.get(heading.lower(), heading.lower().replace(' ', '_')) for heading in raw_headings]


def csv2dict(csv_file, clms=None, key_names=-1):
    # Read in a csv to a dictionary of dictionaries.
    # If no column names are provided, convert headers to column names for keys in the child dictionary
    # Use the nth column for the keys of the parent dictionary. If key_names is -1, use the row index as the key
    csv_file = TextIOWrapper(csv_file, encoding='utf-8-sig')
    reader = csv.reader(csv_file)
    headers = next(reader)
    if not clms:
        clms = convert_headings(headers)
    clms.append('line')
    
    def replace_empty_with_none(row):
        return [None if cell == '' else cell for cell in row]
    
    # Use dictionary comprehension for speed
    return {str(row[key_names] if key_names != -1 else index + 1): dict(zip(clms, replace_empty_with_none(row) + [str(index + 1)]))
            for index, row in enumerate(reader) if len(row) >= len(clms)-1}


def list2dict(lst, clms, key_names=-1, filter_key=None, filter_value=None):
    dct={}
    for row in lst:
        if len(clms) == len(row):
            if key_names != -1: ky = str(row[clms.index(key_names)])
            if key_names == -1: ky = str(len(dct)+1)
            
            if not filter_key:
                dct[ky] = dict(zip(clms,row))
            elif row[clms.index(filter_key)] == filter_value:
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


def dict_2_html_table(data):
    if not data:
        return "<p>No data to display.</p>"
    
    table_html = "<table>\n"
    
    # Assuming the keys of the first dictionary are the headers
    headers = data[0].keys()
    table_html += "<tr>"
    for header in headers:
        table_html += f"<th>{header}</th>"
    table_html += "</tr>\n"
    
    # Iterating over each dictionary to create rows
    for row in data:
        table_html += "<tr>"
        for key in headers:
            table_html += f"<td>{row.get(key, '')}</td>"
        table_html += "</tr>\n"
    table_html += "</table>"
    return table_html


def format_name(nme):
    num = ''.join([str(s) for s in nme if s.isdigit()])
    return nme.replace(num,num.zfill(3))


def group_list(raw_list, group_by, labels_list=[], avg_list=[], sum_list=[], std_list=[], mask_by=''):
    grouped = defaultdict(lambda: {group_by: None, 'grp_' + group_by: []})
    pop_list = set()

    for v in raw_list:
        group_value = v[group_by]
        group = grouped[group_value]
        
        if group[group_by] is None:
            group[group_by] = group_value
            for ky in labels_list:
                group[ky] = v.get(ky)

        if not mask_by or v.get(mask_by):
            group['grp_' + group_by].append(v)

    for group_value, group in grouped.items():
        group_ky = 'grp_' + group_by
        if not group[group_ky]:
            pop_list.add(group_value)
            continue

        for ky in avg_list:
            values = [float(v.get(ky, 0)) for v in group[group_ky] if v.get(ky, 0)]
            group[ky] = mean(values) if values else 0

        for ky in std_list:
            values = [float(v.get(ky, 0)) for v in group[group_ky] if v.get(ky, 0)]
            group['std_' + ky] = pstdev(values) if len(values) > 1 else 0

        for ky in sum_list:
            values = [float(v.get(ky, 0)) for v in group[group_ky] if v.get(ky, 0)]
            group['sum_' + ky] = sum(values)

    for group_value in pop_list:
        grouped.pop(group_value)

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
    if 'staff' in frm_data: calibration_type = 'B'
    else: calibration_type = 'I'
    
    if calibration_type == 'B':
        calib['edmi'] = EDMI_certificate.objects.filter(
            calibration_date__lte = frm_data['survey_date'],
            edm__pk = frm_data['edm'].pk, prism__pk = frm_data['prism'].pk
            ).order_by('-calibration_date')
        calib['staff'] = StaffCalibrationRecord.objects.filter(
            calibration_date__lte = frm_data['survey_date'] ,
            inst_staff__pk = frm_data['staff'].pk
            ).order_by('-calibration_date').first()
        if frm_data['thermometer2']:   
            calib['them2'] = Mets_certificate.objects.filter(
                        calibration_date__lte = frm_data['survey_date'] ,
                        instrument__pk = frm_data['thermometer2'].pk
                        ).order_by('-calibration_date').first()
        else:
            calib['them2'] = None 
    
        if frm_data['barometer2']:
            calib['baro2'] = Mets_certificate.objects.filter(
                        calibration_date__lte = frm_data['survey_date'] ,
                        instrument__pk = frm_data['barometer2'].pk
                        ).order_by('-calibration_date').first()
        else:
            calib['baro2'] = None
        
        if frm_data['hygrometer2']:
            calib['hygro2'] = Mets_certificate.objects.filter(
                        calibration_date__lte = frm_data['survey_date'] ,
                        instrument__pk = frm_data['hygrometer2'].pk
                        ).order_by('-calibration_date').first()
        else:
            calib['hygro2'] = None 
    elif calibration_type == 'I':
        calib['edmi'] = EDMI_certificate.objects.filter(
            calibration_date__lte = frm_data['survey_date'],
            edm__pk = frm_data['edm'].pk, 
            prism__pk = frm_data['prism'].pk
            ).order_by(
                '-calibration_date').select_related(
                    'certificate').values(                                
                        'calibration_date',
                        'scale_correction_factor',
                        'scf_uncertainty',
                        'zero_point_correction',
                        'zpc_uncertainty',
                        'cyclic_one',
                        'cyc_1_uncertainty',
                        'cyclic_two',
                        'cyc_2_uncertainty',
                        'cyclic_three',
                        'cyc_3_uncertainty',
                        'cyclic_four',
                        'cyc_4_uncertainty',
                        'standard_deviation',
                        'degrees_of_freedom')
                    
    calib['them'] = Mets_certificate.objects.filter(
                calibration_date__lte = frm_data['survey_date'] ,
                instrument__pk = frm_data['thermometer'].pk
                ).order_by('-calibration_date').first()
    calib['baro'] = Mets_certificate.objects.filter(
                calibration_date__lte = frm_data['survey_date'] ,
                instrument__pk = frm_data['barometer'].pk
                ).order_by('-calibration_date').first()
    if frm_data['hygrometer']:
        calib['hygro'] = Mets_certificate.objects.filter(
                    calibration_date__lte = frm_data['survey_date'] ,
                    instrument__pk = frm_data['hygrometer'].pk
                    ).order_by('-calibration_date').first()
    else:
        calib['hygro'] = None
        
    return calib


def baseline_qry(frm_data,id=None):
    baseline={}
    #test if it is a baseline or EDMI calibration
    if 'staff' in frm_data: calibration_type = 'B'
    else: calibration_type = 'I'
    
    if calibration_type == 'B':
        baseline['site'] = frm_data['baseline']
        baseline['history'] = (
            Pillar_Survey.objects.filter(
                baseline__pk=frm_data['baseline'].pk,
                results__status='publish',
                results__experimental_std_dev__isnull = False)
            .exclude(id=id)
            .select_related('results')
            .order_by('survey_date')
        )

    
    elif calibration_type == 'I':
        if frm_data['auto_base_calibration']:
            baseline['site'] = frm_data['site']
            baseline['calibrated_baseline'] = (
                Pillar_Survey.objects.filter(
                    baseline = frm_data['site'].pk,
                    survey_date__lte = frm_data['survey_date'],
                    results__status='publish',
                    results__experimental_std_dev__isnull = False)
                .order_by('-survey_date')).first()
        else:
            baseline['calibrated_baseline'] = frm_data['calibrated_baseline']
            baseline['site'] = baseline['calibrated_baseline'].baseline
    
        sd_m = (Std_Deviation_Matrix.objects
                .select_related('from_pillar', 'to_pillar')
                .filter(pillar_survey__pk = baseline['calibrated_baseline'].pk)
                .exclude(
                    pillar_survey__results__status='check',
                    pillar_survey__results__experimental_std_dev__isnull = True))
        baseline['std_dev_matrix'] = ({s.from_pillar.name + ' - ' + s.to_pillar.name:
                                        model_to_dict(s) for s in sd_m})

        cd = (Certified_Distance.objects
                .select_related('from_pillar', 'to_pillar')
                .filter(pillar_survey__pk = baseline['calibrated_baseline'].pk)
                .exclude(
                    pillar_survey__results__status='check',
                    pillar_survey__results__experimental_std_dev__isnull = True))
                
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
    baseline['d_radius'] = (rho(baseline_llh[0])*nu(baseline_llh[0]))**0.5
    
    return baseline
        
    
def uncertainty_qry(frm_data):
    uc_budget={}
    uc_sources = (
        Uncertainty_Budget_Source.objects.filter(
            uncertainty_budget__pk = frm_data['uncertainty_budget'].pk)
        )

    uc_budget['sources'] = list(uc_sources.values())

    uc_budget['stddev_0_adj'] = float(frm_data['uncertainty_budget']
                                      .std_dev_of_zero_adjustment)
    return uc_budget


def get_endnotes(pillar_survey, calibration_type, company):
    if calibration_type == 'B':
        from_pillars = EDM_Observation.objects.filter(
            pillar_survey=pillar_survey.id).values_list('from_pillar', flat=True)
        to_pillars = EDM_Observation.objects.filter(
            pillar_survey=pillar_survey.id).values_list('to_pillar', flat=True)
    
        filters = (
            Q(calibration_type='B')
            & (Q(verifying_authority=pillar_survey.accreditation.accredited_company) | Q(verifying_authority__isnull=True))
            & (Q(accreditation=pillar_survey.accreditation) | Q(accreditation__isnull=True))
            & (Q(company=company) | Q(company__isnull=True))
            & (Q(site=pillar_survey.baseline) | Q(site__isnull=True))
            & (Q(pillar__id__in=from_pillars) | Q(pillar__id__in=to_pillars) | Q(pillar__isnull=True))
        )
    else:
        from_pillars = uEdmObservation.objects.filter(
            pillar_survey=pillar_survey.id).values_list('from_pillar', flat=True)
        to_pillars = uEdmObservation.objects.filter(
            pillar_survey=pillar_survey.id).values_list('to_pillar', flat=True)
        
        filters = (
            Q(calibration_type='E')
            & (Q(verifying_authority=pillar_survey.calibrated_baseline.accreditation.accredited_company) | Q(verifying_authority__isnull=True))
            & (Q(accreditation=pillar_survey.calibrated_baseline.accreditation) | Q(accreditation__isnull=True))
            & (Q(company=company) | Q(company__isnull=True))
            & (Q(site=pillar_survey.calibrated_baseline.baseline) | Q(site__isnull=True))
            & (Q(pillar__id__in=from_pillars) | Q(pillar__id__in=to_pillars) | Q(pillar__isnull=True))
        )
        
    rpt_notes = Calibration_Report_Notes.objects.filter(filters)
    report_notes = []
    for n in rpt_notes:
        report_notes = report_notes + (n.note.split('\n'))

    return report_notes


def decrypt_file(file):
    NORMAL_CHARS =  r'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 abcdefghijklmnopqrstuvwxyz.|(),;"!@#$%^&*()_-+={}[]\<>?/:' +"'"
    ENCRYPT_CHARS = r'962XRLD7YJS1AHBQ5NCO3M08EKGIWUPTVZ4F qwertyuiopasdfghjklzxcvbnm|.(),;"!@#$%^&*()_-=+{}[]\<>?/:'+"'"
    
    dct=dict(zip(ENCRYPT_CHARS,NORMAL_CHARS))
    
    encrypted_rows = file.read().decode("utf-8").replace('\r','').split("\n")
    decrypted_rows = []
    for row in encrypted_rows[1:]:
        decrypted_str = ''
        for s in row:
            decrypted_str += dct[s]
        decrypted_rows.append(decrypted_str.split('|'))
    
    return decrypted_rows


def baseline_qry2(pillar_survey, id=None):
    baseline={}
    # Determine calibration type
    calibration_type = 'B' if hasattr(pillar_survey, 'staff') else 'I'
    
    if calibration_type == 'B':
        baseline['site'] = pillar_survey.baseline
        baseline['history'] = (
            Pillar_Survey.objects.filter(
                baseline__pk=pillar_survey.baseline.pk,
                results__status='publish',
                results__experimental_std_dev__isnull = False)
            .exclude(id=id)
            .select_related('results')
            .order_by('survey_date')
        )
    
    elif calibration_type == 'I':
        if pillar_survey.auto_base_calibration:
            baseline['site'] = pillar_survey.site
            baseline['calibrated_baseline'] = (
                Pillar_Survey.objects.filter(
                    baseline = pillar_survey.site,
                    survey_date__lte = pillar_survey.survey_date,
                    results__status='publish',
                    results__experimental_std_dev__isnull = False)
                .order_by('-survey_date')).first()
            pillar_survey.calibrated_baseline = baseline['calibrated_baseline']
        else:
            baseline['calibrated_baseline'] = pillar_survey.calibrated_baseline
            baseline['site'] = baseline['calibrated_baseline'].baseline
            pillar_survey.site = baseline['site']
        
        if baseline['calibrated_baseline']:
            sd_m = (Std_Deviation_Matrix.objects
                    .select_related('from_pillar', 'to_pillar')
                    .filter(pillar_survey__pk = baseline['calibrated_baseline'].pk)
                    .exclude(
                        pillar_survey__results__status='check',
                        pillar_survey__results__experimental_std_dev__isnull = True))
            baseline['std_dev_matrix'] = ({s.from_pillar.name + ' - ' + s.to_pillar.name:
                                            model_to_dict(s) for s in sd_m})
    
            cd = (Certified_Distance.objects
                    .select_related('from_pillar', 'to_pillar')
                    .filter(pillar_survey__pk = baseline['calibrated_baseline'].pk)
                    .exclude(
                        pillar_survey__results__status='check',
                        pillar_survey__results__experimental_std_dev__isnull = True))
                
            baseline['certified_dist'] ={d.to_pillar.name:model_to_dict(d) for d in cd}
        
    baseline['pillars'] = baseline['site'].pillars.all().order_by('order')
    
    baseline_enz = baseline['pillars'].aggregate(
        Avg('easting'), Avg('northing'), Avg('zone'))
    
    baseline_llh = grid2geo(float(baseline_enz['zone__avg']),
                            float(baseline_enz['easting__avg']),
                            float(baseline_enz['northing__avg']))
    baseline['d_radius'] = (rho(baseline_llh[0])*nu(baseline_llh[0]))**0.5
    
    return baseline
    
    
def calibrations_qry2(pillar_survey):
    calib = {}
    # Determine calibration type
    calibration_type = 'B' if hasattr(pillar_survey, 'staff') else 'I'
    
    calib['edmi'] = EDMI_certificate.objects.filter(
        calibration_date__lte = pillar_survey.survey_date,
        edm__pk = pillar_survey.edm.pk, prism__pk = pillar_survey.prism.pk
        ).order_by('-calibration_date')
    if calibration_type == 'I':
        calib['edmi'] = calib['edmi'].exclude(id = pillar_survey.certificate.id)
        
    elif calibration_type == 'B':
        calib['staff'] = pillar_survey.staff.get_certificate(pillar_survey.survey_date)
        if pillar_survey.thermometer2: 
            calib['them2'] = pillar_survey.thermometer2.get_certificate(pillar_survey.survey_date)
        else:
            calib['them2'] = None        
        
        if pillar_survey.barometer2: 
            calib['baro2'] = pillar_survey.barometer2.get_certificate(pillar_survey.survey_date)
        else:
            calib['baro2'] = None
        
        if pillar_survey.hygrometer2: 
            calib['hygro2'] = pillar_survey.hygrometer2.get_certificate(pillar_survey.survey_date)
        else:
            calib['hygro2'] = None
    
    calib['them'] = pillar_survey.thermometer.get_certificate(pillar_survey.survey_date)
    calib['baro'] = pillar_survey.barometer.get_certificate(pillar_survey.survey_date)
    if pillar_survey.hygrometer:
        calib['hygro'] = pillar_survey.hygrometer.get_certificate(pillar_survey.survey_date)
    else:
        calib['hygro'] = None
        
    return calib

    
def uncertainty_qry2(pillar_survey):
    uc_budget={}
    uc_sources = pillar_survey.uncertainty_budget.uncertainty_budget_source_set.all()
    uc_budget['sources'] = list(uc_sources.values())
    uc_budget['stddev_0_adj'] = float(
        pillar_survey.uncertainty_budget.std_dev_of_zero_adjustment)
        
    return uc_budget


def import_csv_to_observations(csv_file, pillar_survey):
    calibration_type = 'B' if hasattr(pillar_survey, 'staff') else 'I'
    # Decode the file for reading
    file_name = getattr(csv_file, 'name', 'the uploaded file')
    csv_file = TextIOWrapper(csv_file, encoding='utf-8-sig')
    reader = csv.DictReader(csv_file)        

    # Normalize CSV column headings
    def convert_headings(column_name):
        """Standardizes column names to match model field names."""
        mapping = {
            'from_pillar': 'from_pillar',
            'to_pillar': 'to_pillar',
            'height_of_instrument': 'inst_ht',
            'height_of_target': 'tgt_ht',
            'slope_distance': 'raw_slope_dist',
            'temperature': 'raw_temperature',
            'pressure': 'raw_pressure',
            'humidity': 'raw_humidity',
            'horizontal_direction(dd)': 'hz_direction',
            'temperature2': 'raw_temperature2',
            'pressure2': 'raw_pressure2',
            'humidity2': 'raw_humidity2',
        }

        return mapping.get(column_name.strip().lower().replace(" ", "_"), column_name)

    # Convert headings
    reader.fieldnames = [convert_headings(field) for field in reader.fieldnames]

    # Define required headings
    required_headings = {
        'from_pillar':'from_pillar',
        'to_pillar':'to_pillar',
        'inst_ht':'height_of_instrument',
        'tgt_ht':'height_of_target',
        'raw_slope_dist':'slope_distance',
    }
    if calibration_type == 'B':
        required_headings.update({
            'horizontal_direction(dd)': 'hz_direction',
            })
    
    # Check for missing headings
    missing_headings = [
        heading for key, heading in required_headings.items() if key not in reader.fieldnames]
    if missing_headings:
        return [f"The following required headings are missing in the '{file_name}': {', '.join(missing_headings)}"]

    observations = []
    errors = []

    # Process each row in the CSV
    for line_num, row in enumerate(reader, start=1):
        try:
            # Resolve pillars for from_pillar and to_pillar
            from_pillar = pillar_survey.site.pillars.filter(name=row['from_pillar'].strip()).first()
            to_pillar = pillar_survey.site.pillars.filter(name=row['to_pillar'].strip()).first()

            if not from_pillar:
                raise ValueError(f"Invalid from_pillar '{row['from_pillar']}' on line {line_num}.")
            if not to_pillar:
                raise ValueError(f"Invalid to_pillar '{row['to_pillar']}' on line {line_num}.")

            # Map row data to EDMI observation
            if calibration_type == 'I':
                observation = uEdmObservation(
                    pillar_survey=pillar_survey,
                    from_pillar=from_pillar,
                    to_pillar=to_pillar,
                    inst_ht=row.get('inst_ht', '').strip() or None,
                    tgt_ht=row.get('tgt_ht', '').strip() or None,
                    raw_slope_dist=row.get('raw_slope_dist', '').strip() or None,
                    raw_temperature=row.get('raw_temperature', '').strip() or None,
                    raw_pressure=row.get('raw_pressure', '').strip() or None,
                    raw_humidity=row.get('raw_humidity', '').strip() or None,
                )
            # Map row data to EDMI observation
            if calibration_type == 'B':
                observation = EDM_Observation(
                    pillar_survey=pillar_survey,
                    from_pillar=from_pillar,
                    to_pillar=to_pillar,
                    inst_ht=row.get('inst_ht', '').strip() or None,
                    tgt_ht=row.get('tgt_ht', '').strip() or None,
                    raw_slope_dist=row.get('raw_slope_dist', '').strip() or None,
                    hz_direction=row.get('hz_direction', '').strip() or None,
                    raw_temperature=row.get('raw_temperature', '').strip() or None,
                    raw_pressure=row.get('raw_pressure', '').strip() or None,
                    raw_humidity=row.get('raw_humidity', '').strip() or None,
                    raw_temperature2=row.get('raw_temperature2', '').strip() or None,
                    raw_pressure2=row.get('raw_pressure2', '').strip() or None,
                    raw_humidity2=row.get('raw_humidity2', '').strip() or None,
                )

            # Validate observation before saving
            observation.full_clean()
            observations.append(observation)

        except Exception as e:
            # Capture detailed error for this line
            errors.append(f"Error on line {line_num}: {e}")

    # Save all valid observations only if there are no errors
    if len(errors) == 0:
        # Delete old observations if they exist
        if calibration_type == 'I':
            delete_edm_obs = uEdmObservation.objects.filter(pillar_survey=pillar_survey)
        else:
            delete_edm_obs = EDM_Observation.objects.filter(pillar_survey=pillar_survey)
        delete_edm_obs.delete()
        with transaction.atomic():
            if calibration_type == 'I':
                uEdmObservation.objects.bulk_create(observations)
            else:
                EDM_Observation.objects.bulk_create(observations)

    return errors


def import_csv_to_levels(csv_file, pillar_survey):
    # Decode the file for reading
    file_name = getattr(csv_file, 'name', 'the uploaded file')
    csv_file = TextIOWrapper(csv_file, encoding='utf-8-sig')
    reader = csv.DictReader(csv_file)        

    # Normalize CSV column headings
    def convert_headings(column_name):
        """Standardizes column names to match model field names."""
        mapping = {
            'pillar_rl': 'reduced_level',
            'pillar_name': 'pillar',
            'rl_standard_deviation': 'rl_standard_deviation'
        }

        return mapping.get(column_name.strip().lower().replace(" ", "_"), column_name)

    # Convert headings
    reader.fieldnames = [convert_headings(field) for field in reader.fieldnames]
    
    # Define required headings
    required_headings = {
        'pillar':'pillar_name',
        'reduced_level':'pillar_rl',
        'rl_standard_deviation':'rl_standard_deviation',
    }
    
    # Check for missing headings
    missing_headings = [
        heading for key, heading in required_headings.items() if key not in reader.fieldnames]
    if missing_headings:
        return [f"The following required headings are missing in the '{file_name}': {', '.join(missing_headings)}"]

    pillar_levels =[]
    errors = []

    # Process each row in the CSV
    for line_num, row in enumerate(reader, start=1):
        try:
            # Resolve pillars for from_pillar and to_pillar
            pillar = pillar_survey.site.pillars.filter(name=row['pillar'].strip()).first()

            if not pillar:
                raise ValueError(f"Invalid from_pillar '{row['pillar']}' on line {line_num}.")

            pillar = pillar_survey.site.pillars.filter(name=row['pillar'].strip()).first()
            pillar_level = Level_Observation(
                pillar_survey=pillar_survey,
                pillar=pillar,
                reduced_level=row.get('reduced_level', '').strip() or None,
                rl_standard_deviation=row.get('rl_standard_deviation', '').strip() or None,
            )
            pillar_level.full_clean()
            pillar_levels.append(pillar_level)

        except Exception as e:
            # Capture detailed error for this line
            errors.append(f"Error on line {line_num}: {e}")

    # Save all valid observations only if there are no errors
    if len(errors) == 0:        
        delete_lvl_obs = Level_Observation.objects.filter(pillar_survey=pillar_survey)
        delete_lvl_obs.delete()
        with transaction.atomic():
            Level_Observation.objects.bulk_create(pillar_levels)

    return errors