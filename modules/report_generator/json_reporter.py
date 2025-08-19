"""
This module is responsible for generating the JSON report for the OSINT Tool.

It provides a simple function to save the scan results to a JSON file, which
can be easily parsed by other tools or used for data analysis.

Key functionalities include:
    - Serializing the scan results dictionary to a JSON formatted string.
    - Saving the JSON string to a file with a user-specified name.
    - Handling potential file I/O errors gracefully.

By separating the JSON reporting logic, we can ensure that the output format
is consistent and can be easily updated without affecting other parts of the
application.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def save_json_report(results: Dict[str, Any], filename: str):
    """Saves the full results dictionary to a JSON file."""
    logger.info(f"Saving JSON report to {filename}...")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, default=str)
        logger.info(f"JSON report saved successfully to {filename}")
    except IOError as e:
        logger.error(f"Error saving JSON report to {filename}: {e}")
