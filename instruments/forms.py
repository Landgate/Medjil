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
from django import forms
# from django.core.exceptions import NON_FIELD_ERRORS
from .models import (
    InstrumentMake, 
    InstrumentModel, 
    Staff, 
    DigitalLevel,
    EDM_Inst,
    EDM_Specification,
    Prism_Inst,
    Prism_Specification,
    Mets_Inst,
    Mets_Specification,
    EDMI_certificate,
    Mets_certificate
    )

from accounts.models import Company, CustomUser


length_units = (
        ('µm','µm'),
        ('nm','nm'),
        ('mm','mm'),
        ('m','m'),)
freq_units = (
        ('Hz','Hz'),
        ('MHz','MHz'),)
scalar_units = (
        ('A.x','A.x'),
        ('ppm','ppm'),
        ('%','%'),)   
ini_units = ()

# Prepare forms
class CustomClearableFileInput(forms.ClearableFileInput):
    template_name = 'custom_widgets/customclearablefileinput.html'


class InstrumentMakeCreateForm(forms.ModelForm):
    class Meta:
        model = InstrumentMake
        fields = '__all__'

class InstrumentModelCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InstrumentModelCreateForm, self).__init__(*args, **kwargs) 
        self.fields['make'].empty_label = '--- Select one ---'  

    class Meta:
        model = InstrumentModel
        fields = '__all__'
        
        
class InstrumentModelCreateByInstTypeForm(forms.Form):
    inst_types = (
                ( None, 'Select one of the following'),
                ('edm','Total Station EDM'),
                ('prism','Prism'),
                ('level','Digital Level'),
                ('staff','Barcoded Staff'),
                ('baro','Barometer'),
                ('thermo','Themometer'),
                ('hygro','Hygrometer'),
                ('psy','Psychrometer'))

    def __init__(self, *args, **kwargs):
        inst_type = kwargs.pop('inst_type')
        super(InstrumentModelCreateByInstTypeForm, self).__init__(*args, **kwargs)
        self.initial['inst_type'] = inst_type
    
    inst_type = forms.ChoiceField(widget = forms.Select(), choices = inst_types)
    make = forms.ModelChoiceField(empty_label='Select one of the following',
                                required=True,
                                queryset=InstrumentMake.objects.all(),
                                widget=forms.Select())

    inst_make = forms.CharField(
        max_length=25, min_length=4, required=False,
        help_text="e.g., LEICA, TRIMBLE, SOKKIA", label = 'Make (New)')
    inst_abbrev = forms.CharField(
        max_length=4, min_length=3, required=False, 
        help_text="e.g., LEI, TRIM, SOKK",  label = 'Abbreviation (New)')
    model = forms.CharField(
        max_length=25, min_length=3, required=True, 
        help_text="e.g., LS15, DNA03, TS30, S9, SX12, GT-1200/600", 
        label = 'Model (new)')


class DigitalLevelCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(DigitalLevelCreateForm, self).__init__(*args, **kwargs)   
        self.base_fields['level_owner'].initial = user.company
        if not user.is_staff:
            self.fields['level_owner'].disabled = True
        self.fields['level_model'].empty_label = '--- Select one ---'

        # self.fields['level_owner'].queryset = Company.objects.exclude(company_abbrev__iexact='OTH')
        self.fields['level_number'].widget.attrs['placeholder'] = 'Level number, e.g., Serial number'

    level_owner = forms.ModelChoiceField(
        empty_label='Choose a firm/company',
        queryset=Company.objects.exclude(company_abbrev='OTH'),
        widget=forms.Select())
    class Meta:
        model = DigitalLevel
        fields = ('level_model', 'level_owner', 'level_number',)
        # exclude = ('level_model',)


class StaffCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(StaffCreateForm, self).__init__(*args, **kwargs) 
        if not user.is_staff:
            self.fields['staff_owner'].queryset = Company.objects.filter(company_name=user.company.company_name)
        
        self.fields['staff_model'].empty_label = '--- Select one ---'
        self.fields['staff_owner'].empty_label = '--- Select one ---'

    staff_owner = forms.ModelChoiceField(
        #empty_label='--- Select one ---',
        queryset=Company.objects.exclude(company_abbrev='OTH'),
        widget=forms.Select())

    class Meta:
        model = Staff
        fields = '__all__'   
        
    calibrated = forms.BooleanField(
        required=False, 
        label = "Is Calibrated", 
        help_text = "Does it have a previous calibration record?")


class EDM_InstForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(EDM_InstForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['edm_custodian'].queryset = CustomUser.objects.filter(
                company__company_name = user.company.company_name) 
        self.fields['edm_custodian'].empty_label = '--- Select one ---'
        self.fields['edm_specs'].empty_label = '--- Select one ---'

    class Meta:
        model = EDM_Inst
        fields = '__all__'
        exclude = ('created_on', 'modified_on')
        widgets = {
            'photo' :  CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False})
        }

    
class EDM_SpecificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(EDM_SpecificationForm, self).__init__(*args, **kwargs) 
        self.initial['edm_owner'] = user.company
        self.base_fields['units_manu_unc_const'].initial = 'mm'
        self.base_fields['units_manu_unc_ppm'].initial = 'ppm'
        self.base_fields['units_frequency'].initial = 'Hz'
        self.base_fields['units_unit_length'].initial = 'm'
        self.base_fields['units_carrier_wavelength'].initial = 'nm'
        self.base_fields['units_measurement_inc'].initial = 'm'
        if not user.is_staff:
            self.fields['edm_owner'].disabled = True
        self.fields['edm_model'].empty_label = '--- Select one ---'

    class Meta:
        model = EDM_Specification
        fields = '__all__'
        exclude = ('created_on', 'modified_on')
        
    units_manu_unc_const = forms.CharField(
        widget=forms.Select(choices=length_units))
    units_manu_unc_ppm = forms.CharField(
        widget=forms.Select(choices=scalar_units))
    units_frequency = forms.CharField(
        widget=forms.Select(choices=freq_units))
    units_unit_length = forms.CharField(
        widget=forms.Select(choices=length_units))
    units_carrier_wavelength = forms.CharField(
        widget=forms.Select(choices=length_units))
    units_measurement_inc = forms.CharField(
        widget=forms.Select(choices=length_units))
    
    
class Prism_InstForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(Prism_InstForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['prism_custodian'].queryset = CustomUser.objects.filter(
                company__company_name = user.company.company_name) 
        self.fields['prism_custodian'].empty_label = '--- Select one ---'
        self.fields['prism_specs'].empty_label = '--- Select one ---'

    class Meta:
        model = Prism_Inst
        fields = '__all__'
        exclude = ('created_on', 'modified_on')
        widgets = {
            'photo' : CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False})
        }


class Prism_SpecificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(Prism_SpecificationForm, self).__init__(*args, **kwargs) 
        self.initial['prism_owner'] = user.company
        self.base_fields['units_manu_unc_const'].initial = 'mm'
        if not user.is_staff:
            self.fields['prism_owner'].disabled = True
        self.fields['prism_model'].empty_label = '--- Select one ---'

    class Meta:
        model = Prism_Specification
        fields = '__all__'
        exclude = ('created_on', 'modified_on')
        
    units_manu_unc_const = forms.CharField(
        widget=forms.Select(choices=length_units))


class Mets_InstForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        inst_type = kwargs.pop('inst_type', None)
        super(Mets_InstForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['mets_custodian'].queryset = CustomUser.objects.filter(
                company__company_name = user.company.company_name)
        if inst_type:
            self.fields['mets_specs'].queryset = (Mets_Specification.objects
                .filter(mets_model__inst_type = inst_type))
        self.fields['mets_custodian'].empty_label = '--- Select one ---'
        self.fields['mets_specs'].empty_label = '--- Select one ---'

    class Meta:
        model = Mets_Inst
        fields = '__all__'
        exclude = ('created_on', 'modified_on')
        widgets = {
            'photo' : CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False})
        }


