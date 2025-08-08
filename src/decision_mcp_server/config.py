"""Configuration settings for the ODM Decision MCP Server.

This module contains configuration settings for the ODM Decision MCP Server.
"""

import os
from pathlib import Path

# Transport protocol
TRANSPORT = os.environ.get("DECISION_MCP_TRANSPORT", "stdio")


# Security settings
SECURITY_MODE = os.environ.get("DECISION_MCP_SECURITY_MODE", "strict")
SECURITY_CONFIG_PATH = os.environ.get("DECISION_ODM_MCP_SECURITY_CONFIG", "")

# Instructions displayed to client during initialization
INSTRUCTIONS = """
Welcome to the ODM Decision MCP Server!
This server provides access to decision services for operational decision management.
You can invoke decision services using the provided tools.
For more information, please refer to the documentation.
"""

# Application paths
BASE_DIR = Path(__file__).parent.parent.parent