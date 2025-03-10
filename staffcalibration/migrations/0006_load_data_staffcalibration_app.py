# Generated by Django 4.1.9 on 2024-05-29 06:09

import os
import json
import numpy as np
from datetime import date, datetime
from math import sqrt, isnan
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError
from django.db import IntegrityError
from django.conf import settings
import common_func.validators
from django.db import migrations, models

# Preprocess staff readings to calculate the height differences between pins
def preprocess_reading(dataset):
    obs_set = []
    for i in range(len(dataset)-1):
        pini, obsi, nmeasi, stdi = dataset[i] 
        pinj, obsj, nmeasj, stdj = dataset[i+1]
        if float(stdi) == 0:
            stdi = 10**-5
        if float(stdj) == 0:
            stdj = 10**-5
        dMeasuredLength = float(obsj)- float(obsi)
        dStdDeviation = sqrt(float(stdi)**2 + float(stdj)**2)
        obs_set.append([str(int(pini))+'-'+str(int(pinj)), 
                            '{:.5f}'.format(float(obsi)), '{:.5f}'.format(float(obsj)), 
                            '{:.5f}'.format(dMeasuredLength), 
                            '{:.7f}'.format(dStdDeviation)])
    return np.array(obs_set, dtype=object)

# Calculate the correction factor
def compute_correction_factor(newdataset, refdataset, coef, ave_temp, std_temp):

    W = np.zeros([len(newdataset[:,0])])
    W_corr = np.zeros([len(newdataset[:,0])])
    A = np.ones([len(newdataset[:,0])])
    sum_sq_diff = np.zeros([len(newdataset[:,0])])
    variance = np.zeros([len(newdataset[:,0])])
    
    adj_correction = []
    for i in range (len(newdataset)):
        pin, frm, to, diff, std = newdataset[i]
        diff = float(diff)
        ref_diff = float(refdataset[i,1])
        
        corr_diff = diff * (((ave_temp-std_temp)*coef)+1) # correction at standard temperature
        corr = ref_diff - corr_diff
        # print(diff, ref_diff, corr_diff, corr, coef, ave_temp, std_temp)
        # Append array
        sum_sq_diff[i,] = corr**2
        variance[i,] = float(std)

        W[i,] = ref_diff/diff                   # Uncorrected
        W_corr[i,] = ref_diff/corr_diff         # Corrected for temp

        adj_correction.append([pin, frm, to, '{:.5f}'.format(ref_diff), '{:.5f}'.format(diff),'{:.5f}'.format(corr)])
    # Compute Lease Squares Solution
    P = np.diag(1/variance**2)
    sf_0 = (np.matmul(np.transpose(A), np.matmul(P, W)))/(np.matmul(np.transpose(A), np.matmul(P, A)))
    sf_1 = (np.matmul(np.transpose(A), np.matmul(P, W_corr)))/(np.matmul(np.transpose(A), np.matmul(P, A))) # at 25degC
    
    grad_uncertainty = sqrt(np.sum(sum_sq_diff)/(len(W)-1))*1.96

    adj_correction = {'headers': ['PIN','FROM','TO', 'REFERENCE', 'MEASURED', 'CORRECTIONS'], 
                        'data': adj_correction}
    return round(sf_0,8), round(sf_1,7), round(grad_uncertainty,5), adj_correction
