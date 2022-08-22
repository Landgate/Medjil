import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
#from django.views.generic import TemplateView
# from django.forms import formset_factory
from django.forms.models import model_to_dict

# Create your views here.

from django.db.models import Avg
from .forms import (CalibrateBaselineForm,
                    CalibrateBaselineForm1,
                    CalibrateBaselineForm2,
                    CalibrateBaselineForm3,
                    CalibrateBaselineForm4)
from instruments.models import (EDM_Inst,
                    EDMI_certificate,
                    Mets_certificate)
from staffcalibration.models import StaffCalibrationRecord
from calibrationsites.models import (Pillar,
                                     CalibrationSite)
from .models import (Pillar_Survey,
                    EDM_Observation,
                    Accreditation,
                    Uncertainty_Budget,
                    Uncertainty_Budget_Source,
                    Calibrated_Baseline,
                    Certified_Distance,
                    Std_Deviation_Matrix)
from geodepy.geodesy import grid2geo, rho
from common_func.Convert import *
from common_func.SurveyReductions import *
from instrument_calibrations.settings import *
from common_func.LeastSquares import LSA
from django.shortcuts import redirect

@login_required(login_url="/accounts/login") 
def calibration_home(request):
    messages.warning(request, "This is an error")
    #return HttpResponse("This is my Baseline Calibration Home")
    return render(request, 'baseline_calibration/calibrate_baseline.html', {})


