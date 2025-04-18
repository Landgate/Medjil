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
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views import generic
from formtools.wizard.views import NamedUrlSessionWizardView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from common_func.validators import try_delete_protected
# from django.forms import formset_factory
from .forms import (
    InstrumentModelCreateForm,
    InstrumentModelCreateByInstTypeForm,
    StaffCreateForm, 
    DigitalLevelCreateForm,
    EDM_InstForm,
    EDM_SpecificationForm,
    Prism_InstForm,
    Prism_SpecificationForm,
    Mets_InstForm,
    Mets_SpecificationForm,
    EDMI_certificateForm,
    Mets_certificateForm
    )

from .models import (
    InstrumentMake, 
    InstrumentModel, 
    Staff, 
    DigitalLevel,
    EDM_Inst,
    EDM_Specification,
    Prism_Specification,
    Mets_Specification,
    Prism_Inst,
    Mets_Inst,
    EDMI_certificate,
    Mets_certificate,
    Specifications_Recommendations
    )
from staffcalibration.forms import StaffCalibrationRecordForm
from staffcalibration.models import StaffCalibrationRecord
from common_func.Convert import db_std_units


INST_TYPES = [{'abbr':x[0], 'name':x[1]} 
              for x in InstrumentModel.inst_type.field.choices 
              if x[0] not in [None, 'others']]

# Instrument Settings 
@login_required(login_url="/accounts/login")
def instrument_settings(request):
    inst_makes = InstrumentMake.objects.exclude(make_abbrev = 'OTH').order_by('make_abbrev')
    context = {
        'inst_types': INST_TYPES,
        'inst_makes': inst_makes

    }
    return render(request, 'instruments/inst_global_settings.html', context)


