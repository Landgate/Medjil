from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
import logging
import numpy as np
from datetime import datetime
# import models
from calibrationsites.models import (CalibrationSite,
                                     Pillar
                                    )
from .models import (
    BarCodeRangeParam,
    RangeCalibrationRecord,
    HeightDifferenceModel
)

logger = logging.getLogger('django')

    
# Update
def update_range_table(range_obj, from_to_pillar, month_number):
    ''' 
    calibration_list: contains list of range calibrations extracted as model objects via filter
    from_to_pillar: List of pillars as from_to in a dictionary format
    range_obj: RangeParam Table
    '''
    # Declare a param object to store the range parameters
    paramObj = {'count': [], 
                'mean': [], 
                'std_dev': []
                }
    # height differences
    month_dato = HeightDifferenceModel.objects.filter(calibration_id__calibration_date__month = month_number, 
                                                        calibration_id__valid = True).values_list('height_difference', flat=True)
    # Month number (month_number) to e.g., 'Jan', 'Feb' .... so on
    monthText = datetime(1900, int(month_number), 1 ).strftime('%b')
    
    # Compute the mean and standard deviations for all the pillar ranges (e.g., 1-2, 2-3, so on)
    hdiff = [np.array(x['data'], dtype=object) for x in month_dato]
    hdiff = np.array(hdiff, dtype=object)
    i = 0
    for from_to in from_to_pillar['from_to']:
        i += 1
        try:
            match_from_to = hdiff[hdiff[:,:,0]==from_to]
        except:
            match_from_to = []
            paramObj['count'].append(0)
            paramObj['mean'].append(np.nan)
            paramObj['std_dev'].append(np.nan)
        # if data length is more than or equal to one, perform the following:
        if len(match_from_to) == 1: 
            dato = np.array(match_from_to[:,1:3], dtype=float)
            paramObj['count'].append(1)
            paramObj['mean'].append('{:07.5f}'.format(dato[0]))
            paramObj['std_dev'].append('{:04.3f}'.format(dato[2]))
        elif len(match_from_to) == 2: 
            dato = np.array(match_from_to[:,1:3], dtype=float)
            percent_change = (dato[:,0][0]-dato[:,0][1])/dato[:,0][1]*100
            if abs(percent_change) < 1.:
                paramObj['count'].append(len(dato))
                paramObj['mean'].append('{:07.5f}'.format(dato[:, 0].mean()))
                paramObj['std_dev'].append('{:04.3f}'.format(dato[:,1].mean()))
            else:
                paramObj['count'].append(1)
                paramObj['mean'].append('{:07.5f}'.format(dato[:,0][1]))
                paramObj['std_dev'].append('{:04.3f}'.format(dato[:,1][1]))
        else:
            z_threshold = 1.4
            dato = np.array(match_from_to[:,1:3], dtype=float)
            
            if dato[:,0].std() != 0:
                z_score = (dato[:,0]-dato[:,0].mean())/dato[:,0].std()
                # print("Z Score: ", z_score)
                dato1 = dato[abs(z_score)<z_threshold]
                paramObj['count'].append(len(dato1))
                paramObj['mean'].append('{:07.5f}'.format(dato1[:,0].mean()))
                paramObj['std_dev'].append('{:04.3f}'.format(dato1[:,1].mean()))
            else:
                paramObj['count'].append(len(dato))
                paramObj['mean'].append('{:07.5f}'.format(dato[:,0].mean()))
                paramObj['std_dev'].append('{:04.3f}'.format(dato[:,1].mean()))
    # Update the Range Param Values
    range_obj.update(**{monthText:  paramObj} )

