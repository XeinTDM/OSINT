# OSINT-Tool

OSINT-Tool is a powerful and versatile open-source intelligence (OSINT) tool designed to streamline the process of gathering and analyzing information from various public sources. It provides a user-friendly command-line interface (CLI) that allows you to conduct scans for usernames, email addresses, social media profiles, domain/IP information, and phone numbers.

## Features

- **Username Scanning:** Searches for a specific username across a wide range of online platforms and social media sites.
- **Email Scanning:** Gathers information related to an email address, including associated accounts and data breaches.
- **Social Media Scanning:** Retrieves detailed profile information from popular social media platforms like Twitter.
- **Domain/IP Analysis:** Performs a comprehensive analysis of a domain or IP address, including WHOIS lookups, DNS records, and open ports.
- **Phone Number Analysis:** Provides information about a phone number, such as its carrier and location.
- **Comprehensive Reporting:** Generates detailed reports in both JSON and HTML formats, providing a clear and organized summary of the scan results.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/OSINT-Tool.git
   cd OSINT-Tool
   ```

2. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the environment variables:**

   Create a `.env` file in the root directory of the project and add the following environment variables:

   ```
   HIBP_API_KEY=your_have_i_been_pwned_api_key
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   ```

   Replace `your_have_i_been_pwned_api_key` and `your_twitter_bearer_token` with your actual API keys.

## Usage

To start the OSINT-Tool, run the following command:

```bash
python main.py
```

The tool will guide you through an interactive command-line interface (CLI) where you can select the scans you want to perform and provide the necessary input.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more information.
