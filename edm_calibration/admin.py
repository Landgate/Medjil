from django.contrib import admin

# Register your models  here.
from .models import * 

admin.site.register(uPillar_Survey)

admin.site.register(uEDM_Observation)

admin.site.register(uCalibration_Parameter)