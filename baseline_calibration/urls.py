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
#from .views import CreateInstrumentWizard      

app_name = 'baseline_calibration'

urlpatterns = [
    path('', views.calibration_home, name = 'calibration_home'),
    path('calibrate1/<slug:id>', views.calibrate1, name = 'calibrate1'),
    path('calibrate2/<int:id>', views.calibrate2, name = 'calibrate2'),
    path('report/<int:id>', views.report, name = 'report'),
    path('pillar_survey_del/<int:id>', views.pillar_survey_del, name = 'pillar_survey_del'),
    path('bulk_report_download/', views.bulk_report_download, name = 'bulk_report_download'),
    
    path('uc_budgets/', views.uc_budgets, name = 'uc_budgets'),
    path('uc_budget/create/', views.uc_budget_create, name = 'uc_budget_create'),
    path('uc_budget/<int:id>/edit/', views.uc_budget_edit, name = 'uc_budget_edit'),
    path('uc_budget/<int:id>/delete/', views.uc_budget_delete, name = 'uc_budget_delete'),
    
    path('accreditations/', views.accreditations, name = 'accreditations'),
    path('accreditations/<slug:id>/edit/', views.accreditation_edit, name = 'accreditation_edit'),
    path('accreditations/<int:id>/delete/', views.accreditation_delete, name = 'accreditation_delete'),

    path('certified_distances/<int:id>', views.certified_distances_home, name = 'certified_distances_home'),
    path('certified_distances/<int:id>/edit/', views.certified_distances_edit, name = 'certified_distances_edit'),

]