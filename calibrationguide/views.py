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
from django.forms import modelformset_factory, inlineformset_factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
# Create your views here.
from .forms import (
                    InstructionImageForm, 
                    CalibrationInstructionForm,
                    CalibrationInstructionUpdateForm,
                    ManualImageForm,
                    TechnicalManualForm,
                    TechnicalManualUpdateForm
                )
from .models import (
                    InstructionImage, 
                    CalibrationInstruction,
                    ManualImage,
                    TechnicalManual
                )
from calibrationsites.models import CalibrationSite

def guide_view(request):
    # inst_objs = CalibrationInstruction.objects.all()
    # img_objs = InstructionImage.objects.all()
    # context = {
    #     'inst_objs' : inst_objs,
    #     'img_objs' : img_objs,
    # }
    return render(request, 'calibrationguide/calibrationguide_view.html', context={})

def manual_view(request):
    # inst_objs = TechnicalManual.objects.all()
    # img_objs = ManualImage.objects.all()
    # context = {
    #     'inst_objs' : inst_objs,
    #     'img_objs' : img_objs,
    # }
    return render(request, 'calibrationguide/calibrationmanual_view.html', context={})

@login_required(login_url="/accounts/login") 
def guide_create(request):
    ImageFormSet = modelformset_factory(InstructionImage, fields=('photos',), extra=1, can_delete=True)

    if request.method == "POST":
        inst_form = CalibrationInstructionForm(request.POST, request.FILES)
        formset = ImageFormSet(request.POST, request.FILES)

        if inst_form.is_valid() and formset.is_valid():
            inst_obj = inst_form.save(commit=False)
            inst_obj.author = request.user
            inst_obj.save()

            for form in formset.cleaned_data:
                if form:
                    image = form['photos']
                    InstructionImage.objects.create(photos=image, instruction=inst_obj)
            messages.success(request, "New recorded added")
            return redirect('calibrationguide:guide_view')

    else:
        inst_form = CalibrationInstructionForm()
        formset = formset = ImageFormSet(queryset=InstructionImage.objects.none())

    context = {
        'inst_form': inst_form,
        'formset': formset,
    }

    return render(request, 'calibrationguide/calibrationguide_create_form.html', context)


@login_required(login_url="/accounts/login") 
def guide_update(request, id):
    inst_obj = get_object_or_404(CalibrationInstruction, id=id)
    # queryset = InstructionImage.objects.filter(instruction=inst_obj)
    ImageFormSet = inlineformset_factory(CalibrationInstruction, 
                                        InstructionImage, 
                                        form=InstructionImageForm, 
                                        # fields=('photos',), 
                                        extra=0, 
                                        can_delete=True)

    if request.method == "POST":
        inst_form = CalibrationInstructionForm(request.POST, request.FILES, instance = inst_obj)
        formset = ImageFormSet(request.POST, request.FILES, instance=inst_obj)

        if inst_form.is_valid() and formset.is_valid():
            inst_form.save()
            for form in formset:             
                form.save()
            return redirect('calibrationguide:guide_view')
        # else:
        #     print(formset.errors)
        #     print("Cannot save formset")
    else:
        inst_form = CalibrationInstructionForm(instance=inst_obj)
        formset = formset = ImageFormSet(instance = inst_obj)
    context = {
        'inst_form': inst_form,
        'formset': formset,
    }
    return render(request, 'calibrationguide/calibrationguide_update_form.html', context) 

def guide_downloads(request):
    inst_objs = CalibrationInstruction.objects.all()
    img_objs = InstructionImage.objects.all()

    site_objs = CalibrationSite.objects.all()
    
    obj_baselines = CalibrationSite.objects.filter(site_type='baseline').values('site_name')
    baselines = [('None', '--- Select one ---'),]
    for obj in obj_baselines:
        baselines.append((obj['site_name'], obj['site_name'],))
    obj_ranges = CalibrationSite.objects.filter(site_type='staff_range').values('site_name')
    staff_ranges = [('None', '--- Select one ---'),]
    for obj in obj_ranges:
        staff_ranges.append((obj['site_name'], obj['site_name'],))

    context = {
        'inst_objs' : inst_objs,
        'img_objs' : img_objs,
        'site_objs' : site_objs,
        'baselines' : baselines,
        'staff_ranges' : staff_ranges,
    }
    return render(request, 'calibrationguide/calibrationguide_downloads.html', context)

# def get_states_json(request, *args, **kwargs):
#     selected_country = request.GET.get('country')
#     obj_states = list(State.objects.filter(country__id = selected_country).values())
#     return JsonResponse({'data': obj_states})
@login_required(login_url="/accounts/login") 
def manual_create(request):
    ImageFormSet = modelformset_factory(ManualImage, fields=('photos',), extra=1, can_delete=True)

    if request.method == "POST":
        inst_form = TechnicalManualForm(request.POST, request.FILES)
        formset = ImageFormSet(request.POST, request.FILES)

        if inst_form.is_valid() and formset.is_valid():
            inst_obj = inst_form.save(commit=False)
            inst_obj.author = request.user
            inst_obj.save()

            for form in formset.cleaned_data:
                if form:
                    image = form['photos']
                    ManualImage.objects.create(photos=image, manual=inst_obj)
            messages.success(request, "New recorded added")
            return redirect('calibrationguide:manual_view')

    else:
        inst_form = TechnicalManualForm()
        formset = formset = ImageFormSet(queryset=ManualImage.objects.none())

    context = {
        'inst_form': inst_form,
        'formset': formset,
    }

    return render(request, 'calibrationguide/calibrationguide_create_form.html', context)

@login_required(login_url="/accounts/login") 
def manual_update(request, id):
    inst_obj = get_object_or_404(TechnicalManual, id=id)
    # queryset = InstructionImage.objects.filter(instruction=inst_obj)
    ImageFormSet = inlineformset_factory(TechnicalManual, 
                                        ManualImage, 
                                        form=ManualImageForm, 
                                        # fields=('photos',), 
                                        extra=0, 
                                        can_delete=True)

    if request.method == "POST":
        inst_form = TechnicalManualForm(request.POST, request.FILES, instance = inst_obj)
        formset = ImageFormSet(request.POST, request.FILES, instance=inst_obj)

        if inst_form.is_valid() and formset.is_valid():
            inst_form.save()
            for form in formset:             
                form.save()
            return redirect('calibrationguide:manual_view')
        # else:
        #     print(formset.errors)
        #     print("Cannot save formset")
    else:
        inst_form = TechnicalManualForm(instance=inst_obj)
        formset = formset = ImageFormSet(instance = inst_obj)
    context = {
        'inst_form': inst_form,
        'formset': formset,
    }
    return render(request, 'calibrationguide/calibrationguide_update_form.html', context) 
