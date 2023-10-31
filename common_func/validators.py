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
from django.core.exceptions import ValidationError
from profanity_check import predict_prob

def validate_profanity(value):
    """
    Custom validator to check for profanity in the input value.
    """
    if predict_prob([value])[0] > 0.8:
        raise ValidationError("Profanity is not allowed in this field.")
