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
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from .token_generator import account_activation_token
from django.core.mail import EmailMessage
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Lower
from django.contrib.auth.models import Group

from django.core.exceptions import ObjectDoesNotExist
from django_otp.plugins.otp_totp.models import TOTPDevice
from io import BytesIO
from base64 import b64encode, b32decode
import qrcode
import qrcode.image.svg
from django.core.exceptions import ValidationError
from django_otp import user_has_device

from common_func.validators import try_delete_protected
from .models import (
    Company, 
    CustomUser, 
    Calibration_Report_Notes)
from .forms import (
    SignupForm, 
    LoginForm, 
    OTPAuthenticationForm,
    CustomUserChangeForm, 
    CompanyForm, 
    calibration_report_notesForm)


# Create your views here.
def user_home(request):
    return HttpResponse("This is my homepage")

# Send activation link
def activation_sent(request):
    return render(request, 'registration/activation_sent.html')

# Generate activation link
def activate_account(request, uidb64, token):
    try:
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        # login(request, user)
        messages.success(request, 'Your account has been activated successfully. You can now log in.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Your activation link appears to be invalid.')
        return redirect('accounts:signup')

# User Registration
def user_signup(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('accounts:login')
    if request.method=="POST":
        form = SignupForm(data = request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            user = form.save(commit=False)
            user.is_active = False
            
            if user.company.company_abbrev == "OTH":
                company_name = request.POST['company_name']
                company_abbrev = request.POST['company_abbrev'].upper()
                if Company.objects.get(company_name__exact = company_name):
                    user.company = Company.objects.get(company_name__exact = company_name)
                else: 
                    Company.objects.update_or_create(
                        company_name = company_name,
                        company_abbrev = company_abbrev
                    )
                    user.company = Company.objects.get(company_name__exact = company_name)
            user.save()

            # Assign Groups
            geodesy_group = ['kent.wheeler@landgate.wa.gov.au', 
                                'khandu.k@landgate.wa.gov.au', 
                                'khandu@landgate.wa.gov.au', 
                                'vanessa.ung@landgate.wa.gov.au', 
                                'brendon.hellmund@landgate.wa.gov.au',
                                'tony.castelli@landgate.wa.gov.au', 
                                'ireneusz.baran@landgate.wa.gov.au',
                                'irek.baran@landgate.wa.gov.au'
                            ]
            if email.endswith('landgate.wa.gov.au'):
                user.groups.add(Group.objects.get(name = 'Landgate'))
            else:
                user.groups.add(Group.objects.get(name = 'Others'))
            # Assign to geodesy group
            if email in geodesy_group:
                user.groups.add(Group.objects.get(name = 'Geodesy'))
                user.is_staff = True
            user.save()
            
            # Send activation code to log in
            current_site = get_current_site(request)
            email_subject = 'Activate Your Account'
            message = render_to_string('registration/activate_account.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)), #.decode(),
                'token': account_activation_token.make_token(user),
            })
            to_email = email # form.cleaned_data.get('email')
            email = EmailMessage(email_subject, message, to=[to_email])
            email.send()
            
            return redirect('accounts:activation_sent')
        elif request.user.is_authenticated:
                return redirect('/')
    else: 
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form':form})

# User log in
def user_login(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('/')
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(email = email, password=password)
            if user is not None:
                if user.is_active:
                    request.session['email'] = email
                    if 'next' in request.POST:
                        request.session['next'] = request.POST.get('next')
                    else: 
                        request.session['next'] = None
                    try:
                        device = TOTPDevice.objects.get(user=user)
                        # print(device)
                        return redirect('accounts:otp_verify')
                    except TOTPDevice.DoesNotExist:
                        # return HttpResponse('No device found. Set up device!')#redirect('register-device')
                        # # print(user)
                        # # login(request, user)
                        # if 'next' in request.POST:
                        #     return redirect(request.POST.get('next'))
                        # else:
                        #     return redirect('accounts:user_account')
                        return redirect('accounts:otp_register')
                else:
                    current_site = get_current_site(request)
                    email_subject = 'Please activate your account again.'
                    message = render_to_string('registration/activate_account.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)), #.decode(),
                        'token': account_activation_token.make_token(user),
                    })
                    to_email = form.cleaned_data.get('email')
                    email = EmailMessage(email_subject, message, to=[to_email])
                    email.send()
                    return redirect('accounts:activation_sent')
            else:
                messages.error(request, "Please check the login details.")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'login_form': form})

def otp_verify(request):
    form = OTPAuthenticationForm(user=request.user, data=request.POST)
    if request.method == 'POST':
        # form = OTPAuthenticationForm(request, data=request.POST)
        email = request.session['email']
        if form.is_valid():
            otp_token= request.POST.get('otp_token') # int(request.POST.get('otp_token'))
            otp_token = int(otp_token)
            user =  get_object_or_404(CustomUser, email=email)
            try:
                # Get Device
                device = TOTPDevice.objects.get(user=user)
                # Verify the OTP
                if device.verify_token(otp_token):
                    user.verified = True
                    user.save()
                    login(request, user)
                    messages.success(request, 'OTP verified successfully!')
                    if request.session['next']:
                        return redirect(request.session['next'])
                    else:
                        return redirect('accounts:user_account')
                else:
                    messages.warning(request, 'Invalid OTP. Please use the correct OTP device to verify!')
                    return redirect('accounts:login')
            except TOTPDevice.DoesNotExist:
                messages.error(request, 'OTP device not found. Please set up OTP first!')
        else:
            return HttpResponse('Form is not valid')
    return render(request, 'accounts/otp_form.html', {'otp_form': form})
    