#@login_required(login_url="/accounts/login") 
def calibrate_baseline(request):
    if request.method=="POST":
        form = CalibrateBaselineForm(request.POST, request.FILES)
        if form.is_valid():
        		frm = form.cleaned_data
        		calib = {}
        		baseline={}
        		        		
        		edm_inst = EDM_Inst.objects.select_related().get(pk=frm['edm'].pk)
        		edm_wave = edm_inst.edm_specs.carrier_wavelength
        		manu_ref_ind = edm_inst.edm_specs.manu_ref_refrac_index
        		
        		#----------------- Query appropriate instrument calibrations -----------------#
        		calib['edmi'] = EDMI_certificate.objects.filter(
        		                               calibration_date__lte = frm['survey_date'] ,
        		                               edm__pk = frm['edm'].pk, prism__pk = frm['prism'].pk
        		                               ).order_by('-calibration_date')
        		calib['staff'] = StaffCalibrationRecord.objects.filter(
        		                               calibration_date__lte = frm['survey_date'] ,
        		                               inst_staff__pk = frm['staff'].pk
        		                               ).order_by('-calibration_date').first()
        		calib['them'] = Mets_certificate.objects.filter(
        		                               calibration_date__lte = frm['survey_date'] ,
        		                               instrument__pk = frm['thermometer'].pk
        		                               ).order_by('-calibration_date').first()
        		calib['baro'] = Mets_certificate.objects.filter(
        		                               calibration_date__lte = frm['survey_date'] ,
        		                               instrument__pk = frm['barometer'].pk
        		                               ).order_by('-calibration_date').first()
        		calib['hygro'] = Mets_certificate.objects.filter(
        		                               calibration_date__lte = frm['survey_date'] ,
        		                               instrument__pk = frm['hygrometer'].pk
        		                               ).order_by('-calibration_date').first()

        		accreditation = Accreditation.objects.get(pk = frm['accreditation'].pk)

        		#----------------- Query Baseline Location -----------------#  
        		baseline['site'] = CalibrationSite.objects.get(pk = frm['baseline'].pk)
        		baseline['pillars'] = Pillar.objects.filter(
        		                              site_id__pk = frm['baseline'].pk
        		                              ).order_by('order')
        		
        		baseline_enz = Pillar.objects.filter(
        		                              site_id__pk = frm['baseline'].pk
        		                              ).aggregate(Avg('easting'), Avg('northing'), Avg('zone'))
        		baseline_llh = grid2geo(float(baseline_enz['zone__avg']),
        		                        float(baseline_enz['easting__avg']),
        		                        float(baseline_enz['northing__avg']))
        		d_radius = rho(baseline_llh[0])
        		
        		#----------------- Query the default Uncertainty -----------------#
        		uc_budget = {}
        		uc_budget_c = (Uncertainty_Budget_Source.objects.filter(
        		                               uncertainty_budget__pk = frm['uncertainty_budget'].pk ,
        		                               ))
        		uc_budget['sources']=class2dict(uc_budget_c)
        		uc_budget['sources'], calib = add_calib_uc(uc_budget['sources'], calib,frm['survey_date'])
        		uc_budget['subtotal'] = subtotal_uc_budget(uc_budget['sources'])

        		stddev_0_adj = (Uncertainty_Budget.objects.get(
        		                               pk = frm['uncertainty_budget'].pk ,
        		                               )).std_dev_of_zero_adjustment

    				#----------------- Import data files -----------------#
        		edm_clms=['From_Pillar',
        		      'To_Pillar',
        		      'inst_ht',
        		      'tgt_ht',
        		      'Hz_direction',
        		      'Raw_slope_dist',
        		      'Raw_Temp',
        		      'W_Temp',
        		      'Raw_Pres',
        		      'Raw_Humid']
        		edm_observations = csv2dict(frm['edm_file'],edm_clms)
        		
        		level_clms=['Pillar',
                         'RL',
                         'Std_Dev']
        		level_observations = csv2dict(frm['lvl_file'],level_clms,0)
        		
        		Check_Errors = validate_form(frm, calib, accreditation, edm_observations, baseline, level_observations)
        		
        		if len(Check_Errors['Errors']) > 0:
        			msg="<h4>The following errors have been detected:</h4>"
        			msg+="<p>"
        			for e in Check_Errors['Errors']:
        				msg+="	"+ e +"<br>"
        			msg+="</p>"
        			msg+="<h4>The following warnings have been detected:</h4>"
        			msg+="<p>"
        			for w in Check_Errors['Warnings']:
        				msg+="	"+ w +"<br>"
        			msg+="</p>"
        			return HttpResponse(msg)

        		edm_observations = reduce_sets_of_obs(edm_observations)
        		alignment_survey = adjust_alignment_survey(edm_observations,
                                                level_observations,
                                                baseline['pillars'])
        		pillars = [p.name for p in baseline['pillars']]
        		
        		edm_trend = edm_std_function(edm_observations,stddev_0_adj)           #y = Ax + B
        		
        		
        		matrix_A = []
        		matrix_x = []
        		matrix_P = []
            #----------------- Calculate Corrections -----------------#
        		for k, o in edm_observations.items():        			
        			#----------------- Instrument Corrections -----------------#
        			o['Temp'],c = apply_calib(o['Raw_Temp'],frm['thermo_calib_applied'], calib['them'])
        			o['Pres'],c = apply_calib(o['Raw_Pres'],frm['baro_calib_applied'], calib['baro'])
        			o['Humid'],c = apply_calib(o['Raw_Humid'],frm['hygro_calib_applied'], calib['hygro'])
        			c,o['Calibration_Correction'] = apply_calib(o['Raw_slope_dist'],
        			                                           frm['edmi_calib_applied'], calib['edmi'][0])
        			
        			#----------------- Range Calibration Corrections -----------------#
        			o = (edm_mets_correction(o, edm_wave, frm['mets_applied']))
        			
        			o = (offset_slope_correction(o,
        			                        level_observations,
        			                        alignment_survey,
        			                        d_radius))
        			
        			o['Reduced_distance'] = (o['Raw_slope_dist'] 
        			                       + o['Calibration_Correction']
        			                       + o['Mets_Correction']
        			                       + o['Offset_Correction']
        			                       + o['Slope_Correction'])

        			#----------------- Calculate Uncertainties -----------------#
        			o['uc_sources'] = add_surveyed_uc(o, edm_trend, 
        			                                uc_budget['subtotal'],
        			                                level_observations,
        			                                alignment_survey)
        			                                
        			o['uc_subtotal'] = subtotal_uc_budget(o['uc_sources'])
        			    
        			o['uc_budget'] = refline_std_dev(o, 
        			                                 alignment_survey,
        			                                 level_observations, 
        			                                 manu_ref_ind)
        			
        			o['uc_combined'] = sum_uc_budget(o['uc_budget'])
        			
        			edm_observations[k] = o

        		#----------------- Least Squares -----------------#
        			#Build the design matrix 'A' (ISO 17123-4:2012 eq.11)
        			A_row = [0]*len(alignment_survey)
        			A_row[len(alignment_survey)-1] = -1
        			bay = [pillars.index(o['From_Pillar']),
        			       pillars.index(o['To_Pillar'])]
        			A_row[min(bay)-1] = -1
        			A_row[max(bay)-1] = 1
        			matrix_A.append(A_row)
        			
        			matrix_x.append(o['Reduced_distance'])
        			
        			P_row = [0]*len(edm_observations)
        			P_row[list(edm_observations.keys()).index(k)] = (1/
                                             o['uc_combined']['std_dev']**2)
        			matrix_P.append(P_row)
        			
        		matrix_y, vcv_matrix, chi_test, residuals = LSA(matrix_A, matrix_x, matrix_P)

        		
        		for k, o in edm_observations.items():
        		    o['residual'] = residuals[k]['residual']
        		    o['std_residual'] = residuals[k]['std_residual']
        		    edm_observations[k] = o
        		
        		#-------------- Extract pillar to pillar uncertainties from VCV---------------#
        		# Formula 6.10 (6.13) - Adjustment Computation (Ghilani) 4th Edition
        		vcv_A = []
        		bay = []
        		for p0 in pillars:
        		    i0 = pillars.index(p0)
        		    for p1 in pillars[1:]:
        		        i1 = pillars.index(p1)
        		        A_row = [0]*(len(pillars))
        		        if i0!=0: A_row[i0-1] = -1
        		        A_row[i1-1] = 1
        		
        		        if not p1+' - '+ p0 in bay and p1!=p0:
        		            bay.append(p0+' - '+ p1)
        		            vcv_A.append(A_row)
        		
        		vcv_A = np.array(vcv_A, dtype=object)
        		sigma_vv = vcv_A @ vcv_matrix @ vcv_A.T
        		
        		#----------------- Extract the certified distances from LSA results -----------------#
        		# Calculate the average temp and pressure for survey #
        		certified_dists={}
        		avg_t = mean([float(o['Temp']) for k, o in edm_observations.items()])
        		avg_p = mean([float(o['Pres']) for k, o in edm_observations.items()])
        		for p, d, c in zip(pillars[1:], matrix_y[:-1], np.diagonal(vcv_matrix[:-1])):
        		    #--------------------- Add Type B --------------------------------------#
        		    cd={}        
        		    cd['Raw_slope_dist'] = d
        		    cd['Reduced_distance'] = d
        		    cd['Temp'] = avg_t
        		    cd['Pres'] = avg_p
        		    cd['To_Pillar'] = p
        		    cd['From_Pillar'] = pillars[0]
        		    cd['delta_os'] = get_delta_os(alignment_survey,cd)

        		    cd['uc_sources'] = add_surveyed_uc(cd, edm_trend, 
        		                                    uc_budget['subtotal'],
        		                                    level_observations,
        		                                    alignment_survey)
        		    cd['uc_sources'] = add_typeB(cd['uc_sources'], c, vcv_matrix, chi_test['dof'])
        		    cd['uc_subtotal'] = subtotal_uc_budget(cd['uc_sources'])

        		    cd['uncertainty'] = refline_std_dev(cd, 
        		                                        alignment_survey,
        		                                        level_observations,
        		                                        manu_ref_ind)
        		    cd['uc_combined'] = sum_uc_budget(cd['uncertainty'])
        		    certified_dists[p] = cd
        		    

        		#return redirect("blog:post_list")
        		#xValues= ['2016-06-30',
        		#                          '2018-07-1',
        		#                          '2020-08-15',
        		#                          '2022-09-20']
        		#yValues= [50,60,70,80]
        		#xyValues = zip(xValues,yValues)
        		#xyValues = [
        		# {'x':'2016-06-30', 'y':50, 'zpc': 0.01},
        		# {'x':'2018-07-1', 'y':60, 'zpc': 0.01},
        		# {'x':'2020-08-15', 'y':70, 'zpc': 0.01},
        		# {'x':'2022-09-20', 'y':80, 'zpc': 0.01}
        		#]
        		#xyTrend = [
        		# {'x':'2016-06-30', 'y':45},
        		# {'x':'2022-09-20', 'y':85}
        		#]

        		alignment_survey = list(alignment_survey.values())
        		certified_dists = list(certified_dists.values())
        		edm_observations = list(edm_observations.values())
        		n_rpt_shots = range(max([len(e['Raw']) for e in edm_observations]))

        		EDMI_calib = {'frm': frm,
        			            'edm_trend': edm_trend,
        			            'baseline': baseline,
        			            'certified_dists':certified_dists,
        			            'alignment_survey': alignment_survey,
        			            'edm_observations': edm_observations,
        			            'n_rpt_shots':n_rpt_shots}
        		
        		return render(request, 'baseline_calibration/calibrate_report.html', EDMI_calib)

    else:
        print('Form not Valid')
        form = CalibrateBaselineForm()
    return render(request, 'baseline_calibration/calibrate_baseline.html', {'form': form})

                                
