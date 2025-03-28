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
App: baseline_calibration
Directory: Medjil/baseline_calibration/models.py

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
from instruments.models import (
    EDM_Inst, 
    Prism_Inst, 
    Mets_Inst, 
    DigitalLevel, 
    Staff)
from calibrationsites.models import CalibrationSite, Pillar
from common_func.validators import validate_profanity, validate_file_size
from accounts.models import Company

class Accreditation(models.Model):
    def get_upload_to_location(instance, filename):
        creation_date = date.today().strftime('%Y-%m-%d')
        return '%s/%s/%s' % (
            'accreditation_certificates',
            instance.accredited_company.company_abbrev, 
            creation_date+'-'+ filename)
    
    accredited_types = (
        ('B','Baseline Calibration'),
        ('E', 'EDMI Calibration'),
        )
    
    accredited_type = models.CharField(
        max_length=1,
        choices=accredited_types,
        help_text="The physical quantity that the authority is accredited to calibrate.",)
    accredited_company = models.ForeignKey(
        Company, on_delete = models.PROTECT)
    valid_from_date = models.DateField(
        help_text="The date the period of appointment commences.",
        verbose_name= 'Valid From Date')
    valid_to_date = models.DateField(
        help_text="The date the period of appointment finishes.",
        verbose_name= 'Valid To Date')
    LUM_constant = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(50.0)],
        verbose_name= 'LUM constant')
    LUM_ppm = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(50.0)],
        verbose_name= 'LUM ppm')
    statement = models.TextField(
        verbose_name= 'Statement of accreditation',
        help_text="eg. Accredited as a verifying authority for units of lenght according to ISO 17025:2012")
    certificate_upload = models.FileField(
        upload_to = get_upload_to_location,
        null=True,
        blank=True, 
        max_length=1000,
        validators=[validate_file_size],
        verbose_name= 'Accreditation Certificate')
                 
    class Meta:
        ordering = ['accredited_company','valid_to_date']
        unique_together = ('accredited_type', 'accredited_company','valid_from_date','valid_to_date',)
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
    std_dev_of_zero_adjustment = models.DecimalField(
        max_digits=6, decimal_places=5,
        default=0.00029, # Default set according to BASELINE review JM Rueger item [A47]
        validators = [MinValueValidator(0.00005)],
        help_text = "Standard deviation applied to set of observations when all"
                    " measured distances in set of observations are exactly the same. (m)")
    
    # boolean fields to opt for populating uncertainty sources from register.
    auto_EDMI_scf = models.BooleanField(
        default=True,
        help_text = "EDM Scale factor - EDMI Reg13 Scale correction factor")
    auto_EDMI_scf_drift = models.BooleanField(
        default=True,
        help_text = "EDM Scale factor - EDM Scale correction factor (drift over time)")
    auto_EDMI_round = models.BooleanField(
        default=True,
        help_text = "EDMI measurement - Distance Instrument rounding")
    auto_humi_zpc = models.BooleanField(
        default=True,
        help_text = "Humidity - Hygrometer calibrated correction factor")
    auto_humi_rounding = models.BooleanField(
        default=True,
        help_text = "Humidity - Hygrometer rounding")
    
    auto_pressure_zpc = models.BooleanField(
        default=True,
        help_text = "Pressure - Barometer calibrated correction factor")
    auto_pressure_rounding = models.BooleanField(
        default=True,
        help_text = "Pressure - Barometer rounding")
    
    auto_temp_zpc = models.BooleanField(
        default=True,
        help_text = "Temperature - Thermometer calibrated correction factor")
    auto_temp_rounding = models.BooleanField(
        default=True,
        help_text = "Temperature - Thermometer rounding")

    # boolean fields to opt for populating Derived uncertainty sources.
    auto_cd = models.BooleanField(
        default=True,
        help_text = "Certified distances- Pillar distances survey, processed uncertainty")
    auto_EDMI_lr = models.BooleanField(
        default=True,
        help_text = "EDMI measurement - Linear regression on EDM distance standard deviations")
    auto_hgts = models.BooleanField(
        default=True,
        help_text = "Heights - Pillar height differences from imported file")
    auto_os = models.BooleanField(
        default=True,
        help_text = "Offset - Pillar alignment survey processed uncertainty")
    
    class Meta:
        ordering = ['name']
        unique_together = ('name','company')
        verbose_name = "Uncertainty Budgets"
                 
    def get_absolute_url(self):
        return reverse('baseline_calibration:Uncertainty_Budget-detail', args=[str(self.id)])

    def __str__(self):
        return self.name



