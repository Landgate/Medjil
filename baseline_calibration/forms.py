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
from datetime import date

from django import forms
from django.db.models import Q
from django.forms.fields import Field

from .models import (
    Pillar_Survey,
    Accreditation, 
    Uncertainty_Budget,
    Uncertainty_Budget_Source,
    EDM_Observation,
    Certified_Distance,
    Std_Deviation_Matrix,
)
from instruments.models import (
    EDM_Inst,
    Prism_Inst,
    Mets_Inst,
    DigitalLevel,
    Staff,
)
from calibrationsites.models import CalibrationSite


setattr(Field, 'is_checkbox', lambda self: isinstance(self.widget, forms.CheckboxInput))

class CustomClearableFileInput(forms.ClearableFileInput):
    template_name = 'custom_widgets/customclearablefileinput.html'

    
class PillarSurveyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PillarSurveyForm, self).__init__(*args, **kwargs)
        self.fields['baseline'].queryset = CalibrationSite.objects.filter(
            site_type = 'baseline')
        self.fields['edm'].queryset = EDM_Inst.objects.filter(
            edm_specs__edm_owner = user.company)
        self.fields['prism'].queryset = Prism_Inst.objects.filter(
            prism_specs__prism_owner = user.company)
        self.fields['level'].queryset = DigitalLevel.objects.filter(
            level_owner = user.company)
        self.fields['staff'].queryset = Staff.objects.filter(
            staff_owner = user.company)
        self.fields['thermometer'].queryset = Mets_Inst.objects.filter(
            mets_specs__mets_model__inst_type = 'thermo',
            mets_specs__mets_owner = user.company)
        self.fields['barometer'].queryset = Mets_Inst.objects.filter(
            mets_specs__mets_model__inst_type = 'baro',
            mets_specs__mets_owner = user.company)
        self.fields['hygrometer'].queryset = Mets_Inst.objects.filter(
            mets_specs__mets_model__inst_type = 'hygro',
            mets_specs__mets_owner = user.company)
        self.fields['accreditation'].queryset = Accreditation.objects.filter(
            accredited_company = user.company)
        self.fields['uncertainty_budget'].queryset = Uncertainty_Budget.objects.filter(
            Q(company = user.company) | 
            Q(name = 'Default', company__company_name = 'Landgate'))
            
    class Meta:
        model = Pillar_Survey
        fields = '__all__'
        exclude = (
            'psychrometer', 'psy_calib_applied',
            'zero_point_correction','zpc_uncertainty',
            'variance','degrees_of_freedom',
            'uploaded_on', 'modified_on',
            'html_report',
            'data_entered_person','data_entered_position','data_entered_date',
            'data_checked_person','data_checked_position', 'data_checked_date')
        widgets = {
           'baseline': forms.Select(attrs={'class': 'page0'}),
           'computation_date': forms.DateInput(format=('%d-%m-%Y'),
               attrs={'type':'date', 'class': 'page0'}),
           'survey_date': forms.DateInput(format=('%d-%m-%Y'), 
               attrs={'type':'date', 'class': 'page0'}),
           'observer': forms.TextInput (attrs={'class': 'page0'}),    
           'weather': forms.Select(attrs={'class': 'page0'}),
           'job_number': forms.TextInput (
               attrs={'required': 'false', 'class': 'page0'}),
           
           'edm': forms.Select(attrs={'class': 'page1'}),
           'prism': forms.Select(attrs={'class': 'page1'}),
           'level': forms.Select(attrs={'class': 'page1'}),
           'staff': forms.Select(attrs={'class': 'page1'}),
           'thermometer': forms.Select(attrs={'class': 'page1'}),
           'barometer': forms.Select(attrs={'class': 'page1'}),
           'hygrometer': forms.Select(attrs={'class': 'page1'}),
           
           'mets_applied': forms.CheckboxInput(attrs={'class': 'page2',
                                                      'onclick':'tglCO2()'}),
           'co2_content': forms.NumberInput(attrs={'class': 'page2'}),
           'edmi_calib_applied': forms.CheckboxInput(attrs={'class': 'page2'}), 
           'staff_calib_applied': forms.CheckboxInput(attrs={'class': 'page2'}),
           'thermo_calib_applied': forms.CheckboxInput(attrs={'class': 'page2'}), 
           'baro_calib_applied': forms.CheckboxInput(attrs={'class': 'page2'}), 
           'hygro_calib_applied': forms.CheckboxInput(attrs={'class': 'page2'}),
            
           'accreditation': forms.Select(attrs={'class': 'page3'}),
           'apply_lum': forms.CheckboxInput(attrs={'class': 'page3'}),
           'uncertainty_budget': forms.Select(attrs={'class': 'page3'}),
           'outlier_criterion': forms.NumberInput(
               attrs={'placeholder':'Enter number of standard deviations for outlier detection',
                      'class': 'page3'}),
            'fieldnotes_upload': forms.FileInput(
                attrs={'class': 'page3', 'onclick':'ChgNoteFile()'})
            }
        labels = {'outlier_criterion': 'Rejection Criteria for outlier detection',
                  'fieldnotes_upload': 'Scanned Fieldnotes'}

    def clean_survey_date(self):
        survey_date = self.cleaned_data['survey_date']
        if survey_date > date.today():
            raise forms.ValidationError("The survey date cannot be in the future!")
        return survey_date
    
    def clean_computation_date(self):
        computation_date = self.cleaned_data['computation_date']
        if computation_date > date.today():
            raise forms.ValidationError("The computation date cannot be in the future!")
        return computation_date
    
    def pulse_edm_mets_applied(self):
        mets_applied = self.cleaned_data['mets_applied']
        if not mets_applied and self.cleaned_data['edm'].edm_specs.edm_type =='pu':
            raise forms.ValidationError("Pulse instruments must have mets applied!")
        return mets_applied