def test(request):
    if request.method=="POST":
        form = CalibrateBaselineForm1(request.POST, request.FILES)
        if form.is_valid():
        		frm = form.cleaned_data
    				#----------------- Import data files -----------------#

        		edm_clms=['From_Pillar',
        		      'To_Pillar',
        		      'inst_ht',
        		      'tgt_ht',
        		      'Hz_direction',
        		      'Raw_slope_dist',
        		      'Raw_Temp',
        		      'Raw_Pres',
        		      'Raw_Humid']
        		edm_observations = csv2dict(frm['edm_file'],edm_clms)
        		level_clms=['Pillar',
                         'RL',
                         'Std_Dev']
        		level_observations = csv2dict(frm['lvl_file'],level_clms,0)
        		
        		html_ctx = {'job_number':frm['baseline'].pk,
        			          'edm_observations': list(edm_observations.values()),
        			          'level_observations': list(level_observations.values())}
        		request.session['fn'] = html_ctx
        			          	
        		return render(request, 'baseline_calibration/calibrate_baseline_rawdata.html', html_ctx)
        		#return redirect('/baseline_calibration/adjust/', html_data)

    else:
        print('Form not Valid')
        form = CalibrateBaselineForm1()
    return render(request, 'baseline_calibration/calibrate_baseline.html', {'form': form})

