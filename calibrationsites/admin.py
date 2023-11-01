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
from .models import (Country, 
                    State, 
                    Locality,
                    CalibrationSite, 
                    Pillar)

# Register your models here.
admin.site.register(Country)

admin.site.register(Pillar)

class PillarInline(admin.TabularInline):
    model= Pillar
    extra = 0

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'statecode','country']

@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ['name', 'postcode','state','country']

@admin.register(CalibrationSite)
class CalibrationSiteAdmin(admin.ModelAdmin):
    
    list_display = ['id', 'site_name', 'site_type', 'site_address', 'country', 'locality', 'operator', 'uploaded_on', 'modified_on']
    fields = ['site_type', 
            ('site_name', 'no_of_pillars'),
            'site_address', 
            ('country', 'state', 'locality'),
            'operator',
            'site_access',
            'site_config' ]

    # form = LimitToStateForm

    inlines = [
        PillarInline,
    ]

    # inlines = [
    #     PillarInline,
    # ]    

