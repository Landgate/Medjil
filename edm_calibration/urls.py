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

app_name = 'edm_calibration'

urlpatterns = [
    path('', views.edm_calibration_home, name = 'edm_calibration_home'),
    path('calibrate1/<slug:id>', views.calibrate1, name = 'calibrate1'),
    path('calibrate2/<int:id>', views.calibrate2, name = 'calibrate2'),
    path('certificate/<int:id>', views.certificate, name = 'certificate'),
    path('report/<int:id>', views.report, name = 'report'),
    path('pillar_survey_del/<int:id>', views.pillar_survey_del, name = 'pillar_survey_del'),
    path('clear_cache/', views.clear_cache, name='clear_cache'),
    
]