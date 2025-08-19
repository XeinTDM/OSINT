"""
This module defines the API keys for the OSINT Tool.

It retrieves the API keys from the environment variables, so they are not
hard-coded in the source code. This improves the security of the tool and
makes it easier to manage the API keys.

By centralizing the API key management, we can easily add or remove API
keys without having to modify the core application logic.
"""

import os

HIBP_API_KEY = os.getenv("HIBP_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
