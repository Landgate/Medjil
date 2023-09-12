# common/validators.py
from django.core.exceptions import ValidationError
from profanity_check import predict_prob

def validate_profanity(value):
    """
    Custom validator to check for profanity in the input value.
    """
    if predict_prob([value])[0] > 0.8:
        raise ValidationError("Profanity is not allowed in this field.")
