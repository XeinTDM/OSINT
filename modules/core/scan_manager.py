import logging
from typing import Dict, Any, Type

from playwright.async_api import Browser
from rich.progress import Progress

from modules.core.base_scanner import BaseScanner
from modules.core.exceptions import ScannerError

logger = logging.getLogger(__name__)

class ScanManager:
    """Manages the orchestration of individual OSINT scanners."""

    def __init__(self, progress: Progress, browser: Browser):
        self.progress = progress
        self.browser = browser

    async def run_scanner(self, ScannerClass: Type[BaseScanner], target: str, scan_context: Dict[str, Any], kwargs: Dict[str, Any] = None):
        """
        Runs a specific scanner class.

        Args:
            ScannerClass: The class of the scanner to run (e.g., UsernameScanner, FullNameScanner).
            target: The primary target for the scan (e.g., username, full name).
            scan_context: The dictionary to store scan results.
            kwargs: Additional arguments for the scanner's scan method.
        """
        if kwargs is None:
            kwargs = {}

        scanner_name = ScannerClass.NAME
        task_id = self.progress.add_task(f"[cyan]Scanning {scanner_name} for {target}...[/cyan]", total=1)

        try:
            scanner_instance = ScannerClass(self.progress, task_id, self.browser)
            result = await scanner_instance.scan(target, **kwargs)
            
            context_key = scanner_name.lower().replace(" ", "_")
            scan_context[context_key] = result
            if "osint_keywords" in result:
                scan_context["osint_keywords"].update(result["osint_keywords"])

            self.progress.update(task_id, description=f"[green]Finished {scanner_name} for {target}.[/green]", completed=1)
        except ScannerError as e:
            logger.error(f"Error in {scanner_name} for {target}: {e}")
            self.progress.update(task_id, description=f"[red]Error in {scanner_name} for {target}.[/red]", completed=1)
            scan_context[ScannerClass.NAME.lower().replace(" ", "_")] = {"error": str(e)}
        except Exception as e:
            logger.error(f"An unexpected error occurred in {scanner_name} for {target}: {e}", exc_info=True)
            self.progress.update(task_id, description=f"[red]Unexpected error in {scanner_name} for {target}.[/red]", completed=1)
            scan_context[ScannerClass.NAME.lower().replace(" ", "_")] = {"error": "An unexpected error occurred."}