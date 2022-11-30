#baseline_calibration
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.core.validators  import MaxValueValidator, MinValueValidator, DecimalValidator
from django.conf import settings

# Create your models here.
User = settings.AUTH_USER_MODEL
from accounts.models import CustomUser
from instruments.models import EDM_Inst, Prism_Inst, Mets_Inst, DigitalLevel, Staff
from calibrationsites.models import CalibrationSite, Pillar
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
    certificate_upload = models.FileField(upload_to='accreditation_certificates/',
                 null=True,
                 blank=True, 
                 verbose_name= 'Accreditation Certificate')
                 
    class Meta:
        ordering = ['accredited_company','valid_to_date']
        unique_together = ('accredited_company','valid_from_date','valid_to_date',)
        
    def get_absolute_url(self):
        return reverse('baseline_calibration:EDM_Observation-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.accredited_company}: {self.valid_from_date} → {self.valid_to_date}'


#####################
##   UNCERTAINTY   ##
#####################
class Uncertainty_Budget(models.Model):
    name = models.CharField(max_length=30,help_text="e.g., 2021 baseline calibration", unique= False)
    company = models.ForeignKey(Company, on_delete = models.PROTECT, null=False)
    std_dev_of_zero_adjustment = models.DecimalField(max_digits=5, decimal_places=4,
                 validators=[MinValueValidator(0), MaxValueValidator(0.01)],
                 help_text="Standard deviation applied to set of observations when all"
                           " measured distances in set of observations are the same. (m)")

    class Meta:
        ordering = ['name']
                 
    def get_absolute_url(self):
        return reverse('baseline_calibration:Uncertainty_Budget-detail', args=[str(self.id)])

    def __str__(self):
        return self.name


class Uncertainty_Budget_Source(models.Model):
    uncertainty_budget = models.ForeignKey(Uncertainty_Budget, on_delete = models.CASCADE, null = False,
                 help_text="Prism used for survey")
    group_types = (
                 ('1','EDM scale factor'),
                 ('2','EDM scale factor (temp. effect)'),
                 ('3','EDM scale factor (drift over time)'),
                 ('4','EDM zero offset'),
                 ('5','Temperature unc'),
                 ('6','Pressure unc'),
                 ('7','Humidity unc'),
                 ('8','LS fit unc fixed term'),
                 ('9','LS fit unc proportional term'),
                 ('10','Centring'),
                 ('11','Heights'),
                 ('12','Offsets'),
                 ('13','Rounding')
                 )
    group = models.CharField(
                 choices=group_types,
                 max_length=3   ,
                 help_text='Grouping of uncertainty source')
    description = models.CharField(max_length=256,
                 unique=False,)
    units_list = (
                 ('NA','Not applicable (NA)'),
                 ('mm','millimetres (mm)'),
                 ('m','metres (m)'),
                 ('°C','Degrees Celcius (°C)'),
                 ('hPa','hectopascals (hPa)'),
                 ('mmHg','Millimetre of mercury (mmHg)'),
                 ('%','percent (%)'))
    units = models.CharField(
                 max_length=4,
                 choices=units_list,
                 default = 'NA',
                 blank=True, null = True,
                 help_text='Units of input quantity component')
    type_list = (
                 ('A','A'),
                 ('B','B'))
    ab_type = models.CharField(
                 max_length=1,
                 choices=type_list,
                 null = False,
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
                 help_text='A normal distribution represents most physical situations.'
                          ' Notable exceptions include rounding and resolution of a digital instrument.'
                          ' These components would typically be rectangular in distribution '
                          '(equal probability anywhere within the estimated uncertainty range).')
    std_dev = models.FloatField(help_text='Standard deviation'
                 ' in terms of the units specified',
                 null=True,blank = True)
    uc95 = models.FloatField(help_text='Uncertainty at 95% confidence'
                 ' in terms of the units specified',
                  null=True,blank = True)
    k = models.FloatField(
                 validators = [MinValueValidator(1.0), MaxValueValidator(5.0)],
                 help_text="The coverage factor for each input quantity."
                           " Typically 2.0 for a 95% confidence interval (normal distribution)"
                           " or sqrt(3) for a rectangular distribution.", 
                 default = 2.0,
                 null=True)
    degrees_of_freedom = models.IntegerField(
                 validators = [MinValueValidator(0), MaxValueValidator(500)],
                 help_text="Degrees of freedom of calibration "
                 					 "For a Type B estimate use the following as a guide: "
                 					 " 3 for not very confident, "
                 					 "10 for moderate confidence, "
                 					 "30 for very confident.",
                 default = 30)

    def save(self, *args, **kwargs):
         if not self.std_dev:
         	self.std_dev = self.uc95 / self.k
         if not self.uc95:
         	self.uc95 = self.std_dev * self.k
         if self.distribution == 'R':
         	self.k = 3**0.5
         super(Uncertainty_Budget_Source, self).save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(std_dev__isnull=False) | Q(uc95__isnull=False),
                name='not_both_null'
            )
        ]
        
    class Meta:
        ordering = ['uncertainty_budget','group','pk']
                 
    def get_absolute_url(self):
        return reverse('baseline_calibration:Uncertainty_Budget_Source-detail', args=[str(self.id)])
    
    def __str__(self):
        return f'{self.group} - {self.description}'


