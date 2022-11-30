from django.db import models
from PIL import Image as PilImage
# Create your models here.
from accounts.models import CustomUser
from calibrationsites.models import CalibrationSite
# Define UserGuide Type

CHOICES = (
    (None, '--- Select Type ---'),
    ('Site Calibration', (
        ('baseline', 'EDM Baselines'),
        ('range', 'Staff Calibration Ranges'),
    )),
    ('Instrument Calibration', (
        ('edmi', 'Electronic Distance Measurements'),
        ('staff', 'Barcoded Staves'),
    )),
)
    
# calibration_types = (
#         (None, '--- Select Type ---'),
#         ('site', 'Site Calibration'),
#         ('inst', 'Instrument Calibration'),
#     )

# category_types = (
#         (None, '--- Select Type ---'),
#         ('site_baseline', 'EDM Baseline'),
#         ('site_range', 'Staff Calibration Range'),
#         ('inst_edmi','Electronic Distance Measurement'),
#         ('inst_staff','Barcode Staves'), 
#     )

def get_upload_to_thumbnail(instance, filename):
    return '%s/%s/%s/%s/%s' % ('CalibrationInstruction', 
                                instance.site_id.site_name.capitalize(), 
                                instance.calibration_type, 
                                instance.title, 
                                'thumbnail_'+filename)

class CalibrationInstruction(models.Model):
    calibration_type = models.CharField(max_length=24,
                                choices=CHOICES,
                                null=True,
                                verbose_name = 'Calibration Type')
    # category_type = models.CharField(max_length=24,
    #                             choices=category_types,
    #                             null=True,
    #                             verbose_name = 'Choose Category')
    site_id = models.ForeignKey(CalibrationSite,
                                on_delete=models.CASCADE,
                                null = True,
                                verbose_name = 'Calibration Site')
    title = models.CharField(max_length=200, unique=True)
    thumbnail = models.ImageField(upload_to = get_upload_to_thumbnail, 
                                    blank=True, 
                                    verbose_name='Thumbnail')
    content = models.TextField()
    author = models.ForeignKey(CustomUser, 
                                on_delete=models.SET_NULL, 
                                null=True)
    pub_date = models.DateTimeField(auto_now_add=True, 
                                    null=True, 
                                    verbose_name = 'Published on')
    mod_date = models.DateTimeField(auto_now=True, 
                                    null=True, 
                                    verbose_name = 'Last Modified')

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("calibrationguide:detail", args=[self.id])
    
    def save(self, *args, **kwargs):
        super(CalibrationInstruction, self).save(*args, **kwargs)
        img = PilImage.open(self.thumbnail.path)
        if img.width > 250 and img.height> 180:
            output_size = (250, 180)
            img.thumbnail(output_size)
            img.save(self.thumbnail.path)
        else:
            img.save(self.thumbnail.path)

def get_upload_to_images(instance, filename):
    return '%s/%s/%s/%s/%s' % ('CalibrationInstruction', 
                                instance.instruction.site_id.site_name.capitalize(), 
                                instance.instruction.calibration_type, 
                                instance.instruction.title, 
                                filename)

class InstructionImage(models.Model):
    instruction = models.ForeignKey(CalibrationInstruction, 
                                    on_delete=models.CASCADE)
    photos = models.ImageField(upload_to = get_upload_to_images,
                                null=True,
                                blank=True)

    def save(self, *args, **kwargs):
        super(InstructionImage, self).save(*args, **kwargs)
        img = PilImage.open(self.photos.path)
        if img.width > 1920 and img.height> 1080:
            output_size = (1920, 1080)
            img.photos(output_size)
            img.save(self.photos.path)
        else:
            img.save(self.photos.path)

def get_upload_thumbnail_to_manual(instance, filename):
    return '%s/%s/%s/%s' % ('TechnicalManual', 
                                instance.manual_type, 
                                instance.title, 
                                'thumbnail_'+filename)

CHOICES2 = (
    (None, '--- Select Type ---'),
    ('tbaseline', 'EDM Baselines'),
    ('tedmi', 'Electronic Distance Measurements'),
    ('trange', 'Staff Calibration Range'),
    ('tstaff', 'Barcoded Staves'),
)

class TechnicalManual(models.Model):
    manual_type = models.CharField(max_length=24,
                                choices=CHOICES2,
                                null=True,
                                verbose_name = 'Type')
    # site_id = models.ForeignKey(CalibrationSite,
    #                             on_delete=models.CASCADE,
    #                             null = True,
    #                             verbose_name = 'Calibration Site')
    title = models.CharField(max_length=200, unique=True)
    thumbnail = models.ImageField(upload_to = get_upload_thumbnail_to_manual, 
                                    blank=True, 
                                    verbose_name='Thumbnail')
    content = models.TextField()
    author = models.ForeignKey(CustomUser, 
                                on_delete=models.SET_NULL, 
                                null=True)
    pub_date = models.DateTimeField(auto_now_add=True, 
                                    null=True, 
                                    verbose_name = 'Published on')
    mod_date = models.DateTimeField(auto_now=True, 
                                    null=True, 
                                    verbose_name = 'Last Modified')

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("calibrationguide:manual-detail", args=[self.id])
    
    def save(self, *args, **kwargs):
        super(TechnicalManual, self).save(*args, **kwargs)
        img = PilImage.open(self.thumbnail.path)
        if img.width > 250 and img.height> 180:
            output_size = (250, 180)
            img.thumbnail(output_size)
            img.save(self.thumbnail.path)
        else:
            img.save(self.thumbnail.path)

def get_upload_images_to_manual(instance, filename):
    return '%s/%s/%s/%s' % ('TechnicalManual', 
                                instance.manual.manual_type, 
                                instance.manual.title, 
                                filename)

class ManualImage(models.Model):
    manual = models.ForeignKey(TechnicalManual, 
                                    on_delete=models.CASCADE)
    photos = models.ImageField(upload_to = get_upload_images_to_manual,
                                null=True,
                                blank=True)

    def save(self, *args, **kwargs):
        super(ManualImage, self).save(*args, **kwargs)
        img = PilImage.open(self.photos.path)
        if img.width > 1920 and img.height> 1080:
            output_size = (1920, 1080)
            img.photos(output_size)
            img.save(self.photos.path)
        else:
            img.save(self.photos.path)

   