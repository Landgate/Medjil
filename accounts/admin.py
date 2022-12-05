from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
# Customise page headings
admin.site.site_header = "Landgate Admin"
admin.site.site_title = "Survey Services Portal"
admin.site.index_title = "Welcome to Landgate Staff Range Calibration Portal"

# Register your models here.

from .models import CustomUser, Company, Calibration_Report_Notes

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_filter = ('company', 'is_active',)

    list_display = (
        'email', 'first_name', 'last_name', 'company', 'is_active', 'is_staff', 'date_joined', 'last_login', 'get_groups',
    )

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'company')
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
            'fields': ('first_name', 'last_name', 'company')
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

class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'pk']
    class Meta:
        model = Group

    ordering = (
        'pk', 'name',
    )

admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_abbrev',)
    search_fields = ('company_name', 'company_abbrev',)
    class Meta:
        model = Company
        
admin.site.register(Calibration_Report_Notes)