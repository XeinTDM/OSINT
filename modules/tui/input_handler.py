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

async def gather_full_name_arguments() -> Dict[str, Any]:
    """Gathers arguments for a full name scan."""
    args: Dict[str, Any] = {}

    args["full_name"] = await questionary.text(
        "Enter the full name to scan (e.g., John Doe, or John A. Doe):",
        validate=validators.validate_full_name
    ).ask_async()

    if await questionary.confirm("Do you want to provide first, middle, and last names separately?").ask_async():
        args["first_name"] = await questionary.text("Enter first name (optional):").ask_async()
        args["middle_name"] = await questionary.text("Enter middle name (optional):").ask_async()
        args["last_name"] = await questionary.text("Enter last name (optional):").ask_async()

    if await questionary.confirm("Do you want to provide any aliases or maiden names?").ask_async():
        aliases_input = await questionary.text(
            "Enter aliases or maiden names, separated by commas (e.g., Jane Smith, J. Doe):"
        ).ask_async()
        if aliases_input:
            args["aliases"] = [alias.strip() for alias in aliases_input.split(',')]
        else:
            args["aliases"] = []
    else:
        args["aliases"] = []

    args["country"] = await questionary.text(
        "Enter the country for the scan (e.g., Sweden, US):",
        validate=validators.validate_country
    ).ask_async()

    return args