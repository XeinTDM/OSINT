"""
This module is responsible for generating the command-line interface (CLI)
report for the OSINT Tool. It uses the `rich` library to create a visually
appealing and easy-to-read report that is displayed in the console.

Key functionalities include:
    - Creating a structured tree view of the scan results.
    - Formatting the results for each type of scan (username, email, etc.).
    - Handling and displaying errors that may have occurred during the scans.
    - Customizing the output with colors, styles, and panels to improve
      readability.

By separating the CLI reporting logic, we can easily modify the console
output without affecting other report formats like HTML or JSON.
"""

from typing import Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from modules import constants
from modules.core.errors import (
    APIError,
    AuthenticationError,
    NetworkError,
    ParsingError,
    RateLimitError
)
from modules.core.exceptions import ScannerError

console = Console(record=True)


def _add_username_results(tree: Tree, results: Dict[str, Any]):
    if constants.USERNAME_SCAN.lower().replace(" ", "_") not in results:
        return

    scan_results = results[constants.USERNAME_SCAN.lower().replace(" ", "_")]
    user_tree = tree.add("[bold green]👤 Username Scan Results[/bold green]")

    if "error" in scan_results:
        error_obj = scan_results["error"]
        error_message = "An unknown error occurred."
        if isinstance(error_obj, NetworkError):
            error_message = f"Network Error: {error_obj.args[0]}. Please check your internet connection."
        elif isinstance(error_obj, ParsingError):
            error_message = f"Data Parsing Error: {error_obj.args[0]}. The site's response could not be understood."
        elif isinstance(error_obj, APIError):
            error_message = f"API Error: {error_obj.args[0]}. There was an issue with the API."
        elif isinstance(error_obj, RateLimitError):
            error_message = f"Rate Limit Exceeded: {error_obj.args[0]}. Please try again later."
        elif isinstance(error_obj, AuthenticationError):
            error_message = f"Authentication Error: {error_obj.args[0]}. Please check your API key."
        elif isinstance(error_obj, ScannerError):
            error_message = f"Scan Error: {error_obj.args[0]}"
        else:
            error_message = f"Unexpected Error: {error_obj}"

        user_tree.add(f"[bold red]Error: {error_message}[/bold red]")
        if hasattr(error_obj, 'original_exception') and error_obj.original_exception:
            user_tree.add(f"[red]  Original Exception: {type(error_obj.original_exception).__name__} - {error_obj.original_exception}[/red]")
        return

    found_sites = scan_results.get("found", [])
    if found_sites:
        for site in found_sites:
            user_tree.add(f"✔ Found on {site['name']}: {site['url']}")
    else:
        user_tree.add("[yellow]No accounts found on checked sites.[/yellow]")

    if "errors" in scan_results and scan_results["errors"]:
        error_subtree = user_tree.add("[bold red]Errors during scan:[/bold red]")
        for err in scan_results["errors"]:
            error_subtree.add(f"[red]- {err}[/red]")


def _add_email_results(tree: Tree, results: Dict[str, Any]):
    if constants.EMAIL_SCAN.lower().replace(" ", "_") not in results:
        return

    email_tree = tree.add(f"[bold green]📧 Email Scan Results for: {results['target_email']}[/bold green]")
    breaches = results[constants.EMAIL_SCAN.lower().replace(" ", "_")].get("breaches", {})

    if "error" in results[constants.EMAIL_SCAN.lower().replace(" ", "_")]:
        error_obj = results[constants.EMAIL_SCAN.lower().replace(" ", "_")]["error"]
        error_message = "An unknown error occurred."
        if isinstance(error_obj, NetworkError):
            error_message = f"Network Error: {error_obj.args[0]}. Please check your internet connection."
        elif isinstance(error_obj, ParsingError):
            error_message = f"Data Parsing Error: {error_obj.args[0]}. The API response could not be understood."
        elif isinstance(error_obj, APIError):
            error_message = f"API Error: {error_obj.args[0]}. There was an issue with the HIBP API."
        elif isinstance(error_obj, RateLimitError):
            error_message = f"Rate Limit Exceeded: {error_obj.args[0]}. Please try again later."
        elif isinstance(error_obj, AuthenticationError):
            error_message = f"Authentication Error: {error_obj.args[0]}. Please check your HIBP API key."
        elif isinstance(error_obj, ScannerError):
            error_message = f"Scan Error: {error_obj.args[0]}"
        else:
            error_message = f"Unexpected Error: {error_obj}"

        email_tree.add(f"[yellow]⚠️ Breach Check Failed: {error_message}[/yellow]")
        if hasattr(error_obj, 'original_exception') and error_obj.original_exception:
            email_tree.add(f"[red]  Original Exception: {type(error_obj.original_exception).__name__} - {error_obj.original_exception}[/red]")
    elif breaches.get("breached"):
        breach_tree = email_tree.add(f"[bold red]🚨 Found in {breaches['count']} breaches![/bold red]")
        for breach in breaches["breaches"][:10]:
            breach_tree.add(f"[red]- {breach}[/red]")
        if len(breaches["breaches"]) > 10:
            breach_tree.add(f"[red]...and {len(breaches['breaches']) - 10} more.[/red]")
    else:
        email_tree.add("[green]✅ No breaches found in HIBP database.[/green]")