@login_required(login_url="/accounts/login")
def register_edit(request, inst_disp, tab, id):
    
    inst_type=''
    if (inst_disp == 'baro' or inst_disp == 'thermo' 
        or inst_disp == 'hygro' or inst_disp == 'psy'): inst_type='mets'
    
    if tab == 'models':
        if inst_disp == 'edm':
            tmplate = 'instruments/inst_spec_edm_edit_popup_form.html'
            if id == 'None':
                form = EDM_SpecificationForm(
                    request.POST or None, request.FILES or None, user=request.user)
            else:
                obj = get_object_or_404(EDM_Specification, id = id)
                form = EDM_SpecificationForm(
                    request.POST or None, request.FILES or None, 
                    instance = obj, user = request.user)
            
        if inst_disp == 'prism':
            tmplate = 'instruments/inst_spec_prism_edit_popup_form.html'
            if id == 'None':
                form = Prism_SpecificationForm(
                    request.POST or None, request.FILES or None, user=request.user)
            else:
                obj = get_object_or_404(Prism_Specification, id = id)
                form = Prism_SpecificationForm(
                    request.POST or None, request.FILES or None,
                    instance = obj, user = request.user)
                
        if inst_type == 'mets':
            tmplate = 'instruments/inst_spec_met_edit_popup_form.html'
            if id == 'None':
                form = Mets_SpecificationForm(
                    request.POST or None, request.FILES or None, 
                    user=request.user, inst_type = inst_disp)
            else:
                obj = get_object_or_404(Mets_Specification, id = id)
                form = Mets_SpecificationForm(
                    request.POST or None, request.FILES or None, 
                    instance = obj, user = request.user, inst_type = inst_disp)
        
    if tab == 'insts':
        tmplate ='instruments/inst_edit_form.html'
        if inst_disp == 'edm':
            if id == 'None':
                form = EDM_InstForm(request.POST or None, request.FILES or None,
                                    user = request.user)
            else:
                obj = get_object_or_404(EDM_Inst, id = id)
                form = EDM_InstForm(request.POST or None, request.FILES or None,
                                    instance = obj, user = request.user)
        if inst_disp == 'prism':
            if id == 'None':
                form = Prism_InstForm(request.POST or None, request.FILES or None,
                                    user = request.user)
            else:
                obj = get_object_or_404(Prism_Inst, id = id)
                form = Prism_InstForm(request.POST or None, request.FILES or None,
                                      instance = obj, user = request.user)
        if inst_disp == 'level':
            if id == 'None':
                form = DigitalLevelCreateForm(
                    request.POST or None, request.FILES or None,
                    user = request.user)
            else:
                obj = get_object_or_404(DigitalLevel, id = id)
                form = DigitalLevelCreateForm(
                    request.POST or None, request.FILES or None, 
                    instance = obj, user = request.user)
        if inst_disp == 'staff':
                obj = get_object_or_404(Staff, id = id)
                form = StaffCreateForm(
                    request.POST or None, request.FILES or None, 
                    instance = obj, user = request.user)
        if inst_type == 'mets':
            if id == 'None':
                form = Mets_InstForm(request.POST or None, request.FILES or None,
                                      user = request.user, inst_type = inst_disp)           
            else:
                obj = get_object_or_404(Mets_Inst, id = id)
                form = Mets_InstForm(request.POST or None, request.FILES or None,
                                     instance = obj, user = request.user,
                                     inst_type = inst_disp)
        
    if tab == 'certificates':
        tmplate ='instruments/inst_certificates_edit.html'
        if inst_disp == 'edm':
            if id == 'None':
                form = EDMI_certificateForm(request.POST or None,
                                            request.FILES or None,
                                            user=request.user)
            else:
                obj = get_object_or_404(EDMI_certificate, id = id)
                obj.calibration_date = obj.calibration_date.isoformat()
                form = EDMI_certificateForm(request.POST or None,
                                            request.FILES or None, 
                                            instance = obj, 
                                            user = request.user)
        if inst_type == 'mets':
            if id == 'None':
                form = Mets_certificateForm(request.POST or None,
                                            request.FILES or None,
                                            user = request.user,
                                            inst_type = inst_disp)
            else:
                obj = get_object_or_404(Mets_certificate, id = id)
                obj.calibration_date = obj.calibration_date.isoformat()
                form = Mets_certificateForm(request.POST or None, 
                                            request.FILES or None, 
                                            instance = obj, 
                                            user = request.user,
                                            inst_type = inst_disp)

        if inst_disp == 'staff':
            # tmplate = 'staffcalibration/staff_calibration_record_form.html'
            tmplate = 'staffcalibration/staff_calibration_form.html'
            if id == 'None':
                form = StaffCalibrationRecordForm(request.POST or None,
                                            request.FILES or None,
                                            user = request.user)
            else:
                obj = get_object_or_404(StaffCalibrationRecord, id = id)
                obj.calibration_date = obj.calibration_date.isoformat()
                form = StaffCalibrationRecordForm(request.POST or None, 
                                            request.FILES or None, 
                                            instance = obj, 
                                            user = request.user)
                
    models_qs = InstrumentModel.objects.filter(inst_type=inst_disp)
    makes_qs = InstrumentMake.objects.filter(
        id__in=models_qs.values('make')).exclude(make='OTHERS')
    makes = list(makes_qs.values())
    models = list(models_qs.values())
    if not form.is_valid():
        context = {
            'inst_type' : inst_disp,
            'makes': makes,
            'models': models,
            'form': form
            }
        return render(request, tmplate, context) 
    
    else:
        # Commit content to the database
        frm = form.cleaned_data
        instance = form.save(commit=False)

        # Convert input to database standard units
        if inst_disp != 'hygro':
            manu_unc_const = frm.get('manu_unc_const')
            if manu_unc_const:
                instance.manu_unc_const, _ = db_std_units(
                    frm['manu_unc_const'],frm['units_manu_unc_const'])
                if inst_disp == 'edm' or inst_disp == 'prism':
                    instance.manu_unc_const =instance.manu_unc_const * 1000
                
            manu_unc_ppm = frm.get('manu_unc_ppm')
            if manu_unc_ppm:
                manu_ppm, _ = db_std_units(
                    frm['manu_unc_ppm'], frm['units_manu_unc_ppm'])
                if manu_ppm: instance.manu_unc_ppm = manu_ppm * 1e6 
            frequency = frm.get('frequency')
            if frequency: 
                instance.frequency, _ = db_std_units(frm['frequency'],frm['units_frequency'])
            unit_length = frm.get('unit_length')
            if unit_length: 
                instance.unit_length, _ = db_std_units(
                    frm['unit_length'],frm['units_unit_length'])
            carrier_wavelength = frm.get('carrier_wavelength')
            if carrier_wavelength: 
                c_wave, _ = db_std_units(
                    frm['carrier_wavelength'], frm['units_carrier_wavelength'])
                if c_wave: instance.carrier_wavelength = c_wave * 1e9
            measurement_increments = frm.get('measurement_increments')
            if measurement_increments:
                instance.measurement_increments, _ = db_std_units(
                    frm['measurement_increments'], frm['units_measurement_inc'])
    
        if request.user.company and not request.user.is_staff:
            if inst_disp == 'edm': instance.edm_owner = request.user.company
            if inst_disp == 'prism': instance.prism_owner = request.user.company                
            if inst_type == 'mets': instance.mets_owner = request.user.company
            
        instance.save()
        if tab == 'insts':
            request.session['new_instance'] = instance.pk

        if tab == 'models':
            return HttpResponse('<script>opener.closePopup(window, "%s", "%s");</script>' % (instance.pk, instance))
        else:
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect ('instruments:home', inst_disp=inst_disp)
    
    
@login_required(login_url="/accounts/login")
def register_delete(request, inst_disp, tab, id):

    if tab == 'models':
        if inst_disp == 'edm':
            delete_obj = EDM_Specification.objects.get(id=id)
        if inst_disp == 'prism':
            delete_obj = Prism_Specification.objects.get(id=id)
        if inst_disp == 'baro' or inst_disp == 'thermo' or inst_disp == 'hygro' or inst_disp == 'psy':
            delete_obj = Mets_Specification.objects.get(id=id)

    if tab == 'insts':
        if inst_disp == 'edm':
            delete_obj = EDM_Inst.objects.get(id=id)
        if inst_disp == 'prism':
            delete_obj = Prism_Inst.objects.get(id=id)
        if inst_disp == 'level':
            delete_obj = DigitalLevel.objects.get(id=id)
        if inst_disp == 'staff':
            delete_obj = Staff.objects.get(id=id)
        if inst_disp == 'baro' or inst_disp == 'thermo' or inst_disp == 'hygro' or inst_disp == 'psy':
            delete_obj = Mets_Inst.objects.get(id=id)            
    
    if tab == 'certificates':
        if inst_disp == 'edm':
            delete_obj = EDMI_certificate.objects.get(id=id)   
        if inst_disp == 'baro' or inst_disp == 'thermo' or inst_disp == 'hygro' or inst_disp == 'psy':
            delete_obj = Mets_certificate.objects.get(id=id)
        if inst_disp == 'staff':
            delete_obj = StaffCalibrationRecord.objects.get(id=id) 
    
    try_delete_protected(request, delete_obj)
    
    return redirect ('instruments:home', inst_disp=inst_disp)
    

