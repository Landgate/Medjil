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
from django.db.models import Q
from django.db.models import Case, When, Value, IntegerField
from django.core.exceptions import ValidationError
import csv
from django.core.exceptions import NON_FIELD_ERRORS

from instruments.models import Staff, DigitalLevel
from .models import StaffCalibrationRecord
from calibrationsites.models import CalibrationSite


# Prepare forms
class CustomClearableFileInput(forms.ClearableFileInput):
    template_name = 'custom_widgets/customclearablefileinput.html'

# Create Forms
class StaffCalibrationRecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(StaffCalibrationRecordForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner=user.company)
            self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner=user.company)
        self.fields['inst_level'].empty_label = '--- Select one ---'
        self.fields['inst_staff'].empty_label = '--- Select one ---'

    site_id = forms.ModelChoiceField(empty_label='Select one of the following',
                                required=True,
                                queryset=CalibrationSite.objects.all(),
                                widget=forms.Select(),
                                label = 'Calibration Site')
    level_used = forms.BooleanField(
        initial=True,
        required=False, 
        label = "Level Used", 
        help_text = "Has a level instrument been used for this certificate?")

    class Meta:
        model = StaffCalibrationRecord
        fields = '__all__'
        exclude = ('id','field_file', 'field_book', 'observer_isme', 'observer',)
        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'help_text':'Select a date', 'type':'date'}),
            # 'calibration_report' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'}),
            'calibration_report' :  CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False})
            #'field_book' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'})
        }
        
    field_order = ['site_id','job_number','inst_staff', 'level_used', 'inst_level', \
                    'scale_factor', 'grad_uncertainty', 'standard_temperature', 'observed_temperature', \
                    'calibration_date', 'calibration_report']

    
# Calibration Form without Staff Number
class StaffCalibrationRecordFormOnTheGo(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(StaffCalibrationRecordFormOnTheGo, self).__init__(*args, **kwargs)
         
        #print(Staff.objects.filter(staff_owner=user.company))
        if not user.is_staff:
            # self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner=user.company)
            self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner=user.company)
        self.fields['inst_level'].empty_label = '--- Select one ---'
        # self.fields['inst_staff'].empty_label = '--- Select one ---'

    site_id = forms.ModelChoiceField(empty_label='Select one of the following',
                                required=True,
                                queryset=CalibrationSite.objects.filter(Q(site_type = 'staff_range') | Q(site_type = 'staff_lab')),
                                widget=forms.Select(), 
                                label = 'Calibration Site')
    class Meta:
        model = StaffCalibrationRecord
        fields = '__all__'
        exclude = ('id', 'inst_staff', 'field_file', 'field_book', 'observer_isme', 'observer',)
        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'help_text':'Select a date', 'type':'date'}),
            'calibration_report' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'}),
            'field_book' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'})
        }

class StaffCalibrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        groups = list(user.groups.values_list('name', flat=True))
        locations = list(user.locations.values_list('statecode', flat=True))
        super(StaffCalibrationForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner=user.company)
            self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner=user.company)
        else:
            queryset1 = Staff.objects.annotate(
                is_top=Case(
                    When(staff_owner=user.company, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                    )
                ).order_by('-is_top')  # Adjust the ordering as needed
            self.fields['inst_staff'].queryset = queryset1

            queryset2 = DigitalLevel.objects.annotate(
                is_top=Case(
                    When(level_owner=user.company, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                    )
                ).order_by('-is_top')  # Adjust the ordering as needed
            self.fields['inst_level'].queryset = queryset2
        
        # self.fields['site_id'].queryset = CalibrationSite.objects.filter(site_type = 'staff_range' )
        if not 'Verifying_Authority' in groups:
            self.fields['site_id'].queryset = CalibrationSite.objects.filter(Q(site_type = 'staff_range') & Q(state__statecode__in = locations))
        else:
            self.fields['site_id'].queryset = CalibrationSite.objects.filter(site_type = 'staff_range')
            
        self.fields['site_id'].empty_label = '--- Select one ---'
        self.fields['inst_staff'].empty_label = '--- Select one ---'
        self.fields['inst_level'].empty_label = '--- Select one ---'

        self.fields['site_id'].required = True
        self.fields['inst_staff'].required = True
        self.fields['inst_level'].required = True

    start_temperature = forms.FloatField(help_text = "Temperature at the start of observation.")
    end_temperature = forms.FloatField(help_text = "Temperature at the end of observation.")
    class Meta:
        model = StaffCalibrationRecord
        fields = ['site_id','job_number','inst_staff','inst_level','start_temperature','end_temperature', 'field_file','field_book','observer_isme','observer','calibration_date']
        # fields = '__all__'
        exclude = ('id','correction_factor', 'standard_temperature','observed_temperature', 'calibration_report',)
        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'help_text':'Select a date', 'type':'date'}),
            'field_file' : forms.FileInput(attrs={'accept' : '.csv'}),
            'field_book' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'})
        }

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s appears to exist already. Please check the records and calibrate again.",
            }
        }

    def clean_field_file(self):
        field_file = self.cleaned_data.get('field_file')
        if field_file.name.endswith('.csv'):
            reader = csv.reader(field_file.read().decode('utf-8').splitlines()) 
            for row in reader:
                if not row[0].isdigit():
                    raise ValidationError(f'The file appears to contain headers or invalid rows. Please check and upload it again.')
        else:
            raise ValidationError('Invalid file type. Please upload a CSV file.') 
        field_file.seek(0)
        return field_file

