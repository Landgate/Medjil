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

from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views 

app_name = 'staffcalibration'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    # path('', RedirectView.as_view(url='/', permanent=False), name='home'),
    path('create_record/', views.create_record, name = 'create_record'),
    path('delete_record/<str:id>/', views.delete_record, name = 'delete_record'),
    path('calibrate/', views.calibrate, name = 'calibrate'),
    path('print_report/<str:id>/', views.print_report, name='print_report'),
    path('staff_registry/', views.user_staff_registry, name='staff_registry'),
]