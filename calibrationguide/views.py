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
# Create your views here.
from calibrationsites.models import CalibrationSite

def guide_view(request):
    # Display the manual as html page
    return render(request, 'calibrationguide/calibrationguide_view.html', context={})

def manual_view(request):
    # Display the manual as html page
    return render(request, 'calibrationguide/calibrationmanual_view.html', context={})

def read_manual(request, manual_name):
    return render(request, 'calibrationguide/' + manual_name, context={})
