from django.db import models
from django.core.validators  import MaxValueValidator, MinValueValidator, DecimalValidator
from django.conf import settings
from datetime import date

from baseline_calibration.models import (Uncertainty_Budget,
                                    Pillar_Survey)
from instruments.models import (EDM_Inst, 
                                Prism_Inst, Mets_Inst)
from calibrationsites.models import (CalibrationSite, 
                            Pillar)

# Create your models here.
def get_upload_to_location(instance, filename):
    creation_date = date.today().strftime('%Y-%m-%d')
    return '%s/%s/%s/%s/%s' % ('EDMICalibration', 
                            instance.site.state.statecode.capitalize(),
                            instance.site.site_name, 
                            instance.edm.edm_specs.edm_owner.company_abbrev, 
                            creation_date+'-'+ filename)

class uPillar_Survey(models.Model):
   site = models.ForeignKey(CalibrationSite, on_delete = models.PROTECT, null = False,
             help_text="Baseline certified distances")   
   auto_base_calibration = models.BooleanField(default=True)
   calibrated_baseline = models.ForeignKey(Pillar_Survey, on_delete = models.SET_NULL, null = True,
             help_text="Baseline certified distances")
   survey_date = models.DateField(null=False, blank=False)
   computation_date = models.DateField(null=False, blank=False)
   observer = models.CharField(max_length=25,
             null = True,
             blank = True,
             )
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
             unique=False,
             )
   job_number = models.CharField(max_length=25,
             help_text="Job reference eg., JN 20212216",
             unique=False,
             )

   edm = models.ForeignKey(EDM_Inst, on_delete = models.PROTECT, null = False,
             help_text="EDM used for survey")
   prism = models.ForeignKey(Prism_Inst, on_delete = models.PROTECT, null = False,
             help_text="Prism used for survey")
   mets_applied = models.BooleanField(default=True,
             verbose_name= 'Atmospheric corrections applied to EDM data',
             help_text="Meterological corrections have been applied in the EDM instrument.")

   thermometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, null = False,
             limit_choices_to={'mets_specs__mets_model__inst_type': 'thermo'},
             help_text="Thermometer used for survey",
             related_name="ufield_thermometer")
   barometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, null = False,
            limit_choices_to={'mets_specs__mets_model__inst_type': 'baro'},
            help_text="Barometer used for survey",
            related_name="ufield_barometer")
   hygrometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, blank=True, null = True,
            limit_choices_to={'mets_specs__mets_model__inst_type': 'hygro'},
            help_text="Hygrometer, if used for survey",
            related_name="ufield_hygrometer")
   thermo_calib_applied = models.BooleanField(default=True,
             verbose_name= 'thermometer calibration corrections applied',
             help_text="The thermometer calibration correction"
              " has been applied prior to data import.")
   baro_calib_applied = models.BooleanField(default=True,
             verbose_name= 'barometer calibration corrections applied',
             help_text="The barometer calibration correction has been applied prior to data import.")
   hygro_calib_applied = models.BooleanField(default=True,
             verbose_name= 'Hygrometer calibration corrections applied',
             help_text="The hygrometer correction has been applied prior to data import.")

   uncertainty_budget = models.ForeignKey(Uncertainty_Budget, on_delete = models.PROTECT, null = False,
             help_text="Preset uncertainty budget")
   scalar = models.DecimalField(max_digits=6, decimal_places=2, default=1.00,
             verbose_name= 'a-priori scalar',
             help_text="a-priori standard uncertainties are multiplied by the a-priori scalar")
   outlier_criterion = models.DecimalField(max_digits=2, decimal_places=1, default=2,
             validators=[MinValueValidator(0), MaxValueValidator(5)],
             help_text="Number of standard deviations for outlier detection threashold.")
   test_cyclic = models.BooleanField(default=False,
             verbose_name= 'Test for cyclic errors',
             help_text="Test Instrument For Cyclic Errors (Nb. Instrument Parameters Require 'Unit Lenght'")
   fieldnotes_upload = models.FileField(upload_to=get_upload_to_location,
             null=True,
             blank=True, 
             verbose_name= 'Scanned fieldnotes')
   variance = models.FloatField(blank = True, null=True,
             help_text="Variance of least squares adjustment of the calibration")
   degrees_of_freedom = models.IntegerField(blank = True, null=True,
             validators = [MinValueValidator(0), MaxValueValidator(500)],
             help_text="Degrees of freedom of calibration")
   k = models.FloatField(blank = True, null=True,
             verbose_name= 'coverage factor')
    
   uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
   modified_on = models.DateTimeField(auto_now=True, null=True)

   class Meta:
      ordering = ['edm','survey_date']

   def __str__(self):
      return f'{self.job_number} - {self.edm} ({self.survey_date})'


class uEDM_Observation(models.Model):
    pillar_survey = models.ForeignKey(uPillar_Survey, on_delete = models.CASCADE, null = False)
    
    from_pillar = models.ForeignKey(Pillar, on_delete = models.CASCADE, null = False)
    to_pillar = models.ForeignKey(Pillar, on_delete = models.CASCADE, null = False,
              related_name='+')
    
    inst_ht = models.DecimalField(
              max_digits=4, decimal_places=3,
              verbose_name= 'Instrument height')
    tgt_ht = models.DecimalField(
              max_digits=4, decimal_places=3,
              verbose_name= 'Target height')
    
    raw_slope_dist = models.DecimalField(
              max_digits=9, decimal_places=5,
              validators=[MinValueValidator(1), MaxValueValidator(1000)],
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
    use_for_distance = models.BooleanField(default=True,
                 verbose_name= 'Use for surveying the certified distances',
                 help_text="This observation (will) / (will not) be used for determining the calibration of the edmi.")
    
    class Meta:
       ordering = ['pillar_survey','from_pillar','to_pillar']
    
    def __str__(self):
       return f'({self.pillar_survey}): {self.from_pillar} → {self.to_pillar})'


class uCalibration_Parameter(models.Model):
    pillar_survey = models.ForeignKey(uPillar_Survey, on_delete = models.CASCADE, null = False)
    terms = (
             ('zpc','zero point correction'),
             ('scf','scale correction factor'),
             ('1C', '1 - Cyclic'),
             ('2C', '2 - Cyclic'),
             ('3C','3 - Cyclic'),
             ('4C','4 - Cyclic'),
              )
    term = models.CharField(max_length=3,
              choices=terms
              )
    value = models.FloatField(
                  verbose_name= 'parameter Value')
    standard_deviation = models.FloatField(
                  verbose_name= 'standard deviation of this parameter')
    
    class Meta:
       ordering = ['pillar_survey','term']
       unique_together = ('pillar_survey','term')
    
    def __str__(self):
       return f'({self.pillar_survey}): {self.term}'