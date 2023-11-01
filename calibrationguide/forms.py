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
from .models import (
    InstructionImage, 
    CalibrationInstruction, 
    TechnicalManual,
    ManualImage)
from instruments.forms import CustomClearableFileInput

# insert your forms
class CalibrationInstructionForm(forms.ModelForm):
    class Meta:
        model = CalibrationInstruction
        fields = [
            'calibration_type',
            'title',
            'thumbnail',
            'site_id',
            'content',
        ]
        widgets = {
            'thumbnail': CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif'}),
            'content': forms.Textarea(attrs={'class': 'text-area2'}),
        }


class CalibrationInstructionUpdateForm(forms.ModelForm):
    class Meta:
        model = CalibrationInstruction
        fields = '__all__' #[ 'title', 'thumbnail', 'instruct_type', 'site_id', 'content', 'author']
        widgets = {
            'content': forms.Textarea(attrs={'wrap':'hard', 'class': 'text-area2'}),
        }

    def __init__(self, *args, **kwargs):
        super(CalibrationInstructionUpdateForm, self).__init__(*args, **kwargs)
        self.fields['site_id'].disabled = True
        self.fields['calibration_type'].disabled = True


class InstructionImageForm(forms.ModelForm):
    photos = forms.ImageField(
        label='Photo',
        widget=CustomClearableFileInput(attrs={'multiple': False}),
        help_text = 'Select one or more images',
    )

    class Meta:
        model = InstructionImage
        fields = ('photos',)


class TechnicalManualForm(forms.ModelForm):
    class Meta:
        model = TechnicalManual
        fields = [
            'manual_type',
            'title',
            'thumbnail',
            'content',
        ]
        widgets = {
            'thumbnail': CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif'}),
            'content': forms.Textarea(attrs={'class': 'text-area2'}),
        }


class TechnicalManualUpdateForm(forms.ModelForm):
    class Meta:
        model = TechnicalManual
        fields = '__all__' #[ 'title', 'thumbnail', 'instruct_type', 'site_id', 'content', 'author']
        widgets = {
            'thumbnail': CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif'}),
            'content': forms.Textarea(attrs={'wrap':'hard', 'class': 'text-area2'}),
        }

    def __init__(self, *args, **kwargs):
        super(TechnicalManualUpdateForm, self).__init__(*args, **kwargs)
        self.fields['manual_type'].disabled = True


class ManualImageForm(forms.ModelForm):
    photos = forms.ImageField(
        label='Photo',
        widget=CustomClearableFileInput(attrs={'multiple': False}),
        help_text = 'Select one or more images',
    )

    class Meta:
        model = ManualImage
        fields = ('photos',)