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
#baseline_calibration
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.core.validators  import MaxValueValidator, MinValueValidator
from django.conf import settings
from datetime import date

# Create your models here.
User = settings.AUTH_USER_MODEL
from instruments.models import EDM_Inst, Prism_Inst, Mets_Inst, DigitalLevel, Staff
from calibrationsites.models import CalibrationSite, Pillar
from common_func.validators import validate_profanity, validate_file_size
from accounts.models import Company

class Accreditation(models.Model):
    accredited_company = models.ForeignKey(Company, on_delete = models.PROTECT, null=False)
    valid_from_date = models.DateField(null=False, blank=False,
                 help_text="The date the period of appointment commences.")
    valid_to_date = models.DateField(null=False, blank=False,
                 help_text="The date the period of appointment finishes.")
    LUM_constant = models.FloatField(
                 validators = [MinValueValidator(0), MaxValueValidator(50.0)],
                 null = False, blank = False)
    LUM_ppm = models.FloatField(
                 validators = [MinValueValidator(0), MaxValueValidator(50.0)],
                 null = False, blank = False)
    statement = models.TextField(null = False, blank = False,
                 verbose_name= 'Statement of accreditation',
                 help_text="eg. Accredited as a verifying authority for units of lenght according to ISO 17025:2012")
    certificate_upload = models.FileField(upload_to='accreditation_certificates/',
                 null=True,
                 blank=True, 
                 validators=[validate_file_size],
                 verbose_name= 'Accreditation Certificate')
                 
    class Meta:
        ordering = ['accredited_company','valid_to_date']
        unique_together = ('accredited_company','valid_from_date','valid_to_date',)
        verbose_name = "Company Accreditations"
        
    def get_absolute_url(self):
        return reverse('baseline_calibration:EDM_Observation-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.accredited_company}: {self.valid_from_date} → {self.valid_to_date}'


#####################
##   UNCERTAINTY   ##
#####################
class Uncertainty_Budget(models.Model):
    name = models.CharField(max_length=30, unique= False)
    company = models.ForeignKey(Company, on_delete = models.PROTECT, null=False)
    std_dev_of_zero_adjustment = models.DecimalField(max_digits=5, decimal_places=4,
                 validators = [MinValueValidator(0.00005)],
                 help_text="Standard deviation applied to set of observations when all"
                           " measured distances in set of observations are the same. (m)")

    class Meta:
        ordering = ['name']
        unique_together = ('name','company')
        verbose_name = "Uncertainty Budgets"
                 
    def get_absolute_url(self):
        return reverse('baseline_calibration:Uncertainty_Budget-detail', args=[str(self.id)])

    def __str__(self):
        return self.name


class Uncertainty_Budget_Source(models.Model):
    uncertainty_budget = models.ForeignKey(Uncertainty_Budget, on_delete = models.CASCADE, null = False,
                 help_text="Prism used for survey")
    group_types = (
                 ('01','EDM scale factor'),
                 ('02','EDMI measurement'),
                 ('03','EDM LS zero offset'),
                 ('04','Temperature'),
                 ('05','Pressure'),
                 ('06','Humidity'),
                 ('07','Certified distances'),
                 ('08','EDMI calibration'),
                 ('09','Centring'),
                 ('10','Heights'),
                 ('11','Offsets')
                 )
    group = models.CharField(
                 choices=group_types,
                 max_length=3,
                 help_text='Grouping of uncertainty source')
    description = models.CharField(max_length=256,
                 unique=False,)
    units_list = (
                 ('a.x','Scalar (a.x)'),
                 ('ppm','ppm'),
                 ('%','%'),
                 ('mm','mm'),
                 ('m','m'),
                 ('°C','°C'),
                 ('°F','°F'),
                 ('mBar','mBar'),
                 ('hPa','hPa'),
                 ('mmHg','mmHg'))
    units = models.CharField(
                 max_length=4,
                 choices=units_list,
                 blank=True, null = True,
                 help_text='Units of input quantity component')
    type_list = (
                 ('A','A'),
                 ('B','B'))
    ab_type = models.CharField(
                 max_length=1,
                 choices=type_list,
                 null = False,
                 default = 'B',
                 verbose_name= 'type',
                 help_text="Type A for a statistically derived component"
                          " or Type B for any other derivation"
                          " e.g. calibration report, manufacturers specification"
                          " or an estimate based on experience.")
    dist_type = (
                 ('N','Normal'),
                 ('R','Rectangular'))
    distribution = models.CharField(
                 max_length=1,
                 choices=dist_type,
                 null = False,
                 default = 'N',
                 help_text='A normal distribution represents most physical situations.'
                          ' Notable exceptions include rounding and resolution of a digital instrument.'
                          ' These components would typically be rectangular in distribution '
                          '(equal probability anywhere within the estimated uncertainty range).')
    std_dev = models.FloatField(help_text='Standard deviation'
                 ' in terms of the units specified',
                 null=True,blank = True)
    uc95 = models.FloatField(help_text='Uncertainty at 95% confidence'
                 ' in terms of the units specified',
                  validators = [MinValueValidator(1e-20)],
                  verbose_name= 'Uncertainty',
                  null=True,blank = True)
    k = models.FloatField(
                 validators = [MinValueValidator(1.0), MaxValueValidator(5.0)],
                 verbose_name= 'k',
                 help_text="The coverage factor for each input quantity."
                           " Typically 2.0 for a 95% confidence interval (normal distribution)"
                           " or sqrt(3) for a rectangular distribution.", 
                 default = 2.0,
                 null=True)
    degrees_of_freedom = models.IntegerField(
                 validators = [MinValueValidator(0), MaxValueValidator(500)],
                 verbose_name= 'dof',
                 help_text="Degrees of freedom of calibration "
                            "For a Type B estimate use the following as a guide: "
                            " 3 for not very confident, "
                            "10 for moderate confidence, "
                            "30 for very confident.",
                 default = 30)

    def save(self, *args, **kwargs):
        #convert UC -> Std dev or Std -> UC
        if self.k and self.uc95:
            self.std_dev = self.uc95 / self.k
        if self.k and self.std_dev:                
            if not self.uc95:
                self.uc95 = self.std_dev * self.k
            
        if self.distribution == 'R':
            self.k = 3**0.5
             
        super(Uncertainty_Budget_Source, self).save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(std_dev__isnull=False) | Q(uc95__isnull=False),
                name='not_both_null'),            
        ]
        
        ordering = ['uncertainty_budget','group','pk']
        
    def dict_2_object(self, uc_dict):
        for ky, vl in uc_dict.items():
            if ky in self.__dict__:
                setattr(self, ky, vl)
        return self
    
    def group_verbose(self):
        if self.group in dict(self.group_types).keys():
            return dict(self.group_types)[self.group]
    
    def get_absolute_url(self):
        return reverse('baseline_calibration:Uncertainty_Budget_Source-detail', args=[str(self.id)])
    
    def __str__(self):
        return f'{self.group} - {self.description}'


