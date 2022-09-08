from django.urls import path, re_path
from . import views
#from .views import CreateInstrumentWizard      
from .forms import InstrumentModelCreateByInstTypeForm, DigitalLevelCreateForm, StaffCreateForm
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


urlpatterns = [
    path('', views.instruments_home, name = 'home'),
    # path('', views.instruments_levelling, name = 'home'),
    # Make & Models
    path('inst_make_create/', views.inst_make_create, name = 'inst_make_create'),
    path('inst_model_create/', views.inst_model_create, name = 'inst_model_create'),
    path('inst_model_createby_inst_type/<str:inst_type>/', views.inst_model_createby_inst_type, name = 'inst_model_createby_inst_type'),
    
    #EDMs
    path('inst_edm_create/', views.EDMCreateView.as_view(), name = 'edm_inst_create'),
    path('inst_edm_spec_create/', views.inst_edm_spec_create, name = 'inst_edm_spec_create'),
    path('inst_edm/<id>', views.inst_edm_detail, name = 'inst_edm_detail'),

    # Prisms
    path('inst_prism_create/', views.PrismCreateView.as_view(), name = 'prism_inst_create'),
    path('inst_prism_spec_create/', views.inst_prism_spec_create, name = 'inst_prism_spec_create'),
    # path('inst_spec_create/', views.inst_spec_create, name = 'inst_spec_create'),
    # path('inst_edm/<id>', views.inst_edm_detail, name = 'inst_edm_detail'),

    #Mets
    path('inst_mets_create/', views.MetsCreateView.as_view(), name = 'mets_inst_create'),
    path('inst_mets_spec_create/', views.inst_mets_spec_create, name = 'inst_mets_spec_create'),

    # Levelling staves
    path('inst_staff/<id>', views.inst_staff_detail, name = 'inst_staff_detail'),
    path('inst_staff_update/<id>/', views.inst_staff_update, name = 'inst_staff_update'),

    # Digital Level
    path('inst_level_create/', views.DigitalLevelCreateView.as_view(), name='inst_level_create'),
    path('inst_level_create_popup/', views.inst_level_create_popup, name = 'inst_level_create_popup'),
    path('inst_level/<id>', views.inst_level_detail, name = 'inst_level_detail'),
    path('inst_level_update/<id>/', views.inst_level_update, name = 'inst_level_update'),

    # Staves
    re_path(r'^inst_staff_create/(?P<step>.+)/$', staff_creation_wizard, name='sstep'),
    path('inst_staff_create/', staff_creation_wizard, name='inst_staff_create'),


    path('<id>/inst_model_update/', views.inst_model_update, name = 'inst_model_update'),
    path('<id>/inst_make_update/', views.inst_make_update, name = 'inst_make_update'),
]