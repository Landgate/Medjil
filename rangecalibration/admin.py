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
from django.contrib import admin
from .models import RangeCalibrationRecord, RawDataModel, AdjustedDataModel, HeightDifferenceModel, BarCodeRangeParam

from accounts.admin import admin_site

# Register your models here.
@admin.register(BarCodeRangeParam, site=admin_site)
class BarCodeRangeParamAdmin(admin.ModelAdmin):
    list_display = ['site_id', 'modified_on', 'created_on']
    ordering = ['modified_on']
# admin_site.register(BarCodeRangeParam, BarCodeRangeParamAdmin)

@admin.register(RangeCalibrationRecord, site=admin_site)
class RangeCalibrationRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_number', 'site_id', 'inst_staff', 'staff_type', 'staff_length', \
                    'inst_level', 'calibration_date', 'updated_to', 'valid']

    ordering = ['valid', 'inst_staff__staff_number', '-calibration_date']
    list_filter = ['inst_staff__staff_model_name']

@admin.register(RawDataModel, site=admin_site)
class RawDataModelAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']

@admin.register(AdjustedDataModel, site=admin_site)
class AdjustedDataModelAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']

@admin.register(HeightDifferenceModel, site=admin_site)
class HeightDifferenceModelAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']

#####################################################
try:
    from accounts.sites import medjil_super_site

    @admin.register(BarCodeRangeParam, site=medjil_super_site)
    class BarCodeRangeParamAdmin(admin.ModelAdmin):
        list_display = ['site_id', 'modified_on', 'created_on']
        ordering = ['modified_on']

    @admin.register(RangeCalibrationRecord, site=medjil_super_site)
    class RangeCalibrationRecordAdmin(admin.ModelAdmin):
        list_display = ['id', 'job_number', 'site_id', 'inst_staff', 'staff_type', 'staff_length', \
                        'inst_level', 'calibration_date', 'updated_to', 'valid']

        ordering = ['valid', 'inst_staff__staff_number', '-calibration_date']
        list_filter = ['inst_staff__staff_model_name']

    @admin.register(RawDataModel, site=medjil_super_site)
    class RawDataModelAdmin(admin.ModelAdmin):
        list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']

    @admin.register(AdjustedDataModel, site=medjil_super_site)
    class AdjustedDataModelAdmin(admin.ModelAdmin):
        list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']

    @admin.register(HeightDifferenceModel, site=medjil_super_site)
    class HeightDifferenceModelAdmin(admin.ModelAdmin):
        list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date']


except:
    pass