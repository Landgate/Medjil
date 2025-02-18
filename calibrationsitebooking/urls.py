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

app_name = 'calibrationsitebooking'

urlpatterns = [
    path('', views.booking_view, name='booking-view'), 
    path('site_booking/<slug:id>/', views.site_booking, name = 'site-booking'),
    path('site_booking/<slug:id>/delete/', views.site_booking_delete, name = 'site-booking-delete'),
    path('get-locations/<str:calibrationtype>', views.get_locations, name='get-locations'),
    path('get-calib-sites/<str:calibration_type>/<str:location>', views.get_calib_sites, name='get-calib-sites'),
    # path('site_booking/', views.site_booking, name = 'site-booking'),


]