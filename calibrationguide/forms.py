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
from .models import (CalibrationGuide,
                     MedjilGuide,
                     MedjilGuideToSiteCalibration,
                    )

# Prepare forms
class CalibrationGuideForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(CalibrationGuideForm, self).__init__(*args, **kwargs)   
        self.fields['author'].initial = user
        self.fields['author'].disabled = True

    content_book = forms.FileField(required=True,
                                   error_messages={'required': 'Please select a pdf file to upload'})
    class Meta:
        model = CalibrationGuide
        fields = '__all__' 
        widgets = {
                'content_book' : forms.FileInput(attrs={'accept' : '.pdf'})
            }
        
class MedjilGuideForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(MedjilGuideForm, self).__init__(*args, **kwargs)   
        self.fields['author'].initial = user
        self.fields['author'].disabled = True

    medjil_book = forms.FileField(required=True,
                                   error_messages={'required': 'Please select a pdf file to upload'})
    class Meta:
        model = MedjilGuide
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