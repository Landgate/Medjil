#instruments
import uuid
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.core.validators  import MaxValueValidator, MinValueValidator, DecimalValidator, RegexValidator
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from datetime import date
from accounts.models import Company
###################################################################
######################## BARCODE RANGE ############################
###################################################################
alphanumeric = RegexValidator(r'^[A-Z]*$', 'Only capital letters are allowed')

class Country(models.Model):
    name = models.CharField(max_length=40, unique=True,
                            help_text = "Enter the full name of Country, e.g, Australia",)

    def __str__(self):
        return self.name

class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=40, 
                            help_text = "Enter the full name of State/Region, e.g., Western Australia",
                            verbose_name = 'State')
    statecode =  models.CharField(max_length=3, 
                                    null=True,
                                    validators = [alphanumeric], 
                                    help_text = "Enter State Code with a max. of three letters, e.g., WA",
                                    verbose_name = 'State Code')
    class Meta:
        unique_together = ('country','name')

    def __str__(self):
        return self.name

class Locality(models.Model):
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=40, 
                            help_text = "Enter locality or suburb name, e.g., Boya",
                            verbose_name = 'Locality/Suburb')
    postcode =  models.IntegerField(null=True,
                                    help_text = "Enter Postal Code, e.g., 6056", 
                                    verbose_name = 'Post Code')
    class Meta:
        unique_together = ('state','name')

    def __str__(self):
        return f'{self.name} {self.postcode}'

        
    def save(self, *args, **kwargs):
        self.postcode =  '{:05d}'.format(self.postcode)
        super(Locality, self).save(*args, **kwargs)


def get_upload_to_location(instance, filename):
    creation_date = date.today().strftime('%Y-%m-%d')
    return '%s/%s/%s/%s/%s' % ('CalibrationSite', instance.site_type.capitalize(), instance.state.statecode, instance.site_name, creation_date+'-'+ filename)


class CalibrationSite(models.Model):
    site_types = (
                (None, '--- Select Type ---'),
                # ('edm_lab', 'EDM Calibration Laboratory'),
                ('baseline','EDM Calibration Baseline'),
                ('staff_lab', 'Staff Calibration Laboratory'),
                ('staff_range','Staff Calibration Range'),               
                )
    site_type = models.CharField(max_length=20,
                                choices=site_types, 
                                null=True,
                                blank=True,
                                verbose_name = 'Site Type')

    site_name = models.CharField(max_length=100, 
                                    help_text = "Name for the Calibration Site", 
                                    unique = True,
                                    verbose_name = 'Site Name')
    site_address = models.CharField(max_length=100, 
                                        null = True,
                                        help_text = "Address for the Calibration Site, e.g., Kent Street, Curtin University",
                                        verbose_name = 'Site Address')
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True,
                                    help_text = "Add/select a Country",
                                    verbose_name = 'Country',
                                    )
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True,
                                    help_text = "Add/select a State/Region",
                                    verbose_name = 'State/Region',
                                    ) 
    locality = models.ForeignKey(Locality, on_delete=models.SET_NULL, null=True,
                                    help_text = "Add/select the location of Site",
                                    verbose_name = 'Locality/Suburb',
                                    )  
    no_of_pillars = models.IntegerField(null = True, blank=True,
                                        help_text = "Enter the number of pins or baseline pillars, if applicable",
                                        verbose_name = 'Number of Pillars/Pins')
    operator = models.ForeignKey(Company, on_delete=models.RESTRICT, null=True, blank=True,
                                    help_text = "Select the site operator",
                                    verbose_name = 'Authority',
                                    )  
    description = models.TextField(blank=True, null=True)                                                                   
    site_access = models.FileField(upload_to = get_upload_to_location,
                                        null=True, 
                                        help_text = "Upload a pdf diagram showing an access to the location",
                                        verbose_name= 'Access Summary')

    site_config = models.FileField(upload_to = get_upload_to_location,
                                        null=True,
                                        help_text = "Upload a pdf diagram showing the location of pins or pillars",
                                        verbose_name= 'Site Configuration')
    # Status - Good, damaged, destroyed, 
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
            if self.site_access:
                return getattr(self.site_access, 'url', None)
            return None
    
    @property
    def config_url(self):
            """
            Return url if self.site_config is not None, 
            'url' exist and has a value, else, return None.
            """
            if self.site_config:
                return getattr(self.site_config, 'url', None)
            return None

# pin_validate = RegexValidator(r'^[0-9]{1,2}$', 'Only two digits are allowed')


# class PinsForRange(models.Model):
#     site_id = models.ForeignKey(CalibrationSite,
#                  limit_choices_to={'site_type__exact': 'staff_range'},
#                  on_delete = models.RESTRICT, null = False,
#                  verbose_name = 'Site Name')
#     pin_number = models.CharField(max_length=2,
#                     unique = True,
#                     help_text="Enter pin numbers as an integer, e.g., 1",
#                     validators = [pin_validate],
#                     verbose_name= 'Pin/Pillar Number')
#     height = models.FloatField(null=True, 
#                                 blank=True,
#                                 validators=[MinValueValidator(-30), MaxValueValidator(10000)],
#                                 help_text = "Enter the AHD, if known")
    
#     def __str__(self):
#         return f'{self.pin_number} - {self.site_id}'


class Pillar(models.Model):
    site_id = models.ForeignKey(CalibrationSite,
                #  limit_choices_to={'site_type__exact': 'baseline'},
                 on_delete = models.CASCADE, null = False,
                 verbose_name = 'Site Name')
    name = models.CharField(max_length=25, 
                            help_text="e.g., 1", 
                            verbose_name= 'Pillar/Pin No')
    order = models.CharField(max_length=25, 
                            blank = True,
                            verbose_name= 'formatted name')
    easting = models.DecimalField(null=True, blank=True,
                            max_digits=9, 
                            decimal_places=3,
                            validators=[MinValueValidator(300000), MaxValueValidator(900000)],
                            help_text="MGA2020 Easting (m). eg., 395006.085")
    northing = models.DecimalField(null=True, blank=True,
                            max_digits=10, 
                            decimal_places=3,
                            validators=[MinValueValidator(3000000), MaxValueValidator(10000000)],
                            help_text="MGA2020 Northing (m). eg., 6458541.334")
    height = models.FloatField(null=True, 
                                blank=True,
                                validators=[MinValueValidator(-30), MaxValueValidator(10000)],
                                help_text = "Enter the orthometic height, if known")
    zone = models.PositiveSmallIntegerField(null=True, blank=True,
                            validators=[MinValueValidator(1), MaxValueValidator(60)],
                            help_text = "Grid Zone, if applicable")

    class Meta:
        ordering = ['site_id','order']
        unique_together = ('site_id','name',)
        
    @property
    def format_name(self):
        num = ''.join([str(s) for s in f'{self.name}' if s.isdigit()])
        return f'{self.name}'.replace(num,num.zfill(3))

    def save(self, *args, **kwargs):
         self.order = self.format_name
         super(Pillar, self).save(*args, **kwargs)

    # def get_absolute_url(self):
    #     return reverse('baseline_calibration:pillar-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.site_id} - Pillar/Pin {self.name}'