class UploadSurveyFiles(forms.Form):
        
    edm_file = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'page3'}), 
        label = 'EDM File (*.csv)')
    lvl_file  = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'page3'}), 
        label = 'Reduced Levels File (*.csv)')
    

class ChangeSurveyFiles(forms.Form):
        
    change_edm = forms.BooleanField(
        widget = forms.CheckboxInput(attrs={'class': 'page3', 
                                            'onclick':'tglEdmFile()'}),
        required = False, 
        label = 'Change EDM File')
    edm_file = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'edm_file'}),
        required = False, 
        label = 'EDM File (*.csv)')
    change_lvl = forms.BooleanField(
        widget = forms.CheckboxInput(attrs={'class': 'page3',
                                            'onclick':'tglLvlFile()'}),
        required = False,
        label = 'Change Level File')
    lvl_file  = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'lvl_file'}),
        required = False,
        label = 'Reduced Levels File (*.csv)')
    
                
class EDM_ObservationForm(forms.ModelForm):                
    class Meta:
        model = EDM_Observation
        fields = ['use_for_alignment','use_for_distance']
        labels = {'id': 'Obs #',}
        
    
class Certified_DistanceForm(forms.ModelForm):                
    class Meta:
        model = Certified_Distance
        fields = '__all__'
        exclude = ('uploaded_on', 'modified_on')


class PillarSurveyUpdateForm(forms.ModelForm):                
    class Meta:
        model = Pillar_Survey
        fields = ['zero_point_correction','zpc_uncertainty',
                  'variance','degrees_of_freedom',
                  'html_report']      


class PillarSurveyApprovalsForm(forms.ModelForm):                
    class Meta:
        model = Pillar_Survey
        fields = [
            'data_entered_person',
            'data_entered_position',
            'data_entered_date',
            'data_checked_person',
            'data_checked_position', 
            'data_checked_date']   
        widgets = {
            'data_entered_date': forms.DateInput(
                attrs={'type': 'date', 'input_formats': ['%d-%m-%Y']}),
            'data_checked_date': forms.DateInput(
                attrs={'type': 'date', 'input_formats': ['%d-%m-%Y']}),
        }
    
class Std_Deviation_MatrixForm(forms.ModelForm):                
    class Meta:
        model = Std_Deviation_Matrix
        fields = '__all__'
        exclude = ('uploaded_on', 'modified_on')
        
        