@login_required(login_url="/accounts/login")
def instrument_register(request, inst_disp):

    table_headings = {'certificates': [
        'Number',
        'Calibration Date',
        'Zero Point Correction',
        'Action']}
    tabs = {}
    
    ################ EDM TAB #################
    if inst_disp == 'edm':
        tabs['models_list'] = EDM_Specification.objects.filter(
            edm_owner = request.user.company)
        tabs['insts_list'] = EDM_Inst.objects.filter(
            edm_specs__edm_owner = request.user.company)
        tabs['certificates_list'] = (EDMI_certificate.objects
            .filter(edm__edm_specs__edm_owner = request.user.company)
            .order_by('edm__edm_number', '-calibration_date')
            .values('pk', 'edm__edm_number', 'prism__prism_number',
                    'calibration_date',
                    'scale_correction_factor', 'zero_point_correction',
                    'html_report'))
        
        table_headings['certificates']= [
            'EDM Number',
            'Prism Number',
            'Calibration Date',
            'Scale Correction Factor',
            'Zero Point Correction (m)',
            'Action']
    
    ################ PRISM TAB #################
    if inst_disp == 'prism':
        tabs['models_list'] = Prism_Specification.objects.filter(
            prism_owner = request.user.company)
        tabs['insts_list'] = Prism_Inst.objects.filter(
            prism_specs__prism_owner = request.user.company)
    
    ################ LEVEL TAB #################
    if inst_disp == 'level':
        tabs['insts_list'] = DigitalLevel.objects.filter(
            level_owner = request.user.company)
    
    ################ STAFF TAB #################
    if inst_disp == 'staff':
        table_headings['certificates']= [
            'Staff Number',
            'Calibration Date',
            'Scale Factor',
            'Graduation Uncertainty',
            'Action']

        tabs['insts_list'] = Staff.objects.filter(
            staff_owner = request.user.company)
        tabs['certificates_list'] = (StaffCalibrationRecord.objects
            .filter(inst_staff__staff_owner = request.user.company)
            .order_by('-calibration_date', 'inst_staff__staff_number')
            .values('pk', 'inst_staff__staff_number',
                    'calibration_date',
                    'scale_factor', 'grad_uncertainty','calibration_report'))
            
    ################ METS TAB #################
    if (inst_disp == 'baro' or inst_disp == 'thermo' 
        or inst_disp == 'hygro' or inst_disp == 'psy'):
        
        tabs['models_list'] = Mets_Specification.objects.filter(
            inst_type = inst_disp, mets_owner = request.user.company)
        tabs['insts_list'] = Mets_Inst.objects.filter(
            mets_specs__inst_type = inst_disp, mets_specs__mets_owner = request.user.company)
        tabs['certificates_list'] = (Mets_certificate.objects.filter(
            instrument__mets_specs__inst_type = inst_disp, instrument__mets_specs__mets_owner = request.user.company)
            .order_by('instrument__mets_number', '-calibration_date')
            .values('pk', 'instrument__mets_number',
                    'calibration_date',
                    'zero_point_correction'))
                    
    context = {
        'inst_disp': inst_disp,
        'inst_types': INST_TYPES,
        'tabs': tabs,
        'table_headings':table_headings
    }
    return render(request, 'instruments/instrument_register.html', context)


