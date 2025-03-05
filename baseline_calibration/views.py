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
from collections import OrderedDict
from copy import deepcopy
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.forms import formset_factory, modelformset_factory
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
import json
from math import sqrt
from statistics import mean
import numpy as np
import pandas as pd

from calibrationsites.models import Pillar
from .forms import (
    PillarSurveyForm,
    UploadSurveyFilesForm,
    ChangeSurveyFilesForm,
    EDM_ObservationForm,
    Certified_DistanceForm,
    Std_Deviation_MatrixForm,
    Uncertainty_BudgetForm,
    Uncertainty_Budget_SourceForm,
    AccreditationForm,
    PillarSurveyResultsForm,
    PillarSurveyApprovalsForm,
    BulkBaselineReportForm)
from .models import (
    Pillar_Survey,
    PillarSurveyResults,
    EDM_Observation,
    Accreditation,
    Uncertainty_Budget,
    Uncertainty_Budget_Source,
    Certified_Distance,
    Std_Deviation_Matrix)
from common_func.Convert import (
    import_csv_to_observations,
    import_csv_to_levels,
    uncertainty_qry2,
    baseline_qry2,
    get_endnotes,
    )
from common_func.SurveyReductions import (
    raw_edm_obs_reductions,
    validate_survey2,
    add_calib_uc2,
    add_surveyed_uc2,
    adjust_alignment_survey,
    reduce_sets_of_obs, 
    hd_std_function,
    edm_std_function, 
    offset_slope_correction,
    refline_std_dev, 
    sum_uc_budget,
    get_delta_os,
    add_typeB)
from medjil.settings import *
from common_func.LeastSquares import (
    LSA,
    ISO_test_b,
    ISO_test_c)
from common_func.validators import try_delete_protected


def is_staff(user):
    return user.is_staff


@login_required(login_url="/accounts/login")
@user_passes_test(is_staff)
def calibration_home(request):
    locations = list(request.user.locations.values_list('statecode', flat=True))
    
    pillar_surveys = Pillar_Survey.objects.filter(
        Q(certified_distance__isnull=True) | Q(certified_distance__distance=0)
        & Q(baseline__state__statecode__in = locations)
        ).order_by('baseline_id', '-survey_date')

    context = {
        'pillar_surveys': pillar_surveys
    }
    return render(request, 'baseline_calibration/baseline_calibration_home.html', context)


@login_required(login_url="/accounts/login") 
@user_passes_test(is_staff)
def report(request, id):    
    # This uses the html report saved to the database to popluate the report
    # It also loads the approvals form that can be edited and saved.
    psr_qs = get_object_or_404(PillarSurveyResults, pillar_survey=id)
    ps_approvals = PillarSurveyApprovalsForm(
        request.POST or None, instance=psr_qs)
    if ps_approvals.is_valid():
        ps_approvals.save()
        return redirect('baseline_calibration:calibration_home')
    
    context = {'ps_approvals':ps_approvals,
               'html_report': psr_qs.html_report}
    return render(request, 'baseline_calibration/display_report.html', context)


@login_required(login_url="/accounts/login") 
def uc_budgets(request):
    uc_budget_list = Uncertainty_Budget.objects.filter(
        Q(name = 'Default', company__company_name = 'Landgate')|
        Q(company = request.user.company))
    
    context = {
        'uc_budget_list': uc_budget_list}
    
    return render(request, 'baseline_calibration/uncertainty_budgets_list.html', context)


@login_required(login_url="/accounts/login")
def uc_budget_create(request):    
    uc_sources = formset_factory(Uncertainty_Budget_SourceForm, extra=0)
    if request.method == 'POST':        
        uc_sources = uc_sources(request.POST)
        uc_budget = Uncertainty_BudgetForm(
            request.POST,
            sources = uc_sources,
            user=request.user)
        if uc_budget.is_valid() and uc_sources.is_valid():
            uc_budget.save()
            # Save the pk if this has been called during calibration with add_btn.
            request.session['new_instance'] = uc_budget.instance.pk
            for uc_source in uc_sources:
                f = uc_source.save(commit=False)
                f.uncertainty_budget = uc_budget.instance
                f.save()
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('baseline_calibration:uc_budgets')
    else:
        ini_budget={}
        ini_budget['std_dev_of_zero_adjustment'] = (
            Uncertainty_Budget.objects.get(
                        name = 'Default', 
                        company__company_name = 'Landgate')
                        .std_dev_of_zero_adjustment)
        ini_sources = Uncertainty_Budget_Source.objects.filter(
                        uncertainty_budget__name = 'Default', 
                        uncertainty_budget__company__company_name = 'Landgate')
        
        uc_sources = uc_sources(initial=[vars(row) for row in ini_sources])
        
        uc_budget = Uncertainty_BudgetForm(
            initial=ini_budget, 
            sources = uc_sources,
            user=request.user)
    
    context = {}
    context['Header'] = 'Create Custom Uncertainty Budget'        
    context['form'] = uc_budget
    context['formset'] = uc_sources
    
    return render(request, 'baseline_calibration/uncertainty_budget_form.html', context)


