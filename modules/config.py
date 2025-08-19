class Config:
    HIBP_API_KEY = None
    TWITTER_BEARER_TOKEN = None
    BASIC_CHECK_CONCURRENCY = 4
    DYNAMIC_CHECK_CONCURRENCY = 2
    PORT_SCAN_TIMEOUT = 1.0 # Seconds
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    DISABLE_SSL_VERIFICATION = True
    PLAYWRIGHT_TIMEOUT = 90000
    PLAYWRIGHT_WAIT_UNTIL = "domcontentloaded" # "load", "domcontentloaded", "networkidle", "commit"
