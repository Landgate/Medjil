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