###############################################################
def load_data(apps, schema_editor):  
    Location = apps.get_model('accounts', 'Location')
    Company = apps.get_model('accounts', 'Company')
    User = apps.get_model('accounts', 'CustomUser')
    CalibrationSite = apps.get_model("calibrationsites", "CalibrationSite")
    Staff = apps.get_model("instruments", "Staff")
    DigitalLevel = apps.get_model("instruments", "DigitalLevel")
    StaffCalibrationRecord = apps.get_model("staffcalibration", "StaffCalibrationRecord")
    StaffAdjustedDataModel = apps.get_model("staffcalibration", "AdjustedDataModel")
    RangeCalibrationRecord = apps.get_model('rangecalibration', 'RangeCalibrationRecord')

    # Starting to read the files
    jsonfile = os.path.join(settings.STATIC_ROOT, 'data/InitialData/StaffApp/db.json')
    staff_types = {
        'invar': 'Invar',
        'fiberglass': 'Fibreglass',
        'wood': 'Wood',
        'aluminium': 'Aluminium',
        'steel': 'Steel',
        'epoxy': 'Carbon/epoxy',
        'e_glass': 'E-glass',
        's2_glass': 'S2-glass',
    }

    if os.path.exists(jsonfile):
        with open(jsonfile) as f:
            data = json.load(f)
            #########################################################
            # 1. Read Company | Also Read Staff_Types
            AuthorityTable = []; StaffTypes = []
            for i in range(len(data)):
                pk = data[i]['pk']
                field = data[i]['fields']

                if 'accounts.authority' == data[i]['model']:
                    AuthorityTable.append([pk, field['authority_name'], field['authority_abbrev']])
                if 'staffs.stafftype' == data[i]['model']:
                    StaffTypes.append([pk, field['staff_type'], field['thermal_coefficient'], field['added_on'], field['updated_on']])
            AuthorityTable = np.array(AuthorityTable, dtype=object)
            StaffTypes = np.array(StaffTypes, dtype=object)
            #########################################################
            # 2. Users
            StaffUsers = []
            for i in range(len(data)):
                pk = data[i]['pk']
                field = data[i]['fields']
                if 'accounts.customuser' == data[i]['model']:
                    authority = AuthorityTable[AuthorityTable[:,0] == field['authority']][0]
                    try: 
                        # Create Company
                        com_obj, created = Company.objects.get_or_create(
                                company_name = authority[1], 
                                company_abbrev = authority[2]
                        )
                        location_obj = Location.objects.filter(statecode  = 'WA')
                        # Create Object
                        user_obj, created = User.objects.get_or_create(
                            email = field['email'],
                            password = field['password'],
                            first_name = field['first_name'], 
                            last_name = field['last_name'],
                            company = com_obj,
                            is_staff = field['is_staff'],
                            is_superuser = field['is_superuser'],
                            is_active = field['is_active'],
                            date_joined = field['date_joined'],
                            last_login = field['last_login'],
                        )
                        user_obj.locations.set(location_obj)
                        user_obj.save()
                    except IntegrityError:
                        pass
                    StaffUsers.append([pk, field['email'], authority[1]])
            StaffUsers = np.array(StaffUsers, dtype=object)
            #########################################################
            # 3. Levels | Staves | Range Calibration Data | Staff Calibration Data
            LevelList = []; StaffList = []
            URangeCalibID = []; URangeAdjData = []
            UStaffCalibID = []; UStaffRawData = []
            UStaffCalibData = []
            for i in range(len(data)):
                pk = data[i]['pk']
                field = data[i]['fields']
                if 'staffs.digitallevel' == data[i]['model']:
                    level_owner = Company.objects.get(company_name = StaffUsers[StaffUsers[:,0]==field['user']][0][2])
                    level_custodian = User.objects.get(email = StaffUsers[StaffUsers[:,0]==field['user']][0][1])
                    if not DigitalLevel.objects.filter(level_owner = level_owner, level_number = field['level_number']).exists():
                        DigitalLevel.objects.get_or_create(
                                level_owner = level_owner,
                                level_custodian = level_custodian,
                                level_make_name = field['level_make'].upper(),
                                level_model_name = field['level_model'].upper(),
                                level_number = field['level_number']                
                                )
                    LevelList.append({'pk': pk, 'level_custodian': level_custodian, 'level_number' :field['level_number']})
                if 'staffs.staff' == data[i]['model']:
                    staff_type1 = None
                    staff_owner = Company.objects.get(company_name = StaffUsers[StaffUsers[:,0]==field['user']][0][2])
                    staff_custodian = User.objects.get(email = StaffUsers[StaffUsers[:,0]==field['user']][0][1])
                    staff_type = StaffTypes[StaffTypes[:,0]==field['staff_type']][0][1]
                    for key, value in staff_types.items():
                        if staff_type == value:
                            staff_type1 = key
                            break
                    thermal_coefficient = StaffTypes[StaffTypes[:,0]==field['staff_type']][0][2]
                    if field['correction_factor']:
                        iscalibrated = True
                        calibration_date = field['calibration_date']
                        scale_factor = field['correction_factor']
                    else:
                        iscalibrated = False
                        calibration_date = ''
                        scale_factor = ''
                    if not Staff.objects.filter(staff_owner = staff_owner, staff_number = field['staff_number']).exists():
                        Staff.objects.get_or_create(
                                staff_owner = staff_owner,
                                staff_custodian = staff_custodian,
                                staff_number = field['staff_number'],
                                staff_type = staff_type1,
                                staff_length = field['staff_length'],
                                thermal_coefficient = thermal_coefficient,
                                iscalibrated = iscalibrated,             
                                )
                    StaffList.append({'pk': pk, 'staff_custodian': staff_custodian, 'staff_number' :field['staff_number']})
                if 'range_calibration.heightdifferencemodel' == data[i]['model']:
                    unique_index = field['update_index']
                    if not unique_index in URangeCalibID:
                        URangeCalibID.append(unique_index)

                        URangeAdjData.append( {
                                'job_number': unique_index,
                                'site_id': 1,
                                'staff_number': unique_index.split('-', maxsplit=1)[1],
                                'calibration_date': datetime.fromisoformat(field['observation_date']).date(),
                                'adjusted_data': np.empty((0, 2), object)
                                })
                if 'staff_calibration.urawdatamodel' == data[i]['model']:
                    unique_index = field['update_index']
                    staff_user = User.objects.get(email = StaffUsers[StaffUsers[:,0]==field['user']][0][1])
                    calibration_date = datetime.fromisoformat(field['calibration_date']).date()
                    if not unique_index in UStaffCalibID:
                        UStaffCalibID.append(unique_index)
                        UStaffRawData.append({
                                'job_number': unique_index,
                                'site_id': 1,
                                'staff_number': field['staff_number'],
                                'staff_user': staff_user,
                                'calibration_date': calibration_date,
                                'staff_reading': np.empty((0, 4), object)
                                })
                if 'staff_calibration.ucalibrationupdate' == data[i]['model']:
                    UStaffCalibData.append({
                        'site_name': 'Boya',
                        'job_number': pk, 
                        'inst_staff' : field['staff_number'],
                        'staff_user' : field['user'],
                        'inst_level' : field['level_number'],
                        'calibration_date' : datetime.fromisoformat(field['calibration_date']).date(),
                        'created_on' : field['submission_date'],
                        'modified_on' : datetime.now(),
                        'observer' : field['observer'],
                        'scale_factor' : field['correction_factor'],
                        'observed_temperature' : field['observed_temperature'],
                        'standard_temperature' : field['correction_factor_temperature'] 
                    })
            ####################################################
            # Read Range Data and Save it
            ####################################################
            for i, uindex in enumerate(URangeAdjData):
                index = URangeAdjData[i]['job_number']
                for j in range(len(data)):
                    field = data[j]['fields']
                    if 'range_calibration.heightdifferencemodel' == data[j]['model']:
                        unique_index = field['update_index']
                        tmp0 = [ field['pin'], field['adjusted_ht_diff'] ]
                        if unique_index == index:
                            URangeAdjData[i]['adjusted_data'] = np.vstack([URangeAdjData[i]['adjusted_data'], tmp0])
            # Process Average Range
            p_list = ['1-2','2-3','3-4','4-5','5-6','6-7','7-8','8-9','9-10','10-11','11-12','12-13','13-14','14-15','15-16','16-17','17-18','18-19','19-20','20-21']
            dateList = []; refData = []
            for i, dat in enumerate(URangeAdjData):
                dateList.append(dat['calibration_date'])
                refData.append(dat['adjusted_data'][:,:2])
            dateList = np.array(dateList, dtype=object).reshape(-1,1)

            monthList = np.array([[x.strftime('%b'), x.month] for x in dateList[:,0]], dtype = object)
            dateList = np.append(dateList,np.c_[monthList], axis=1)

            monthNoList, indices, nCounts  = np.unique(monthList[:,1], return_index=True, return_counts=True)

            ReferenceData_MonList = []
            for mon in monthNoList:
                monthText = datetime(1900, int(mon), 1 ).strftime('%b')
                # n_count = nCounts[i]
                ind = np.where(dateList[:,-1] == mon)[0]
                reference = [refData[i] for i in ind]
                ncounts = len(reference)
                
                RefData_PinList = []
                for p in p_list:
                    dat_mean = None
                    if ncounts <= 2:
                        dat = []
                        for tmp in reference:
                            ind2 = np.where(tmp[:,0] == p)[0]
                            dat.append([tmp[j][1] for j in ind2][0])
                        dat_mean = np.array(dat, dtype=float).mean()
                        RefData_PinList.append([p, float("{:.5f}".format(dat_mean))])
                    elif ncounts > 2:
                        dat = []
                        for tmp in reference:
                            ind2 = np.where(tmp[:,0] == p)[0]
                            dat.append([tmp[j][1] for j in ind2][0])
                        dat = np.array(dat, dtype=float)    
                        mdat = dat.mean()
                        mad = np.sum(abs(dat-mdat))/len(dat)
                        if mad == 0:
                            dat_mean = dat.mean()
                        else:
                            madev = 0.6745*(abs(dat-mdat))/mad
                            ind = madev.argsort()[:2]
                            dat_mean = dat[ind].mean()
                        RefData_PinList.append([p, float("{:.5f}".format(dat_mean))])

                ReferenceData_MonList.append(
                            {
                            'Month': monthText,
                            'adjusted_data': np.array(RefData_PinList, dtype=object)
                            })
                # print(ReferenceData_MonList)
            ####################################################
            # Read Staff Calibration Raw Data and Save it
            ####################################################
            for i, uindex in enumerate(UStaffRawData):
                index = UStaffRawData[i]['job_number']
                for j in range(len(data)):
                    field = data[j]['fields']
                    if 'staff_calibration.urawdatamodel' == data[j]['model']:
                        unique_index = field['update_index']
                        tmp0 = [int(field['pin_number']), float(field['staff_reading']), int(field['number_of_readings']), float(field['standard_deviations'])],
                        if unique_index == index:
                            UStaffRawData[i]['staff_reading'] = np.vstack([UStaffRawData[i]['staff_reading'], tmp0])
            ######################################################
            # Calibrate & Update the Staff Calirbation Record
            k = 0
            LgStaffList = [209,210,212,213,214,222,26296,26909,27690,79918]
            for i, idata in enumerate(UStaffRawData):
                # Initialise
                staff_number = None; average_temperature = None; standard_tempearture = None
                scale_factor = None; staff_length = None; thermal_coefficient = None
                observer = None
                inst_level = None
                # Get params
                dataIndex = idata['job_number']
                calibration_date = idata['calibration_date']
                calibMonText = calibration_date.strftime('%b')
                inst_staff = Staff.objects.filter(staff_number = idata['staff_number']).first()

                # Get staff parameters
                if inst_staff:
                    staff_number = inst_staff.staff_number
                    staff_length = inst_staff.staff_length
                    staff_owner = inst_staff.staff_owner
                    thermal_coefficient = inst_staff.thermal_coefficient*10**-6
                    # Get metadata from calibration record
                    for met in UStaffCalibData:
                        refIndex = met['job_number']
                        if refIndex == dataIndex:
                            average_temperature = met['observed_temperature']
                            standard_temperature = met['standard_temperature']
                            scale_factor = met['scale_factor']
                            observer = met['observer'].split(',')[-1] + ' ' + met['observer'].split(',')[0]
                            # Get level 
                            for level in LevelList:
                                if level['pk'] == met['inst_level']:
                                    inst_level = DigitalLevel.objects.filter(level_number=level['level_number']).first()                                  
                    #########################################
                    # get data and calibrate
                    obs_data = idata['staff_reading']
                    if len(obs_data) < 21 and len(obs_data >= 13):
                        for ref in ReferenceData_MonList:
                            if ref['Month'] == calibMonText:
                                ref_data = ref['adjusted_data']
                                break
                        new_obs_data = preprocess_reading(obs_data)
                        
                        common_pins, data_ind, ref_ind = np.intersect1d(new_obs_data[:,0], ref_data[:,0], return_indices=True)
                        new_obs_data = new_obs_data[np.sort(data_ind), :]                            # Extract & sort data
                        ref_data = ref_data[np.sort(ref_ind),:]                              # Extract & sort reference 
                    
                        if average_temperature and thermal_coefficient and scale_factor and len(common_pins) > 0:
                            k +=1
                            scaleFactor0, scaleFactor1, grad_uncertainty, diff_correction = compute_correction_factor(new_obs_data, 
                                                                                                                    ref_data, 
                                                                                                                    thermal_coefficient, 
                                                                                                                    average_temperature,
                                                                                                                    standard_temperature)
                            if not isnan(scaleFactor0):
                                temp_at_sf1 = '{:.1f}'.format(((1/scaleFactor0)-1)/(thermal_coefficient)+average_temperature)
                                data_adj = np.array(diff_correction['data'], dtype=object)
                                # Update Staff CalibrationRecord
                                if 'Landgate' not in staff_owner.company_name and staff_number not in LgStaffList:
                                    try:
                                        calib_obj, created = StaffCalibrationRecord.objects.get_or_create(
                                                job_number = dataIndex[:4]+dataIndex.split('-', maxsplit=1)[1][:4],
                                                site_id = CalibrationSite.objects.filter(site_name = 'Boya').first(),
                                                inst_staff = inst_staff,
                                                inst_level = inst_level,
                                                scale_factor = scaleFactor1,
                                                grad_uncertainty = grad_uncertainty,
                                                observed_temperature = average_temperature,
                                                observer = observer,
                                                calibration_date = calibration_date
                                        )
                                        # Update Staff AdjustedData Model
                                        if created:
                                            calib_adj, created = StaffAdjustedDataModel.objects.update_or_create(
                                                calibration_id = calib_obj,
                                                uscale_factor = scaleFactor0,
                                                temp_at_sf1 = temp_at_sf1,
                                                staff_reading = {
                                                            'pin': data_adj[:,0].tolist(),
                                                            'from': data_adj[:,1].tolist(),
                                                            'to': data_adj[:,2].tolist(),
                                                            'reference': data_adj[:,3].tolist(),
                                                            'measured': data_adj[:,4].tolist(),
                                                            'correction': data_adj[:,5].tolist(),
                                                })
                                    except IntegrityError:
                                        pass
                        else:
                            pass
                            #print('Cannot be computed!')

    else:
        print("Files Not found")
def reverse_func(apps, schema_editor):
    Company = apps.get_model('accounts', 'Company')
    User = apps.get_model('accounts', 'CustomUser')
    k = 0 
    # Delete users
    staff_company = []; 
    for u in User.objects.filter(is_superuser=True, is_staff=True):
        if u.company and u.company.company_name not in staff_company:
                staff_company.append(u.company.company_name)
    # other_company = []
    for u in User.objects.filter(is_superuser=False, is_staff=False):
        k =+1
        try:
            u.delete()
        except ObjectDoesNotExist:
            pass
            # print('Cannot delete ', k, u)
    for c in Company.objects.all():
        if c.company_name not in staff_company:
            try:
                c.delete()
            except ProtectedError:
                pass
                # print(c.company_name, ' cannot be deleted!')
            

class Migration(migrations.Migration):

    dependencies = [
        ("staffcalibration", "0005_alter_staffcalibrationrecord_field_book_and_more"),
    ]

    operations = [
            migrations.RunPython(load_data, reverse_func),
    ]
