
import logging
import json
from collections import defaultdict
import requests
from requests.exceptions import RequestException

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
        credentials = Credentials(odm_url='http://your_odm_url', username='your_username', password='your_password')
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
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize with provided credentials
        self.credentials = credentials
        self.auth, self.headers = self.credentials.get_auth()
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
             and any(prop["id"] == "tools.parameters" for prop in ruleset["properties"])
           ]

#           
            if not filtered_rulesets:
                continue

            sorted_rulesets = sorted(filtered_rulesets, key=lambda x: (x[0], x[1]["version"]), reverse=True)
                # Get the highest version ruleset
            highest_version_ruleset = sorted_rulesets[0][1]
            highest_version_rulesets[str(ruleapp_name)+str(ruleset_name)] = highest_version_ruleset

        return highest_version_rulesets
    
    def generate_tools_format(self, filtered_rulesets):
        """
        :no-index:
        Generates a formatted list of rulesets in the tools format from the filtered rulesets.

        Args:
            filtered_rulesets (dict): A dictionary of filtered rulesets.

        Returns:
            list: A list of formatted rulesets.
        """
        formatted_rulesets = []

        for ruleset in filtered_rulesets.values():
            # Extract tools.parameters
            tools_parameters = next((prop["value"] for prop in ruleset["properties"] if prop["id"] == "tools.parameters"), "[]")
            args = json.loads(tools_parameters)

            callbackName = next((prop["value"] for prop in ruleset["properties"] if prop["id"] == "tools.callback"), None)

            formatted_ruleset = {
                "engine": "odm",
                "toolName": ruleset["displayName"],
                "rulesetProperties": ruleset["properties"],
                "toolDescription": ruleset["description"],
                "toolPath": "/"+ruleset["id"],
                "callbackClassName": callbackName,
                "args": args,
                "output": "resultat"
            }
            formatted_rulesets.append(formatted_ruleset)

        return formatted_rulesets

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
            response = session.get(self.credentials.odm_url+'/api/v1/ruleapps', auth=self.auth, headers=self.headers)

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

    def invokeDecisionService(self, rulesetPath, decisionInputs):
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
        # TODO: Add trace , **self.trace
        try:
            session = self.credentials.get_session()
            response = session.post(self.credentials.odm_url_runtime+'/rest'+rulesetPath, headers=headers,
                                    json=params, auth=self.auth)

            # check response
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Request error, status: {response.status_code}")
        except requests.exceptions.RequestException as e:  
            return {"error": f"An error occurred when invoking the Decision Service: {e}"}
    
# Example usage:
# For Basic Auth
# manager = DecisionServerManager(odm_url='http://your_odm_url', username='your_username', password='your_password')

# For Bearer Token
# manager = DecisionServerManager(odm_url='http://your_odm_url', bearer_token='your_bearer_token')

# For ZenAPIKey
# manager = DecisionServerManager(odm_url='http://your_odm_url', zenapikey='your_zenapikey')

# manager.fetch_rulesets()