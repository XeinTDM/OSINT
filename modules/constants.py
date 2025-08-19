"""
This module defines the constants for the OSINT Tool.

It includes constants for the scanner names, check methods, error types, and
check types. These constants are used throughout the application to ensure
consistency and avoid magic strings.

By centralizing the constants, we can easily manage and update them without
having to modify the core application logic.
"""

from .enums import CheckMethods, CheckTypes, ErrorTypes, ScannerNames
from .strings import (
    DOMAIN_IP_ANALYSIS,
    EMAIL_SCAN,
    PHONE_NUMBER_ANALYSIS,
    TWITTER_PROFILE_SCAN,
    USERNAME_SCAN,
)

__all__ = [
    "CheckMethods",
    "CheckTypes",
    "ErrorTypes",
    "ScannerNames",
    "DOMAIN_IP_ANALYSIS",
    "EMAIL_SCAN",
    "PHONE_NUMBER_ANALYSIS",
    "TWITTER_PROFILE_SCAN",
    "USERNAME_SCAN",
]

FULL_NAME_SITES_URL = "https://raw.githubusercontent.com/XeinTDM/OSINT/main/data/full_name_sites.json"