@login_required(login_url="/accounts/login") 
def inst_model_createby_inst_type(request, inst_type):
    if request.method=="POST":
        form = InstrumentModelCreateByInstTypeForm(request.POST, inst_type = inst_type)
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
        form = InstrumentModelCreateByInstTypeForm(inst_type = inst_type)
    return render(request, 'instruments/inst_model_create_popup_form.html', {'form': form})


@login_required(login_url="/accounts/login") 
def inst_model_update(request, id):
    this_model = get_object_or_404(InstrumentModel, id = id)
    form = InstrumentModelCreateForm(request.POST or None, 
                                     instance = this_model)
    if form.is_valid():
        form.save()
        return redirect ('instruments:inst_settings')
    else:
        form = InstrumentModelCreateForm(instance = this_model)
    context = {
        'form': form
        }
    return render(request, 'instruments/inst_model_create_form.html', context)


@login_required(login_url="/accounts/login") 
def inst_model_delete(request, id):
    delete_obj = InstrumentModel.objects.get(id=id)
    try_delete_protected(request, delete_obj)
 
    return redirect ('instruments:inst_settings')


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

    models_qs = InstrumentModel.objects.filter(inst_type='level')
    makes_qs = InstrumentMake.objects.filter(
        id__in=models_qs.values('make')).exclude(make='OTHERS')
    makes = list(makes_qs.values())
    models = list(models_qs.values())
    context = {
        'form':form,
        'makes': makes,
        'models': models
        }
    return render(request, 'instruments/inst_level_create_popup_form.html', context)

#####################################################################################
class DigitalLevelCreateView(LoginRequiredMixin, generic.CreateView):
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(DigitalLevelCreateView, self).get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        models_qs = InstrumentModel.objects.filter(inst_type='level')
        makes_qs = InstrumentMake.objects.filter(
            id__in=models_qs.values('make')).exclude(make='OTHERS')
        makes = list(makes_qs.values())
        models = list(models_qs.values())
        context = {
            'form': DigitalLevelCreateForm(user=self.request.user),
            'makes': makes,
            'models': models
            }
        return render(request, 'instruments/inst_level_create_form.html', context)

    def post(self, request, *args, **kwargs):
        form = DigitalLevelCreateForm(request.POST, user=self.request.user)
        if form.is_valid():
            level = form.save()
            level.save()
            return redirect ('instruments:home', inst_disp='level')
        
        return render(request, 'instruments/inst_level_create_form.html', {'form': form})
    
#######################################################################
######################## STAFF CREATE #################################
#######################################################################
def show_calibrated_form_condition(wizard):
    # try to get the cleaned data of step 1
    cleaned_data = wizard.get_cleaned_data_for_step('inst_staff_form') or {}
    # check if the field ``leave_message`` was checked.
    return cleaned_data.get('iscalibrated', True)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        models_qs = InstrumentModel.objects.filter(inst_type='staff')
        makes_qs = InstrumentMake.objects.filter(
            id__in=models_qs.values('make')).exclude(make='OTHERS')
                
        context['makes'] = list(makes_qs.values())
        context['models'] = list(models_qs.values())
        return context
    
    def done(self, form_list, **kwargs):
        data = {k: v for form in form_list for k, v in form.cleaned_data.items()}
        inst_number = data['staff_number']
        inst_owner = data['staff_owner']
        inst_custodian = data['staff_custodian']
        inst_model = data['staff_model']
        
        # Other parameters
        staff_type = data['staff_type']
        staff_length = data['staff_length']
        thermal_coefficient = data['thermal_coefficient']
        iscalibrated = data['iscalibrated']
        isreference = data['isreference']

        # Create Staff

        inst_staff = Staff.objects.create(
                staff_owner = inst_owner,
                staff_number = inst_number,
                staff_custodian = inst_custodian,
                staff_model = inst_model,
                staff_type = staff_type,
                staff_length = staff_length,
                thermal_coefficient = thermal_coefficient,
                iscalibrated = iscalibrated,
                isreference = isreference,
        )
        if iscalibrated:
            site_id = data['site_id']
            job_number = data['job_number']
            inst_level = data['inst_level']
            scale_factor = data['scale_factor']
            grad_uncertainty = data['grad_uncertainty']
            standard_temperature = data['standard_temperature']
            observed_temperature = data['observed_temperature']
            calibration_date = data['calibration_date']
            calibration_report = data['calibration_report']
            
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
        return redirect ('instruments:home', inst_disp='staff')
