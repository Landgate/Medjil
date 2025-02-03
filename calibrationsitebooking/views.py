from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, date
from .models import CalibrationSiteBooking
from .forms import CalibrationSiteBookingForm
from accounts.models import Location
from calibrationsites.models import CalibrationSite

from common_func.validators import try_delete_protected
# Create your views here.


def booking_view(request):

    booking_list = CalibrationSiteBooking.objects.filter(observer = request.user)
        
    context = {
        'booking_list': booking_list}
    
    return render(request, 'calibrationsitebooking/site_booking_list.html', context=context)
    # return HttpResponse('This is the booking dashboard')

def site_booking(request, id=None):
    context = {}
    if id == 'None':
        form = CalibrationSiteBookingForm(request.POST or None,
                                          user=request.user)
        context['Header'] = 'Input Booking Details'
    else:
        obj = get_object_or_404(CalibrationSiteBooking, id=id)
        obj.calibration_date = obj.calibration_date.isoformat()
        form = CalibrationSiteBookingForm(request.POST or None,
                                          instance=obj,
                                          user=request.user)
        context['Header'] = 'Edit Booking Details'
    
    if request.method == 'POST':
        if form.is_valid():
            form.save()  
            # Save the pk if this has been called during calibration with add_btn.
            request.session['new_instance'] = form.instance.id
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('calibrationsitebooking:booking-view')
        
    context['form'] = form
    
    return render(request, 'calibrationsitebooking/site_booking_form.html', context)

@login_required(login_url="/accounts/login") 
def site_booking_delete(request, id):
    # Only allow delete if record belongs to company
    delete_obj = CalibrationSiteBooking.objects.get(
        id=id,
        observer = request.user)

    try_delete_protected(request, delete_obj)
    
    return redirect('calibrationsitebooking:booking-view')



# def site_booking(request):
#     if request.method=="POST":
#             form = CalibrationSiteBookingForm(request.POST, user=request.user)
#             print(form)
#             if form.is_valid():
#                 new_obj = form.save(commit=False)
#                 new_obj.save()
#                 if 'next' in request.POST:
#                     return redirect(request.POST.get('next'))
#                 else:
#                     messages.success(request, 'Your booking is confirmed!.')
#                     return redirect('calibrationguide:guide_view')
#     else:
#         form = CalibrationSiteBookingForm(user=request.user)
#     return render(request, 'calibrationsitebooking/site_booking_form.html', {'form':form})

def get_calib_sites(request, calibration_type, location):
    location = Location.objects.get(id = location)

    site_type  = None
    if calibration_type in ['baseline', 'edmi']:
         site_type = 'baseline'
    elif calibration_type in ['staff', 'range']:
         site_type = 'staff_range'
    site_obj = list(CalibrationSite.objects.filter(site_type=site_type, state__statecode = location.statecode).values_list('id', 'site_name'))

    return JsonResponse({'site_obj': site_obj})