# Create Range Param Database if Range Param DoesNot Exists on Login (Staff)
def compute_range_parameters():
    # Get the site ids for staff range
    siteids = CalibrationSite.objects.filter(site_type='staff_range')
    # Update range for all the sites
    for site in siteids:
        # Get the pillars
        pillarList = Pillar.objects.filter(site_id = site).values_list('name')
        pillarList = np.sort(np.array([x for y in pillarList for x in y], dtype=int))
        from_to_pillar = {'from_to': []}
        i = 0
        while i < len(pillarList)-1:
            from_to_pillar['from_to'].append(str(pillarList[i]) + '-' + str(pillarList[i+1]))
            i += 1
        
        CalibrationList = None
        # If BarCodeRangeParam table does not exists 
        if not BarCodeRangeParam.objects.filter(site_id=site).exists():                                                
            obj, created = BarCodeRangeParam.objects.get_or_create(site_id = site, from_to =  from_to_pillar)
            rangeObj = BarCodeRangeParam.objects.filter(site_id = obj.site_id)
            CalibrationList = RangeCalibrationRecord.objects.filter(site_id = site, valid=True)
        # if table exists but range needs to be updated - updated_to=False in RangeCalibrationRecord table
        elif RangeCalibrationRecord.objects.filter(site_id = site, valid=True, updated_to = False).exists():  
            rangeObj = BarCodeRangeParam.objects.filter(site_id = site)
            CalibrationList = RangeCalibrationRecord.objects.filter(site_id = site, valid=True, updated_to = False)

        if CalibrationList:
            # get the dates and months list
            obsDateList = np.array(CalibrationList.values_list('job_number', 'calibration_date'), dtype=object)
            allMonList = [[x.strftime('%b'), x.month] for x in obsDateList[:,1]]
            updatedObsDateList = np.append(obsDateList,np.c_[allMonList], axis=1)
            monthNoList, ind  = np.unique(updatedObsDateList[:,-1], return_index=True)

            # for each month in a year, loop to height differences and calculate the range parameters        
            for m_no in monthNoList:
                update_range_table(rangeObj, from_to_pillar, m_no)
                # print('Successfully updated for month_number: ', m_no)
            for obj2 in CalibrationList:
                obj2.updated_to = True
                obj2.save()

def update_range_table_current(calib_id):
    # Get Pillar Site from Calibration Site
    if Pillar.objects.filter(site_id = calib_id.site_id).first():
        pillarList = Pillar.objects.filter(site_id = calib_id.site_id).values_list('name')
        pillarList = np.sort(np.array([x for y in pillarList for x in y], dtype=int))
        from_to_pillar = {'from_to': []}
        i = 0
        while i < len(pillarList)-1:
            from_to_pillar['from_to'].append(str(pillarList[i]) + '-' + str(pillarList[i+1]))
            i += 1
    else:
        print('No calibrate sites or pillar exists for this calibration. Please check the CalibrationSites.')

    current_month_no = int(calib_id.calibration_date.strftime('%m'))

    if BarCodeRangeParam.objects.filter(site_id = calib_id.site_id).exists(): 
         rangeObj = BarCodeRangeParam.objects.filter(site_id = calib_id.site_id)
         update_range_table(rangeObj, from_to_pillar, current_month_no)
        #  print('Successfully updated for month_number: ', current_month_no)
    else:
        obj, created = BarCodeRangeParam.objects.get_or_create(site_id = calib_id.site_id, from_to = from_to_pillar)
        rangeObj = BarCodeRangeParam.objects.filter(site_id = obj.site_id)

        CalibrationList = RangeCalibrationRecord.objects.filter(site_id = calib_id.site_id, valid=True)

        if CalibrationList.first():
            # get the dates and months list
            obsDateList = np.array(CalibrationList.values_list('job_number', 'calibration_date'), dtype=object)
            allMonList = [[x.strftime('%b'), x.month] for x in obsDateList[:,1]]
            updatedObsDateList = np.append(obsDateList,np.c_[allMonList], axis=1)
            monthNoList, ind  = np.unique(updatedObsDateList[:,-1], return_index=True)

            # for each month in a year, loop to height differences and calculate the range parameters        
            for m_no in monthNoList:
                update_range_table(rangeObj, from_to_pillar, m_no)
                # print('Successfully updated for month_number: ', m_no)
            for obj2 in CalibrationList:
                obj2.updated_to = True
                obj2.save()

@receiver(user_logged_in)
def post_login(sender, request, user, **kwargs):
    if not user.username:
        logger.info(f'User: {user.email} logged in')
    else:
        logger.info(f'User: {user.username} logged in')
    
# @receiver(user_logged_out)
# def post_logout(sender, request, user, **kwargs):
#     if not user.username:
#         logger.info(f'User: {user.email} logged out')
#     else:
#         logger.info(f'User: {user.username} logged out')

# @receiver(user_login_failed)
# def post_login_fail(sender, credentials, request, **kwargs):
#     logger.info(f'Login failed with credentials: {credentials}')