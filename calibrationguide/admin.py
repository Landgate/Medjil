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
from .models import * 

@admin.register(CalibrationInstruction)
class CalibrationInstructionAdmin(admin.ModelAdmin):
    list_display = ['id','site_id', 'calibration_type', 'title','thumbnail','content','author']

@admin.register(InstructionImage)
class InstructionImageAdmin(admin.ModelAdmin):
    list_display = ['instruction', 'photos']

@admin.register(TechnicalManual)
class TechnicalManualAdmin(admin.ModelAdmin):
    list_display = ['id','manual_type', 'title','thumbnail','content','author']

@admin.register(ManualImage)
class ManualImageAdmin(admin.ModelAdmin):
    list_display = ['manual', 'photos']