# Docker image build Guide

The repository features a [Dockerfile](/Dockerfile) so that you can build a Docker image running the IBM ODM Management MCP server, which can be useful to run the MCP server remotely.

## Build

- Clone this repository, and set the current directory to the root folder (which contains the `Dockerfile`)
    ```bash
    git clone https://github.com/DecisionsDev/ibm-odm-management-mcp-server.git
    cd ibm-odm-management-mcp-server
    ```

- Build the image
    ```bash
    docker build --no-cache -t management-mcp-server:latest .
    ```

## Test with ODM for Developer

Follow the instructions below to test the Docker image on your laptop:

- Start an ODM for Developer Docker container
    ```bash
    docker compose up &
    ```
    >Note:
    >This creates a Docker network named `ibm-odm-management-mcp-server_default` (the name of the network is made of the current directory name and the `_default` suffix).
    >
    >This Docker network is used at the next step so that the Management MCP server can communicate with ODM.

- Start a Management MCP server container
    ```bash
    docker run -t --rm --name management-mcp-server -p 3000:3000 --network ibm-odm-management-mcp-server_default management-mcp-server:latest
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

- Configure an AI agent tool running on your laptop such as Claude Desktop, IBM Bob or VS Code to use the Management MCP server

    - refer to [Claude Desktop integration guide](./Claude-desktop-integration-guide.md#step-4-configure-claude-desktop) or [IBM Bob integration guide](./IBM-Bob-integration-guide.md#configure-ibm-bob) to edit the MCP configuration file

    - use the configuration below:
        ```json
        {
            "mcpServers": {
                "ibm-odm-management-mcp-server": {
                    "command": "npx",
                    "args": ["mcp-remote", "http://localhost:3000/mcp", "--allow-http"]
                }
            }
        }
        ```

- Start the AI agent and try a few prompts. See the examples in the guides above.

## Passing MCP server arguments

In the previous section the `docker run` does not contain any MCP argument because the [Dockerfile](/Dockerfile#L35) defines all the arguments suitable to communicate with the ODM for developer Docker container (and run in remote mode) by default:
```
CMD ["--transport", "streamable-http", "--url", "http://odm:9060/decisioncenter-api", "--res-url", "http://odm:9060/res"]
```

To communicate with a different instance of ODM, add the relevant MCP arguments at the end of the `docker run` command.

Here is an example with Basic Authentication:
```bash
docker run \
    -t --rm -p 3000:3000 \
    --name management-mcp-server \
    --volume ./odmserver.pem:/certs/server.pem \
    management-mcp-server:latest \
    --transport streamable-http \
    --ssl-cert-path /certs/server.pem \
    --url       "https://${DC_HOST}/decisioncenter-api" \
    --res-url   "https://${RES_CONSOLE_HOST}/res" \
    --username  <username> \
    --password  <password>
```

>Note: the ODM servers certificate file (`odmserver.pem`) is mounted in the container as the file `/certs/server.pem` thanks to the `--volume` docker run option.
