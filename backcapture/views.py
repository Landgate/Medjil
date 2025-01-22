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
from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from calibrationsites.models import CalibrationSite, Pillar
from common_func.Convert import decrypt_file, list2dict, group_list
from instruments.models import (
    DigitalLevel, EDM_Inst, EDM_Specification,
    Mets_Inst,
    Mets_Specification, Prism_Inst,
    Prism_Specification, Staff
)
from baseline_calibration.models import (
    Accreditation, Certified_Distance,
    Pillar_Survey, Std_Deviation_Matrix,
    PillarSurveyResults,
    Uncertainty_Budget, Uncertainty_Budget_Source,
    EDM_Observation, Level_Observation
)
from edm_calibration.models import uPillar_Survey, uEDM_Observation
from common_func.SurveyReductions import float_or_null
from geodepy.survey import joins
from .forms import ImportDliDataForm
from .models import Backcapture_History


def db_files2dict(files, is_staff=False):

    columns_dict = {
        'rxBaseline.db':['pk', 'name', 'location',
                'operator', 'calibrated_date', 'reference',
                'ellipsoid_fk', 'confidence_level', 'reference_height',
                'StdICConstant', 'StdICPPM', 'humidity', 'ArchiveFlag',
                'operator_address'],
        'rxBaselineAccuracy.db':['baseline_fk', 'UncertaintyConstant',
                                 'UncertaintyScale'],
        'rxDistance.db': ['pk', 'baseline_fk', 'from_pillar_fk',
                    'to_pillar_fk', 'certified_distance', 'DistSigma'],
        'rxEDMObs.db':['pk', 'MeasID', 'EDMObsDistance',
                    'MeasDryTemp', 'MeasHumidity', 'MeasPressure'],
        'rxInstrument.db':['pk', 'inst_type', 'InstrumentModel_fk',
                    'serial_number', 'manu_unc_const', 'manu_unc_ppm',
                    'AntennaModelID', 'InstAntennaSerialNo',
                    'InstConstant', 'InstScaleFact', 'comments'],
        'rxInstrumentMake.db':['pk', 'manufacturer', 'country'],
        'rxInstrumentModel.db':['pk', 'InstrumentMake_fk', 'name', 'type',
                    'manu_unc_const', 'manu_unc_ppm',
                    'unit_length', 'frequency', 'carrier_wavelength',
                    'comments', 'is_pulse', 'manu_ref_refrac_index' ],
        'rxJob.db':['pk', 'name', 'instrument_edm_fk','instrument_prism_fk',
                    'edm_owner', 'prism_owner', 'ProcessingSoftware',
                    'survey_date', 'survey_time', 'computation_date',
                    'computation_time', 'observer_name', 'baseline_fk',
                    'weather', 'TempCorr', 'PressureCorr', 'StdDevTemp', 
                    'StdDevPressure', 'InstCentringStdDev', 'InstLevellingStdDev',
                    'calibration_type', 'JobComments', 'edm_owner_address', 'Thermometer1',
                    'Thermometer2','Barometer1','Barometer2','ThermometerCorr1',
                    'ThermometerCorr2','BarometerCorr1','BarometerCorr2',
                    'NumberThermometers','NumberBarometers'],
        'rxJMeasure.db':['pk', 'MeasType', 'job_fk','from_pillar_fk', 'to_pillar_fk',
                    'from_ht', 'to_ht', 'raw_dry_temp', 'raw_humidity', 'humidity_type',
                    'raw_pressure', 'mets_flag', 'wet_temp', 'humidity',
                    'raw_dry_temp2', 'raw_pressure2', 'raw_humidity2'],
        'rxPillar.db':['pk', 'baseline_fk', 'order','name', 'height', 'offset',
                    'latitude', 'longitude', 'EllipsARadius', 'EllipsBRadius',
                    'EllipsOrient', 'HtStdDev'],
        'rxStandard.db': ['Type', 'StandardConstant', 'StandardScale','Authority',
                    'Description', 'LUMUnits', 'AlternateConstant',
                    'AlternateScale'],
        'rxUncertaintyBaseline.db':['Description', 'Default', 'Unit'],
        'rxUncertaintyEDM.db':['Description', 'Default', 'Unit']
        }
    # Import the BASELINE_WA database into a single dictionary.
    rx={}
    for f in files:
        pk = 'pk'
        ky = f.name[2:-3]
        if f.name in columns_dict.keys():
            if f.name == 'rxBaselineAccuracy.db': pk = 'baseline_fk'
            if f.name == 'rxStandard.db': pk = 'Type'
            if f.name.startswith('rxUncertainty'): pk = 'Description'
            if not is_staff and f.name == 'rxJob.db':
                rx[ky] = list2dict(
                    decrypt_file(f), columns_dict[f.name], pk,
                    filter_key = 'calibration_type',
                    filter_value = 'I')
            else:
                rx[ky] = list2dict(decrypt_file(f), columns_dict[f.name], pk)
    
    # remove unused JobMeasurements from the variable
    try:
        del_list = []
        for pk, o in rx['JMeasure'].items():
            if o['job_fk'] not in rx['Job']: 
                del_list.append(pk)
        for pk in del_list:
            del rx['JMeasure'][pk]
    except:
        pass
    return rx


