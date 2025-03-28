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
    
    # Detailed view
    path('site/<int:id>/view/', views.site_detailed_view, name = 'site-detail'),
    path('site/<int:id>/site_update/', views.site_update, name = 'site-update'),
    path('site/<int:id>/pillar_create/', views.pillar_create, name = 'pillar-create'),


    # pillar update
    path('each_pillar_update/<int:id>/<str:pk>', views.each_pillar_update, name = 'each_pillar_update'),
    # site json
    path('pin-create/get-site-json/<int:site>/', views.get_site_json, name = 'get-site-json'),
    
    # State
    path('get-states-json/<int:country>/', views.get_states_json, name = 'get-states-json'),
    path('get-locality-json/<int:state>/', views.get_locality_json, name = 'get-locality-json'),
]