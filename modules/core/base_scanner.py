from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from rich.progress import Progress
from playwright.async_api import Browser
from modules.core.errors import NetworkError, APIError, ParsingError, RateLimitError, AuthenticationError

class BaseScanner(ABC):
    """Abstract base class for all OSINT scanners."""

    def __init__(self, progress: Progress, task_id, browser: Optional[Browser] = None):
        self.progress = progress
        self.task_id = task_id
        self.browser = browser

    @abstractmethod
    async def scan(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        Abstract method to perform the scan.

        Args:
            target: The primary target for the scan (e.g., username, email, domain).
            **kwargs: Additional arguments required for the specific scan (e.g., API keys, sites list).

        Returns:
            A dictionary containing the scan results.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the scanner."""
        pass
