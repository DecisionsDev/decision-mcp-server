import asyncio

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
import logging
from .Credentials import Credentials
from .DecisionServerManager import DecisionServerManager
import argparse
# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

server = Server("decision-mcp-server")

parser = argparse.ArgumentParser(description="Decision MCP Server")
parser.add_argument("--odm-url", type=str, default="http://localhost:9060/res", help="ODM service URL")
parser.add_argument("--username", type=str, default="odmAdmin", help="ODM username (optional)")
parser.add_argument("--password", type=str, default="odmAdmin", help="ODM password (optional)")
args, unknown = parser.parse_known_args()

credentials = Credentials(
    odm_url=args.odm_url,
    username=args.username,
    password=args.password
)
manager = DecisionServerManager(
         credentials=credentials
     )

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available note resources.
    Each note is exposed as a resource with a custom note:// URI scheme.
    """
    return [
        types.Resource(
            uri=AnyUrl(f"note://internal/{name}"),
            name=f"Note: {name}",
            description=f"A simple note named {name}",
            mimeType="text/plain",
        )
        for name in notes
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific note's content by its URI.
    The note name is extracted from the URI host component.
    """
    if uri.scheme != "note":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    name = uri.path
    if name is not None:
        name = name.lstrip("/")
        return notes[name]
    raise ValueError(f"Note not found: {name}")

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
    logging.info("Using ODM URL: %s", args.odm_url)
    return [
        types.Tool(
            name="vacation",
            description="retrieve the number of vacation days per year for a given employee and his hiring date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hiringDate": {"type": "string", "description":"The hiring date with this format 'yyyy-mm-dd'"},
                },
                "required": ["hiringDate"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    logging.info("Calling ODM tools")
    if name != "vacation":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments:
        raise ValueError("Missing arguments")

    hiring_date = arguments.get("hiringDate")
  
    if not hiring_date :
        raise ValueError("Missing hiring_date argument")

    # TODO Implement the ressource logic
    # Update server state
#    notes[note_name] = content

    # Notify clients that resources have changed
#   await server.request_context.session.send_resource_list_changed()
    result =  manager.invokeDecisionService(
         rulesetPath='/hr_decision_service/1.0/number_of_timeoff_days/1.3',
         decisionInputs={ "hiringDate": hiring_date}
     )
    return [
        types.TextContent(
            type="text",
            text=result.get('timeoffDays', 'No vacation days found') ,
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
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )