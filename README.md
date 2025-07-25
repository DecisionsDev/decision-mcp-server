# decision-mcp-server MCP Server

## What is IBM ODM?

IBM Operational Decision Manager (ODM) is a business rules management system that helps organizations automate, manage, and govern business decisions. ODM allows you to define, deploy, and update decision logic outside of application code, making your business more agile and responsive.

## Why Connect MCP Server to IBM ODM?

The Model Context Protocol (MCP) server acts as a bridge between IBM ODM and modern AI assistants or orchestration platforms. By connecting MCP to ODM Decision Server Runtime, you can:
- Expose decision services as tools and prompts for AI assistants
- Enable dynamic decision automation in workflows
- Simplify integration with Watson Orchestrate and other platforms
- Centralize business logic and make it accessible to end users and bots

## Features

- **Decision Storage**: Demonstrates resource management with a local storage system
- **Tools**: Add  and invoke ODM decision services as tools

## Quickstart

### Prerequisites

- Python 3.13+
- Docker 
- [Watson Orchestrate ADK](https://developer.watson-orchestrate.ibm.com/getting_started/installing)

### Installation in Watson Orchestrate ADK Integration

#### **Clone the repository**

   ```bash
   git clone <repo-url>
   cd decision-mcp-server
   ```



#### To use this MCP server as a Watson Orchestrate tool:

1. **Install Watson Orchestrate ADK**

   Follow the [official guide](https://developer.watson-orchestrate.ibm.com/getting_started/installing).

2. Run the [Operational Decison Manager for Developers image](https://hub.docker.com/r/ibmcom/odm)

```bash
docker run -e LICENSE=accept --network wxo-server -p 9060:9060 -p 9443:9443 --name odm -e SAMPLE=true icr.io/cpopen/odm-k8s/odm:9.5
```
3. **Import the sample material**

- Open the Decision Server Console [Decision Server Console](https://localhost:9060/res)
* Login - odmAdmin / odmAdmin
* Click Explorer
* Deploy button
* Select the file in `<DIRECTORY>/samples/hr_ruleapps.jar`
* Click Deploy button

4. **Register the MCP Server**

  Use the Waston orchestrate command line 
```bash
orchestrate toolkits import  --kind mcp  --name DecisionServer --description "A MCP IBM Decision Server" --package-root $PWD  --command "uv run decision-mcp-server --odm-url=http://odm:9060/res"
```
This should return something like that
```
[INFO] - ✅ The following tools will be imported:
  • vacation
[INFO] - Successfully imported tool kit DecisionServer
```


> Notes: 
> - If you have issue to import the mcp server verify you have not .venv directory. If so remove it by using `rm -R .venv`

5. **Use Waston Orchestrate with ODM**

   * Start the Watson Orchestrate Chat UI 
```
orchestrate chat start
```

   * Click `Create a new Agent`
      - Name : Decision Agent
      - Description : A Decisional Agent
    Click `Create` button

   * Click `Manage Agents`
   * Select the `Decision Agent`
   * Click Toolset
   * Click `Add tools`
   * Click Add from Local instance
   * Check `DecisionServer:vacation`
   * Click `Add Agents` button


Now we are ready to use this agent.
Select the Decision Agent chat 

Then ask this question :
`
John Doe is an Acme Corp employee who was hired on November 1st, 1999. How many vacation days is John Doe entitled to each year?
`
This should return 
```
John Doe is entitled to 43 days per year.
```


## Configuration

   * Set your ODM credentials and endpoint in the command line or environment variables. Example:

```bash
uv run decision-mcp-server --odm-url http://your-odm-url/res --username your_user --password your_pass
```


   * Register this MCP Server in MCP Client*

   In your ADK configuration, add the MCP server as a tool provider:

   ```json
   "mcpServers": {
     "decision-mcp-server": {
       "command": "uv",
       "args": [
         "--directory",
         "<PATH_TO>/decision-mcp-server",
         "run",
         "decision-mcp-server"
       ]
     }
   }
   ```

   For published servers, use:

   ```json
   "mcpServers": {
     "decision-mcp-server": {
       "command": "uvx",
       "args": [
         "decision-mcp-server"
       ]
     }
   }
   ```

## Support

For more details on IBM ODM, see [IBM Documentation](https://www.ibm.com/docs/en/odm).
For Watson Orchestrate ADK, see [Getting Started](https://developer.watson-orchestrate.ibm.com/getting_started/installing).


### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory $PWD/decision-mcp-server run decision-mcp-server
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.