def calibrate1(request):
    if request.method == 'POST':
        form = CalibrateBaselineForm1(request.POST or None)
        if form.is_valid():
            frm = form.cleaned_data
            frm['baseline']=frm['baseline'].pk
            frm['computation_date']=frm['computation_date'].strftime("%Y %m, %d")
            frm['survey_date']=frm['survey_date'].strftime("%Y %m, %d")
            request.session['calibrate1'] = frm
            return HttpResponseRedirect('/baseline_calibration/calibrate2')
    else:
        print('Form not Valid')
        form = CalibrateBaselineForm1()
    return render(request, 'baseline_calibration/calibrate.html', {'Header':'Calibrate the Baseline',
    	                                                             'Page': 'Page 1 of 4',
    	                                                             'BackBtn': False,
    	                                                             'form': form})


def calibrate2(request):
    if request.method == 'POST':
        form = CalibrateBaselineForm2(request.POST or None, request.FILES)
        if form.is_valid():
            frm = form.cleaned_data
            frm['edm']=frm['edm'].pk
            frm['prism']=frm['prism'].pk
            frm['level']=frm['level'].pk
            frm['staff']=frm['staff'].pk
            frm['thermometer']=frm['thermometer'].pk
            frm['barometer']=frm['barometer'].pk
            frm['hygrometer']=frm['hygrometer'].pk
            request.session['calibrate2'] = frm
            return HttpResponseRedirect('/baseline_calibration/calibrate3')
    else:
        print('Form not Valid')
        form = CalibrateBaselineForm2()
    return render(request, 'baseline_calibration/calibrate.html', {'Header':'Instrumentation',
    	                                                             'Page': 'Page 2 of 4',
    	                                                             'BackBtn': True,
    	                                                             'form': form})


