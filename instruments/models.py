#instruments
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.core.validators  import (
    MaxValueValidator, 
    MinValueValidator, 
    MinLengthValidator)
from django.conf import settings
from accounts.models import (
    CustomUser,
    Company)
from common_func.validators import validate_profanity
from datetime import date


User = settings.AUTH_USER_MODEL

length_units = (
    ('µm','µm'),
    ('nm','nm'),
    ('mm','mm'),
    ('m','m'),)
freq_units = (
    ('Hz','Hz'),
    ('MHz','MHz'),)
scalar_units = (
    ('x:1','x:1'),
    ('1:x','1:x'),
    ('ppm','ppm'),)
edm_types = (
    ('ph','Phase'),
    ('pu','Pulse'),
)
        
class InstrumentMake(models.Model):
    make = models.CharField(
        max_length=25,
        validators=[MinLengthValidator(4), validate_profanity],
        help_text="e.g., LEICA, TRIMBLE, SOKKIA",
        unique=True
    )
    make_abbrev = models.CharField(
        max_length=4,
        validators=[MinLengthValidator(3), validate_profanity],
        help_text="Specify a 3 to 4 letter abbreviation",
        unique=True,
        verbose_name='Abbreviation'
    )

    def __str__(self):
        return self.make


class InstrumentModel(models.Model):
    inst_types = (
        (None, 'Select one of the following'),
        ('edm', 'Total Station EDM'),
        ('prism', 'Prism'),
        ('level', 'Digital Level'),
        ('staff', 'Barcoded Staff'),
        ('baro', 'Barometer'),
        ('thermo', 'Thermometer'),
        ('hygro', 'Hygrometer'),
        ('psy', 'Psychrometer'),
        ('others', 'Others'),
    )

    inst_type = models.CharField(
        max_length=6,
        choices=inst_types,
        verbose_name='instrument type',
        null=True
    )
    make = models.ForeignKey(InstrumentMake, on_delete=models.CASCADE, null=True)
    model = models.CharField(
        max_length=25,
        validators=[MinLengthValidator(2), validate_profanity],
        help_text="e.g., LS15, DNA03, TS30, S9, SX12, GT-1200/600"
    )

    class Meta:
        ordering = ['inst_type', 'make', 'model']
        unique_together = ('inst_type', 'make', 'model')

    def __str__(self):
        return f'{self.model} ({self.inst_type})'


class DigitalLevel(models.Model):
    level_owner = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    level_number = models.CharField(
        max_length=15,
        validators=[MinLengthValidator(4), validate_profanity],
        help_text="Enter the instrument number"
    )
    level_model = models.ForeignKey(
        InstrumentModel,
        limit_choices_to={'inst_type__exact': 'level'},
        on_delete=models.CASCADE,
        null=True
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['level_number', 'level_model']
        unique_together = ['level_number', 'level_owner']

    def get_absolute_url(self):
        return reverse('instruments:inst_level_update', args=[str(self.id)])

    def __str__(self):
        return f'{self.level_number} {self.level_model}'


class Staff(models.Model):
    staff_model = models.ForeignKey(
        InstrumentModel,
        limit_choices_to={'inst_type__exact': 'staff'},
        on_delete=models.CASCADE,
        null=True
    )
    staff_owner = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    staff_number = models.CharField(
        max_length=15,
        validators=[validate_profanity],
        help_text="Enter the instrument number"
    )
    staff_types = (
        (None, 'Select one of the following'),
        ('invar', 'Invar'),
        ('fiberglass', 'Fiber glass'),
        ('wood', 'Wood'),
        ('aluminium', 'Aluminium'),
        ('steel', 'Steel'),
        ('epoxy', 'Carbon/epoxy'),
        ('e_glass', 'E-glass'),
        ('s2_glass', 'S2-glass'),
    )

    staff_type = models.CharField(
        max_length=10,
        choices=staff_types
    )

    staff_length = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Staff length in meters",
        verbose_name="Staff length (in metres)"
    )
    thermal_coefficient = models.FloatField(
        null=True,
        validators=[MinValueValidator(-100), MaxValueValidator(100)],
        help_text="Coefficient of expansion in ppm units- e.g., Fibreglass: 10.0, Carbon: 3.0",
        verbose_name="CoE (in ppm)"
    )

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ['staff_number', 'staff_owner']
        ordering = ['staff_number']

    def __str__(self):
        return f'{self.staff_number} - {self.staff_type}'

    def get_absolute_url(self):
        return reverse('instruments:inst_staff_update', args=[str(self.id)])

