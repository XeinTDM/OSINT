"""
This module is responsible for handling user input in the TUI (Text-based User
Interface). It provides functions to gather the necessary arguments for the
selected scans, such as usernames, email addresses, and API keys.

Key functionalities include:
    - Prompting the user for input using the `questionary` library.
    - Validating the user input using the validators from the `validators` module.
    - Retrieving API keys from environment variables or prompting the user if they
      are not found.

By separating the input handling logic, we can keep the main menu module clean
and focused on the overall flow of the user interface.
"""

import os
from typing import Dict, Any, Optional, List

import questionary

from modules.tui import validators


async def get_api_key(env_var: str, prompt: str) -> Optional[str]:
    """Gets an API key from environment variables or prompts the user."""
    api_key = os.getenv(env_var)
    if not api_key:
        if await questionary.confirm(f"Do you have a {prompt}?").ask_async():
            api_key = await questionary.password(f"Enter {prompt}:").ask_async()
    return api_key


async def gather_scan_arguments(scan_choices: List[str]) -> Dict[str, Any]:
    """Gathers the necessary arguments for the selected scans."""
    args: Dict[str, Any] = {choice: None for choice in scan_choices}

    if "Username Scan" in scan_choices or "Twitter Profile Scan" in scan_choices:
        args["username"] = await questionary.text(
            "Enter the username to scan:",
            validate=validators.validate_username
        ).ask_async()

    if "Email Scan" in scan_choices:
        args["email"] = await questionary.text(
            "Enter the email to scan:",
            validate=validators.validate_email
        ).ask_async()
        args["hibp_key"] = await get_api_key("HIBP_API_KEY", "Have I Been Pwned API key")

    if "Twitter Profile Scan" in scan_choices:
        args["twitter_bearer_token"] = await get_api_key("TWITTER_BEARER_TOKEN", "Twitter Bearer Token")

    if "Domain/IP Analysis" in scan_choices:
        args["domain_or_ip"] = await questionary.text(
            "Enter the domain or IP address to analyze:",
            validate=validators.validate_domain_or_ip
        ).ask_async()

    if "Phone Number Analysis" in scan_choices:
        args["phone_number"] = await questionary.text(
            "Enter the phone number to analyze (with country code):",
            validate=validators.validate_phone_number
        ).ask_async()

    return args
