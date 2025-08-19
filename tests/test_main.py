import unittest
from unittest.mock import patch
from io import StringIO
import sys

sys.path.append(".")
from main import print_banner


class TestMain(unittest.TestCase):
    def test_print_banner(self):
        with patch("sys.stdout", new=StringIO()) as fake_out:
            print_banner()
            self.assertIn("OSINT-Tool", fake_out.getvalue())


if __name__ == "__main__":
    unittest.main()
