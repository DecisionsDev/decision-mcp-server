from . import DecisionMCPServer

import asyncio
import sys

def main():
    """Main entry point for the package."""
    # Skip argument parsing when running tests
    if 'pytest' in sys.modules:
        return
    asyncio.run(DecisionMCPServer.main())

# Optionally expose other important items at package level
__all__ = ['main', 'DecisionMCPServer', 'DecisionServerManager', 'Credentials', "DecisionServiceDescription"]