class Mets_SpecificationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        inst_type = kwargs.pop('inst_type', None)
        super(Mets_SpecificationForm, self).__init__(*args, **kwargs) 
        self.initial['mets_owner'] = user.company
        if not user.is_staff:
            self.fields['mets_owner'].disabled = True
        self.fields['mets_model'].empty_label = '--- Select one ---'
        if inst_type:
            self.fields['mets_model'].queryset = (InstrumentModel.objects
                .filter(inst_type = inst_type))

    class Meta:
        model = Mets_Specification
        fields = '__all__'
        exclude = ('created_on', 'modified_on')
        widgets = {'mets_model': forms.Select(attrs={'onchange':'ChgUnits()'})
                    }    
    
    units_manu_unc_const = forms.CharField(
        widget=forms.Select(choices=ini_units))
        
    units_measurement_inc = forms.CharField(
        widget=forms.Select(choices=ini_units))
        
    
class EDMI_certificateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(EDMI_certificateForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['edm'].queryset = EDM_Inst.objects.filter(
                edm_specs__edm_owner = user.company)
            self.fields['prism'].queryset = Prism_Inst.objects.filter(
                prism_specs__prism_owner = user.company)
        else:
            self.fields['edm'].queryset = EDM_Inst.objects.all()
            self.fields['prism'].queryset = Prism_Inst.objects.all()
        
        self.fields['edm'].empty_label = '--- Select one ---'
        self.fields['prism'].empty_label = '--- Select one ---'

    class Meta:
        model = EDMI_certificate
        fields = '__all__'
        exclude = ('created_on', 'modified_on',
                   'scf_std_dev', 'zpc_std_dev',
                   'cyc_1_std_dev','cyc_2_std_dev','cyc_3_std_dev','cyc_4_std_dev',
                   'html_report')

        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'),
                attrs={'type':'date'}),
            'certificate_upload' : CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False}),
            'has_cyclic_corrections': forms.CheckboxInput(
                attrs={'onclick': 'toggleCyclic();'})
           }
        
    units_scf = forms.CharField(
        widget=forms.Select(choices=ini_units))
    units_zpc = forms.CharField(
        widget=forms.Select(choices=ini_units))
    units_cyc_1 = forms.CharField(
        widget=forms.Select(choices=ini_units))
    units_cyc_2 = forms.CharField(
        widget=forms.Select(choices=ini_units))
    units_cyc_3 = forms.CharField(
        widget=forms.Select(choices=ini_units))
    units_cyc_4 = forms.CharField(
        widget=forms.Select(choices=ini_units))
    units_stdev = forms.CharField(
        widget=forms.Select(choices=ini_units))


class Mets_certificateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        inst_type = kwargs.pop('inst_type', None)
        super(Mets_certificateForm, self).__init__(*args, **kwargs)
        if not user.is_staff and inst_type:
            self.fields['instrument'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_owner = user.company,
                mets_specs__mets_model__inst_type = inst_type)
        if not user.is_staff and not inst_type:
            self.fields['instrument'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_owner = user.company)
                
        if user.is_staff and inst_type:
            self.fields['instrument'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_model__inst_type = inst_type)                
        if user.is_staff and not inst_type:
                self.fields['instrument'].queryset = Mets_Inst.objects.all()
            
        self.fields['instrument'].empty_label = '--- Select one ---'

    class Meta:
        model = Mets_certificate
        fields = '__all__'
        exclude = ('created_on', 'modified_on', 'zpc_std_dev')

        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'),
                attrs={'type':'date'}),
            'certificate_upload': CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, jpeg, .png, .tif'})
           }

    units_zpc = forms.CharField(
        widget=forms.Select(choices=ini_units))
        
