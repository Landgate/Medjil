# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/logo-drawing.svg)

Individual states and territories have regulations that require the Surveyor-General (or an institution) to arrange for a standard or standards to be available to enable surveyors to comply with requirements to calibrate measuring equipment. Regular calibration of survey instrumentation is required to ensure the distances measured are legally traceable back to the national standard, currently provided by the National Measurement Act 1960.


Medjil is an on-line instrument calibration portal that allows for rigorous calibration of baselines (the standard) and survey equipment (e.g. EDM Instrumentation or levelling staff).
This code is a Django-based open-source web application developed by Landgate. 

# Medjil Beta testing

Medjil is now available for Beta testing. We are seeking expressions of interest from stakeholders to test Medjil and provide feedback.
Press [Start Testing](http://medjil.lb.landgate.wa.gov.au) to begin. 

## Major Points

- **Production Environment URL**: http://medjil.lb.landgate.wa.gov.au/
- Please send your feedback to geodesy@landgate.wa.gov.au
- When you sign up, you will be assigned normal user permissions. (You will need to supply us your log-in details to be given the permissions of a Verifying Authority)
- Data from our staff-calibration portal has been migrated and users who have previously registered can use the same log in.
- Feedback is welcome immediately but no later than **31 Dec 2024**.
- We aim to launch Medjil in **March 2025** with the re-calibration of the WA EDM baselines.
- The database from Medjil Beta testing will be cleared before the official launch.
- After the official launch of Medjil, we plan to decommission Baseline.exe software.

Medjil is a serverless application on AWS. Please allow a few seconds for it to wake up. [Here](./Medjil-QuickUserGuide.pdf) is a quick reference guide that might be helpful to new users. To download the guide, right-click the link and select "Save link as...".

# Medjil Cloning and Local development
To clone and contribute to development in a local, off-line environment, please consider the following information.

### Requirements
Python 3.8 or higher plus see requirements.txt
Git CLI
#### Installation - Python
Install ```Python 3``` or ```Anaconda 3```. Note that this application has been tested with ```Python 3.8.8```
#### Check version in Command Prompt
python --version  

### Create a virtual environment
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
### Django Migration and load initial data
```
python manage.py collectstatic

set EMAIL_HOST_USER=admin@admin.com
set EMAIL_HOST_PASSWORD=admin
set DEBUG=1

python manage.py migrate
```

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
Use the sample datasets in the folder .\assets\data\Test Data\ to conduct some test calibrations. 

### Database Relationship diagram
[dbdiagram.io](https://dbdiagram.io/d/63db952d296d97641d7df322)

### Django User permission & groups
Permissions are rules or restrictions to view, add, change, delete that can be assigned to a user or group of users

Group is a group of users. One user can be part of many groups and one group can have many users. Groups can use of labeling users.
Groups can contain list of permissions

### Admin permissions
``is_staff`` can access the admin site. Specific permissions should be given to access in the admin site.   
``is_superuser`` can access the admin site and has all the permissions without explicitly assigning them. 

### Authors

* **Khandu** - *Application development and deployment*, Landgate
* **Irek Baran**, *Graphic design, Technical Manuals and Guidelines, Testing*, Landgate
* **Kent Wheeler** - *Project Management, EDMI Calibration software, Testing*, Landgate


### License
Copyright © 2020-2024 Western Australian Land Information Authority.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