#########################################################################
STAFF_TEMPLATES_POPUP  = {
                    "inst_staff_form": "instruments/inst_staff_create_form_popup.html",
                    "inst_staff_record_form": "staffcalibration/staff_calibration_record_form_popup.html",
                    }

class StaffCreationWizardPopUp(LoginRequiredMixin, NamedUrlSessionWizardView):
    # get the template names and their steps
    def get_template_names(self):                
        return [STAFF_TEMPLATES_POPUP[self.steps.current]]

    # directory to store the ascii files
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'media')) #
    # get the user
    def get_form_kwargs(self, step=1):
        kwargs = super(StaffCreationWizardPopUp, self).get_form_kwargs(step)
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        models_qs = InstrumentModel.objects.filter(inst_type='staff')
        makes_qs = InstrumentMake.objects.filter(
            id__in=models_qs.values('make')).exclude(make='OTHERS')
        
        context['makes'] = list(makes_qs.values())
        context['models'] = list(models_qs.values())
        return context
    
    def done(self, form_list, **kwargs):
        data = {k: v for form in form_list for k, v in form.cleaned_data.items()}
        inst_number = data['staff_number']
        inst_owner = data['staff_owner']
        inst_custodian = data['staff_custodian']
        inst_make = data['staff_make_name']
        inst_model = data['staff_model_name']

        # Other parameters
        staff_type = data['staff_type']
        staff_length = data['staff_length']
        thermal_coefficient = data['thermal_coefficient']
        iscalibrated = data['iscalibrated']
        isreference = data['isreference']

        # Create Staff
        inst_staff = Staff.objects.create(
                staff_owner = inst_owner,
                staff_custodian = inst_custodian,
                staff_number = inst_number,
                staff_make_name = inst_make,
                staff_model_name = inst_model,
                staff_type = staff_type,
                staff_length = staff_length,
                thermal_coefficient = thermal_coefficient,
                iscalibrated = iscalibrated,
                isreference = isreference,
                )
        if iscalibrated:
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
        return HttpResponse('<script type="text/javascript">window.close()</script>') 
################################################################

@login_required(login_url="/accounts/login") 
def inst_staff_update(request, id):
    this_inst = get_object_or_404(Staff, id = id)
    form = StaffCreateForm(request.POST or None, instance = this_inst, user = request.user)
    if form.is_valid():
        form.save()
        return redirect ('instruments:home', inst_disp='staff')
    
    models_qs = InstrumentModel.objects.filter(inst_type='level')
    makes_qs = InstrumentMake.objects.filter(
        id__in=models_qs.values('make')).exclude(make='OTHERS')
    makes = list(makes_qs.values())
    models = list(models_qs.values())
    context = {
        'form': form,
        'makes': makes,
        'models': models
        }
    return render(request, 'instruments/inst_edit_form.html', context)


@login_required(login_url="/accounts/login") 
def inst_staff_delete(request, id):
    delete_obj = Staff.objects.get(staff_owner=request.user.company, id=id)
    try_delete_protected(request, delete_obj)
        
    return redirect ('instruments:home', inst_disp='staff')
    
    
# Get instrument model based on makes
def get_inst_model_json(request, *args, **kwargs):
    selected_make = request.GET.get('inst_make')

    # get instrument models and list them
    obj_makes = list(InstrumentModel.objects.filter(make__make_abbrev__exact = selected_make).values())
    return JsonResponse({'data': obj_makes})


@login_required(login_url="/accounts/login") 
def edm_recommended_specs(request):
    queryset = Specifications_Recommendations.objects.all()
    queryset_dict = [
        {field.verbose_name: {'field_id':field.name, 
                              'value':getattr(item, field.name)} 
         for field in Specifications_Recommendations._meta.get_fields()[1:]}
        for item in queryset
    ]
    context = {
        'queryset': queryset_dict
    }
    return render(request, 'instruments/inst_spec_edm_recommendations.html', context)
