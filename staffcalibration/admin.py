from django.contrib import admin
from .models import StaffCalibrationRecord, AdjustedDataModel

# Register your models here.
@admin.register(StaffCalibrationRecord)
class StaffCalibrationRecordAdmin(admin.ModelAdmin):
    list_display = ['job_number','inst_staff', 'staff_type', 'staff_length', \
                    'inst_level', 'calibration_date', 'site_id']

    ordering = ['inst_staff__staff_number', '-calibration_date']
    list_filter = ['inst_staff__staff_model', 'site_id']

# @admin.register(RawDataModel)
# class RawDataModelAdmin(admin.ModelAdmin):
#     list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']

@admin.register(AdjustedDataModel)
class AdjustedDataModelAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date', 'uscale_factor', 'temp_at_sf1']
