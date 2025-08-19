"""
This module is responsible for generating the HTML report for the OSINT Tool.

It uses the Jinja2 templating engine to create a modern and visually appealing
report that can be viewed in any web browser. The report is generated from a
template file and populated with the scan results.

Key functionalities include:
    - Loading the HTML template from the file system.
    - Rendering the template with the scan results and other context data.
    - Saving the rendered HTML to a file with a user-specified name.
    - Handling potential errors during the template rendering or file I/O.

By separating the HTML reporting logic, we can easily update the design and
layout of the report without affecting the core application logic.
"""

import os
import logging
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateError

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def save_html_report(results: Dict[str, Any], filename: str):
    """Saves a modern HTML report using Jinja2 template."""
    logger.info(f"Saving HTML report to {filename}...")
    try:
        target_id = results.get("_target_input", "Unknown Target")
        scan_results_only = {k: v for k, v in results.items() if k not in ["_target_input", "osint_keywords"]}

        template = jinja_env.get_template("report_template.html")
        rendered_html = template.render(
            results=scan_results_only,
            target_id=target_id,
            osint_keywords=results.get("osint_keywords", {})
        )
        with open(filename, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        logger.info(f"HTML report saved successfully to {filename}")
    except TemplateNotFound as e:
        logger.error(f"HTML report template not found: {e}")
    except TemplateError as e:
        logger.error(f"Error rendering HTML report template: {e}")
    except IOError as e:
        logger.error(f"File I/O error saving HTML report to {filename}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving HTML report to {filename}: {e}")
