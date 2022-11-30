from django import forms
from datetime import date
from django.db.models import Q
from django.core.validators import MaxValueValidator, MinValueValidator

# import Models
from .models import (uPillar_Survey,
                     uEDM_Observation,
                     uCalibration_Parameter)

from baseline_calibration.models import Uncertainty_Budget
from instruments.models import (EDM_Inst, 
                                Prism_Inst, 
                                Mets_Inst, 
                                DigitalLevel, 
                                Staff)
from calibrationsites.models import (CalibrationSite, 
                                     Pillar)

# make your forms
class CalibrateEdmForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CalibrateEdmForm, self).__init__(*args, **kwargs)
        self.fields['site'].queryset = CalibrationSite.objects.filter(
            site_type = 'baseline')
        self.fields['uncertainty_budget'].queryset = Uncertainty_Budget.objects.filter(
            Q(company = user.company) | 
            Q(name = 'Default', company__company_name = 'Landgate'))
        self.fields['auto_base_calibration'].required = False
        self.fields['calibrated_baseline'].required = False
        if user.is_staff:
            self.fields['auto_base_calibration'].widget.attrs['class'] = 'show'
            self.fields['edm'].queryset = EDM_Inst.objects.all()
            self.fields['prism'].queryset = Prism_Inst.objects.all()
            self.fields['thermometer'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_model__inst_type = 'thermo')
            self.fields['barometer'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_model__inst_type = 'baro')
            self.fields['hygrometer'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_model__inst_type = 'hygro')
        else:
            self.fields['edm'].queryset = EDM_Inst.objects.filter(
                edm_specs__edm_owner = user.company)
            self.fields['prism'].queryset = Prism_Inst.objects.filter(
                prism_specs__prism_owner = user.company)
            self.fields['thermometer'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_model__inst_type = 'thermo',
                mets_specs__mets_owner = user.company)
            self.fields['barometer'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_model__inst_type = 'baro',
                mets_specs__mets_owner = user.company)
            self.fields['hygrometer'].queryset = Mets_Inst.objects.filter(
                mets_specs__mets_model__inst_type = 'hygro',
                mets_specs__mets_owner = user.company)
            
    class Meta:
        model = uPillar_Survey
        fields = '__all__'
        exclude = ('degrees_of_freedom','variance','k',
                   'uploaded_on', 'modified_on')
        widgets = {
           'site': forms.Select(attrs={'class': 'page0'}),
           'auto_base_calibration':forms.CheckboxInput(
               attrs={'onclick':'tglCalibBase()'}),
           'calibrated_baseline': forms.Select(attrs={'class':'bCalib_slct'}),
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
           'fieldnotes_upload': forms.FileInput(attrs={'accept' : '.jpg, .pdf',
                                                         'class': 'page2'})
            }
        labels = {'auto_base_calibration':'Auto select corresponding calibration of this baseline',
                  'outlier_criterion': 'Rejection Criteria for outlier detection',
                  'fieldnotes_upload': 'Scanned Fieldnotes'}
        
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


class UploadSurveyFiles(forms.Form):
    edm_file = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'page2'}), 
        label = 'EDM File (*.csv)')


class ChangeSurveyFiles(forms.Form):
    change_edm = forms.BooleanField(
        widget = forms.CheckboxInput(attrs={'class': 'page2', 
                                            'onclick':'tglEdmFile()'}),
        required = False, 
        label = 'Change EDM File')
    edm_file = forms.FileField(
        widget = forms.FileInput(attrs={'accept' : '.csv, .asc',
                                        'class': 'edm_file'}),
        required = False, 
        label = 'EDM File (*.csv)')
    
                
class EDM_ObservationForm(forms.ModelForm):                
    class Meta:
        model = uEDM_Observation
        fields = ['use_for_distance']
        labels = {'id': 'Obs #',}
    

class PillarSurveyUpdateForm(forms.ModelForm):
    class Meta:
        model = uPillar_Survey
        fields = ['degrees_of_freedom','variance','k']


class CalibrationParamForm(forms.ModelForm):
    class Meta:
        model = uCalibration_Parameter
        fields = '__all__'
