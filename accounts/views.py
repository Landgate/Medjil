from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .token_generator import account_activation_token
from django.core.mail import EmailMessage
from django.contrib import messages
from django.core.paginator import Paginator

# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Group
from .models import Company, CustomUser
from staffcalibration.models import StaffCalibrationRecord
from .forms import SignupForm, LoginForm, CustomUserChangeForm, CompanyForm


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
            # print(user.company.company_abbrev)
            
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
            # print(email)
            password = form.cleaned_data.get('password')
            user = authenticate(email = email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if 'next' in request.POST:
                        return redirect(request.POST.get('next'))
                    else:
                        return redirect('accounts:user_account')
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
                return redirect('/')
            return redirect('/')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'login_form': form})

# User log out
def user_logout(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/')

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
    try:
        this_user = get_object_or_404(CustomUser, email=email)
        this_user.delete()
        messages.success(request, email + ' has been successfully deleted.')
    except ObjectDoesNotExist:
        messages.warning(request, 'This user cannot be deleted.')

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
        company.delete()
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
    company_list = Company.objects.exclude(company_abbrev__exact='OTH').order_by('company_name')
    company_page = Paginator(company_list, 25) # Show 25 list per page.
    company_page_number = request.GET.get('page')
    company_page_obj = company_page.get_page(company_page_number)
    
    # Calibrated Instruments # Staff
    # staff_list = Staff.objects.filter(staff_owner__exact=request.user.company, calibration_date__isnull=False).distinct().order_by('staff_model'), '-calibration_date')[:10]
    staff_list = StaffCalibrationRecord.objects.filter(inst_staff__staff_owner=request.user.company).distinct().order_by('inst_staff__staff_model')


    context = {
        'this_user': this_user,
        'user_page_obj': user_page_obj,
        'company_page_obj': company_page_obj,
        'staff_list': staff_list,
    }
    return render(request, 'accounts/user_accounts.html', context)