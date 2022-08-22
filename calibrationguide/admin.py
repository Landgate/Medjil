from django.contrib import admin

# Register your models here.
from .models import * 

@admin.register(CalibrationInstruction)
class CalibrationInstructionAdmin(admin.ModelAdmin):
    list_display = ['id','site_id', 'calibration_type', 'title','thumbnail','content','author']

@admin.register(InstructionImage)
class InstructionImageAdmin(admin.ModelAdmin):
    list_display = ['instruction', 'photos']