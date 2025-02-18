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
from .models import StaffCalibrationRecord, AdjustedDataModel

from accounts.admin import admin_site
# Register your models here.
@admin.register(StaffCalibrationRecord, site=admin_site)
class StaffCalibrationRecordAdmin(admin.ModelAdmin):
    list_display = ['job_number','inst_staff', 'staff_length', \
                    'inst_level', 'scale_factor', 'calibration_date', 'site_id']

    ordering = ['inst_staff__staff_number', '-calibration_date']
    list_filter = ['inst_staff__staff_model_name', 'site_id']

@admin.register(AdjustedDataModel, site=admin_site)
class AdjustedDataModelAdmin(admin.ModelAdmin):
    list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date', 'uscale_factor', 'temp_at_sf1']

#####################################################
try:
    from accounts.sites import medjil_super_site

    @admin.register(StaffCalibrationRecord, site=medjil_super_site)
    class StaffCalibrationRecordAdmin(admin.ModelAdmin):
        list_display = ['job_number','inst_staff', 'staff_type', 'staff_length', \
                        'inst_level', 'calibration_date', 'site_id']

        ordering = ['-calibration_date', 'inst_staff__staff_number']
        list_filter = ['inst_staff__staff_model_name', 'site_id']

    @admin.register(AdjustedDataModel, site=medjil_super_site)
    class AdjustedDataModelAdmin(admin.ModelAdmin):
        list_display = ['job_number', 'calibration_id', 'staff_number','staff_type','staff_length','level_number','calibration_date', 'uscale_factor', 'temp_at_sf1']

except:
    pass