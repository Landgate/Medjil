::****************************************************************************************************************************************************************************************
::
:: Prerequisite: You must samlapi from the CMD and set AWS_PROFILE to the role name.
:: 
:: This Batch file is used assign Environment variables to the configurations in settings.py file for the Staffcalibration django application.
::
:: To run this successfully, In CMD, type the name of the file with an argument of environment type you are deploying to. For e.g. Medjil_AssignEnv.bat dev or Medjil_AssignEnv.bat test etc.
:: It assigns the SSM Parameters to the Database configurations for the settings.py file
:: Only run this file when you want to run some commands like python manage.py runserver, makemigrations, migrate, collectstatic etc on your local desktop.
:: Run this batch file and then execute the commands on your local desktop or else it will through some errors like SECRET_KEY is configured or Database credentails are not configured.
::
:: Change History:
:: 19-April-2024 Dilan Patel - Initial Version
::
::*****************************************************************************************************************************************************************************************


REM Pass in env as first param
set MEDJIL_ENVIRONMENT=%1

REM Passes in the Database Configurations from the SSM Paramaters
for /f "tokens=*" %%a IN ('aws --region ap-southeast-2 ssm get-parameter --name /%MEDJIL_ENVIRONMENT%/Medjil/Zappa/SECRET_KEY --with-decryption --output text --query Parameter.Value') DO (SET MEDJIL_SECRET_KEY=%%a)

for /f "tokens=*" %%a IN ('aws rds describe-db-clusters --region ap-southeast-2 --db-cluster-identifier medjil-database --output text --query DBClusters[0].Endpoint') DO (SET MEDJIL_DB_HOST=%%a)

for /f "tokens=*" %%a IN ('aws --region ap-southeast-2 ssm get-parameter --name /%MEDJIL_ENVIRONMENT%/Medjil/Zappa/DB_PASSWORD --with-decryption --output text --query Parameter.Value') DO (SET MEDJIL_DB_PASSWORD=%%a)

for /f "tokens=*" %%a IN ('aws --region ap-southeast-2 ssm get-parameter --name /%MEDJIL_ENVIRONMENT%/Medjil/Zappa/DB_USER --output text --query Parameter.Value') DO (SET MEDJIL_DB_USER=%%a)

for /f "tokens=*" %%a IN ('aws --region ap-southeast-2 ssm get-parameter --name /%MEDJIL_ENVIRONMENT%/Medjil/Zappa/DB_NAME --output text --query Parameter.Value') DO (SET MEDJIL_DB_NAME=%%a)

for /f "tokens=*" %%a IN ('aws --region ap-southeast-2 ssm get-parameter --name /%MEDJIL_ENVIRONMENT%/Medjil/EMAIL_HOST_PASSWORD --with-decryption --output text --query Parameter.Value') DO (SET MEDJIL_EMAIL_HOST_PASSWORD=%%a)

for /f "tokens=*" %%a IN ('aws --region ap-southeast-2 ssm get-parameter --name /%MEDJIL_ENVIRONMENT%/Medjil/EMAIL_HOST_USER --output text --query Parameter.Value') DO (SET MEDJIL_EMAIL_HOST_USER=%%a)

for /f "tokens=*" %%a IN ('aws --region ap-southeast-2 ssm get-parameter --name /%MEDJIL_ENVIRONMENT%/Medjil/DB_ENGINE --output text --query Parameter.Value') DO (SET MEDJIL_DB_ENGINE=%%a)