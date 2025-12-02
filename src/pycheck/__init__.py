"""pycheck

A simple, dynamic sanity-check library for Python distributions.

Usage:
    import pycheck
    
    result = pycheck.doSanityCheck(pycheck.OS)
    if result:
        print("OS Library is good")

    result = pycheck.doSanityCheck(pycheck.ALL)
    if result:
        print(result + " Libraries are fine!")
"""

from .checker import doSanityCheck, OS, ALL, SPECIFIC, check_filesystem_access, check_ssl_support

__all__ = [
    "doSanityCheck",
    "OS",
    "ALL",
    "SPECIFIC",
    "check_filesystem_access",
    "check_ssl_support",
]

__author__ = "Aubrey"
__license__ = "MIT"
__version__ = "0.1.2"
