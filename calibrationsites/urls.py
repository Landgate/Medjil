from django.urls import path, re_path
from . import views
#from .views import CreateInstrumentWizard   
#
from .forms import CalibrationSiteForm, AddPillarFormSet
# from .forms import ContactForm1, ContactForm2


app_name = 'calibrationsites'

FORMS = [("site_form", CalibrationSiteForm),
        ("pillar_form", AddPillarFormSet),
        ] 
site_creation_wizard = views.CreateCalibrationSiteWizard.as_view(FORMS, 
                            url_name = 'calibrationsites:lstep')

urlpatterns = [
    path('', views.site_home, name = 'home'),

    # path('site-create/', views.site_create, name = 'site-create'),
    path('site/country_create/', views.country_create, name = 'country_create'),
    path('site/state_create/', views.state_create, name = 'state_create'),
    path('site/locality_create/', views.locality_create, name = 'locality_create'),

    re_path(r'^create-site/(?P<step>.+)/$', site_creation_wizard, name='lstep'),
    path('create-site/', site_creation_wizard, name='create-site'),


    # path('create-site/', views.CreateCalibrationSiteWizard.as_view(FORMS), name = 'create-site'),
    # path('site/test/', views.test_view, name = 'test'),
    
    path('site/<int:id>/site_update', views.site_update, name = 'site-update'),
    path('site/<int:id>/pillar_create/', views.pillar_create, name = 'pillar-create'),

    # Detailed view
    path('site/<int:id>/view/', views.site_detailed_view, name = 'site-detail'),
    # path('create-site/', views.CalibrateSiteFormWizard.as_view(), name='create-site'),

    # pillar update
    path('each_pillar_update/<int:id>/<str:pk>', views.each_pillar_update, name = 'each_pillar_update'),
    path('update_pillar/<int:id>', views.PillarUpdateView.as_view(), name = 'update_pillar'),
    # site json
    path('pin-create/get-site-json/<int:site>/', views.get_site_json, name = 'get-site-json'),
    
    # State
    # path('site/get-states-json/<int:country>/', views.get_states_json, name = 'get-states-json'),

    path('get-states-json/<int:country>/', views.get_states_json, name = 'get-states-json'),
    path('get-locality-json/<int:state>/', views.get_locality_json, name = 'get-locality-json'),
]