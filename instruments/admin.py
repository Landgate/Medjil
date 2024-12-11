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

# Register your models here.
from .models import InstrumentMake, InstrumentModel#, InstrumentType
from .models import DigitalLevel, Staff
from .models import EDM_Specification, EDM_Inst
from .models import Prism_Specification, Prism_Inst
from .models import Mets_Specification, Mets_Inst
from .models import EDMI_certificate, Mets_certificate

from accounts.admin import admin_site
########################
## SURVEY INSTRUMENTS ##
########################
@admin.register(InstrumentMake, site=admin_site)
class InstrumentMakeAdmin(admin.ModelAdmin):
    list_display = ('id', 'make', 'make_abbrev')
    ordering = ('make',)
    search_fields = ('make_abbrev',)
    list_filter = ('make_abbrev',)

@admin.register(InstrumentModel, site=admin_site)
class InstrumentModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'inst_type', 'make', 'model')
    ordering = ('inst_type',)
    search_fields = ('inst_type',)
    list_filter = ('inst_type', 'make',)

@admin.register(Staff, site=admin_site)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'staff_make_name','staff_model_name', 'staff_number', 'staff_owner', 'staff_type','staff_length','thermal_coefficient', 'created_on', 'modified_on']
    list_filter = ('staff_make_name', 'staff_owner',)

@admin.register(DigitalLevel, site=admin_site)
class DigitalLevelAdmin(admin.ModelAdmin):
    list_display = ('level_make_name','level_model_name', 'level_number', 'level_owner', 'created_on', 'modified_on')
    list_filter = ('level_make_name', 'level_owner', )

@admin.register(EDM_Specification, site=admin_site)
class EDM_SpecificationAdmin(admin.ModelAdmin):
    list_display = ('edm_make_name', 'edm_model_name','edm_owner', 'edm_type')
    list_filter = ('edm_owner',)
    fields = ['edm_owner',
              ('edm_make_name', 'edm_model_name', 'edm_type'), 
              ('manu_unc_const', 'manu_unc_ppm', 'manu_unc_k'),
              ('unit_length', 'frequency', 'carrier_wavelength', 'manu_ref_refrac_index'),
              ('c_term', 'd_term'),
              'measurement_increments']

@admin.register(EDM_Inst, site=admin_site)
class EDM_InstAdmin(admin.ModelAdmin):
    list_display = ('edm_specs','edm_number')
    list_filter = ('edm_specs__edm_owner',)

@admin.register(Prism_Specification, site=admin_site)
class Prism_SpecificationAdmin(admin.ModelAdmin):
    list_display = ('prism_make_name','prism_model_name',)
    list_filter = ('prism_owner',)
    fields = ['prism_owner',
              'prism_make_name', 'prism_model_name', 
              ('manu_unc_const','manu_unc_k')]

@admin.register(Prism_Inst, site=admin_site)
class Prism_InstAdmin(admin.ModelAdmin):
    list_display = ('prism_specs','prism_number')
    list_filter = ('prism_specs__prism_owner',)
################################
## METEOROLOGICAL INSTRUMENTS ##
################################
@admin.register(Mets_Specification, site=admin_site)
class Mets_SpecificationAdmin(admin.ModelAdmin):
    list_display = ('mets_model_name',)
    list_filter = ('inst_type','mets_owner',)
    fields = ['mets_owner', 
              'inst_type', 
              ('mets_make_name', 'mets_model_name'), 
              ('manu_unc_const','manu_unc_k'),
              'measurement_increments']

@admin.register(Mets_Inst, site=admin_site)
class Mets_InstAdmin(admin.ModelAdmin):
    list_display = ('mets_specs','mets_number')
    list_filter = ('mets_specs__mets_model_name','mets_specs__mets_owner', )
##############################
## CALIBRATION CERTIFICATES ##
##############################
@admin.register(EDMI_certificate, site=admin_site)
class EDMI_certificateAdmin(admin.ModelAdmin):
    list_display = ('calibration_date', 'edm', 'prism','scale_correction_factor','zero_point_correction')
    list_filter = ('edm', 'edm__edm_specs__edm_owner', )
    fields = [('edm' ,'prism'),
              'calibration_date',
              ('scale_correction_factor', 'scf_uncertainty','scf_coverage_factor','scf_std_dev'),
              ('zero_point_correction', 'zpc_uncertainty','zpc_coverage_factor','zpc_std_dev'),
              ('has_cyclic_corrections'),
              ('cyclic_one', 'cyc_1_uncertainty','cyc_1_coverage_factor','cyc_1_std_dev'),
              ('cyclic_two', 'cyc_2_uncertainty','cyc_2_coverage_factor','cyc_2_std_dev'),
              ('cyclic_three', 'cyc_3_uncertainty','cyc_3_coverage_factor','cyc_3_std_dev'),
              ('cyclic_four', 'cyc_4_uncertainty','cyc_4_coverage_factor','cyc_4_std_dev'),
              ('standard_deviation', 'degrees_of_freedom'),
              'certificate_upload',
              'html_report']

@admin.register(Mets_certificate, site=admin_site)
class Mets_certificateAdmin(admin.ModelAdmin):
    list_display = ('calibration_date', 'instrument')
    list_filter = ('instrument__mets_specs__inst_type', 
                   'instrument',
                   'instrument__mets_specs__mets_owner',)
