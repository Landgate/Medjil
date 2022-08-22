from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import date
# import Models
from .models import Pillar_Survey, Accreditation, Uncertainty_Budget
from instruments.models import EDM_Inst, Prism_Inst, Mets_Inst, DigitalLevel, Staff
from calibrationsites.models import CalibrationSite

# make your forms
class CalibrateBaselineForm(forms.ModelForm):
   def __init__(self, *args, **kwargs):
       user = kwargs.pop('user', None)                             
       super(CalibrateBaselineForm, self).__init__(*args, **kwargs)
       self.fields['baseline'].queryset = CalibrationSite.objects.filter(site_type = 'baseline')
       self.fields['accreditation'].queryset = Accreditation.objects.all()
       self.fields['edm'].queryset = EDM_Inst.objects.all()
       self.fields['prism'].queryset = Prism_Inst.objects.all()
       self.fields['level'].queryset = DigitalLevel.objects.all()
       self.fields['staff'].queryset = Staff.objects.all()
       self.fields['thermometer'].queryset = Mets_Inst.objects.filter(mets_specs__mets_model__inst_type = 'thermo')
       self.fields['barometer'].queryset = Mets_Inst.objects.filter(mets_specs__mets_model__inst_type = 'baro')
       self.fields['hygrometer'].queryset = Mets_Inst.objects.filter(mets_specs__mets_model__inst_type = 'hygro')
       self.fields['uncertainty_budget'].queryset = Uncertainty_Budget.objects.all()
   
   
   class Meta:
       model = Pillar_Survey
       fields = ['baseline', 'computation_date', 'survey_date',
                 'accreditation', 
                 'observer', 'weather', 'job_number', 
                 'edm', 'prism', 'level', 'staff', 'thermometer', 'barometer', 'hygrometer', 
                 'mets_applied', 'edmi_calib_applied', 'staff_calib_applied', 'thermo_calib_applied', 'baro_calib_applied', 'hygro_calib_applied', 'psy_calib_applied', 
                 'uncertainty_budget'
                 ]
       widgets = {
           'baseline': forms.Select(attrs={'required': 'true'}),
           'computation_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'type':'date'}),
           'survey_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'type':'date'}),
           'accreditation': forms.Select(attrs={'required': 'true'}),
           'observer': forms.TextInput (attrs={'required': 'true'}),	
           'weather': forms.Select(attrs={'required': 'true'}),
           'job_number': forms.TextInput (attrs={'required': 'true'}),
           'edm': forms.Select(attrs={'required': 'true'}),
           'prism': forms.Select(attrs={'required': 'true'}),
           'level': forms.Select(attrs={'required': 'true'}),
           'staff': forms.Select(attrs={'required': 'true'}),
           'thermometer': forms.Select(attrs={'required': 'true'}),
           'barometer': forms.Select(attrs={'required': 'true'}),
           'hygrometer': forms.Select(attrs={'required': 'true'}), 
           'mets_applied': forms.CheckboxInput(), 
           'edmi_calib_applied': forms.CheckboxInput(), 
           'staff_calib_applied': forms.CheckboxInput(), 
           'thermo_calib_applied': forms.CheckboxInput(), 
           'baro_calib_applied': forms.CheckboxInput(), 
           'hygro_calib_applied': forms.CheckboxInput(), 
           'psy_calib_applied': forms.CheckboxInput(), 
           'uncertainty_budget': forms.Select(attrs={'required': 'true'}),
            }
   outlier_criterion = forms.FloatField(
                             widget=forms.NumberInput(
                                   attrs={'placeholder':'Enter number of standard deviations for outlier detection','required': 'true'}), 
                                   validators=[
                                           MaxValueValidator(5.0),
                                           MinValueValidator(0)
                                           ],
                                   label = "Rejection Criteria for outlier detection")
   Scanned_field_notes = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.jpg, .pdf'}),
   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	required = False)
   
   edm_file = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.csv, .asc'}), label = 'EDM File (*.csv)')
   lvl_file = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.csv, .asc'}), label = 'Reduced Levels File (*.csv)')
   
   
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


