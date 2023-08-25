from django.urls import path, re_path
from . import views
#from .views import CreateInstrumentWizard      
from .forms import StaffCreateForm
from staffcalibration.forms import StaffCalibrationRecordFormOnTheGo

# url links below
app_name = 'instruments'

STAFFFORM = [
                ("inst_staff_form", StaffCreateForm),
                ("inst_staff_record_form", StaffCalibrationRecordFormOnTheGo),
                ] 

staff_creation_wizard = views.StaffCreationWizard.as_view(STAFFFORM, 
                            condition_dict={'inst_staff_record_form': views.show_calibrated_form_condition},
                            url_name = 'instruments:sstep')

staff_creation_wizard_popup = views.StaffCreationWizardPopUp.as_view(STAFFFORM, 
                            condition_dict={'inst_staff_record_form': views.show_calibrated_form_condition},
                            url_name = 'instruments:sstep')

urlpatterns = [
    # Global Settings
    path('settings/', views.instrument_settings, name = 'inst_settings'),
    path('get_inst_model_json/<str:inst_make>/', views.get_inst_model_json, name = 'get_inst_model_json'),
    
    # Instrument Register
    path('instrument_register/<slug:inst_disp>/', views.instrument_register, name='home'),
    path('instrument_register/<slug:inst_disp>/<slug:tab>/<slug:id>/edit/', views.register_edit, name = 'register_edit'),
    path('instrument_register/<slug:inst_disp>/<slug:tab>/<id>/delete/', views.register_delete, name = 'register_delete'),
    
    
    # Make & Models
    path('inst_model_createby_inst_type/<str:inst_type>/', views.inst_model_createby_inst_type, name = 'inst_model_createby_inst_type'),
    path('edm_recommended_specifications/', views.edm_recommended_specs, name = 'edm_recommended_specs'),
    
    # Digital Level
    path('inst_level_create/', views.DigitalLevelCreateView.as_view(), name='inst_level_create'),
    path('inst_level_create_popup/', views.inst_level_create_popup, name = 'inst_level_create_popup'),

    # Levelling Staves
    re_path(r'^inst_staff_create/(?P<step>.+)/$', staff_creation_wizard, name='sstep'),
    path('inst_staff_create/', staff_creation_wizard, name='inst_staff_create'),
    path('inst_staff/<id>/update', views.inst_staff_update, name = 'inst_staff_update'),
    path('inst_staff/<id>/delete/', views.inst_staff_delete, name = 'inst_staff_delete' ),
    # popup staff
    re_path(r'^inst_staff_create_popup/(?P<step>.+)/$', staff_creation_wizard_popup, name='sstep'),
    path('inst_staff_create_popup/', staff_creation_wizard_popup, name='inst_staff_create_popup'),

    path('<id>/inst_model_update/', views.inst_model_update, name = 'inst_model_update'),
    path('<id>/inst_model_delete/', views.inst_model_delete, name = 'inst_model_delete'),
        
]