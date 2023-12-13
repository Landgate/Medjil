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
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib import messages

from profanity_check import predict_prob

def validate_profanity(value):
    """
    Custom validator to check for profanity in the input value.
    """
    if predict_prob([value])[0] > 0.8:
        raise ValidationError("Profanity is not allowed in this field.")


def try_delete_protected(request, delete_obj):
    try:
        delete_obj.delete()
        messages.success(
            request, "You have successfully deleted: " + f"{delete_obj} <br>Please note that the deleted record cannot be retrieved.")
    except ObjectDoesNotExist:
        messages.warning(request, "No record to delete.")
    except ProtectedError as e:
        related_models = set([obj.__class__ for obj in e.protected_objects])
        related_records = [obj for obj in e.protected_objects]
        html = ""
        for model in related_models:
            html += "<ul>"
            html += f"<li>Table: { model._meta.verbose_name }</li>"
            html += "<ul>"
            for record in related_records:
                if model == record.__class__:
                    html += f"<li>Record: { record }</li>"
            html += "</ul>"
            html += "</ul>"
        
        error_message = (
            "This action cannot be performed as dependent records must be deleted first: "
            + html
        )
        messages.error(request, error_message)
    

def validate_csv_text(value):
    numbers = value.split(',')
    for num in numbers:
        try:
            float_num = float(num.strip())
        except ValueError:
            raise ValidationError(f'{num} is not a valid number.')
