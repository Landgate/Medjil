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
from django.db import models
from django.urls import reverse
from PIL import Image as PilImage
from common_func.validators import validate_file_size
from django.conf import settings
from urllib.parse import urljoin
# Create your models here.
from accounts.models import CustomUser
from accounts.models import Location
from calibrationsites.models import CalibrationSite
# Define UserGuide Type

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


def get_upload_to_content(instance, filename):
    #filename = instance.calibration_date.strftime('%Y%m%d') + '-' + filename
    return '%s/%s/%s/%s' % ('CalibrationInstruction', 
                                instance.location.name, 
                                instance.calibration_type, 
                                filename)

class CalibrationGuide(models.Model):
    calibration_type = models.CharField(max_length=24,
                                choices=CALIB_CHOICES,
                                null=True,
                                verbose_name = 'Calibration Type')

    location = models.ForeignKey(Location,
                                on_delete=models.CASCADE,
                                null = True,
                                verbose_name = 'Location')
    title = models.CharField(max_length=200, 
                             help_text = 'e.g., EDMI Calibration in Western Australia')
    content_book = models.FileField(
        upload_to = get_upload_to_content,
        null = True, blank = True,
        validators=[validate_file_size],
        help_text = 'Upload a user guide or handbook in pdf format',
        verbose_name= 'User Guide')
    author = models.ForeignKey(CustomUser, 
                                on_delete=models.SET_NULL, 
                                null=True)
    pub_date = models.DateTimeField(auto_now_add=True, 
                                    null=True, 
                                    verbose_name = 'Published on')
    mod_date = models.DateTimeField(auto_now=True, 
                                    null=True, 
                                    verbose_name = 'Last Modified')

    class Meta:
        ordering = ['location','calibration_type']
        unique_together = ('location','calibration_type',)
        constraints = [models.UniqueConstraint(
            fields=['location','calibration_type'], name = 'unique_guide_instance',
            violation_error_message='The user guide for already exists for this location.'
            ),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def content_url(self):
        """
        Return url if self.site_access is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.content_book:
            return getattr(self.content_book, 'url', None)
        return None

def get_upload_to_medjil(instance, filename):
    return '%s/%s' % ('CalibrationInstruction',  
                                filename)   
class MedjilGuide(models.Model):
    title = models.CharField(max_length=200, 
                             help_text = 'e.g., Medjil User Guide')
    medjil_book = models.FileField(
        upload_to = get_upload_to_medjil,
        null = True, blank = True,
        validators=[validate_file_size],
        help_text = 'Upload a Medjil User Guide or handbook in pdf format',
        verbose_name= 'User Guide')
    author = models.ForeignKey(CustomUser, 
                                on_delete=models.SET_NULL, 
                                null=True)
    pub_date = models.DateTimeField(auto_now_add=True, 
                                    null=True, 
                                    verbose_name = 'Published on')
    mod_date = models.DateTimeField(auto_now=True, 
                                    null=True, 
                                    verbose_name = 'Last Modified')

    class Meta:
        ordering = ['title','author']
        unique_together = ('title','author',)
        constraints = [models.UniqueConstraint(
            fields=['title','author'], name = 'unique_medjil_instance',
            violation_error_message='The user guide for already exists for this location.'
            ),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def medjil_url(self):
        """
        Return url if self.site_access is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.medjil_book:
            return getattr(self.medjil_book, 'url', None)
        return None

CALIB_SITE_CHOICES = (
    (None, '--- Select Type ---'),
    ('baseline', 'EDM Baseline'),
    ('range', 'Staff Range'),
    )    
class MedjilGuideToSiteCalibration(models.Model):
    site_type = models.CharField(max_length=24,
                                choices=CALIB_SITE_CHOICES,
                                null=True,
                                verbose_name = 'Site Type')
    location = models.ForeignKey(Location,
                                on_delete=models.CASCADE,
                                null = True,
                                verbose_name = 'Location')
    title = models.CharField(max_length=200, 
                             help_text = 'e.g., Medjil User Guide to Staff Calibration')
    content_book = models.FileField(
        upload_to = get_upload_to_medjil,
        null = True, blank = True,
        validators=[validate_file_size],
        help_text = 'Upload a User Guide or handbook in pdf format',
        verbose_name= 'User Guide')
    author = models.ForeignKey(CustomUser, 
                                on_delete=models.SET_NULL, 
                                null=True)
    pub_date = models.DateTimeField(auto_now_add=True, 
                                    null=True, 
                                    verbose_name = 'Published on')
    mod_date = models.DateTimeField(auto_now=True, 
                                    null=True, 
                                    verbose_name = 'Last Modified')

    class Meta:
        ordering = ['location','site_type']
        unique_together = ('location','site_type',)
        constraints = [models.UniqueConstraint(
            fields=['location','site_type'], name = 'unique_site_instance',
            violation_error_message='The user guide for already exists for this location.'
            ),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def content_url(self):
        """
        Return url if self.site_access is not None, 
        'url' exist and has a value, else, return None.
        """
        if self.content_book:
            return getattr(self.content_book, 'url', None)
        return None
    