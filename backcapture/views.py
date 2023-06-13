from datetime import datetime as dt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from calibrationsites.models import CalibrationSite, Pillar
from common_func.Convert import decrypt_file, list2dict, group_list
from instruments.models import (
    DigitalLevel, EDM_Inst, EDM_Specification,
    InstrumentMake, InstrumentModel, Mets_Inst,
    Mets_Specification, Prism_Inst,
    Prism_Specification, Staff
)
from baseline_calibration.models import (
    Accreditation, Certified_Distance,
    Pillar_Survey, Std_Deviation_Matrix,
    Uncertainty_Budget, EDM_Observation
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
                rx[ky] = list2dict(decrypt_file(f), columns_dict[f.name], pk,
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

            
def unknown_mets(mets_type, request, mets_number=''):
    # Create the Mets of type in Medjil
    try:
        medjil_mets_model, created = InstrumentModel.objects.get_or_create(
            inst_type=mets_type, make=None, model=f'Unknown {mets_type}')
            # use unpacking to get the created flag
    except InstrumentModel.DoesNotExist:
        print(f'{mets_type} Model in Medjil not inserted')
    except Exception as e:
        print(f'Error creating {mets_type} Model in Medjil: {e}')
    else:
        if created:
            print(f'{mets_type} Model in Medjil created successfully')
        
        mets_specs, created = Mets_Specification.objects.get_or_create(
            mets_owner=request.user.company,
            mets_model=medjil_mets_model,
            manu_unc_const=0,
            manu_unc_k=2,
            measurement_increments=0.0001)
        if created:
            print(f'{mets_type} Specs in Medjil created successfully')
        
        this_inst, created = Mets_Inst.objects.get_or_create(
            mets_specs=mets_specs,
            mets_number=mets_number,
            mets_custodian=None,
            comment=f'Unknown {mets_type}')
        if created:
            print(f'{mets_type} in Medjil created successfully')
    return this_inst


def create_medjil_level_gear(request, commit_errors):
    try:
        medjil_level, created = DigitalLevel.objects.get_or_create(
            level_owner = request.user.company,
            level_number = '0000',
            level_model = None)
    except Exception as e:
        commit_errors.append(f'Error creating generic level in Medjil: {e}')
    
    # Create dummy Barcode staff in Medjil
    try:
        medjil_staff, created = Staff.objects.get_or_create(
            staff_model = None,
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

            
def create_medjil_manu(rx, commit_errors):
    # Create BASELINE Makes as Medjil Manufacturers
    for rx_make in rx['InstrumentMake'].values():
        manufacturer = rx_make['manufacturer'].upper().strip()                    
        rx_make['medjil_pk'] = InstrumentMake.objects.filter(
            make = manufacturer).first()
        if not rx_make['medjil_pk']:
            try:
                rx_make['medjil_pk'] = InstrumentMake.objects.create(
                    make=manufacturer,
                    make_abbrev=manufacturer[:4].upper())
            except Exception as e:
                commit_errors.append(
                    f'Error creating {manufacturer} Manufacturer in Medjil: {e}')
    return rx, commit_errors


def create_medjil_model(rx, request, commit_errors):
    # Create BASELINE Models as Medjil Models/Specifications
    for rx_model in rx['InstrumentModel'].values():
        rx_make = rx['InstrumentMake'][rx_model['InstrumentMake_fk']]
        make = rx_make['medjil_pk']
        model = rx_model['name'].upper().strip()
        inst_type = 'edm'
        if rx_model['type'] != 'P': inst_type = 'prism'
        # create the Models in Medjil
        try:
            rx_model['medjil_model_pk'], created = InstrumentModel.objects.get_or_create(
                inst_type = inst_type,
                make = make,
                model = model)
        except Exception as e:
            commit_errors.append(
                f'Error creating {inst_type} Model {model} in Medjil: {e}')
        
        # create the Specs in Medjil tables
        if rx_model['manu_unc_const'] == '': rx_model['manu_unc_const'] = 0
        if rx_model['manu_unc_ppm'] == '': rx_model['manu_unc_ppm'] = 0
        if rx_model['type'] == 'P':
            # Create the prism in Medjil Specifications tables
            try:
                rx_model['medjil_specs_pk'], created = (
                    Prism_Specification.objects.get_or_create(
                        prism_owner = request.user.company,
                        prism_model = rx_model['medjil_model_pk'],
                        manu_unc_const = float(rx_model['manu_unc_const']) * 2,
                        manu_unc_k = 2))
            except Exception as e:
                commit_errors.append(
                    f'Error creating Prism Model {model} in Medjil: {e}')
        else:
            # Create the EDM in Medjil Model and Specifications tables
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
                        edm_owner = request.user.company,
                        edm_model = rx_model['medjil_model_pk'],
                        edm_type = rx_model['type'],
                        manu_unc_const = float(rx_model['manu_unc_const']) * 2,
                        manu_unc_ppm = float(rx_model['manu_unc_ppm']) * 2,
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
                rx_inst['medjil_pk'], created = EDM_Inst.objects.get_or_create(
                    edm_number = rx_inst['serial_number'],
                    edm_custodian = request.user,
                    comment = rx_inst['comments'],
                    edm_specs = specs)
            if rx_inst['inst_type'] == 'P':
                rx_inst['medjil_pk'], created = Prism_Inst.objects.get_or_create(
                    prism_number = rx_inst['serial_number'],
                    prism_custodian = request.user,
                    comment = rx_inst['comments'],
                    prism_specs = specs)
        except Exception as e:
            commit_errors.append(
                f"Error creating Instrument SN {rx_inst['serial_number']} in Medjil: {e}")
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
                medjil_join, az = joins(
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
        
        if commit_count >=3:
            importForm.add_error(None, 'Error - You have exceeded your number of database imports for today.')
    
    if importForm.is_valid():
        # Import the BASELINE_WA database into a single dictionary.
        rx = db_files2dict(importForm.cleaned_data["file_field"],
                           request.user.is_staff)
        
        Unknown_UC_budget = Uncertainty_Budget.objects.get(
                    name = 'Default', 
                    company__company_name = 'Landgate')
        
        # query the medjil baselines
        medjil_baselines = get_medjil_baselines()
        
        commit_errors = []
        commit_successes = []
        if all(key in rx.keys() for key in ['InstrumentMake', 'InstrumentModel', 'Instrument']):
            # Create BASELINE Makes as Medjil Manufacturers
            rx, commit_errors = create_medjil_manu(rx, commit_errors)
            
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

                mets_applied = False
                try:
                    if job_measurements[0]['mets_flag'] == 'N': mets_applied = True
                except:
                    mets_applied = True
                
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
                        uncertainty_budget = Unknown_UC_budget,
                        outlier_criterion = 3,
                        fieldnotes_upload = None,
                        zero_point_correction = 0,
                        zpc_uncertainty = float(rx['BaselineAccuracy'][job['baseline_fk']]['UncertaintyConstant'])/1000,
                        variance = 1,
                        degrees_of_freedom = int(len(uniq_bays) - len(pillars)),
                        )
                    commit_successes.append(job["name"])

                    first_pillar = medjil_pillars[0]
                    UC_formula = rx['BaselineAccuracy'][job['baseline_fk']]
                    for pillar, medjil_pillar in zip(pillars.values(), medjil_pillars):                            
                        combined_uc = (
                            float(UC_formula['UncertaintyScale'])*10**-6 * pillar['certified_distance']
                            + float(UC_formula['UncertaintyConstant']) * 0.001)
                        
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
                                raw_temperature = float_or_null(obs['MeasDryTemp']),
                                raw_pressure = float_or_null(obs['MeasPressure']),
                                raw_humidity = float_or_null(obs['MeasHumidity'])
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
                            edm = medjil_edm,
                            prism = medjil_prism,
                            mets_applied = mets_applied,
                            thermometer = job['medjil_thermo1_pk'],
                            barometer = job['medjil_baro1_pk'],
                            hygrometer = medjil_hygro,
                            thermo_calib_applied = thermo_calib_applied,
                            baro_calib_applied = baro_calib_applied,
                            hygro_calib_applied = True,
                            uncertainty_budget = Unknown_UC_budget,
                            outlier_criterion = 3,
                            test_cyclic = test_cyclic,
                            variance = 1,
                            degrees_of_freedom = len(uniq_bays)-2,
                            k = 1.996)
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
                                    raw_temperature = float_or_null(obs['MeasDryTemp']),
                                    raw_pressure = float_or_null(obs['MeasPressure']),
                                    raw_humidity = float_or_null(obs['MeasHumidity'])
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