def get_medjil_baselines():
    medjil_baselines_obj = CalibrationSite.objects.filter(
        site_type = 'baseline')
    medjil_baselines = []
    for medjil_baseline in medjil_baselines_obj:
        medjil_baselines.append({
            'baseline' : medjil_baseline,
            'pillars' :  Pillar.objects.filter(
                site_id = medjil_baseline.pk).order_by('order')
            })
    return medjil_baselines

            
def unknown_mets(mets_type, request, mets_number='Unknown'):
    try:
        mets_specs, created = Mets_Specification.objects.get_or_create(
            inst_type=mets_type,
            mets_make_name='Unknown Make Name'.upper(),
            mets_model_name='Unknown Model Name',
            mets_owner=request.user.company,            
            manu_unc_const=0,
            manu_unc_k=2,
            measurement_increments=0.0001
            )
        if created:
            print(f'{mets_type} Specs in Medjil created successfully')
        
        this_inst, created = Mets_Inst.objects.get_or_create(
            mets_specs=mets_specs,
            mets_number=mets_number,
            mets_custodian=None,
            comment=f'Unknown {mets_type} from Backcapture Import')
        if created:
            print(f'{mets_type} in Medjil created successfully')
            
        return this_inst
    
    except Exception as e:
        print(e)
        return False


def create_medjil_level_gear(request, commit_errors):
    medjil_level, medjil_staff = None, None
    try:
        medjil_level, created = DigitalLevel.objects.get_or_create(
            level_owner = request.user.company,
            level_number = '0000',
            level_make_name = 'Unknown',
            level_model_name = 'Unknown')
    except Exception as e:
        commit_errors.append(f'Error creating generic level in Medjil: {e}')
    
    # Create dummy Barcode staff in Medjil
    try:
        medjil_staff, created = Staff.objects.get_or_create(
            staff_make_name = 'Unknown',
            staff_model_name = 'Unknown',
            staff_owner = request.user.company,
            staff_number = '',
            staff_type = 'Unknown',
            staff_length = 4,
            thermal_coefficient = None)
    except Exception as e:
        commit_errors.append(
            f'Error creating generic barcode staff in Medjil: {e}')
    return medjil_level, medjil_staff, commit_errors


def create_medjil_accreditation(rx, commit_errors, request):
    # Commit an accreditaion to use for backcaptured data
    medjil_accreditation = Accreditation.objects.filter(
        accredited_company = request.user.company,
        statement = 'Unknown accreditation from BaselineDLI backcaptured data').first()
    if not medjil_accreditation:
        try:
            medjil_accreditation = Accreditation.objects.create(
                accredited_company = request.user.company,
                valid_from_date = '1900-01-01',
                valid_to_date = '2022-01-01',
                LUM_constant = rx['Standard']['F']['StandardConstant'],
                LUM_ppm = rx['Standard']['F']['StandardScale'],
                statement = 'Unknown accreditation from BaselineDLI backcaptured data')    
        except Exception as e:
            commit_errors.append(
                f'Error creating generic accreditation in Medjil: {e}')
    return medjil_accreditation, commit_errors


