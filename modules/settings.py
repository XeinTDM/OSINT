"""
This module defines the settings for the OSINT Tool.

It includes settings for concurrency limits and the user agent to be used
for web requests. These settings can be easily adjusted to control the
behavior of the tool.

By centralizing these settings, we can easily manage and update them without
having to modify the core application logic.
"""

# Concurrency Limits
BASIC_CHECK_CONCURRENCY = 30
DYNAMIC_CHECK_CONCURRENCY = 8

# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
