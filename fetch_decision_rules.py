#!/usr/bin/env python3
"""
Decision Rules Fetcher Tool

This module provides a tool to fetch business rules from IBM ODM Decision Center API
and extract relevant information for decision explanation purposes.

It can be used as:
1. A standalone script to fetch and display rules
2. An imported module to integrate with other tools for decision explanation

Example usage as a module:
```python
from fetch_decision_rules import fetch_decision_rules

# Get rules for a specific project
rules = fetch_decision_rules(
    project_id="f46ca966-2d2b-4ff3-a1d0-eb2a68e641ca",
    host="localhost",
    port=9060,
    username="odmAdmin",
    password="odmAdmin"
)

# Process the rules
for rule_id, rule_data in rules.items():
    print(f"Rule ID: {rule_id}")
    print(f"Definition: {rule_data['definition']}")
    print(f"Link: {rule_data['permaLink']}")
```
"""

import requests
import json
import sys
from typing import Dict, Any, Optional


def fetch_decision_rules(
    project_id: str = "f46ca966-2d2b-4ff3-a1d0-eb2a68e641ca",
    host: str = "localhost",
    port: int = 9060,
    username: str = "odmAdmin",
    password: str = "odmAdmin",
    with_content: bool = True,
    use_dependencies: bool = False,
    verbose: bool = True
) -> Dict[str, Dict[str, str]]:
    """
    Fetch rules from Decision Center API and extract rule information.
    
    This function connects to the IBM ODM Decision Center API, retrieves rules
    for a specific project, and extracts the internalId, permaLink, and definition
    for each rule. The extracted information is returned as a dictionary with
    internalId as the key and a dictionary containing permaLink and definition as the value.
    
    Args:
        project_id (str): The ID of the project to fetch rules from
        host (str): The hostname of the Decision Center server
        port (int): The port number of the Decision Center server
        username (str): The username for Basic Authentication
        password (str): The password for Basic Authentication
        with_content (bool): Whether to include rule content in the response
        use_dependencies (bool): Whether to use dependencies in the response
        verbose (bool): Whether to print status messages
        
    Returns:
        Dict[str, Dict[str, str]]: A dictionary with internalId as key and a dictionary
                                  containing permaLink and definition as value
                                  
    Raises:
        requests.exceptions.ConnectionError: If the connection to the server fails
        Exception: For any other errors during the request
    """
    # API endpoint
    url = f"http://{host}:{port}/decisioncenter-api/v1/projects/{project_id}/rules"
    
    # Query parameters
    params = {
        "withContent": str(with_content).lower(),
        "useDependencies": str(use_dependencies).lower()
    }
    
    # Headers
    headers = {
        "accept": "*/*"
    }
    
    # Basic Authentication credentials
    auth = (username, password)
    
    try:
        # Make the GET request with Basic Authentication
        if verbose:
            print(f"Fetching rules from: {url}")
            print(f"Using Basic Authentication with username: {username}")
        
        response = requests.get(url, params=params, headers=headers, auth=auth)
        
        # Check if the request was successful
        if response.status_code == 200:
            if verbose:
                print("Request successful!")
            
            # Parse the JSON response
            try:
                rules_data = response.json()
                
                # Extract the required information
                if "elements" in rules_data:
                    rules_dict = {}
                    for element in rules_data["elements"]:
                        internal_id = element.get("internalId", "")
                        perma_link = element.get("permaLink", "")
                        definition = element.get("definition", "")
                        
                        rules_dict[internal_id] = {
                            "permaLink": perma_link,
                            "definition": definition
                        }
                    
                    # Print the extracted information if verbose
                    if verbose:
                        print(f"Found {len(rules_dict)} rules:")
                        print(json.dumps(rules_dict, indent=2))
                    
                    return rules_dict
                else:
                    if verbose:
                        print("No elements found in the response")
                        print("Full response:")
                        print(json.dumps(rules_data, indent=2))
                    return {}
            except json.JSONDecodeError:
                # If not valid JSON, print as text
                if verbose:
                    print("Response content is not valid JSON:")
                    print(response.text)
                raise Exception("Invalid JSON response from server")
        else:
            if verbose:
                print(f"Request failed with status code: {response.status_code}")
                print("Response content:")
                print(response.text)
            raise Exception(f"Request failed with status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        if verbose:
            print(f"Error: Could not connect to {url}")
            print("Make sure the Decision Center server is running and accessible.")
        raise e
    except Exception as e:
        if verbose:
            print(f"Error making request: {e}")
        raise e


def main():
    """
    Main function to run the script from the command line.
    """
    try:
        rules = fetch_decision_rules()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
