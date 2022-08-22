import os
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views import generic
from formtools.wizard.views import SessionWizardView, NamedUrlSessionWizardView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db import IntegrityError
from django.core.paginator import Paginator
# from django.forms import formset_factory
from django.forms.models import model_to_dict
from .forms import (InstrumentMakeCreateForm, 
                    InstrumentModelCreateForm,
                    InstrumentModelCreateByInstTypeForm,
                    StaffCreateForm, 
                    DigitalLevelCreateForm,
                    EDM_InstForm,
                    EDM_SpecificationForm,
                    Prism_InstForm,
                    Prism_SpecificationForm,
                    Mets_InstForm,
                    Mets_SpecificationForm
                    )

from .models import (InstrumentMake, 
                    InstrumentModel, 
                    Staff, 
                    DigitalLevel,
                    EDM_Inst,
                    EDM_Specification,
                    Prism_Inst,
                    Mets_Inst)

from staffcalibration.models import StaffCalibrationRecord
# Create your views here.

# Create lists - for Home Page
instrument_types = [
        {'abbr': 'edm', 'name': 'Electronic Distance Measurement (EDM)'},
        {'abbr': 'prism', 'name': 'Prism'}, 
        {'abbr': 'level', 'name': 'Digital Level'}, 
        {'abbr': 'staff', 'name': 'Barcoded Staff'},
        {'abbr': 'met', 'name': 'Meteorological Station'}
    ]
@login_required(login_url="/accounts/login") 
def instruments_home(request):
    inst_types = instrument_types
    # EDM List
    edm_list = EDM_Inst.objects.filter(edm_specs__edm_owner=request.user.company)
    # Page Setting
    edm_page = Paginator(edm_list, 25) # Show 10 list per page.
    edm_page_number = request.GET.get('page')
    edm_page_obj = edm_page.get_page(edm_page_number)

    # Prism List
    prism_list = Prism_Inst.objects.filter(prism_specs__prism_owner=request.user.company)
    # Page Setting
    prism_page = Paginator(prism_list, 25) # Show 10 list per page.
    prism_page_number = request.GET.get('page')
    prism_page_obj = prism_page.get_page(prism_page_number)

    # Staff List
    staff_list = Staff.objects.filter(staff_owner = request.user.company)
    # Page Setting
    staff_page = Paginator(staff_list, 25) # Show 10 list per page.
    staff_page_number = request.GET.get('page')
    staff_page_obj = staff_page.get_page(staff_page_number)

    # Level List
    level_list = DigitalLevel.objects.filter(level_owner = request.user.company)
    # Page Setting
    level_page = Paginator(level_list, 25) # Show 10 list per page.
    level_page_number = request.GET.get('page')
    level_page_obj = level_page.get_page(level_page_number)

    # Mets List
    mets_list = Mets_Inst.objects.filter(mets_specs__mets_owner = request.user.company)
    # Page Setting
    mets_page = Paginator(mets_list, 25) # Show 10 list per page.
    mets_page_number = request.GET.get('page')
    mets_page_obj = mets_page.get_page(mets_page_number)

    context = {
        'inst_types': inst_types, 
        'edm_page_obj': edm_page_obj,
        'prism_page_obj': prism_page_obj,
        'staff_page_obj': staff_page_obj,
        'level_page_obj': level_page_obj,
        'mets_page_obj': mets_page_obj
    }
    return render(request, 'instruments/instruments_list.html', context)
    
@login_required(login_url="/accounts/login") 
def instruments_levelling(request):
    model_list = InstrumentModel.objects.filter(Q(inst_type='staff') | Q(inst_type='level')).order_by('-inst_type')

    staff_list = Staff.objects.filter(staff_owner = request.user.company)

    level_list = DigitalLevel.objects.filter(level_owner = request.user.company)

    print(staff_list)
    context = {
        'model_list': model_list,
        'staff_list': staff_list,
        'level_list': level_list
    }
    return render(request, 'instruments/instruments_home.html', context)
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_make_create(request):
    if request.method=="POST":
        form = InstrumentMakeForm(request.POST)
        if form.is_valid():
            form.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect ('instruments:home')
    else:
        form = InstrumentMakeForm()
    return render(request, 'instruments/inst_make_create_form.html', {'form': form})
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_make_update(request, id):
    this_make = get_object_or_404(InstrumentMake, id = id)
    form = InstrumentMakeOnlyForm(request.POST or None, instance = this_make)
    if form.is_valid():
        form.save()
        return redirect ('accounts:user-account')
    context = {
        'form': form
        }
    return render(request, 'instruments/inst_make_create_form.html', context)    
