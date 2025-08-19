import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
from modules.core.errors import ParsingError, NetworkError
from modules.domain_ip_scanner import DomainIPScanner
from whois.parser import PywhoisError
from rich.progress import Progress


class TestDomainIPScanner(unittest.IsolatedAsyncioTestCase):

    # Define mock exception classes within the test class
    class MockDNSError(Exception):
        pass

    def setUp(self):
        self.mock_progress = MagicMock(spec=Progress)
        self.mock_task_id = 1
        # Pass the mock_progress and mock_task_id to the scanner instance
        self.scanner = DomainIPScanner(progress=self.mock_progress, task_id=self.mock_task_id)

    def test_normalize_whois_dates(self):
        self.assertEqual(self.scanner._normalize_whois_dates("2023-01-01"), "2023-01-01")
        self.assertEqual(self.scanner._normalize_whois_dates(["2023-01-01", "2023-01-02"]), "2023-01-01")
        self.assertEqual(self.scanner._normalize_whois_dates(None), "None")
        self.assertEqual(self.scanner._normalize_whois_dates(123), "123")

    @patch('asyncio.open_connection')
    async def test_scan_port_open(self, mock_open_connection):
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.close = MagicMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        
        semaphore = asyncio.Semaphore(1)
        result = await self.scanner._scan_port('example.com', 80, semaphore)
        self.assertEqual(result, 80)
        mock_open_connection.assert_called_once_with('example.com', 80)
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_called_once()

    @patch('asyncio.open_connection', side_effect=ConnectionRefusedError)
    async def test_scan_port_closed(self, mock_open_connection):
        semaphore = asyncio.Semaphore(1)
        result = await self.scanner._scan_port('example.com', 80, semaphore)
        self.assertIsNone(result)

    @patch('asyncio.open_connection', side_effect=asyncio.TimeoutError)
    async def test_scan_port_timeout(self, mock_open_connection):
        semaphore = asyncio.Semaphore(1)
        result = await self.scanner._scan_port('example.com', 80, semaphore)
        self.assertIsNone(result)

    @patch('modules.domain_ip_scanner.whois')
    @patch('modules.domain_ip_scanner.aiodns') # Patch aiodns module directly
    @patch.object(DomainIPScanner, '_scan_port', new_callable=AsyncMock)
    async def test_scan_domain_or_ip_async_domain(self, mock_scan_port, mock_aiodns, mock_whois):
        # Mock WHOIS
        mock_whois_result = MagicMock()
        mock_whois_result.registrar = "Example Registrar"
        mock_whois_result.creation_date = "2020-01-01"
        mock_whois_result.expiration_date = ["2025-01-01"]
        mock_whois_result.name_servers = ["ns1.example.com"]
        mock_whois_result.emails = ["abuse@example.com"]
        mock_whois.whois.return_value = mock_whois_result

        # Assign our mock exception to the patched module
        mock_aiodns.error.DNSError = self.MockDNSError

        # Mock DNS Resolver
        mock_resolver_instance = mock_aiodns.DNSResolver.return_value
        mock_resolver_instance.query = AsyncMock()
        mock_resolver_instance.query.side_effect = [
            [MagicMock(host='192.0.2.1')], # A record
            [MagicMock(host='2001:db8::1')], # AAAA record
            [MagicMock(host='mail.example.com')], # MX record
            [MagicMock(strings=['v=spf1 include:_spf.example.com ~all'])], # TXT record
            [MagicMock(host='ns1.example.com')], # NS record
            [MagicMock(mname='ns1.example.com')], # SOA record
            self.MockDNSError, # CNAME error - use our mock exception
        ]

        # Mock _scan_port
        # There are 14 ports to scan in domain_ip_scanner.py
        # [21, 22, 25, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 5432, 8080]
        mock_scan_port.side_effect = [80, 443] + [None] * 12 # Simulate open ports 80, 443, rest closed

        target = "example.com"
        with self.assertRaises(NetworkError) as cm:
            await self.scanner._scan_domain_or_ip_async(target)
        self.assertIn("DNS error for CNAME record", str(cm.exception))

    @patch.object(DomainIPScanner, '_scan_port', new_callable=AsyncMock)
    async def test_scan_domain_or_ip_async_ip(self, mock_scan_port):
        # Mock _scan_port
        # There are 14 ports to scan in domain_ip_scanner.py
        mock_scan_port.side_effect = [22, 80] + [None] * 12 # Simulate open ports 22, 80, rest closed

        target = "192.0.2.1"
        results = await self.scanner._scan_domain_or_ip_async(target)

        self.assertNotIn("whois", results) # WHOIS should be skipped for IP
        self.assertNotIn("dns", results) # DNS should be skipped for IP
        self.assertIn("open_ports", results)
        self.assertListEqual(results["open_ports"], [22, 80])

    @patch('modules.domain_ip_scanner.whois')
    @patch('modules.domain_ip_scanner.aiodns') # Patch aiodns module directly
    @patch('whois.parser.PywhoisError')
    async def test_scan_domain_or_ip_async_whois_error(self, mock_pywhois_error, mock_aiodns, mock_whois):
        # Mock DNS Resolver to prevent actual lookups
        mock_resolver_instance = mock_aiodns.DNSResolver.return_value
        mock_resolver_instance.query = AsyncMock(return_value=[]) # Return empty list for DNS queries

        mock_whois.whois.side_effect = PywhoisError("WHOIS parse error")
        with self.assertRaises(ParsingError) as cm:
            await self.scanner._scan_domain_or_ip_async("example.com")
        self.assertIn("WHOIS parsing error", str(cm.exception))

    @patch.object(DomainIPScanner, '_scan_domain_or_ip_async', new_callable=AsyncMock)
    async def test_domain_ip_scanner_scan(self, mock_scan_domain_or_ip_async):
        mock_scan_domain_or_ip_async.return_value = {"test": "data"}

        target = "test.com"
        results = await self.scanner.scan(target)

        self.assertEqual(results, {"test": "data"})
        # Assert on the mock_progress object directly
        self.mock_progress.update.assert_any_call(self.scanner.task_id, description=f"[bold yellow]Analyzing domain/IP: {target}...[/bold yellow]")
        self.mock_progress.update.assert_any_call(self.scanner.task_id, advance=1)
        self.mock_progress.update.assert_any_call(self.scanner.task_id, description=f"[bold green]Domain/IP analysis for {target} complete.[/bold green]")


if __name__ == '__main__':
    unittest.main()