def _add_twitter_results(tree: Tree, results: Dict[str, Any]):
    if constants.TWITTER_PROFILE_SCAN.lower().replace(" ", "_") not in results:
        return

    twitter_data = results[constants.TWITTER_PROFILE_SCAN.lower().replace(" ", "_")]
    twitter_tree = tree.add("[bold blue]🐦 Twitter Scan Results[/bold blue]")

    if "error" in twitter_data:
        error_obj = twitter_data["error"]
        error_message = "An unknown error occurred."
        if isinstance(error_obj, NetworkError):
            error_message = f"Network Error: {error_obj.args[0]}. Please check your internet connection."
        elif isinstance(error_obj, ParsingError):
            error_message = f"Data Parsing Error: {error_obj.args[0]}. The API response could not be understood."
        elif isinstance(error_obj, APIError):
            error_message = f"API Error: {error_obj.args[0]}. There was an issue with the Twitter API."
        elif isinstance(error_obj, RateLimitError):
            error_message = f"Rate Limit Exceeded: {error_obj.args[0]}. Please try again later."
        elif isinstance(error_obj, AuthenticationError):
            error_message = f"Authentication Error: {error_obj.args[0]}. Please check your Twitter Bearer Token."
        elif isinstance(error_obj, ScannerError):
            error_message = f"Scan Error: {error_obj.args[0]}"
        else:
            error_message = f"Unexpected Error: {error_obj}"

        twitter_tree.add(f"[yellow]⚠️ {error_message}[/yellow]")
        if hasattr(error_obj, 'original_exception') and error_obj.original_exception:
            twitter_tree.add(f"[red]  Original Exception: {type(error_obj.original_exception).__name__} - {error_obj.original_exception}[/red]")
        return

    if not twitter_data.get("found"):
        twitter_tree.add("[green]✅ No public Twitter profile found.[/green]")
        return

    panel_content = f"[bold]{twitter_data['name']}[/bold] (@{twitter_data['username']})\n"
    panel_content += f"[dim]{twitter_data['description']}[/dim]\n\n"
    panel_content += f"[b]Verified:[/b] {'Yes' if twitter_data['verified'] else 'No'}\n"
    panel_content += f"[b]Location:[/b] {twitter_data.get('location', 'N/A')}\n"
    panel_content += f"[b]Joined:[/b] {twitter_data['created_at']}\n"

    table = Table(show_header=False, box=None)
    table.add_row("Followers", str(twitter_data["followers"]))
    table.add_row("Following", str(twitter_data["following"]))
    table.add_row("Tweets", str(twitter_data["tweet_count"]))

    twitter_tree.add(Panel(panel_content, title="Profile Info", border_style="blue"))
    twitter_tree.add(table)
    twitter_tree.add(f"[link=https://twitter.com/{twitter_data['username']}]View Profile[/link]")


def generate_cli_report(results: Dict[str, Any]):
    """
    Generates and prints the CLI report.

    Args:
        results (Dict[str, Any]): The OSINT scan results.
    """
    report_title = f"OSINT Report for: {results.get('target', 'N/A')}"
    console.print(Panel(report_title, style="bold magenta", expand=False))

    main_tree = Tree("Scan Results")

    _add_username_results(main_tree, results)
    _add_email_results(main_tree, results)
    _add_twitter_results(main_tree, results)

    console.print(main_tree)
