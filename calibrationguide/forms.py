from django import forms
from .models import InstructionImage, CalibrationInstruction

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
		widget=forms.ClearableFileInput(attrs={'multiple': False}),
		help_text = 'Select one or more images',
	)

	class Meta:
		model = InstructionImage
		fields = ('photos',)