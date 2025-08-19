class ScannerError(Exception):
    """Custom exception for scanner-related errors."""
    def __init__(self, message: str, scanner_name: str, original_exception: Exception = None):
        super().__init__(message)
        self.scanner_name = scanner_name
        self.original_exception = original_exception

    def __str__(self):
        if self.original_exception:
            return f"[{self.scanner_name} Error]: {self.args[0]} (Original: {type(self.original_exception).__name__} - {self.original_exception})"
        return f"[{self.scanner_name} Error]: {self.args[0]}"