################
##   SURVEY   ##
################
class Pillar_Survey(models.Model):
    baseline = models.ForeignKey(CalibrationSite, on_delete = models.CASCADE, null = False,
                 help_text="Baseline under survey")
    survey_date = models.DateField(null=False, blank=False)
    computation_date = models.DateField(null=False, blank=False)
    accreditation = models.ForeignKey(Accreditation, on_delete = models.SET_NULL, null = True,
                 help_text="corresponding certification survey.")
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
                 verbose_name= 'Atmospheric corrections applied',
                 help_text="Meterological corrections have been applied in the EDM instrument.")
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
    outlier_criterion = models.DecimalField(max_digits=2, decimal_places=1, default=3,
                 validators=[MinValueValidator(0), MaxValueValidator(5)],
                 help_text="Number of standard deviations for outlier detection threashold.")
    fieldnotes_upload = models.FileField(upload_to='fieldnotes/',
                 null=True,
                 blank=True, 
                 verbose_name= 'Scanned fieldnotes')
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ['baseline','survey_date']
                 
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
    
    slope_dist = models.DecimalField(
                 max_digits=9, decimal_places=5,
                 validators=[MinValueValidator(1), MaxValueValidator(1000)],
                 verbose_name= 'slope distance')
    
    temperature = models.FloatField(
                 validators = [MinValueValidator(0), MaxValueValidator(50.0)],
                 null = True, blank = True)
    wet_temp = models.FloatField(
                 validators = [MinValueValidator(0), MaxValueValidator(50.0)],
                 null = True, blank = True)
    pressure = models.FloatField(
                 validators = [MinValueValidator(0), MaxValueValidator(1500.0)],
                 null = True, blank = True)
    humidity = models.FloatField(
                 validators = [MinValueValidator(0), MaxValueValidator(100.0)],
                 null = True, blank = True)

    class Meta:
        ordering = ['pillar_survey','from_pillar','to_pillar']
                 
    def get_absolute_url(self):
        return reverse('baseline_calibration:EDM_Observation-detail', args=[str(self.id)])

    def __str__(self):
        return f'({self.pillar_survey}): {self.from_pillar} → {self.to_pillar})'


class Level_Observation(models.Model):
    pillar_survey = models.ForeignKey(Pillar_Survey, on_delete = models.CASCADE, null = False)
    baseline_pillar = models.ForeignKey(Pillar, on_delete = models.CASCADE, null = False)
    reduced_level = models.DecimalField(max_digits=7, decimal_places=4)
    rl_standard_deviation = models.DecimalField(max_digits=7, decimal_places=4)

    class Meta:
        ordering = ['pillar_survey','baseline_pillar__order']
        unique_together  =('pillar_survey','baseline_pillar')


    def __str__(self):
        return f'{self.pillar_survey}: {self.baseline_pillar})'


