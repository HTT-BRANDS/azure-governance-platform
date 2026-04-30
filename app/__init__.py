"""HTT Control Tower.

A lightweight, cost-effective platform for managing Azure/M365 governance
across multiple tenants with focus on cost optimization, compliance,
resource management, and identity governance.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("control-tower")
except PackageNotFoundError:
    # Package not installed (e.g., running from source without install)
    __version__ = "2.5.0"

__author__ = "HTT Control Tower Team"
