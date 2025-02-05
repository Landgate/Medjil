'''

   © 2024 Western Australian Land Information Authority

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
from datetime import date
from django.db.models import Q

# import Models
from .models import (
    uPillarSurvey,
    uEdmObservation,
    Intercomparison)

from baseline_calibration.models import (
    Uncertainty_Budget,
    Pillar_Survey)
from instruments.models import (
    EDM_Inst,
    Prism_Inst, 
    Mets_Inst,
    EDMI_certificate)

from calibrationsites.models import (CalibrationSite)

# Custom widget for clearing an upload file
class CustomClearableFileInput(forms.ClearableFileInput):
    template_name = 'custom_widgets/customclearablefileinput.html'

# make your forms
                
class EDM_ObservationForm(forms.ModelForm):   
    # def __init__(self, *args, **kwargs):
    #     self.fields['use_for_distance'].initial = True
        
    class Meta:
        model = uEdmObservation
        fields = ('use_for_distance',)

        
class EDMI_certificateForm(forms.ModelForm):
    class Meta:
        model = EDMI_certificate
        fields = '__all__'
        

class PillarSurveyApprovals(forms.ModelForm):        
    class Meta:
        model = uPillarSurvey
        fields = [
            'data_entered_person',
            'data_entered_position',
            'data_entered_date',
            'data_checked_person',
            'data_checked_position', 
            'data_checked_date']

        widgets = {
            'data_entered_date': forms.DateInput(
                attrs={'type': 'date', 'format': '%d-%m-%Y'}),
            'data_checked_date': forms.DateInput(
                attrs={'type': 'date', 'format': '%d-%m-%Y'}),
        }
        
class IntercomparisonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(IntercomparisonForm, self).__init__(*args, **kwargs)
        
        self.fields['edm'].queryset = EDM_Inst.objects.filter(
            edm_specs__edm_owner = user.company)
        self.fields['prism'].queryset = Prism_Inst.objects.filter(
            prism_specs__prism_owner = user.company)
                    
    class Meta:
        model = Intercomparison
        fields = '__all__'
        exclude = ('html_report', 'created_on', 'modified_on')

        widgets = {
            'from_date': forms.DateInput(
                attrs={'type': 'date', 'format': '%d-%m-%Y'}),
            'to_date': forms.DateInput(
                attrs={'type': 'date', 'format': '%d-%m-%Y'}),
        }


class BulkEDMIReportForm(forms.Form):
    # Form used for bulk downloading calibration html reports
    # called by .view def bulk_report_download
    baseline = forms.ModelChoiceField(
        queryset=CalibrationSite.objects.filter(
            site_type='baseline'), 
        label="Select Baseline")
    from_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="From Date",
        required=False)
    to_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), 
        label="To Date",
        required=False)
    
    
class uPillarSurveyForm(forms.ModelForm):
    # was CalibrateEdmForm
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        locations = list(user.locations.values_list('statecode', flat=True))
        super(uPillarSurveyForm, self).__init__(*args, **kwargs)
        
        self.fields['survey_date'].initial = date.today().isoformat()
        self.fields['computation_date'].initial = date.today().isoformat()
        
        self.fields['site'].queryset = CalibrationSite.objects.filter(
            Q(site_type = 'baseline') &
            Q(state__statecode__in = locations))
        self.fields['calibrated_baseline'].queryset = Pillar_Survey.objects.filter(
            baseline__state__statecode__in = locations)
        self.fields['uncertainty_budget'].queryset = Uncertainty_Budget.objects.filter(
            Q(company = user.company) | 
            Q(name = 'Default', company__company_name = 'Landgate'))
        self.fields['auto_base_calibration'].required = False
        self.fields['calibrated_baseline'].required = False

        self.fields['edm'].queryset = EDM_Inst.objects.filter(
            edm_specs__edm_owner = user.company)
        self.fields['prism'].queryset = Prism_Inst.objects.filter(
            prism_specs__prism_owner = user.company)
        self.fields['thermometer'].queryset = Mets_Inst.objects.filter(
            mets_specs__inst_type = 'thermo',
            mets_specs__mets_owner = user.company)
        self.fields['barometer'].queryset = Mets_Inst.objects.filter(
            mets_specs__inst_type = 'baro',
            mets_specs__mets_owner = user.company)
        self.fields['hygrometer'].queryset = Mets_Inst.objects.filter(
            mets_specs__inst_type = 'hygro',
            mets_specs__mets_owner = user.company)
            
    class Meta:
        model = uPillarSurvey
        fields = '__all__'
        exclude = (
            'certificate',
            'uploaded_on', 'modified_on',
            'data_entered_person','data_entered_position','data_entered_date',
            'data_checked_person','data_checked_position', 'data_checked_date')
        widgets = {
           'site': forms.Select(attrs={'class': 'page0'}),
           'auto_base_calibration':forms.CheckboxInput(
               attrs={'onclick':'tglCalibBase()'}),
           'calibrated_baseline': forms.Select(attrs={'class':'page0'}),
           'computation_date': forms.DateInput(
               attrs={'type':'date', 'input_formats': ['%d-%m-%Y']}),
           'survey_date': forms.DateInput(
               attrs={'type':'date', 'input_formats': ['%d-%m-%Y'], 'class': 'page0'}),
           'observer': forms.TextInput (attrs={'class': 'page0'}),    
           'weather': forms.Select(attrs={'class': 'page0'}),
           'job_number': forms.TextInput (
               attrs={'class': 'page0'}),
           'comment': forms.TextInput (
               attrs={'class': 'page0'}),
           
           'edm': forms.Select(attrs={'class': 'page1'}),
           'prism': forms.Select(attrs={'class': 'page1'}),
           'thermometer': forms.Select(attrs={'class': 'page1'}),
           'barometer': forms.Select(attrs={'class': 'page1'}),
           'hygrometer': forms.Select(attrs={'class': 'page1'}),
           
           'mets_applied': forms.CheckboxInput(attrs={'class': 'page1'}),
           'thermo_calib_applied': forms.CheckboxInput(attrs={'class': 'page1'}), 
           'baro_calib_applied': forms.CheckboxInput(attrs={'class': 'page1'}), 
           'hygro_calib_applied': forms.CheckboxInput(attrs={'class': 'page1'}),
            
           'uncertainty_budget': forms.Select(attrs={'class': 'page2'}),
           'scalar': forms.NumberInput(
               attrs={'placeholder':'observation standard uncertianties are multiplied by the a-priori scalar',
                      'class': 'page2'}),
           'outlier_criterion': forms.NumberInput(
               attrs={'placeholder':'Enter number of standard deviations for outlier detection',
                      'class': 'page2'}),
           'test_cyclic': forms.CheckboxInput(attrs={'class': 'page2'}),
           'fieldnotes_upload': CustomClearableFileInput(
               attrs={'accept' : '.jpg, .pdf',
                      'class': 'page2'})
            }
        
    def clean_survey_date(self):
        survey_date = self.cleaned_data['survey_date']
        if survey_date > date.today():
            raise forms.ValidationError("The survey date cannot be in the future!")
        return survey_date
    
    def computation_date_date(self):
        computation_date = self.cleaned_data['computation_date']
        if computation_date > date.today():
            raise forms.ValidationError("The computation date cannot be in the future!")
        return computation_date


class UploadSurveyFilesForm(forms.Form):
    edm_file = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'page2'}),
        label = 'EDM File (*.csv)')

    
class ChangeSurveyFilesForm(forms.Form):
    change_edm = forms.BooleanField(
        widget = forms.CheckboxInput(
            attrs={'onclick':'tglFile("edm")',
                   'class': 'page2'}),
        required = False, 
        label = 'Change EDM File')
    
    edm_file = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'page2', 
                                        'style': 'display:none;'}),
        required = False, 
        label = 'EDM File (*.csv)')