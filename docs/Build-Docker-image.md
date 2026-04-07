# Docker image build Guide

You can build a Docker image running the IBM ODM Decision MCP server, which can be useful to run the MCP server remotely.

## Building

- Clone this repository, and set the current directory to the root folder (which contains the `Dockerfile`)
    ```bash
    git clone https://github.com/DecisionsDev/ibm-odm-decision-mcp-server.git
    cd ibm-odm-decision-mcp-server
    ```

- Build the image

    You can either build an image based on a Python official image in Docker Hub or on a Red Hat UBI image.
    - using the Python official image:
    ```bash
    docker compose build ibm-odm-decision-mcp-server
    ```
    - using the Red Hat UBI image:
    ```bash
    docker compose build ibm-odm-decision-mcp-server-ubi
    ```

## Testing with ODM for Developer

- Run the command below to test the Docker image (built using the Python official image) on your laptop (This command starts two containers: ODM for Developer and Decision MCP server):
    ```bash
    export ODM_PASSWORD="resDeployer"
    docker compose up -d ibm-odm-decision-mcp-server
    ```

- To check the logs of the Decision MCP server, run:
    ```bash
    docker compose logs ibm-odm-decision-mcp-server
    ```

    You should see:
    ```
    2026-03-05 08:37:49 - root - INFO - Running Python sys.version_info(major=3, minor=14, micro=3, releaselevel='final', serial=0). Logging level set to: INFO
    2026-03-05 08:37:49 - decisioncenter_mcp_server.DecisionCenterManager - INFO - Connected with rtsAdministrator role
    2026-03-05 08:37:49 - decisioncenter_mcp_server.DecisionCenterManager - INFO - Parsing http://odm:9060/decisioncenter-api/v3/api-docs
    2026-03-05 08:37:51 - decisioncenter_mcp_server.DecisionCenterManager - INFO - successfully retrieved Decision Center REST API openapi
    2026-03-05 08:37:52 - decisioncenter_mcp_server.DecisionCenterManager - INFO - Decision Center REST API openapi parsing successful
    2026-03-05 08:37:52 - decisioncenter_mcp_server.DecisionCenterManager - INFO - Successfully generated the MCP tools for the Decision Center REST API
    2026-03-05 08:37:52 - decisioncenter_mcp_server.DecisionCenterManager - INFO - Retrieving http://odm:9060/res/apiauth/v1/DecisionServer.wadl
    2026-03-05 08:37:53 - decisioncenter_mcp_server.DecisionCenterManager - INFO - successfully retrieved the RES console REST API WADL
    2026-03-05 08:37:53 - decisioncenter_mcp_server.DecisionCenterManager - INFO - Connected with the resDeployer role
    2026-03-05 08:37:53 - decisioncenter_mcp_server.DecisionCenterManager - INFO - Successfully generated the MCP tools for the RES Console REST API
    INFO:     Started server process [1]
    INFO:     Waiting for application startup.
    2026-03-05 08:37:53 - mcp.server.streamable_http_manager - INFO - StreamableHTTP session manager started
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
    ```

- Configure an AI agent tool running on your laptop such as Claude Desktop, IBM Bob or VS Code to use the Decision MCP server

    - refer to [Claude Desktop integration guide](./Claude-desktop-integration-guide.md#step-4-configure-claude-desktop) or [IBM Bob integration guide](./IBM-Bob-integration-guide.md#configure-ibm-bob) to find the MCP configuration file

    - edit the configuration file and replace its content by:
        ```json
        {
            "mcpServers": {
                "ibm-odm-decision-mcp-server": {
                    "command": "npx",
                    "args": ["mcp-remote", "http://localhost:3001/mcp", "--allow-http"]
                }
            }
        }
        ```

- Start the AI agent and try a few prompts (you can find examples in the guides above).

- To stop both containers, run:
    ```bash
    docker compose --profile ibm-odm-decision-mcp-server down
    ```
