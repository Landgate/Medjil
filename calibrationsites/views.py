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
import os
import numpy as np
from django.http import HttpResponse, JsonResponse
from django.forms import modelformset_factory, formset_factory
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from formtools.wizard.views import NamedUrlSessionWizardView
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import Q

# Forms
from .forms import (CountryForm, 
                    StateForm, 
                    LocalityForm,
                    CalibrationSiteUpdateForm,
                    PillarForm, 
                    AddPillarForm, 
                    CustomBaseModelFormSet)
# Models
from .models import (State, 
                    Locality,
                    CalibrationSite, 
                    Pillar)

from baseline_calibration.models import Certified_Distance

###########################################################################
# Create your views here.
@login_required(login_url="/accounts/login") 
def site_home(request):
    locations = list(request.user.locations.values_list('statecode', flat=True))
    calibration_sites = CalibrationSite.objects.filter(
        Q(state__statecode__in = locations)).order_by(
            'state__statecode', 'site_name')
    
    staff_ranges = calibration_sites.filter(site_type = 'staff_range')
    baselines = calibration_sites.filter(site_type = 'baseline')
    
    filter_states = CalibrationSite.objects.filter(country__name__exact = 'Australia').order_by('state').values('state').distinct()
    state_list = [('None', '--- Select one ---'),]
    for state_id in filter_states:
        state = State.objects.filter(id = state_id['state']).values('statecode')[0]
        state_list.append((state_id['state'], state['statecode'],))
    context = {
        'baselines': baselines,
        'staff_ranges': staff_ranges,
        'state_list': state_list,
        
    }
    # print(request.user.company.company_name)
    # print(staff_ranges.operator)
    return render(request, 'calibrationsites/calibrationsite_home.html', context)
###########################################################################
# Detailed view
@login_required(login_url="/accounts/login") 
def site_detailed_view(request, id):
    site = get_object_or_404(CalibrationSite, id = id)
    pillars = Pillar.objects.filter(site_id=site).order_by('order')
    
    return render(request, 
                    'calibrationsites/site_detail.html', 
                    context = {'site': site,
                                'pillars': pillars})
###########################################################################


EditPillarFormSet = modelformset_factory(
    Pillar, form=PillarForm,
    extra=0,
    can_delete=False
)
@login_required(login_url="/accounts/login") 
def site_update(request, id):
    site = get_object_or_404(CalibrationSite, id = id)
    original_reference_height = round(float(site.reference_height), 3) if site.reference_height else 0.000
    
    form = CalibrationSiteUpdateForm(
        request.POST or None, request.FILES or None,
        instance = site, request=request)
    formset = EditPillarFormSet(
        request.POST or None, 
        queryset=Pillar.objects.filter(site_id=site))
    
    if form.is_valid() and formset.is_valid():
        # Check if reference height changed and there are Certified Distance records
        if 'reference_height' in  form.cleaned_data:
            new_reference_height = round(float(form.cleaned_data["reference_height"]), 3) if form.cleaned_data["reference_height"] else 0.000
            if new_reference_height != original_reference_height:
                has_certified_distances = Certified_Distance.objects.filter(pillar_survey__baseline=site).exists()
                if has_certified_distances:
                    messages.warning(request, 
                        "Warning: The Reference Height has changed for a site with existing Certified Distance records. "
                        "Future certified distances will be detemined at this height and are not directly comparable to historical distances. "
                        "Historical distances will need to be recalculated for historical comparisons.")

        form.save()
        formset.save()
        return redirect('calibrationsites:home')

    context = {
        'form': form, 
        'formset': formset}
    return render(
        request, 'calibrationsites/calibrationsite_update_form.html', context)


#########################################################################
def missing_elements(L):
    start, end = L[0], L[-1]
    return set(range(start, end + 1)).difference(L)

