import logging
from typing import Dict, Any

import questionary
from playwright.async_api import async_playwright

from modules import report_generator, config
from modules.core import scanner
from modules.tui import menu

logger = logging.getLogger(__name__)

async def run_new_scan(sites_data: list):
    """Runs the interactive TUI to gather scan options."""
    scan_choices = await menu.get_scan_choices()
    if not scan_choices:
        logger.info("No scans selected.")
        return

    args = await menu.gather_scan_arguments(scan_choices)

    output_filename_base = await questionary.text(
        "Enter the base name for the report files:", default="osint_report",
        validate=lambda text: True if text and all(c.isalnum() or c in "_-" for c in text) else "Filename can only contain alphanumeric characters, underscores, and hyphens."
    ).ask_async()
    args["output"] = f"{output_filename_base}.json"
    args["html"] = f"{output_filename_base}.html"

    await main_scan_logic(args, sites_data)


async def main_scan_logic(args: Dict[str, Any], sites_data: list):
    """Main function to orchestrate the OSINT scan."""
    scan_context: Dict[str, Any] = {"osint_keywords": {}}
    if args.get("username"):
        scan_context["target_username"] = args["username"]
    if args.get("email"):
        scan_context["target_email"] = args["email"]
    if args.get("domain_or_ip"):
        scan_context["target_domain_or_ip"] = args["domain_or_ip"]
    if args.get("phone_number"):
        scan_context["target_phone_number"] = args["phone_number"]

    # Add API keys from config if not already present in args
    if "hibp_key" not in args and config.Config.HIBP_API_KEY:
        args["hibp_key"] = config.Config.HIBP_API_KEY
    if "twitter_bearer_token" not in args and config.Config.TWITTER_BEARER_TOKEN:
        args["twitter_bearer_token"] = config.Config.TWITTER_BEARER_TOKEN

    browser = None
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
            await scanner.run_scans(args, scan_context, browser, sites_data)
        except Exception as e:
            logger.error(f"Error launching Playwright browser: {e}")
            return
        finally:
            if browser:
                await browser.close()

    print("\n" + "=" * 50)
    print("           OSINT SCAN COMPLETE - REPORT")
    print("=" * 50 + "\n")
    report_generator.generate_cli_report(scan_context)
    if args.get("output"):
        report_generator.save_json_report(scan_context, args["output"])
    if args.get("html"):
        report_generator.save_html_report(scan_context, args["html"])
