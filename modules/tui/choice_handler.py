from typing import List

import questionary

from modules.enums import ScannerNames
from modules.tui.input_handler import gather_scan_arguments
from modules.main_runner import run_scans, run_full_name_scan
from modules.sites_manager import sites_manager

async def get_scan_choices() -> List[str]:
    """Prompts the user to select the scans to perform."""
    scan_choices = await questionary.checkbox(
        "Select the scans you want to perform (or select 'All'):",
        choices=[
            "All",
            ScannerNames.USERNAME.value,
            ScannerNames.EMAIL.value,
            ScannerNames.TWITTER_PROFILE.value,
            ScannerNames.DOMAIN_IP.value,
            ScannerNames.PHONE_NUMBER.value,
            ScannerNames.FULL_NAME.value,
        ],
    ).ask_async()
    if not scan_choices:
        return []
    if "All" in scan_choices:
        return [
            ScannerNames.USERNAME.value,
            ScannerNames.EMAIL.value,
            ScannerNames.TWITTER_PROFILE.value,
            ScannerNames.DOMAIN_IP.value,
            ScannerNames.PHONE_NUMBER.value,
            ScannerNames.FULL_NAME.value,
        ]
    return scan_choices

async def handle_main_menu_choice(choice: str):
    """Handles the user's choice from the main menu."""
    if choice == "Start a new scan":
        selected_scans = await get_scan_choices()
        if selected_scans:
            scan_arguments = await gather_scan_arguments(selected_scans)
            if scan_arguments:
                scan_arguments["output"] = "osint_report.json"
                scan_arguments["html"] = "osint_report.html"
                await run_scans(scan_arguments)
    elif choice == ScannerNames.FULL_NAME.value:
        await handle_full_name_scan()
    elif choice == "Update sites.json":
        await sites_manager.update_sites_json_from_url()
    elif choice == "Exit":
        print("Exiting OSINT Tool. Goodbye!")
        return True
    return False

async def handle_full_name_scan():
    """Handles the full name scan option, prompting for name and country."""
    full_name = await questionary.text("Enter the full name (e.g., 'John Doe'):").ask_async()
    if not full_name:
        print("Full name cannot be empty.")
        return

    country = await questionary.text("Enter the country for the search (e.g., 'Sweden', 'USA'):").ask_async()
    if not country:
        print("Country cannot be empty.")
        return

    await run_full_name_scan(full_name, country)