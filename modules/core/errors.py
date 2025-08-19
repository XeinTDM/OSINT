from modules.core.exceptions import ScannerError

class NetworkError(ScannerError):
    """Exception raised for network-related issues during scanning."""
    pass

class APIError(ScannerError):
    """Exception raised for issues with API responses or authentication."""
    pass

class ParsingError(ScannerError):
    """Exception raised when there are issues parsing data from a source."""
    pass

class RateLimitError(APIError):
    """Exception raised when an API rate limit is hit."""
    pass

class AuthenticationError(APIError):
    """Exception raised for authentication failures with an API."""
    pass
