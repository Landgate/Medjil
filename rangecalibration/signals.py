from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
import logging
import numpy as np
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

def compute_range_parameters_all():
    siteids = CalibrationSite.objects.filter(site_type='staff_range')
    for site in siteids:
        pillarList = Pillar.objects.filter(site_id = site).values_list('name')
        pillarList = np.sort(np.array([x for y in pillarList for x in y], dtype=int))
        from_to_Pillar = from_to_PillarList = {'from_to': []}
        i = 0
        while i < len(pillarList)-1:
            from_to_Pillar['from_to'].append(str(pillarList[i]) + '-' + str(pillarList[i+1]))
            i += 1
        
        paramObj, created = BarCodeRangeParam.objects.get_or_create( site_id = site, from_to =  from_to_PillarList )
        if BarCodeRangeParam.objects.filter(site_id = site).first():
            calibrationList = RangeCalibrationRecord.objects.filter(site_id = site, valid=True, updated_to = False)
        else:
            calibrationList = RangeCalibrationRecord.objects.filter(site_id = site, valid=True)

        if calibrationList:
            obsDateList = np.array(calibrationList.values_list('job_number', 'calibration_date'), dtype=object)
            all_mon_list = [[x.strftime('%b'), x.month] for x in obsDateList[:,1]]
            obsDateList = np.append(obsDateList,np.c_[all_mon_list], axis=1)
            monthList, indices  = np.unique(obsDateList[:,-1], return_index=True)
            monthText = obsDateList[indices,2]
            # print(monthList, monthText)
            thisObj = {'count': [], 
                    'mean': [], 
                    'std_dev': []
                }
            for i in range(len(monthList)):
                m_text = monthText[i]
                data = HeightDifferenceModel.objects.filter(calibration_id__calibration_date__month = monthList[i]).values_list('height_difference', flat=True)
                hdiff = [np.array(x['data'], dtype=object) for x in data]
                hdiff = np.array(hdiff, dtype=object)
                
                # Pins
                pillarList = hdiff[:,:,0][0]
                dataList = hdiff[:,:,1]  
                
                # Compute the Range Parameters
                if len(dataList) == 1:
                    for i in range(len(pillarList)):
                        diff = dataList[:,i].astype(float)[0]
                        # print(diff)
                        thisObj['count'].append(1)
                        thisObj['mean'].append('{:07.5f}'.format(diff))
                        thisObj['std_dev'].append('{:07.5f}'.format(0))
                    # print(thisObj)

                elif len(dataList) > 1: 
                    z_threshold = 1.4
                    for i in range(len(pillarList)):
                        diff = dataList[:,i].astype(float)
                        if diff.std() != 0:
                            z_score = (diff-diff.mean())/diff.std()
                            #print("Z Score: ", z_score)
                            diff = diff[abs(z_score)<z_threshold]
                            #print("Later Diff: ", diff)
                            thisObj['count'].append(len(diff))
                            thisObj['mean'].append('{:07.5f}'.format(diff.mean()))
                            thisObj['std_dev'].append('{:07.5f}'.format(diff.std()))
                        else:
                            thisObj['count'].append(len(diff))
                            thisObj['mean'].append('{:07.5f}'.format(diff.mean()))
                            thisObj['std_dev'].append('{:07.5f}'.format(diff.std()))
                # Update the Range Param Values
                BarCodeRangeParam.objects.filter( site_id = site).update(**{m_text:  thisObj} )
                # Re-initialise the cell array - else values keep appending
                thisObj = {'count': [], 
                    'mean': [], 
                    'std_dev': []
                }
            # Update RangeCalibration Update
            for obj in calibrationList:
                obj.updated_to = True
                obj.save()

