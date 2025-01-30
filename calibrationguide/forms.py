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
from .models import (CalibrationFieldInstruction,
                     MedjilUserGuide,
                     MedjilGuideToSiteCalibration,
                    )

# Prepare forms
class CalibrationFieldInstructionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(CalibrationFieldInstructionForm, self).__init__(*args, **kwargs)   
        self.fields['author'].initial = user
        self.fields['author'].disabled = True

    content_book = forms.FileField(required=True,
                                   error_messages={'required': 'Please select a pdf file to upload'})
    class Meta:
        model = CalibrationFieldInstruction
        fields = '__all__' 
        error_messages = {
            NON_FIELD_ERRORS: {
                # "unique_together": "%(model_name)s's %(field_labels)s are not unique.",
                "unique_together": "The user guide already exists for this location."
            }
        }
        widgets = {
                'content_book' : forms.FileInput(attrs={'accept' : '.pdf'})
            }
        
class MedjilUserGuideForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(MedjilUserGuideForm, self).__init__(*args, **kwargs)   
        self.fields['author'].initial = user
        self.fields['author'].disabled = True

    medjil_book = forms.FileField(required=True,
                                   error_messages={'required': 'Please select a pdf file to upload'})
    class Meta:
        model = MedjilUserGuide
        fields = '__all__' 
        widgets = {
                'medjil_book' : forms.FileInput(attrs={'accept' : '.pdf'})
            }

class MedjilGuideToSiteCalibrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(MedjilGuideToSiteCalibrationForm, self).__init__(*args, **kwargs)   
        self.fields['author'].initial = user
        self.fields['author'].disabled = True

    content_book = forms.FileField(required=True,
                                   error_messages={'required': 'Please select a pdf file to upload'})
    class Meta:
        model = MedjilGuideToSiteCalibration
        fields = '__all__' 
        widgets = {
                'content_book' : forms.FileInput(attrs={'accept' : '.pdf'})
            }