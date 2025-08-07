import asyncio
import json
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
import logging
from decision_mcp_server.Credentials import Credentials
from decision_mcp_server.DecisionServerManager import DecisionServerManager
from decision_mcp_server.config import INSTRUCTIONS
import argparse
import os

class DecisionMCPServer:
    def __init__(self,credentials: Credentials):
        self.notes: dict[str, str] = {}
        self.repository: dict[str, DecisionServiceDescription] = {}
        self.server = Server("decision-mcp-server")
        self.manager = None,
        self.credentials = credentials
        

    async def list_resources(self) -> list[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl(f"decisionservice://internal/{name}"),
                name=f"DecisionService: {name}",
                description=f"Decision Service: {name}",
                mimeType="text/plain",
            )
            for name in self.repository.keys()
        ]

    async def read_resource(self, uri: AnyUrl) -> str:
        if uri.scheme != "decisionservice":
            raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

        name = uri.path
        if name is not None:
            name = name.lstrip("/")
            return str(self.repository[name].__dict__)
        raise ValueError(f"DecisionService not found: {name}")

    async def list_tools(self) -> list[types.Tool]:
        logging.info("Listing ODM tools")
        rulesets = self.manager.fetch_rulesets()
        extractedTools = self.manager.generate_tools_format(rulesets)
        tools = []
        for decisionService in extractedTools:   
            tool_info = decisionService.tool_description
            tools.append(tool_info)
            self.repository[decisionService.tool_name] = decisionService
        return tools

    async def call_tool(self, name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if self.repository.get(name) is None:
            logging.error("Tool not found: %s", name)
            raise ValueError(f"Unknown tool: {name}")

        logging.info("Invoking decision service for tool: %s with arguments: %s", name, arguments)
        result = self.manager.invokeDecisionService(
            rulesetPath=self.repository[name].rulesetPath,
            decisionInputs=arguments
        )

        # Handle dictionary response
        if isinstance(result, dict):
            if result.get("__DecisionID__") is not None:
                del result["__DecisionID__"]
            response_text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            # Handle non-dict response (string, etc)
            response_text = str(result)

        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]

    async def start(self):

        self.manager = DecisionServerManager(credentials=self.credentials)

        # Register handlers
        self.server.list_resources()(self.list_resources)
        self.server.read_resource()(self.read_resource)
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="decision-mcp-server",
                    server_version="0.2.0",
                    instructions=INSTRUCTIONS,
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

def parse_arguments():
    parser = argparse.ArgumentParser(description="Decision MCP Server")
    parser.add_argument("--url", type=str, default=os.getenv("ODM_URL", "http://localhost:9060/res"), help="ODM service URL")

    parser.add_argument("--runtime-url", type=str, default=os.getenv("ODM_RUNTIME_URL"), help="ODM service URL")
    parser.add_argument("--username", type=str, default=os.getenv("ODM_USERNAME", "odmAdmin"), help="ODM username (optional)")
    parser.add_argument("--password", type=str, default=os.getenv("ODM_PASSWORD", "odmAdmin"), help="ODM password (optional)")
    parser.add_argument("--zenapikey", type=str, default=os.getenv("ZENAPIKEY"), help="Zen API Key (optional)")
    parser.add_argument("--client_id", type=str, default=os.getenv("CLIENT_ID"), help="OpenID Client ID (optional)")
    parser.add_argument("--client_secret", type=str, default=os.getenv("CLIENT_SECRET"), help="OpenID Client Secret (optional)")
    parser.add_argument("--verifyssl", type=str, default=os.getenv("VERIFY_SSL", "True"), choices=["True", "False"], help="Disable SSL check. Default is True (SSL verification enabled).")
            

    return parser.parse_args()

def create_credentials(args):
    verifyssl = args.verifyssl != "False"

    if args.zenapikey:  # If zenapikey is provided, use it for authentication
        return Credentials(
            odm_url=args.url,
            odm_url_runtime=args.runtime_url,
            username=args.username,
            zenapikey=args.zenapikey,
            verify_ssl=verifyssl
        )
    elif args.client_id:  # If OpenID credentials are provided, use them for authentication
        return Credentials(
            odm_url=args.url,
            odm_url_runtime=args.runtime_url,
            client_id=args.client_id,
            client_secret=args.client_secret,  # Changed from client_secrets to client_secret
            verify_ssl=verifyssl
        )
    else:  # Default to basic authentication
        if not args.username or not args.password:
            raise ValueError("Username and password must be provided for basic authentication.")
        return Credentials(
            odm_url=args.url,
            username=args.username,
            password=args.password,
            verify_ssl=verifyssl
        )
async def main():
    """Main entry point for the Decision MCP Server."""
    args = parse_arguments()
    credentials = create_credentials(args)
    server = DecisionMCPServer(credentials=credentials)
    await server.start()