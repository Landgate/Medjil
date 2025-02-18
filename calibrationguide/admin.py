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
from .models import (CalibrationFieldInstruction,
                     MedjilUserGuide,
                     MedjilGuideToSiteCalibration,
                     )

from accounts.admin import admin_site
# Register your models here.


@admin.register(CalibrationFieldInstruction, site=admin_site)
class CalibrationFieldInstructionAdmin(admin.ModelAdmin):
    list_display = ['location', 'calibration_type', 'title', 'content_book', 'author']
    list_filter = ['location', 'calibration_type', 'title']

@admin.register(MedjilUserGuide, site=admin_site)
class MedjilUserGuideAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'medjil_book']
    list_filter = ['title','medjil_book']

@admin.register(MedjilGuideToSiteCalibration, site=admin_site)
class MedjilGuideToSiteCalibrationnAdmin(admin.ModelAdmin):
    list_display = ['location', 'site_type', 'title', 'content_book', 'author']

try:
    from accounts.sites import medjil_super_site

    @admin.register(CalibrationFieldInstruction, site=medjil_super_site)
    class CalibrationFieldInstructionAdmin(admin.ModelAdmin):
        list_display = ['location', 'calibration_type', 'title', 'content_book', 'author']
        list_filter = ['location', 'calibration_type', 'title']

    @admin.register(MedjilUserGuide, site=medjil_super_site)
    class MedjilUserGuideAdmin(admin.ModelAdmin):
        list_display = ['title', 'author', 'medjil_book']
        list_filter = ['title','medjil_book']

    @admin.register(MedjilGuideToSiteCalibration, site=medjil_super_site)
    class MedjilGuideToSiteCalibrationnAdmin(admin.ModelAdmin):
        list_display = ['location', 'site_type', 'title', 'content_book', 'author']
except:
    pass



# @admin.register(CalibrationSite, site=admin_site)
# class CalibrationSiteAdmin(admin.ModelAdmin):
#     list_display = ['id', 'site_name', 'site_type', 'site_status', 'site_address', 'country', 'locality', 'operator', 'uploaded_on', 'modified_on']
#     list_filter = ['site_type']
#     fields = ['site_type', 
#               'site_status', 
#             ('site_name', 'no_of_pillars'),
#             'site_address', 
#             ('country', 'state', 'locality'),
#             'operator',
#             'site_access_plan',
#             'site_booking_sheet' ]

#     inlines = [
#         PillarInline,
#     ]

# try:
#     from accounts.sites import medjil_super_site

#     medjil_super_site.register(Country)

#     @admin.register(State, site=medjil_super_site)
#     class StateAdmin(admin.ModelAdmin):
#         list_display = ['name', 'statecode','country']

#     @admin.register(Locality, site=medjil_super_site)
#     class LocalityAdmin(admin.ModelAdmin):
#         list_display = ['name', 'postcode','state','country']

#     @admin.register(CalibrationSite, site=medjil_super_site)
#     class CalibrationSiteAdmin(admin.ModelAdmin):
#         list_display = ['id', 'site_name', 'site_type', 'site_status', 'site_address', 'country', 'locality', 'operator', 'uploaded_on', 'modified_on']
#         list_filter = ['site_type']
#         fields = ['site_type', 
#                   'site_status',
#                 ('site_name', 'no_of_pillars'),
#                 'site_address', 
#                 ('country', 'state', 'locality'),
#                 'operator',
#                 'site_access_plan',
#                 'site_booking_sheet' ]

#         inlines = [
#             PillarInline,
#         ]
# except:
#     pass