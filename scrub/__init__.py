"""Top-level package for SCRUB."""

__author__ = """Lyle Barner"""
__email__ = 'lyle.barner@jpl.nasa.gov'
__version__ = '2.4.0'

# Check the Python version for compatibility
import sys
if not sys.version_info >= (3, 6):
    print('ERROR: Python version 3.6 or greater is required to run SCRUB')
    sys.exit(100)
