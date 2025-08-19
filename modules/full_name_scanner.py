import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from rich.progress import Progress
from playwright.async_api import Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from modules.core.base_scanner import BaseScanner
from modules.sites_manager import sites_manager # Import the singleton instance

from modules.core.errors import NetworkError, ScannerError
from modules import config
from modules.core.site_models import Site
from modules.enums import CheckMethods

logger = logging.getLogger(__name__)

class FullNameScanner(BaseScanner):
    """Scanner for full name OSINT."""

    def __init__(self, progress: Progress, task_id, browser: Optional[Browser] = None):
        super().__init__(progress, task_id, browser)
        self.sites_manager = sites_manager # Use the imported singleton

    NAME: str = "Full Name Scan"

    async def scan(self, target: str, **kwargs) -> Dict[str, Any]:
        full_name = kwargs.get("full_name", "")
        first_name = kwargs.get("first_name", "")
        middle_name = kwargs.get("middle_name", "")
        last_name = kwargs.get("last_name", "")
        aliases = kwargs.get("aliases", [])
        country = kwargs.get("country", "")

        display_name = full_name
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
            if middle_name:
                display_name = f"{first_name} {middle_name} {last_name}"

        self.progress.update(self.task_id, description=f"[bold yellow]Scanning full name: {display_name} in {country}...[/bold yellow]")
        results = {"full_name": full_name, "first_name": first_name, "middle_name": middle_name, "last_name": last_name, "country": country, "found_on": [], "errors": []}

        country_sites: List[Site] = self.sites_manager.get_full_name_sites_by_country(country)

        if not country_sites:
            self.progress.update(self.task_id, description=f"[bold red]No full name sites found for {country}.[/bold red]")
            return results

        tasks = []
        basic_semaphore = asyncio.Semaphore(config.Config.BASIC_CHECK_CONCURRENCY)
        dynamic_semaphore = asyncio.Semaphore(config.Config.DYNAMIC_CHECK_CONCURRENCY)

        context = None
        if self.browser:
            context = await self.browser.new_context(user_agent=config.Config.USER_AGENT)

        try:
            async with aiohttp.ClientSession() as session:
                for site in country_sites:
                    if site.active:
                        query_params = {}
                        advanced_search = kwargs.get("advanced_search", False)
                        city = kwargs.get("city", "")

                        if "first" in site.placeholders and "last" in site.placeholders:
                            query_params["first"] = first_name
                            query_params["last"] = last_name
                            
                            if advanced_search and "city" in site.advanced_placeholders and city:
                                query_params["city"] = city

                            if not site.requiresJs:
                                tasks.append(self._check_site_basic(session, site, basic_semaphore, **query_params))
                            elif site.requiresJs and context:
                                tasks.append(self._check_site_dynamic(context, site, dynamic_semaphore, **query_params))
                            else:
                                logger.warning(f"Skipping site {site.name} due to unsupported check method or missing browser context.")
                        else:
                            name_variations = []
                            if middle_name:
                                name_variations.append(f"{first_name} {middle_name} {last_name}")
                                name_variations.append(f"{first_name} {last_name}")
                            else:
                                name_variations.append(full_name)
                            
                            for alias in aliases:
                                name_variations.append(alias)

                            for name_to_scan in name_variations:
                                query_params_for_variation = {"query": name_to_scan}
                                if not site.requiresJs:
                                    tasks.append(self._check_site_basic(session, site, basic_semaphore, **query_params_for_variation))
                                elif site.requiresJs and context:
                                    tasks.append(self._check_site_dynamic(context, site, dynamic_semaphore, **query_params_for_variation))
                                else:
                                    logger.warning(f"Skipping site {site.name} due to unsupported check method or missing browser context.")
                    else:
                        logger.info(f"Skipping inactive site: {site.name}")

                site_results = await asyncio.gather(*tasks, return_exceptions=True)

                for res in site_results:
                    if isinstance(res, Exception):
                        logger.error(f"Error during full name scan: {res}")
                        results["errors"].append(str(res))
                    elif res.get("found"):
                        results["found_on"].append({"name": res["name"], "url": res["url"]})
        finally:
            if context:
                await context.close()
            self.progress.update(self.task_id, advance=len(country_sites))

        self.progress.update(self.task_id, description=f"[bold green]Full name scan for {display_name} in {country} complete.[/bold green]")
        return results

    async def _check_site_basic(
        self,
        session: aiohttp.ClientSession,
        site: Site,
        semaphore: asyncio.Semaphore,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Performs a basic check on a site using aiohttp.
        """
        site_name = site.name
        url = site.urlTemplate.format(**kwargs)
        if site.urlEncode:
            from urllib.parse import quote_plus
            encoded_kwargs = {k: quote_plus(str(v)) for k, v in kwargs.items()}
            url = site.urlTemplate.format(**encoded_kwargs)

        headers = site.headers if site.headers else {"User-Agent": config.Config.USER_AGENT}
        timeout = site.timeoutSeconds if site.timeoutSeconds else 45
        retries = site.retries if site.retries is not None else 0
        
        found = False
        for attempt in range(retries + 1):
            try:
                async with semaphore:
                    async with session.request(
                        site.method,
                        url,
                        timeout=timeout,
                        allow_redirects=True,
                        headers=headers
                    ) as response:
                        content = await response.text()
                        
                        if site.noResult.type == "contains":
                            found = site.noResult.value.lower() not in content.lower()
                        elif site.noResult.type == "status_code":
                            found = response.status != int(site.noResult.value)
                        else:
                            found = 200 <= response.status < 300

                        if found:
                            break
                        else:
                            logger.debug(f"Attempt {attempt + 1} for {site_name}: No result found. Retrying...")

            except (asyncio.TimeoutError, aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
                logger.warning(f"Attempt {attempt + 1} for {site_name}: Network error - {type(e).__name__}. Retrying...")
                if attempt == retries:
                    raise NetworkError(f"Error checking basic site {site_name}: {type(e).__name__}", self.name, e)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} for {site_name}: Unexpected error - {type(e).__name__}. Retrying...")
                if attempt == retries:
                    raise ScannerError(f"Error checking basic site {site_name}: {type(e).__name__}", self.name, e)
            finally:
                self.progress.update(self.task_id, advance=1)

        return {"name": site_name, "url": url, "found": found, "method": site.method.value}

    async def _check_site_dynamic(
        self,
        context: BrowserContext,
        site: Site,
        semaphore: asyncio.Semaphore,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Performs a check on a JS-heavy site using a shared browser context.
        """
        site_name = site.name
        url = site.urlTemplate.format(**kwargs)
        if site.urlEncode:
            from urllib.parse import quote_plus
            encoded_kwargs = {k: quote_plus(str(v)) for k, v in kwargs.items()}
            url = site.urlTemplate.format(**encoded_kwargs)

        timeout = site.timeoutSeconds if site.timeoutSeconds else 45
        retries = site.retries if site.retries is not None else 0
        
        found = False
        page = None
        for attempt in range(retries + 1):
            try:
                async with semaphore:
                    page = await context.new_page()
                    if site.headers:
                        await page.set_extra_http_headers(site.headers)

                    await page.route(
                        "**/*",
                        lambda route: route.abort()
                        if route.request.resource_type in {"image", "stylesheet", "font", "media"}
                        else route.continue_(),
                    )

                    response = await page.goto(url, timeout=timeout * 1000, wait_until="load")

                    content = await page.content()
                    status = response.status if response else 0

                    if site.noResult.type == "contains":
                        found = site.noResult.value.lower() not in content.lower()
                    elif site.noResult.type == "status_code":
                        found = status != int(site.noResult.value)
                    else:
                        found = 200 <= status < 300

                    if found:
                        break
                    else:
                        logger.debug(f"Attempt {attempt + 1} for {site_name}: No result found. Retrying...")

            except PlaywrightTimeoutError as e:
                logger.warning(f"Attempt {attempt + 1} for {site_name}: Timeout checking dynamic site - {type(e).__name__}. Retrying...")
                if attempt == retries:
                    raise NetworkError(f"Timeout checking dynamic site {site_name}: {type(e).__name__}", self.name, e)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} for {site_name}: Unexpected error checking dynamic site - {type(e).__name__}. Retrying...")
                if attempt == retries:
                    raise ScannerError(f"Error checking dynamic site {site_name}: {type(e).__name__}", self.name, e)
            finally:
                if page:
                    await page.close()
                self.progress.update(self.task_id, advance=1)

        return {"name": site_name, "url": url, "found": found, "method": CheckMethods.DYNAMIC.value}

    