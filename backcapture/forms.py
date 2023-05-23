from django import forms

class ImportDliDataForm(forms.Form):

    dot_db_files = forms.FileField(
        widget = forms.FileInput(
            attrs={'allow_multiple_selected': True,
                   'accept' : '.db'}),
        label = 'Select Database Files to Import')
