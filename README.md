# OSINT: Open-Source Intelligence Acquisition Framework

A precision instrument for systematic data acquisition and analysis from public sources.

## Overview

This framework is engineered for the efficient and structured collection of open-source intelligence (OSINT). It automates the extraction of publicly available data, transforming disparate information into actionable intelligence. Designed for the discerning analyst, it prioritizes data integrity, operational efficiency, and modular extensibility.

## Core Principles

*   **Data-Centricity**: Every component is optimized for the accurate and reliable acquisition of information.
*   **Modularity**: A decoupled architecture facilitates independent development and integration of scanning modules.
*   **Efficiency**: Asynchronous operations and optimized data handling minimize resource consumption and maximize throughput.
*   **Integrity**: Data models enforce strict validation, ensuring the consistency and reliability of acquired intelligence.

## Features

*   **Username Scanning**: Identify presence across a multitude of platforms.
*   **Full Name Scanning**: Correlate identities across national and international data repositories.
*   **Domain & IP Analysis**: Uncover network footprints and associated entities.
*   **Email & Phone Number Validation**: Verify contact points and associated data.
*   **Social Media Profiling**: Extract public data from designated social platforms.
*   **Structured Reporting**: Generate comprehensive reports in various formats (CLI, HTML, JSON).
*   **Dynamic Site Definitions**: Update intelligence sources from remote repositories.
*   **Robust Data Validation**: Pydantic-driven schema enforcement for all acquired site definitions.

## Installation

To deploy this framework, ensure Python 3.8+ and `pip` are installed.

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/XeinTDM/OSINT.git
    cd OSINT
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Playwright requires additional browser binaries. Execute `playwright install` after `pip install` if dynamic web scanning is intended.*

## Usage

Execute the primary script to initiate the interactive command-line interface:

```bash
python main.py
```

The system will present a menu for selecting desired scanning operations. Input is processed for optimal data acquisition.

## Data Management

The framework relies on external JSON files for defining intelligence sources:

*   `data/sites.json`: Defines sources for username scanning.
*   `data/full_name_sites.json`: Defines sources for full name correlation, often country-specific.

Upon initial execution, these files are either loaded from local storage or, if absent/empty, are initialized with default structures. The system will then attempt to synchronize these definitions with remote repositories to ensure access to the most current intelligence sources.

All site definitions are rigorously validated against Pydantic schemas, guaranteeing data integrity and preventing operational anomalies due to malformed source configurations.

## Development & Contribution

Contributions are evaluated based on their adherence to the framework's core principles and their capacity to enhance its analytical capabilities.

1.  **Code Style**: Adhere to `ruff` standards.
2.  **Testing**: Implement comprehensive unit and integration tests using `pytest`.
3.  **Extensibility**: Design modules for clear separation of concerns and minimal interdependency.

To execute tests:
```bash
pytest
```

## License

This project is distributed under the MIT License. Refer to the `LICENSE` file for complete terms.