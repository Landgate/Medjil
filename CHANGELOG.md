# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/logo-drawing.svg)

Medjil is an on-line instrument calibration portal that allows for rigorous calibration of baselines (the standard) and survey equipment (e.g. EDM Instrumentation or levelling staff).
This code is a Django-based open-source web application developed by Landgate. 

# Medjil Beta testing
Medjil is now available for Beta testing. We are seeking expressions of interest from stakeholders to test Medjil and provide feedback. 
Press [Start Testing](http://medjil.lb.landgate.wa.gov.au) to begin. 

## Issues Fixed 
* 
* In the lists of staff calibrations and staff calibration certificates the action buttons and to edits or delete a record are missing.
    - Buttons added (?)
* Cancelling the “Edit Barcoded Staff Certificate” interface (in the levelling registry) jumps to barcoded staff register in the dashboard. 
    - Url reverse corrected (?)


## Additions | Fixes | Changes 
### [1.0.12] - 2024-12-06 - [Khandu]
Added
* Added filter based on location group in forms.py in RangeCalibration/forms.py
	-*RangeCalibration/forms.py*
* Added filter based on location group * Role in forms.py in staffcalibration/forms.py
	- *staffcalibration/forms.py*
* All tested and working - github updated

### [1.0.12] - 2024-12-04 - [Khandu]
Fixed
* Removed Group - "Landgate" & "Geodesy" and replaced by "Verifying Authority". All Survey Team Members added to Admin Group by Default. All Landgate NATA members added to VerifyingAuthority
	-*accounts/apps.py*
	-*accounts/signals.py*
	-*accounts/migrations/0003_create_suser.py*
	
Added
* Added a model named Location in accounts/models.py
* Added a locations field for CustomUser model as a ManyToMany to Location. This is allow Users to have multiple locations. 
	-*accounts/models.py*
* Added the new field locations to Admin Site
	-*accounts/admin.py*
	-*accounts/sites.py*
* Added the new field locations to forms - UserSignUp, CustomUserChangeForm
* Added user.locations.set(form.cleaned_data['locations']) in user_signup function in views.py
	-*accounts/views.py*


### [1.0.11] - 2024-12-02 - [Khandu]
Fixed
* Edit Barcoded Staff Certificate template showing *Step of*. Changed template under 
    - *instruments/views.py > register_edit* 

### [1.0.10] - 2024-11-26 - [Kent Wheeler]
Added 
* Site name added to baseline calibration report  
    - *templates\baseline_calibration/certified_distances_list.html*  
Changed
* 
Fixed
* Prevent clicking submit twice 
    - *assets/js/script.js*
* Fix missing printed lines
    - *instruments/templates/instruments/inst_edit_form.html*
    - *templates/base_generic.html*
    - *templates/base_popup.html*

### [1.0.09] - 2024-11-21 - [Kent Wheeler]
Added
* Added more prisms to list
    - *assets/data/InitialData/Default Instruments/Default Instrument Models.csv*

Changed
* Added known issue when entering EDM-Model specs for Trimble
    - *Medjil-QuickUserGuide.pdf*

### [1.0.08] - 2024-11-11 - [Kent Wheeler]
Added
* 
Fixed
* Fix Select Observation in the Imported EDM Observations page
    - *edm_calibration/views.py*
* Error report cancel btn directed to EDMI
    - *edm_calibration/templates/edm_calibration/edm_rawdata.html*
    - *edm_calibration/views.py*

Changed
* Added known issue when entering EDM-Model specs for Trimble
    - *Medjil-QuickUserGuide.pdf*

### [1.0.07] - 2024-11-07 - [Kent Wheeler]
Added
* Add TS 50 to Model List
    - *assets/data/InitialData/Default Instruments/Default Instrument Models.csv*

Fixed
* Changes to backcapture commit
    - *backcapture/views.py*

### [1.0.06] - 2024-10-15 - [Kent Wheeler]
Added
* Help text for scf, a.x and A.x
    - *instruments/migrations/0006_changes_from_beta_testing.py*

Fixed
* Make consistent use of scf where scf as A.x = a.x + 1
    - *baseline_calibration/forms.py*
    - *calibrationguide/templates/calibrationguide/edmi_calibration_manual.html*
    - *edm_calibration/templates/edm_calibration/calibrate_report.html*
    - *edm_calibration/templates/edm_calibration/intercomparison_report.html*
    - *instruments/models.py*
* Javascript treated number as string
    - *instruments/templates/instruments/inst_certificates_edit.html*
* Rename instrument SN for unique constraints
    - *backcapture/views.py*
* Convert mm to m
    - *backcapture/views.py*

Changed
* Updated year on copyright
    - *calibrationguide/views.py*

### [1.0.05] - 2024-10-14 - [Kent Wheeler]
Added
* Added experiental standard deviation & Chi Sq. test
    - *baseline_calibration/templates/baseline_calibration/calibrate_report.html*

Fixed
* Correct ISO 17123-4:2012 eq.14 and Manu Specifications
    - *backcapture/views.py*
    - *baseline_calibration/admin.py*
    - *baseline_calibration/forms.py*
    - *baseline_calibration/migrations/0001_initial.py*
    - *baseline_calibration/migrations/0002_changes_from_beta_testing.py*
    - *baseline_calibration/models.py*
    - *baseline_calibration/templates/baseline_calibration/baseline_calibration_home.html*
    - *baseline_calibration/views.py*
    - *common_func/Convert.py*
    - *common_func/LeastSquares.py*
    - *common_func/SurveyReductions.py*
    - *edm_calibration/templates/edm_calibration/calibrate_report.html*
    - *edm_calibration/views.py*
    - *instruments/migrations/0006_changes_from_beta_testing.py*
    - *instruments/models.py*

### [1.0.04] - 2024-10-11 - [Kent Wheeler]
Added
* 

Fixed
* Correct ISO 17123-4:2012 eq.14
    - *common_func/LeastSquares.py*

### [1.0.03] - 2024-10-07 - [Khandu]
Added
* Added permission levels
    - *accounts/signals.py*

Fixed
* Fixed staff calibration ranges list display for individuals & amended file validations for csv files
*staffcalibration/forms.py*
* Corrected help text in field_file in StaffcalibrationRecord
    - *staffcalibration/migrations/0001_initial.py*
    - *staffcalibration/models.py*
    - *staffcalibration/views.py*

### [1.0.02] - 2024-09-05 - [Kent Wheeler]
Added
* media/edmi_calibration folder added to .gitignore
    - *.gitignore*
* Updated README file
    - *README.md*
* Added Medjil User Guide
    - *Medjil-QuickUserGuide.pdf*

Fixed
* Corrected Earth radius
    - *common_func/Convert.py*

Changed
* Added extra widget fields to Certified_DistanceForm
    - *baseline_calibration/forms.py*
    - *baseline_calibration/templates/baseline_calibration/certified_distances_form.html*
    - *baseline_calibration/views.py*
    - *common_func/SurveyReductions.py*

### [1.0.01] - 2024-09-02 - [Kent Wheeler]
Added
* Added Beta Testing to README.md
    - *README.md*

### [1.0.00] - 2024-08-30 - [Khandu]
Added
* Added 403 Forbidden error template
    - *accounts/templates/accounts/403.html*
* Added Roles & Permission levels to admin page
    - *accounts/signals.py*
