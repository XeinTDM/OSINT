"""
This module provides a collection of validator functions that are used to
validate user input in the TUI (Text-based User
Interface).

Each validator is a callable that takes a string as input and returns `True`
if the input is valid, or a `ValidationResult` with an error message if the
input is invalid. These validators are used by the `questionary` library to
provide real-time feedback to the user.

By centralizing the validation logic, we can easily reuse the same validators
across different input prompts and maintain a consistent validation behavior
throughout the application.
"""

import re
import phonenumbers
from phonenumbers import NumberParseException


def validate_username(text: str) -> bool:
    """Validates that the username is not empty."""
    return len(text) > 0


def validate_email(text: str) -> bool:
    """Validates that the email has a valid format."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", text) is not None


def validate_domain_or_ip(text: str) -> bool:
    """Validates that the input is a valid domain or IP address."""
    domain_regex = r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}$"
    ip_regex = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return re.match(domain_regex, text) is not None or re.match(ip_regex, text) is not None


def validate_phone_number(text: str) -> bool:
    """Validates that the input is a valid phone number with a country code."""
    try:
        parsed_number = phonenumbers.parse(text, None)
        return phonenumbers.is_valid_number(parsed_number)
    except NumberParseException:
        return False


def validate_filename(text: str) -> bool:
    """Validates that the filename contains only alphanumeric characters, underscores, and hyphens."""
    return all(c.isalnum() or c in "_-" for c in text)

def validate_full_name(text: str) -> bool:
    """Validates that the full name is not empty."""
    return len(text) > 0

def validate_country(text: str) -> bool:
    """Validates that the country is not empty."""
    return len(text) > 0