class Uncertainty_BudgetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.sources = kwargs.pop('sources', None)
        super(Uncertainty_BudgetForm, self).__init__(*args, **kwargs)
        if user:
            self.initial['company'] = user.company
            if not user.is_staff:
                self.fields['company'].disabled = True
                
    class Meta:
        model = Uncertainty_Budget
        fields = '__all__'        
        labels = {
            'std_dev_of_zero_adjustment': 'Std Dev Used When Statistically Zero (m)',
            'auto_EDMI_scf':
                {'group':"EDM Scale factor", 
                 'description': "EDMI Reg13 Scale correction factor",
                 'units': "x:1",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Instument Register"},
            'auto_EDMI_scf_drift':
                {'group':"EDM Scale factor",
                 'description': "EDM Scale correction factor drift over time)",
                 'units': "x:1",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Instument Register"},
            'auto_EDMI_round': 
                {'group':"EDMI measurement", 
                 'description': "Distance Instrument rounding",
                 'units': "m",
                 'type': "B",
                 'distribution': "R",
                 'origin': "Instument Register"},
            'auto_humi_rounding':
                {'group': "Humidity", 
                 'description': "Hygrometer rounding",
                 'units': "%",
                 'type': "B",
                 'distribution': "R",
                 'origin': "Instument Register"},
            'auto_humi_zpc':
                {'group':"Humidity", 
                 'description': "Hygrometer calibrated correction factor",
                 'units': "%",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Instument Register"},
            'auto_pressure_rounding':
                {'group':"Pressure", 
                 'description': "Barometer rounding",
                 'units': "hPa",
                 'type': "B",
                 'distribution': "R",
                 'origin': "Instument Register"},
            'auto_pressure_zpc':
                {'group':"Pressure", 
                 'description': "Barometer calibrated correction factor",
                 'units': "hPa",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Instument Register"},
            'auto_temp_rounding':
                {'group':"Temperature", 
                 'description': "Thermometer rounding",
                 'units': "°C",
                 'type': "B",
                 'distribution': "R",
                 'origin': "Instument Register"},
            'auto_temp_zpc': 
                {'group':"Temperature", 
                 'description': "Thermometer calibrated correction factor",
                 'units': "°C",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Instument Register"},
            'auto_cd': 
                {'group':"Certified distances", 
                 'description': "Pillar distances survey, processed uncertainty",
                 'units': "m",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Derived"},
            'auto_EDMI_lr': 
                {'group':"EDMI measurement", 
                 'description': "Linear regression on EDM distance standard deviations",
                 'units': "m",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Derived"},
            'auto_hgts': 
                {'group':"Heights", 
                 'description': "Pillar height differences from imported file",
                 'units': "m",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Derived"},
            'auto_os': 
                {'group':"Offset", 
                 'description': "Pillar alignment survey processed uncertainty",
                 'units': "m",
                 'type': "B",
                 'distribution': "N",
                 'origin': "Derived"},
            }

    def clean_name(self):
        nme = self.cleaned_data['name']
        if nme.lower() == 'default':
            raise forms.ValidationError("'Default' is a reserved keyword. Please rename this item.")
        return nme

    def clean_auto_os(self):
        selected = self.cleaned_data['auto_os']
        if self.sources.is_valid() and not selected:
            groups = [uc['group'] for uc in self.sources.cleaned_data]
            if not '11' in groups:
                raise forms.ValidationError("If this uncertainty source is not selected an uncertainty for this group must be added to 'Custom - Uncertainty Budget Sources' table")
        return selected

    def clean_auto_hgts(self):
        selected = self.cleaned_data['auto_hgts']
        if self.sources.is_valid() and not selected:
            groups = [uc['group'] for uc in self.sources.cleaned_data]
            if not '10' in groups:
                raise forms.ValidationError("If this uncertainty source is not selected an uncertainty for this group must be added to 'Custom - Uncertainty Budget Sources' table")
        return selected
    

class Uncertainty_Budget_SourceForm(forms.ModelForm):
    class Meta:
        model = Uncertainty_Budget_Source
        fields = '__all__'
        exclude = ('std_dev', 'uncertainty_budget')
        widgets = {
            'group': forms.Select(attrs={'onchange':'FilterUnits(this)'}),
            'distribution': forms.Select(attrs={'onchange':'RectCoverFctr(this)'}),
            'uc95': forms.NumberInput(attrs={'required': 'true'})
            }   


class AccreditationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AccreditationForm, self).__init__(*args, **kwargs)
        if user:
            if not user.is_staff:
                self.fields['accredited_company'].disabled = True
                
    class Meta:
        model = Accreditation
        fields = '__all__'

        widgets = {
            'statement': forms.Textarea(attrs={'class': 'text-area2'}),
            'valid_from_date': forms.DateInput(format=('%d-%m-%Y'),
                attrs={'type':'date'}),
            'valid_to_date': forms.DateInput(format=('%d-%m-%Y'),
                attrs={'type':'date'}),
            'certificate_upload': CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False})
           }

