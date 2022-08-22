from django.urls import path
from . import views
#from .views import CreateInstrumentWizard      

app_name = 'baseline_calibration'

urlpatterns = [
    path('', views.calibration_home, name = 'calibration_home'),
    path('calibrate_baseline/', views.calibrate_baseline, name = 'calibrate_baseline'),
    path('calibrate1/', views.calibrate1, name = 'calibrate1'),
    path('calibrate2/', views.calibrate2, name = 'calibrate2'),
    path('calibrate3/', views.calibrate3, name = 'calibrate3'),
    path('calibrate4/', views.calibrate4, name = 'calibrate4'),
    path('test/', views.test, name='test'),
    #path('adjust/<str:job_number>/', views.adjust, name='adjust'),
    #path('adjust/', views.adjust, name='adjust'),
]