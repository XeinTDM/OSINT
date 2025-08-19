import asyncio
import whois
import aiodns
from whois.parser import PywhoisError
import ipaddress

import logging
from typing import Dict, Any, List, Optional, Union
from modules.core.base_scanner import BaseScanner
from modules.core.errors import NetworkError, ParsingError
from modules.enums import ScannerNames
from modules import config

logger = logging.getLogger(__name__)

class DomainIPScanner(BaseScanner):
    @property
    def name(self) -> str:
        return ScannerNames.DOMAIN_IP.value

    async def scan(self, target: str, **kwargs) -> Dict[str, Any]:
        """Asynchronously analyzes a domain or IP address."""
        self.progress.update(self.task_id, description=f"[bold yellow]Analyzing domain/IP: {target}...[/bold yellow]")
        result = await self._scan_domain_or_ip_async(target)
        self.progress.update(self.task_id, advance=1)
        self.progress.update(self.task_id, description=f"[bold green]Domain/IP analysis for {target} complete.[/bold green]")
        return result

    def _normalize_whois_dates(self, date_val: Any) -> str:
        """Helper to convert WHOIS date values (which can be lists) to strings."""
        if isinstance(date_val, list):
            return str(date_val[0])
        return str(date_val)

    async def _scan_port(self, target: str, port: int, semaphore: asyncio.Semaphore) -> Optional[int]:
        """Attempts to connect to a single port and returns the port number if successful."""
        async with semaphore:
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(target, port), timeout=config.Config.PORT_SCAN_TIMEOUT)
                writer.close()
                await writer.wait_closed()
                return port
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return None
            except Exception as e:
                logger.error(f"Error scanning port {port} on {target}: {e}")
                return None

    async def _scan_domain_or_ip_async(self, target: str) -> Dict[str, Any]:
        """Asynchronous function to analyze a domain or IP address."""
        results: Dict[str, Any] = {}
        is_ip = False
        try:
            ipaddress.ip_address(target)
            is_ip = True
        except ValueError:
            pass

        if not is_ip:
            try:
                loop = asyncio.get_running_loop()
                w = await loop.run_in_executor(None, whois.whois, target)
                if w and w.registrar:
                    results["whois"] = {
                        "registrar": w.registrar,
                        "creation_date": self._normalize_whois_dates(w.creation_date),
                        "expiration_date": self._normalize_whois_dates(w.expiration_date),
                        "name_servers": w.name_servers,
                        "emails": w.emails,
                    }
                else:
                    raise ParsingError("WHOIS data not found or domain does not exist.", self.name)
            except Exception as e:
                if isinstance(e, PywhoisError):
                    raise ParsingError(f"WHOIS parsing error: {e}", self.name, e)
                else:
                    raise NetworkError(f"WHOIS lookup failed: {type(e).__name__} - {e}", self.name, e)

            dns_records: Dict[str, Union[str, List[str]]] = {}
            resolver = aiodns.DNSResolver()
            record_types = ["A", "AAAA", "MX", "TXT", "NS", "SOA", "CNAME"]
            for r_type in record_types:
                try:
                    answers = await resolver.query(target, r_type)
                    dns_records[r_type] = sorted([str(rdata).strip(".") for rdata in answers])
                except aiodns.error.DNSError as e:
                    raise NetworkError(f"DNS error for {r_type} record: {e}", self.name, e)
                except Exception as e:
                    raise NetworkError(f"Unexpected error during DNS lookup for {r_type} record: {e}", self.name, e)
            results["dns"] = dns_records

        ports_to_scan = [21, 22, 25, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 5432, 8080]
        port_scan_semaphore = asyncio.Semaphore(50)

        port_scan_tasks = [
            self._scan_port(target, port, port_scan_semaphore) for port in ports_to_scan
        ]
        open_ports_results = await asyncio.gather(*port_scan_tasks)
        results["open_ports"] = sorted([p for p in open_ports_results if p is not None])

        return results