def calibrate3(request):
    if request.method == 'POST':
        form = CalibrateBaselineForm3(request.POST or None, request.FILES)
        if form.is_valid():
            frm = form.cleaned_data
            request.session['calibrate3'] = frm
            return HttpResponseRedirect('/baseline_calibration/calibrate4')
    else:
        print('Form not Valid')
        form = CalibrateBaselineForm3()
    return render(request, 'baseline_calibration/calibrate.html', {'Header':'Calibrations applied to Instruments',
    	                                                             'Page': 'Page 3 of 4',
    	                                                             'BackBtn': True,
    	                                                             'form': form})


def calibrate4(request):
    if request.method == 'POST':
        form = CalibrateBaselineForm4(request.POST or None, request.FILES)
        if form.is_valid():
            frm = form.cleaned_data
            #request.session['calibrate4'] = frm
            #return HttpResponseRedirect('/baseline_calibration/calibrate4')
    else:
        print('Form not Valid')
        form = CalibrateBaselineForm4()
    print(form)
    return render(request, 'baseline_calibration/calibrate.html', {'Header':'File Uploads',
    	                                                             'Page': 'Page 4 of 4',
    	                                                             'BackBtn': True,
    	                                                             'form': form})






"""

        		this_pillar_survey = Pillar_Survey.objects.create(
        		                        baseline=frm['baseline'],
        		                        survey_date=frm['survey_date'],
        		                        computation_date=frm['computation_date'],
        		                        accreditation=frm['accreditation'],
        		                        observer=frm['observer'],
        		                        weather=frm['weather'],
        		                        job_number=frm['job_number'],
        		                        edm=frm['edm'],
        		                        prism=frm['prism'],
        		                        mets_applied=frm['mets_applied'],
        		                        edmi_calib_applied=frm['edmi_calib_applied'],
        		                        level=frm['level'],
        		                        staff=frm['staff'],
        		                        staff_calib_applied=frm['staff_calib_applied'],
        		                        thermometer=frm['thermometer'],
        		                        thermo_calib_applied=frm['thermo_calib_applied'],
        		                        barometer=frm['barometer'],
        		                        baro_calib_applied=frm['baro_calib_applied'],
        		                        hygrometer=frm['hygrometer'],
        		                        hygro_calib_applied=frm['hygro_calib_applied'],
        		                        #psychrometer=frm['psychrometer'],
        		                        #psy_calib_applied=frm['psy_calib_applied'],
        		                        uncertainty_budget=frm['uncertainty_budget'],
        		                        outlier_criterion=frm['outlier_criterion'],
        		                        fieldnotes_upload=frm['Scanned_field_notes'])
        		this_pillar_survey.save()

        		for k, o in edm_observations.items():
        		  this_EDM_Observation = EDM_Observation.objects.create(
        		                        pillar_survey = this_pillar_survey,
        		                        from_pillar = baseline['pillars'].get(name=o['From_Pillar']),
        		                        to_pillar = baseline['pillars'].get(name=o['To_Pillar']),
        		                        inst_ht = o['inst_ht'],
        		                        tgt_ht = o['tgt_ht'],
        		                        hz_direction = o['Hz_direction'],
        		                        slope_dist = o['Raw_slope_dist'],
        		                        temperature = o['Raw_Temp'],
        		                        wet_temp = o['W_Temp'],
        		                        pressure = o['Raw_Pres'],
        		                        humidity = o['Raw_Humid'])

        		n = len(matrix_y)-1
        		this_Calibrated_Baseline = Calibrated_Baseline.objects.create(
        		                        pillar_survey = this_pillar_survey,
        		                        zero_point_correction = matrix_y[n],
        		                        zpc_uncertainty = sqrt(vcv_matrix[n,n]),
        		                        degrees_of_freedom = chi_test['dof'])
        		this_Calibrated_Baseline.save()

        		for p, vv in zip(bay, np.diagonal(sigma_vv)):
        			p0, p1 = p.split(' - ')
        			this_std_dev_matrix = Std_Deviation_Matrix.objects.create(
        		                        calibrated_baseline = this_Calibrated_Baseline,
        		                        from_pillar = baseline['pillars'].get(name=p0),
        		                        to_pillar = baseline['pillars'].get(name=p1),
        		                        std_uncertainty = sqrt(vv))
        		this_std_dev_matrix.save()
        		
        		    
        		    certified_dist = Certified_Distance.objects.create(
        		                        calibrated_baseline = this_Calibrated_Baseline,
        		                        from_pillar = baseline['pillars'].get(name=cd['From_Pillar']),
        		                        to_pillar = baseline['pillars'].get(name=cd['To_Pillar']),
        		                        distance = cd['Reduced_distance'],
        		                        a_uncertainty = cd['uncertainty']['14']['std_dev']*cd['uncertainty']['14']['k'],
        		                        k_a_uncertainty = cd['uncertainty']['14']['k'],
        		                        combined_uncertainty = cd['uc_combined']['std_dev']*cd['uc_combined']['k'],
        		                        k_combined_uncertainty = cd['uc_combined']['k'],
        		                        offset = cd['delta_os'],
        		                        os_uncertainty = cd['uc_subtotal']['12']['std_dev']* cd['uc_subtotal']['12']['k'],
        		                        k_os_uncertainty =  cd['uc_subtotal']['12']['k'],
        		                        reduced_level = float(level_observations[cd['To_Pillar']]['RL']),
        		                        rl_uncertainty = cd['uc_subtotal']['11']['std_dev']* cd['uc_subtotal']['11']['k'],
        		                        k_rl_uncertainty = cd['uc_subtotal']['11']['k'],
        		                        )
        		    certified_dist.save()
        		
        		#Create some error trapping, if the calibrations need to be applied there must be a calibration record/certificate
        		msg = ''
        		if calib['edmi'] is None and not frm['edmi_calib_applied']: msg += str(frm['edm']) + ' with prism ' +str(frm['prism']) + '<br>'
        		if calib['staff'] is None and not frm['staff_calib_applied']: msg += str(frm['staff']) + '<br>'
        		if calib['them'] is None and not frm['thermo_calib_applied']: msg += str(frm['thermometer']) + '<br>'
        		if calib['baro'] is None and not frm['baro_calib_applied']: msg += str(frm['barometer']) + '<br>'
        		if calib['hygro'] is None and not frm['hygro_calib_applied']: msg += str(frm['hygrometer']) + '<br>'
        		if len(msg) != 0: return HttpResponse('The following instrumentation does not have a calibration certificate for the time of survey: <br><p style="margin-left:10%;">' + msg + '</p>')
        		

"""
