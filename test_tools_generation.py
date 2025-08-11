import json
import ast

from src.decision_mcp_server.Credentials import Credentials
from src.decision_mcp_server.DecisionServerManager import DecisionServerManager
from src.decision_mcp_server.DecisionServiceDescription import DecisionServiceDescription
from pprint import pprint




creds = Credentials(
    odm_url="https://odmchart-odm-ds-console-route-keycloak.apps.fme.cp.fyre.ibm.com/res",
    token_url="http://keycloak-keycloak.apps.fme.cp.fyre.ibm.com/auth/realms/myrealm/protocol/openid-connect/token",
    client_id="myclient",
    client_secret="mysecret",
    scope='openid',
    verify_ssl=False
)

#creds = Credentials(
#    odm_url="http://localhost:9060/res",
#    zenapikey="Hx8EbQ1BlUUR8eALrhSBcvfGx1Wc8y8yJW2RoINe",
#    username="cp4admin",
#)
#creds = Credentials(
#    odm_url="http://localhost:9060/res",
#    username="odmAdmin",
#    password="odmAdmin"
#     verify_ssl=False
#)
#creds = Credentials(
#    odm_url="http://localhost:9060/res")
manager = DecisionServerManager(
    credentials=creds
)
repostory: dict[str, DecisionServiceDescription] = {}
rulesets = manager.fetch_rulesets()
print("Fetched rulesets:", rulesets)
extractedTools = manager.generate_tools_format(rulesets)
tools= []

for decisionService in extractedTools:
    print("Decision Service:",str( decisionService.tool_name))
    tool_info = decisionService.tool_description
    tools.append(tool_info)
    # logging.info(f"Tool for service '{service_key}':"+ str(tool_info))
    #print("Service key:", decisionService.get('tool_name'))
    repostory[decisionService.tool_name]=decisionService

    
#print("Tools" + str(tools))
# Display the object in a friendly (pretty-printed) manner
pprint(repostory["number_of_timeoff_days"].__dict__)
# Example: get schema from a ruleset (adjust as needed)
# This assumes fetch_rulesets returns a list/dict with schema info
if repostory.get("number_of_timeoff_days")==None:
    print("SSS cannot be found")