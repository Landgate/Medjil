from django.contrib import admin

# Register your models here.
from .models import InstrumentMake, InstrumentModel#, InstrumentType
from .models import DigitalLevel, Staff
from .models import EDM_Specification, EDM_Inst
from .models import Prism_Specification, Prism_Inst
from .models import Mets_Specification, Mets_Inst
from .models import EDMI_certificate, Mets_certificate

########################
## SURVEY INSTRUMENTS ##
########################
# admin.site.register(InstrumentType)
@admin.register(InstrumentMake)
class InstrumentMakeAdmin(admin.ModelAdmin):
    list_display = ('id', 'make', 'make_abbrev')
    ordering = ('make',)
    search_fields = ('make_abbrev',)
    list_filter = ('make_abbrev',)

    
@admin.register(InstrumentModel)
class InstrumentModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'inst_type', 'make', 'model')
    ordering = ('inst_type',)
    search_fields = ('inst_type',)
    list_filter = ('inst_type', 'make',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'staff_number', 'staff_owner', 'staff_model', 'staff_type','staff_length','thermal_coefficient', 'created_on', 'modified_on']
    list_filter = ('staff_model__make', 'staff_owner',)

@admin.register(DigitalLevel)
class DigitalLevelAdmin(admin.ModelAdmin):
    list_display = ('level_number', 'level_owner', 'level_model', 'created_on', 'modified_on')
    list_filter = ('level_model__make', 'level_owner', )

@admin.register(EDM_Specification)
class EDM_SpecificationAdmin(admin.ModelAdmin):
    list_display = ('edm_model',)
    list_filter = ('edm_owner',)
    fields = ['edm_owner',
              ('edm_model', 'edm_type'), 
              ('manu_unc_const', 'manu_unc_ppm', 'manu_unc_k'),
              ('unit_length', 'frequency', 'carrier_wavelength', 'manu_ref_refrac_index'),
              'measurement_increments']

@admin.register(EDM_Inst)
class EDM_InstAdmin(admin.ModelAdmin):
    list_display = ('edm_specs','edm_number')
    list_filter = ('edm_specs__edm_owner',)

@admin.register(Prism_Specification)
class Prism_SpecificationAdmin(admin.ModelAdmin):
    list_display = ('prism_model',)
    list_filter = ('prism_owner',)
    fields = ['prism_owner',
              'prism_model', 
              ('manu_unc_const','manu_unc_k')]

@admin.register(Prism_Inst)
class Prism_InstAdmin(admin.ModelAdmin):
    list_display = ('prism_specs','prism_number')
    list_filter = ('prism_specs__prism_owner',)

################################
## METEOROLOGICAL INSTRUMENTS ##
################################
@admin.register(Mets_Specification)
class Mets_SpecificationAdmin(admin.ModelAdmin):
    list_display = ('mets_model',)
    list_filter = ('mets_model__inst_type','mets_owner',)
    fields = ['mets_owner', 
              'mets_model', 
              ('manu_unc_const','manu_unc_k'),
              'measurement_increments']

@admin.register(Mets_Inst)
class Mets_InstAdmin(admin.ModelAdmin):
    list_display = ('mets_specs','mets_number')
    list_filter = ('mets_specs__mets_model','mets_specs__mets_owner', )

##############################
## CALIBRATION CERTIFICATES ##
##############################
@admin.register(EDMI_certificate)
class EDMI_certificateAdmin(admin.ModelAdmin):
    list_display = ('calibration_date', 'edm', 'prism','scale_correction_factor','zero_point_correction')
    list_filter = ('edm', 'edm__edm_specs__edm_owner', )
    fields = [('edm' ,'prism'),
              'calibration_date',
              ('scale_correction_factor', 'scf_uncertainty','scf_coverage_factor','scf_std_dev'),
              ('zero_point_correction', 'zpc_uncertainty','zpc_coverage_factor','zpc_std_dev'),
              ('standard_deviation', 'degrees_of_freedom'),
              'certificate_upload']

@admin.register(Mets_certificate)
class Mets_certificateAdmin(admin.ModelAdmin):
    list_display = ('calibration_date', 'instrument')
    list_filter = ('instrument__mets_specs__mets_model__inst_type', 
                   'instrument',
                   'instrument__mets_specs__mets_owner',)