#####################################################################################
###################################### USED #########################################
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_model_createby_inst_type(request, inst_type):
    if request.method=="POST":
        form = InstrumentModelCreateByInstTypeForm(request.POST, user=request.user, inst_type = inst_type)
        if form.is_valid():
            inst_type = form.cleaned_data['inst_type']
            inst_make = form.cleaned_data['make']
            inst_model = form.cleaned_data['model']
            # if Make == "others", create a new instrument make
            if inst_make.make=='OTHERS':
                new_make = form.cleaned_data['inst_make']
                new_abbrev = form.cleaned_data['inst_abbrev']

                inst_make, created = InstrumentMake.objects.get_or_create(
                    make = new_make,
                    make_abbrev = new_abbrev
                )
            
            instance, created = InstrumentModel.objects.get_or_create(
                        inst_type = inst_type,
                        make = inst_make,
                        model = inst_model,
            )
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s", "#id_author");</script>' % (instance.pk, instance))
                # return redirect ('instruments:home')
    else:
        form = InstrumentModelCreateByInstTypeForm(user=request.user, inst_type = inst_type)
    return render(request, 'instruments/inst_model_create_popup_form.html', {'form': form})
#####################################################################################
#################################### UNUSED #########################################
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_model_create(request):
   if request.method=="POST":
    #    form = InstrumentModelCreateForm(request.POST)
       form = InstrumentModelCreateForm(request.POST, user=request.user)
       if form.is_valid():
           instance = form.save()
           if 'next' in request.POST:
               return redirect(request.POST.get('next'))
           else:
            #    return HttpResponse('<script type="text/javascript">window.close(); window.parent.location.href = "/";</script>')
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (instance.pk, instance))
   else:
    #    form = InstrumentModelCreateForm()
       form = InstrumentModelCreateForm(user=request.user)
   return render(request, 'instruments/inst_model_create_popup_form.html', {'form':form})
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_model_update(request, id):
    this_model = get_object_or_404(InstrumentModel, id = id)
    form = InstrumentMakeOnlyForm(request.POST or None, instance = this_model)
    if form.is_valid():
        form.save()
        return redirect ('accounts:user-account')
    else:
        form = InstrumentMakeOnlyForm(instance = this_model)
    context = {
        'form': form
        }
    return render(request, 'instruments/inst_model_create_form.html', context)
#####################################################################################
@login_required(login_url="/accounts/login")    
def inst_level_detail(request, id):
    this_inst = get_object_or_404(DigitalLevel, id = id)

    context = {
        'this_inst': this_inst,
        }
    return render(request, 'instruments/inst_level_detail.html', context)
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_level_create_popup(request):
    if request.method=="POST":
        form = DigitalLevelCreateForm(request.POST, user= request.user)
        if form.is_valid():
            this_inst = form.save(commit=False)
            if request.user.company: 
                this_inst.staff_owner = request.user.company
            this_inst.save()
            
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (this_inst.pk, this_inst))
                # return redirect('accounts:user-account')
    else:
        form = DigitalLevelCreateForm(user= request.user)
    return render(request, 'instruments/inst_level_create_popup_form.html', {'form':form})
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_level_update(request, id):
    this_inst = get_object_or_404(DigitalLevel, id = id)
    form = DigitalLevelCreateForm(request.POST or None, instance = this_inst, user = request.user)
    if form.is_valid():
        form.save()
        return redirect ('instruments:home')
    context = {
        'form': form
        }
    return render(request, 'instruments/inst_update_form.html', context)
