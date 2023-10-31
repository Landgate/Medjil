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