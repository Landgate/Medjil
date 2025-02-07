from django.contrib import admin
from accounts.admin import admin_site

# Register your models here.
from .models import CalibrationSiteBooking


# Register your models here.


@admin.register(CalibrationSiteBooking, site=admin_site)
class CalibrationSiteBookingAdmin(admin.ModelAdmin):
    list_display = ['location', 'calibration_type', 'observer', 'calibration_date', 'calibration_time']
    list_filter = ['location', 'calibration_type', 'calibration_date']

try:
    from accounts.sites import medjil_super_site
    @admin.register(CalibrationSiteBooking, site=medjil_super_site)
    class CalibrationSiteBookingAdmin(admin.ModelAdmin):
        list_display = ['location', 'calibration_type', 'observer', 'calibration_date', 'calibration_time']
        list_filter = ['location', 'calibration_type', 'calibration_date']
except:
    pass
