'''

   © 2025 Western Australian Land Information Authority

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
from django.db.models import Q
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
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
        groups = list(user.groups.values_list('name', flat=True))
        locations = list(user.locations.values_list('statecode', flat=True))
        super(RangeForm1, self).__init__(*args, **kwargs)
        self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner = user.company,
                                                                   staff_type__exact = "invar")
        self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner = user.company)
        self.fields['observer'].widget.attrs['placeholder'] = 'Enter the name of Observer, if other than you.'
        self.fields['observer_isme'].widget.attrs['checked'] = False

        # Filter sites based on location
        if not 'Verifying_Authority' in groups:
            self.fields['site_id'].queryset = CalibrationSite.objects.filter(Q(site_type = 'staff_range') & Q(state__statecode__in = locations))
        else:
            self.fields['site_id'].queryset = CalibrationSite.objects.filter(site_type = 'staff_range')

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

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s appears to exist already. Please check the records and calibrate again.",
            }
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