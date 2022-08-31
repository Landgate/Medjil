from django.urls import path
from . import views   

app_name = 'calibrationguide'

urlpatterns = [
    path('', views.guide_view, name='home'), 
    path('downloads/', views.guide_downloads, name='guide_downloads'), 
    path('guide_create/', views.guide_create, name='guide_create'),
    path('guide_update/<int:id>/', views.guide_update, name='guide_update'),
    # path('step_by_step_guide/', views.step_by_step_guide, name='step_by_step_guide'),   
]