#############################
##   CALIBRATED BASELINE   ##
#############################
class Calibrated_Baseline(models.Model):
    pillar_survey = models.ForeignKey(Pillar_Survey, on_delete = models.CASCADE, null = False)
    zero_point_correction = models.FloatField(
                 validators = [MinValueValidator(-0.10000), MaxValueValidator(0.10000)],
                 help_text="If: Instrument Correction (m) = 1.00000013.L + 0.0003, Zero Point Correction = 0.0003m")
    zpc_uncertainty = models.FloatField(
                 validators = [MinValueValidator(0.00000), MaxValueValidator(0.10000)],
                 help_text="Uncertainty of the zero point correction (m) at 95% Confidence Level",
                 verbose_name= 'zero point correction uncertainty')
    degrees_of_freedom = models.IntegerField(
                 validators = [MinValueValidator(0), MaxValueValidator(500)],
                 help_text="Degrees of freedom of calibration")
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ['pillar_survey__baseline','pillar_survey']

    def __str__(self):
        return f'{self.pillar_survey.baseline}: {self.pillar_survey}'


class Certified_Distance(models.Model):
    calibrated_baseline = models.ForeignKey(Calibrated_Baseline, on_delete = models.CASCADE, null = False)
    from_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                 related_name="certified_distance_from_pillar")
    to_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                 related_name="certified_distance_to_pillar")
    distance = models.DecimalField(
                 max_digits=9, decimal_places=5,
                 validators=[MinValueValidator(0), MaxValueValidator(1000)],
                 verbose_name= 'certified distance')
    a_uncertainty = models.DecimalField(
                 max_digits=6, decimal_places=5,
                 validators = [MinValueValidator(0), MaxValueValidator(1.0)],
                 verbose_name= 'type A uncertainty of certified distance')
    k_a_uncertainty = models.FloatField(
                 validators = [MinValueValidator(1.0), MaxValueValidator(5.0)],
                 verbose_name="Coverage factor for type A uncertainty of certified distance",
                 default = 2.0)
    combined_uncertainty = models.DecimalField(
                 max_digits=6, decimal_places=5,
                 validators = [MinValueValidator(0), MaxValueValidator(1.0)],
                 verbose_name= 'combined uncertainty of certified distance')
    k_combined_uncertainty = models.FloatField(
                 validators = [MinValueValidator(1.0), MaxValueValidator(5.0)],
                 verbose_name="Coverage factor for combined uncertainty of certified distance",
                 default = 2.0)
    offset = models.DecimalField(
                 max_digits=5, decimal_places=4,
                 validators=[MinValueValidator(-0.3), MaxValueValidator(0.3)],
                 verbose_name= 'pillar offset')
    os_uncertainty = models.DecimalField(
                 max_digits=6, decimal_places=5,
                 validators = [MinValueValidator(0), MaxValueValidator(1.0)],
                 verbose_name= 'pillar offset uncertainty')
    k_os_uncertainty = models.FloatField(
                 validators = [MinValueValidator(1.0), MaxValueValidator(5.0)],
                 verbose_name="Coverage factor for pillar offset uncertainty",
                 default = 2.0)
    reduced_level = models.DecimalField(max_digits=7, decimal_places=4)
    rl_uncertainty = models.DecimalField(
                 max_digits=6, decimal_places=5,
                 validators = [MinValueValidator(0), MaxValueValidator(0.3)],
                 verbose_name= 'Reduced level uncertainty')
    k_rl_uncertainty = models.FloatField(
                 validators = [MinValueValidator(1.0), MaxValueValidator(5.0)],
                 verbose_name="Coverage factor for reduced level uncertainty",
                 default = 2.0)
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ['calibrated_baseline__pillar_survey','to_pillar__order']
        unique_together  =('calibrated_baseline','from_pillar','to_pillar')

    def __str__(self):
        return f'({self.calibrated_baseline}): {self.from_pillar} - {self.to_pillar}'


class Std_Deviation_Matrix(models.Model):
    calibrated_baseline = models.ForeignKey(Calibrated_Baseline, on_delete = models.CASCADE, null = False)
    from_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                 related_name="distance_standard_deviation_from_pillar")
    to_pillar = models.ForeignKey(Pillar, on_delete = models.PROTECT, null = False,
                 related_name="distance_standard_deviation_to_pillar")
    std_uncertainty = models.FloatField(help_text = 'One Sigma Standard deviation of certified distance - Type A uncertianty only from LSA',
    																		verbose_name= 'One Sigma Standard deviation')
    
    def __str__(self):
    	return f'({self.calibrated_baseline}): {self.from_pillar} -  {self.to_pillar}'
    	