#####################################################################################
class DigitalLevelCreateView(LoginRequiredMixin, generic.CreateView):
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(DigitalLevelCreateView, self).get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        context = {'form': DigitalLevelCreateForm(user=self.request.user)}
        return render(request, 'instruments/inst_level_create_form.html', context)

    def post(self, request, *args, **kwargs):
        form = DigitalLevelCreateForm(request.POST, user=self.request.user)
        if form.is_valid():
            level = form.save()
            level.save()
            return redirect(reverse("instruments:home"))
            #return HttpResponseRedirect(reverse_lazy('books:detail', args=[book.id]))
        return render(request, 'instruments/inst_level_create_form.html', {'form': form})
#################################################################################
@login_required(login_url="/accounts/login")    
def inst_staff_detail(request, id):
    this_inst = get_object_or_404(Staff, id = id)
    this_inst = model_to_dict(this_inst)
    context = {
        'this_inst': this_inst
        }
    return render(request, 'instruments/inst_staff_detail.html', context)
#####################################################################################
@login_required(login_url="/accounts/login") 
def inst_staff_update(request, id):
    this_inst = get_object_or_404(Staff, id = id)
    form = StaffCreateForm(request.POST or None, instance = this_inst, user = request.user)
    if form.is_valid():
        form.save()
        return redirect ('instruments:home')
    context = {
        'form': form
        }
    return render(request, 'instruments/inst_update_form.html', context)
#######################################################################
######################## STAFF CREATE #################################
#######################################################################
# Create your views here.
def show_calibrated_form_condition(wizard):
    # try to get the cleaned data of step 1
    cleaned_data = wizard.get_cleaned_data_for_step('inst_staff_form') or {}
    # check if the field ``leave_message`` was checked.
    return cleaned_data.get('calibrated', True)

STAFF_TEMPLATES  = {
                    "inst_staff_form": "instruments/inst_staff_create_form.html",
                    "inst_staff_record_form": "staffcalibration/staff_calibration_record_form.html",
                    }
class StaffCreationWizard(LoginRequiredMixin, NamedUrlSessionWizardView):
    # get the template names and their steps
    def get_template_names(self):				
        return [STAFF_TEMPLATES[self.steps.current]]

    # directory to store the ascii files
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'media')) #
    # get the user
    def get_form_kwargs(self, step=1):
        kwargs = super(StaffCreationWizard, self).get_form_kwargs(step)
        kwargs['user'] = self.request.user
        # if step == 'inst_model_form':
        #     kwargs['inst_type'] = 'staff'
        return kwargs

    def done(self, form_list, **kwargs):
        data = {k: v for form in form_list for k, v in form.cleaned_data.items()}
        inst_number = data['staff_number']
        inst_owner = data['staff_owner']
        inst_model = data['staff_model']
        # inst_make = data['make']
        # print(data)
        # Other parameters
        staff_type = data['staff_type']
        staff_length = data['staff_length']
        thermal_coefficient = data['thermal_coefficient']
        # Is it calibrated?
        calibrated = data['calibrated']

        # Create Staff
        if not calibrated:
            inst_staff = Staff.objects.create(
                    staff_owner = inst_owner,
                    staff_number = inst_number,
                    staff_model = inst_model,
                    staff_type = staff_type,
                    staff_length = staff_length,
                    thermal_coefficient = thermal_coefficient,
                    )
        else:
            site_id = data['site_id']
            job_number = data['job_number']
            inst_level = data['inst_level']
            scale_factor = data['scale_factor']
            grad_uncertainty = data['grad_uncertainty']
            standard_temperature = data['standard_temperature']
            observed_temperature = data['observed_temperature']
            calibration_date = data['calibration_date']
            calibration_report = data['calibration_report']
            
            # enter staff details
            inst_staff = Staff.objects.create(
                    staff_owner = inst_owner,
                    staff_number = inst_number,
                    staff_model = inst_model,
                    staff_type = staff_type,
                    staff_length = staff_length,
                    thermal_coefficient = thermal_coefficient,
                    )
            instrument_calib = StaffCalibrationRecord.objects.create(
                site_id = site_id,
                job_number = job_number,
                inst_staff = inst_staff,
                inst_level = inst_level,
                scale_factor = scale_factor,
                grad_uncertainty = grad_uncertainty,
                standard_temperature = standard_temperature,
                observed_temperature = observed_temperature,
                calibration_date = calibration_date,
                calibration_report = calibration_report,
            )
        return redirect('instruments:home')

