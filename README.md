# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/logo-drawing.svg)

This is a django-based web application developed by Landgate for itself and other external users (e.g., surveyors and engineers) who are use require their measurement instruments to have calibration traceability back to a standard.

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

### Clone the Medjil repo 
```
git clone https://github.com/Landgate/Medjil.git
cd Medjil
pip install -r requirements.txt
```

### Django Migration
```
python manage.py makemigrations
python manage.py migrate
```

### Create superuser for admin
```
python manage.py createsuperuser
```
Wait for the prompt and enter an email and password. 
This is the root user and has all the privillages and access. 

``` 
python manage.py runserver
```

### Load initial data using custom migrations
```
copy accounts\custom_migrations\*.py accounts\migrations
copy baseline_calibration\custom_migrations\*.py baseline_calibration\migrations
copy calibrationsites\custom_migrations\*.py calibrationsites\migrations
copy instruments\custom_migrations\*.py instruments\migrations
copy rangecalibration\custom_migration\*.py rangecalibration\migrations

python manage.py migrate
```

Open a web browser and enter address http://127.0.0.1:8000/ into the address bar. 
# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/HomePage.PNG)

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