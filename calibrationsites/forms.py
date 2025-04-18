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
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.forms import modelformset_factory, BaseModelFormSet
from .models import (Country, 
                    State, 
                    Locality, 
                    CalibrationSite, 
                    Pillar)
from accounts.models import Company


class CustomClearableFileInput(forms.ClearableFileInput):
    template_name = 'custom_widgets/customclearablefileinput.html'
    
    
# Prepare forms
class CalibrationSiteForm(forms.ModelForm):
    country = forms.ModelChoiceField(empty_label='--- Choose a Country ---',
                                    queryset=Country.objects.all(),
                                    widget=forms.Select())
    state = forms.ModelChoiceField(empty_label='--- Choose a State/Region ---',
                                    queryset=State.objects.all(),
                                    widget=forms.Select())
    locality = forms.ModelChoiceField(empty_label='--- Choose a Locality/Suburb ---',
                                    queryset=Locality.objects.all(),
                                    widget=forms.Select())
    operator = forms.ModelChoiceField(empty_label='--- Choose your firm/company ---',
                                    queryset=Company.objects.exclude(company_abbrev='OTH'),
                                    widget=forms.Select())
    class Meta:
        model = CalibrationSite
        fields = '__all__' 
        widgets = {
            'reference_height': forms.NumberInput(attrs={"step": "0.001"}),
            'description': forms.TextInput(attrs={'class': 'text-area'}),
            'site_access_plan' : forms.FileInput(attrs={'accept' : '.pdf'}),
            'site_booking_sheet' : forms.FileInput(attrs={'accept' : '.pdf'})
            }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CalibrationSiteForm, self).__init__(*args, **kwargs)
        self.fields['site_type'].required = True
        self.fields['site_type'].choices = [(k, v) for k, v in CalibrationSite.site_types if k != 'staff_lab']
        # self.fields['state'].queryset = State.objects.none()
        # self.fields['locality'].queryset = Locality.objects.none()
        # self.fields['operator'].initial = user.company

        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['state'].queryset = State.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        elif self.instance.pk:
            self.fields['state'].queryset = self.instance.country.state_set.order_by('name')

        if 'state' in self.data:
            try:
                country_id = int(self.data.get('country'))
                state_id = int(self.data.get('state'))
                self.fields['locality'].queryset = Locality.objects.filter(state__id = state_id, country__id = country_id)
            except(ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['locality'].queryset = self.instance.state.locality_set.order_by('name')
            

#########################################################################
class CalibrationSiteUpdateForm(forms.ModelForm):
    class Meta:
        model = CalibrationSite
        fields = ['site_type', 'site_name', 'site_status', 'site_address', 'no_of_pillars', 'reference_height', 'description', 'site_access_plan', 'site_booking_sheet']
        widgets = {
            'reference_height': forms.NumberInput(attrs={"step": "0.001"}),
            'description': forms.TextInput(attrs={'class': 'text-area'}),
            'site_access_plan' :  CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False}),
            'site_booking_sheet' :  CustomClearableFileInput(
                attrs={'accept' : '.pdf, .jpg, .jpeg, .png, .tif',
                       'required': False})
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Capture request for messages
        super().__init__(*args, **kwargs)
        # disable fields
        self.fields['site_type'].disabled = True
        self.fields['no_of_pillars'].disabled = True

        if self.instance and self.instance.site_type != 'baseline':
            self.fields.pop('reference_height', None)


#########################################################################
class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = '__all__'
#########################################################################
class StateForm(forms.ModelForm):
    country = forms.ModelChoiceField(empty_label='--- Choose a Country ---',
                                    queryset=Country.objects.all(),
                                    widget=forms.Select())
    class Meta:
        model = State
        fields = '__all__'
#########################################################################
class LocalityForm(forms.ModelForm):
    country = forms.ModelChoiceField(empty_label='--- Choose a Country ---',
                                    queryset=Country.objects.all(),
                                    widget=forms.Select())
    state = forms.ModelChoiceField(empty_label='--- Choose a State/Region ---',
                                    queryset=State.objects.all(),
                                    widget=forms.Select())
    class Meta:
        model = Locality
        fields = '__all__'
#########################################################################

class PillarForm(forms.ModelForm):
    class Meta:
        model = Pillar
        fields = '__all__'
        exclude = ('site_id', 'order',)
        widgets = {
            'height': forms.TextInput(attrs={'placeholder': 'Optional'}),
        }

        
#############################################################################
class AddPillarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        sitetype = kwargs.pop('sitetype', None)
        sitename = kwargs.pop('sitename', None)
        super(AddPillarForm, self).__init__(*args, **kwargs)
        # self.fields['site_id'].queryset = Pillar.objects.filter(site_id__site_name__exact = sitename) 
        self.fields['name'].widget.attrs['required'] = 'required'
        self.fields['name'].widget.attrs['placeholder'] = 'e.g., 2A'
        if sitetype == 'baseline':
            self.fields['easting'].widget.attrs['required'] = 'required'
            self.fields['northing'].widget.attrs['required'] = 'required'
            self.fields['zone'].widget.attrs['required'] = 'required'
            # Place holder
            self.fields['easting'].widget.attrs['placeholder'] = 'MGA2020- e.g., 395006.085'
            self.fields['northing'].widget.attrs['placeholder'] = 'MGA2020- e.g., 6458541.334'
            self.fields['zone'].widget.attrs['placeholder'] = 'Grid Zone'

    class Meta:
        model = Pillar
        fields = '__all__'
        exclude = ('site_id', 'order',)
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s appears to exist already. Pillar/Pin No must be unique.",
            }
        }

class CustomBaseModelFormSet(BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return
        values = set()
        for form in self.forms:
            if form.cleaned_data:
                siteid = form.cleaned_data.get('site_id')
                name = form.cleaned_data.get('name')
                if (siteid, name) in values:
                    form.add_error(None, "Pillar/Pin No must be unique.")
                values.add((siteid, name))

BaseAddPillarFormSet = modelformset_factory(Pillar, 
                                            form=AddPillarForm, 
                                            formset=CustomBaseModelFormSet,
                                            extra=1, 
                                            can_delete=True)

class AddPillarFormSet(BaseAddPillarFormSet):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.sitetype = kwargs.pop('sitetype', None)
        self.sitename = kwargs.pop('sitename', None)
        super(AddPillarFormSet, self).__init__(*args, **kwargs)
        self.queryset = Pillar.objects.filter(site_id__site_name__exact = self.sitename)  
    
    def _construct_form(self, *args, **kwargs):
        # inject user in each form on the formset
        kwargs['user'] = self.user
        kwargs['sitetype'] = self.sitetype
        kwargs['sitename'] = self.sitename
        return super(AddPillarFormSet, self)._construct_form(*args, **kwargs)
###############################################################################