def create_medjil_model(rx, request, commit_errors):
    # Create BASELINE Models as Medjil Model Specifications
    for rx_model in rx['InstrumentModel'].values():
        if rx_model['manu_unc_const'] == '': rx_model['manu_unc_const'] = 0
        if rx_model['manu_unc_ppm'] == '': rx_model['manu_unc_ppm'] = 0
        
        rx_make = rx['InstrumentMake'][rx_model['InstrumentMake_fk']]
        make = rx_make['manufacturer'].upper().strip()
        zpc = float(rx_model['manu_unc_const']) * 1000
        ppm = rx_model['manu_unc_ppm']
        model = rx_model['name'].strip()
               
        # create Prism in Medjil Prism_Specification tables
        if rx_model['type'] == 'P':
            # Create the prism in Medjil Specifications tables
            # If the unique constraint fails, try with different model_name
            try:
                rx_model['medjil_specs_pk'], created = (
                    Prism_Specification.objects.get_or_create(
                        prism_make_name = make,
                        prism_model_name = model,
                        prism_owner = request.user.company,
                        manu_unc_const = float(zpc) * 2,
                        manu_unc_k = 2))
            except:
                try:
                    rx_model['medjil_specs_pk'], created = (
                        Prism_Specification.objects.get_or_create(
                            prism_make_name = make,
                            prism_model_name = model + ' (Baseline.exe)',
                            prism_owner = request.user.company,
                            manu_unc_const = float(zpc) * 2,
                            manu_unc_k = 2))
                except Exception as e:
                    commit_errors.append(
                        f'Error creating Prism Model {model} in Medjil: {e}')
        else:
            # Create the EDM in Medjil EDM_Specification tables
            # If the unique constraint fails, try with different model_name
            rx_model['type'] = 'pu'
            if rx_model['is_pulse'] =='False': rx_model['type'] ='ph'
            if len(rx_model['manu_ref_refrac_index']) == 0:
                rx_model['manu_ref_refrac_index'] = '999999999'
            if len(rx_model['frequency']) == 0:
                rx_model['frequency'] = '999999999'
            if len(rx_model['unit_length']) == 0:
                rx_model['unit_length'] = '999999999'
            if len(rx_model['carrier_wavelength']) == 0:
                rx_model['carrier_wavelength'] = '999999999'
            try:
                rx_model['medjil_specs_pk'], created = (
                    EDM_Specification.objects.get_or_create(
                        edm_make_name = make,
                        edm_model_name = model,
                        edm_owner = request.user.company,
                        edm_type = rx_model['type'],
                        manu_unc_const = float(zpc) * 2,
                        manu_unc_ppm = float(ppm) * 2,
                        manu_unc_k = 2,
                        unit_length = rx_model['unit_length'],
                        frequency = rx_model['frequency'],
                        carrier_wavelength = rx_model['carrier_wavelength'],
                        manu_ref_refrac_index = rx_model['manu_ref_refrac_index'],
                        measurement_increments = 0.0001))
            except:
                try:
                    rx_model['medjil_specs_pk'], created = (
                        EDM_Specification.objects.get_or_create(
                            edm_make_name = make,
                            edm_model_name = model + ' (Baseline.exe)',
                            edm_owner = request.user.company,
                            edm_type = rx_model['type'],
                            manu_unc_const = float(zpc) * 2,
                            manu_unc_ppm = float(ppm) * 2,
                            manu_unc_k = 2,
                            unit_length = rx_model['unit_length'],
                            frequency = rx_model['frequency'],
                            carrier_wavelength = rx_model['carrier_wavelength'],
                            manu_ref_refrac_index = rx_model['manu_ref_refrac_index'],
                            measurement_increments = 0.0001))
                except Exception as e:
                    commit_errors.append(
                        f'Error creating EDM Model {model} in Medjil: {e}')
    return rx, commit_errors


