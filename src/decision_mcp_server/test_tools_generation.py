import json
import ast

from decision_mcp_server.Credentials import Credentials
from decision_mcp_server.DecisionServerManager import DecisionServerManager
from decision_mcp_server.DecisionServiceDescription import DecisionServiceDescription
from pprint import pprint
#creds = Credentials(
#    odm_url="http://localhost:9060/res",
#    username="odmAdmin",
#    password="odmAdmin"
#)

#creds = Credentials(
#    odm_url="https://cpd-odm.apps.vtt-ocp4-250804-010958.cp.fyre.ibm.com/odm/res",
#    zenapikey="mdGZBRlITzavs6UZ1lEj6IA0ScHA5IeEwV37FKB7",
#    username="cp4admin",
#    verify_ssl=args.disablessl
#)

creds = Credentials(
    odm_url="http://localhost:9060/res",
    username="odmAdmin",
    password="odmAdmin"
)

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
    tool_info = decisionService.toolDescription
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