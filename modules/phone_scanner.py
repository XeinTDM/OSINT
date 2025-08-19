import asyncio
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from typing import Dict, Any
from modules.core.base_scanner import BaseScanner
from modules.core.errors import ParsingError
from modules.enums import ScannerNames

class PhoneScanner(BaseScanner):
    @property
    def name(self) -> str:
        return ScannerNames.PHONE_NUMBER.value

    async def scan(self, phone_number_str: str, **kwargs) -> Dict[str, Any]:
        """Asynchronously analyzes a phone number."""
        self.progress.update(self.task_id, description=f"[bold yellow]Analyzing phone number: {phone_number_str}...[/bold yellow]")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._analyze_phone_number_sync, phone_number_str)
        self.progress.update(self.task_id, advance=1)
        self.progress.update(self.task_id, description=f"[bold green]Phone number analysis for {phone_number_str} complete.[/bold green]")
        return result

    def _analyze_phone_number_sync(self, phone_number_str: str) -> Dict[str, Any]:
        """Synchronous function to analyze a phone number."""
        try:
            parsed_number = phonenumbers.parse(phone_number_str, None)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ParsingError("Invalid phone number provided.", self.name)

            country_code = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL).split(
                " "
            )[0]
            national_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)

            return {
                "is_valid": True,
                "country": geocoder.description_for_number(parsed_number, "en"),
                "country_code": country_code,
                "national_number": national_number,
                "carrier": carrier.name_for_number(parsed_number, "en"),
                "timezone": timezone.time_zones_for_number(parsed_number)[0],
            }
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ParsingError(f"Could not parse phone number: {e}", self.name, e)