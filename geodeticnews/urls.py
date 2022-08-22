from django.urls import path, re_path
from . import views
#from .views import CreateInstrumentWizard   
#

app_name = 'geodeticnews'

urlpatterns = [
    path('', views.news_home, name = 'home'),
    path('geodeticnews/<int:pk>', views.NewsDetailView.as_view(), name='news-detail'),
]