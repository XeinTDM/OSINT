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
from rich.console import Console

def setup_logging(level=logging.INFO, console: Console = None):
    """
    Configures the root logger for the application.

    This function sets up a handler that formats log messages and outputs
    them to the console. It uses the `rich` library to provide a more
    visually appealing and readable log output.

    Args:
        level (int): The minimum logging level to be processed.
                     Defaults to `logging.INFO`.
        console (Console, optional): A Rich Console instance to use for logging.
                                     If None, a default Console will be used.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    handler = RichHandler(
        rich_tracebacks=True,
        console=console,
        show_time=True,
        show_level=True,
        show_path=True,
        enable_link_path=True
    )
    formatter = logging.Formatter(fmt="%(message)s", datefmt="[%X]")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
