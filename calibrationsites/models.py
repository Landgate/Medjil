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
#instruments
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.core.validators  import MaxValueValidator, MinValueValidator, RegexValidator
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from datetime import date
from accounts.models import Company
from common_func.validators import validate_file_size

###################################################################
######################## BARCODE RANGE ############################
###################################################################
alphanumeric = RegexValidator(r'^[A-Z]*$', 'Only capital letters are allowed')

class Country(models.Model):
    name = models.CharField(
        max_length=40, unique=True,
        help_text="Enter the full name of Country, e.g, Australia",
    )

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=40,
        help_text="Enter the full name of State/Region, e.g., Western Australia",
        verbose_name='State'
    )
    statecode = models.CharField(
        max_length=3,
        null=True,
        validators=[alphanumeric],
        help_text="Enter State Code with a max. of three letters, e.g., WA",
        verbose_name='State Code'
    )

    class Meta:
        unique_together = ('country', 'name')

    def __str__(self):
        return self.name

class Locality(models.Model):
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True
    )
    state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(
        max_length=40,
        help_text="Enter locality or suburb name, e.g., Boya",
        verbose_name='Locality/Suburb'
    )
    postcode = models.IntegerField(
        null=True,
        help_text="Enter Postal Code, e.g., 6056",
        verbose_name='Post Code'
    )

    class Meta:
        unique_together = ('state', 'name')

    def __str__(self):
        return f'{self.name} {self.postcode}'

    def save(self, *args, **kwargs):
        self.postcode = '{:05d}'.format(self.postcode)
        super(Locality, self).save(*args, **kwargs)


def get_upload_to_location(instance, filename):
    creation_date = date.today().strftime('%Y-%m-%d')
    return '%s/%s/%s/%s/%s' % (
        'CalibrationSite', instance.site_type.capitalize(),
        instance.state.statecode, instance.site_name,
        creation_date+'-'+filename
    )

class CalibrationSite(models.Model):
    site_types = (
        (None, '--- Select Type ---'),
        ('baseline', 'EDM Calibration Baseline'),
        ('staff_lab', 'Staff Calibration Laboratory'),
        ('staff_range', 'Staff Calibration Range'),
    )
    site_type = models.CharField(
        max_length=20,
        choices=site_types,
        null=True,
        blank=True,
        verbose_name='Site Type'
    )
    site_name = models.CharField(
        max_length=100,
        help_text="Name for the Calibration Site",
        unique=True,
        verbose_name='Site Name'
    )
    site_statuses = (
        (None, '--- Select Status ---'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    )
    site_status = models.CharField(
        max_length=20,
        choices=site_statuses,
        null=True,
        blank=True,
        verbose_name='Site Status'
    )
    site_address = models.CharField(
        max_length=100,
        null=True,
        help_text="Address for the Calibration Site, e.g., Kent Street, Curtin University",
        verbose_name='Site Address'
    )
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True,
        help_text="Add/select a Country",
        verbose_name='Country',
    )
    state = models.ForeignKey(
        State, on_delete=models.SET_NULL, null=True,
        help_text="Add/select a State/Region",
        verbose_name='State/Region',
    )
    locality = models.ForeignKey(
        Locality, on_delete=models.SET_NULL, null=True,
        help_text="Add/select the location of Site",
        verbose_name='Locality/Suburb',
    )
    no_of_pillars = models.IntegerField(
        null=True, blank=True,
        help_text="Enter the number of pins or baseline pillars, if applicable",
        verbose_name='Number of Pillars/Pins'
    )
    operator = models.ForeignKey(
        Company, on_delete=models.PROTECT, null=True, blank=True,
        help_text="Select the site operator",
        verbose_name='Authority',
    )
    description = models.TextField(blank=True, null=True)
    site_access_plan = models.FileField(
        upload_to=get_upload_to_location,
        null=True,
        validators=[validate_file_size],
        help_text="Upload a pdf file showing an access to the location",
        verbose_name='Access Plan'
    )
    site_booking_sheet = models.FileField(
        upload_to=get_upload_to_location,
        null=True,
        validators=[validate_file_size],
        help_text="Upload a pdf file containing the booking sheet",
        verbose_name='Booking Sheet'
    )
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f'{self.site_name} ({self.state.statecode})'

    def get_absolute_url(self):
        return reverse('calibrationsites:site-detail', args=[str(self.id)])

    @property
    def access_url(self):
        """
        Return url if self.site_access is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.site_access_plan:
            return getattr(self.site_access_plan, 'url', None)
        return None
    
    
    @property
    def booking_url(self):
        """
        Return url if self.site_booking is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.site_booking_sheet:
            return getattr(self.site_booking_sheet, 'url', None)
        return None


class Pillar(models.Model):
    site_id = models.ForeignKey(
        CalibrationSite,
        on_delete=models.CASCADE, null=False,
        verbose_name='Site Name'
    )
    name = models.CharField(
        max_length=25,
        help_text="e.g., 1",
        verbose_name='Pillar/Pin No'
    )
    order = models.CharField(max_length=25, verbose_name='formatted name')
    easting = models.DecimalField(
        null=True, blank=True,
        max_digits=9,
        decimal_places=3,
        verbose_name='Easting [m]',
        validators=[MinValueValidator(160000), MaxValueValidator(900000)],
        help_text="MGA2020- e.g., 395006.085"
    )
    northing = models.DecimalField(
        null=True, blank=True,
        max_digits=10,
        decimal_places=3,
        verbose_name='Northing [m]',
        validators=[MinValueValidator(3000000), MaxValueValidator(10000000)],
        help_text="MGA2020- e.g., 6458541.334"
    )
    zone = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Grid Zone"
    )

    class Meta:
        ordering = ['site_id', 'order']
        unique_together = ('site_id', 'name',)

    @property
    def format_name(self):
        num = ''.join([str(s) for s in f'{self.name}' if s.isdigit()])
        return f'{self.name}'.replace(num, num.zfill(3))

    def __str__(self):
        return f'{self.site_id} - Pillar/Pin {self.name}'