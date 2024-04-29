'''

   © 2023 Western Australian Land Information Authority

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

# Register your models here.
from accounts.admin import admin_site
from .models import * 

@admin.register(CalibrationInstruction, site=admin_site)
class CalibrationInstructionAdmin(admin.ModelAdmin):
    list_display = ['id','site_id', 'calibration_type', 'title','thumbnail','content','author']

@admin.register(InstructionImage, site=admin_site)
class InstructionImageAdmin(admin.ModelAdmin):
    list_display = ['instruction', 'photos']

@admin.register(TechnicalManual, site=admin_site)
class TechnicalManualAdmin(admin.ModelAdmin):
    list_display = ['id','manual_type', 'title','thumbnail','content','author']

@admin.register(ManualImage, site=admin_site)
class ManualImageAdmin(admin.ModelAdmin):
    list_display = ['manual', 'photos']

try:
    from accounts.sites import medjil_super_site

    @admin.register(CalibrationInstruction, site=medjil_super_site)
    class CalibrationInstructionAdmin(admin.ModelAdmin):
        list_display = ['id','site_id', 'calibration_type', 'title','thumbnail','content','author']

    @admin.register(InstructionImage, site=medjil_super_site)
    class InstructionImageAdmin(admin.ModelAdmin):
        list_display = ['instruction', 'photos']

    @admin.register(TechnicalManual, site=medjil_super_site)
    class TechnicalManualAdmin(admin.ModelAdmin):
        list_display = ['id','manual_type', 'title','thumbnail','content','author']

    @admin.register(ManualImage, site=medjil_super_site)
    class ManualImageAdmin(admin.ModelAdmin):
        list_display = ['manual', 'photos']

except:
    pass