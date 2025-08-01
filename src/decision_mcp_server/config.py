"""Configuration settings for the ODM Decision MCP Server.

This module contains configuration settings for the ODM Decision MCP Server.

Environment variables:
- AWS_MCP_TIMEOUT: Custom timeout in seconds (default: 300)
- AWS_MCP_MAX_OUTPUT: Maximum output size in characters (default: 100000)
- AWS_MCP_TRANSPORT: Transport protocol to use ("stdio" or "sse", default: "stdio")
- AWS_PROFILE: AWS profile to use (default: "default")
- AWS_REGION: AWS region to use (default: "us-east-1")
- AWS_DEFAULT_REGION: Alternative to AWS_REGION (used if AWS_REGION not set)
- AWS_MCP_SECURITY_MODE: Security mode for command validation (strict or permissive, default: strict)
- AWS_MCP_SECURITY_CONFIG: Path to custom security configuration file
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