@login_required(login_url="/accounts/login") 
def uc_budget_edit(request, id=None):
    user_company = request.user.company
    
    uc_sources = modelformset_factory(
        Uncertainty_Budget_Source,
        form=Uncertainty_Budget_SourceForm, 
        extra=0)
    qs = Uncertainty_Budget_Source.objects.filter(
        uncertainty_budget__company = user_company,
        uncertainty_budget = id)
    formset = uc_sources(request.POST or None, queryset=qs)
    
    obj = get_object_or_404(
        Uncertainty_Budget, id=id, 
        company=request.user.company)
    uc_budget = Uncertainty_BudgetForm(
        request.POST or None, 
        sources = formset,
        instance=obj)
    
    # Edit the database according to submitted valid form.
    if all([uc_budget.is_valid(), formset.is_valid()]):
        uc_budget.save()
        new_sources_id=[]
        for uc_source in formset:
            new_sources_id.append(uc_source.instance.id)
            source = uc_source.save(commit=False)
            source.uncertainty_budget = uc_budget.instance
        formset.save()
        
        # Delete uc_source if it has been removed
        for orig_source in qs:
            if not orig_source.id in new_sources_id:
                orig_source.delete()
                 
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('baseline_calibration:uc_budgets')

    context = {}
    context['Header'] = 'Edit Uncertainty Budget'
    context['form'] = uc_budget
    context['formset'] = formset
    
    return render(request, 'baseline_calibration/uncertainty_budget_form.html', context)


@login_required(login_url="/accounts/login") 
def uc_budget_delete(request, id):
    # only allow delete if record belongs to company
    delete_obj = Uncertainty_Budget.objects.get(
        id=id,
        company = request.user.company)
    try_delete_protected(request, delete_obj)
    
    return redirect('baseline_calibration:uc_budgets')


@login_required(login_url="/accounts/login") 
def accreditations(request):
    # Only list records that belong to company
    accreditation_list = Accreditation.objects.filter(
        accredited_company = request.user.company)
    
    context = {
        'accreditation_list': accreditation_list}
    
    return render(request, 'baseline_calibration/accreditation_list.html', context)


@login_required(login_url="/accounts/login") 
def accreditation_edit(request, id=None):
    context = {}
    # if id==None this is a new accredittion.
    if id == 'None':
        accreditation = AccreditationForm(request.POST or None,
                                          request.FILES or None,
                                          user=request.user)
        context['Header'] = 'Input Accreditation Details'
    else:
        obj = get_object_or_404(
            Accreditation, id=id,
            accredited_company=request.user.company)
        obj.valid_from_date = obj.valid_from_date.isoformat()
        obj.valid_to_date = obj.valid_to_date.isoformat()
        accreditation = AccreditationForm(request.POST or None,
                                          request.FILES or None,
                                          instance=obj,
                                          user=request.user)

        context['Header'] = 'Edit Accreditation Details'
    
    if accreditation.is_valid():
        accreditation.save()  
        # Save the pk if this has been called during calibration with add_btn.
        request.session['new_instance'] = accreditation.instance.pk
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        else:
            return redirect('baseline_calibration:accreditations')
        
    context['form'] = accreditation
    
    return render(request, 'baseline_calibration/accreditation_form.html', context)


@login_required(login_url="/accounts/login") 
def accreditation_delete(request, id):
    # Only allow delete if record belongs to company
    delete_obj = Accreditation.objects.get(
        id=id,
        accredited_company = request.user.company)

    try_delete_protected(request, delete_obj)
    
    return redirect('baseline_calibration:accreditations')


