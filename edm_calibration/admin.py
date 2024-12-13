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
from accounts.admin import admin_site
from .models import * 

@admin.register(uPillar_Survey, site=admin_site)
class UPillarSurveyAdmin(admin.ModelAdmin):
    list_display = ['calibrated_baseline', 'survey_date', 'observer', 'job_number', 'edm']
    list_filter = ['site']
    ordering = ['site', 'survey_date']

@admin.register(uEDM_Observation, site=admin_site)
class UEDMObservationAdmin(admin.ModelAdmin):
    list_display = ['pillar_survey', 'from_pillar', 'to_pillar']

@admin.register(Inter_Comparison, site=admin_site)
class InterComparisonAdmin(admin.ModelAdmin):
    list_display = ['edm', 'prism', 'from_date', 'to_date', 'job_number']


try:
    from accounts.sites import medjil_super_site

    @admin.register(uPillar_Survey, site=medjil_super_site)
    class UPillarSurveyAdmin(admin.ModelAdmin):
        list_display = ['calibrated_baseline', 'survey_date', 'observer', 'job_number', 'edm']
        list_filter = ['site']
        ordering = ['site', 'survey_date']

    @admin.register(uEDM_Observation, site=medjil_super_site)
    class UEDMObservationAdmin(admin.ModelAdmin):
        list_display = ['pillar_survey', 'from_pillar', 'to_pillar']

    @admin.register(Inter_Comparison, site=medjil_super_site)
    class InterComparisonAdmin(admin.ModelAdmin):
        list_display = ['edm', 'prism', 'from_date', 'to_date', 'job_number']

except:
    pass