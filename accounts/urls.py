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
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', RedirectView.as_view(url='/', permanent=False), name='home'),
    path('user_account/', views.user_account, name ='user_account'),
    path('signup/', views.user_signup, name='signup'),
    path('sent/', views.activation_sent, name = 'activation_sent'),
    path('activate/<slug:uidb64>/<slug:token>/', views.activate_account, name='activate_account'),
    path('login/', views.user_login, name='login'),
    path('otp_verify/', views.otp_verify, name = 'otp_verify'),
    path('otp_register/', views.otp_register, name = 'otp_register'),
    path('logout/', views.user_logout, name = 'logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name = "registration/password_reset_email.html",
        success_url = reverse_lazy("accounts:password_reset_done")), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view( template_name="registration/password_reset_done.html"), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>', views.CustomPasswordResetConfirmView.as_view( template_name="registration/password_reset_confirm.html",
        success_url = reverse_lazy("accounts:password_reset_complete")), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view( template_name="registration/password_reset_complete.html"), name='password_reset_complete'),
    path('user_profile/', views.user_profile, name='user_profile'),
    path('user_profile/<email>/', views.user_update_for_admin, name='user_update_for_admin'),
    path('user_accounts/accounts/<email>/delete', views.user_delete_for_admin, name='user_delete_for_admin'),
    path('company/<id>/update', views.company_update, name = 'company_update'),
    path('company/<id>/delete', views.company_delete, name = 'company_delete'),
    path('company/create', views.company_create, name = 'company_create'),
    
    path('calibration_report_notes/<slug:report_disp>/', 
         views.calibration_report_notes_list, 
         name='calibration_report_notes_list'),
    path('calibration_report_notes/<slug:report_disp>/<slug:id>/edit', 
         views.calibration_report_notes_edit, 
         name = 'calibration_report_notes_edit'),
    path('calibration_report_notes/<slug:report_disp>/<id>/delete', 
         views.calibration_report_notes_delete,
         name = 'calibration_report_notes_delete'),
]