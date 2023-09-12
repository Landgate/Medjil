# common/validators.py
from django.core.exceptions import ValidationError
from profanity_check import predict

def validate_profanity(value):
    """
    Custom validator to check for profanity in the input value.
    """
    if predict([value])[0] == 1:
        raise ValidationError("Profanity is not allowed in this field.")
