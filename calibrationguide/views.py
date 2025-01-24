'''

   © 2024 Western Australian Land Information Authority

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
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.decorators import login_required
# Create your views here.
from .models import (
    CalibrationGuide, 
    MedjilGuide, 
    MedjilGuideToSiteCalibration
)
from calibrationsites.models import CalibrationSite
from accounts.models import Location
from .forms import (CalibrationGuideForm,
                    MedjilGuideForm,
                    MedjilGuideToSiteCalibrationForm,
)

@xframe_options_exempt
def guide_view(request):
    # Get calibration types from the database
    calibration_types = CalibrationGuide._meta.get_field('calibration_type').choices
    # Get the guide objects
    guides_obj = CalibrationGuide.objects.all()
    # Get distinct site locations from the database
    location_list = guides_obj.values_list('location', flat=True).distinct()  
    calib_locations = Location.objects.filter(id__in=location_list)
    context = {
        'calibration_types': calibration_types, 
        'guides_obj': guides_obj,
        'calib_locations': calib_locations,
    }
    return render(request, 'calibrationguide/calibrationguide_view.html', context=context)

def get_content_url(request, location, calibration_type):
    location = Location.objects.get(name=location)
    guide_obj = CalibrationGuide.objects.filter(location = location.id, calibration_type=calibration_type).first()
    if guide_obj:
        content_url = guide_obj.content_url
    else:
        content_url = None
    return JsonResponse({'content_url': content_url})

@login_required(login_url="/accounts/login") 
def guide_create(request):
    if request.method=="POST":
        form = CalibrationGuideForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_obj = form.save(commit=False)

            new_obj.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('calibrationguide:guide_view')
    else:
        form = CalibrationGuideForm(user=request.user)
    return render(request, 'calibrationguide/guide_create_form.html', {'form':form})

@login_required(login_url="/accounts/login") 
def medjil_guide_create(request):
    if request.method=="POST":
        form = MedjilGuideForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_obj = form.save(commit=False)

            new_obj.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('calibrationguide:guide_view')
        else:
            print(form.errors)
    else:
        form = MedjilGuideForm(user=request.user)
    return render(request, 'calibrationguide/guide_create_form.html', {'form':form})

@login_required(login_url="/accounts/login") 
def medjil_guide_to_calib_create(request):
    if request.method=="POST":
        form = MedjilGuideToSiteCalibrationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_obj = form.save(commit=False)

            new_obj.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('calibrationguide:guide_view')
        else:
            print(form.errors)
    else:
        form = MedjilGuideToSiteCalibrationForm(user=request.user)
    return render(request, 'calibrationguide/guide_create_form.html', {'form':form})

def display_medjil_guide(request):
    try:
        obj = MedjilGuide.objects.first()
        if not obj:
            raise Http404("<p>Medjil User Guide currently does not exist.. Please contact <a href='mailto:geodesy@landgate.wa.gov.au'>geodesy@landgate.wa.gov.au</a>.</p>")
        filepath = obj.medjil_book.path        
        return FileResponse(open(filepath, 'rb'), content_type='application/pdf')
    except Http404 as e:
        return HttpResponse(str(e), status=404)
    except Exception as e:
        return HttpResponse("<p>An unexpected error occurred. Please contact <a href='mailto:geodesy@landgate.wa.gov.au'>geodesy@landgate.wa.gov.au</a>.</p>", status=500)

def display_medjil_calib_baseline(request):
    try:
        obj = MedjilGuideToSiteCalibration.objects.filter(site_type='baseline').first()
        print(obj)
        if not obj:
            raise Http404("<p>Medjil Guide to EDM Baseline Calibration currently does not exist. Please contact <a href='mailto:geodesy@landgate.wa.gov.au'>geodesy@landgate.wa.gov.au</a>.</p>")
        filepath = obj.content_book.path        
        return FileResponse(open(filepath, 'rb'), content_type='application/pdf')
    except Http404 as e:
        return HttpResponse(str(e), status=404)
    except Exception as e:
        return HttpResponse("<p>An unexpected error occurred. Please contact <a href='mailto:geodesy@landgate.wa.gov.au'>geodesy@landgate.wa.gov.au</a>.</p>", status=500)
        
def display_medjil_calib_staff(request):
    try:
        obj = MedjilGuideToSiteCalibration.objects.filter(site_type='range').first()
        print(obj)
        if not obj:
            raise Http404("<p>Medjil Guide to Staff Range Calibration currently does not exist. Please contact <a href='mailto:geodesy@landgate.wa.gov.au'>geodesy@landgate.wa.gov.au</a>.</p>")
        filepath = obj.content_book.path        
        return FileResponse(open(filepath, 'rb'), content_type='application/pdf')
    except Http404 as e:
        return HttpResponse(str(e), status=404)
    except Exception as e:
        return HttpResponse("<p>An unexpected error occurred. Please contact <a href='mailto:geodesy@landgate.wa.gov.au'>geodesy@landgate.wa.gov.au</a>.</p>", status=500)

def guide_view1(request):
    # Display the manual as html page
    return render(request, 'calibrationguide/calibrationguide_view_old.html', context={})

def manual_view(request):
    # Display the manual as html page
    return render(request, 'calibrationguide/calibrationmanual_view.html', context={})

def read_manual(request, manual_name):
    return render(request, 'calibrationguide/' + manual_name, context={})
