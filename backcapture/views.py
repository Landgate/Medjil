from datetime import datetime as dt

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from calibrationsites.models import CalibrationSite, Pillar
from common_func.Convert import decrypt_file, list2dict
from instruments.models import (DigitalLevel, EDM_Inst, EDM_Specification,
                                InstrumentMake, InstrumentModel, Mets_Inst,
                                Mets_Specification, Prism_Inst,
                                Prism_Specification, Staff)
from baseline_calibration.models import (Accreditation, Certified_Distance,
                                          Pillar_Survey, Std_Deviation_Matrix,
                                          Uncertainty_Budget)
from .forms import ImportDliDataForm


def unknown_mets(mets_type, request):
    # Create the Mets of type in Medjil
    try:
        medjil_mets_model, created = InstrumentModel.objects.get_or_create(
            inst_type=mets_type, make=None, model=f'Unknown {mets_type}')
            # use unpacking to get the created flag
    except InstrumentModel.DoesNotExist:
        print(f'{mets_type} Model in Medjil not inserted')
    except Exception as e:
        print(f'Error creating {mets_type} Model: {e}')
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
            mets_number='',
            mets_custodian=None,
            comment=f'Unknown {mets_type}')
        if created:
            print(f'{mets_type} in Medjil created successfully')
    
    return this_inst


