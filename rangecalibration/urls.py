from django.urls import path
from . import views
from .forms import (
        RangeForm1,
        RangeForm2,
        # RangeForm3,
    )
#from .views import CreateInstrumentWizard      

app_name = 'rangecalibration'

FORMS = [("prefill_form", RangeForm1),
         ("upload_data", RangeForm2),
        #  ("process_data", RangeForm3),
        ] 
        
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('range-guide/', views.view_user_guide, name='user_guide'),
    path('calibrate/', views.RangeCalibrationWizard.as_view(FORMS), name='calibrate'),
    path('adjust/<str:id>/', views.adjust, name='adjust'),
    path('print-record/<str:id>/', views.print_record, name='print_record'),
    path('delete-record/<str:id>/', views.delete_record, name='delete_record'),
    path('range-param/', views.range_param_process, name='range_param'),
]