###########################################################################
try:
    from accounts.sites import medjil_super_site

    @admin.register(InstrumentMake, site=medjil_super_site)
    class InstrumentMakeAdmin(admin.ModelAdmin):
        list_display = ('id', 'make', 'make_abbrev')
        ordering = ('make',)
        search_fields = ('make_abbrev',)
        list_filter = ('make_abbrev',)

    @admin.register(InstrumentModel, site=medjil_super_site)
    class InstrumentModelAdmin(admin.ModelAdmin):
        list_display = ('id', 'inst_type', 'make', 'model')
        ordering = ('inst_type',)
        search_fields = ('inst_type',)
        list_filter = ('inst_type', 'make',)

    @admin.register(Staff, site=medjil_super_site)
    class StaffAdmin(admin.ModelAdmin):
        list_display = ['id', 'staff_make_name','staff_model_name', 'staff_number', 'staff_owner', 'staff_type','staff_length','thermal_coefficient', 'created_on', 'modified_on']
        list_filter = ('staff_make_name', 'staff_owner',)

    @admin.register(DigitalLevel, site=medjil_super_site)
    class DigitalLevelAdmin(admin.ModelAdmin):
        list_display = ('level_make_name','level_model_name','level_number', 'level_owner', 'created_on', 'modified_on')
        list_filter = ('level_make_name', 'level_owner', )

    @admin.register(EDM_Specification, site=medjil_super_site)
    class EDM_SpecificationAdmin(admin.ModelAdmin):
        list_display = ('edm_make_name', 'edm_model_name','edm_owner', 'edm_type')
        list_filter = ('edm_owner',)
        fields = ['edm_owner',
                  ('edm_make_name', 'edm_model_name', 'edm_type'), 
                  ('manu_unc_const', 'manu_unc_ppm', 'manu_unc_k'),
                  ('unit_length', 'frequency', 'carrier_wavelength', 'manu_ref_refrac_index'),
                  ('c_term', 'd_term'),
                  'measurement_increments']

    @admin.register(EDM_Inst, site=medjil_super_site)
    class EDM_InstAdmin(admin.ModelAdmin):
        list_display = ('edm_specs','edm_number')
        list_filter = ('edm_specs__edm_owner',)

    @admin.register(Prism_Specification, site=medjil_super_site)
    class Prism_SpecificationAdmin(admin.ModelAdmin):
        list_display = ('prism_make_name','prism_model_name',)
        list_filter = ('prism_owner',)
        fields = ['prism_owner',
                  'prism_make_name', 'prism_model_name', 
                  ('manu_unc_const','manu_unc_k')]

    @admin.register(Prism_Inst, site=medjil_super_site)
    class Prism_InstAdmin(admin.ModelAdmin):
        list_display = ('prism_specs','prism_number')
        list_filter = ('prism_specs__prism_owner',)

    @admin.register(Mets_Specification, site=medjil_super_site)
    class Mets_SpecificationAdmin(admin.ModelAdmin):
        list_display = ('mets_model_name',)
        list_filter = ('inst_type','mets_owner',)
        fields = ['mets_owner', 
                  'inst_type', 
                  ('mets_make_name', 'mets_model_name'), 
                  ('manu_unc_const','manu_unc_k'),
                  'measurement_increments']

    @admin.register(Mets_Inst, site=medjil_super_site)
    class Mets_InstAdmin(admin.ModelAdmin):
        list_display = ('mets_specs','mets_number')
        list_filter = ('mets_specs__mets_model_name','mets_specs__mets_owner', )

    @admin.register(EDMI_certificate, site=medjil_super_site)
    class EDMI_certificateAdmin(admin.ModelAdmin):
        list_display = ('calibration_date', 'edm', 'prism','scale_correction_factor','zero_point_correction')
        list_filter = ('edm', 'edm__edm_specs__edm_owner', )
        fields = [('edm' ,'prism'),
                'calibration_date',
                ('scale_correction_factor', 'scf_uncertainty','scf_coverage_factor','scf_std_dev'),
                ('zero_point_correction', 'zpc_uncertainty','zpc_coverage_factor','zpc_std_dev'),
                ('has_cyclic_corrections'),
                ('cyclic_one', 'cyc_1_uncertainty','cyc_1_coverage_factor','cyc_1_std_dev'),
                ('cyclic_two', 'cyc_2_uncertainty','cyc_2_coverage_factor','cyc_2_std_dev'),
                ('cyclic_three', 'cyc_3_uncertainty','cyc_3_coverage_factor','cyc_3_std_dev'),
                ('cyclic_four', 'cyc_4_uncertainty','cyc_4_coverage_factor','cyc_4_std_dev'),
                ('standard_deviation', 'degrees_of_freedom'),
                'certificate_upload',
                'html_report']

    @admin.register(Mets_certificate, site=medjil_super_site)
    class Mets_certificateAdmin(admin.ModelAdmin):
        list_display = ('calibration_date', 'instrument')
        list_filter = ('instrument__mets_specs__inst_type', 
                    'instrument',
                    'instrument__mets_specs__mets_owner',)

except:
    pass