def otp_register(request):
    context = {}
    user = get_object_or_404(CustomUser, email=request.session['email'])
    if user.first_name:
        username = user.first_name
    else:
        username = user.email

    if not user_has_device(user=user):
        totp_device = TOTPDevice.objects.create(user=user)
        image_factory = qrcode.image.svg.SvgPathImage
        qr_code_data = qrcode.make(
            totp_device.config_url,
            image_factory=image_factory
        ).to_string().decode('utf_8')
        context = {
            'username' : username,
            'qr_code_data' : qr_code_data
        }
        return render(request, 'accounts/otp_qr_code.html', context)
    else:
        messages.warning(request, 'Your device is already registered. Please login!')
        return redirect('accounts:login')


# User log out
def user_logout(request):
    logout(request)
    return redirect('home')

# Update user 
def user_profile(request):
    if request.method=='POST':
        form = CustomUserChangeForm(data=request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect ('accounts:user_account')
    else:
        form = CustomUserChangeForm(instance = request.user)
    return render(request, 'accounts/user_profile_update.html', {'form': form})

# Update user - possible by admin/staff only
def user_update_for_admin(request, email):
    user = get_object_or_404(CustomUser, email=email)
    form = CustomUserChangeForm(request.POST or None, instance = user)
    if form.is_valid():
        obj= form.save(commit= False)
        obj.save()
        return redirect ('accounts:user_account')
    context = {
        'form': form
        }
    return render(request, 'accounts/user_profile_update.html', context)

# Delete user - possible by admin/staff only
def user_delete_for_admin(request, email):
    this_user = get_object_or_404(CustomUser, email=email)
    try_delete_protected(request, this_user)

    return redirect('accounts:user_account')

# Update company - possible by admin/staff only
def company_create(request):
    form = CompanyForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect ('accounts:user_account')
    context = {
        'form': form
        }
    return render(request, 'accounts/company_create.html', context)

def company_update(request, id):
    company = Company.objects.get(id=id)
    form = CompanyForm(request.POST or None, instance = company)
    if form.is_valid():
        form.save()
        return redirect ('accounts:user_account')
    context = {
        'form': form
        }
    return render(request, 'accounts/company_update.html', context)

# Delete company - possible by admin/staff only
def company_delete(request, id):
    try:
        company = Company.objects.get(id=id)
        try_delete_protected(request, company)
        return redirect('accounts:user_account')
    except ObjectDoesNotExist:
        return redirect('/accounts')

# Account information
@login_required(login_url="/accounts/login")
def user_account(request):
    # my profile
    this_user = get_object_or_404(CustomUser, email=request.user.email)

    # other users
    if request.user.is_staff:
        user_list = CustomUser.objects.all().exclude(is_staff=True).order_by('id')
    else:
        user_list = CustomUser.objects.filter(company=request.user.company).order_by('date_joined')
    user_page = Paginator(user_list, 25) # Show 25 list per page.
    user_page_number = request.GET.get('page')
    user_page_obj = user_page.get_page(user_page_number)

    # company list
    company_list = Company.objects.exclude(company_abbrev__exact='OTH').order_by(Lower('company_name'))
    company_page = Paginator(company_list, 25) # Show 25 list per page.
    company_page_number = request.GET.get('page')
    company_page_obj = company_page.get_page(company_page_number)
    
    context = {
        'this_user': this_user,
        'user_page_obj': user_page_obj,
        'company_page_obj': company_page_obj,
        # 'staff_list': staff_list,
    }
    return render(request, 'accounts/user_accounts.html', context)


@login_required(login_url="/accounts/login")
def calibration_report_notes_list(request, report_disp):

    report_types = [{'abbr':x[0], 'name':x[1]} 
                  for x in Calibration_Report_Notes.report_type.field.choices]
    
    if report_disp == 'B':
        note_list = (Calibration_Report_Notes.objects.filter(
            report_type = 'B')
            .order_by('note_type', 'company'))
        
    if report_disp == 'E':
        note_list = (Calibration_Report_Notes.objects.filter(
            report_type = 'E')
            .order_by('note_type', 'company'))
        
    context = {
        'report_disp': report_disp,
        'report_types': report_types,
        'note_list': note_list
    }
    return render(request, 'accounts/calibration_report_notes_list.html', context)
    
    
@login_required(login_url="/accounts/login")
def calibration_report_notes_edit(request, report_disp, id):
    if id == 'None':
        form = calibration_report_notesForm(
            request.POST or None, user=request.user)
    else:
        obj = get_object_or_404(Calibration_Report_Notes, id = id)
        form = calibration_report_notesForm(
            request.POST or None,
            instance = obj, user = request.user)
    
    if not form.is_valid():
        context = {'form': form}
        tmplate = 'accounts/calibration_report_notes_edit.html'
        return render(request, tmplate, context) 
    
    else:
        obj = form.save(False)
        obj.report_type = report_disp
        obj.save()
        
        return redirect ('accounts:calibration_report_notes_list', report_disp=report_disp)


@login_required(login_url="/accounts/login")
def calibration_report_notes_delete(request, report_disp, id):
    
    delete_obj = Calibration_Report_Notes.objects.get(id=id)
    try_delete_protected(request, delete_obj)
    
    return redirect ('accounts:calibration_report_notes_list', report_disp=report_disp)
    