class Uncertainty_Budget_Source(models.Model):
    uncertainty_budget = models.ForeignKey(Uncertainty_Budget, on_delete = models.CASCADE, 
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
    description = models.CharField(max_length=256)
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
        default = 'N',
        help_text='A normal distribution represents most physical situations.'
                 ' Notable exceptions include rounding and resolution of a digital instrument.'
                 ' These components would typically be rectangular in distribution '
                 '(equal probability anywhere within the estimated uncertainty range).')
    std_dev = models.FloatField(
        help_text='Standard deviation in terms of the units specified',
        null=True,blank = True)
    uc95 = models.FloatField(
        help_text='Uncertainty at 95% confidence in terms of the units specified',
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
        validators = [MinValueValidator(1), MaxValueValidator(500)],
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

class Pillar_Survey(models.Model):
    def get_upload_to_location(instance, filename):
        creation_date = date.today().strftime('%Y-%m-%d')
        return '%s/%s/%s/%s/%s' % (
            'pillar_survey', 
            instance.baseline.state.statecode.capitalize(),
            instance.baseline.site_name, 
            instance.accreditation.accredited_company.company_abbrev, 
            'fieldnotes - '+creation_date+'-'+ filename)
    
    
    baseline = models.ForeignKey(
        CalibrationSite, on_delete = models.CASCADE,
        verbose_name= 'Site',
        help_text="Baseline under survey")
    survey_date = models.DateField()
    computation_date = models.DateField()
    accreditation = models.ForeignKey(
        Accreditation, on_delete = models.SET_NULL, 
        null = True, blank=True,
        help_text="corresponding certification survey.")
    apply_lum = models.BooleanField(
        default=True,
        verbose_name= 'Apply LUM to uncertainties')
    observer = models.CharField(
        max_length=25,
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
    weather = models.CharField(
        max_length=25,
        choices=weather_type,
        help_text="Weather conditions",
        )
    job_number = models.CharField(
        max_length=25,
        help_text="Job reference eg., JN 20212216",
        )
    comment = models.CharField(max_length=256, blank = True, null=True)

    edm = models.ForeignKey(
        EDM_Inst, on_delete = models.PROTECT,
        verbose_name= 'EDM',
        help_text="EDM used for survey")
    prism = models.ForeignKey(
        Prism_Inst, on_delete = models.PROTECT, 
        help_text="Prism used for survey")
    mets_applied = models.BooleanField(
        default=True,
        verbose_name= 'Atmospheric corrections applied',
        help_text="Meterological corrections have been applied in the EDM instrument.")
    co2_content = models.FloatField(
        blank = True, null=True, default=420,
        verbose_name= 'CO2 content (ppm)',
        help_text="Atmospheric CO2 content in ppm")
    
    edmi_calib_applied = models.BooleanField(
        default=False,
        verbose_name= 'EDMI calibration corrections applied',
        help_text="The EDMI calibration correction"
        " has been applied prior to data import.")

    level = models.ForeignKey(
        DigitalLevel, on_delete = models.PROTECT,
        help_text="Digital level used for survey")
    staff = models.ForeignKey(
        Staff, on_delete = models.PROTECT, 
        help_text="barcoded staff used for survey")
    staff_calib_applied = models.BooleanField(
        default=True,
        verbose_name= 'staff calibration corrections applied',
        help_text="The staff calibration correction"
         " has been applied prior to data import.")
                  
    thermometer = models.ForeignKey(
        Mets_Inst, on_delete = models.PROTECT, 
        limit_choices_to={'mets_specs__inst_type': 'thermo'},
        help_text="Thermometer used for survey",
        related_name="field_thermometer")
    thermo_calib_applied = models.BooleanField(
        default=True,
        verbose_name= 'thermometer calibration corrections applied',
        help_text="The thermometer calibration correction"
         " has been applied prior to data import.")
    thermometer2 = models.ForeignKey(
        Mets_Inst, on_delete = models.PROTECT, 
        null = True, blank = True,
        limit_choices_to={'mets_specs__inst_type': 'thermo'},
        verbose_name= 'Thermometer 2',
        help_text="Thermometer 2 used for survey",
        related_name="field_thermometer2")
    thermo2_calib_applied = models.BooleanField(
        default=True,
        verbose_name= 'thermometer 2 calibration corrections applied',
        help_text="The thermometer 2 calibration correction"
         " has been applied prior to data import.")
    
    barometer = models.ForeignKey(
        Mets_Inst, on_delete = models.PROTECT, 
        limit_choices_to={'mets_specs__inst_type': 'baro'},
        help_text="Barometer used for survey",
        related_name="field_barometer")
    baro_calib_applied = models.BooleanField(
        default=True,
        verbose_name= 'barometer calibration corrections applied',
        help_text="The barometer calibration correction"
        " has been applied prior to data import.")
    barometer2 = models.ForeignKey(
        Mets_Inst, on_delete = models.PROTECT, 
        null = True, blank = True,
        limit_choices_to={'mets_specs__inst_type': 'baro'},
        verbose_name= 'Barometer 2',
        help_text="Barometer 2 used for survey",
        related_name="field_barometer2")
    baro2_calib_applied = models.BooleanField(
        default=True,
        verbose_name= 'barometer 2 calibration corrections applied',
        help_text="The barometer 2 calibration correction"
        " has been applied prior to data import.")
    
    hygrometer = models.ForeignKey(
        Mets_Inst, on_delete = models.PROTECT, blank=True, null = True,
        limit_choices_to={'mets_specs__inst_type': 'hygro'},
        help_text="Hygrometer used for survey",
        related_name="field_hygrometer")
    hygro_calib_applied = models.BooleanField(
        default=True,
        verbose_name= 'Hygrometer calibration corrections applied',
        help_text="The hygrometer correction"
        " has been applied prior to data import.")
    hygrometer2 = models.ForeignKey(
        Mets_Inst, on_delete = models.PROTECT, blank=True, null = True,
        limit_choices_to={'mets_specs__inst_type': 'hygro'},
        verbose_name= 'Hygrometer 2',
        help_text="Hygrometer 2 used for survey",
        related_name="field_hygrometer2")
    hygro2_calib_applied = models.BooleanField(
        default=True,
        verbose_name= 'Hygrometer 2 calibration corrections applied',
        help_text="The hygrometer 2 correction has"
        " been applied prior to data import.")
    
    psychrometer = models.ForeignKey(
        Mets_Inst, on_delete = models.PROTECT, blank=True, null = True,
        limit_choices_to={'mets_specs__inst_type': 'psy'},
        help_text="Psychrometer, if used for survey",
        related_name="field_psychrometer")
    psy_calib_applied = models.BooleanField(
        default=True,
        help_text="The psychrometer correction has been applied prior to data import.")

    uncertainty_budget = models.ForeignKey(
        Uncertainty_Budget, on_delete = models.PROTECT, 
                 help_text="Preset uncertainty budget")
    outlier_criterion = models.DecimalField(
        max_digits=2, decimal_places=1, default=2,
                 validators=[MinValueValidator(0), MaxValueValidator(5)],
                 help_text="Number of standard deviations for outlier detection threashold.")
    fieldnotes_upload = models.FileField(
        upload_to = get_upload_to_location,
        null=True,
        blank=True,
        max_length=1000,
        help_text="Uploaded copy of digital records or scanned fieldnotes.",
        validators=[validate_file_size],
        verbose_name= 'Field record')    
    
    class Meta:
        ordering = ['baseline','survey_date']
        verbose_name = "Baseline Calibrations"
                 
    def get_absolute_url(self):
        return reverse(
            'baseline_calibration:Pillar_Survey-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.baseline} ({self.survey_date})'

    def certified_distances(self):
        queryset = Certified_Distance.objects.filter(
            pillar_survey = self.pk).order_by('to_pillar__order')
        return queryset


class EDM_Observation(models.Model):
    pillar_survey = models.ForeignKey(
        Pillar_Survey, on_delete = models.CASCADE)
    
    from_pillar = models.ForeignKey(
        Pillar, on_delete = models.CASCADE, 
                 related_name="from_pillar")
    to_pillar = models.ForeignKey(
        Pillar, on_delete = models.CASCADE, 
        related_name="to_pillar")
    
    inst_ht = models.DecimalField(
        max_digits=4, decimal_places=3,
        verbose_name= 'Instrument height')
    tgt_ht = models.DecimalField(
        max_digits=4, decimal_places=3,
        verbose_name= 'Target height')
    
    hz_direction = models.DecimalField(
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        max_digits=32, decimal_places=26)
    
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
    
    raw_temperature2 = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(50.0)],
        null = True, blank = True)
    raw_pressure2 = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(1500.0)],
        null = True, blank = True)
    raw_humidity2 = models.FloatField(
        validators = [MinValueValidator(0), MaxValueValidator(100.0)],
        null = True, blank = True)

    use_for_alignment = models.BooleanField(
        default=True,
        verbose_name= 'Use for alignment survey',
        help_text="This observation (will) / (will not) be used for the alignment survey.")
    use_for_distance = models.BooleanField(
        default=True,
        verbose_name= 'Use for surveying the certified distances',
        help_text="This observation (will) / (will not) be used to determine certified distances for the range calibration survey.")
    
    class Meta:
        ordering = ['pillar_survey','from_pillar','to_pillar']

    def __str__(self):
        return f'({self.pillar_survey}): {self.from_pillar} → {self.to_pillar})'        
    