#######################################################################
########################## EDM CREATE #################################
#######################################################################
class EDMCreateView(LoginRequiredMixin, generic.CreateView):
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(EDMCreateView, self).get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        context = {'form': EDM_InstForm(user=self.request.user)}
        return render(request, 'instruments/inst_edm_create_form.html', context)

    def post(self, request, *args, **kwargs):
        form = EDM_InstForm(request.POST, user=self.request.user)
        if form.is_valid():
            instance = form.save()
            instance.save()
            return redirect(reverse("instruments:home"))
            #return HttpResponseRedirect(reverse_lazy('books:detail', args=[book.id]))
        return render(request, 'instruments/inst_edm_create_form.html', {'form': form})
#########################################################################
@login_required(login_url="/accounts/login")    
def inst_edm_detail(request, id):
    this_inst = get_object_or_404(EDM_Inst, id = id)

    context = {
        'this_inst': this_inst,
        }
    return render(request, 'instruments/inst_edm_detail.html', context)
#########################################################################
@login_required(login_url="/accounts/login") 
def inst_edm_spec_create(request):
    if request.method=="POST":
        form = EDM_SpecificationForm(request.POST, user= request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            if request.user.company:
                instance.edm_owner = request.user.company
            instance.save()
            
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (instance.pk, instance))
                # return redirect('accounts:user-account')
    else:
        form = EDM_SpecificationForm(user= request.user)
    return render(request, 'instruments/inst_spec_edm_create_popup_form.html', {'form':form})
#######################################################################
########################## EDM CREATE #################################
#######################################################################
class PrismCreateView(LoginRequiredMixin, generic.CreateView):
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(PrismCreateView, self).get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        context = {'form': Prism_InstForm(user=self.request.user)}
        return render(request, 'instruments/inst_prism_create_form.html', context)

    def post(self, request, *args, **kwargs):
        form = Prism_InstForm(request.POST, user=self.request.user)
        if form.is_valid():
            instance = form.save()
            instance.save()
            return redirect(reverse("instruments:home"))
            #return HttpResponseRedirect(reverse_lazy('books:detail', args=[book.id]))
        return render(request, 'instruments/inst_prism_create_form.html', {'form': form})
#########################################################################
@login_required(login_url="/accounts/login") 
def inst_prism_spec_create(request):
    if request.method=="POST":
        form = Prism_SpecificationForm(request.POST, user= request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            if request.user.company:
                instance.edm_owner = request.user.company
            instance.save()
            
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (instance.pk, instance))
                # return redirect('accounts:user-account')
    else:
        form = Prism_SpecificationForm(user= request.user)
    return render(request, 'instruments/inst_spec_prism_create_popup_form.html', {'form':form})
#######################################################################
########################## METS CREATE ################################
#######################################################################
class MetsCreateView(LoginRequiredMixin, generic.CreateView):
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(MetsCreateView, self).get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        context = {'form': Mets_InstForm(user=self.request.user)}
        return render(request, 'instruments/inst_mets_create_form.html', context)

    def post(self, request, *args, **kwargs):
        form = Mets_InstForm(request.POST, user=self.request.user)
        if form.is_valid():
            instance = form.save()
            instance.save()
            return redirect(reverse("instruments:home"))
            #return HttpResponseRedirect(reverse_lazy('books:detail', args=[book.id]))
        return render(request, 'instruments/inst_mets_create_form.html', {'form': form})
#########################################################################
@login_required(login_url="/accounts/login") 
def inst_mets_spec_create(request):
    if request.method=="POST":
        form = Mets_SpecificationForm(request.POST, user= request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            if request.user.company:
                instance.mets_owner = request.user.company
            instance.save()
            
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (instance.pk, instance))
                # return redirect('accounts:user-account')
    else:
        form = Mets_SpecificationForm(user= request.user)
    return render(request, 'instruments/inst_spec_met_create_popup_form.html', {'form':form})
#########################################################################
