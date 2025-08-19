from typing import Dict, Any

from playwright.async_api import Browser

from modules.core.scan_manager import ScanManager


async def run_scans(args: Dict[str, Any], scan_context: Dict[str, Any], browser: Browser, sites: list):
    """Gathers and runs the selected scans using the new modular architecture."""
    scan_manager = ScanManager(args, browser, sites)
    results = await scan_manager.run_scans()
    scan_context.update(results)