@login_required(login_url="/accounts/login") 
@user_passes_test(is_staff)
def certified_distances_home(request, id):
    pillar_surveys = (Pillar_Survey.objects.annotate(
        num_cd=Count('certified_distance')).filter(num_cd__gt=0).filter(
            baseline__pk=id)
            .order_by('survey_date'))
    first_pillar_survey = pillar_surveys.first()
    pillars = Pillar.objects.filter(
        site_id = id).order_by('order')
    
    # Calculate data for graph
    back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                    '#00FF00', '#008000', '#00FFFF', '#008080', 
                    '#0000FF', '#000080', '#FF00FF', '#800080']
    
    labels = [pillar_survey.survey_date for pillar_survey in pillar_surveys]
    dataset1 = []
    dataset2 = []
    dataset3 = []
    i=0
    for pillar in pillars[1:]:
        data1 =[]
        data2 =[]
        data3 =[]
        for pillar_survey in pillar_surveys:
            if pillar_survey.results.status == 'publish':
                data1.append(
                    pillar_survey.certified_distances().get(
                    to_pillar = pillar).distance
                    - first_pillar_survey.certified_distances().get(
                        to_pillar = pillar).distance
                    )
                data2.append(
                    pillar_survey.certified_distances().get(
                    to_pillar = pillar).offset
                    - first_pillar_survey.certified_distances().get(
                        to_pillar = pillar).offset
                    )
                data3.append(
                    pillar_survey.certified_distances().get(
                    to_pillar = pillar).reduced_level
                    - first_pillar_survey.certified_distances().get(
                        to_pillar = pillar).reduced_level
                    )

        dataset1.append(
             {'borderColor':back_colours[i],
             'borderWidth': 1,
             'data':data1,
             'fill':False,
             'label': pillar.name,
             'pointRadius': 1,
             'showLine': True,
             'tension': 0})
        dataset2.append(
             {'borderColor':back_colours[i],
             'borderWidth': 1,
             'data':data2,
             'fill':False,
             'label': pillar.name,
             'pointRadius': 1,
             'showLine': True,
             'tension': 0})
        dataset3.append(
             {'borderColor':back_colours[i],
             'borderWidth': 1,
             'data':data3,
             'fill':False,
             'label': pillar.name,
             'pointRadius': 1,
             'showLine': True,
             'tension': 0})
        i+=1
        if i>len(back_colours): i=0
    
    graph1_data = {
        'labels':labels,
        'datasets':dataset1}
    graph2_data = {
        'labels':labels,
        'datasets':dataset2}
    graph3_data = {
        'labels':labels,
        'datasets':dataset3}
    
    #convert from python to json
    graph1_data = json.dumps(graph1_data, cls=DjangoJSONEncoder)
    graph2_data = json.dumps(graph2_data, cls=DjangoJSONEncoder)
    graph3_data = json.dumps(graph3_data, cls=DjangoJSONEncoder)
    context = {
        'pillar_surveys':pillar_surveys,
        'graph1_datasets': graph1_data,
        'graph2_datasets': graph2_data,
        'graph3_datasets': graph3_data}
    
    return render(
        request,
        'baseline_calibration/certified_distances_list.html', 
        context)


@login_required(login_url="/accounts/login") 
@user_passes_test(is_staff)
def certified_distances_edit(request, id):
    pillar_survey_results_obj = PillarSurveyResults.objects.select_related(
        'pillar_survey').filter(pillar_survey=id).first()
    
    pillar_survey_results_form = PillarSurveyResultsForm(
        request.POST or None, 
        request.FILES or None, 
        instance=pillar_survey_results_obj)

    certified_distances_qs = Certified_Distance.objects.filter(
        pillar_survey=id).select_related(
        'from_pillar', 'to_pillar')

    std_deviation_matrix_qs = Std_Deviation_Matrix.objects.filter(
        pillar_survey=id).select_related(
        'to_pillar')

    certified_distances_formset = modelformset_factory(
        Certified_Distance, form=Certified_DistanceForm, extra=0
    )(request.POST or None, prefix='formset1', queryset=certified_distances_qs)

    std_deviation_matrix_formset = modelformset_factory(
        Std_Deviation_Matrix, form=Std_Deviation_MatrixForm, extra=0
    )(request.POST or None, prefix='formset2', queryset=std_deviation_matrix_qs)

    if (
        pillar_survey_results_form.is_valid()
        and certified_distances_formset.is_valid()
        and std_deviation_matrix_formset.is_valid()
    ):
        pillar_survey_results_form.save()
        certified_distances_formset.save()
        std_deviation_matrix_formset.save()
        return redirect(request.POST.get('next', 'calibrationsites:home'))

    context = {
        'pillar_survey_results_form': pillar_survey_results_form,
        'certified_distances_obj': certified_distances_qs,
        'combined': zip(certified_distances_qs, certified_distances_formset),
        'certified_distances_formset': certified_distances_formset,
        'std_deviation_matrix_formset': std_deviation_matrix_formset,
        'std_combined': list(zip(std_deviation_matrix_qs, std_deviation_matrix_formset)),
    }

    return render(request, 'baseline_calibration/certified_distances_form.html', context)


