import asyncio
import json
from typing import Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
import logging

from decision_mcp_server.DecisionServiceDescription import DecisionServiceDescription
from decision_mcp_server.Credentials import Credentials
from decision_mcp_server.DecisionServerManager import DecisionServerManager
from decision_mcp_server.config import INSTRUCTIONS, BASE_DIR
from decision_mcp_server.ExecutionToolTrace import ExecutionToolTrace, DiskTraceStorage
import argparse
import os

class DecisionMCPServer:
    def __init__(self, credentials: Credentials, traces_dir: Optional[str] = None, trace_enable: bool = False, trace_maxsize: int = 50):
        self.notes: dict[str, str] = {}
        self.repository: dict[str, DecisionServiceDescription] = {}
        
        # Store trace configuration
        self.trace_enable = trace_enable
        self.trace_maxsize = trace_maxsize
        
        # Set up trace storage with configured parameters if tracing is enabled
        # If traces_dir is None, DiskTraceStorage will use the default path in user's home directory
        if self.trace_enable:
            self.execution_traces = DiskTraceStorage(storage_dir=traces_dir, max_traces=self.trace_maxsize)
        else:
            self.execution_traces = None
            logging.info("Trace storage is disabled")
        
        self.server = Server("decision-mcp-server")
        self.manager = None
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
        # Ensure manager is initialized before using it
        if self.manager is None:
            self.manager = DecisionServerManager(credentials=self.credentials)
            
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
        # Ensure manager is initialized before using it
        if self.manager is None:
            self.manager = DecisionServerManager(credentials=self.credentials)
            
        result = self.manager.invokeDecisionService(
            rulesetPath=self.repository[name].rulesetPath,
            decisionInputs=arguments
        )

        # Extract decision ID and trace if available
        decision_id = None
        decision_trace = None
        
        # Handle dictionary response
        if isinstance(result, dict):
            if result.get("__DecisionID__") is not None:
                decision_id = result["__DecisionID__"]
                del result["__DecisionID__"]
            if result.get("__DecisionTrace__") is not None:
                # Ensure decision_trace is a dictionary
                trace_value = result["__DecisionTrace__"]
                if isinstance(trace_value, dict):
                    decision_trace = trace_value
                elif isinstance(trace_value, str):
                    # Try to parse JSON string to dict
                    try:
                        decision_trace = json.loads(trace_value)
                    except json.JSONDecodeError:
                        # If not valid JSON, store as dict with original string
                        decision_trace = {"raw_trace": trace_value}
                else:
                    # For any other type, convert to a dictionary
                    decision_trace = {"value": str(trace_value)}
                
                del result["__DecisionTrace__"]
                
            response_text = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            # Handle non-dict response (string, etc)
            response_text = str(result)

        # Create and store execution trace if tracing is enabled
        if self.trace_enable and self.execution_traces is not None:
            trace = ExecutionToolTrace(
                tool_name=name,
                ruleset_path=self.repository[name].rulesetPath,
                inputs=arguments or {},
                results=result,
                decision_id=decision_id,
                decision_trace=decision_trace
            )
            trace_id = self.execution_traces.add(trace)
            
            # Log the creation of the trace
            logging.info(f"Created execution trace with ID: {trace_id}")
        else:
            logging.debug("Trace storage is disabled, not creating execution trace")

        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]
        
    # Add a new method to list execution traces
    async def list_execution_traces(self) -> list[types.Resource]:
        """Return a list of execution traces as resources."""
        if not self.trace_enable or self.execution_traces is None:
            logging.info("Trace storage is disabled, returning empty list")
            return []
            
        trace_metadata = self.execution_traces.get_all_metadata()
        return [
            types.Resource(
                uri=AnyUrl(f"trace://{metadata['id']}"),
                name=f"Execution Trace: {metadata['tool_name']}",
                description=f"Trace executed at {metadata['timestamp']}",
                mimeType="application/json",
            )
            for metadata in trace_metadata
        ]
    
    # Add a method to get a specific execution trace
    async def get_execution_trace(self, trace_id: str) -> Optional[ExecutionToolTrace]:
        """Get a specific execution trace by ID."""
        if not self.trace_enable or self.execution_traces is None:
            logging.info("Trace storage is disabled, cannot retrieve trace")
            return None
            
        return self.execution_traces.get(trace_id)

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
    parser.add_argument("--token_url", type=str, default=os.getenv("TOKEN_URL"), help="OpenID Connect token endpoint URL (optional)")
    parser.add_argument("--scope", type=str, default=os.getenv("SCOPE", "openid"), help="OpenID Connect scope using when requesting an access token using Client Credentials (optional)")
    parser.add_argument("--verifyssl", type=str, default=os.getenv("VERIFY_SSL", "True"), choices=["True", "False"], help="Disable SSL check. Default is True (SSL verification enabled).")
    parser.add_argument("--ssl_cert_path", type=str, default=os.getenv("SSL_CERT_PATH"), help="Path to the SSL certificate file. If not provided, defaults to system certificates.")
    
    # Logging-related arguments
    parser.add_argument("--log-level", type=str, default=os.getenv("LOG_LEVEL", "INFO"),
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level (default: INFO)")
    
    # Trace-related arguments
    parser.add_argument("--traces-dir", type=str, default=os.getenv("TRACES_DIR"), help="Directory to store execution traces (optional). If not provided, traces will be stored in the 'traces' directory in the project root.")
    parser.add_argument("--trace-enable", action="store_true", default=(os.getenv("TRACE_ENABLE", "False").lower() == "true"), help="Enable trace storage (default: False)")
    parser.add_argument("--trace-maxsize", type=int, default=int(os.getenv("TRACE_MAXSIZE", "50")), help="Maximum number of traces to store (default: 50)")
            

    return parser.parse_args()

def create_credentials(args):
    verifyssl = args.verifyssl != "False"

    if args.zenapikey:  # If zenapikey is provided, use it for authentication
        return Credentials(
            odm_url=args.url,
            odm_url_runtime=args.runtime_url,
            username=args.username,
            zenapikey=args.zenapikey,
            ssl_cert_path=args.ssl_cert_path,
            verify_ssl=verifyssl
        )
    elif args.client_id:  # If OpenID credentials are provided, use them for authentication
        return Credentials(
            odm_url=args.url,
            odm_url_runtime=args.runtime_url,
            token_url=args.token_url,
            scope=args.scope,
            client_id=args.client_id,
            client_secret=args.client_secret,
            ssl_cert_path=args.ssl_cert_path,
            verify_ssl=verifyssl
        )
    else:  # Default to basic authentication
        if not args.username or not args.password:
            raise ValueError("Username and password must be provided for basic authentication.")
        return Credentials(
            odm_url=args.url,
            odm_url_runtime=args.runtime_url,
            username=args.username,
            password=args.password,
            ssl_cert_path=args.ssl_cert_path,
            verify_ssl=verifyssl
        )
async def main():
    """Main entry point for the Decision MCP Server."""
    args = parse_arguments()
    
    # Configure logging with the specified level
    try:
        logging_level = getattr(logging, args.log_level)
    except AttributeError:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.warning(f"Invalid log level '{args.log_level}' specified. Falling back to INFO.")
        logging_level = logging.INFO
    else:
        logging.basicConfig(
            level=logging_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    logging.info(f"Logging level set to: {logging.getLevelName(logging_level)}")
    
    credentials = create_credentials(args)
    server = DecisionMCPServer(
        credentials=credentials,
        traces_dir=args.traces_dir,
        trace_enable=args.trace_enable,
        trace_maxsize=args.trace_maxsize
    )
    await server.start()