def compute_range_parameters_one(siteid):
    try:
        pillarList = Pillar.objects.filter(site_id = siteid).values_list('name')
        pillarList = np.sort(np.array([x for y in pillarList for x in y], dtype=int))
        from_to_Pillar = from_to_PillarList = {'from_to': []}
        i = 0
        while i < len(pillarList)-1:
            from_to_Pillar['from_to'].append(str(pillarList[i]) + '-' + str(pillarList[i+1]))
            i += 1
        
        paramObj, created = BarCodeRangeParam.objects.get_or_create( site_id = siteid, from_to =  from_to_PillarList )
        if BarCodeRangeParam.objects.filter(site_id = siteid).first():
            calibrationList = RangeCalibrationRecord.objects.filter(site_id = siteid, valid=True, updated_to = False)
        else:
            calibrationList = RangeCalibrationRecord.objects.filter(site_id = siteid
, valid=True)
        if calibrationList:
            obsDateList = np.array(calibrationList.values_list('job_number', 'calibration_date'), dtype=object)
            all_mon_list = [[x.strftime('%b'), x.month] for x in obsDateList[:,1]]
            obsDateList = np.append(obsDateList,np.c_[all_mon_list], axis=1)
            monthList, indices  = np.unique(obsDateList[:,-1], return_index=True)
            monthText = obsDateList[indices,2]
            # print(monthList, monthText)
            thisObj = {'count': [], 
                    'mean': [], 
                    'std_dev': []
                }
            for i in range(len(monthList)):
                m_text = monthText[i]
                data = HeightDifferenceModel.objects.filter(calibration_id__calibration_date__month = monthList[i]).values_list('height_difference', flat=True)
                hdiff = [np.array(x['data'], dtype=object) for x in data]
                hdiff = np.array(hdiff, dtype=object)
                
                # Pins
                pillarList = hdiff[:,:,0][0]
                dataList = hdiff[:,:,1]  
                
                # Compute the Range Parameters
                if len(dataList) == 1:
                    for i in range(len(pillarList)):
                        diff = dataList[:,i].astype(float)[0]
                        # print(diff)
                        thisObj['count'].append(1)
                        thisObj['mean'].append('{:07.5f}'.format(diff))
                        thisObj['std_dev'].append('{:07.5f}'.format(0))
                    # print(thisObj)

                elif len(dataList) > 1: 
                    z_threshold = 1.4
                    for i in range(len(pillarList)):
                        diff = dataList[:,i].astype(float)
                        if diff.std() != 0:
                            z_score = (diff-diff.mean())/diff.std()
                            #print("Z Score: ", z_score)
                            diff = diff[abs(z_score)<z_threshold]
                            #print("Later Diff: ", diff)
                            thisObj['count'].append(len(diff))
                            thisObj['mean'].append('{:07.5f}'.format(diff.mean()))
                            thisObj['std_dev'].append('{:07.5f}'.format(diff.std()))
                        else:
                            thisObj['count'].append(len(diff))
                            thisObj['mean'].append('{:07.5f}'.format(diff.mean()))
                            thisObj['std_dev'].append('{:07.5f}'.format(diff.std()))
                # Update the Range Param Values
                BarCodeRangeParam.objects.filter( site_id = siteid).update(**{m_text:  thisObj} )
                # Re-initialise the cell array - else values keep appending
                thisObj = {'count': [], 
                    'mean': [], 
                    'std_dev': []
                }
            # Update RangeCalibration Update
            for obj in calibrationList:
                obj.updated_to = True
                obj.save()
    except:
        pass


@receiver(user_logged_in)
def post_login(sender, request, user, **kwargs):
    # if not user.username:
    #     logger.info(f'User: {user.email} logged in')
    # else:
    #     logger.info(f'User: {user.username} logged in')

    # Update the Range Calibration Param
    try:
        compute_range_parameters_all()
    except:
        pass
# @receiver(user_logged_out)
# def post_logout(sender, request, user, **kwargs):
#     if not user.username:
#         logger.info(f'User: {user.email} logged out')
#     else:
#         logger.info(f'User: {user.username} logged out')

# @receiver(user_login_failed)
# def post_login_fail(sender, credentials, request, **kwargs):
#     logger.info(f'Login failed with credentials: {credentials}')