@login_required(login_url="/accounts/login") 
@user_passes_test(is_staff)
def bulk_report_download(request):
    if request.method == 'POST':
        form = BulkBaselineReportForm(request.POST,user=request.user)
        if form.is_valid():
            baseline = form.cleaned_data['baseline']
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']
            
            # Set default values if dates are not provided
            if not from_date:
                from_date = date(1800, 1, 1)
            if not to_date:
                to_date = date.today() + timedelta(days=1)
            
            # Filter based on date range
            data = Pillar_Survey.objects.filter(
                baseline=baseline,
                survey_date__range=[from_date, to_date]
            ).values("results__html_report")
            
            if not data.exists():
                # No data found, return to form with an error message
                return render(request, 'baseline_calibration/bulk_report_download.html', {
                    'form': form,
                    'error': 'No data found for the selected baseline and date range.'
                })
            
            baseline_name = baseline.site_name
            df = pd.DataFrame(data)
            # Create a response object and set the appropriate headers
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{baseline_name}_baseline_clibration_reports.html"'
            # Write the DataFrame to the response without the header
            df.to_csv(path_or_buf=response, index=False, header=False)
            return response
    else:
        form = BulkBaselineReportForm(user=request.user)

    return render(request, 'baseline_calibration/bulk_report_download.html', {'form': form})


@login_required(login_url="/accounts/login")   
@user_passes_test(is_staff)
def survey_delete(request, id):
    survey = get_object_or_404(
        Pillar_Survey, 
        id=id,
        accreditation__accredited_company = request.user.company.id)
    try_delete_protected(request, survey)
    
    return redirect('baseline_calibration:calibration_home')


@login_required(login_url="/accounts/login")
@user_passes_test(is_staff)
def survey_create(request, id=None):
    instance = None
    if id:
        instance = Pillar_Survey.objects.filter(
            id=id,
            accreditation__accredited_company=request.user.company.id
        ).first()
    
    pillar_survey_form = PillarSurveyForm(
        request.POST or None,
        request.FILES or None, 
        instance=instance, 
        user=request.user)
    
    survey_files = (
        ChangeSurveyFilesForm(request.POST or None, request.FILES or None) 
        if instance else 
        UploadSurveyFilesForm(request.POST or None, request.FILES or None)
    )
    
    import_errors = []
    if pillar_survey_form.is_valid() and survey_files.is_valid():
        # Do not save immediately
        pillar_survey = pillar_survey_form.save()
        
        # Check for file validation errors before saving
        if survey_files.cleaned_data.get('edm_file'):
            edm_file = survey_files.cleaned_data.get('edm_file')
            import_errors.extend(import_csv_to_observations(edm_file, pillar_survey))

        if survey_files.cleaned_data.get('lvl_file'):
            lvl_file = survey_files.cleaned_data.get('lvl_file')
            import_errors.extend(import_csv_to_levels(lvl_file, pillar_survey))
        
        if import_errors:
            if not instance: pillar_survey.delete()
            return render(request, 'baseline_calibration/errors_report.html', {
                'Check_Errors': {'Errors': import_errors, 'Warnings': []}
            })

        return redirect('baseline_calibration:edm_observations_update', id=pillar_survey.pk)
    
    headers = {
        'page0': 'Calibrate the Baseline',
        'page1': 'Instrumentation',
        'page2': 'Corrections / Calibrations Applied to Instruments',
        'page3': 'Error Budget and File Uploads',
    }

    return render(request, 'baseline_calibration/PillarSurvey_form.html', {
        'headers': headers,
        'form': pillar_survey_form,
        'survey_files': survey_files,
    })



@user_passes_test(is_staff)
@login_required(login_url="/accounts/login")
def edm_observations_update(request, id):
    pillar_survey = get_object_or_404(
        Pillar_Survey.objects.select_related('baseline'),id=id)
    edm_observations_qs = pillar_survey.edm_observation_set.all()
    
    # Create the formset
    formset = modelformset_factory(EDM_Observation, form=EDM_ObservationForm, extra=0)

    if request.method == 'GET':
        # Prepare Page 5 of 5
        raw_edm_obs, _, _ = raw_edm_obs_reductions(pillar_survey)
        
        pillars = pillar_survey.baseline.pillars.all().order_by('order')
        adjust_alignment_survey(raw_edm_obs, pillars)
        
        edm_obs_formset = formset(None, queryset=edm_observations_qs)
        formset = zip(edm_obs_formset,raw_edm_obs.values())
        
        return render(request, 'baseline_calibration/edm_observations_update.html', {
            'Page': 'Page 5 of 5',
            'id': id,
            'edm_obs_formset':edm_obs_formset,
            'pillar_survey': pillar_survey,
            'formset': formset})

    elif request.method == 'POST':
        edm_obs_formset = formset(request.POST, queryset=edm_observations_qs)
        # Validate and save the formset
        if edm_obs_formset.is_valid():
            edm_obs_formset.save()
            return redirect('baseline_calibration:compute_calibration', id=id)
    

