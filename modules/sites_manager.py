import os
import json
import logging
import aiohttp
from typing import List

from modules import paths
from modules.core.site_models import CountrySites, Site
from pydantic import ValidationError
from modules.constants import FULL_NAME_SITES_URL

logger = logging.getLogger(__name__)

class SitesManager:
    """Manages the loading and access of OSINT sites data from sites.json and full_name_sites.json."""

    def __init__(self):
        self._username_sites_data: List[Site] = []
        self._full_name_sites_data: List[CountrySites] = []

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
        try:
            with open(paths.DEFAULT_FULL_NAME_SITES_JSON_PATH, "r", encoding="utf-8") as f:
                default_content = json.load(f)
        except FileNotFoundError:
            logger.error(f"Default full name sites JSON file not found at {paths.DEFAULT_FULL_NAME_SITES_JSON_PATH}")
            default_content = []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding default full name sites JSON: {e}")
            default_content = []

        with open(paths.FULL_NAME_SITES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(default_content, f, indent=2)
        logger.info("Default full_name_sites.json created.")

    def _parse_full_name_sites_data(self, raw_data: list) -> List[CountrySites]:
        parsed_data = []
        if isinstance(raw_data, list):
            for country_data in raw_data:
                try:
                    parsed_data.append(CountrySites.model_validate(country_data))
                except ValidationError as e:
                    logger.error(f"Validation error parsing country data: {e}")
                    continue
                except Exception as e:
                    logger.error(f"An unexpected error occurred during parsing country data: {e}")
                    continue
        return parsed_data

    def get_username_sites(self) -> List[Site]:
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
                    response.raise_for_status()
                    new_sites_content = await response.text()

            parsed_content = json.loads(new_sites_content)
            with open(paths.SITES_JSON_PATH, "w", encoding="utf-8") as f:
                f.write(new_sites_content)
            
            validated_sites = []
            for site_data in parsed_content.get("username_sites", []):
                try:
                    validated_sites.append(Site.model_validate(site_data))
                except ValidationError as e:
                    logger.error(f"Validation error parsing username site data: {e}")
                    continue
                except Exception as e:
                    logger.error(f"An unexpected error occurred during parsing username site data: {e}")
                    continue
            self._username_sites_data = validated_sites
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
                    response.raise_for_status()
                    new_sites_content = await response.text()

            parsed_content = json.loads(new_sites_content)
            with open(paths.FULL_NAME_SITES_JSON_PATH, "w", encoding="utf-8") as f:
                f.write(new_sites_content)
            self._full_name_sites_data = self._parse_full_name_sites_data(parsed_content)
            logger.info("full_name_sites.json updated successfully!")
            return True
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch full_name_sites.json from URL: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating full_name_sites.json: {e}")
        return False

    def _load_username_sites_data_from_file(self) -> List[Site]:
        try:
            with open(paths.SITES_JSON_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f).get("username_sites", [])
                validated_sites = []
                for site_data in raw_data:
                    try:
                        validated_sites.append(Site.model_validate(site_data))
                    except ValidationError as e:
                        logger.error(f"Validation error parsing local username site data: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"An unexpected error occurred during parsing local username site data: {e}")
                        continue
                return validated_sites
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading sites.json: {e}.")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during sites.json parsing: {e}.")
            return []

    def _load_full_name_sites_data_from_file(self) -> List[CountrySites]:
        try:
            with open(paths.FULL_NAME_SITES_JSON_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                return self._parse_full_name_sites_data(raw_data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading full_name_sites.json: {e}.")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during full_name_sites.json parsing: {e}.")
            return []

    async def ensure_sites_json_exists(self):
        """Ensures sites.json and full_name_sites.json exist and are loaded. Attempts to update from URL if not found or empty."""
        # Load username sites
        if not self._username_sites_data:
            if not os.path.exists(paths.SITES_JSON_PATH):
                logger.warning("sites.json not found. Creating a default file.")
                self._create_default_username_sites_json()

            self._username_sites_data = self._load_username_sites_data_from_file()

            if not self._username_sites_data:
                logger.warning("Username sites data is empty or missing after local load. Attempting to fetch from URL...")
                await self.update_sites_json_from_url()
                if not self._username_sites_data:
                    logger.error("Failed to load username sites. Using empty default data.")
                    self._username_sites_data = []

        # Load full name sites
        if not self._full_name_sites_data:
            if not os.path.exists(paths.FULL_NAME_SITES_JSON_PATH):
                logger.warning("full_name_sites.json not found. Creating a default file.")
                self._create_default_full_name_sites_json()

            self._full_name_sites_data = self._load_full_name_sites_data_from_file()

            if not self._full_name_sites_data:
                logger.warning("Full name sites data is empty or missing after local load. Attempting to fetch from URL...")
                await self.update_full_name_sites_json_from_url(FULL_NAME_SITES_URL)
                if not self._full_name_sites_data:
                    logger.error("Failed to load full name sites. Using empty default data.")
                    self._full_name_sites_data = []

sites_manager = SitesManager()
