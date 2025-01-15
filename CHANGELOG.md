# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/logo-drawing.svg)

Medjil is an on-line instrument calibration portal that allows for rigorous calibration of baselines (the standard) and survey equipment (e.g. EDM Instrumentation or levelling staff).
This code is a Django-based open-source web application developed by Landgate. 

# Medjil Beta testing
Medjil is now available for Beta testing. We are seeking expressions of interest from stakeholders to test Medjil and provide feedback. 
Press [Start Testing](http://medjil.lb.landgate.wa.gov.au) to begin. 

## Issues Fixed 
* In the lists of staff calibrations and staff calibration certificates the action buttons and to edits or delete a record are missing.
    - Buttons added (?)
* Cancelling the “Edit Barcoded Staff Certificate” interface (in the levelling registry) jumps to barcoded staff register in the dashboard. 
    - Url reverse corrected (?)


## Additions | Fixes | Changes 
### [1.0.19] - 2025-01-15 - [Kent Wheeler]
Changes
* Changes made to EndNotes to allow full flexibility.

## Additions | Fixes | Changes 
### [1.0.18] - 2025-01-14 - [Kent Wheeler]
Additions
* atmos_corr_formula added to edm_specification model
  - *instruments/migrations/0004_auto_recommended_specifications.py*
  - *instruments/migrations/0005_alter_staff_iscalibrated_alter_staff_isreference_and_more.py*
  - *instruments/migrations/0006_changes_from_beta_testing.py*
  - *instruments/forms.py*
  - *instruments/models.py*
  - *common_func/Convert.py*
  - *instruments/templates/instruments/inst_spec_edm_edit_popup_form.html*
  - *calibrationguide/templates/calibrationguide/edmi_calibration_manual.html*
* add instrument specifications supplied by Aptella and UPG
  - *assets/data/InitialData/Specification Recommendations/Edm Specification Recommendations.csv*
  - *assets/data/InitialData/Default Instruments/Default Instrument Models.csv*

Changes
* EDM specifications changed to accept minimal parameters
  - *edm_calibration\templates\edm_calibration\calibrate_report.html*
  - *calibrationguide\templates\calibrationguide\edmi_calibration_manual.html*
  - *baseline_calibration\templates\baseline_calibration\errors_report.html*
  - *edm_calibration\templates\edm_calibration\errors_report.html*
  - *instruments\templates\instruments\inst_certificates_edit.html*
  - *instruments\templates\instruments\inst_edit_form.html*
  - *instruments\templates\instruments\inst_model_create_form.html*
  - *assets\data\InitialData\Specification Recommendations\Edm Specification Recommendations.csv*
  - *instruments\migrations\0006_changes_from_beta_testing.py*
  - *common_func\LeastSquares.py*
  - *common_func\SurveyReductions.py*
  - *instruments\models.py*
  - *baseline_calibration\views.py*
  - *edm_calibration\views.py*
  - *instruments\views.py*


### [1.0.17] - 2025-01-07 - [Kent Wheeler]
Additions
* Add link to backcapture to dashboard for VA
  - *templates/base_generic.html*
  - *backcapture/templates/backcapture/import_dli.html*
  - *backcapture/templates/backcapture/import_report.html*
* Editing and Deleting Baseline calibrations restricted to users company
  - *baseline_calibration/templates/baseline_calibration/baseline_calibration_home.html*

Changes
* Filtering Instrument register restricted to users company
* Ordering of Instrument models set to align with `def __str__`
  - *instruments/views.py*
  - *instruments/models.py*
  - *instruments/templates/instruments/inst_global_settings.html*
* EDM observation file changes to allow null mets observations.
  - *common_func/Convert.py*
  - *common_func/SurveyReductions.py*

Fixes
* Importing EDM observations checks model validations
	- *edm_calibration/views.py*
    - *edm_calibration/templates/edm_calibration/edm_rawdata.html*
   	- *baseline_calibration/views.py*
    - *baseline_calibration/templates/baseline_calibration/edm_rawdata.html*

### [1.0.16] - 2025-01-06 - [Kent Wheeler]
Fixed
* Add security to accounts with user_passes_test
	- *accounts/views.py*
* Fix bug def user_profile not saving locations
	- *accounts/views.py*

### [1.0.15] - 2025-01-06 - [Kent Wheeler]
Fixed
* Add Queensland, and SA baselines to initial migration
* Visibility of baselines restricted according to user location settings
	- *baseline_calibration/admin.py*
	- *edm_calibration/admin.py*
	
* All tested and working - github updated

### [1.0.14] - 2024-12-11 - [Kent Wheeler]
Fixed
* Included missing fields in Admin site
	- *baseline_calibration/admin.py*
	- *edm_calibration/admin.py*
	- *instruments/admin.py*

* All tested and working - github updated

### [1.0.13] - 2024-12-11 - [Kent Wheeler]
Added
* Added baseline_calibration/bulk_report_download/ url, form and html for bulk download of calibration data on specified baselines
* Added edm_calibration/bulk_report_download/ url, form and html for bulk download of edmi calibration data from specified baselines
* django.contrib.auth.decorators import user_passes_test added to edm_calibration/view.py

* All tested and working - github updated

### [1.0.12] - 2024-12-06 - [Khandu]
Added
* Added filter based on location group in forms.py in RangeCalibration/forms.py
	- *RangeCalibration/forms.py*
* Added filter based on location group * Role in forms.py in staffcalibration/forms.py
	- *staffcalibration/forms.py*
* All tested and working - github updated

### [1.0.12] - 2024-12-04 - [Khandu]
Fixed
* Removed Group - "Landgate" & "Geodesy" and replaced by "Verifying Authority". All Survey Team Members added to Admin Group by Default. All Landgate NATA members added to VerifyingAuthority
	- *accounts/apps.py*
	- *accounts/signals.py*
	- *accounts/migrations/0003_create_suser.py*
	
Added
* Added a model named Location in accounts/models.py
* Added a locations field for CustomUser model as a ManyToMany to Location. This is allow Users to have multiple locations. 
	- *accounts/models.py*
* Added the new field locations to Admin Site
	- *accounts/admin.py*
	- *accounts/sites.py*
* Added the new field locations to forms - UserSignUp, CustomUserChangeForm
* Added user.locations.set(form.cleaned_data['locations']) in user_signup function in views.py
	- *accounts/views.py*


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