def pillar_create(request, id):
    site_id = get_object_or_404(CalibrationSite, id=id)
    
    no_of_pillars = Pillar.objects.filter(site_id = site_id.id).count()
    required_num_of_pillars = int(site_id.no_of_pillars-no_of_pillars)
    # Existing Pins
    existPillarNumbers = []
    existingPillarInfo = {}
    if Pillar.objects.all().exists():
        pillar_numbers = Pillar.objects.filter(site_id = site_id.id).values('name')
        for pillar in pillar_numbers:
            existPillarNumbers.append(int(pillar['name']))

        existPillarNumbers = np.sort(np.array(existPillarNumbers))
        missingPillars = missing_elements(existPillarNumbers)
        next_sq_number = existPillarNumbers[-1]+1

        existingPillarInfo = {'number_of_existing_pillars' : no_of_pillars,
                            'required_num_of_pillars': required_num_of_pillars,
                            'missingPillars' : missingPillars,
                            'next_sq_number': next_sq_number}

    if (no_of_pillars < site_id.no_of_pillars):
        AddPillarFormSet = formset_factory(AddPillarForm, 
                                           formset= CustomBaseModelFormSet,
                                           extra=2, 
                                           max_num= required_num_of_pillars)

        if request.method == 'POST':
            formset = AddPillarFormSet(request.POST)
            
            if formset.is_valid():
                if len(formset) == required_num_of_pillars:
                    for form in formset:
                        data = form.cleaned_data
                        Pillar.objects.create(site_id = data['site_id'],
                                                    name = data['name'])
                    return render(request, 'accounts:user-account')
                else:
                    messages.error(request, "Please add "+ str(required_num_of_pillars- len(formset)) + " more pillars(s). Required: "+ str(required_num_of_pillars) + " (out of "+ str(int(site_id.no_of_pillars)) + ")")
        else:
            formset = AddPillarFormSet()
        return render(request, 'calibrationsites/add_pillar_form.html', {
                                                                        'site_id': site_id,
                                                                        'existingPillarInfo': existingPillarInfo,
                                                                        'formset': formset})
    else:
        messages.warning(request, "You have all the pins added")
        return redirect('rangecalibration:calibrate')
###########################################################################
@login_required(login_url="/accounts/login") 
def each_pillar_update(request, id, pk):
    instance = Pillar.objects.get(site_id__exact=id, name__exact=pk)
    form = PillarForm(request.POST or None, instance = instance)
    if form.is_valid():
        instance = form.save()
        if 'next' in request.POST:
            return redirect(request.POST.get('next'))
        else:
            return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (instance.pk, instance))
    return render(request, 'calibrationsites/pillar_update_form.html', {'form': form})
###########################################################################
def country_create(request):
    if request.method=="POST":
        form = CountryForm(request.POST)
        if form.is_valid():
            new_country = form.save(commit=False)

            new_country.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (new_country.pk, new_country))
                # return redirect('accounts:user-account')#redirect('blog:post_detail', pk= post.pk)
    else:
        form = CountryForm()
    return render(request, 'calibrationsites/country_form.html', {'form':form})
###########################################################################
def state_create(request):
    if request.method=="POST":
        form = StateForm(request.POST)
        if form.is_valid():
            new_state = form.save(commit=False)

            new_state.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (new_state.pk, new_state))
                # return redirect('accounts:user-account')#redirect('blog:post_detail', pk= post.pk)
    else:
        form = StateForm()
    return render(request, 'calibrationsites/state_form.html', {'form':form})
###########################################################################
def locality_create(request):
    if request.method=="POST":
        form = LocalityForm(request.POST)
        if form.is_valid():
            new_locality = form.save(commit=False)

            new_locality.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (new_locality.pk, new_locality))

                # return redirect('accounts:user-account')#redirect('blog:post_detail', pk= post.pk)
    else:
        form = LocalityForm()
    return render(request, 'calibrationsites/locality_form.html', {'form':form})
###############################################################################
######################### SessionWizardView ###################################
###############################################################################
TEMPLATES  = {"site_form": "calibrationsites/CalibrationSiteForm1.html",
             "pillar_form": "calibrationsites/CalibrationSiteForm2.html",
             }
