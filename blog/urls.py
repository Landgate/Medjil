from django.urls import path, re_path
from . import views 

from .forms import ContactForm1, ContactForm2

app_name = 'blog'


named_contact_forms = (
    ('contactdata', ContactForm1),
    ('leavemessage', ContactForm2),
)
contact_wizard = views.ContactWizard.as_view(named_contact_forms,
    condition_dict={'leavemessage': views.show_message_form_condition}, 
    url_name='blog:contact_step')


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/<int:pk>/edit', views.post_edit, name='post_edit'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new', views.post_new, name='post_new'),
    re_path(r'^contact/(?P<step>.+)/$', contact_wizard, name='contact_step'),
    path('contact/', contact_wizard, name='contact'),
]