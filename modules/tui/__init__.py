"""
This package provides modules for creating the text-based user interface (TUI)
for the OSINT Tool.

It includes the following modules:
    - `menu`: The main menu of the TUI.
    - `validators`: A collection of input validators.
    - `input_handler`: Handles user input.
    - `choice_handler`: Handles scan choices.

The `__init__.py` file exposes the public functions from these modules so
that they can be easily imported and used by other parts of the application.
"""

from .choice_handler import get_scan_choices
from .input_handler import gather_scan_arguments
from .menu import get_main_menu_choice

__all__ = [
    "get_scan_choices",
    "gather_scan_arguments",
    "get_main_menu_choice",
]