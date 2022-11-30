# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/logo.png)

This is a django-based web application developed by Landgate for itself and other external users (e.g., surveyors and engineers) who are use require their measurement instruments to have calibration traceability back to a standard.

# Requirements

Python 3.8 or higher plus see requirements.txt
Git CLI

## Installation - Python

Download the [```Medjil```](https://github.com/Landgate/Medjil/archive/refs/heads/main.zip) package and unzip to your working directory (e.g., "C:/Data/Development/django-projects/"). 

Install ```Python 3``` or ```Anaconda 3```. Note that this application has been tested with ```Python 3.8.8```

### Check version in Command Prompt
python --version 

## Installation - Git CLI
https://git-scm.com/download/win and install the right version 

### Check the installation in Command Prompt
git –version

### Generate ssh key
Go to user directory - e.g., C:\Users\likxx00
Create a new directory called ".ssh"
In the Command Prompt > 
``` 
cd .ssh
sh-keygen -t ed25519 -C "your_email@example.com"
start-ssh-agent.cmd
cd .ssh 
clip < id_ed25519.pub
```

### github security configuration
Open github in browser and log in 
```
Go go Profiles > Settings > Developer Settings > Personal Token > Token (classic) 
```
Insert Name & Create a token
Copy it and save it. 

## Create a virtual environemnt
Install a python package called "virtualenv" from the command prompt and activate it. 
By activating the environment, your project packages will be installed in that library. 

```
cd <Working directory> e.g., cd C:\Data\Development\django-projects
pip install virtualenv 
virtualenv .venv
.\.venv\Scripts\activate
```
## Clone the Medjil repo 
### Clone and navigate to the directory
```
git clone https://github.com/Landgate/Medjil.git
cd Medjil
```
### Install the requirements.txt
```
pip install -r requirements.txt
```

## Migration

```
python manage.py makemigrations
python manage.py migrate
```

## Create superuser and login
```
python manage.py createsuperuser
```
Wait for the prompt and enter an email and password. 
This is the root user and has all the privillages and access. 

``` 
python manage.py runserver
```

Open a web browser and enter address http://127.0.0.1:8000/ into the address bar. 
# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/HomePage.PNG)

Open the internet browser and copy the development server address to view the website. More information is provided under docs/_build/html

### Authors


* **Khandu** - *Staff Calibration software, Testing, Integration and Deployment*, Landgate
* **Irek Baran**, *Graphic design, Technical Manuals and Guidelines*, Landgate
* **Kent Wheeler** - *Project Management, EDMI Calibration software, Testing*, Landgate


### License

Copyright 2020-2021 Landgate

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
