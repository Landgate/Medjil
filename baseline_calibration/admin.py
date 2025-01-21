'''

   © 2024 Western Australian Land Information Authority

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
from accounts.admin import admin_site
from .models import * 

class EDM_ObservationInline(admin.TabularInline):
    model = EDM_Observation
    extra = 0

class Level_ObservationInline(admin.TabularInline):
    model = Level_Observation
    extra = 0

@admin.register(Certified_Distance, site=admin_site)
class CertifiedDistanceAdmin(admin.ModelAdmin):
    list_display = ['pillar_survey', 'from_pillar', 'to_pillar', 'distance']

class Certified_DistanceInline(admin.TabularInline):
    model = Certified_Distance
    extra = 0

class Std_Deviation_MatrixInline(admin.TabularInline):
    model = Std_Deviation_Matrix
    extra = 0

class Uncertainty_Budget_SourceInline(admin.TabularInline):
    model = Uncertainty_Budget_Source
    extra = 0


@admin.register(Pillar_Survey, site=admin_site)
class Pillar_SurveyAdmin(admin.ModelAdmin):
    list_display = ('baseline','survey_date','job_number','comment')
    list_filter = ('baseline','job_number',)
    search_fields = ['pillar_survey__baseline__site_name']
    fieldsets = (
        ('Documentation', {
        'fields': 
        ('baseline',
        ('survey_date','computation_date'),
        ('accreditation','apply_lum'),
        ('weather','observer'),
        'job_number',
        'comment',
        'fieldnotes_upload')
        }),
        ('Survey Instrumentation', {
        'fields': (
        ('edm','prism','edmi_calib_applied','mets_applied'),
        'co2_content',
        ('level','staff','staff_calib_applied'))
        }),
        ('Meterological Instrumentation', { 
        'fields':
        (('thermometer','thermo_calib_applied'),
        ('barometer','baro_calib_applied'),
        ('hygrometer','hygro_calib_applied'),
        ('thermometer2','thermo2_calib_applied'),
        ('barometer2','baro2_calib_applied'),
        ('hygrometer2','hygro2_calib_applied'),
        ('psychrometer','psy_calib_applied'))
        }),
        ('Statistical parameters', { 
        'fields': (
        'uncertainty_budget',
        'outlier_criterion')
        }),
    )

    # inlines = [EDM_ObservationInline, Level_ObservationInline, Certified_DistanceInline,Std_Deviation_MatrixInline]
    inlines = [Certified_DistanceInline,]


@admin.register(PillarSurveyResults, site=admin_site)
class PillarSurveyResultsAdmin(admin.ModelAdmin):
    list_display = ['pillar_survey', 'status', 'uploaded_on', 'modified_on']
    list_filter = ['status']
    # search_fields = ['pillar_survey__baseline__site_name']

    fieldsets = (
              ('Statistical parameters', { 
              'fields': (
              'uncertainty_budget',
              'outlier_criterion')
              }),
              ('Calibrated Baseline', { 
              'fields': (
              ('zero_point_correction','zpc_uncertainty'),
              ('degrees_of_freedom', 'experimental_std_dev'),
              'html_report')
              }),
              ('Approavals', { 
              'fields': (
              ('data_entered_person','data_checked_person'),
              ('data_entered_position','data_checked_position'),
              ('data_entered_date','data_checked_date')
              )
              }))


@admin.register(EDM_Observation, site=admin_site)
class EDM_ObservationAdmin(admin.ModelAdmin):
    list_display = ('pillar_survey','from_pillar','to_pillar')
    list_filter = ('pillar_survey',)
    fields = ['pillar_survey',
              ('from_pillar','to_pillar'),
              ('inst_ht','tgt_ht'),
              ('hz_direction','raw_slope_dist'),
              ('raw_temperature','raw_temperature2'),
              ('raw_pressure','raw_pressure2'),
              ('raw_humidity','raw_humidity2'),
              ('use_for_alignment','use_for_distance'),]


#admin.site.register(Level_Observation)
@admin.register(Level_Observation, site=admin_site)
class Level_ObservationAdmin(admin.ModelAdmin):
    list_display = ('pillar', 'pillar_survey')


#admin.site.register(Uncertainty_Budget)
@admin.register(Uncertainty_Budget, site=admin_site)
class Uncertainty_BudgetAdmin(admin.ModelAdmin):
    inlines = [Uncertainty_Budget_SourceInline]


@admin.register(Uncertainty_Budget_Source, site=admin_site)
class UncertaintyBudgetSourceAdmin(admin.ModelAdmin):
    list_display = ['uncertainty_budget', 'group', 'description']

@admin.register(Accreditation, site=admin_site)
class AccreditationnAdmin(admin.ModelAdmin):
    list_display = ('accredited_company','valid_from_date','valid_to_date')
    list_filter = ('accredited_company',)
    fields = ['accredited_company',
              ('valid_from_date','valid_to_date'),
              ('LUM_constant','LUM_ppm'),
              'statement',
              'certificate_upload']


    @admin.register(Std_Deviation_Matrix, site=admin_site)
    class Std_Deviation_MatrixAdmin(admin.ModelAdmin):
        list_display = ['from_pillar', 'to_pillar', 'std_uncertainty']
              
####################################################################
######################## REGISTER MODEL IN SUPER ADMIN #############
####################################################################
try:
    from accounts.sites import medjil_super_site
    @admin.register(Certified_Distance, site=medjil_super_site)
    class CertifiedDistanceAdmin(admin.ModelAdmin):
        list_display = ['pillar_survey', 'from_pillar', 'to_pillar', 'distance']
        
    @admin.register(Pillar_Survey, site=medjil_super_site)
    class Pillar_SurveyAdmin(admin.ModelAdmin):
        list_display = ('baseline','survey_date','job_number','comment')
        list_filter = ('baseline','job_number',)
        search_fields = ['pillar_survey__baseline__site_name']
        fieldsets = (
            ('Documentation', {
            'fields': 
            ('baseline',
            ('survey_date','computation_date'),
            ('accreditation','apply_lum'),
            ('weather','observer'),
            'job_number',
            'comment',
            'fieldnotes_upload')
            }),
            ('Survey Instrumentation', {
            'fields': (
            ('edm','prism','edmi_calib_applied','mets_applied'),
            'co2_content',
            ('level','staff','staff_calib_applied'))
            }),
            ('Meterological Instrumentation', { 
            'fields':
            (('thermometer','thermo_calib_applied'),
            ('barometer','baro_calib_applied'),
            ('hygrometer','hygro_calib_applied'),
            ('thermometer2','thermo2_calib_applied'),
            ('barometer2','baro2_calib_applied'),
            ('hygrometer2','hygro2_calib_applied'),
            ('psychrometer','psy_calib_applied'))
            }),
            ('Statistical parameters', { 
            'fields': (
            'uncertainty_budget',
            'outlier_criterion')
            }),
      )

        # inlines = [EDM_ObservationInline, Level_ObservationInline, Certified_DistanceInline,Std_Deviation_MatrixInline]
        inlines = [Certified_DistanceInline,]

    
    @admin.register(PillarSurveyResults, site=medjil_super_site)
    class PillarSurveyResultsAdmin(admin.ModelAdmin):
        list_display = ['pillar_survey', 'status', 'uploaded_on', 'modified_on']
        list_filter = ['status']
        search_fields = ['pillar_survey__baseline__site_name']
    
        fieldsets = (
                  ('Calibrated Baseline', { 
                  'fields': (
                  ('zero_point_correction','zpc_uncertainty'),
                  ('degrees_of_freedom', 'experimental_std_dev'),
                  'html_report')
                  }),
                  ('Approavals', { 
                  'fields': (
                  ('data_entered_person','data_checked_person'),
                  ('data_entered_position','data_checked_position'),
                  ('data_entered_date','data_checked_date')
                  )
                  }))
              
              
    @admin.register(Pillar_Survey, site=medjil_super_site)
    class EDM_ObservationAdmin(admin.ModelAdmin):
        list_display = ('pillar_survey','from_pillar','to_pillar')
        list_filter = ('pillar_survey',)
        fields = ['pillar_survey',
                  ('from_pillar','to_pillar'),
                  ('inst_ht','tgt_ht'),
                  ('hz_direction','raw_slope_dist'),
                  ('raw_temperature','raw_temperature2'),
                  ('raw_pressure','raw_pressure2'),
                  ('raw_humidity','raw_humidity2'),
                  ('use_for_alignment','use_for_distance'),]    
    
    
    @admin.register(EDM_Observation, site=medjil_super_site)
    class EDM_ObservationAdmin(admin.ModelAdmin):
        list_display = ('pillar_survey','from_pillar','to_pillar')
        list_filter = ('pillar_survey',)
        fields = ['pillar_survey',
                  ('from_pillar','to_pillar'),
                  ('inst_ht','tgt_ht'),
                  ('hz_direction','raw_slope_dist'),
                  ('raw_temperature','raw_temperature2'),
                  ('raw_pressure','raw_pressure2'),
                  ('raw_humidity','raw_humidity2'),
                  ('use_for_alignment','use_for_distance'),]


    #admin.site.register(Level_Observation)
    @admin.register(Level_Observation, site=medjil_super_site)
    class Level_ObservationAdmin(admin.ModelAdmin):
        list_display = ('pillar', 'pillar_survey')


    #admin.site.register(Uncertainty_Budget)
    @admin.register(Uncertainty_Budget, site=medjil_super_site)
    class Uncertainty_BudgetAdmin(admin.ModelAdmin):
        inlines = [Uncertainty_Budget_SourceInline]


    @admin.register(Uncertainty_Budget_Source, site=medjil_super_site)
    class UncertaintyBudgetSourceAdmin(admin.ModelAdmin):
        list_display = ['uncertainty_budget', 'group', 'description']

    @admin.register(Accreditation, site=medjil_super_site)
    class AccreditationnAdmin(admin.ModelAdmin):
        list_display = ('accredited_company','valid_from_date','valid_to_date')
        list_filter = ('accredited_company',)
        fields = ['accredited_company',
                ('valid_from_date','valid_to_date'),
                ('LUM_constant','LUM_ppm'),
                'statement',
                'certificate_upload']


    @admin.register(Std_Deviation_Matrix, site=medjil_super_site)
    class Std_Deviation_MatrixAdmin(admin.ModelAdmin):
        list_display = ['from_pillar', 'to_pillar', 'std_uncertainty']
except:
    pass