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
"""Medjil URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
# import views
from . import views
from accounts.admin import admin_site as medjil_admin_site
from accounts.sites import medjil_super_site

# URL 
urlpatterns = [
    path('admin/', medjil_super_site.urls),                                # No mfa authentication for this site
    path('medjil-admin/', medjil_admin_site.urls),
    path('accounts/', include('accounts.urls')),
    path('calibrationsites/', include('calibrationsites.urls')),
    path('instruments/', include('instruments.urls')),
    path('rangecalibration/', include('rangecalibration.urls')),   
    path('staffcalibration/', include('staffcalibration.urls')),
    path('baseline_calibration/', include('baseline_calibration.urls')),
    path('backcapture/', include('backcapture.urls')),
    path('edm_calibration/', include('edm_calibration.urls')),
    path('calibrationguide/', include('calibrationguide.urls')),
    path('calibrationsitebooking/', include('calibrationsitebooking.urls')),
    path('', views.home, name='home'),
    path('terms/', views.terms, name='terms'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)