#####################################################################
############################ EDM INSTRUMENTS ########################
#####################################################################
class EDM_Specification(models.Model):
    edm_owner = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        verbose_name='EDM owner'
    )
    edm_model = models.ForeignKey(
        InstrumentModel,
        limit_choices_to={'inst_type__exact': 'edm'},
        on_delete=models.PROTECT,
        verbose_name='EDM model'
    )

    edm_type = models.CharField(
        max_length=2,
        choices=edm_types,
        default='ph',
        help_text='Instrument measurement type',
        verbose_name='EDM type'
    )
    manu_unc_const = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Accuracy = A mm ± B ppm, Uncertainty Constant = A",
        verbose_name='manufacturers uncertainty constant'
    )
    manu_unc_ppm = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Accuracy = A mm ± B ppm, Uncertainty ppm = B",
        verbose_name='manufacturers parts per million uncertainty'
    )
    manu_unc_k = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        default=2.0,
        verbose_name='manufacturers uncertainty coverage factor'
    )

    unit_length = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10000.0)],
        help_text="Unit Length (m)"
    )
    frequency = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(100000000)],
        help_text="Frequency (Hz)",
        null=True,
        blank=True
    )
    carrier_wavelength = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Carrier Wavelength (nm)",
        null=True,
        blank=True
    )
    manu_ref_refrac_index = models.FloatField(
        validators=[MinValueValidator(0.000000000), MaxValueValidator(2.000000000)],
        help_text="Manufacturers reference refractive index",
        verbose_name='Manufacturers reference refractive index',
        null=True,
        blank=True
    )

    c_term = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Coefficients C for first velocity correction eg 281.8",
        null=True,
        blank=True
    )
    d_term = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Coefficients D for first velocity correction eg 79.39",
        null=True,
        blank=True
    )

    measurement_increments = models.DecimalField(
        max_digits=7, decimal_places=6,
        help_text="Resolution of the measurement eg. 0.01"
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['edm_model']
        unique_together = ('edm_model', 'edm_owner')

    def __str__(self):
        return f'{self.edm_model.make} {self.edm_model.model} ({self.edm_owner.company_abbrev})'


def get_upload_to_edm_photos(instance, filename):
    modified_date = date.today().strftime('%Y%m%d')
    filename = filename.split('\\')[-1]
    return 'InstrumentPhotos/%s/EDM/%s/%s/%s' % (
        instance.edm_specs.edm_owner.company_abbrev, instance.edm_number, modified_date, filename
    )


class EDM_Inst(models.Model):
    edm_number = models.CharField(
        max_length=15,
        validators=[validate_profanity],
        help_text="Enter the instrument serial number / unique ID",
        verbose_name='EDM Number'
    )
    edm_custodian = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Name of instrument custodian",
        verbose_name="EDM Custodian"
    )
    photo = models.FileField(
        upload_to=get_upload_to_edm_photos,
        null=True,
        blank=True,
        verbose_name='Instrument Photo'
    )
    comment = models.CharField(
        validators=[validate_profanity],
        max_length=265, 
        null=True, blank=True)
    edm_specs = models.ForeignKey(
        EDM_Specification,
        on_delete=models.PROTECT,
        null=True,
        verbose_name="EDM Specification"
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['edm_specs']
        unique_together = ('edm_specs', 'edm_number')

    def get_absolute_url(self):
        return reverse('instruments:inst_edm_update', args=[str(self.id)])

    def __str__(self):
        return f'{self.edm_specs} - {self.edm_number}'

    def delete(self, *args, **kwargs):
        super(EDM_Inst, self).delete(*args, **kwargs)
        try:
            self.photo.storage.delete(self.photo.path)
        except:
            print('No files to delete')


class Prism_Specification(models.Model):
    prism_owner = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Prism Owner"
    )
    prism_model = models.ForeignKey(
        InstrumentModel,
        limit_choices_to={'inst_type__exact': 'prism'},
        on_delete=models.PROTECT
    )
    manu_unc_const = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Manufacturers centring accuracy = ±1mm",
        verbose_name='manufacturers uncertainty constant'
    )
    manu_unc_k = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        default=2.00,
        verbose_name='manufacturers uncertainty coverage factor'
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['prism_model']
        unique_together = ('prism_model', 'prism_owner')

    def __str__(self):
        return f'{self.prism_model.make} {self.prism_model.model} ({self.prism_owner.company_abbrev})'


