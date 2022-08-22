"""InstrumentCalibration URL Configuration

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

# URL 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('geodeticnews/', include('geodeticnews.urls')),
    path('calibrationsites/', include('calibrationsites.urls')),
    path('instruments/', include('instruments.urls')),
    path('rangecalibration/', include('rangecalibration.urls')),   
    path('staffcalibration/', include('staffcalibration.urls')),  
    path('baseline_calibration/', include('baseline_calibration.urls')),
    path('edm_calibration/', include('edm_calibration.urls')),
    path('calibrationguide/', include('calibrationguide.urls')),
    path('blog/', include('blog.urls')),
    path('', views.home, name='home'),
    path('terms/', views.terms, name='terms'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)