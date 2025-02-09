'''
File: models.py
App: calibrationsitebooking
Directory: Medjil/calibrationsitebooking/models.py

'''

from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from accounts.models import Location, CustomUser
from calibrationsites.models import CalibrationSite
# Create your models here.
CALIB_CHOICES = (
    (None, '--- Select Type ---'),
    ('Site Calibration', (
        ('baseline', 'EDM Baseline'),
        ('range', 'Staff Range'),
    )),
    ('Instrument Calibration', (
        ('edmi', 'Electronic Distance Measurement'),
        ('staff', 'Barcoded Staff'),
    )),
)

TIME_CHOICES = (
    (None, '--- Select Time ---'),
    ('08:00', '8 AM - 12 PM'),
    ('13:00', '1:00 PM - 5:00 PM'),
)

def validate_future_date(value):
    if value < datetime.now().date():
        raise ValidationError('You cannot select a date in the past.')
    
class CalibrationSiteBooking(models.Model):
    calibration_type = models.CharField(max_length=24,
                                choices=CALIB_CHOICES,
                                null=True,
                                verbose_name = 'Calibration Type')

    location = models.ForeignKey(Location,
                                on_delete=models.CASCADE,
                                null = True,
                                verbose_name = 'Location')
    site_id = models.ForeignKey(
        CalibrationSite, 
        on_delete = models.CASCADE,
        blank = True, null = True, 
        help_text = "Select the calibration site.",
        verbose_name = 'Calibration Site')
    job_number = models.CharField(
        max_length=15, 
        help_text = "Enter a job number, e.g., JN20222511",
        verbose_name = 'Job Number')   
    observer = models.ForeignKey(CustomUser, 
                                on_delete=models.SET_NULL, 
                                null=True)
    calibration_date = models.DateField(
        validators = [validate_future_date],
        help_text = "Date of calibration",
        null=True)
    calibration_time = models.CharField(
        max_length=10, 
        choices=TIME_CHOICES,)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['-calibration_date', 'calibration_time', 'location','site_id']
        unique_together = ('site_id','calibration_date', 'calibration_time')

