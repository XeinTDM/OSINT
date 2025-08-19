"""
This module provides utility functions that are used across the OSINT Tool.

These functions are general-purpose and do not fit into a specific domain,
but they provide essential functionalities like printing a banner or other
helper tasks that can be shared among different parts of the application.

By centralizing these utilities, we can avoid code duplication and make it
easier to maintain and update these common functions.
"""

def print_banner():
    """Prints the application banner."""
    banner_text = """
██████╗ ███████╗██╗███╗   ██╗████████╗
██╔══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██████╔╝███████╗██║██╔██╗ ██║   ██║   
██╔═══╝ ╚════██║██║██║╚██╗██║   ██║   
██║     ███████║██║██║ ╚████║   ██║   
╚═╝     ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═══╝   
    """
    print(banner_text)
    print("=============================================")
    print("        OSINT-Tool - by @snorreks")
    print("=============================================")
    print()
