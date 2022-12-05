from django import forms
from django.db.models import Q
from instruments.models import Staff, DigitalLevel
from .models import StaffCalibrationRecord
from calibrationsites.models import CalibrationSite

# Create Forms
class StaffCalibrationRecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(StaffCalibrationRecordForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner=user.company)
            self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner=user.company)
        self.fields['inst_level'].empty_label = '--- Select one ---'
        self.fields['inst_staff'].empty_label = '--- Select one ---'

    site_id = forms.ModelChoiceField(empty_label='Select one of the following',
                                required=True,
                                queryset=CalibrationSite.objects.all(),
                                widget=forms.Select(),
                                label = 'Calibration Site')
    class Meta:
        model = StaffCalibrationRecord
        fields = '__all__'
        exclude = ('id','field_file', 'field_book', 'observer_isme', 'observer',)
        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'help_text':'Select a date', 'type':'date'}),
            'calibration_report' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'}),
            'field_book' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'})
        }

# Calibration Form without Staff Number
class StaffCalibrationRecordFormOnTheGo(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(StaffCalibrationRecordFormOnTheGo, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner=user.company)
            self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner=user.company)
        self.fields['inst_level'].empty_label = '--- Select one ---'
        # self.fields['inst_staff'].empty_label = '--- Select one ---'

    site_id = forms.ModelChoiceField(empty_label='Select one of the following',
                                required=True,
                                queryset=CalibrationSite.objects.filter(Q(site_type = 'staff_range') | Q(site_type = 'staff_lab')),
                                widget=forms.Select(), 
                                label = 'Calibration Site')
    class Meta:
        model = StaffCalibrationRecord
        fields = '__all__'
        exclude = ('id', 'inst_staff', 'field_file', 'field_book', 'observer_isme', 'observer',)
        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'help_text':'Select a date', 'type':'date'}),
            'calibration_report' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'}),
            'field_book' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'})
        }

class StaffCalibrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(StaffCalibrationForm, self).__init__(*args, **kwargs)
        if not user.is_staff:
            self.fields['inst_staff'].queryset = Staff.objects.filter(staff_owner=user.company)
            self.fields['inst_level'].queryset = DigitalLevel.objects.filter(level_owner=user.company)
            self.fields['site_id'].queryset = CalibrationSite.objects.filter(site_type = 'staff_range')
            
        self.fields['site_id'].empty_label = '--- Select one ---'
        self.fields['inst_staff'].empty_label = '--- Select one ---'
        self.fields['inst_level'].empty_label = '--- Select one ---'

    start_temperature = forms.FloatField(help_text = "Temperature at the start of observation.")
    end_temperature = forms.FloatField(help_text = "Temperature at the end of observation.")
    class Meta:
        model = StaffCalibrationRecord
        fields = ['site_id','job_number','inst_staff','inst_level','start_temperature','end_temperature', 'field_file','field_book','observer_isme','observer','calibration_date']
        # fields = '__all__'
        exclude = ('id','correction_factor', 'standard_temperature','observed_temperature', 'calibration_report',)
        widgets = {
            'calibration_date': forms.DateInput(format=('%d-%m-%Y'), attrs={'help_text':'Select a date', 'type':'date'}),
            'field_file' : forms.FileInput(attrs={'accept' : '.csv'}),
            'field_book' : forms.FileInput(attrs={'accept' : '.pdf, .jpg, .tif'})
        }

