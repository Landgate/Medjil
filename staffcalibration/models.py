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

File: models.py
App: staffcalibration
Directory: Medjil/staffcalibration/models.py

'''
import uuid
from django.db import models
from django.db.models import Q
from django.core.validators  import MaxValueValidator, MinValueValidator
# import models
from instruments.models import Staff, DigitalLevel
from calibrationsites.models import CalibrationSite
from common_func.validators import validate_file_size
# Create your models here.

#####################################################################
##################### STAFF CALIBRATION CERTIFICATES ################
#####################################################################
def get_upload_to_fieldfile(instance, filename):
    filename = instance.calibration_date.strftime('%Y%m%d') + '-' + filename
    return 'StaffCalibration/%s/%s/FieldData/%s' % (instance.inst_staff.staff_owner.company_abbrev, instance.inst_staff.staff_type, filename)

def get_upload_to_fieldbook(instance, filename):
    filename = instance.calibration_date.strftime('%Y%m%d') + '-' + filename
    return 'StaffCalibration/%s/%s/FieldBook/%s' % (instance.inst_staff.staff_owner.company_abbrev, instance.inst_staff.staff_type, filename)

def get_upload_to_calibreport(instance, filename):
    filename = instance.calibration_date.strftime('%Y%m%d') + '-' + filename
    return 'StaffCalibration/%s/%s/CalibrationReport/%s' % (instance.inst_staff.staff_owner.company_abbrev, instance.inst_staff.staff_type, filename)

def get_upload_to_starrerror(instance, filename):
    filename = filename + '-' + instance.inst_staff.staff_number + '-' + instance.calibration_date.strftime('%Y%m%d') + '.svg'
    return 'StaffCalibration/%s/%s/CalibrationReport/%s' % (instance.inst_staff.staff_owner.company_abbrev, instance.inst_staff.staff_type, filename)

class StaffCalibrationRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for this calibration record')
    site_id = models.ForeignKey(
        CalibrationSite, 
        limit_choices_to=Q(site_type = 'staff_range') | Q(site_type = 'staff_lab'),
        on_delete = models.PROTECT, 
        null = True, blank = True,
        help_text = "Select the staff calibration range. Please contact Landgate, if it does not exist.",
        verbose_name = 'Calibration Site')
    job_number = models.CharField(
        max_length=15, 
        help_text = "Enter a job number, e.g., JN20222511",
        verbose_name = 'Job Number')   
    inst_staff = models.ForeignKey(
        Staff, 
        null=True,
        on_delete = models.PROTECT, 
        help_text = "Select staff.",
        verbose_name = 'Staff Number')
    inst_level = models.ForeignKey(
        DigitalLevel, 
        on_delete = models.PROTECT, 
        null = True, blank = True,
        help_text = "Select level.",
        verbose_name = 'Level Number')
    scale_factor = models.FloatField(
        null=True, 
        validators = [MinValueValidator(0.99), MaxValueValidator(1.003)],
        help_text = "Enter the correction factor provided in the Certificate.",
        verbose_name = "Scale Factor")
    grad_uncertainty = models.FloatField(
        null = True, blank = True,
        validators = [MinValueValidator(0), MaxValueValidator(0.1)],
        help_text = "Enter the graduation uncertainty, if provided in the certificate.",
        verbose_name = "Graduation Uncertainty")
    standard_temperature = models.FloatField(
        default=25.0, null = True, 
        help_text = "Temperature at which the Scale Factor is valid.")
    observed_temperature = models.FloatField(
        null = True, blank=True, 
        help_text = "Average temperature observed during the observation.")
        
    field_file = models.FileField(
        upload_to = get_upload_to_fieldfile,
        null=True,
        max_length=1000,
        validators=[validate_file_size],
        # blank=True,
        help_text = 'Upload the staff reading from the level instrument in CSV format',
        verbose_name= 'Field Data')
    field_book = models.FileField(
        upload_to = get_upload_to_fieldbook,
        null = True, blank = True,
        max_length=1000,
        validators=[validate_file_size],
        help_text = 'Upload the field book in pdf/jpg/tif format',
        verbose_name= 'Field Book')
    observer_isme = models.BooleanField(
        default=False, verbose_name = "I am the Observer")
    observer = models.CharField(
        max_length=50, null=True, blank=True)
    calibration_date = models.DateField(
        help_text = "Date of observation/measurement taken.",
        null=True)
    calibration_report = models.FileField(
        upload_to = get_upload_to_calibreport,
        null = True, blank = True,
        max_length=1000,
        validators=[validate_file_size],
        help_text = "Calibration report/certificate in pdf/jpg/tif format.",
        verbose_name= 'Calibration certificate')
    calibration_error = models.ImageField(
        upload_to = get_upload_to_starrerror,
        null = True, blank = True,
        help_text = "Staff errors svg format.",
        verbose_name= 'Staff Errors')
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['inst_staff', 'calibration_date']
        unique_together = ['inst_staff', 'calibration_date']
        verbose_name = "Barcode Staff Calibrations"

    def __str__(self):
        return f'{self.inst_staff.staff_number} ({self.calibration_date.strftime("%Y-%m-%d")})'
    def staff_type(self):
        return self.inst_staff.staff_type
    def staff_length(self):
        return self.inst_staff.staff_length

    @property
    def report_url(self):
        """
        Return url if self.calibration_report is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.calibration_report:
            return getattr(self.calibration_report, 'url', None)
        return None
    
    @property
    def field_url(self):
        """
        Return url if self.field_report is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.field_book:
            return getattr(self.field_book, 'url', None)
        return None
    @property
    def error_url(self):
        """
        Return url if self.calibration_error is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.calibration_error:
            return getattr(self.calibration_error, 'url', None)
        return None
# Adjustment
class AdjustedDataModel(models.Model):
    calibration_id = models.ForeignKey(
        StaffCalibrationRecord, 
        null = True,
        on_delete = models.CASCADE,
        verbose_name = 'Calibration Id')
    uscale_factor = models.FloatField(
        null=True, 
        validators = [MinValueValidator(0.99), MaxValueValidator(1.003)],
        help_text = "Enter the correction factor provided in the Certificate.",
        verbose_name = "Uncorrected Scale Factor")
    temp_at_sf1 = models.FloatField(
        null = True, help_text = "Temperature at which Scale Factor is 1.")
    staff_reading = models.JSONField(
        null=True, verbose_name = 'Staff Reading')
  
    def __str__(self):
        return f'{self.calibration_id.job_number} ({self.calibration_id.calibration_date.strftime("%Y-%m-%d")})'

    def job_number(self):
        return self.calibration_id.job_number

    def staff_number(self):
        return self.calibration_id.inst_staff.staff_number
    
    def staff_type(self):
        return self.calibration_id.inst_staff.staff_type
    
    def staff_length(self):
        return self.calibration_id.inst_staff.staff_length

    def level_number(self):
        return self.calibration_id.inst_level.level_number

    def calibration_date(self):
        return self.calibration_id.calibration_date