# Create your views here.
class CreateCalibrationSiteWizard(LoginRequiredMixin, NamedUrlSessionWizardView):
    # get the template names and their steps
    def get_template_names(self):                
        return [TEMPLATES[self.steps.current]]
    
    def perm_check(self):
        if not self.request.user.has_perm("monitorings.manage_perm", self.monitoring):
            raise PermissionDenied()

    # directory to store the ascii files
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'media')) #
    
    # get the user
    def get_form_kwargs(self, step=1):
        kwargs = super(CreateCalibrationSiteWizard, self).get_form_kwargs(step)
        #if step == 'site_form':
        kwargs['user'] = self.request.user
        if step == 'pillar_form':
            data = self.get_cleaned_data_for_step('site_form')
            kwargs['sitetype'] = data['site_type']
            kwargs['sitename'] = data['site_name']

        return kwargs

    def get_form(self, step=None, data=None, files=None):
        form = super(CreateCalibrationSiteWizard, self).get_form(step, data, files)

        if step is None:
            step = self.steps.current
        if step == 'pillar_form':
            data = self.get_cleaned_data_for_step('site_form')
            no_pillars = int(data['no_of_pillars'])
            form.extra = no_pillars
            form.max_num = no_pillars
            form.user = self.request.user
        return form

    def get_context_data(self, form, **kwargs):
        context = super(CreateCalibrationSiteWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.current == 'pillar_form':
            data = self.get_cleaned_data_for_step('site_form'); 
            context.update({
                'sitetype': data['site_type'],
                'sitename': data['site_name'],
                'sitestate': data['state'],
                'no_pillars': data['no_of_pillars']
            })

        return context

    def done(self, form_list, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        site_form_data = form_data[0]
        pillar_form_data = form_data[1]
        
        site_name = site_form_data['site_name']
        site_type = site_form_data['site_type']
        # Create Site
        try:
            site = CalibrationSite.objects.create(
                site_name = site_name,
                site_type = site_type, #site_form_data['site_type'],
                site_address = site_form_data['site_address'],
                site_status = site_form_data['site_status'],
                locality = site_form_data['locality'],
                state = site_form_data['state'],
                country = site_form_data['country'],
                no_of_pillars = site_form_data['no_of_pillars'],
                reference_height = site_form_data['reference_height'],
                operator = site_form_data['operator'],
                site_access_plan = site_form_data['site_access_plan'],
                site_booking_sheet = site_form_data['site_booking_sheet']
            )
        except:
            site = CalibrationSite.objects.get(site_name = site_name)

        if site_type.startswith('staff'):
            for pillars in pillar_form_data:
                new_pillars = Pillar.objects.create(
                    site_id = site,
                    name = pillars['name'],
                )
        elif site_type.startswith('baseline'):
            for ordr, pillars in enumerate(pillar_form_data, start=1):
                new_pillars = Pillar.objects.create(
                    site_id = site,
                    name = pillars['name'],
                    easting = pillars['easting'],
                    northing = pillars['northing'],
                    zone = pillars['zone'],
                    order = f'{ordr:0>3}',
                )


        return redirect('calibrationsites:home')



#########################################################################
####################### JSON ############################################
#########################################################################
# return JsonResponse({'data': obj_states})
def get_site_json(request, *args, **kwargs):
    selected_site = request.GET.get('site')
    try:
        obj_site = CalibrationSite.objects.get(id = selected_site)
        data = {
            'no_of_pins': obj_site.number_of_pins
        }
        return JsonResponse({'data': data})
    except ObjectDoesNotExist:
        return JsonResponse({'data': None})

def get_states_json(request, *args, **kwargs):
    selected_country = request.GET.get('country')
    obj_states = list(State.objects.filter(country__id = selected_country).values())
    return JsonResponse({'data': obj_states})

def get_locality_json(request, *args, **kwargs):
    selected_state = kwargs.get('state')
    obj_locality = list(Locality.objects.filter(state__id = selected_state).values())

    return JsonResponse({'data': obj_locality})
###########################################################################