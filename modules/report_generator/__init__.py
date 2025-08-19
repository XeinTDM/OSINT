"""
This package provides modules for generating reports in various formats.

It includes the following modules:
    - `cli_reporter`: Generates a report for the command-line interface.
    - `json_reporter`: Generates a report in JSON format.
    - `html_reporter`: Generates a report in HTML format.

The `__init__.py` file exposes the public functions from these modules so
that they can be easily imported and used by other parts of the application.
"""

from .cli_reporter import generate_cli_report
from .json_reporter import save_json_report
from .html_reporter import save_html_report

__all__ = [
    "generate_cli_report",
    "save_json_report",
    "save_html_report",
]
