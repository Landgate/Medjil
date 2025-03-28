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
App: edm_calibration
Directory: Medjil/edm_calibration/models.py

'''
from django.db import models
from django.core.validators  import MaxValueValidator, MinValueValidator
from django.db.models import Q
from datetime import date

from baseline_calibration.models import (
    Accreditation,
    Uncertainty_Budget,
    Pillar_Survey)
from common_func.validators import (
    validate_profanity,
    validate_csv_text,
    validate_file_size)
from instruments.models import (
    EDM_Inst,
    Prism_Inst,
    Mets_Inst, 
    EDMI_certificate)
from calibrationsites.models import (
    CalibrationSite,
    Pillar)

# Create your models here.
def get_upload_to_location(instance, filename):
    creation_date = date.today().strftime('%Y-%m-%d')
    return '%s/%s/%s/%s/%s' % (
        'edmi_calibration', 
        instance.site.state.statecode.capitalize(),
        instance.site.site_name, 
        instance.edm.edm_specs.edm_owner.company_abbrev, 
        creation_date+'-'+ filename)

class uPillarSurvey(models.Model):
    site = models.ForeignKey(
        CalibrationSite, on_delete = models.PROTECT, null = True, blank = True,
        help_text="Select the baseline used for the calibration")
    auto_base_calibration = models.BooleanField(
        default=True,
        verbose_name = 'Auto select corresponding calibration of this baseline',
        help_text="Auto select will use the most recent certified distances dated prior to this EDMI Calibration survey date")
    calibrated_baseline = models.ForeignKey(
        Pillar_Survey, on_delete = models.PROTECT, null = True,
        help_text="Baseline certified distances")
    survey_date = models.DateField()
    computation_date = models.DateField()
    observer = models.CharField(
         validators=[validate_profanity],max_length=25, null = True, blank = True)
    weather_type = (
        ('Sunny/Clear','Sunny/Clear'),
        ('Partially cloudy','Partially cloudy'),
        ('Cloudy', 'Cloudy'),
        ('Overcast', 'Overcast'),
        ('Drizzle','Drizzle'),
        ('Raining','Raining'),
        ('Stormy','Stormy'),
        )
    weather = models.CharField(max_length=25,
              choices=weather_type,
              help_text="Weather conditions",
              )
    job_number = models.CharField(max_length=25,
              help_text="Job reference eg., JN 20212216",
              validators=[validate_profanity],
              blank=True, null = True,
              verbose_name= 'Job Number/Reference'
              )
    comment = models.CharField(max_length=256, blank = True, null=True)
    
    edm = models.ForeignKey(EDM_Inst, on_delete = models.PROTECT,
              help_text="EDM used for survey",
              verbose_name= 'EDM')
    prism = models.ForeignKey(Prism_Inst, on_delete = models.PROTECT,
              help_text="Prism used for survey")
    mets_applied = models.BooleanField(default=True,
              verbose_name= 'Atmospheric corrections have been applied to imported EDM data',
              help_text="Meterological corrections have been applied in the EDM instrument.")
    
    thermometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT,
              limit_choices_to={'mets_specs__inst_type': 'thermo'},
              help_text="Thermometer used for survey",
              related_name="ufield_thermometer")
    barometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT,
             limit_choices_to={'mets_specs__inst_type': 'baro'},
             help_text="Barometer used for survey",
             related_name="ufield_barometer")
    hygrometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, blank=True, null = True,
             limit_choices_to={'mets_specs__inst_type': 'hygro'},
             help_text="Hygrometer, if used for survey",
             related_name="ufield_hygrometer")
    thermo_calib_applied = models.BooleanField(default=True,
              verbose_name= 'thermometer calibration corrections applied or not required',
              help_text="The thermometer calibration correction"
               " has been applied prior to data import.")
    baro_calib_applied = models.BooleanField(default=True,
              verbose_name= 'barometer calibration corrections applied or not required',
              help_text="The barometer calibration correction has been applied prior to data import.")
    hygro_calib_applied = models.BooleanField(default=True,
              verbose_name= 'Hygrometer calibration corrections applied or not required',
              help_text="The hygrometer correction has been applied prior to data import.")
    
    uncertainty_budget = models.ForeignKey(Uncertainty_Budget, on_delete = models.PROTECT,
              help_text="Preset uncertainty budget")
    scalar = models.DecimalField(max_digits=6, decimal_places=2, default=1.00,
              verbose_name= 'a-priori scalar',
              help_text="a-priori standard uncertainties are multiplied by the a-priori scalar")
    apply_lum = models.BooleanField(default=False,
              verbose_name= 'Apply LUM to underestimated uncertainties',
              help_text="The Least Uncertainty of Measurement specified in the company's accreditation is applied if a posteriori uncertainties are less than LUM.")
    e_accreditation = models.ForeignKey(
        Accreditation, on_delete = models.SET_NULL, 
        null = True, blank=True,
        help_text="Accreditaion and LUM for EDM Instrumentation calibration.")
    outlier_criterion = models.DecimalField(max_digits=2, decimal_places=1, default=2,
              validators=[MinValueValidator(0), MaxValueValidator(5)],
              help_text="Number of standard deviations for outlier detection threashold.",
              verbose_name = 'Rejection Criteria for outlier detection')
    test_cyclic = models.BooleanField(default=False,
              verbose_name= 'Test for cyclic errors',
              help_text="Test Instrument For Cyclic Errors (Nb. Instrument Parameters Require 'Unit Lenght'")
    fieldnotes_upload = models.FileField(upload_to=get_upload_to_location,
              null=True,
              blank=True,
              max_length=1000,
              help_text="Uploaded copy of digital records or scanned fieldnotes.",
              validators=[validate_file_size],
              verbose_name= 'Field record') 
    
    certificate = models.OneToOneField(
         EDMI_certificate, on_delete = models.SET_NULL , null = True, blank=True)
    
    data_entered_person = models.CharField(
        validators=[validate_profanity],max_length=25,null=True, blank=True)
    data_entered_position = models.CharField(
        validators=[validate_profanity],max_length=25,null=True, blank=True)
    data_entered_date = models.DateField(null=True, blank=True)
    data_checked_person = models.CharField(
        validators=[validate_profanity],max_length=25,null=True, blank=True)
    data_checked_position = models.CharField(
        validators=[validate_profanity],max_length=25,null=True, blank=True)
    data_checked_date = models.DateField(null=True, blank=True)
    
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
       ordering = ['edm','survey_date']
       constraints = [
           models.CheckConstraint(
               check=Q(site__isnull=False) | Q(calibrated_baseline__isnull=False),
               name='Both site and calibrated baseline fields can not be null')
           ]
       verbose_name = "EDMI Calibration Surveys"
    
    def __str__(self):
       return f'{self.job_number} - {self.edm} ({self.survey_date})'   
    
    def get_pillars_used(self):
        # returns a unique list of the pillar id's for pillars used in survey
        edm_observations_obj = self.uedmobservation_set.distinct('from_pillar','to_pillar')
        distinct_from = edm_observations_obj.values_list('from_pillar', flat=True).distinct()
        distinct_to = edm_observations_obj.values_list('to_pillar', flat=True).distinct()
        
        # Combine the two lists and remove duplicates
        combined_distinct = list(set(distinct_from) | set(distinct_to))
        pillars_used = self.site.pillars.filter(
            Q(id__in=combined_distinct)).order_by('order')
        return pillars_used
   
    def delete(self, *args, **kwargs):
        try:
            self.certificate.delete()
        except:
            pass
        super().delete(*args, **kwargs)
    

class uEdmObservation(models.Model):
    pillar_survey = models.ForeignKey(
        uPillarSurvey, on_delete = models.CASCADE)
    
    from_pillar = models.ForeignKey(
        Pillar, on_delete = models.CASCADE)
    to_pillar = models.ForeignKey(
        Pillar, on_delete = models.CASCADE, related_name='+')
    
    inst_ht = models.DecimalField(
        max_digits=4, decimal_places=3,
        verbose_name= 'Instrument height')
    tgt_ht = models.DecimalField(
        max_digits=4, decimal_places=3,
        verbose_name= 'Target height')
    
    raw_slope_dist = models.DecimalField(
        max_digits=29, decimal_places=25,
        validators=[MinValueValidator(1), MaxValueValidator(1500)],
        verbose_name= 'slope distance')
    
    raw_temperature = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(50.0)],
        null = True, blank = True)
    raw_pressure = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(1500.0)],
        null = True, blank = True)
    raw_humidity = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(100.0)],
        null = True, blank = True)
    use_for_distance = models.BooleanField(
        default=True,
        verbose_name= 'Use for surveying the certified distances',
        help_text="This observation (will) / (will not) be used for determining the calibration of the edmi.")
    
    class Meta:
       ordering = ['pillar_survey','from_pillar','to_pillar']
    
    def __str__(self):
       return f'({self.pillar_survey}): {self.from_pillar} → {self.to_pillar})'
   
    
class Intercomparison(models.Model):
    edm = models.ForeignKey(
        EDM_Inst, on_delete = models.CASCADE,
        help_text="EDM used for interlaboratory comparison",
        verbose_name= 'EDM')
    prism = models.ForeignKey(
        Prism_Inst, on_delete = models.CASCADE,
        help_text="Prism used for interlaboratory comparison",
        verbose_name= 'Prism')
    from_date = models.DateField()
    to_date = models.DateField()
    job_number = models.CharField(max_length=25,
              help_text="Job reference eg., JN 20212216",
              validators=[validate_profanity],
              blank=True, null = True,
              verbose_name= 'Job Number/Reference'
              )
    sample_distances = models.CharField(
        validators=[validate_csv_text],
        max_length=255,
        default="20, 300, 600",
        help_text="Comma seperated list of distances",
        verbose_name= 'Sample Distances (m)')
    html_report = models.TextField(blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
       ordering = ['edm']
       constraints = [
           models.CheckConstraint(
               check=(models.Q(to_date__gt=models.F('from_date'))),
               name='The from date must be before the to date'),
           ]
       verbose_name= 'Interlaboratory comparison'
    
    def __str__(self):
       return f'{self.edm}'
