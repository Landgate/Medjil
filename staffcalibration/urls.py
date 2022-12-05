
from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views 

app_name = 'staffcalibration'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    # path('', RedirectView.as_view(url='/', permanent=False), name='home'),
    path('create_record/', views.create_record, name = 'create_record'),
    path('calibrate/', views.calibrate, name = 'calibrate'),
    path('print_report/<str:id>/', views.print_report, name='print_report'),
    path('staff_registry/', views.user_staff_registry, name='staff_registry'),
]