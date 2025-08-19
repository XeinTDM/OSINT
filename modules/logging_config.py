"""
This module provides a centralized logging configuration for the OSINT Tool.

It configures a logger that outputs messages to the console with a specific
format, including a timestamp, log level, and the message itself. The log
level can be easily adjusted to control the verbosity of the output.

Usage:
    - Import the `setup_logging` function from this module.
    - Call `setup_logging()` at the beginning of the main application script.
    - Use the standard `logging.getLogger(__name__)` to get a logger instance
      in any module.
"""

import logging
from rich.logging import RichHandler

def setup_logging(level=logging.INFO):
    """
    Configures the root logger for the application.

    This function sets up a handler that formats log messages and outputs
    them to the console. It uses the `rich` library to provide a more
    visually appealing and readable log output.

    Args:
        level (int): The minimum logging level to be processed.
                     Defaults to `logging.INFO`.
    """
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
