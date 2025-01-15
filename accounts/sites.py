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
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

# Custom Site
class MedjilSuperAdminSite(admin.AdminSite): 
    pass
medjil_super_site = MedjilSuperAdminSite(name='medjil_super_admin')
# Customise page headings
medjil_super_site.site_header = "Landgate - Medjil Administration"
medjil_super_site.site_title = "Survey Services Instrument Calibration"
medjil_super_site.index_title = "Medjil Site Administration"

#######################################################################
####################### register models ###############################
#######################################################################
# import models
from .models import (CustomUser,
                    Company,
                    Calibration_Report_Notes,
                    MedjilTOTPDevice,
                    Location,
                    )                   

# medjil_super_site.register(CustomUser)
@admin.register(CustomUser, site=medjil_super_site)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_filter = ('company', 'is_active',)

    list_display = (
        'email', 'first_name', 'last_name', 'company', 'get_locations', 'is_active', 'is_staff', 'date_joined', 'last_login', 'get_groups',
    )

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'company', 'locations')
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', #'is_superuser',
                'groups', 'user_permissions'
                )
        }),
        # ('Important dates', {
        #     'fields': ('last_login', 'date_joined')
        # }),
    )

    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'company', 'locations')
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff',  #'is_superuser',
                'groups', 'user_permissions'
                )
        }),
        # ('Important dates', {
        #     'fields': ('last_login', 'date_joined')
        # }),
    )

    search_fields = ('email', 'company',)
    ordering = ( 'company', 'email', )

    def get_groups(self, obj):
        return ','.join(x for x in obj.groups.values_list('name', flat=True))

    get_groups.short_description = 'Groups'


medjil_super_site.register(Group)

medjil_super_site.register(MedjilTOTPDevice)

@admin.register(Location, site=medjil_super_site)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'statecode',)
    search_fields = ('statecode',)
    class Meta:
        model = Location
    ordering = ( 'name', )

@admin.register(Company, site=medjil_super_site)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_abbrev',)
    search_fields = ('company_name', 'company_abbrev',)
    class Meta:
        model = Company

@admin.register(Calibration_Report_Notes, site=medjil_super_site)
class CalibrationReportNotesAdmin(admin.ModelAdmin):
    list_display = ('calibration_type', 'verifying_authority', 'accreditation', 'company', 'site', 'pillar', 'note')
    list_filter = ('calibration_type', 'verifying_authority','company')
    class Meta:
        model = Calibration_Report_Notes