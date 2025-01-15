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
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.core.validators  import RegexValidator
from django.core.exceptions import ValidationError

import hashlib
import uuid
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django.utils import timezone

from common_func.validators import validate_profanity

alphanumeric = RegexValidator(r'^[A-Z]*$', 'Only capital letters are allowed')
# Create your models here.
class MedjilTOTPDevice(TOTPDevice):
    # created_sat = models.DateTimeField(auto_now_add=True, null=True)
    # last_used_sat = models.DateTimeField(null=True, blank=True)
    session_key = models.UUIDField(blank=True, null=True)

    def name(self, obj):
        # return the value of the field you want to display
        return obj.name
        name.short_description = 'Device Name'

    def verify_token(self, token):
        verified = super().verify_token(token)
        if verified:
            self.last_used_at = timezone.now()
            self.save()
        return verified
    
    def rotate_session_key(self):
        self.session_key = uuid.uuid4()
        self.save(update_fields=['session_key'])

def generate_short_hash():
    # Generate a UUID, hash it, and take the first 8 characters
    uuid_hash = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:8]
    return uuid_hash

class Company(models.Model):
    company_name = models.CharField(
        validators=[validate_profanity],
        max_length=200, unique=True)
    company_abbrev = models.CharField(
        validators=[validate_profanity],
        max_length=20)
    company_secret_key = models.CharField(
        max_length=8,
        default=generate_short_hash,
        blank=True, null=True,
        verbose_name='CSK - Company Secret Key',
        help_text='Users aleady registerd with this company have access to this key')

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name
    
    def save(self, *args, **kwargs):
        self.company_abbrev = self.company_abbrev.upper()
        super().save(*args, **kwargs)  

class Location(models.Model):
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

    def __str__(self):
        return self.name
        
####### CUSTOM MANAGER TO MAKE EMAIL AS UNIQUE ID INSTEAD OF USERNAME ######
class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        # user.is_admin = False;
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)
    

class LowerCaseEmailField(models.EmailField):
    """
    Override email field to convert to lowercase
    """
    def to_lower_case(self, value):
        value = super(LowerCaseEmailField, self).to_lower_case(value)
        if isinstance(value, str):
            return value.lower()
        return value
    

class CustomUser(AbstractUser):
    company = models.ForeignKey(
        Company,
        on_delete = models.SET_NULL,
        blank = True,
        null = True,
    )

    username = None
    email = LowerCaseEmailField(
        _('email address'), 
        max_length = 150,
        unique=True,
        error_messages = {
            'unique': _("The user with that email address already exists.")
            }
    )

    locations =  models.ManyToManyField(Location, blank = True, help_text="Select the ones that applies to you. Hold down “Control”, or “Command” on a Mac, to select more than one.")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email.lower()
    
    def get_locations(self):
        return ", ".join([str(p) for p in self.locations.all()])
    
class Calibration_Report_Notes(models.Model):
    from calibrationsites.models import CalibrationSite, Pillar
    from baseline_calibration.models import Accreditation
    
    calibration_types = (
        ('B','Baseline Calibration'),
        # ('R','Range Calibration'),
        ('E', 'EDMI Calibration'),
        # ('S', 'Staff Calibration')
        )
    who_created_note = models.ForeignKey(
        Company, on_delete = models.CASCADE,
        help_text="Used for filtering the endnotes home page")
    
    calibration_type = models.CharField(
        max_length=1,
        choices=calibration_types,
        help_text="Report type that the notes will be added to",)
    
    verifying_authority = models.ForeignKey(
        Company, on_delete = models.CASCADE,
        help_text="Notes will be created on all reports related to this Verifying Authority",
        related_name='verifying_authority_notes',
        null = True, blank = True)
    
    accreditation = models.ForeignKey(
        Accreditation, on_delete = models.CASCADE,
        help_text="Notes will be created on all reports related to this Verifying Authority",
        related_name='accreditation_notes',
        null = True, blank = True)
    
    company = models.ForeignKey(
        Company, on_delete = models.CASCADE, 
        help_text="Notes will be created on all reports related to this Company",
        related_name='company_notes',
        null = True, blank = True)
    
    site = models.ForeignKey(
        CalibrationSite, on_delete = models.CASCADE,
        help_text="Notes will be created on all reports related to this Site",
        related_name='site_notes',
        null = True, blank = True)
    
    pillar = models.ForeignKey(
        Pillar, on_delete = models.CASCADE,
        help_text="Notes will be created on all reports related to this Pillar",
        related_name='pillar_notes',
        null = True, blank = True)
   
    note = models.TextField(
        null = False, blank = False,
        verbose_name= 'Report Note',
        help_text="Notes will be created at the end of each report")

    class Meta:
        ordering = ['verifying_authority','company','site', 'pillar']

    def __str__(self):
        return f'{self.pk}. {self.company} - {self.get_report_type_display()} ({self.get_note_type_display()})'
    
    
    
    
    
    
    
    
    
    
    
    
    