def find_pillar(baseline_id, pillar_name):
    try:
        medjil_pillar = Pillar.objects.get(site_id__pk=baseline_id, name=pillar_name)
    except Pillar.DoesNotExist:
        print(f'Pillar "{pillar_name}" for baseline {baseline_id} not found')
        return None
    
    return medjil_pillar
    
    
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
                        'StdICConstant', 'StdICPPM', 'humidity', 'ArchiveFlag',
                        'operator_address']
                rxBaseline = list2dict(decrypt_file(f), clms, 'pk')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxBaseline))
                
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

            if f.name == 'rxUncertaintyBaseline.db':
                clms = ['Description', 'Default', 'Unit']
                rxUncertaintyBaseline = list2dict(
                    decrypt_file(f), clms, 'Description')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxUncertaintyBaseline))

            if f.name == 'rxUncertaintyEDM.db':
                clms = ['Description', 'Default', 'Unit']
                rxUncertaintyEDM = list2dict(
                    decrypt_file(f), clms, 'Description')
                print(str(f.name.replace('.db','')) + ' = ' + str(rxUncertaintyEDM))
                
        Unknown_UC_budget = Uncertainty_Budget.objects.get(
                    name = 'Default', 
                    company__company_name = 'Landgate')

        try:
            medjil_level = DigitalLevel.objects.get_or_create(
                level_owner = None,
                level_number = '0000',
                level_model = None)
        except Exception as e:
            print(e)
            print('Level in Medjil not inserted')
            pass
        
        # Create dummy Barcode staff in Medjil
        try:
            medjil_staff = Staff.objects.get_or_create(
                staff_model = None,
                staff_owner = None,
                staff_number = '',
                staff_type = 'Unknown',
                staff_length = 4,
                thermal_coefficient = None)
        except Exception as e:
            print(e)
            print('Staff in Medjil not inserted')
            pass
        
        # Create the Mets gear in Medjil
        medjil_baro = unknown_mets('baro', request)
        medjil_thermo = unknown_mets('thermo', request)
        medjil_hygro = unknown_mets('hygro', request)        
                    
        # Create dummy accreditation in Medjil
        try:
            medjil_accreditation = Accreditation.objects.get_or_create(
                accredited_company = request.user.company,
                valid_from_date = '1900-01-01',
                valid_to_date = '2022-01-01',
                LUM_constant = rxStandard['F']['StandardConstant'],
                LUM_ppm = rxStandard['F']['StandardScale'],
                statement = 'Unknown accreditation from BaselineDLI backcaptured data')    
        except Exception as e:
            print(e)
            print('Accreditation not inserted')
            pass
        
        if rxJob:
            commit_errors = []
            for job in rxJob.values():
                commit_error = []
                pillars = {
                    k:v for k,v in rxPillar.items() 
                    if v.get('baseline_fk') ==  job['baseline_fk']}

                certified_dists = []
                for dist in rxDistance.values():
                    if dist['baseline_fk'] == job['baseline_fk']:
                        dist['from_pillar_order'] = int(pillars[dist['from_pillar_fk']]['order'])
                        certified_dists.append(dist)
                certified_dists = sorted(certified_dists, key=lambda x: x['from_pillar_order'])
                pillars = sorted(pillars.values(), key=lambda x: x['order'])
                
                job_measurements =(
                    [meas for meas in rxJMeasure.values() if meas['job_fk'] == job['pk']])
                
                # Find the Medjil baseline that matches
                baseline_name = rxBaseline[job['baseline_fk']]['name'].lower()
                num_pillars = len(pillars)
                if 'curtin' in baseline_name and num_pillars == 11:
                    baseline_id = CalibrationSite.objects.get(
                        site_name = 'Curtin')
                elif 'curtin' in baseline_name and num_pillars == 12:
                    baseline_id = CalibrationSite.objects.get(
                        site_name = 'Curtin 12 Pillar')
                elif 'kalgoorlie' in baseline_name:
                    baseline_id = CalibrationSite.objects.get(
                        site_name = 'Kalgoorlie')        
                elif 'busselton' in baseline_name:
                    baseline_id = CalibrationSite.objects.get(
                        site_name = 'Busselton')
                
                # Check the Names of the pillars
                for pillar in pillars:
                    if not find_pillar(baseline_id.pk, pillar['name']):
                        commit_error.append(
                            f"Pillar names in job: {job['name']} do not match {rxBaseline[job['baseline_fk']]['name']}")

                mets_applied = False
                try:
                    if job_measurements[0]['mets_flag'] == 'N': mets_applied = True
                except:
                    mets_applied = True
                
                thermo_calib_applied = all([job['ThermometerCorr1'] == '0', job['ThermometerCorr2'] == '0'])
                if mets_applied: thermo_calib_applied = True
                
                baro_calib_applied = all([job['BarometerCorr1'] == '0', job['BarometerCorr2'] == '0'])
                if mets_applied: baro_calib_applied = True
                
                # Find the EDM in BASELINE
                try:
                    edm = rxInstrument[job['instrument_edm_fk']]
                    edm_model = rxInstrumentModel[edm['InstrumentModel_fk']]
                    edm_model['type'] = 'pu'
                    if edm_model['is_pulse'] =='False': edm_model['type'] ='ph'
                    edm_make = rxInstrumentMake[edm_model['InstrumentMake_fk']]
                    if len(edm_model['manu_ref_refrac_index']) == 0:
                        edm_model['manu_ref_refrac_index'] = '999999999'
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append(
                        f'EDM specified for {job["name"]} not in BASELINE database files')
                    pass
                    
                # Create the EDM in Medjil
                try:
                    medjil_edm_make = InstrumentMake.objects.get_or_create(
                        make = edm_make['manufacturer'],
                        make_abbrev = edm_make['manufacturer'])
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('EDM Make in Medjil not inserted')
                    pass
                try:
                    medjil_edm_model = InstrumentModel.objects.get_or_create(
                        inst_type = 'edm',
                        make = medjil_edm_make[0],
                        model = edm_model['name'])
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('EDM Model in Medjil not inserted')
                    pass
                try:
                    medjil_edm_specs = EDM_Specification.objects.get_or_create(
                        edm_owner = request.user.company,
                        edm_model = medjil_edm_model[0],
                        edm_type = edm_model['type'],
                        manu_unc_const = edm_model['manu_unc_const'],
                        manu_unc_ppm = edm_model['manu_unc_ppm'],
                        manu_unc_k = 2,
                        unit_length = edm_model['unit_length'],
                        frequency = edm_model['frequency'],
                        carrier_wavelength = edm_model['carrier_wavelength'],
                        manu_ref_refrac_index = edm_model['manu_ref_refrac_index'],
                        measurement_increments = 0.0001)
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('EDM Specs in Medjil not inserted')
                    pass
                try:
                    medjil_edm = EDM_Inst.objects.get_or_create(
                        edm_number = edm['serial_number'],
                        edm_custodian = request.user,
                        comment = edm['comments'],
                        edm_specs = medjil_edm_specs[0])
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('EDM in Medjil not inserted')
                    pass
                
                # Find the Prism in BASELINE
                try:
                    prism = rxInstrument[job['instrument_prism_fk']]
                    prism_model = rxInstrumentModel[prism['InstrumentModel_fk']]
                    prism_make = rxInstrumentMake[prism_model['InstrumentMake_fk']]
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append(
                        f'Prism specified for {job["name"]} not in BASELINE database files')
                    pass
                
                # Create the Prism in Medjil
                try:
                    medjil_prism_make = InstrumentMake.objects.get_or_create(
                        make = prism_make['manufacturer'],
                        make_abbrev = prism_make['manufacturer'])
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('Prism Make in Medjil not inserted')
                    pass
                try:
                    medjil_prism_model = InstrumentModel.objects.get_or_create(
                        inst_type = 'prism',
                        make = medjil_prism_make[0],
                        model = prism_model['name'])
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('Prism Model in Medjil not inserted')
                    pass
                try:
                    medjil_prism_specs = Prism_Specification.objects.get_or_create(
                        prism_owner = request.user.company,
                        prism_model = medjil_prism_model[0],
                        manu_unc_const = prism_model['manu_unc_const'],
                        manu_unc_k = 2)
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('Prism Specs in Medjil not inserted')
                    pass
                try:
                    medjil_prism = Prism_Inst.objects.get_or_create(
                        prism_number = prism['serial_number'],
                        prism_custodian = request.user,
                        comment = prism['comments'],
                        prism_specs = medjil_prism_specs[0])
                except Exception as e:
                    commit_error.append(e)
                    commit_error.append('EDM in Medjil not inserted')
                    pass
                
                if job['calibration_type'] == 'B' and len(commit_error) == 0:                    
                    medjil_baseline_calibration = Pillar_Survey.objects.get_or_create(
                        baseline = baseline_id,
                        survey_date = dt.strptime(
                            job['survey_date'],'%d/%m/%Y').isoformat()[:10],
                        computation_date = dt.strptime(
                            job['computation_date'],'%d/%m/%Y').isoformat()[:10],
                        accreditation = medjil_accreditation[0],
                        apply_lum = False,
                        observer = job['observer_name'],
                        weather = 'Sunny/Clear',
                        job_number = rxBaseline[job['baseline_fk']]['reference'],
                        edm = medjil_edm[0],
                        prism = medjil_prism[0],
                        mets_applied = mets_applied,
                        edmi_calib_applied = True,
                        level = medjil_level[0],
                        staff = medjil_staff[0],
                        staff_calib_applied = True,
                        thermometer = medjil_thermo,
                        thermo_calib_applied = thermo_calib_applied,
                        barometer = medjil_baro,
                        baro_calib_applied = baro_calib_applied,
                        hygrometer = medjil_hygro,
                        hygro_calib_applied = True,
                        psychrometer = None,
                        psy_calib_applied = True,
                        uncertainty_budget = Unknown_UC_budget,
                        outlier_criterion = 3,
                        fieldnotes_upload = None,
                        zero_point_correction = 0,
                        zpc_uncertainty = float(rxBaselineAccuracy[job['baseline_fk']]['UncertaintyConstant'])/1000,
                        variance = 1,
                        degrees_of_freedom = int(len(job_measurements)/4) - len(pillars),
                        )

                    
                    UC_formula = rxBaselineAccuracy[job['baseline_fk']]
                    medjil_cert_dist = Certified_Distance.objects.get_or_create(
                        pillar_survey = medjil_baseline_calibration[0],
                        from_pillar = find_pillar(
                            baseline_id.pk,
                            pillars[0]['name']),
                        to_pillar = find_pillar(
                            baseline_id.pk,
                            pillars[0]['name']),
                        distance = 0,
                        a_uncertainty = 0,
                        combined_uncertainty = float(UC_formula['UncertaintyConstant']) * 0.001,
                        offset = 0,
                        os_uncertainty = 0,
                        reduced_level = float(pillars[0]['height']),
                        rl_uncertainty = 0
                        )
                    
                    from_p0_dist = {pillars[0]['name']:0}
                    for d in certified_dists:
                        p0_name = pillars[0]['name']
                        p1_name = rxPillar[d['from_pillar_fk']]['name']
                        p2_name = rxPillar[d['to_pillar_fk']]['name']
                        if p0_name == p1_name:
                            t_dist = float(d['certified_distance'])
                        else:
                            t_dist = float(d['certified_distance']) + t_dist
                        from_p0_dist[p2_name] = t_dist
                        combined_uc = (float(UC_formula['UncertaintyScale'])*10**-6 * t_dist
                                       + float(UC_formula['UncertaintyConstant']) * 0.001)
                        
                        medjil_cert_dist = Certified_Distance.objects.get_or_create(
                            pillar_survey = medjil_baseline_calibration[0],
                            from_pillar = find_pillar(
                                baseline_id.pk,
                                p0_name),
                            to_pillar = find_pillar(
                                baseline_id.pk,
                                p2_name),
                            distance = t_dist,
                            a_uncertainty = float(d['DistSigma']),
                            combined_uncertainty = combined_uc,
                            offset = float(
                                rxPillar[d['to_pillar_fk']]['offset']),
                            os_uncertainty = float(
                                rxUncertaintyBaseline['Pillar offset']['Default']) / 1000,
                            reduced_level = float(
                                rxPillar[d['to_pillar_fk']]['height']),
                            rl_uncertainty = float(
                                rxPillar[d['to_pillar_fk']]['HtStdDev'])
                            )
                    
                    # BASELINE WA used a linear formula to assign standard deviations
                    # to the certified distances. Medjil stores the full vcv by
                    # recording standard deviations of all from and to pillar combinations
                    for i, p1 in enumerate(pillars[:-1]):
                        for p2 in pillars[i+1:]:
                            p1_p2_dist = (from_p0_dist[p2['name']] - 
                                          from_p0_dist[p1['name']])
                            uc = (float(UC_formula['UncertaintyScale']) * p1_p2_dist
                                  + float(UC_formula['UncertaintyConstant']) * 0.001)
                            medjil_sdev_mtx = (
                                Std_Deviation_Matrix.objects.get_or_create(
                                    pillar_survey = medjil_baseline_calibration[0],
                                    from_pillar = find_pillar(
                                        baseline_id.pk,
                                        p1['name']),
                                    to_pillar = find_pillar(
                                        baseline_id.pk,
                                        p2['name']),
                                    std_uncertainty = uc
                                    ))
                commit_errors.append(commit_error)
    context ={
        'Header': 'Import BaselineDLI Database Records',
        'form': importForm}
    
    return render(request, 'baseline_calibration/Accreditation_form.html', context)