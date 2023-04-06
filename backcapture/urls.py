from django.urls import path
from . import views 

app_name = 'backcapture'

urlpatterns = [
    path('', views.import_dli, name = 'import_home'),

 
]