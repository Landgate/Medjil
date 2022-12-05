from django.forms import ModelForm
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UserCreationForm, UserChangeForm


from .models import CustomUser, Company,  Calibration_Report_Notes

class SignupForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    company = forms.ModelChoiceField(empty_label='Choose your firm/company',
                                    queryset=Company.objects.all(),
                                    widget=forms.Select())
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'company', 'password1', 'password2')
    
    def clean_email(self):
        return self.cleaned_data.get('email').lower()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        password_validation.validate_password(self.cleaned_data.get('password1'), None)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomUserChangeForm(ModelForm):
    # password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = ['email', 'company']

    # def clean_password(self):
    #     return self.initial["password"]

class LoginForm(forms.Form): 
    email = forms.EmailField(widget=forms.TextInput(
        attrs={'class': 'form-control','type':'text','name': 'email','placeholder':'Email address'}), 
        label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class':'form-control','type':'password', 'name': 'password','placeholder':'Password'}),
        label='Password')

    class Meta:
        fields = ['email', 'password']
        # widgets = {
        #     'password': forms.PasswordInput(attrs={'placeholder':'********','autocomplete': 'off','data-toggle': 'password'}), 
        # }
    
    def clean_email(self):
        return self.cleaned_data.get('email').lower()

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
        super(calibration_report_notesForm, self).__init__(*args, **kwargs) 
        self.initial['company'] = user.company
        if not user.is_staff:
            self.fields['company'].disabled = True

    class Meta:
        model = Calibration_Report_Notes
        fields = '__all__'
        exclude = ('report_type',)