def get_upload_to_prism_photos(instance, filename):
    modified_date = date.today().strftime('%Y%m%d')
    filename = filename.split('\\')[-1]
    return 'InstrumentPhotos/%s/Prism/%s/%s/%s' % (
        instance.prism_specs.prism_owner.company_abbrev, instance.prism_number, modified_date, filename
    )


class Prism_Inst(models.Model):
    prism_number = models.CharField(
        validators=[validate_profanity],
        max_length=15,
        help_text="Enter the instrument serial number / unique ID",
        verbose_name='Prism Number'
    )
    prism_custodian = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text="Name of instrument custodian",
        verbose_name='Prism Custodian'
    )
    photo = models.FileField(
        upload_to=get_upload_to_prism_photos,
        null=True,
        blank=True,
        verbose_name='Instrument Photo'
    )
    comment = models.CharField(
        validators=[validate_profanity],
        max_length=265, 
        null=True, blank=True)
    prism_specs = models.ForeignKey(
        Prism_Specification,
        on_delete=models.PROTECT,
        verbose_name='Prism Specification'
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['prism_specs']
        unique_together = ('prism_specs', 'prism_number')

    def get_absolute_url(self):
        return reverse('instruments:inst_prism_update', args=[str(self.id)])

    def __str__(self):
        return f'{self.prism_specs} - {self.prism_number}'

    def delete(self, *args, **kwargs):
        super(Prism_Inst, self).delete(*args, **kwargs)
        try:
            self.photo.storage.delete(self.photo.path)
        except:
            print('No files to delete')
class Mets_Specification(models.Model):
    mets_owner = models.ForeignKey(
        Company,
        on_delete=models.PROTECT
    )

    mets_model = models.ForeignKey(
        InstrumentModel,
        limit_choices_to=Q(inst_type__exact='baro') |
                         Q(inst_type__exact='thermo') |
                         Q(inst_type__exact='hygro') |
                         Q(inst_type__exact='psy'),
        on_delete=models.PROTECT
    )

    manu_unc_const = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Manufacturers stated accuracy = ±1°C, Uncertainty Constant = 1",
        verbose_name='manufacturers uncertainty constant'
    )

    manu_unc_k = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        default=2.00,
        verbose_name='manufacturers uncertainty coverage factor'
    )

    measurement_increments = models.DecimalField(
        max_digits=7, decimal_places=6,
        help_text="Resolution of the measurement eg. 0.0001"
    )

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['mets_model']
        unique_together = ('mets_model', 'mets_owner')

    def __str__(self):
        return f'({self.mets_model.inst_type}) {self.mets_model.make} {self.mets_model.model} ({self.mets_owner.company_abbrev})'


def get_upload_to_mets_photos(instance, filename):
    modified_date = date.today().strftime('%Y%m%d')
    filename = filename.split('\\')[-1]
    return 'InstrumentPhotos/%s/%s/%s/%s' % (
        instance.mets_specs.mets_owner.company_abbrev,
        instance.mets_number,
        modified_date,
        filename
    )


