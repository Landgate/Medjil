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
from django.forms import ModelForm
from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserCreationForm, UserChangeForm, SetPasswordForm
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q

from .models import CustomUser, Company,  Calibration_Report_Notes, Location
from calibrationsites.models import CalibrationSite, Pillar
from baseline_calibration.models import Accreditation

class SignupForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    company = forms.ModelChoiceField(
        empty_label='Choose your firm/company',
        queryset=Company.objects.all(),
        widget=forms.Select())
    
    csk = forms.CharField(
        required=False,
        label='Company Secret Key',
        widget=forms.TextInput(
            attrs={'placeholder': "Existing users from this company with Medjil login's have access to this key."}))
        
    locations = forms.ModelMultipleChoiceField(
        queryset = Location.objects.all(),
        label = 'Location Group (only select the ones applicable to you)',
        widget = forms.CheckboxSelectMultiple,
        error_messages = {'required': 'Please select at least one location group.'})
        
    class Meta:
        model = CustomUser
        fields = (
            'email', 'first_name', 'last_name', 'company',  'csk', 'locations', 'password1', 'password2')
    
    def clean_email(self):
        return self.cleaned_data.get('email').lower()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        password_validation.validate_password(self.cleaned_data.get('password1'), None)
        return password2
    
    def clean_csk(self):
        company = self.cleaned_data.get('company')
        csk = self.cleaned_data.get('csk')
        
        if Company.company_name != "Others":
            if not Company.objects.filter(id=company.id, company_secret_key=csk).exists():
                raise forms.ValidationError("The Company Secret Key is incorrect. Existing users from this company with Medjil login's have access to this key.")
        return csk
    
    def clean_locations(self):
        locations = self.cleaned_data.get('locations')
        if not locations:
            raise forms.ValidationError("Please choose at least one location group.")
        return locations
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(ModelForm):
    csk = forms.CharField(
        required=False,
        label='Company Secret Key')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.exclude(
            company_name='Others')
        
    class Meta:
        model = CustomUser
        fields = ['first_name','last_name','email', 'company', 'csk', 'locations']

    def clean_csk(self):
        company = self.cleaned_data.get('company')
        csk = self.cleaned_data.get('csk')
        
        if Company.company_name != "Others":
            if not Company.objects.filter(id=company.id, company_secret_key=csk).exists():
                raise forms.ValidationError("The Company Secret Key is incorrect. Existing users from this company with Medjil login's have access to this key.")
        return csk
        
class LoginForm(forms.ModelForm):
    '''
    Form for logging users
    '''
    email = forms.EmailField(widget=forms.TextInput(
        attrs={'class': 'form-control','type':'text','name': 'email','placeholder':'Email address'}), 
        label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class':'form-control','type':'password', 'name': 'password','placeholder':'Password'}),
        label='Password')
    
    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def __init__(self, *args, **kwargs):
        """
          specifying styles to fields 
        """
        super(LoginForm, self).__init__(*args, **kwargs)
        for field in (self.fields['email'],self.fields['password']):
            field.widget.attrs.update({'class': 'form-control '})

    def clean(self):
        if self.is_valid():
            email = self.cleaned_data.get('email').lower()
            password = self.cleaned_data.get('password')
            if not authenticate(email=email, password=password):
                raise forms.ValidationError('The username and/or password you have entered is incorrect. Please check and try again!')
            # modify cleaned_data to have a lower-cased email, if any
            self.cleaned_data['email'] = email

            return self.cleaned_data

class OTPAuthenticationForm(forms.Form):
    """
    """
    otp_token = forms.CharField(
        required=False, widget=forms.TextInput(attrs={'placeholder': 'Insert the 6-digit code from the Authenticator App', 'autocomplete': 'off'})
    )

    def __init__(self, user, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        super().clean()
        # self.clean_otp(self.user)
        return self.cleaned_data

    def get_user(self):
        return self.user

class CustomSetPasswordForm(SetPasswordForm):
    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')

        if self.user.check_password(new_password1):
            raise forms.ValidationError("New password cannot be the same as the current password.")
        return new_password1
            
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['company_name','company_abbrev']
        
        widgets = {
            'company_name' : forms.TextInput(attrs={'placeholder':'Enter a company, e.g., Landgate'}),
            'company_abbrev' : forms.TextInput(attrs={'placeholder':'Give an abbreviation, e.g., LG'}),
        }

    def clean_company_abbrev(self):
        company_abbrev = self.cleaned_data['company_abbrev'].upper()
        return company_abbrev
    
class calibration_report_notesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        locations = list(user.locations.values_list('statecode', flat=True))        
        super(calibration_report_notesForm, self).__init__(*args, **kwargs) 
        
        if not user.company.company_name == 'Landgate':
            self.initial['verifying_authority'] = user.company
        self.fields['verifying_authority'].queryset = Company.objects.filter(
            company_name = user.company)
        self.fields['accreditation'].queryset = Accreditation.objects.filter(
            accredited_company = user.company)
        self.fields['site'].queryset = CalibrationSite.objects.filter(
            Q(site_type = 'baseline') &
            Q(state__statecode__in = locations))
        self.fields['pillar'].queryset = Pillar.objects.filter(
            Q(site_id__site_type = 'baseline') &
            Q(site_id__state__statecode__in = locations))
        
        if not user.is_staff:
            self.fields.pop('verifying_authority', None)
            self.fields.pop('accreditation', None)
            self.fields.pop('pillar', None)
            self.fields['company'].disabled = True
            self.fields['company'].queryset = Company.objects.filter(
                company_name = user.company)
            self.initial['company'] = user.company

    class Meta:
        model = Calibration_Report_Notes
        fields = '__all__'
        exclude = ('calibration_type', 'who_created_note')
