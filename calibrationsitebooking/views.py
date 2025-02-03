from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, date
from .models import CalibrationSiteBooking
from .forms import CalibrationSiteBookingForm
from accounts.models import Location
from calibrationsites.models import CalibrationSite
# Create your views here.

def booking_view(request):


    print(request.user.locations.values_list('statecode', flat=True))

    # print(timezonenow.date())
    # # Get calibration types from the database
    # calibration_types = CalibrationFieldInstruction._meta.get_field('calibration_type').choices
    # # Get the guide objects
    # guides_obj = CalibrationFieldInstruction.objects.all()
    # # Get distinct site locations from the database
    # location_list = guides_obj.values_list('location', flat=True).distinct()  
    # calib_locations = Location.objects.filter(id__in=location_list)
    # context = {
    #     'calibration_types': calibration_types, 
    #     'guides_obj': guides_obj,
    #     'calib_locations': calib_locations,
    # }
    # return render(request, 'calibrationguide/calibrationguide_view.html', context=context)
    return HttpResponse('This is the booking dashboard')

def site_booking(request):
    if request.method=="POST":
            form = CalibrationSiteBookingForm(request.POST, user=request.user)
            print(form)
            if form.is_valid():
                new_obj = form.save(commit=False)
                new_obj.save()
                if 'next' in request.POST:
                    return redirect(request.POST.get('next'))
                else:
                    messages.success(request, 'Your booking is confirmed!.')
                    return redirect('calibrationguide:guide_view')
    else:
        form = CalibrationSiteBookingForm(user=request.user)
    return render(request, 'calibrationsitebooking/site_booking_form.html', {'form':form})

def get_calib_sites(request, calibration_type, location):
    location = Location.objects.get(id = location)

    site_type  = None
    if calibration_type in ['baseline', 'edmi']:
         site_type = 'baseline'
    elif calibration_type in ['staff', 'range']:
         site_type = 'staff_range'
    site_obj = list(CalibrationSite.objects.filter(site_type=site_type, state__statecode = location.statecode).values_list('id', 'site_name'))

    return JsonResponse({'site_obj': site_obj})