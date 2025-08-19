import asyncio
import logging
from dotenv import load_dotenv
import questionary

from modules.logging_config import setup_logging
from modules.tui.menu import get_main_menu_choice
from modules.tui.choice_handler import handle_main_menu_choice
from modules.sites_manager import sites_manager
from modules.utils import print_banner

load_dotenv()
setup_logging()

logger = logging.getLogger(__name__)

async def main_menu():
    """Displays the main menu and handles user choices."""
    while True:
        choice = await get_main_menu_choice()

        should_exit = await handle_main_menu_choice(choice)
        if should_exit:
            break

        await questionary.press_any_key_to_continue(
            "Press any key to return to the main menu."
        ).ask_async()

def main():
    """Main entry point for the OSINT Tool."""
    try:
        asyncio.run(sites_manager.ensure_sites_json_exists())
        print_banner()
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()

