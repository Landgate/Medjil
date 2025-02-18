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

'''
from django.urls import path
from . import views   

app_name = 'edm_calibration'

urlpatterns = [
    path('', views.edm_calibration_home, name = 'edm_calibration_home'),
    path('certificate/<int:id>', views.certificate, name = 'certificate'),
    path('report/<int:id>', views.report, name = 'report'),
    path('bulk_report_download/', views.bulk_report_download, name = 'bulk_report_download'),
    path('intercomparison_home', views.intercomparison_home, name = 'intercomparison_home'),
    path('intercomparison/<slug:id>', views.intercomparison, name = 'intercomparison'),
    path('intercomparison_report/<int:id>', views.intercomparison_report, name = 'intercomparison_report'),
    path('intercomparison/delete/<int:id>', views.intercomparison_del, name = 'intercomparison_del'),
    
    #paths for computing a calibration
    path('survey/create', views.survey_create, name = 'upillar_survey_create'),
    path('survey/<int:id>/update', views.survey_create, name = 'upillar_survey_update'),
    path('survey/<int:id>/delete', views.survey_delete, name = 'upillar_survey_delete'),
    path('edm_observations/<int:id>/update', views.edm_observations_update, name = 'edm_observations_update'),
    path('survey/<int:id>/compute_calibration', views.compute_calibration, name = 'compute_calibration'),
]