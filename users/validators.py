import re
from django.core.exceptions import ValidationError


def validate_special_character(value):
    # This is a custom validator that adds aditional layer of complexity to ensure passwords
    # includes characters beyond alpha numeric ones
    pattern = r'[\W_]+'
    if not re.search(pattern, value):
        raise ValidationError('Password must contain at least one special character eg."~!@#$%^&*"')