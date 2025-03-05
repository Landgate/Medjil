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

app_name = 'calibrationguide'

urlpatterns = [
    # path('', views.guide_view1, name='guide_view1'), 
    path('', views.guide_view, name='guide_view'),
    path('get-content-url/<str:location>/<str:calibration_type>/', views.get_content_url, name='get-content-url'),
    path('create-guide/', views.guide_create, name='create-guide'),
    path('create-medjil-guide/', views.medjil_guide_create, name='create-medjil-guide'),
    path('create-medjil-calib-guide/', views.medjil_guide_to_calib_create, name='create-medjil-calib-guide'),
    
    path('manuals/', views.manual_view, name='manual_view'), 
    path('read_manual/<str:manual_name>', views.read_manual, name='read_manual'), 
]

