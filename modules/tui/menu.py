"""
This module provides the main menu for the OSINT Tool's TUI (Text-based User
Interface). It orchestrates the user interaction, allowing them to choose
scans, update data, and exit the application.

Key functionalities include:
    - Displaying the main menu options.
    - Handling user selections and dispatching the corresponding actions.
    - Integrating with other TUI modules to gather input and run scans.

This module is the central hub of the TUI, and it is designed to be easily
extensible with new options and functionalities.
"""

import logging

import questionary



logger = logging.getLogger(__name__)

async def get_main_menu_choice():
    """Displays the main menu and returns the user's choice."""
    choice = await questionary.select(
        "What would you like to do?",
        choices=["Start a new scan", "Full Name Scan", "Update sites.json", "Exit"],
        qmark=">"
    ).ask_async()
    return choice