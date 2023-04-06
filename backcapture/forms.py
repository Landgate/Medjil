
from django import forms

class ImportDliDataForm(forms.Form):
        
    inst_make_file = forms.FileField(
        widget = forms.FileInput(
            attrs={'accept' : '.db',
                   'multiple': True}),
        label = 'Select Database Files to Import')
