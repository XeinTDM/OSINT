import os
import json
import logging
import aiohttp
from typing import List

from modules import paths
from modules.core.site_models import CountrySites, Site, NoResult, ResultMatcher, FieldExtraction, Extraction, Pagination, Legal

logger = logging.getLogger(__name__)

class SitesManager:
    """Manages the loading and access of OSINT sites data from sites.json and full_name_sites.json."""

    def __init__(self):
        self._username_sites_data = []
        self._full_name_sites_data: List[CountrySites] = []
        self._load_sites_data()

    def _load_sites_data(self):
        """Loads the sites data from the local sites.json and full_name_sites.json files."""
        # Load username sites
        if not os.path.exists(paths.SITES_JSON_PATH):
            logger.warning("sites.json not found. Attempting to create a default file.")
            self._create_default_username_sites_json()

        try:
            with open(paths.SITES_JSON_PATH, "r", encoding="utf-8") as f:
                self._username_sites_data = json.load(f).get("username_sites", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading sites.json: {e}. Returning empty username sites.")
            self._username_sites_data = []

        # Load full name sites
        if not os.path.exists(paths.FULL_NAME_SITES_JSON_PATH):
            logger.warning("full_name_sites.json not found. Attempting to create a default file.")
            self._create_default_full_name_sites_json()

        try:
            with open(paths.FULL_NAME_SITES_JSON_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                parsed_data = []
                if isinstance(raw_data, list): # Ensure raw_data is a list
                    for country_data in raw_data:
                        sites = []
                        for site_info in country_data.get("sites", []):
                            try:
                                no_result = NoResult(**site_info["noResult"])
                                result_matcher = ResultMatcher(**site_info["resultMatcher"]) if "resultMatcher" in site_info else None
                                extract = None
                                if "extract" in site_info:
                                    fields = {k: FieldExtraction(**v) for k, v in site_info["extract"].get("fields", {}).items()}
                                    extract = Extraction(recordsSelector=site_info["extract"]["recordsSelector"], fields=fields)
                                pagination = Pagination(**site_info["pagination"]) if "pagination" in site_info else None
                                legal = Legal(**site_info["legal"]) if "legal" in site_info else None

                                site = Site(
                                    id=site_info["id"],
                                    name=site_info["name"],
                                    homeUrl=site_info["homeUrl"],
                                    urlTemplate=site_info["urlTemplate"],
                                    placeholders=site_info["placeholders"],
                                    urlEncode=site_info["urlEncode"],
                                    method=site_info["method"],
                                    headers=site_info.get("headers", {}),
                                    responseType=site_info["responseType"],
                                    requiresJs=site_info["requiresJs"],
                                    noResult=no_result,
                                    resultMatcher=result_matcher,
                                    extract=extract,
                                    pagination=pagination,
                                    rateLimitPerMinute=site_info.get("rateLimitPerMinute"),
                                    timeoutSeconds=site_info.get("timeoutSeconds"),
                                    retries=site_info.get("retries"),
                                    lastVerified=site_info.get("lastVerified"),
                                    active=site_info.get("active", True),
                                    legal=legal,
                                    tags=site_info.get("tags", []),
                                    notes=site_info.get("notes"),
                                    advanced_placeholders=site_info.get("advanced_placeholders", [])
                                )
                                sites.append(site)
                            except KeyError as ke:
                                logger.error(f"Missing key in site data: {ke} in {site_info.get('name', 'Unknown Site')}")
                                continue
                            except TypeError as te:
                                logger.error(f"Type error in site data: {te} in {site_info.get('name', 'Unknown Site')}")
                                continue
                        parsed_data.append(CountrySites(country=country_data["country"], country_code=country_data.get("country_code"), sites=sites))
                self._full_name_sites_data = parsed_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading full_name_sites.json: {e}. Returning empty full name sites.")
            self._full_name_sites_data = []
        except Exception as e:
            logger.error(f"An unexpected error occurred during full_name_sites.json parsing: {e}")
            self._full_name_sites_data = []

    def _create_default_username_sites_json(self):
        """Creates a default sites.json file if it doesn't exist."""
        os.makedirs(os.path.dirname(paths.SITES_JSON_PATH), exist_ok=True)
        default_content = {"username_sites": []}
        with open(paths.SITES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(default_content, f, indent=2)
        logger.info("Default sites.json created.")

    def _create_default_full_name_sites_json(self):
        """Creates a default full_name_sites.json file if it doesn't exist."""
        os.makedirs(os.path.dirname(paths.FULL_NAME_SITES_JSON_PATH), exist_ok=True)
        default_content = [
            {
                "country": "Sweden",
                "country_code": "SE",
                "sites": [
                    {
                        "id": "ratsit_v1",
                        "name": "Ratsit",
                        "homeUrl": "https://www.ratsit.se",
                        "urlTemplate": "https://www.ratsit.se/sok/person?who={query}",
                        "placeholders": ["query"],
                        "urlEncode": True,
                        "method": "GET",
                        "headers": {
                            "User-Agent": "osint-tool/1.0"
                        },
                        "responseType": "html",
                        "requiresJs": False,
                        "noResult": { "type": "contains", "value": "Inga träffar" },
                        "resultMatcher": { "type": "css", "value": ".search-results .person" },
                        "extract": {
                            "recordsSelector": ".search-results .person",
                            "fields": {
                                "name": { "type": "css", "value": ".name", "multiple": False },
                                "age": { "type": "regex", "value": r"(\d+) år" },
                                "address": { "type": "css", "value": ".address" }
                            }
                        },
                        "pagination": { "type": "param", "paramName": "page", "start": 1, "maxPages": 2 },
                        "rateLimitPerMinute": 30,
                        "timeoutSeconds": 10,
                        "retries": 2,
                        "lastVerified": "2025-08-01T00:00:00Z",
                        "active": True,
                        "legal": { "allowed": None, "note": "Check robots/TOS for commercial scraping" },
                        "tags": ["people", "phone", "directory"],
                        "notes": "Use query = 'First Last' or SSN when available"
                    }
                ]
            }
        ]
        with open(paths.FULL_NAME_SITES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(default_content, f, indent=2)
        logger.info("Default full_name_sites.json created.")

    def get_username_sites(self) -> list:
        """Returns the list of username scanning sites."""
        return self._username_sites_data

    def get_full_name_sites_by_country(self, country: str) -> List[Site]:
        """Returns the list of full name scanning sites for a given country."""
        for country_data in self._full_name_sites_data:
            if country_data.country.lower() == country.lower():
                return country_data.sites
        return []


    async def update_sites_json_from_url(self, url: str = "https://raw.githubusercontent.com/XeinTDM/OSINT/main/data/sites.json"):
        """Fetches the latest sites.json (username sites) from a URL and saves it locally."""
        logger.info(f"Attempting to fetch latest sites.json from {url}...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()  # Raise an exception for bad status codes
                    new_sites_content = await response.text()

            with open(paths.SITES_JSON_PATH, "w", encoding="utf-8") as f:
                f.write(new_sites_content)
            self._username_sites_data = json.loads(new_sites_content).get("username_sites", []) # Update in-memory data
            logger.info("sites.json updated successfully!")
            return True
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch sites.json from URL: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating sites.json: {e}")
        return False

    async def update_full_name_sites_json_from_url(self, url: str):
        """Fetches the latest full_name_sites.json from a URL and saves it locally."""
        logger.info(f"Attempting to fetch latest full_name_sites.json from {url}...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()  # Raise an exception for bad status codes
                    new_sites_content = await response.text()

            with open(paths.FULL_NAME_SITES_JSON_PATH, "w", encoding="utf-8") as f:
                f.write(new_sites_content)
            self._full_name_sites_data = json.loads(new_sites_content) # Update in-memory data
            logger.info("full_name_sites.json updated successfully!")
            return True
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch full_name_sites.json from URL: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating full_name_sites.json: {e}")
        return False

    async def ensure_sites_json_exists(self):
        """Ensures sites.json and full_name_sites.json exist and are loaded. Attempts to update from URL if not found or empty."""
        # Check username sites
        if not self._username_sites_data:
            logger.warning("Username sites data is empty or missing. Attempting to fetch from URL...")
            await self.update_sites_json_from_url()
            if not self._username_sites_data:
                logger.error("Failed to load username sites. Using empty default data.")
                self._username_sites_data = []

        # Check full name sites
        if not self._full_name_sites_data:
            logger.warning("Full name sites data is empty or missing. Using empty default data.")
            self._full_name_sites_data = []

# Instantiate the manager for global access if needed, or pass it around
sites_manager = SitesManager()