def create_medjil_insts(rx, request, commit_errors):
    for rx_inst in rx['Instrument'].values():
        rx_specs = rx['InstrumentModel'][rx_inst['InstrumentModel_fk']]
        try:
            specs = rx_specs['medjil_specs_pk']
            if rx_inst['inst_type'] == 'E':
                rx_inst['medjil_pk'], _ = EDM_Inst.objects.get_or_create(
                    edm_number = rx_inst['serial_number'],
                    edm_custodian = request.user,
                    comment = rx_inst['comments'],
                    edm_specs = specs)
        except:
            try:
                specs = rx_specs['medjil_specs_pk']
                if rx_inst['inst_type'] == 'E':
                    rx_inst['medjil_pk'], _ = EDM_Inst.objects.get_or_create(
                        edm_number = rx_inst['serial_number'] + ' (Baseline.exe)',
                        edm_custodian = request.user,
                        comment = rx_inst['comments'],
                        edm_specs = specs)
            except Exception as e:
                commit_errors.append(
                    f"Error creating EDM Instrument SN {rx_inst['serial_number']} in Medjil: {e}")
        try:
            if rx_inst['inst_type'] == 'P':
                rx_inst['medjil_pk'], _ = Prism_Inst.objects.get_or_create(
                    prism_number = rx_inst['serial_number'],
                    prism_custodian = request.user,
                    comment = rx_inst['comments'],
                    prism_specs = specs)
        except:
            try:
                if rx_inst['inst_type'] == 'P':
                    rx_inst['medjil_pk'], _ = Prism_Inst.objects.get_or_create(
                        prism_number = rx_inst['serial_number'] + ' (Baseline.exe)',
                        prism_custodian = request.user,
                        comment = rx_inst['comments'],
                        prism_specs = specs)
            except Exception as e:
                commit_errors.append(
                    f"Error creating Prism Instrument SN {rx_inst['serial_number']} in Medjil: {e}")
            
    return rx, commit_errors


def mod_pillars(rx):
    # Combine the rxDistance and rxPillar data into one usable dictionary
    rxDistance = group_list(rx['Distance'].values(), 'baseline_fk')
    rxPillar = group_list(rx['Pillar'].values(), 'baseline_fk')
    for baseline_id, grp in rxDistance.items():
        pillars = rxPillar[baseline_id]['grp_baseline_fk']
        certified_dists = grp['grp_baseline_fk']
        for dist in certified_dists:
            dist['from_pillar_order'] = int(
                rx['Pillar'][dist['from_pillar_fk']]['order'])
        grp['grp_baseline_fk'] = sorted(certified_dists, key=lambda x: x['from_pillar_order'])     
        
        # Add certified_distances to rxPillar Dictionary
        pillars = sorted(pillars, key=lambda x: float(x['order']))
        sum_dist = 0
        pillars[0]['certified_distance'] = 0
        pillars[0]['DistSigma'] = 0
        for pillar, dist in zip(pillars[1:], certified_dists):
            sum_dist+= float(dist['certified_distance'])
            pillar['certified_distance'] = sum_dist
            pillar['DistSigma'] = dist['DistSigma']
    return rxPillar


def match_baseline(pillars, medjil_baselines):
    # Find the Medjil baseline that matches
    medjil_pillars = None
    medjil_bline = None
    min_match_dist = 1e10
    for medjil_baseline in medjil_baselines:
        if len(pillars) == len(medjil_baseline['pillars']):
            match_dist = 0
            for pillar, medjil_pillar in zip(pillars, medjil_baseline['pillars']):
                medjil_join, _ = joins(
                    medjil_baseline['pillars'][0].easting,
                    medjil_baseline['pillars'][0].northing,
                    medjil_pillar.easting,
                    medjil_pillar.northing)
                match_dist += abs(pillar['certified_distance'] - medjil_join)
            if match_dist < min_match_dist:
                min_match_dist = match_dist
                medjil_pillars = medjil_baseline['pillars']
                medjil_bline = medjil_baseline['baseline']
    
    if medjil_pillars:
        for p, mp in zip(pillars, medjil_pillars): 
            p['medjil_pillar'] = mp
    return medjil_bline, medjil_pillars
   

