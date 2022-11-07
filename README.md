# ![Medjil](https://github.com/Landgate/Medjil/blob/main/assets/logo.png)

This is a django-based web application developed by Landgate for itself and other external users (e.g., surveyors and engineers) who are use require their measurement instruments to have calibration traceability back to a standard.

### Requirements

Python 3.8 or higher plus see requirements.txt

### Installation

Download the [```Medjil```](https://github.com/Landgate/Medjil/archive/refs/heads/main.zip) package and unzip to your working directory (e.g., "C:/Data/Development/django-projects/"). 

Install ```Python 3``` or ```Anaconda 3```. Note that this application has been tested with ```Python 3.8.8```

Install a python package called "virtualenv" from the command prompt
 ```
	pip install virtualenv 
```

In your working directory (e.g., "C:/Data/Development/django-projects/"), create a virtual python environment called "venv" in the command prompt and activate the virtual environment:

```
	cd C:/Data/Development/django-projects/
	virtualenv venv
	.\venv\Scripts\activate
```
Navigate to "Medjil" - install python requirements and migrate the default package. 

```	
	cd Staff-Calibration
	pip install -r requirements.txt
	python manage.py makemigrations
	python manage.py migrate
```

Type the email address and password when prompted. If migration is successful, type:

```
	python manage.py runserver
```

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
