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
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.decorators import login_required
# Create your views here.
from .models import (
    CalibrationFieldInstruction, 
    MedjilUserGuide, 
    MedjilGuideToSiteCalibration
)
from accounts.models import Location
from .forms import (CalibrationFieldInstructionForm,
                    MedjilUserGuideForm,
                    MedjilGuideToSiteCalibrationForm,
)


@xframe_options_exempt
def guide_view(request):
    # Get calibration types from the database
    calibration_types = CalibrationFieldInstruction._meta.get_field('calibration_type').choices
    # Get the guide objects
    guides_obj = CalibrationFieldInstruction.objects.all()
    # Get distinct site locations from the database
    location_list = guides_obj.values_list('location', flat=True).distinct()  
    calib_locations = Location.objects.filter(id__in=location_list)
    
    medjil_guide = MedjilUserGuide.objects.first()
    print(medjil_guide)
    medjil_baseline = MedjilGuideToSiteCalibration.objects.filter(site_type='baseline').first()
    medjil_staff = MedjilGuideToSiteCalibration.objects.filter(site_type='range').first()
    
    context = {
        'calibration_types': calibration_types, 
        'guides_obj': guides_obj,
        'medjil_guide': medjil_guide,
        'medjil_baseline': medjil_baseline,
        'medjil_staff': medjil_staff,
        'calib_locations': calib_locations,
    }
    return render(request, 'calibrationguide/calibrationguide_view.html', context=context)

def get_content_url(request, location, calibration_type):
    location = Location.objects.get(name=location)
    guide_obj = CalibrationFieldInstruction.objects.filter(location = location.id, calibration_type=calibration_type).first()
    if guide_obj:
        content_url = guide_obj.content_url
    else:
        content_url = None
    return JsonResponse({'content_url': content_url})


@login_required(login_url="/accounts/login") 
def guide_create(request):
    if request.method=="POST":
        form = CalibrationFieldInstructionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_obj = form.save(commit=False)

            new_obj.save()
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('calibrationguide:guide_view')
    else:
        form = CalibrationFieldInstructionForm(user=request.user)
    return render(request, 'calibrationguide/guide_create_form.html', {'form':form})


@login_required(login_url="/accounts/login") 
def medjil_guide_create(request):
    if request.method=="POST":
        form = MedjilUserGuideForm(request.POST, request.FILES, user=request.user)
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
        form = MedjilUserGuideForm(user=request.user)
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

def guide_view1(request):
    # Display the manual as html page
    return render(request, 'calibrationguide/calibrationguide_view_old.html', context={})

def manual_view(request):
    # Display the manual as html page
    return render(request, 'calibrationguide/calibrationmanual_view.html', context={})

def read_manual(request, manual_name):
    return render(request, 'calibrationguide/' + manual_name, context={})