@login_required(login_url="/accounts/login") 
def import_dli(request):
    importForm = ImportDliDataForm(
        request.POST or None,
        request.FILES or None)
    
    # Restrict user to 3 attempts per day
    if importForm.is_valid():
        threshold = timezone.now() - timezone.timedelta(days=1)
        Backcapture_History.objects.filter(created_on__lt=threshold).delete()
        commit_count = Backcapture_History.objects.filter(user=request.user).count()
        
        if commit_count >=300:
            importForm.add_error(None, 'Error - You have exceeded your number of database imports for today.')
    
    if importForm.is_valid():
        # Import the BASELINE_WA database into a single dictionary.
        rx = db_files2dict(importForm.cleaned_data["file_field"],
                           request.user.is_staff)
                
        # query the medjil baselines
        medjil_baselines = get_medjil_baselines()
        
        commit_errors = []
        commit_successes = []
        if all(key in rx.keys() for key in ['InstrumentMake', 'InstrumentModel', 'Instrument']):            
            # Create BASELINE Models as Medjil Models/Specifications
            rx, commit_errors = create_medjil_model(rx, request, commit_errors)
        
            # Create BASELINE instruments as Medjil EDMs and Prisms
            rx, commit_errors = create_medjil_insts(rx, request, commit_errors)
        
        if request.user.is_staff:
            # Create in Medjil
            #   - dummy Level
            #   - dummy Staff
            #   - dummy Hygrometer
            #   - dummy accreditation 
            medjil_level, medjil_staff, commit_errors = create_medjil_level_gear(
                request, commit_errors)
            medjil_hygro = unknown_mets('hygro', request)
            medjil_accreditation, commit_errors = create_medjil_accreditation(
                rx, commit_errors, request)
        
        if 'JMeasure' in rx.keys():
            jobs_measurements = group_list(rx['JMeasure'].values(),'job_fk')
        
        # Combine the rxDistance and rxPillar data into one usable dictionary
        if 'Distance' in rx.keys() and 'Pillar' in rx.keys():
            rxPillar =  mod_pillars(rx)

        if all(key in rx.keys() for key in ['Job', 'EDMObs', 'Distance', 'Pillar']):
            for job in rx['Job'].values():
                commit_error = []
                # Create the Mets gear in Medjil
                job['medjil_baro1_pk'] = unknown_mets('baro', request, job['Barometer1'])
                job['medjil_baro2_pk'] = unknown_mets('baro', request, job['Barometer2'])
                job['medjil_thermo1_pk'] = unknown_mets('thermo', request, job['Thermometer1'])
                job['medjil_thermo2_pk'] = unknown_mets('thermo', request, job['Thermometer2'])
                
                # Create the Uncertainty Budget to match
                rx_UC_Name = (
                    'Backcapture - ' +
                    job['StdDevTemp'] +
                    job['StdDevPressure'] +
                    job['InstCentringStdDev'] +
                    job['InstLevellingStdDev'] 
                    )
                try:
                    rx_UC_budget, created = Uncertainty_Budget.objects.get_or_create(
                        name = rx_UC_Name, 
                        company = request.user.company,
                        std_dev_of_zero_adjustment = 0.0002,
                        auto_EDMI_scf = False,
                        auto_EDMI_scf_drift = False,
                        auto_EDMI_round = False,
                        auto_humi_zpc = False,
                        auto_humi_rounding = False,
                        auto_pressure_zpc = False,
                        auto_pressure_rounding = False,
                        auto_temp_zpc = False,
                        auto_temp_rounding = False,
                        auto_cd = True,
                        auto_EDMI_lr = True,
                        auto_hgts = True,
                        auto_os = True,
                        )
                except:
                    rx_UC_budget = Uncertainty_Budget.objects.get(
                        name = 'Default',
                        company__company_name = 'Landgate')
                if float(job['StdDevTemp']) > 0:
                    UC_source1,_ = Uncertainty_Budget_Source.objects.get_or_create(
                        uncertainty_budget = rx_UC_budget,
                        group = '04',
                        description = 'Imported From BaselineWA software',
                        units = '°C',
                        uc95 = float(job['StdDevTemp'])
                        )
                if float(job['StdDevPressure']) > 0:
                    UC_source2,_ = Uncertainty_Budget_Source.objects.get_or_create(
                        uncertainty_budget = rx_UC_budget,
                        group = '05',
                        description = 'Imported From BaselineWA software',
                        units = 'hPa',
                        uc95 = float(job['StdDevPressure'])
                        )
                if float(job['InstCentringStdDev']) > 0:
                        if float(job['InstCentringStdDev']) < 0.01:
                            # Note - some data is in m some in mm Grrr#!!!
                            job['InstCentringStdDev'] = float(job['InstCentringStdDev']) * 1000
                        UC_source3,_ = Uncertainty_Budget_Source.objects.get_or_create(
                            uncertainty_budget = rx_UC_budget,
                            group = '09',
                            description = 'Imported From BaselineWA software',
                            units = 'm',
                            uc95 = float(job['InstCentringStdDev'])/1000
                            )
                if float(job['InstLevellingStdDev']) > 0:
                    UC_source4,_ = Uncertainty_Budget_Source.objects.get_or_create(
                        uncertainty_budget = rx_UC_budget,
                        group = '10',
                        description = 'Imported From BaselineWA software',
                        units = 'm',
                        uc95 = float(job['InstLevellingStdDev'])
                        )
                try:
                    job_measurements = jobs_measurements[job['pk']]['grp_job_fk']
                    uniq_bays = set(
                        [f'{m["from_pillar_fk"]} - {m["to_pillar_fk"]}' for m in job_measurements]
                        )
                except:
                    job_measurements = []
                    uniq_bays = []
                meas_kys = [m['pk'] for m in job_measurements]
                job_measurements = dict(zip(meas_kys, job_measurements))
                job_edm_obs = [obs for obs in rx['EDMObs'].values() if obs['MeasID'] in meas_kys]
                
                # Find the Medjil baseline that matches
                pillars = rxPillar[job['baseline_fk']]['grp_baseline_fk']

                medjil_baseline, medjil_pillars = match_baseline(
                    pillars, medjil_baselines)
                pillars = dict(zip([p['pk'] for p in pillars], pillars))
                
                if not medjil_pillars:
                    commit_error.append(
                        f"No Medjil baseline matched for job: {job['name']}")

                #  NB this mets_applied = True, ['mets_flag'] == 'Y' appears wrong, but it has been checked and BASELINE.exe appeared to be the cause of confusion
                mets_applied = True
                try:
                    key_0 = list(job_measurements)[0]
                    if job_measurements[key_0]['mets_flag'] == 'Y': mets_applied = False
                except Exception as e:
                    commit_error.append(
                        f'{job["name"]} Error setting mets_flag, default to Y: {e}')

                
                thermo_calib_applied = all([job['ThermometerCorr1'] == '0', 
                                            job['ThermometerCorr2'] == '0'])
                if mets_applied: thermo_calib_applied = True
                
                baro_calib_applied = all([job['BarometerCorr1'] == '0',
                                          job['BarometerCorr2'] == '0'])
                if mets_applied: baro_calib_applied = True
                
                # Find the EDM in BASELINE
                try:
                    edm = rx['Instrument'][job['instrument_edm_fk']]
                    medjil_edm = edm['medjil_pk']
                    if float(medjil_edm.edm_specs.id):pass
                except Exception as e:
                    commit_error.append(
                        f'EDM specified for {job["name"]} not in BASELINE database files: {e}')
                
                # Find the Prism in BASELINE
                try:
                    prism = rx['Instrument'][job['instrument_prism_fk']]
                    medjil_prism = prism['medjil_pk']
                    if float(medjil_prism.prism_specs.id):pass
                except Exception as e:
                    commit_error.append(
                        f'Prism specified for {job["name"]} not in BASELINE database files: {e}')

                if job['calibration_type'] == 'B' and len(commit_error) == 0:
                    medjil_baseline_calibration, created = Pillar_Survey.objects.get_or_create(
                        baseline = medjil_baseline,
                        survey_date = dt.strptime(
                            job['survey_date'],'%d/%m/%Y').isoformat()[:10],
                        computation_date = dt.strptime(
                            job['computation_date'],'%d/%m/%Y').isoformat()[:10],
                        accreditation = medjil_accreditation,
                        apply_lum = False,
                        observer = job['observer_name'],
                        weather = 'Sunny/Clear',
                        job_number = rx['Baseline'][job['baseline_fk']]['reference'],
                        comment = f"{job['JobComments']} ({job['name']})",
                        edm = medjil_edm,
                        prism = medjil_prism,
                        mets_applied = mets_applied,
                        edmi_calib_applied = True,
                        level = medjil_level,
                        staff = medjil_staff,
                        staff_calib_applied = True,
                        thermometer = job['medjil_thermo1_pk'],
                        thermo_calib_applied = thermo_calib_applied,
                        barometer = job['medjil_baro1_pk'],
                        baro_calib_applied = baro_calib_applied,
                        hygrometer = medjil_hygro,
                        hygro_calib_applied = True,
                        psychrometer = None,
                        psy_calib_applied = True,
                        uncertainty_budget = rx_UC_budget,
                        outlier_criterion = 3,
                        fieldnotes_upload = None,
                        )
                    zpc_uncertainty = float(rx['BaselineAccuracy'][job['baseline_fk']]['UncertaintyConstant'])/1000
                    dof = int(len(uniq_bays) - len(pillars))
                    if created: 
                        commit_successes.append(job["name"])
                        PillarSurveyResults.objects.get_or_create(
                            pillar_survey = medjil_baseline_calibration,
                            zero_point_correction = 0,
                            zpc_uncertainty = zpc_uncertainty,
                            experimental_std_dev = 0.001,
                            degrees_of_freedom = dof,
                            )
                        
                    else:commit_error.append(
                        f'Database commit error while creating {job["name"]}')

                    first_pillar = medjil_pillars[0]
                    UC_formula = rx['BaselineAccuracy'][job['baseline_fk']]
                    for pillar, medjil_pillar in zip(pillars.values(), medjil_pillars):                            
                        combined_uc = (
                            float(UC_formula['UncertaintyScale'])*10**-6 * pillar['certified_distance']
                            + float(UC_formula['UncertaintyConstant']) * 0.001)
                        
                        # Store certified distances
                        medjil_cert_dist, created = Certified_Distance.objects.get_or_create(
                            pillar_survey = medjil_baseline_calibration,
                            from_pillar = first_pillar,
                            to_pillar = medjil_pillar,
                            distance =  pillar['certified_distance'],
                            a_uncertainty = float(pillar['DistSigma']),
                            combined_uncertainty = combined_uc,
                            offset = float(pillar['offset']),
                            os_uncertainty = float(
                                rx['UncertaintyBaseline']['Pillar offset']['Default']) / 1000,
                            reduced_level = float(pillar['height']),
                            rl_uncertainty = float(pillar['HtStdDev'])
                            )
                        if not created: commit_error.append(
                            f'Database commit error while creating certified distance {first_pillar} to {medjil_pillar} in {job["name"]}')
                        
                        #Store level observations
                        medjil_lvl_obs, created = Level_Observation.objects.get_or_create(
                            pillar_survey = medjil_baseline_calibration,
                            pillar = medjil_pillar,
                            reduced_level = float(pillar['height']),
                            rl_standard_deviation =float(pillar['HtStdDev'])
                            )
                        if not created: commit_error.append(
                            f'Database commit error while creating certified height for {medjil_pillar} in {job["name"]}')
                        

                    # Store observations used for calibration
                    try:
                        for obs in job_edm_obs:
                            meas = job_measurements[obs['MeasID']]
                            from_pillar = pillars[meas['from_pillar_fk']]
                            to_pillar = pillars[meas['to_pillar_fk']]
                            dist, az = joins(
                                float(from_pillar['offset']),
                                from_pillar['certified_distance'],
                                float(to_pillar['offset']),
                                to_pillar['certified_distance'])
                            medjil_obs, created = EDM_Observation.objects.get_or_create(
                                pillar_survey = medjil_baseline_calibration,
                                from_pillar = from_pillar['medjil_pillar'],
                                to_pillar = to_pillar['medjil_pillar'],
                                inst_ht = meas['from_ht'],
                                tgt_ht = meas['to_ht'],
                                hz_direction = az,
                                raw_slope_dist = obs['EDMObsDistance'],
                                raw_temperature = float_or_null(obs['MeasDryTemp']) or 20,
                                raw_pressure = float_or_null(obs['MeasPressure']) or 1013.25,
                                raw_humidity = float_or_null(obs['MeasHumidity']) or 50
                                )
                    except Exception as e:
                        commit_errors.append(
                            f'Error importing measurement observations for {job["name"]}: {e}')
                        
                    
                    # BASELINE WA used a linear formula to assign standard deviations
                    # to the certified distances. Medjil stores the full vcv by
                    # recording standard deviations of all from and to pillar combinations
                    pillars = list(pillars.values())
                    for i1, from_pillar in enumerate(pillars[:-1]):
                        for to_pillar in pillars[i1+1:]:
                            p1_p2_dist = abs(from_pillar['certified_distance'] - 
                                          to_pillar['certified_distance'])
                            uc = (float(UC_formula['UncertaintyScale'])*10**-6 * p1_p2_dist
                                  + float(UC_formula['UncertaintyConstant']) * 0.001)
                            medjil_sdev_mtx, created = (
                                Std_Deviation_Matrix.objects.get_or_create(
                                    pillar_survey = medjil_baseline_calibration,
                                    from_pillar = from_pillar['medjil_pillar'],
                                    to_pillar = to_pillar['medjil_pillar'],
                                    std_uncertainty = uc
                                    ))
                
                if job['calibration_type'] == 'I' and len(commit_error) == 0:
                    test_cyclic = True
                    if float(medjil_edm.edm_specs.unit_length) < 5: test_cyclic = False
                    try:
                        medjil_edmi_calibration, created = (
                            uPillar_Survey.objects.get_or_create(
                                site = medjil_baseline,
                                survey_date =  dt.strptime(
                                    job['survey_date'],'%d/%m/%Y').isoformat()[:10],
                                computation_date = dt.strptime(
                                    job['computation_date'],'%d/%m/%Y').isoformat()[:10],
                                observer = job['observer_name'],
                                weather = 'Sunny/Clear',
                                job_number = rx['Baseline'][job['baseline_fk']]['reference'],
                                comment = f"{job['JobComments']} ({job['name']})",
                                edm = medjil_edm,
                                prism = medjil_prism,
                                mets_applied = mets_applied,
                                thermometer = job['medjil_thermo1_pk'],
                                barometer = job['medjil_baro1_pk'],
                                # hygrometer = medjil_hygro,
                                thermo_calib_applied = thermo_calib_applied,
                                baro_calib_applied = baro_calib_applied,
                                hygro_calib_applied = True,
                                uncertainty_budget = rx_UC_budget,
                                outlier_criterion = 3,
                                test_cyclic = test_cyclic
                                )
                            )
                        commit_successes.append(job["name"])
                    except Exception as e:
                        commit_errors.append(
                            f'Error importing job {job["name"]}: {e}')
                    
                    # Store observations used for calibration
                    try:
                        for obs in job_edm_obs:
                            meas = job_measurements[obs['MeasID']]
                            from_pillar = pillars[meas['from_pillar_fk']]
                            to_pillar = pillars[meas['to_pillar_fk']]
                            medjil_edmi_obs, created = (
                                uEDM_Observation.objects.get_or_create(
                                    pillar_survey = medjil_edmi_calibration,
                                    from_pillar = from_pillar['medjil_pillar'],
                                    to_pillar = to_pillar['medjil_pillar'],
                                    inst_ht = meas['from_ht'],
                                    tgt_ht = meas['to_ht'],
                                    raw_slope_dist = obs['EDMObsDistance'],
                                    raw_temperature = float_or_null(obs['MeasDryTemp']) or 20,
                                    raw_pressure = float_or_null(obs['MeasPressure']) or 1013.25,
                                    raw_humidity = float_or_null(obs['MeasHumidity']) or 1013.25
                                    ))
                    except Exception as e:
                        commit_errors.append(
                            f'Error importing measurement observations for {job["name"]}: {e}')

                if len(commit_error) > 0: commit_errors += commit_error
        
        # Finish import by returning the import report
        user_history = Backcapture_History(user=request.user)
        user_history.save()
        context ={
            'commits': commit_successes,
            'Check_Errors': commit_errors}
        return render(request, 'backcapture/import_report.html', context)
    context ={
        'Header': 'Import BaselineDLI Database Records',
        'form': importForm}
    
    return render(request, 'backcapture/import_dli.html', context)