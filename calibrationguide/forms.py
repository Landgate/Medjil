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