@user_passes_test(is_staff)
@login_required(login_url="/accounts/login")
def compute_calibration(request, id):
    try:
    # if 1==1:
        # Retrieve the Pillar Survey instance and baseline dictionary of records
        pillar_survey = get_object_or_404(
            Pillar_Survey.objects.select_related(
                'edm', 'prism', 'uncertainty_budget', 'baseline'
            ).prefetch_related(
                Prefetch(
                    'edm_observation_set',
                    queryset=EDM_Observation.objects.select_related('from_pillar', 'to_pillar')
                )
            ),
            id=id
        )
        baseline = baseline_qry2(pillar_survey,id)
        
        # Handle the approvals form and commit computed solution from session memory if valid.
        ps_approvals = PillarSurveyApprovalsForm(
            request.POST or None, 
            instance=pillar_survey)
        if ps_approvals.is_valid():
            # Save signiture block
            ps_approvals.save()
            
            # pillar survey update
            psu = request.session['pillar_survey_result_' + str(id)]
            del request.session['pillar_survey_result_' + str(id)]
            PillarSurveyResults.objects.update_or_create(
                pillar_survey=pillar_survey,
                defaults={
                    'zero_point_correction': psu['zero_point_correction'],
                    'zpc_uncertainty': psu['zpc_uncertainty'],
                    'degrees_of_freedom': psu['degrees_of_freedom'],
                    'experimental_std_dev': psu['experimental_std_dev'],
                    'reference_height': baseline['site'].reference_height,
                    'html_report': psu['html_report'],
                }
            )
            
            # Commit the certified distances and standard deviations within a single atomic transaction
            with transaction.atomic():
                # Commit the certified distances
                cd_formset = request.session['cd_formset_' + str(id)]
                del request.session['cd_formset_' + str(id)]
                for cd in cd_formset:
                    cd['from_pillar'] = baseline['pillars'].get(name=cd['from_pillar'])
                    cd['to_pillar'] = baseline['pillars'].get(name=cd['to_pillar'])
                
                    Certified_Distance.objects.update_or_create(
                        pillar_survey=pillar_survey,
                        from_pillar=cd['from_pillar'],
                        to_pillar=cd['to_pillar'],
                        defaults={
                            'distance': cd['distance'],
                            'a_uncertainty': cd['a_uncertainty'],
                            'k_a_uncertainty': cd['k_a_uncertainty'],
                            'combined_uncertainty': cd['combined_uncertainty'],
                            'k_combined_uncertainty': cd['k_combined_uncertainty'],
                            'offset': cd['offset'],
                            'os_uncertainty': cd['os_uncertainty'],
                            'k_os_uncertainty': cd['k_os_uncertainty'],
                            'reduced_level': cd['reduced_level'],
                            'rl_uncertainty': cd['rl_uncertainty'],
                            'k_rl_uncertainty': cd['k_rl_uncertainty'],
                        }
                    )
                
                # Commit the standard deviations
                bay = request.session['bay_' + str(id)]
                sigma_vv = request.session['sigma_vv_' + str(id)]
                del request.session['bay_' + str(id)]
                del request.session['sigma_vv_' + str(id)]
                for b, vv in zip(bay, sigma_vv):
                    p0, p1 = b.split(' - ')
                
                    Std_Deviation_Matrix.objects.update_or_create(
                        pillar_survey=pillar_survey,
                        from_pillar=baseline['pillars'].get(name=p0),
                        to_pillar=baseline['pillars'].get(name=p1),
                        defaults={
                            'std_uncertainty': sqrt(vv),
                        }
                    )
                                
            return redirect('baseline_calibration:calibration_home')
        
        # Code below is either the approvals form was invalid or this is a GET request.
        raw_edm_obs, raw_lvl_obs, calib = raw_edm_obs_reductions(pillar_survey)
    
        Check_Errors = validate_survey2(
            pillar_survey=pillar_survey,
            baseline=baseline,
            calibrations=calib,
            raw_edm_obs=raw_edm_obs,
            raw_lvl_obs=raw_lvl_obs)
        
        if len(Check_Errors['Errors']) > 0:
           return render(request, 'baseline_calibration/errors_report.html', 
                         {'Check_Errors':Check_Errors})
              
        #----------------- Query related data -----------------#
    
        report_notes = get_endnotes(
            pillar_survey = pillar_survey,
            company=request.user.company, calibration_type='B')
        
        uc_budget = uncertainty_qry2(pillar_survey)
        uc_budget['sources'] = add_calib_uc2(
            uc_budget['sources'],
            calib,
            pillar_survey)
        
        alignment_survey = adjust_alignment_survey(
            raw_edm_obs, 
            baseline['pillars'])
        
        for k, p in alignment_survey.items():
            p['reduced_level'] = float(raw_lvl_obs[k]['reduced_level'])
            p['rl_uncertainty'] = float(raw_lvl_obs[k]['rl_standard_deviation'])*2
            p['k_rl_uncertainty'] = 2
            
        edm_observations = reduce_sets_of_obs(raw_edm_obs)
        
        hd_trend = hd_std_function(
            baseline['pillars'],
            raw_lvl_obs)
        
        edm_trend = edm_std_function(
            edm_observations,
            uc_budget['stddev_0_adj'])           #y = Ax + B
                
        pillars = [p.name for p in baseline['pillars']]
           
        matrix_A = []
        matrix_x = []
        matrix_P = []
        o_temp = []
        o_pres = []
        o_humi = []
        len_alignment_survey = len(alignment_survey)
        len_edm_observations = len(edm_observations)
        for i, o in enumerate(edm_observations.values()):
            o_temp.append(o['Temp'])
            o_pres.append(o['Pres'])
            o_humi.append(o['Humid'])
            o = offset_slope_correction(o,
                                      raw_lvl_obs,
                                      alignment_survey,
                                      baseline['d_radius'],
                                      baseline['site'].reference_height)
              
            o['Reduced_distance'] = (o['slope_dist'] 
                                    + o['Offset_Correction']
                                    + o['Slope_Correction'])
    
            #----------------- Calculate Uncertainties -----------------#
            o['uc_sources'] = add_surveyed_uc2(o, edm_trend, hd_trend,
                                              pillar_survey,
                                              uc_budget['sources'],
                                              alignment_survey)
                  
            o['uc_budget'] = refline_std_dev(o, 
                                             alignment_survey,
                                             pillar_survey.edm)
            o['apriori_uc_budget'] = deepcopy(o['uc_budget'])
              
            o['uc_combined'] = sum_uc_budget(o['uc_budget'])
    
            #----------------- Least Squares -----------------#
            #Build the design matrix 'A' (ISO 17123-4:2012 eq.11)
            o['id']= str(i+1)
            A_row = [0]*len_alignment_survey
            A_row[-1] = -1
            bay = [pillars.index(o['from_pillar']),
                     pillars.index(o['to_pillar'])]
            A_row[min(bay)-1] = -1
            A_row[max(bay)-1] = 1
            matrix_A.append(A_row)
              
            matrix_x.append(o['Reduced_distance'])
            
            P_row = [0]*len_edm_observations
            P_row[i] = (1/
                        o['uc_combined']['std_dev']**2)
            matrix_P.append(P_row)
             
        matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)
        
        for o in edm_observations.values():
            o['residual'] = residuals[o['id']]['residual']
            o['std_residual'] = residuals[o['id']]['std_residual']
    
        ISO_test=[]
        if baseline['history'].exists():
            prev = baseline['history'].first()
            ISO_test.append(
                ISO_test_b(
                    {'dof': prev.results.degrees_of_freedom,
                     'So': prev.results.experimental_std_dev},
                    chi_test
                )
            )
        else:
            report_notes.append(
                'The ISO 17123:4 Test B statistical test has not been performed due to insufficient historical records.'
            )
    
            
        ISO_test.append(
            ISO_test_c(
                matrix_y[-1]['value'],
                matrix_y[-1]['std_dev'],
                chi_test))
        
        #-------------- Extract pillar to pillar uncertainties from VCV---------------#
        # Formula 6.10 (6.13) - Adjustment Computation (Ghilani) 4th Edition
        
        vcv_A = []
        bay = []
        for i0, p0 in enumerate(pillars[:-1]):
            for p1 in pillars[i0+1:]:
                i1 = pillars.index(p1)
                A_row = [0]*(len(pillars))
                if i0!=0: A_row[i0-1] = -1
                A_row[i1-1] = 1
                
                bay.append(p0+' - '+ p1)
                vcv_A.append(A_row)
        
        
        vcv_A = np.array(vcv_A, dtype=object)
        sigma_vv = vcv_A @ vcv_matrix @ vcv_A.T
        
        # save data to session and commit form Submit
        request.session['bay_' + str(id)] = bay
        request.session['sigma_vv_' + str(id)] = sigma_vv.diagonal().tolist()
        
        #----------------- Extract the certified distances from LSA results -----------------#
        # Calculate the average temp and pressure for survey #
        certified_dists = {}
        avg_t = mean(o_temp)
        avg_p = mean(o_pres)
        avg_h = mean(o_humi)
        sess_data = []
        pillar_survey.some_lum_adopted = False  # Temporary flag
        
        for i, (p, d) in enumerate(zip(pillars[1:], matrix_y[:-1])):
            cd = {}
            ini_cd = {}
            cd['pillar_survey'] = pillar_survey.id
            cd['date'] = pillar_survey.survey_date.isoformat()
            cd['slope_dist'] = d['value']
            cd['Reduced_distance'] = d['value']
            cd['Temp'] = avg_t
            cd['Pres'] = avg_p
            cd['Humid'] = avg_h
            cd['to_pillar'] = p
            cd['from_pillar'] = pillars[0]
            cd['delta_os'] = get_delta_os(alignment_survey,cd)
            cd['reduced_level'] = float(raw_lvl_obs[p]['reduced_level'])
            cd['rl_standard_deviation'] = float(raw_lvl_obs[p]['rl_standard_deviation'])
        
            #--------------------- Add Type B --------------------------------------#
            cd['uc_sources'] = add_surveyed_uc2(cd, edm_trend, hd_trend,
                                               pillar_survey,
                                               uc_budget['sources'],
                                               alignment_survey)
            cd['uc_sources'] = add_typeB(cd['uc_sources'], d, matrix_y, chi_test['dof'])
        
            cd['uc_budget'] = refline_std_dev(cd, 
                                              alignment_survey,
                                              pillar_survey.edm)
            cd['uc_combined'] = sum_uc_budget(cd['uc_budget'])
            certified_dists[p] = cd
            
            # apply LUM if necessary
            lum = ((pillar_survey.accreditation.LUM_constant +
                   pillar_survey.accreditation.LUM_ppm * d['value'] * 10**-3)
                   * 0.001 )
            
            if pillar_survey.apply_lum and cd['uc_combined']['uc95'] < lum:
                cd['uc_combined']['uc95'] = lum
                cd['uc_combined']['k'] = 2
                cd['lum_adopted'] = True
                if not pillar_survey.some_lum_adopted:
                    pillar_survey.some_lum_adopted = True
                    report_notes.append(
                        'The uncertainty of some of the certified distances '
                        'are smaller than the company\'s accredited '
                        'least uncertainty of measurement (LUM). In these cases '
                        'the LUM has been published in this report.')
            
            # populate a dictionary to save to session memory and commit after form Submit
            ini_cd['from_pillar'] = pillars[0]
            ini_cd['to_pillar'] = p
            ini_cd['distance'] = d['value']
            ini_cd['a_uncertainty'] = cd['uc_budget']['07']['ui95']
            ini_cd['k_a_uncertainty'] = cd['uc_budget']['07']['k']
            ini_cd['combined_uncertainty'] = cd['uc_combined']['uc95']
            ini_cd['k_combined_uncertainty'] = cd['uc_combined']['k']
            ini_cd['offset'] = cd['delta_os']
            ini_cd['os_uncertainty'] = (cd['uc_budget']['11']['std_dev'] *
                                        cd['uc_budget']['11']['k'])
            ini_cd['k_os_uncertainty'] = cd['uc_budget']['11']['k']
            ini_cd['reduced_level'] = float(raw_lvl_obs[p]['reduced_level'])
            ini_cd['rl_uncertainty'] = (cd['uc_budget']['10']['std_dev'] *
                                        cd['uc_budget']['10']['k'])
            ini_cd['k_rl_uncertainty'] = cd['uc_budget']['10']['k']
            sess_data.append(ini_cd)
            
            # add an extra for the first pillar
            if i == 0:
                ini_cd0 = ini_cd.copy()
                ini_cd0['to_pillar'] = pillars[0]
                ini_cd0['distance'] = 0
                ini_cd0['offset'] = 0
                ini_cd0['reduced_level'] = float(raw_lvl_obs[pillars[0]]['reduced_level'])
                ini_cd0['rl_uncertainty'] = float(raw_lvl_obs[pillars[0]]['std_dev'])
                sess_data.insert(0, ini_cd0)
        
        request.session['cd_formset_' + str(pillar_survey.id)] = sess_data
        
        #Prepare the context for the template
        od = OrderedDict(sorted(alignment_survey.items()))
        alignment_survey = list(od.values())
        certified_dists = list(certified_dists.values())
        
        back_colours = ['#FF0000', '#800000', '#FFFF00', '#808000', 
                        '#00FF00', '#008000', '#00FFFF', '#008080', 
                        '#0000FF', '#000080', '#FF00FF', '#800080']
        for cd, colour in zip(certified_dists, back_colours):
            for uc in cd['uc_budget'].values():
                uc['chart_colour'] = colour
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            for uc in cd['uc_sources']:
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            cd['uc_sources']=sorted(cd['uc_sources'], key=lambda x: x['group_verbose'])
            cd['uc_budget'] = OrderedDict(sorted(cd['uc_budget'].items()))
            
        edm_observations = list(edm_observations.values())
        n_rpt_shots = max([len(e['grp_Bay']) for e in edm_observations])
        for o in edm_observations:
            num_to_append = n_rpt_shots - len(o['grp_Bay'])
            if num_to_append > 0:
                o['grp_Bay'].extend([''] * num_to_append)
            
            for uc in o['uc_budget'].values():
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            
            for uc in o['uc_sources']:
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            
            o['uc_budget'] = OrderedDict(sorted(o['uc_budget'].items()))
            
            for uc in o['apriori_uc_budget'].values():
                if uc['group'] in dict(Uncertainty_Budget_Source.group_types).keys():
                    uc['group_verbose'] = dict(Uncertainty_Budget_Source.group_types)[uc['group']]
            o['apriori_uc_budget'] = OrderedDict(sorted(o['apriori_uc_budget'].items()))
    
        if 'edmi_drift' in calib.keys():
            calib['edmi_drift']['xyValues'] = [
                {'x':c['calibration_date'].isoformat()[:10],
                'y':c['scale_correction_factor'],
                'zpc':c['zero_point_correction']} 
                for c in calib['edmi'].values()]
    
        #prepare the data for the comparison to history graph
        surveys={}
        if baseline['history']: 
            first_cds = baseline['history'].first().certified_distances()[1:]
            colour_index = 0
            for ps in baseline['history']:
                colour = back_colours[colour_index]
                colour_index += 1
                if colour_index > len(back_colours): colour_index = 0
                dte = ps.survey_date.isoformat()
                surveys[ps.pk] = {'date':dte, 
                                   'bays':[]}
                for cd_0, cd in zip(first_cds, ps.certified_distances()[1:]):
                     if cd.from_pillar.name != cd.to_pillar.name:
                        surveys[ps.pk]['bays'].append(
                            {'to_pillar':cd.to_pillar.name,
                             'diff_to_initial': float(cd.distance) - float(cd_0.distance),
                             'chart_colour':colour})
            
            # add the survey currently being processed to the dataset
            surveys[id] = {'date':pillar_survey.survey_date.isoformat(),
                            'bays':[]}
            for cd_0, cd in zip(first_cds, certified_dists):
                diff = 0
                if baseline['history']: 
                    diff = float(cd_0.distance)-cd['Reduced_distance']
                surveys[id]['bays'].append(
                    {'to_pillar':cd['to_pillar'],
                     'diff_to_initial': diff,
                     'chart_colour':'#808080'}
                    )
            baseline['history'] = surveys
            baseline['pillar_meta'] = []
            for p in baseline['pillars']:
                baseline['pillar_meta'].append(model_to_dict(p))
                baseline['pillar_meta'][-1]['reduced_level'] = (
                    float(raw_lvl_obs[p.name]['reduced_level']))
        
        context = {'pillar_survey':pillar_survey,
                   'calib':calib,
                   'baseline': baseline,
                   'certified_dists': certified_dists,
                   'chi_test':chi_test,
                   'ISO_test':ISO_test,
                   'alignment_survey': alignment_survey,
                   'edm_observations': edm_observations,
                   'report_notes': report_notes,
                   'Check_Errors':Check_Errors}
        
        html_report = render_to_string(
            'baseline_calibration/calibrate_report.html', context)
        
        # create update for pillar survey processing
        n = len(matrix_y)-1
        request.session['pillar_survey_result_' + str(id)] = {
            'zero_point_correction': matrix_y[n]['value'],
            'zpc_uncertainty': matrix_y[n]['std_dev'],
            'degrees_of_freedom': chi_test['dof'],
            'experimental_std_dev': chi_test['So'],
            'html_report': html_report
            }           
        
        context = {'pillar_survey': pillar_survey,
                   'html_report': html_report,
                   'ps_approvals':ps_approvals,
                   'hidden':[]}
        
        return render(request, 'baseline_calibration/display_report.html', context)
    
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, 'baseline_calibration/errors_report.html', 
                      {})