from django.contrib import admin
from .models import RangeCalibrationRecord, RawDataModel, AdjustedDataModel, HeightDifferenceModel, BarCodeRangeParam

# Register your models here.
@admin.register(BarCodeRangeParam)
class BarCodeRangeParamAdmin(admin.ModelAdmin):
    list_display = ['site_id', 'modified_on', 'created_on']

    ordering = ['modified_on']

@admin.register(RangeCalibrationRecord)
class RangeCalibrationRecordAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'site_id', 'inst_staff', 'staff_type', 'staff_length', \
                    'inst_level', 'calibration_date', 'updated_to', 'valid']

    ordering = ['valid', 'inst_staff__staff_number', '-calibration_date']
    list_filter = ['inst_staff__staff_model']

@admin.register(RawDataModel)
class RawDataModelAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']
    # class Meta:
    #     model = RawDataModel

@admin.register(AdjustedDataModel)
class AdjustedDataModelAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']

@admin.register(HeightDifferenceModel)
class HeightDifferenceModelAdmin(admin.ModelAdmin):
    # class Meta:
    #     model = HeightDifferenceModel
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']
    # list_display = ['site_name', 'staff_number', 'observation_date', 'start_temperature','end_temperature']

# @admin.register(RangeParameters)
# class RangeParametersAdmin(admin.ModelAdmin):
#     class Meta:
#         model = RangeParameters
#     # list_display = ['Jan', 'Feb', 'Mar']