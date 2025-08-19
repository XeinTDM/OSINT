"""
This module defines the enumerations for the OSINT Tool.

It includes enumerations for scanner names, check methods, error types, and
check types. These enumerations are used to define a set of named constants
that can be used throughout the application.

By using enumerations, we can improve the readability and maintainability of
the code, as they provide a clear and concise way to represent a set of
related values.
"""

from enum import Enum


class ScannerNames(Enum):
    """Enum for scanner names."""
    USERNAME = "Username Scan"
    EMAIL = "Email Scan"
    TWITTER_PROFILE = "Twitter Profile Scan"
    DOMAIN_IP = "Domain/IP Analysis"
    PHONE_NUMBER = "Phone Number Analysis"
    FULL_NAME = "Full Name Scan"


class CheckMethods(Enum):
    """Enum for check methods."""
    BASIC = "basic"
    DYNAMIC = "dynamic"


class ErrorTypes(Enum):
    """Enum for error types."""
    STATUS_CODE = "status_code"
    STRING = "string"


class CheckTypes(Enum):
    """Enum for check types."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