class CalibrateBaselineForm1(forms.ModelForm):
   
   def __init__(self, *args, **kwargs):
       user = kwargs.pop('user', None)                             
       super(CalibrateBaselineForm1, self).__init__(*args, **kwargs)
       self.fields['baseline'].queryset = CalibrationSite.objects.filter(site_type = 'baseline')
   
   
   class Meta:
       model = Pillar_Survey
       fields = ['baseline', 'computation_date', 'survey_date', 
                 'observer', 'weather', 'job_number', 
                 ]
       widgets = {
           'baseline': forms.Select(attrs={'required': 'true'}),
           'computation_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'type':'date'}),
           'survey_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'type':'date'}),
           'observer': forms.TextInput (attrs={'required': 'true'}),	
           'weather': forms.Select(attrs={'required': 'true'}),
           'job_number': forms.TextInput (attrs={'required': 'true'}),
            }
   
   edm_file = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.csv, .asc'}), label = 'EDM File (*.csv)')
   lvl_file = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.csv, .asc'}), label = 'Reduced Levels File (*.csv)')
   	   
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


class CalibrateBaselineForm2(forms.ModelForm):
   def __init__(self, *args, **kwargs):
       user = kwargs.pop('user', None)                             
       super(CalibrateBaselineForm2, self).__init__(*args, **kwargs)
       self.fields['edm'].queryset = EDM_Inst.objects.all()
       self.fields['prism'].queryset = Prism_Inst.objects.all()
       self.fields['level'].queryset = DigitalLevel.objects.all()
       self.fields['staff'].queryset = Staff.objects.all()
       self.fields['thermometer'].queryset = Mets_Inst.objects.filter(mets_specs__mets_model__inst_type = 'thermo')
       self.fields['barometer'].queryset = Mets_Inst.objects.filter(mets_specs__mets_model__inst_type = 'baro')
       self.fields['hygrometer'].queryset = Mets_Inst.objects.filter(mets_specs__mets_model__inst_type = 'hygro')
          
   class Meta:
       model = Pillar_Survey
       fields = ['edm', 'prism', 
                 'level','staff', 
                 'thermometer', 
                 'barometer', 
                 'hygrometer', 
                 'mets_applied',     
                 ]
       widgets = {
           'edm': forms.Select(attrs={'required': 'true'}),  
           'mets_applied': forms.CheckboxInput(), 
           'prism': forms.Select(attrs={'required': 'true'}),
           'level': forms.Select(attrs={'required': 'true'}),
           'staff': forms.Select(attrs={'required': 'true'}),
           'thermometer': forms.Select(attrs={'required': 'true'}),
           'barometer': forms.Select(attrs={'required': 'true'}),
           'hygrometer': forms.Select(attrs={'required': 'true'}),
            }


class CalibrateBaselineForm3(forms.ModelForm):
   class Meta:
       model = Pillar_Survey
       fields = ['staff_calib_applied', 
                 'thermo_calib_applied', 
                 'baro_calib_applied', 
                 'hygro_calib_applied',    
                 ]       
       widgets = {
           'staff_calib_applied': forms.CheckboxInput(), 
           'thermo_calib_applied': forms.CheckboxInput(), 
           'baro_calib_applied': forms.CheckboxInput(), 
           'hygro_calib_applied': forms.CheckboxInput(), 
            }


class CalibrateBaselineForm4(forms.ModelForm):
   def __init__(self, *args, **kwargs):
       user = kwargs.pop('user', None)                             
       super(CalibrateBaselineForm4, self).__init__(*args, **kwargs)
       self.fields['accreditation'].queryset = Accreditation.objects.all()
       self.fields['uncertainty_budget'].queryset = Uncertainty_Budget.objects.all()
   
   
   class Meta:
       model = Pillar_Survey
       fields = ['accreditation', 
                 'uncertainty_budget'
                 ]
       widgets = {
           'accreditation': forms.Select(attrs={'required': 'true'}),
           'uncertainty_budget': forms.Select(attrs={'required': 'true'}),
            }
   outlier_criterion = forms.FloatField(
                             widget=forms.NumberInput(
                                   attrs={'placeholder':'Enter number of standard deviations for outlier detection','required': 'true'}), 
                                   validators=[
                                           MaxValueValidator(5.0),
                                           MinValueValidator(0)
                                           ],
                                   label = "Rejection Criteria for outlier detection")
   Scanned_field_notes = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.jpg, .pdf'}),
   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	   	required = False)
   
   edm_file = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.csv, .asc'}), label = 'EDM File (*.csv)')
   lvl_file = forms.FileField(widget=forms.FileInput(attrs={'accept' : '.csv, .asc'}), label = 'Reduced Levels File (*.csv)')
   
   