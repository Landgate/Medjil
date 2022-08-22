from django.urls import path
from . import views
#from .views import CreateInstrumentWizard      

app_name = 'baseline_calibration'

urlpatterns = [
    path('', views.calibration_home, name = 'calibration_home'),
    path('calibrate1/<slug:id>', views.calibrate1, name = 'calibrate1'),
    path('calibrate2/<int:id>', views.calibrate2, name = 'calibrate2'),
    path('pillar_survey_del/<int:id>', views.pillar_survey_del, name = 'pillar_survey_del'),
    path('uc_budgets/', views.uc_budgets, name = 'uc_budgets'),
    path('uc_budget/create/', views.uc_budget_create, name = 'uc_budget_create'),
    path('uc_budget/<int:id>/edit/', views.uc_budget_edit, name = 'uc_budget_edit'),
    path('uc_budget/<int:id>/delete/', views.uc_budget_delete, name = 'uc_budget_delete'),
    
]