class Mets_Inst(models.Model):
    mets_specs = models.ForeignKey(
        Mets_Specification,
        on_delete=models.PROTECT,
        verbose_name='instrument specifications'
    )
    mets_number = models.CharField(
        max_length=15,
        validators=[validate_profanity],
        help_text="Enter the instrument serial number / unique ID",
        verbose_name='instrument number'
    )
    mets_custodian = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Name of instrument custodian",
        verbose_name='instrument custodian'
    )
    comment = models.CharField(
        validators=[validate_profanity],
        max_length=265, 
        null=True, blank=True)
    photo = models.FileField(
        upload_to=get_upload_to_mets_photos,
        null=True,
        blank=True,
        verbose_name='Instrument photo'
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['mets_specs']
        unique_together = ('mets_specs', 'mets_number')

    def get_absolute_url(self):
        return reverse('instruments:inst_mets_update', args=[str(self.id)])

    def __str__(self):
        return f'{self.mets_specs} - {self.mets_number}'

    def delete(self, *args, **kwargs):
        super(Mets_Inst, self).delete(*args, **kwargs)
        try:
            self.photo.storage.delete(self.photo.path)
        except:
            print('No files to delete')


def get_upload_to_edmi_certificate(instance, filename):
    modified_date = date.today().strftime('%Y%m%d')
    filename = filename.split('\\')[-1]
    return 'calibration_certificates/%s/%s/%s/%s' % (
        instance.edm.edm_specs.edm_owner.company_abbrev,
        instance.edm.edm_number,
        modified_date,
        filename
    )

class EDMI_certificate (models.Model):
    edm = models.ForeignKey(EDM_Inst, on_delete = models.PROTECT)
    prism = models.ForeignKey(Prism_Inst, on_delete = models.PROTECT)
    calibration_date = models.DateField(null=True, blank=True)

    scale_correction_factor = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(2.00000000)],
        help_text="If: Instrument Correction = 1.00000013.L + 0.0003, Scale Correction Factor = 1.00000013")
    scf_uncertainty = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        help_text="Uncertainty of the scale correction factor at 95% Confidence Level",
        verbose_name= 'scale correction factor uncertainty')
    scf_coverage_factor = models.FloatField(
        validators = [MinValueValidator(1.00), MaxValueValidator(5.00)],
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        default = 2.00,
        verbose_name= 'scale correction factor coverage factor')
    scf_std_dev = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        help_text="Standard deviation of the scale correction factor",
        verbose_name= 'scale correction factor standard deviation',
        null=True,blank = True)
                
    zero_point_correction = models.FloatField(
        validators = [MinValueValidator(-5.00000), MaxValueValidator(5.00000)],
        help_text="If: Instrument Correction (m) = 1.00000013.L + 0.0003, Zero Point Correction = 0.0003m",)
    zpc_uncertainty = models.FloatField(
        validators = [MinValueValidator(0.00000), MaxValueValidator(5.00000)],
        help_text="Uncertainty of the zero point correction (m) at 95% Confidence Level",
        verbose_name= 'zero point correction uncertainty')
    zpc_coverage_factor = models.FloatField(
        validators = [MinValueValidator(1.00), MaxValueValidator(5.00)],
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        default = 2.00,
        verbose_name= 'zero point correction coverage factor')
    zpc_std_dev = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        help_text="Standard deviation of the zero point correction",
        verbose_name= 'Zero point correction standard deviation',
        null=True,blank = True)
    
    has_cyclic_corrections = models.BooleanField(default=False,
        verbose_name= 'Enter cyclic error parameters',
        help_text="Click to toggle the input of cyclic error correction parameters")

    cyclic_one = models.FloatField(
        validators = [MinValueValidator(-5.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="The first order cyclic error parameter associated with the SIN() function",
        verbose_name= 'Cyclic error parameter 1',
        null=True, blank = True)
    cyc_1_uncertainty = models.FloatField(
        validators = [MinValueValidator(0.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="Uncertainty of the cyclic error parameter 1 at 95% Confidence Level",
        verbose_name= 'Cyclic error parameter 1 uncertainty',
        null=True, blank = True)
    cyc_1_coverage_factor = models.FloatField(
        validators = [MinValueValidator(1.00), MaxValueValidator(5.00)],
        default = 2.0,
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        verbose_name= 'Cyclic error parameter 1 coverage factor',
        null=True, blank = True)
    cyc_1_std_dev = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        default = 0,
        help_text="Standard deviation of the Cyclic error parameter 1",
        verbose_name= 'Cyclic error parameter 1 standard deviation',
        null=True, blank = True)

    cyclic_two = models.FloatField(
        validators = [MinValueValidator(-5.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="The first order cyclic error parameter associated with the COS() function",
        verbose_name= 'Cyclic error parameter 2',
        null=True, blank = True)
    cyc_2_uncertainty = models.FloatField(
        validators = [MinValueValidator(0.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="Uncertainty of the cyclic error parameter 2 at 95% Confidence Level",
        verbose_name= 'Cyclic error parameter 2 uncertainty',
        null=True, blank = True)
    cyc_2_coverage_factor = models.FloatField(
        validators = [MinValueValidator(1.00), MaxValueValidator(5.00)],
        default = 2.0,
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        verbose_name= 'Cyclic error parameter 2 coverage factor',
        null=True, blank = True)
    cyc_2_std_dev = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        default = 0,
        help_text="Standard deviation of the Cyclic error parameter 1",
        verbose_name= 'Cyclic error parameter 2 standard deviation',
        null=True, blank = True)

    cyclic_three = models.FloatField(
        validators = [MinValueValidator(-5.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="The second order cyclic error parameter associated with the SIN() function",
        verbose_name= 'Cyclic error parameter 3',
        null=True, blank = True)
    cyc_3_uncertainty = models.FloatField(
        validators = [MinValueValidator(0.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="Uncertainty of the cyclic error parameter 3 at 95% Confidence Level",
        verbose_name= 'Cyclic error parameter 3 uncertainty',
        null=True, blank = True)
    cyc_3_coverage_factor = models.FloatField(
        validators = [MinValueValidator(1.00), MaxValueValidator(5.00)],
        default = 2.0,
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        verbose_name= 'Cyclic error parameter 3 coverage factor',
        null=True, blank = True)
    cyc_3_std_dev = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        default = 0,
        help_text="Standard deviation of the Cyclic error parameter 1",
        verbose_name= 'Cyclic error parameter 3 standard deviation',
        null=True, blank = True)

    cyclic_four = models.FloatField(
        validators = [MinValueValidator(-5.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="The second order cyclic error parameter associated with the COS() function",
        verbose_name= 'Cyclic error parameter 4',
        null=True, blank = True)
    cyc_4_uncertainty = models.FloatField(
        validators = [MinValueValidator(0.00000), MaxValueValidator(5.00000)],
        default = 0,
        help_text="Uncertainty of the cyclic error parameter 4 at 95% Confidence Level",
        verbose_name= 'Cyclic error parameter 4 uncertainty',
        null=True, blank = True)
    cyc_4_coverage_factor = models.FloatField(
        validators = [MinValueValidator(1.00), MaxValueValidator(5.00)],
        default = 2.0,
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        verbose_name= 'Cyclic error parameter 4 coverage factor',
        null=True, blank = True)
    cyc_4_std_dev = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        default = 0,
        help_text="Standard deviation of the Cyclic error parameter 1",
        verbose_name= 'Cyclic error parameter 4 standard deviation',
        null=True, blank = True)
        
    standard_deviation = models.FloatField(
        validators = [MinValueValidator(0.00000), MaxValueValidator(10.00000)],
        help_text="Results of measurement standard deviation (m)")
    degrees_of_freedom = models.IntegerField(
        validators = [MinValueValidator(0), MaxValueValidator(500)],
        help_text="Degrees of freedom of calibration")

    certificate_upload = models.FileField(
        upload_to=get_upload_to_edmi_certificate,
        null=True,
        blank=True, 
        verbose_name= 'Calibration Record')
    html_report = models.TextField(blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        ordering = ['edm', 'calibration_date']

    def save(self, *args, **kwargs):
          self.scf_std_dev = self.scf_uncertainty / self.scf_coverage_factor
          self.zpc_std_dev = self.zpc_uncertainty / self.zpc_coverage_factor
          self.cyc_1_std_dev = self.cyc_1_uncertainty / self.cyc_1_coverage_factor
          self.cyc_2_std_dev = self.cyc_2_uncertainty / self.cyc_2_coverage_factor
          self.cyc_3_std_dev = self.cyc_3_uncertainty / self.cyc_3_coverage_factor
          self.cyc_4_std_dev = self.cyc_4_uncertainty / self.cyc_4_coverage_factor
          
          if self.has_cyclic_corrections == False:
              self.cyc_1_std_dev = 0
              self.cyc_2_std_dev = 0
              self.cyc_3_std_dev = 0
              self.cyc_4_std_dev = 0
              self.cyc_1_uncertainty = 0
              self.cyc_2_uncertainty = 0
              self.cyc_3_uncertainty = 0
              self.cyc_4_uncertainty = 0
              self.cyc_1_coverage_factor = 2
              self.cyc_2_coverage_factor = 2
              self.cyc_3_coverage_factor = 2
              self.cyc_4_coverage_factor = 2
              
          super(EDMI_certificate, self).save(*args, **kwargs)
         
    def get_absolute_url(self):
        return reverse('instrument_calibrations:EDMI-Certificate-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.edm} ({self.calibration_date.strftime("%Y-%m-%d")})'


def get_upload_to_mets_certificate(instance, filename):
    modified_date = date.today().strftime('%Y%m%d')
    filename = filename.split('\\')[-1]
    return 'calibration_certificates/%s/%s/%s/%s' % (
        instance.instrument.mets_specs.mets_owner.company_abbrev, 
        instance.instrument.mets_number, 
        modified_date, 
        filename)


class Mets_certificate (models.Model):
    instrument = models.ForeignKey(Mets_Inst, on_delete = models.PROTECT)
    calibration_date = models.DateField(null=True, blank=True)

    zero_point_correction = models.FloatField(
        validators = [MinValueValidator(-10.00), MaxValueValidator(10.00)],
        help_text="If: Correction to readings = Reading + 0.12°C, Zero point correction = 0.12")
    zpc_uncertainty = models.FloatField(
        validators = [MinValueValidator(0.00), MaxValueValidator(10.00)],
        help_text="Uncertainty of the zero point correction (m) at 95% Confidence Level",
        verbose_name= 'zero point correction uncertainty')
    zpc_coverage_factor = models.FloatField(
        validators = [MinValueValidator(1.00), MaxValueValidator(5.00)],
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        default = 2.00,
        verbose_name= 'zero point correction coverage factor')
    zpc_std_dev = models.FloatField(
        validators = [MinValueValidator(0.00000000), MaxValueValidator(10.00000000)],
        help_text="Standard deviation of the zero point correction",
        verbose_name= 'Zero point correction standard deviation',
        null=True,blank = True)

    degrees_of_freedom = models.IntegerField(
        validators = [MinValueValidator(0), MaxValueValidator(500)],
        help_text="Degrees of freedom of calibration " +
                  "For a Type B estimate use the following as a guide: "
                  " 3 for not very confident, "
                  "10 for moderate confidence, "
                  "30 for very confident.",
        default = 30)
    certificate_upload = models.FileField(
        upload_to=get_upload_to_mets_certificate,
        null=True,
        blank=True, 
        verbose_name= 'Calibration Record')
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['instrument', 'calibration_date']

    def save(self, *args, **kwargs):
         self.zpc_std_dev = self.zpc_uncertainty / self.zpc_coverage_factor
         super(Mets_certificate, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('instrument_calibrations:Mets-Certificate-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.instrument} ({self.calibration_date.strftime("%Y-%m-%d")})'


class Specifications_Recommendations(models.Model):
    source_ref = models.CharField(
        max_length=265,           
        verbose_name='Source reference')
    manufacturer = models.CharField(
        max_length=25,
        verbose_name='Manufacturer')
    model = models.CharField(
        max_length=25,
        verbose_name='Model')

    edm_type = models.CharField(
        max_length=2,
        choices=edm_types,
        default='ph',
        help_text='Instrument measurement type',
        verbose_name='EDM type',
        null=True, blank=True)
    manu_unc_const = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Accuracy = A mm ± B ppm, Uncertainty Constant = A",
        verbose_name='Manufacturers uncertainty constant',
        null=True, blank=True)
    units_manu_unc_const = models.CharField(        
        max_length=3,
        choices=length_units,
        null=True, blank=True)
        
    manu_unc_ppm = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Accuracy = A mm ± B ppm, Uncertainty ppm = B",
        verbose_name='Manufacturers ppm uncertainty',
        null=True, blank=True)
    units_manu_unc_ppm = models.CharField(        
       max_length=3,
       choices=scalar_units,
       null=True, blank=True)
    manu_unc_k = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Coverage factor at 95% Confidence Level eg. 2.0",
        default=2.0,
        verbose_name='Manufacturers uncertainty coverage factor',
        null=True, blank=True)

    unit_length = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(10000.0)],
        help_text="Unit Length (m)",
        verbose_name='Unit Length',
        null=True, blank=True)
    units_unit_length = models.CharField(        
       max_length=3,
       choices=length_units,
       null=True, blank=True)
    frequency = models.FloatField(
        validators=[MinValueValidator(1), MaxValueValidator(100000000)],
        help_text="Frequency (Hz)",
        verbose_name='Frequency',
        null=True, blank=True)
    units_frequency = models.CharField(        
       max_length=3,
       choices=freq_units,
       null=True, blank=True)
    carrier_wavelength = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Carrier Wavelength (nm)",
        verbose_name='Carrier wavelength',
        null=True, blank=True)
    units_carrier_wavelength = models.CharField(        
       max_length=3,
       choices=length_units,
       null=True, blank=True)
    manu_ref_refrac_index = models.FloatField(
        validators=[MinValueValidator(0.000000000), MaxValueValidator(2.000000000)],
        help_text="Manufacturers reference refractive index",
        verbose_name='Manufacturers reference refractive index',
        null=True, blank=True)

    c_term = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Coefficients C for first velocity correction eg 281.8",
        verbose_name='C term',        
        null=True, blank=True)
    d_term = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Coefficients D for first velocity correction eg 79.39",
        verbose_name='D term',     
        null=True, blank=True)
    
    remark = models.CharField(max_length=265, null=True, blank=True,
                              verbose_name='Remark')
    
    
    def __str__(self):
        return f'{self.manufacturer} - {self.model} ({self.source_ref})'