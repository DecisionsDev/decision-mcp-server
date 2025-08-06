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
from decision_mcp_server.DecisionServiceDescription import DecisionServiceDescription
import argparse
import os
# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}
repository: dict[str,DecisionServiceDescription] = {}


parser = argparse.ArgumentParser(description="Decision MCP Server")
parser.add_argument("--url", type=str, default=os.getenv("ODM_URL", "http://localhost:9060/res"), help="ODM service URL")

parser.add_argument("--runtime-url", type=str, default=os.getenv("ODM_RUNTIME_URL", "http://localhost:9060/DecisionService"), help="ODM service URL")
parser.add_argument("--username", type=str, default=os.getenv("ODM_USERNAME", "odmAdmin"), help="ODM username (optional)")
parser.add_argument("--password", type=str, default=os.getenv("ODM_PASSWORD", "odmAdmin"), help="ODM password (optional)")
parser.add_argument("--zenapikey", type=str, default=os.getenv("ZENAPIKEY"), help="Zen API Key (optional)")
parser.add_argument("--bearertoken", type=str, default=os.getenv("BEARER"), help="OpenID Bearer token (optional)")
parser.add_argument("--verifyssl", type=str,default=os.getenv("VERIFY_SSL", "True"), choices=["True", "False"], help="Disable SSL check. Default is True (SSL verification enabled).")
            

args, unknown = parser.parse_known_args()
verifyssl = True
if args.verifyssl:
    if args.verifyssl == "False":
        verifyssl = False

args = parser.parse_args()
#logging.info("Parsed arguments: %s", str(args))
if args.zenapikey:  # If zenapikey is provided, use it for authentication
    credentials = Credentials(
        odm_url=args.url,
        odm_url_runtime=args.runtime_url,
        username=args.username,
        zenapikey=args.zenapikey,
        verify_ssl=verifyssl
    )
elif args.bearertoken:  # If bearer token is provided, use it for authentication
    credentials = Credentials(
        odm_url=args.url,
        odm_url_runtime=args.runtime_url,
        bearer_token=args.bearertoken,
        verify_ssl=verifyssl
    )
else:  # Default to basic authentication if no zenapikey or bearer token is provided
    if not args.username or not args.password:
        raise ValueError("Username and password must be provided for basic authentication.")
    if not args.url:
        raise ValueError("ODM URL must be provided.")
    if not args.runtime_url:
        args.runtime_url = args.url # Default runtime URL to ODM URL if not specified
    credentials = Credentials( 
        odm_url=args.url,
        username=args.username,
        password=args.password,
        verify_ssl=verifyssl
    )
manager = DecisionServerManager(
         credentials=credentials
     )

server = Server("decision-mcp-server")
@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available note resources.
    Each note is exposed as a resource with a custom note:// URI scheme.
    """
    return [

        types.Resource(
            uri=AnyUrl(f"decisionservice://internal/{name}"),
            name=f"DecisionService: {name}",
            description=f"Decision Service: {name}",
            mimeType="text/plain",
        )
        for name in repository.keys()
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific note's content by its URI.
    The note name is extracted from the URI host component.
    """
    if uri.scheme != "decisionservice":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    name = uri.path
    if name is not None:
        name = name.lstrip("/")
        return str(repository[name].__dict__)
    raise ValueError(f"DecisonService not found: {name}")

@server.list_prompts()  
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    The prompt includes all current notes and can be customized via arguments.
    """
    if name != "summarize-notes":
        raise ValueError(f"Unknown prompt: {name}")

    style = (arguments or {}).get("style", "brief")
    detail_prompt = " Give extensive details." if style == "detailed" else ""

    return types.GetPromptResult(
        description="Summarize the current notes",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
                    + "\n".join(
                        f"- {name}: {content}"
                        for name, content in notes.items()
                    ),
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    logging.info("Listing ODM tools")
    logging.info("Using ODM URL: %s", args.url)

    rulesets = manager.fetch_rulesets()
    extractedTools = manager.generate_tools_format(rulesets)
    tools = []
    for decisionService in extractedTools:   
        tool_info = decisionService.tool_description
        tools.append(tool_info)
        repository[decisionService.tool_name]=decisionService
    return tools
    

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    logging.info("Calling ODM tools")
    if repository.get(name)==None:
        logging.error("Tool not found: %s", name)
        raise ValueError(f"Unknown tool: {name}")


    # Notify clients that resources have changed
#    await server.request_context.session.send_resource_list_changed()
    logging.info("Invoking decision service for tool: %s with arguments: %s", name, arguments)
    result =  manager.invokeDecisionService(
         rulesetPath=repository[name].rulesetPath,
         decisionInputs=arguments
     )
    if result.get("__DecisionID__") is not None:
         del result["__DecisionID__"]
    return [
        types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False) if isinstance(result, dict) else str(result)
        )
    ]

async def main():
    
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="decision-mcp-server",
                server_version="0.1.0",
                instructions=INSTRUCTIONS,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )