
import logging
import json
from collections import defaultdict
import requests
import yaml
import jsonref
from typing import Dict, Any, Optional
from requests.exceptions import RequestException
from .DecisionServiceDescription import DecisionServiceDescription
class DecisionServerManager:
    """
    :no-index:
    DecisionServerManager is a class responsible for managing interactions with a decision server, including fetching rulesets, extracting the highest version rulesets, generating tools format, and invoking decision services.

    Methods:
        __init__(self, credentials):
            Initializes the DecisionServerManager with the provided credentials.
        extract_highest_version_rulesets(self, data):
            Extracts the highest version rulesets from the provided data.
        generate_tools_format(self, filtered_rulesets):
            Generates a formatted list of rulesets in the tools format from the filtered rulesets.
        fetch_rulesets(self):
            Fetches rulesets from the decision server and extracts the highest version rulesets.
        invokeDecisionService(self, rulesetPath, decisionInputs):
            Invokes a decision service with the provided ruleset path and decision inputs.

    Usage:
        # Initialize the manager with credentials
        # Example using environment variables (recommended for security)
        import os
        credentials = Credentials(
            odm_url=os.environ.get('ODM_URL'),
            username=os.environ.get('ODM_USERNAME'),
            password=os.environ.get('ODM_PASSWORD')
        )
        manager = DecisionServerManager(credentials)

        # Fetch rulesets
        rulesets = manager.fetch_rulesets()
        print(rulesets)

        # Generate tools format
        formatted_rulesets = manager.generate_tools_format(rulesets)
        print(formatted_rulesets)

        # Invoke decision service
        decision_inputs = {"input1": "value1", "input2": "value2"}
        response = manager.invokeDecisionService('/path/to/ruleset', decision_inputs)
        print(response)
    """
    
    def __init__(self, credentials):
        """
        :no-index:
        Initializes the DecisionServerManager with the provided credentials.

        Args:
            credentials (object): An object containing authentication details.

        Attributes:
            logger (logging.Logger): Logger instance for logging information.
            credentials (object): The provided credentials object.
            auth (str): Authentication token obtained from credentials.
            headers (dict): Headers obtained from credentials.
            trace (dict): Trace configuration for logging rule firing information.
        """
        # Get logger for this class
        self.logger = logging.getLogger(__name__)

        # Initialize with provided credentials
        self.credentials = credentials
        self.headers = self.credentials.get_auth()
        self.trace={ 
            "__TraceFilter__": {
                "none": True,
                "infoTotalRulesFired": True,
                "infoRulesFired": True
                }
            }
   
    def extract_highest_version_rulesets(self, data):
        """
        :no-index:
        Extracts the highest version rulesets from the provided data.

        Args:
            data (list): A list of rule applications and their rulesets.

        Returns:
            dict: A dictionary containing the highest version rulesets.
        """
        highest_version_rulesets = {}

        # Group rulesets by ruleapp name and ruleset name
        ruleset_groups = defaultdict(list)
        for ruleapp in data:
            ruleapp_name, ruleapp_version = ruleapp["id"].split('/')[0], ruleapp["id"].split('/')[1]
            for ruleset in ruleapp["rulesets"]:
                ruleset_name = ruleset["id"].split('/')[2]
                ruleset_groups[(ruleapp_name, ruleset_name)].append((ruleapp_version, ruleset))

        # Find the highest version ruleset for each group
        for (ruleapp_name, ruleset_name), rulesets in ruleset_groups.items():
            # Sort rulesets by ruleapp version and then by ruleset version
            filtered_rulesets = [
            (version, ruleset) for version, ruleset in rulesets
            if any(prop["id"] == "ruleset.status" and prop["value"] == "enabled" for prop in ruleset["properties"])
             and any(prop["id"] == "agent.enabled" and prop["value"].lower() == "true" for prop in ruleset["properties"])
           ]
            if not filtered_rulesets:
                continue
            sorted_rulesets = sorted(filtered_rulesets, key=lambda x: (x[0], x[1]["version"]), reverse=True)
                # Get the highest version ruleset
            highest_version_ruleset = sorted_rulesets[0][1]
            highest_version_rulesets[str(ruleapp_name)+str(ruleset_name)] = highest_version_ruleset

        return highest_version_rulesets
    

    def to_plain_dict(self,obj):
        """
        Recursively convert a jsonref.JsonRef structure to a plain JSON-serializable dict, dealing with circular references
        """

        def circular_reference(v,seen_ids):
            if isinstance(v, dict) and v.get("type", "") == "object" and "properties" in v:
                v_id = id(v)
                if v_id in seen_ids:
                    return True # this is a circular reference
                seen_ids.append(v_id)
            return False

        def to_plain_dict(obj,seen_ids):
            if isinstance(obj, dict):
                x = {}
                for k, v in obj.items():
                    seen_ids_copy = seen_ids.copy()
                    if not circular_reference(v,seen_ids_copy):
                        x[k] = to_plain_dict(v,seen_ids_copy)
                return x
            elif isinstance(obj, list):
                return [to_plain_dict(i,seen_ids) for i in obj]
            else:
                return obj

        return to_plain_dict(obj,[])

    def get_ruleset_openapi(self, ruleset):
        """
        :no-index:
        Extracts the input schema from a ruleset.

        Args:
            ruleset (dict): A dictionary representing a ruleset.

        Returns:
            dict: The input schema of the ruleset.
        """
        try:
                # Make the GET request with headers
                self.logger.info("Retrieve OpenAPI schema at "+self.credentials.odm_url_runtime+'/rest/'+ruleset["id"]+ '/openapi')
                session = self.credentials.get_session()
                response = session.get(self.credentials.odm_url_runtime+'/rest/'+ruleset["id"]+ '/openapi?format=json', headers=self.headers, verify=self.credentials.cacert)


                # Check if the request was successful
                if response.status_code == 200:
                    self.logger.info("Request successful!")

                    # Resolve $ref references
                    jsonopenApiData = jsonref.JsonRef.replace_refs(json.loads(response.text))

                    # Get the response schema (for 200 response as an example)
                    # Extract the input 
                    inputParameterSchema= jsonopenApiData["paths"]["/"+ruleset["id"]]["post"]["requestBody"]["content"]["application/json"]["schema"]
                    if "properties" in inputParameterSchema and "__DecisionID__" in inputParameterSchema["properties"]:
                        del inputParameterSchema["properties"]["__DecisionID__"]
                    # Convert to plain JSON-serializable dict
                    return self.to_plain_dict(inputParameterSchema)
                else:
                    self.logger.error("Request failed with status code: %s", response.status_code)
                    self.logger.error("Response: %s", response.text)

        except requests.exceptions.RequestException as e:
                self.logger.error("An error occurred: %s", e)
        except json.JSONDecodeError:
                self.logger.error("Failed to decode JSON response.")
        

    def get_input_schema(self, ruleset):

        """
        :no-index:
        Extracts the input schema from a ruleset using OpenAPI generation.

        Args:
            ruleset (dict): A dictionary representing a ruleset.

        Returns:
            dict: The input schema of the ruleset.
        """
        return self.get_ruleset_openapi(ruleset)
    



    def generate_tools_format(self, filtered_rulesets)-> list[DecisionServiceDescription]:
        """
        :no-index:
        Generates a formatted list of rulesets in the tools format from the filtered rulesets.

        Args:
            filtered_rulesets (dict): A dictionary of filtered rulesets.

        Returns:
            list: A list of formatted rulesets.
        """
        formatted_tools = []

        for ruleset in filtered_rulesets.values():

            input_schema = self.get_input_schema(ruleset)
            toolName = next((prop["value"] for prop in ruleset["properties"] if prop["id"] == "agent.name"), ruleset["displayName"]).replace(" ", "_").lower()
            toolDescription = next((prop["value"] for prop in ruleset["properties"] if prop["id"] == "agent.description"), ruleset["description"])
             # Define a class to hold the formatted ruleset data
            formatted_ruleset = DecisionServiceDescription(toolName, ruleset, toolDescription, input_schema)
            formatted_tools.append(formatted_ruleset)
        return formatted_tools

    def fetch_rulesets(self):
        """
        :no-index:
        Fetches rulesets from the decision server and extracts the highest version rulesets.

        Returns:
            dict: A dictionary containing the highest version rulesets, or None if the request fails.
        """
        try:
            # Make the GET request with headers
            self.logger.info(self.credentials.odm_url+'/api/v1/ruleapps')
            session = self.credentials.get_session()
            response = session.get(self.credentials.odm_url+'/api/v1/ruleapps', headers=self.headers, verify=self.credentials.cacert)

            # Check if the request was successful
            if response.status_code == 200:
                self.logger.info("Request successful!")

                # Parse and display the JSON response
                data = response.json()
                # Extract the highest version rulesets
                highest_version_rulesets = self.extract_highest_version_rulesets(data)

                return highest_version_rulesets
            else:
                self.logger.error("Request failed with status code: %s", response.status_code)
                self.logger.error("Response: %s", response.text)

        except requests.exceptions.RequestException as e:
            self.logger.error("An error occurred: %s", e)
        except json.JSONDecodeError:
            self.logger.error("Failed to decode JSON response.")

    def invokeDecisionService(self, rulesetPath, decisionInputs, trace=True):
        """
        :no-index:
        Invokes a decision service with the provided ruleset path and decision inputs.

        Args:
            rulesetPath (str): The path to the ruleset.
            decisionInputs (dict): A dictionary of decision inputs.

        Returns:
            dict: The response from the decision service, or an error message if the request fails.
        """
        # POST with basic auth        
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        
        params = {**decisionInputs}
        if trace:
            params.update(self.trace)  # Add trace information to params
        try:
            session = self.credentials.get_session()
            response = session.post(self.credentials.odm_url_runtime+'/rest'+rulesetPath, headers=headers,
                                    json=params)

            # check response
            if response.status_code == 200:
                return response.json()
            else:
                err = response.content.decode('utf-8')
                logging.error(f"Request error, status: {response.status_code}, error: {err}")
                raise Exception(err)
