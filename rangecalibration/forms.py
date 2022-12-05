from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
# from .models import Calibration_Update
from instruments.models import Staff, DigitalLevel
from staffcalibration.models import StaffCalibrationRecord
from .models import RangeCalibrationRecord, BarCodeRangeParam
from calibrationsites.models import CalibrationSite
# make your forms
class RangeCalibrationUpdateForm(forms.Form):
    # Range update form
    def __init__(self, *args, **kwargs):
        super(RangeCalibrationUpdateForm, self).__init__(*args, **kwargs)
        
        self.fields['site_id'].widget.attrs['disabled'] = 'disabled'

    class Meta:
        model = RangeCalibrationRecord
        fields = [
            'job_number', 'site_id', 'inst_staff', 'inst_level', 'calibration_date', 'observer_isme', 'observer'
        ]


class RangeForm1(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RangeForm1, self).__init__(*args, **kwargs)
        self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner = user.company,
                                                                   staff_type__exact = "invar")
        self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner = user.company)
        self.fields['observer'].widget.attrs['placeholder'] = 'Enter the name of Observer, if other than you.'
        self.fields['observer_isme'].widget.attrs['checked'] = False

        self.fields['site_id'].empty_label = '--- Select one ---'
        self.fields['inst_staff'].empty_label = '--- Select one ---'
        self.fields['inst_level'].empty_label = '--- Select one ---'


    class Meta:
        model = RangeCalibrationRecord
        fields = ['job_number', 'site_id', 'inst_staff', 'inst_level', 'calibration_date', 'observer_isme', 'observer']
        widgets = {
            'site_id': forms.Select(attrs={'required': 'true'}),
            'inst_staff': forms.Select(attrs={'required': 'true'}),
            'inst_level': forms.Select(attrs={'required': 'true'}),
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'type':'date'}),
            }

class RangeForm2(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RangeForm2, self).__init__(*args, **kwargs)

    start_temp_1 = forms.FloatField(
                                    widget=forms.NumberInput(
                                                            attrs={'placeholder':'Enter values between 0 and 45','required': 'true'}), 
                                                            validators=[
                                                                    MaxValueValidator(50.0),
                                                                    MinValueValidator(-5)
                                                                ],
                                                            label = "Start Temperature (set 1)")                                   
    end_temp_1 = forms.FloatField(widget=forms.NumberInput(
                                                            attrs={'placeholder':'Enter values between 0 and 45','required': 'true'}), 
                                                            validators=[
                                                                    MaxValueValidator(50.0),
                                                                    MinValueValidator(-5)
                                                                ],
                                                            label = "End Temperature (set 1)")
    start_temp_2 = forms.FloatField(widget=forms.NumberInput(
                                                            attrs={'placeholder':'Enter values between 0 and 45','required': 'true'}), 
                                                            validators=[
                                                                    MaxValueValidator(50.0),
                                                                    MinValueValidator(-5)
                                                                ],
                                                            label = "Start Temperature (set 2)")
    end_temp_2 = forms.FloatField(widget=forms.NumberInput(
                                                            attrs={'placeholder':'Enter values between 0 and 45','required': 'true'}), 
                                                            validators=[
                                                                    MaxValueValidator(50.0),
                                                                    MinValueValidator(-5)
                                                                ],
                                                            label = "End Temperature (set 2)")   
    
    class Meta:
        model = RangeCalibrationRecord
        fields = ['start_temp_1', 'start_temp_1', 'end_temp_1', 'start_temp_2', 'end_temp_2', 'field_file', 'field_book']
        widgets = {
            'field_file' : forms.FileInput(attrs={'accept' : '.asc','required': 'true'}),
            'field_book' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif','required': 'true'}), 
            
        }

class RangeForm3(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RangeForm3, self).__init__(*args, **kwargs)

class RangeParamForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(RangeParamForm, self).__init__(*args, **kwargs)
    #     self.fields['site_id'].queryset = CalibrationSite.objects.filter(site_type__exact = 'staff_range')

    site_id = forms.ModelChoiceField(label='Site ID', 
                                        empty_label='--- Select one ---',
                                        queryset= CalibrationSite.objects.filter(site_type__exact = 'staff_range'),
                                        widget=forms.Select(), 
                                    )