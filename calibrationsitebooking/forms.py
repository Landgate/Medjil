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
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError
from datetime import datetime
from .models import (CalibrationSiteBooking,
                    )
from calibrationsites.models import CalibrationSite

# Prepare forms
class CalibrationSiteBookingForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        groups = list(user.groups.values_list('name', flat=True))
        # locations = list(user.locations.values_list('statecode', flat=True))  
        super(CalibrationSiteBookingForm, self).__init__(*args, **kwargs)   
        self.fields['observer'].initial = user
        self.fields['observer'].disabled = True

        # self.fields['site_id'].choices = []; # CalibrationSite.objects.filter(state__statecode__in = locations)
        if not 'Verifying_Authority' in groups:
            self.fields['calibration_type'].choices = [('', '--- Select Type ---')] + [group for group in self.fields['calibration_type'].choices if group[0] == 'Instrument Calibration']
        
        self.fields['location'].empty_label = '--- Select Location ---'
        # self.fields['site_id'].queryset = CalibrationSite.objects.none()
        self.fields['site_id'].empty_label = '--- Select Site ---'

    class Meta:
        model = CalibrationSiteBooking
        # fields = '__all__' 
        exclude = ('id',)
        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": "There is an existing booking for this site. Please select a different date/time."
            }
        }
        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'help_text':'Select a date', 'type':'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        calibration_date = cleaned_data['calibration_date']
        calibration_time = cleaned_data['calibration_time'][:2]
        current_date = datetime.now().date()
        current_time = datetime.now().strftime('%H')

        if calibration_date == current_date and int(calibration_time) < int(current_time):
            raise ValidationError('You have already passed the time. Please choose the next available time.')
        return cleaned_data
