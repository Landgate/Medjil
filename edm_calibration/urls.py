from django.urls import path
from . import views   

app_name = 'edm_calibration'

urlpatterns = [
    path('', views.edm_calibration_home, name = 'edm_calibration_home'),
    path('calibrate1/<slug:id>', views.calibrate1, name = 'calibrate1'),
    path('calibrate2/<int:id>', views.calibrate2, name = 'calibrate2'),
    path('pillar_survey_del/<int:id>', views.pillar_survey_del, name = 'pillar_survey_del'),
    path('clear_cache/', views.clear_cache, name='clear_cache'),
    
]