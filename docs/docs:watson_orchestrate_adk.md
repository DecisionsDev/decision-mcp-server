# Watson Orchestrate ADK Integration Guide

## Overview

The Watson Orchestrate ADK integration allows you to connect the Decision MCP Server to Watson Orchestrate for dynamic decision-making workflows.

---

## Prerequisites

- Python 3.13+
- Docker
- [Watson Orchestrate ADK](https://developer.watson-orchestrate.ibm.com/getting_started/installing)

---

## Steps

### 1. Clone the Repository
```bash
git clone <repo-url>
cd decision-mcp-server
```

### 2. Run ODM Locally
```bash
docker run -e LICENSE=accept --network wxo-server -p 9060:9060 -p 9443:9443 --name odm -e SAMPLE=true icr.io/cpopen/odm-k8s/odm:9.5
```

### 3. Import Sample Material
1. Open the [Decision Server Console](http://localhost:9060/res).
2. Login: `odmAdmin / odmAdmin`.
3. Deploy the sample file:
   - Click **Explorer** → **Deploy** → Select `<DIRECTORY>/samples/hr_ruleapps.jar` → **Deploy**.

### 4. Register the MCP Server
```bash
orchestrate toolkits import --kind mcp --name DecisionServer --description "A MCP IBM Decision Server" --package-root $PWD --command "uv run decision-mcp-server --url=http://odm:9060/res"
```

### 5. Use Watson Orchestrate
1. Start the Watson Orchestrate Chat UI:
   ```bash
   orchestrate chat start
   ```
2. Create and configure an agent:
   - Name: Decision Agent
   - Description: A Decisional Agent
   - Add tools: Select `DecisionServer:vacation`.

---

## Support

For Watson Orchestrate ADK, see [Getting Started](https://developer.watson-orchestrate.ibm.com/getting_started/installing).