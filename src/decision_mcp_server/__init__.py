
from . import DecisionMCPServer

import asyncio

def main():
    """Main entry point for the package."""
    asyncio.run(DecisionMCPServer.main())

# Optionally expose other important items at package level
__all__ = ['main', 'DecisionMCPServer', 'DecisionServerManager', 'Credentials']