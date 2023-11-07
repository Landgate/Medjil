'''

   © 2023 Western Australian Land Information Authority

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
# common/validators.py
from django.apps import apps
from django.db.models import ForeignKey
from django.db import models
from django.core.exceptions import ValidationError

from profanity_check import predict_prob

def validate_profanity(value):
    """
    Custom validator to check for profanity in the input value.
    """
    if predict_prob([value])[0] > 0.8:
        raise ValidationError("Profanity is not allowed in this field.")


def afind_dependent_models(parent_app_name, parent_model_name):
    # Get the 'Uncertainty_Budget' model
    parent_model = apps.get_model(parent_app_name, parent_model_name)

    # Initialize dictionaries to store models with protected and cascade foreign keys and their dependent records
    dependent_models = {'protected': {}, 'cascade': {}}

    # Find all models with a ForeignKey relationship to 'Uncertainty_Budget'
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, ForeignKey) and field.remote_field.model == parent_model:
                model_name = model._meta.model_name
                print(model_name)
                # Get the value of the parent_model's ForeignKey field
                parent_model_fk_value = getattr(parent_model, field.name)
                dependent_records = model.objects.filter(**{field.name: parent_model_fk_value})
                print(dependent_records)
                if dependent_records:
                    print('************************************************************')
                    print(model_name)
                    print(dependent_models['protected'])
                    if field.remote_field.on_delete == models.PROTECT:
                        print('***************************Protected stuff')
                        if model_name not in dependent_models['protected']:
                            dependent_models['protected'][model_name] = []
                        # Find dependent records and add to the dictionary under the model's name
                        dependent_models['protected'][model_name].extend(dependent_records)
                        
                    elif field.remote_field.on_delete == models.CASCADE:
                        if model_name not in dependent_models['cascade']:
                            dependent_models['cascade'][model_name] = []
                        # Find dependent records and add to the dictionary under the model's name
                        dependent_models['cascade'][model_name].extend(dependent_records)

    return dependent_models


def find_dependent_records(parent_record):
    # Initialize dictionaries to store models with protected and cascade foreign keys and their dependent records
    dependent_records = {'protected': {}, 'protected_html': "", 
                         'cascade': {}, 'cascade_html': ""}

    # Find all models with a ForeignKey relationship to the parent record
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, ForeignKey) and field.remote_field.model == parent_record.__class__:
                model_name = model._meta.model_name
                # Get the value of the ForeignKey field in the parent record
                dependent_records_query = model.objects.filter(**{field.name: parent_record})
                if dependent_records_query:
                    if field.remote_field.on_delete == models.PROTECT:
                        if model_name not in dependent_records['protected']:
                            dependent_records['protected'][model_name] = []
                        # Find dependent records and add to the dictionary under the model's name
                        dependent_records['protected'][model_name].extend(dependent_records_query)
                        dependent_records['protected_html'] += (
                            dependent_records_msg(model_name, dependent_records_query))
                        
                    elif field.remote_field.on_delete == models.CASCADE:
                        if model_name not in dependent_records['cascade']:
                            dependent_records['cascade'][model_name] = []
                        # Find dependent records and add to the dictionary under the model's name
                        dependent_records['cascade'][model_name].extend(dependent_records_query)
                        dependent_records['cascade_html'] += (
                            dependent_records_msg(model_name, dependent_records_query))

    return dependent_records


def dependent_records_msg(model_name, dependent_records):
    html = "<ul>"
    html += f"<li>Model: {model_name }</li>"
    html += "<ul>"
    for record in dependent_records:
        html += f"<li>Record: { record }</li>"
    html += "</ul>"
    html += "</ul>"
     
    return html




