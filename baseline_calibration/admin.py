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

# Register your models  here.
from .models import * 

class EDM_ObservationInline(admin.TabularInline):
    model = EDM_Observation
    extra = 0

class Level_ObservationInline(admin.TabularInline):
    model = Level_Observation
    extra = 0

admin.site.register(Certified_Distance)

class Certified_DistanceInline(admin.TabularInline):
    model = Certified_Distance
    extra = 0

class Std_Deviation_MatrixInline(admin.TabularInline):
    model = Std_Deviation_Matrix
    extra = 0

class Uncertainty_Budget_SourceInline(admin.TabularInline):
    model = Uncertainty_Budget_Source
    extra = 0


@admin.register(Pillar_Survey)
class Pillar_SurveyAdmin(admin.ModelAdmin):
    list_display = ('baseline','survey_date','job_number')
    list_filter = ('baseline','job_number',)
    fieldsets = (
              ('Documentation', {
              'fields': 
              ('baseline',
              ('survey_date','computation_date'),
              'accreditation',
              ('weather','observer'),
              'job_number',
              'fieldnotes_upload')
              }),
              ('Survey Instrumentation', {
              'fields': (
              ('edm','prism','edmi_calib_applied','mets_applied'),
              ('level','staff','staff_calib_applied'))
              }),
              ('Meterological Instrumentation', { 
              'fields':
              (('thermometer','thermo_calib_applied'),
              ('barometer','baro_calib_applied'),
              ('hygrometer','hygro_calib_applied'),
              ('psychrometer','psy_calib_applied'))
              }),
              ('Statistical parameters', { 
              'fields': (
              'uncertainty_budget',
              'outlier_criterion')
              }),
              ('Calibrated Baseline', { 
              'fields': (
              ('zero_point_correction','zpc_uncertainty'),
              'degrees_of_freedom', 'variance')
              }),
              ('Approavals', { 
              'fields': (
              ('data_entered_person','data_checked_person'),
              ('data_entered_position','data_checked_position'),
              ('data_entered_date','data_checked_date')
              )
              }))

    # inlines = [EDM_ObservationInline, Level_ObservationInline, Certified_DistanceInline,Std_Deviation_MatrixInline]
    inlines = [Certified_DistanceInline,]

@admin.register(EDM_Observation)
class EDM_ObservationAdmin(admin.ModelAdmin):
    list_display = ('pillar_survey','from_pillar','to_pillar')
    list_filter = ('pillar_survey',)
    fields = ['pillar_survey',
              ('from_pillar','to_pillar'),
              ('inst_ht','tgt_ht'),
              ('hz_direction','slope_dist'),
              'temperature',
              'wet_temp',
              'pressure',
              'humidity']


#admin.site.register(Level_Observation)
@admin.register(Level_Observation)
class Level_ObservationAdmin(admin.ModelAdmin):
    list_display = ('pillar', 'pillar_survey')


#admin.site.register(Uncertainty_Budget)
@admin.register(Uncertainty_Budget)
class Uncertainty_BudgetAdmin(admin.ModelAdmin):
    inlines = [Uncertainty_Budget_SourceInline]


admin.site.register(Uncertainty_Budget_Source)

@admin.register(Accreditation)
class AccreditationnAdmin(admin.ModelAdmin):
    list_display = ('accredited_company','valid_from_date','valid_to_date')
    list_filter = ('accredited_company',)
    fields = ['accredited_company',
              ('valid_from_date','valid_to_date'),
              ('LUM_constant','LUM_ppm'),
              'statement',
              'certificate_upload']
              
