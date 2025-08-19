import logging
from typing import Dict, Any

import questionary
from playwright.async_api import async_playwright
from rich.progress import Progress, SpinnerColumn, TextColumn

from modules import report_generator, config
from modules.core.scan_manager import ScanManager
from modules.username_scanner import UsernameScanner
from modules.email_scanner import EmailScanner
from modules.social_media_scanner import SocialMediaScanner
from modules.domain_ip_scanner import DomainIPScanner
from modules.phone_scanner import PhoneScanner
from modules.full_name_scanner import FullNameScanner
from modules.enums import ScannerNames

logger = logging.getLogger(__name__)

async def run_scans(args: Dict[str, Any]):
    """Main function to orchestrate the OSINT scan based on selected options."""
    scan_context: Dict[str, Any] = {"osint_keywords": {}}

    # Add API keys from config if not already present in args
    if "hibp_key" not in args and config.Config.HIBP_API_KEY:
        args["hibp_key"] = config.Config.HIBP_API_KEY
    if "twitter_bearer_token" not in args and config.Config.TWITTER_BEARER_TOKEN:
        args["twitter_bearer_token"] = config.Config.TWITTER_BEARER_TOKEN

    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                scan_manager = ScanManager(progress, browser)

                if ScannerNames.USERNAME.value in args["selected_scans"] and args.get("username"):
                    await scan_manager.run_scanner(UsernameScanner, args["username"], scan_context, args)

                if ScannerNames.EMAIL.value in args["selected_scans"] and args.get("email"):
                    await scan_manager.run_scanner(EmailScanner, args["email"], scan_context, args)

                if ScannerNames.TWITTER_PROFILE.value in args["selected_scans"] and args.get("twitter_username"):
                    await scan_manager.run_scanner(SocialMediaScanner, args["twitter_username"], scan_context, args)

                if ScannerNames.DOMAIN_IP.value in args["selected_scans"] and args.get("domain_or_ip"):
                    await scan_manager.run_scanner(DomainIPScanner, args["domain_or_ip"], scan_context, args)

                if ScannerNames.PHONE_NUMBER.value in args["selected_scans"] and args.get("phone_number"):
                    await scan_manager.run_scanner(PhoneScanner, args["phone_number"], scan_context, args)

            print("\n" + "=" * 50)
            print("           OSINT SCAN COMPLETE - REPORT")
            print("=" * 50 + "\n")
            report_generator.generate_cli_report(scan_context)
            if args.get("output"):
                report_generator.save_json_report(scan_context, args["output"])
            if args.get("html"):
                report_generator.save_html_report(scan_context, args["html"])

    except Exception as e:
        logger.error(f"An error occurred during the scan: {e}", exc_info=True)
    finally:
        if browser:
            await browser.close()

async def run_full_name_scan(full_name: str, country: str):
    """Runs a dedicated full name OSINT scan."""
    scan_context: Dict[str, Any] = {"osint_keywords": {}}
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                scan_manager = ScanManager(progress, browser)
                await scan_manager.run_scanner(FullNameScanner, full_name, scan_context, {"country": country})

            print("\n" + "=" * 50)
            print("           FULL NAME SCAN COMPLETE - REPORT")
            print("=" * 50 + "\n")
            report_generator.generate_cli_report(scan_context)
            # For full name scan, we might want to save a specific report format
            # For now, just CLI report.

    except Exception as e:
        logger.error(f"An error occurred during the full name scan: {e}", exc_info=True)
    finally:
        if browser:
            await browser.close()
