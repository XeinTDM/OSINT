import aiohttp
import logging
import asyncio
import json
from typing import Dict, Any, Optional
from modules import config
from modules.core.base_scanner import BaseScanner
from modules.core.errors import NetworkError, APIError, ParsingError, RateLimitError, AuthenticationError
from modules.enums import ScannerNames

logger = logging.getLogger(__name__)

class EmailScanner(BaseScanner):
    @property
    def name(self) -> str:
        return ScannerNames.EMAIL.value

    async def scan(self, email: str, api_key: Optional[str], **kwargs) -> Dict[str, Any]:
        """
        Asynchronously checks an email for breaches using the HIBP API.
        """
        self.progress.update(self.task_id, description=f"[bold yellow]Scanning email: {email}...[/bold yellow]")

        if not api_key:
            self.progress.update(self.task_id, description=f"[bold red]HIBP API Key not provided. Skipping breach check for {email}.[/bold red]")
            raise AuthenticationError("HIBP API Key not provided. Skipping breach check.", self.name)

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {"hibp-api-key": api_key, "User-Agent": config.Config.USER_AGENT}
        result: Dict[str, Any] = {}

        try:
            async with aiohttp.ClientSession() as session:
                response = await self._query_hibp(session, url, headers)

                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", "2"))
                    logger.warning(f"Rate limited by HIBP. Waiting for {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    raise RateLimitError(f"Rate limited by HIBP. Retrying after {retry_after} seconds.", self.name)

                if response.status == 200:
                    try:
                        breaches = await response.json()
                        result = {"breached": True, "breaches": [breach["Name"] for breach in breaches], "count": len(breaches)}
                    except json.JSONDecodeError as e:
                        raise ParsingError("HIBP API returned non-JSON response.", self.name, e)
                elif response.status == 404:
                    result = {"breached": False, "message": "No breaches found for this email."}
                else:
                    raise APIError(
                        f"HIBP API error: Status: {response.status}, Response: {await response.text()[:100]}",
                        self.name
                    )

        except asyncio.TimeoutError as e:
            raise NetworkError("Request to HIBP API timed out.", self.name, e)
        except aiohttp.ClientConnectorError as e:
            raise NetworkError("Network connection error to HIBP API.", self.name, e)
        except aiohttp.ClientResponseError as e:
            raise NetworkError(f"HIBP API returned an HTTP error: Status: {e.status}, Message: {e.message}", self.name, e)
        except aiohttp.ClientError as e:
            raise NetworkError(f"An unexpected aiohttp error occurred: {e}", self.name, e)
        finally:
            self.progress.update(self.task_id, advance=1)

        self.progress.update(self.task_id, description=f"[bold green]Email scan for {email} complete.[/bold green]")
        return {"breaches": result}

    async def _query_hibp(self, session: aiohttp.ClientSession, url: str, headers: Dict[str, str]) -> aiohttp.ClientResponse:
        """Helper function to query the HIBP API."""
        return await session.get(url, headers=headers, timeout=15)