################
##   SURVEY   ##
################
def get_upload_to_location(instance, filename):
    creation_date = date.today().strftime('%Y-%m-%d')
    return '%s/%s/%s/%s/%s' % ('pillar_survey', 
                            instance.baseline.state.statecode.capitalize(),
                            instance.baseline.site_name, 
                            instance.accreditation.accredited_company.company_abbrev, 
                            creation_date+'-'+ filename)


class Pillar_Survey(models.Model):
    baseline = models.ForeignKey(CalibrationSite, on_delete = models.CASCADE, null = False,
                 verbose_name= 'Site',
                 help_text="Baseline under survey")
    survey_date = models.DateField(null=False, blank=False)
    computation_date = models.DateField(null=False, blank=False)
    accreditation = models.ForeignKey(Accreditation, on_delete = models.SET_NULL, 
                 null = True, blank=True,
                 help_text="corresponding certification survey.")
    apply_lum = models.BooleanField(default=True,
                 verbose_name= 'Apply LUM to uncertainties')
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
                verbose_name= 'EDM',
                 help_text="EDM used for survey")
    prism = models.ForeignKey(Prism_Inst, on_delete = models.PROTECT, null = False,
                 help_text="Prism used for survey")
    mets_applied = models.BooleanField(default=True,
                 verbose_name= 'Atmospheric corrections applied',
                 help_text="Meterological corrections have been applied in the EDM instrument.")
    co2_content = models.FloatField(blank = True, null=True, default=420,
                 verbose_name= 'CO2 content (ppm)',
                 help_text="Atmospheric CO2 content in ppm")
    
    edmi_calib_applied = models.BooleanField(default=False,
                 verbose_name= 'EDMI calibration corrections applied',
                 help_text="The EDMI calibration correction has been applied prior to data import.")

    level = models.ForeignKey(DigitalLevel, on_delete = models.PROTECT, null = False,
                 help_text="Digital level used for survey")
    staff = models.ForeignKey(Staff, on_delete = models.PROTECT, null = False,
                 help_text="barcoded staff used for survey")
    staff_calib_applied = models.BooleanField(default=True,
                 verbose_name= 'staff calibration corrections applied',
                 help_text="The staff calibration correction"
                  " has been applied prior to data import.")
                  
    thermometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, null = False,
                 limit_choices_to={'mets_specs__mets_model__inst_type': 'thermo'},
                 help_text="Thermometer used for survey",
                 related_name="field_thermometer")
    thermo_calib_applied = models.BooleanField(default=True,
                 verbose_name= 'thermometer calibration corrections applied',
                 help_text="The thermometer calibration correction"
                  " has been applied prior to data import.")
    barometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, null = False,
                 limit_choices_to={'mets_specs__mets_model__inst_type': 'baro'},
                 help_text="Barometer used for survey",
                 related_name="field_barometer")
    baro_calib_applied = models.BooleanField(default=True,
                 verbose_name= 'barometer calibration corrections applied',
                 help_text="The barometer calibration correction has been applied prior to data import.")
    hygrometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, blank=True, null = True,
                 limit_choices_to={'mets_specs__mets_model__inst_type': 'hygro'},
                 help_text="Hygrometer, if used for survey",
                 related_name="field_hygrometer")
    hygro_calib_applied = models.BooleanField(default=True,
                 verbose_name= 'Hygrometer calibration corrections applied',
                 help_text="The hygrometer correction has been applied prior to data import.")
    psychrometer = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT, blank=True, null = True,
                 limit_choices_to={'mets_specs__mets_model__inst_type': 'psy'},
                 help_text="Psychrometer, if used for survey",
                 related_name="field_psychrometer")
    psy_calib_applied = models.BooleanField(default=True,
                 help_text="The psychrometer correction has been applied prior to data import.")

    uncertainty_budget = models.ForeignKey(Uncertainty_Budget, on_delete = models.PROTECT, null = False,
                 help_text="Preset uncertainty budget")
    outlier_criterion = models.DecimalField(max_digits=2, decimal_places=1, default=2,
                 validators=[MinValueValidator(0), MaxValueValidator(5)],
                 help_text="Number of standard deviations for outlier detection threashold.")
    fieldnotes_upload = models.FileField(upload_to = get_upload_to_location,
                 null=True,
                 blank=True, 
                 validators=[validate_file_size],
                 verbose_name= 'Scanned fieldnotes')    

    zero_point_correction = models.FloatField(blank = True, null=True,
                 validators = [MinValueValidator(-0.10000), MaxValueValidator(0.10000)],
                 help_text="If: Instrument Correction (m) = 1.00000013.L + 0.0003, Zero Point Correction = 0.0003m")
    zpc_uncertainty = models.FloatField(blank = True, null=True,
                 validators = [MinValueValidator(0.00000), MaxValueValidator(0.10000)],
                 help_text="Uncertainty of the zero point correction (m) at 95% Confidence Level",
                 verbose_name= 'zero point correction uncertainty')
    variance = models.FloatField(blank = True, null=True,
                 help_text="Variance of least squares adjustment of the calibration")
    degrees_of_freedom = models.IntegerField(blank = True, null=True,
                 validators = [MinValueValidator(0), MaxValueValidator(500)],
                 help_text="Degrees of freedom of calibration")
   
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
    
    html_report = models.TextField(blank=True, null=True)
   
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ['baseline','survey_date']
        verbose_name = "Baseline Calibrations"
                 
    def get_absolute_url(self):
        return reverse('baseline_calibration:Pillar_Survey-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.job_number} - {self.baseline} ({self.survey_date})'


class EDM_Observation(models.Model):
    pillar_survey = models.ForeignKey(Pillar_Survey, on_delete = models.CASCADE, null = False)
    
    from_pillar = models.ForeignKey(Pillar, on_delete = models.CASCADE, null = False,
                 related_name="from_pillar")
    to_pillar = models.ForeignKey(Pillar, on_delete = models.CASCADE, null = False,
                 related_name="to_pillar")
    
    inst_ht = models.DecimalField(
                 max_digits=4, decimal_places=3,
                 verbose_name= 'Instrument height')
    tgt_ht = models.DecimalField(
                 max_digits=4, decimal_places=3,
                 verbose_name= 'Target height')
    
    hz_direction = models.DecimalField(
                 max_digits=12, decimal_places=6)
    
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

    use_for_alignment = models.BooleanField(default=True,
                 verbose_name= 'Use for alignment survey',
                 help_text="This observation (will) / (will not) be used for the alignment survey.")
    use_for_distance = models.BooleanField(default=True,
                 verbose_name= 'Use for surveying the certified distances',
                 help_text="This observation (will) / (will not) be used to determine certified distances for the range calibration survey.")
    
    class Meta:
        ordering = ['pillar_survey','from_pillar','to_pillar']

    def __str__(self):
        return f'({self.pillar_survey}): {self.from_pillar} → {self.to_pillar})'
    

class Level_Observation(models.Model):
    pillar_survey = models.ForeignKey(Pillar_Survey, on_delete = models.CASCADE, null = False)
    pillar = models.ForeignKey(Pillar, on_delete = models.CASCADE, null = False)
    reduced_level = models.DecimalField(max_digits=7, decimal_places=4)
    rl_standard_deviation = models.DecimalField(max_digits=7, decimal_places=4)

    class Meta:
        ordering = ['pillar_survey','pillar__order']
        unique_together  =('pillar_survey','pillar')


    def __str__(self):
        return f'{self.pillar_survey}: {self.pillar})'


#############################
##   CALIBRATED BASELINE   ##
#############################
class Certified_Distance(models.Model):
    pillar_survey = models.ForeignKey(Pillar_Survey, on_delete = models.CASCADE, null = False)
    from_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                  related_name="certified_distance_from_pillar")
    to_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                  related_name="certified_distance_to_pillar")
    distance = models.FloatField(
                  verbose_name= 'certified distance')
    a_uncertainty = models.FloatField(
                  verbose_name= 'type A uncertainty of certified distance')
    k_a_uncertainty = models.FloatField(
                  verbose_name="Coverage factor for type A uncertainty of certified distance",
                  default = 2.0)
    combined_uncertainty = models.FloatField(
                  verbose_name= 'combined uncertainty of certified distance')
    k_combined_uncertainty = models.FloatField(
                  verbose_name="Coverage factor for combined uncertainty of certified distance",
                  default = 2.0)
    offset = models.FloatField(
                  verbose_name= 'pillar offset')
    os_uncertainty = models.FloatField(
                  verbose_name= 'pillar offset uncertainty')
    k_os_uncertainty = models.FloatField(
                  verbose_name="Coverage factor for pillar offset uncertainty",
                  default = 2.0)
    reduced_level = models.FloatField()
    rl_uncertainty = models.FloatField(
                  verbose_name= 'Reduced level uncertainty')
    k_rl_uncertainty = models.FloatField(
                  verbose_name="Coverage factor for reduced level uncertainty",
                  default = 2.0)
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ['pillar_survey__survey_date','to_pillar__order']
        unique_together  =('from_pillar','to_pillar','pillar_survey')
        verbose_name = "Baseline Certified Distances"

    def __str__(self):
        return f'({self.pillar_survey}): {self.from_pillar} - {self.to_pillar}'


class Std_Deviation_Matrix(models.Model):
    pillar_survey = models.ForeignKey(Pillar_Survey, on_delete = models.CASCADE, null = False)
    from_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                  related_name="distance_standard_deviation_from_pillar")
    to_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                  related_name="distance_standard_deviation_to_pillar")
    std_uncertainty = models.FloatField(help_text = 'One Sigma Standard deviation of certified distance - Type A uncertianty only from LSA',
                                        verbose_name= 'One Sigma Standard deviation')
    
    def __str__(self):
      return f'({self.pillar_survey}): {self.from_pillar} -  {self.to_pillar}'
      

