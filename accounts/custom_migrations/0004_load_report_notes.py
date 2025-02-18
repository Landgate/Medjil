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
from django.db import migrations

notes = [
    {'report_type':'B',
     'note_type':'M',
     'note':"""The uncertainty stated in this Report has been calculated in accordance with the principles in JCGM 100:2008 Evaluation of measurement data - Guide to the expression of uncertainty in measurement known as GUM. 
Term ‘uncertainty’ refers to the GUM’s ‘expanded uncertainty' with a covering factor (k) of 2.0, being approximately at 95% confidence level and the ‘standard deviation’ relates the GUM’s ‘standard uncertainty’ (68% confidence level).
When estimating the uncertainty budget of baseline length, both Type A and Type B uncertainties were identified and applied in accordance with GUM and ISO17123-4:2012.
The uncertainty value applies at the time of measurement only and takes no account of any effects that may apply afterwards.
Baseline measurements were performed in accordance with the ISO17123-4:2012 Optics and optical instruments – Field procedures for testing geodetic and surveying instruments – Part 4: Electro-optical distance meters (EDM measurements to reflectors)"""},
    {'report_type':'E',
     'note_type':'M',
     'note':"""The uncertainty stated in this Report has been calculated in accordance with the principles in JCGM 100:2008 Evaluation of measurement data - Guide to the expression of uncertainty in measurement known as GUM. 
Term ‘uncertainty’ refers to the GUM’s ‘expanded uncertainty' with a covering factor (k) of 2.0, being approximately at 95% confidence level and the ‘standard deviation’ relates the GUM’s ‘standard uncertainty’ (68% confidence level).
When estimating the uncertainty budget of baseline length, both Type A and Type B uncertainties were identified and applied in accordance with GUM and ISO17123-4:2012.
The uncertainty value applies at the time of measurement only and takes no account of any effects that may apply afterwards.
Baseline measurements were performed in accordance with the ISO17123-4:2012 Optics and optical instruments – Field procedures for testing geodetic and surveying instruments – Part 4: Electro-optical distance meters (EDM measurements to reflectors)"""}
    ]

def load_report_notes(apps, schema_editor):
    Company = apps.get_model("accounts", "Company")
    Calibration_Report_Notes = apps.get_model(
        "accounts", "Calibration_Report_Notes")

    for note in notes:
        note_obj, created = Calibration_Report_Notes.objects.get_or_create(
            company = Company.objects.get(company_name__exact='Landgate'),
            report_type = note['report_type'],
            note_type = note['note_type'],
            note = note['note']
            )
    
class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_create_suser')
    ]

    operations = [
        migrations.RunPython(load_report_notes),
    ]
