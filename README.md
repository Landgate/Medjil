# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/logo-drawing.svg)

Individual states and territories have regulations that require the Surveyor-General (or an institution) to arrange for a standard or standards to be available to enable surveyors to comply with requirements to calibrate measuring equipment. Regular calibration of survey instrumentation is required to ensure the distances measured are legally traceable back to the national standard, currently provided by the National Measurement Act 1960.



Medjil is a Django-based open-source web application developed by Landgate that allows for rigorous calibration of baselines (the standard) and survey equipment (e.g. EDM Instrumentation or levelling staff).

### Requirements
Python 3.8 or higher plus see requirements.txt
Git CLI
#### Installation - Python
Install ```Python 3``` or ```Anaconda 3```. Note that this application has been tested with ```Python 3.8.8```
#### Check version in Command Prompt
python --version  

### Create a virtual environemnt
Install a python package called "virtualenv" from the command prompt and activate it. 
By activating the environment, your project packages will be installed in that library. 

```
cd <Working directory> e.g., cd C:\Data\Development\django-projects
pip install virtualenv 
virtualenv .venv
.\.venv\Scripts\activate
```

### Clone the Medjil repo and install requirements
The repository can be cloned with a git client or downloading the zip file.  
Below are the commands for using Git commandline.
  ```
  git clone https://github.com/Landgate/Medjil.git
  cd Medjil
  pip install -r requirements.txt
  ```
If you are not familiar with a git client, download the zip file and extract the contents to your working directory.
![image](https://user-images.githubusercontent.com/48744654/205527306-73fd1983-1669-429c-b7ff-bbe141248969.png)
```
cd Medjil-main
pip install -r requirements.txt
```
<!--- ### Django Migration
```
python manage.py makemigrations
python manage.py migrate
```

### Load initial data using custom migrations
```
copy accounts\custom_migrations\*.py accounts\migrations
copy baseline_calibration\custom_migrations\*.py baseline_calibration\migrations
copy calibrationsites\custom_migrations\*.py calibrationsites\migrations
copy instruments\custom_migrations\*.py instruments\migrations
copy rangecalibration\custom_migration\*.py rangecalibration\migrations
copy calibrationguide\custom_migrations\*.py calibrationguide\migrations
set EMAIL_HOST_USER=admin@admin.com
set EMAIL_HOST_PASSWORD=admin

python manage.py migrate
python manage.py runserver
```
--->
### Run a local server
```
python manage.py runserver
```
Open a web browser and enter address http://127.0.0.1:8000/ into the address bar. 

Login to Medjil using the email and password.  
&nbsp;&nbsp;&nbsp;&nbsp;**email**: ``admin@admin.com``  
&nbsp;&nbsp;&nbsp;&nbsp;**password**: ``admin``  

# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/HomePage.PNG)

This is the root user and has all the privilages and access. 
### Test Data 
Use the sample datasets in the folder .\Test Data\ to conduct some test calibrations. 


### Authors

* **Khandu** - *Application development and deployment*, Landgate
* **Irek Baran**, *Graphic design, Technical Manuals and Guidelines*, Landgate
* **Kent Wheeler** - *Project Management, EDMI Calibration software, Testing*, Landgate


### License
Copyright 2020-2021 Landgate

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
