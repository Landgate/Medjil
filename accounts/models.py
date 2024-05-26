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
from django.utils.translation import gettext_lazy as _

import hashlib
import uuid
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django.utils import timezone

from common_func.validators import validate_profanity

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

class MedjilTOTPDeviceAdmin(TOTPDeviceAdmin):
    list_display = TOTPDeviceAdmin.list_display + ['created_at', 'last_used_at']
    
    def name(self, obj):
        # return the value of the field you want to display
        return obj.name
        name.short_description = 'Device Name'
        
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['name'].label = 'Device Name'
        return form  


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
        verbose_name='CSK - Company Secret Key',
        help_text='Users aleady registerd with this company have access to this key')

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name
    
        
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
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email.lower()
    

class Calibration_Report_Notes(models.Model):
    company = models.ForeignKey(Company, on_delete = models.CASCADE, null = False)
    report_types = (
        ('B','Baseline Calibration'),
        # ('R','Range Calibration'),
        ('E', 'EDMI Calibration'),
        # ('S', 'Staff Calibration')
        )
    report_type = models.CharField(max_length=1,
        choices=report_types,
        help_text="Report type that the notes will be added to",
        unique=False,
        )
    note_types = (
        ('M','All Reports'),
        ('C','Company Specific'),
        )
    note_type = models.CharField(max_length=1,
        choices=note_types,
        help_text="Notes can be either company specific or appear on all users reports",
        unique=False,
        )    
    note = models.TextField(
        null = False, blank = False,
        verbose_name= 'Report Note',
        help_text="Notes will be created at the end of each report")

    class Meta:
        ordering = ['company','report_type','note_type']

    def __str__(self):
        return f'{self.pk}. {self.company} - {self.get_report_type_display()} ({self.get_note_type_display()})'
    
    
    
    
    
    
    
    
    
    
    
    
    