import logging
from typing import Dict, Any


from playwright.async_api import async_playwright
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from modules import report_generator, config
from modules.core.scan_manager import ScanManager
from modules.username_scanner import UsernameScanner
from modules.email_scanner import EmailScanner
from modules.social_media_scanner import SocialMediaScanner
from modules.domain_ip_scanner import DomainIPScanner
from modules.phone_scanner import PhoneScanner
from modules.full_name_scanner import FullNameScanner
from modules.enums import ScannerNames
from modules.logging_config import setup_logging

logger = logging.getLogger(__name__)

async def run_scans(args: Dict[str, Any]):
    """Main function to orchestrate the OSINT scan based on selected options."""
    scan_context: Dict[str, Any] = {"osint_keywords": {}}
    if args.get("username"):
        scan_context["_target_input"] = args["username"]
    elif args.get("email"):
        scan_context["_target_input"] = args["email"]
    elif args.get("twitter_username"):
        scan_context["_target_input"] = args["twitter_username"]
    elif args.get("domain_or_ip"):
        scan_context["_target_input"] = args["domain_or_ip"]
    elif args.get("phone_number"):
        scan_context["_target_input"] = args["phone_number"]

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
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TimeRemainingColumn(),
                transient=True,
            ) as progress:
                setup_logging(console=progress.console)
                scan_manager = ScanManager(progress, browser)

                if ScannerNames.USERNAME.value in args["selected_scans"] and args.get("username"):
                    username_args = args.copy()
                    username_args.pop("username", None)
                    await scan_manager.run_scanner(UsernameScanner, args["username"], scan_context, username_args)

                if ScannerNames.EMAIL.value in args["selected_scans"] and args.get("email"):
                    email_args = args.copy()
                    email_args.pop("email", None)
                    await scan_manager.run_scanner(EmailScanner, args["email"], scan_context, email_args)

                if ScannerNames.TWITTER_PROFILE.value in args["selected_scans"] and args.get("twitter_username"):
                    twitter_args = args.copy()
                    twitter_args.pop("twitter_username", None)
                    await scan_manager.run_scanner(SocialMediaScanner, args["twitter_username"], scan_context, twitter_args)

                if ScannerNames.DOMAIN_IP.value in args["selected_scans"] and args.get("domain_or_ip"):
                    domain_ip_args = args.copy()
                    domain_ip_args.pop("domain_or_ip", None)
                    await scan_manager.run_scanner(DomainIPScanner, args["domain_or_ip"], scan_context, domain_ip_args)

                if ScannerNames.PHONE_NUMBER.value in args["selected_scans"] and args.get("phone_number"):
                    phone_number_args = args.copy()
                    phone_number_args.pop("phone_number", None)
                    await scan_manager.run_scanner(PhoneScanner, args["phone_number"], scan_context, phone_number_args)

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
    scan_context["_target_input"] = full_name
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            with Progress(
                SpinnerColumn(),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TimeRemainingColumn(),
                transient=True,
            ) as progress:
                scan_manager = ScanManager(progress, browser)
                await scan_manager.run_scanner(FullNameScanner, full_name, scan_context, {"country": country})

            print("\n" + "=" * 50)
            print("           FULL NAME SCAN COMPLETE - REPORT")
            print("=" * 50 + "\n")
            report_generator.generate_cli_report(scan_context)

    except Exception as e:
        logger.error(f"An error occurred during the full name scan: {e}", exc_info=True)
    finally:
        if browser:
            await browser.close()
