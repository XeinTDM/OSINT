"""
This module defines the paths for the OSINT Tool.

It includes the path to the `sites.json` file, which is used for the
username scanning functionality. By centralizing the paths, we can easily
manage and update them without having to modify the core application logic.
"""

import os

SITES_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sites.json")
FULL_NAME_SITES_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "full_name_sites.json")
DEFAULT_FULL_NAME_SITES_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "default_full_name_sites.json")
