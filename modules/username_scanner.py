import aiohttp
import asyncio
import logging
from playwright.async_api import Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from rich.progress import Progress
from typing import Dict, List, Any, Coroutine
from modules import config
from modules.core.base_scanner import BaseScanner
from modules.sites_manager import sites_manager
from modules.enums import CheckMethods, ErrorTypes, CheckTypes
from modules.core.site_models import Site

logger = logging.getLogger(__name__)

class UsernameScanner(BaseScanner):
    def __init__(self, progress: Progress, task_id, browser: Browser):
        super().__init__(progress, task_id, browser)
        self.sites_manager = sites_manager

    @property
    def name(self) -> str:
        return "Username Scan"

    async def scan(self, username: str, **kwargs) -> Dict[str, Any]:
        """
        Orchestrates the scanning of a username across multiple sites.
        Reuses the provided Playwright browser instance for efficiency.
        """
        
        results: Dict[str, Any] = {"username": username, "found_on": [], "errors": []}

        sites = self.sites_manager.get_username_sites()
        self.progress.update(self.task_id, total=len(sites))

        basic_sites = [s for s in sites if s.checkMethod == CheckMethods.BASIC]
        dynamic_sites = [s for s in sites if s.checkMethod == CheckMethods.DYNAMIC]

        tasks: List[Coroutine] = []
        basic_semaphore = asyncio.Semaphore(config.Config.BASIC_CHECK_CONCURRENCY)
        dynamic_semaphore = asyncio.Semaphore(config.Config.DYNAMIC_CHECK_CONCURRENCY)

        context = await self.browser.new_context(
            user_agent=config.Config.USER_AGENT
        )

        try:
            connector = aiohttp.TCPConnector(ssl=False) if config.Config.DISABLE_SSL_VERIFICATION else None
            async with aiohttp.ClientSession(connector=connector) as session:
                for site in dynamic_sites:
                    tasks.append(self._check_site_dynamic(context, site, username, dynamic_semaphore))

                for site in basic_sites:
                    tasks.append(self._check_site_basic(session, site, username, basic_semaphore))

                scan_results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in scan_results:
                if isinstance(res, Exception):
                    logger.error(f"Error during username scan: {res}")
                    results["errors"].append(str(res))
                elif res.get("found"):
                    results["found_on"].append({"name": res["name"], "url": res["url"]})
        finally:
            await context.close()

        self.progress.update(self.task_id, description=f"[bold green]Username scan for {username} complete.[/bold green]")
        return results

    def _get_error_list(self, site: Site) -> List[str]:
        """Helper to handle both string and list of strings for error messages."""
        errors = site.errorString if site.errorString is not None else []
        return [errors] if isinstance(errors, str) else errors

    async def _check_site_basic(
        self,
        session: aiohttp.ClientSession,
        site: Site,
        username: str,
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:
        """Performs a simple check on a site using aiohttp."""
        url = site.generate_url(username)
        error_type = site.errorType
        check_type = site.checkType

        async with semaphore:
            try:
                # Handle custom checks
                if hasattr(site, 'customCheck') and site.customCheck:
                    return await self._handle_custom_check(session, site, username)
                
                headers = {"User-Agent": config.Config.USER_AGENT}
                # Use custom headers if provided
                if hasattr(site, 'headers') and site.headers:
                    headers.update(site.headers)
                
                # Use custom HTTP method if provided
                method = getattr(site, 'method', 'GET').upper()
                
                if method == 'POST':
                    # For POST requests, send empty JSON body
                    async with session.post(url, json={}, timeout=45, allow_redirects=True, headers=headers) as response:
                        return await self._process_response(response, site, url, username)
                else:
                    async with session.get(url, timeout=30, allow_redirects=True, headers=headers) as response:
                        return await self._process_response(response, site, url, username)

            except (asyncio.TimeoutError, aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
                error_msg = str(e)
                if "DNS" in error_msg or "Timeout while contacting DNS servers" in error_msg:
                    logger.warning(f"DNS resolution failed for {site.name}: {url}")
                else:
                    logger.error(f"Error checking basic site {site.name}: {type(e).__name__} - {e}")
                return {"name": site.name, "url": url, "found": False, "method": CheckMethods.BASIC.value, "error": str(e)}
            finally:
                self.progress.update(self.task_id, advance=1)

    async def _handle_custom_check(self, session: aiohttp.ClientSession, site: Site, username: str) -> Dict[str, Any]:
        """Handle custom site-specific checks."""
        if site.customCheck == "discord_api":
            return await self._check_discord_api(session, site, username)
        else:
            # Fallback to basic check for unknown custom checks
            return {"name": site.name, "url": site.urlTemplate, "found": False, "method": CheckMethods.BASIC.value, "error": "Unknown custom check"}

    async def _check_discord_api(self, session: aiohttp.ClientSession, site: Site, username: str) -> Dict[str, Any]:
        """Check Discord user existence using their API."""
        try:
            # Discord API endpoint for checking user relationships
            url = "https://discord.com/api/v9/users/@me/relationships"
            
            # Discord requires authentication, but we can try to check if the user exists
            # by attempting to access their profile page
            profile_url = f"https://discord.com/users/{username}"
            
            headers = {"User-Agent": config.Config.USER_AGENT}
            async with session.get(profile_url, timeout=45, headers=headers) as response:
                # Discord returns 200 for existing users, 404 for non-existent
                found = response.status == 200
                
                return {
                    "name": site.name, 
                    "url": profile_url, 
                    "found": found, 
                    "method": CheckMethods.BASIC.value
                }
        except Exception as e:
            logger.error(f"Error checking Discord API: {e}")
            return {"name": site.name, "url": site.urlTemplate, "found": False, "method": CheckMethods.BASIC.value, "error": str(e)}

    async def _process_response(self, response, site: Site, url: str, username: str) -> Dict[str, Any]:
        """Process the HTTP response to determine if username exists."""
        error_type = site.errorType
        check_type = site.checkType
        
        found = False
        if error_type == ErrorTypes.STATUS_CODE:
            # For status code checks, also verify the content doesn't contain error indicators
            if 200 <= response.status < 300:
                content = await response.text()
                # Check if content contains common error indicators even with 200 status
                error_indicators = [
                    "not found", "doesn't exist", "user not found", "profile not found",
                    "page not found", "404", "no such user", "could not find",
                    "doesn't exist", "not available", "unavailable", "broken link"
                ]
                found = not any(indicator in content.lower() for indicator in error_indicators)
            else:
                found = False
        elif error_type == ErrorTypes.STRING:
            content = await response.text()
            error_list = self._get_error_list(site)
            is_success_status = 200 <= response.status < 300
            found = is_success_status and not any(err.lower() in content.lower() for err in error_list)
        else:
            # Default case: check both status and content
            if 200 <= response.status < 300:
                content = await response.text()
                error_indicators = [
                    "not found", "doesn't exist", "user not found", "profile not found",
                    "page not found", "404", "no such user", "could not find"
                ]
                found = not any(indicator in content.lower() for indicator in error_indicators)
            else:
                found = False

        if check_type == CheckTypes.POSITIVE:
            found = not found

        return {"name": site.name, "url": url, "found": found, "method": CheckMethods.BASIC.value}

    async def _check_site_dynamic(
        self,
        context: BrowserContext,
        site: Site,
        username: str,
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:
        """
        Performs a check on a JS-heavy site using a shared browser context.
        """
        url = site.generate_url(username)
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

                response = await page.goto(url, timeout=config.Config.PLAYWRIGHT_TIMEOUT, wait_until=config.Config.PLAYWRIGHT_WAIT_UNTIL)

                try:
                    content = await page.content()
                except Exception as e:
                    if "navigating" in str(e).lower() or "unable to retrieve content" in str(e).lower():
                        try:
                            await page.wait_for_load_state("domcontentloaded", timeout=10000)
                            content = await page.content()
                        except Exception:
                            content = await page.text_content() or ""
                    else:
                        raise e
                status = response.status if response else 0

                check_type = site.checkType

                if check_type == CheckTypes.POSITIVE:
                    success_string = site.successString if site.successString is not None else ""
                    found = success_string.lower() in content.lower()
                else:
                    error_type = site.errorType
                    if error_type == ErrorTypes.STATUS_CODE:
                        # For status code checks, also verify the content doesn't contain error indicators
                        if 200 <= status < 300:
                            # Check if content contains common error indicators even with 200 status
                            error_indicators = [
                                "not found", "doesn't exist", "user not found", "profile not found",
                                "page not found", "404", "no such user", "could not find",
                                "doesn't exist", "not available", "unavailable", "broken link"
                            ]
                            found = not any(indicator in content.lower() for indicator in error_indicators)
                        else:
                            found = False
                    else:
                        error_list = self._get_error_list(site)
                        status = response.status if response else 0
                        is_success_status = 200 <= status < 300
                        if is_success_status:
                            # Even with success status, check for error indicators in content
                            error_indicators = [
                                "not found", "doesn't exist", "user not found", "profile not found",
                                "page not found", "404", "no such user", "could not find"
                            ]
                            found = not any(indicator in content.lower() for indicator in error_indicators)
                            # Also check the site-specific error strings
                            found = found and not any(err.lower() in content.lower() for err in error_list)
                        else:
                            found = False

                return {"name": site.name, "url": url, "found": found, "method": CheckMethods.DYNAMIC.value}

            except PlaywrightTimeoutError as e:
                logger.warning(f"Timeout checking dynamic site {site.name}: {e}")
                return {"name": site.name, "url": url, "found": False, "method": CheckMethods.DYNAMIC.value, "error": str(e)}
            except Exception as e:
                logger.error(f"Error checking dynamic site {site.name}: {type(e).__name__} - {e}")
                return {"name": site.name, "url": url, "found": False, "method": CheckMethods.DYNAMIC.value, "error": str(e)}
            finally:
                if page:
                    await page.close()
                self.progress.update(self.task_id, advance=1)