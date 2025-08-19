import aiohttp
import asyncio
import logging
from playwright.async_api import Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from rich.progress import Progress
from typing import Dict, List, Any, Coroutine
from modules import config
from modules.core.base_scanner import BaseScanner
from modules.core.exceptions import ScannerError
from modules.core.errors import NetworkError
from modules.sites_manager import SitesManager
from modules.enums import CheckMethods, ErrorTypes, CheckTypes

logger = logging.getLogger(__name__)

class UsernameScanner(BaseScanner):
    def __init__(self, progress: Progress, task_id, browser: Browser):
        super().__init__(progress, task_id, browser)
        self.sites_manager = SitesManager()

    @property
    def name(self) -> str:
        return "Username Scan"

    async def scan(self, username: str, **kwargs) -> Dict[str, Any]:
        """
        Orchestrates the scanning of a username across multiple sites.
        Reuses the provided Playwright browser instance for efficiency.
        """
        self.progress.update(self.task_id, description=f"[bold yellow]Scanning username: {username}...[/bold yellow]")
        results: Dict[str, Any] = {"username": username, "found_on": [], "errors": []}

        sites = self.sites_manager.get_username_sites()

        basic_sites = [s for s in sites if s.get("checkMethod", CheckMethods.BASIC.value) == CheckMethods.BASIC.value]
        dynamic_sites = [s for s in sites if s.get("checkMethod", CheckMethods.BASIC.value) == CheckMethods.DYNAMIC.value]

        tasks: List[Coroutine] = []
        basic_semaphore = asyncio.Semaphore(config.Config.BASIC_CHECK_CONCURRENCY)
        dynamic_semaphore = asyncio.Semaphore(config.Config.DYNAMIC_CHECK_CONCURRENCY)

        context = await self.browser.new_context(
            user_agent=config.Config.USER_AGENT
        )

        try:
            async with aiohttp.ClientSession() as session:
                for site in dynamic_sites:
                    tasks.append(self._check_site_dynamic(context, site, username, dynamic_semaphore))

                for site in basic_sites:
                    tasks.append(self._check_site_basic(session, site, username, basic_semaphore))

                # Use return_exceptions=True to gather all results, including exceptions
                scan_results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in scan_results:
                if isinstance(res, Exception):
                    logger.error(f"Error during username scan: {res}")
                    results["errors"].append(str(res))
                elif res.get("found"):
                    results["found_on"].append({"name": res["name"], "url": res["url"]})
        finally:
            await context.close()
            self.progress.update(self.task_id, advance=len(sites))

        self.progress.update(self.task_id, description=f"[bold green]Username scan for {username} complete.[/bold green]")
        return results

    def _get_error_list(self, site: Dict[str, Any]) -> List[str]:
        """Helper to handle both string and list of strings for error messages."""
        errors = site.get("errorString", [])
        return [errors] if isinstance(errors, str) else errors

    async def _check_site_basic(
        self,
        session: aiohttp.ClientSession,
        site: Dict[str, Any],
        username: str,
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:
        """Performs a simple check on a site using aiohttp."""
        url = site["url"].format(username)
        error_type = site.get("errorType", ErrorTypes.STATUS_CODE.value)
        check_type = site.get("checkType", CheckTypes.NEGATIVE.value)

        async with semaphore:
            try:
                headers = {"User-Agent": config.Config.USER_AGENT}
                async with session.get(url, timeout=45, allow_redirects=True, headers=headers) as response:
                    found = False
                    if error_type == ErrorTypes.STATUS_CODE.value:
                        found = 200 <= response.status < 300
                    elif error_type == ErrorTypes.STRING.value:
                        content = await response.text()
                        error_list = self._get_error_list(site)
                        found = response.ok and not any(err.lower() in content.lower() for err in error_list)
                    else:
                        found = 200 <= response.status < 300

                    if check_type == CheckTypes.POSITIVE.value:
                        found = not found # Invert logic for positive checks

                    return {"name": site["name"], "url": url, "found": found, "method": CheckMethods.BASIC.value}

            except (asyncio.TimeoutError, aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
                raise NetworkError(f"Error checking basic site {site['name']}: {type(e).__name__}", self.name, e)
            finally:
                self.progress.update(self.task_id, advance=1)

    async def _check_site_dynamic(
        self,
        context: BrowserContext,
        site: Dict[str, Any],
        username: str,
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:
        """
        Performs a check on a JS-heavy site using a shared browser context.
        """
        url = site["url"].format(username)
        page = None
        async with semaphore:
            try:
                page = await context.new_page()
                await page.route(
                    "**/*",
                    lambda route: route.abort()
                    if route.request.resource_type in {"image", "stylesheet", "font", "media"}
                    else route.continue_(),
                )

                response = await page.goto(url, timeout=45000, wait_until="load")

                content = await page.content()
                status = response.status if response else 0

                check_type = site.get("checkType", CheckTypes.NEGATIVE.value)

                if check_type == CheckTypes.POSITIVE.value:
                    success_string = site.get("successString", "")
                    found = success_string.lower() in content.lower()
                else:
                    error_type = site.get("errorType", ErrorTypes.STATUS_CODE.value)
                    if error_type == ErrorTypes.STATUS_CODE.value:
                        found = 200 <= status < 300
                    else:
                        error_list = self._get_error_list(site)
                        found = (response.ok if response else False) and not any(
                            err.lower() in content.lower() for err in error_list
                        )

                return {"name": site["name"], "url": url, "found": found, "method": CheckMethods.DYNAMIC.value}

            except PlaywrightTimeoutError as e:
                raise NetworkError(f"Timeout checking dynamic site {site['name']}", self.name, e)
            except Exception as e:
                raise ScannerError(f"Error checking dynamic site {site['name']}: {type(e).__name__}", self.name, e)
            finally:
                if page:
                    await page.close()
                self.progress.update(self.task_id, advance=1)