class Level_Observation(models.Model):
    pillar_survey = models.ForeignKey(
        Pillar_Survey, on_delete = models.CASCADE)
    pillar = models.ForeignKey(
        Pillar, on_delete = models.CASCADE)
    reduced_level = models.DecimalField(
        max_digits=27, decimal_places=24)
    rl_standard_deviation = models.DecimalField(
        max_digits=27, decimal_places=24)

    class Meta:
        ordering = ['pillar_survey','pillar__order']
        unique_together  =('pillar_survey','pillar')

    def __str__(self):
        return f'{self.pillar_survey}: {self.pillar})'


#############################
##   CALIBRATED BASELINE   ##
#############################
# Status choices for calibrated baseline
SURVEY_STATUS_CHOICES = [
    ('publish', 'Publish'),
    ('check', 'Check Survey'),
]

class PillarSurveyResults(models.Model):
    def get_upload_to_location(instance, filename):
        creation_date = date.today().strftime('%Y-%m-%d')
        return '%s/%s/%s/%s/%s' % (
            'pillar_survey', 
            instance.pillar_survey.baseline.state.statecode.capitalize(),
            instance.pillar_survey.baseline.site_name, 
            instance.pillar_survey.accreditation.accredited_company.company_abbrev, 
            'Reg13 - '+creation_date+'-'+ filename)
    
    pillar_survey = models.OneToOneField(
        'Pillar_Survey',
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name="Related Pillar Survey"
    )
    zero_point_correction = models.FloatField(
        blank=True, null=True,
        validators=[MinValueValidator(-0.10000), MaxValueValidator(0.10000)],
        help_text="If: Instrument Correction (m) = 1.00000013.L + 0.0003, Zero Point Correction = 0.0003m"
    )
    zpc_uncertainty = models.FloatField(
        blank=True, null=True,
        validators=[MinValueValidator(0.00000), MaxValueValidator(0.10000)],
        help_text="Uncertainty of the zero point correction (m) at 95% Confidence Level",
        verbose_name='Zero Point Correction Uncertainty'
    )
    experimental_std_dev = models.FloatField(
        blank=True, null=True,
        help_text="Experimental Standard Deviation of single observation (m) ISO 17123-4:2012 eq.14",
        verbose_name='Experimental Standard Deviation'
    )
    degrees_of_freedom = models.IntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1), MaxValueValidator(500)],
        help_text="Degrees of freedom of calibration"
    )
    reference_height = models.FloatField(
        default=0.000,
        help_text="Certified distances were determined at this reference height (mAHD)",
        verbose_name="Reference Height (mAHD)"
    )
    data_entered_person = models.CharField(
        validators=[validate_profanity], max_length=25, null=True, blank=True
    )
    data_entered_position = models.CharField(
        validators=[validate_profanity], max_length=25, null=True, blank=True
    )
    data_entered_date = models.DateField(null=True, blank=True)
    data_checked_person = models.CharField(
        validators=[validate_profanity], max_length=25, null=True, blank=True
    )
    data_checked_position = models.CharField(
        validators=[validate_profanity], max_length=25, null=True, blank=True
    )
    data_checked_date = models.DateField(null=True, blank=True)
    html_report = models.TextField(blank=True, null=True)
    reg13_upload = models.FileField(
        upload_to = get_upload_to_location,
        null=True,
        blank=True,
        max_length=1000,
        validators=[validate_file_size],
        verbose_name='Reg13 Certificate'
    )
    status = models.CharField(
        max_length=10,
        choices=SURVEY_STATUS_CHOICES,
        default='publish',
        verbose_name='Publish Status'
    )
    uploaded_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['pillar_survey']
        verbose_name = "Pillar Survey Results"

    def __str__(self):
        return f'Results for Survey {self.pillar_survey}'
        
        
class Certified_Distance(models.Model):
    pillar_survey = models.ForeignKey(
        Pillar_Survey, on_delete = models.CASCADE)
    from_pillar = models.ForeignKey(
        Pillar, on_delete = models.PROTECT, 
        related_name="certified_distance_from_pillar")
    to_pillar = models.ForeignKey(
        Pillar, on_delete = models.PROTECT, 
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
    pillar_survey = models.ForeignKey(
        Pillar_Survey, on_delete = models.CASCADE)
    from_pillar = models.ForeignKey(
        Pillar, on_delete = models.PROTECT, 
                  related_name="distance_standard_deviation_from_pillar")
    to_pillar = models.ForeignKey(
        Pillar, on_delete = models.PROTECT, 
                  related_name="distance_standard_deviation_to_pillar")
    std_uncertainty = models.FloatField(
        help_text = 'One Sigma Standard deviation of certified distance - Type A uncertianty only from LSA',
        verbose_name= 'One Sigma Standard deviation')
    
    def __str__(self):
      return f'({self.pillar_survey}): {self.from_pillar} -  {self.to_pillar}'
      

