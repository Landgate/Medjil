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
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group
from django.http.request import HttpRequest
from django.urls import path, reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from .models import MedjilTOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin

from django.shortcuts import render

from .views import AdminSetupTwoFactorAuthView, AdminConfirmTwoFactorAuthView

# Register your models here.
from .models import CustomUser, Company, Calibration_Report_Notes, Location
##############################################################################
############################ BUILD A CUSTOM ADMIN SITE #######################
##############################################################################
class MedjilAdminSite(admin.AdminSite):
    def get_urls(self):
        base_urlpatterns = super().get_urls()

        extra_urlpatterns = [
            path(
                "setup-mfa/",
                self.admin_view(AdminSetupTwoFactorAuthView.as_view()),
                name="setup-mfa"
            ),
            path(
                "confirm-mfa/",
                self.admin_view(AdminConfirmTwoFactorAuthView.as_view()),
                name="confirm-mfa"
            )
        ]

        return extra_urlpatterns + base_urlpatterns
    
    def login(self, request, *args, **kwargs):
        if request.method != 'POST':
            return super().login(request, *args, **kwargs)

        username = request.POST.get('username')
        # Query the device 
        two_factor_auth_data = MedjilTOTPDevice.objects.filter(user__email = username).first()

        request.POST._mutable = True
        request.POST[REDIRECT_FIELD_NAME] = reverse('admin:confirm-mfa')

        if two_factor_auth_data is None:
            request.POST[REDIRECT_FIELD_NAME] = reverse("admin:setup-mfa")

        request.POST._mutable = False

        return super().login(request, *args, **kwargs)
    
    def has_permission(self, request):
        has_perm = super().has_permission(request)

        if not has_perm:
            return has_perm

        two_factor_auth_data = MedjilTOTPDevice.objects.filter(
            user=request.user
        ).first()

        allowed_paths = [
            reverse("admin:confirm-mfa"),
            reverse("admin:setup-mfa")
        ]

        if request.path in allowed_paths:
            return True

        if two_factor_auth_data is not None and request.user.is_staff:
            two_factor_auth_token = request.session.get("session_key")
            return str(two_factor_auth_data.session_key) == two_factor_auth_token
            # return True

        return False
##############################################################################
############################ USER CUSTOMISATION  #############################
##############################################################################
@admin.register(CustomUser)
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

##############################################################################
######################### DEFINE THE CUSTOM ADMIN SITE #######################
##############################################################################
admin_site = MedjilAdminSite(name='landgate_admin')
admin_site.site_header = 'Landgate - Medjil Administration Site'
admin_site.site_title = 'Medjil Administration'
admin_site.index_title = 'Medjil Site Administration'
#######################################################################
##################### REGISTER MODELS #################################
#######################################################################
admin_site.register(CustomUser, CustomUserAdmin)

class MedjilTOTPDeviceAdmin(TOTPDeviceAdmin):
    list_display = TOTPDeviceAdmin.list_display + ['created_at', 'last_used_at']
    
    def name(self, obj):
        # return the value of the field you want to display
        return obj.name
        name.short_description = 'Device Name'
        
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['name'].label = 'Device Name'
        return form  
    
    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        admin_group = Group.objects.get(name='Geodesy')
        if request.user.groups.filter(name = admin_group.name).exists():
            return render(request, 'accounts/403.html', status=403)
        return super().change_view(request, object_id, form_url, extra_context)
    
admin_site.register(MedjilTOTPDevice, MedjilTOTPDeviceAdmin)

class Roles(Group):
    class Meta:
        proxy = True
        verbose_name = verbose_name_plural = 'Roles'

@admin.register(Roles, site=admin_site)
class RolesAdmin(admin.ModelAdmin):
    list_display = ['name', 'pk']
    class Meta:
        model = Roles

    ordering = (
        'pk', 'name',
    )
    # Hide Group table from Geodesy Group
    def has_module_permission(self, request):
        if request.user.groups.filter(name='Geodesy').exists():
            return False
        return True

@admin.register(Location, site=admin_site)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'statecode',)
    search_fields = ('statecode',)
    class Meta:
        model = Location

@admin.register(Company, site=admin_site)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_abbrev','company_secret_key')
    search_fields = ('company_name', 'company_abbrev',)
    class Meta:
        model = Company
      
@admin.register(Calibration_Report_Notes, site=admin_site)
class CalibrationReportNotesAdmin(admin.ModelAdmin):
    list_display = ['company', 'report_type', 'note_type']
    list_filter = ['company']
##############################################################################
##################################### END OF LINE  ###########################
##############################################################################
