import pytest
from decision_mcp_server.DecisionServerManager import DecisionServerManager  # Correct import path
from http.server import BaseHTTPRequestHandler, HTTPServer
from decision_mcp_server.Credentials import Credentials  # Correct import path
import json
import threading

# Mock data to be returned by the server
mock_data = [
    {
        "id": "checktoolsparam/v1",
        "rulesets": [
            # This ruleset has a tools.parameters property
            {"id": "checktoolsparam/v1/ruleset1", "properties": [{"id":"ruleset.status","value":"enabled"},{"id":"tools.enabled","value":"true"}], "version": "1.0","test":"true"},
            {"id": "checktoolsparam/v1/ruleset2", "properties": [{"id":"ruleset.status","value":"enabled"}],"version": "2.0","test":"false"}
        ]
    },
    {
        "id": "verifystatusenabled/v1",
        "rulesets": [
            # This ruleset has an enabled status
            {"id": "verifystatusenabled/v1/ruleset1", "properties": [{"id":"ruleset.status","value":"enabled"},{"id":"tools.enabled","value":"true"}], "version": "1.0","test":"true"},
            # This ruleset has an enabled status - Should be selected
            {"id": "verifystatusenabled/v1/ruleset1", "properties": [{"id":"ruleset.status","value":"enabled"},{"id":"tools.enabled","value":"true"}], "version": "2.0","test":"true"},
            # This ruleset has a disabled status
            {"id": "verifystatusenabled/v1/ruleset1", "properties": [{"id":"ruleset.status","value":"disabled"},{"id":"tools.enabled","value":"true"}],"version": "3.0","test":"false"}
        ]
    },
    {
        "id": "multipleruleset/v1",
        "rulesets": [
            {"id": "multipleruleset/v1/ruleset1","properties": [{"id":"ruleset.status","value":"enabled"},{"id":"tools.enabled","value":"true"}], "version": "1.1","test":"true"},
            {"id": "multipleruleset/v1/ruleset2","properties": [{"id":"ruleset.status","value":"enabled"},{"id":"tools.enabled","value":"true"}], "version": "1.2","test":"true"}
        ]
    },
    {
        "id": "minorrulesetversion/v1",
        "rulesets": [
            {"id": "minorrulesetversion/v1/ruleset1","properties": [{"id":"ruleset.status","value":"enabled"},{"id":"tools.parameters","value":"{\"arg\":\"name\"}"}], "version": "1.1","test":"true"},
            {"id": "minorrulesetversion/v1/ruleset1","properties": [{"id":"ruleset.status","value":"enabled"},{"id":"tools.enabled","value":"true"}],"version": "1.2","test":"true"}
        ]
    }
]

class MockServerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/res/api/v1/ruleapps':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(mock_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_mock_server(server_class=HTTPServer, handler_class=MockServerRequestHandler, port=8885):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

@pytest.fixture(scope='module', autouse=True)
def mock_server():
    # Start the mock server in a separate thread
    mock_server_thread = threading.Thread(target=run_mock_server)
    mock_server_thread.daemon = True
    mock_server_thread.start()
    yield
    # Cleanup code can be added here if needed

def test_fetch_rulesets(caplog):
    credentials = Credentials(
    odm_url='http://localhost:8885/res',
        username='mock_bearer_token', password='mock_password',
)
    manager = DecisionServerManager(
        credentials=credentials
    )

    # Capture the output of the fetch_rulesets method
#    with caplog.at_level(logging.INFO):
#        manager.fetch_rulesets()
    ruleset_fetched = manager.fetch_rulesets()
    # Verify the rulesets contain the expected output

    fetchedresult={}
    for ruleset in ruleset_fetched.values():
        fetchedresult[ruleset["id"]]=ruleset["properties"]

    print("RESULT : "+str(fetchedresult))


    def filter_rulesets(mock_data):
        filtered_data = []
        result_tocheck = {}
        for app in mock_data:
            filtered_rulesets = []
            for ruleset in app["rulesets"]:
                if ruleset.get("test") == "true":
                    ruleset_copy = ruleset.copy()
                    del ruleset_copy["test"]
                    filtered_rulesets.append(ruleset_copy)
                    result_tocheck[ruleset["id"]]=ruleset_copy['properties']
                    
            
            if filtered_rulesets:
                filtered_data.append({
                    "id": app["id"],
                    "rulesets": filtered_rulesets
                })   
        return result_tocheck

    expected_rulesets = filter_rulesets(mock_data)

    # Extract the dictionary
    assert len(fetchedresult) == len(expected_rulesets)

    # Make sure you sort any lists in the dictionary before dumping to a string

    resultsort = json.dumps(fetchedresult, sort_keys=True)
    expectedsort = json.dumps(expected_rulesets, sort_keys=True)

    assert resultsort == expectedsort
    # Verify the logs contain the expected output
 #   log_output = caplog.text
 #   assert "RuleApp: ruleapp1, Ruleset: ruleset1, Highest Version Ruleset: ruleapp1/v1/ruleset2" in log_output
 #   assert "RuleApp: ruleapp2, Ruleset: ruleset2, Highest Version Ruleset: ruleapp2/v1/ruleset2" in log_output

@pytest.mark.parametrize("tools_parameters,expected_call_openapi", [
    (None, True),  # When tools.parameters is None, should call get_ruleset_openapi
    ("[]", True),  # When tools.parameters is "[]", should call get_ruleset_openapi
    ('{"type":"object","properties":{"name":{"type":"string"}}}', False)  # Valid JSON, should not call get_ruleset_openapi
])
def test_get_input_schema(tools_parameters, expected_call_openapi):
    # Create a test ruleset with the given tools.parameters value
    ruleset = {
        "id": "test/v1/ruleset",
        "properties": []
    }
    
    if tools_parameters is not None:
        ruleset["properties"].append({
            "id": "tools.parameters",
            "value": tools_parameters
        })
    
    # Create a mock DecisionServerManager with a mocked get_ruleset_openapi method
    credentials = Credentials(
        odm_url='http://localhost:8885/res',
        username='mock_bearer_token',
        password='mock_password',
    )
    
    manager = DecisionServerManager(credentials)
    
    # Mock the get_ruleset_openapi method
    original_get_ruleset_openapi = manager.get_ruleset_openapi
    openapi_called = [False]  # Using a list to track if the method was called
    
    def mock_get_ruleset_openapi(ruleset):
        openapi_called[0] = True
        return {"type": "object", "properties": {"mocked": {"type": "string"}}}
    
    manager.get_ruleset_openapi = mock_get_ruleset_openapi
    
    try:
        # Call get_input_schema
        result = manager.get_input_schema(ruleset)
        
        # Check if get_ruleset_openapi was called as expected
        assert openapi_called[0] == expected_call_openapi
        
        # If tools_parameters is a valid JSON and not None or "[]", 
        # verify the result matches the parsed JSON
        if tools_parameters and tools_parameters != "[]":
            expected = json.loads(tools_parameters)
            assert result == expected
        else:
            # Otherwise, verify the result is the mocked OpenAPI schema
            assert result == {"type": "object", "properties": {"mocked": {"type": "string"}}}
    
    finally:
        # Restore the original method
        manager.get_ruleset_openapi = original_get_ruleset_openapi

def test_tools_name_handling():
    """Test the handling of tools.name property in generate_tools_format method."""
    # Create test data with two rulesets - one with tools.name and one without
    rulesets = {
        "ruleset1": {
            "id": "test/v1/ruleset1",
            "displayName": "Display Name With Spaces",
            "description": "Test description",
            "properties": [
                {"id": "tools.enabled", "value": "true"},
                {"id": "tools.parameters", "value": '{"type":"object","properties":{"name":{"type":"string"}}}'},
                # No tools.name here - should use displayName
            ]
        },
        "ruleset2": {
            "id": "test/v1/ruleset2",
            "displayName": "Unused Display Name",
            "description": "Test description 2",
            "properties": [
                {"id": "tools.enabled", "value": "true"},
                {"id": "tools.parameters", "value": '{"type":"object","properties":{"name":{"type":"string"}}}'},
                {"id": "tools.name", "value": "CustomToolName"},  # Explicit tools.name
            ]
        }
    }
    
    # Create a mock DecisionServerManager
    credentials = Credentials(
        odm_url='http://localhost:8885/res',
        username='mock_user',
        password='mock_password',
    )
    
    manager = DecisionServerManager(credentials)
    
    # Mock the get_input_schema method to return a simple schema
    original_get_input_schema = manager.get_input_schema
    
    def mock_get_input_schema(ruleset):
        return {"type": "object", "properties": {"name": {"type": "string"}}}
    
    manager.get_input_schema = mock_get_input_schema
    
    try:
        # Call generate_tools_format
        result = manager.generate_tools_format(rulesets)
        
        # Verify both tools were formatted correctly
        assert len(result) == 2
        
        # First ruleset should use displayName (converted to lowercase with underscores)
        assert result[0].tool_name == "display_name_with_spaces"
        
        # Second ruleset should use the explicit tools.name
        assert result[1].tool_name == "customtoolname"
        
    finally:
        # Restore the original method
        manager.get_input_schema = original_get_input_schema

def test_tools_name_and_description_handling():
    """
    Test that tools.name and tools.description properties are correctly handled
    in the generate_tools_format method.
    """
    # Create test data with three rulesets to test different scenarios
    rulesets = {
        "ruleset1": {
            "id": "test/v1/ruleset1",
            "displayName": "Display Name With Spaces",
            "description": "Default description",
            "properties": [
                {"id": "tools.enabled", "value": "true"},
                # No tools.name or tools.description - should use defaults
            ]
        },
        "ruleset2": {
            "id": "test/v1/ruleset2",
            "displayName": "Unused Display Name",
            "description": "Unused description",
            "properties": [
                {"id": "tools.enabled", "value": "true"},
                {"id": "tools.name", "value": "CustomToolName"},  # Custom name
                {"id": "tools.description", "value": "Custom description"},  # Custom description
            ]
        },
        "ruleset3": {
            "id": "test/v1/ruleset3",
            "displayName": "Another Display Name",
            "description": "Another default description",
            "properties": [
                {"id": "tools.enabled", "value": "true"},
                {"id": "tools.name", "value": "ThirdTool"},  # Custom name
                # No tools.description - should fall back to default
            ]
        }
    }
    
    # Create a mock DecisionServerManager
    credentials = Credentials(
        odm_url='http://localhost:8885/res',
        username='mock_user',
        password='mock_password',
    )
    
    manager = DecisionServerManager(credentials)
    
    # Mock the get_input_schema method to return a simple schema
    original_get_input_schema = manager.get_input_schema
    
    def mock_get_input_schema(ruleset):
        return {"type": "object", "properties": {"name": {"type": "string"}}}
    
    manager.get_input_schema = mock_get_input_schema
    
    try:
        # Call generate_tools_format
        result = manager.generate_tools_format(rulesets)
        
        # Verify all tools were formatted correctly
        assert len(result) == 3
        
        # First ruleset should use displayName and default description
        assert result[0].tool_name == "display_name_with_spaces"
        assert result[0].description == "Default description"
        
        # Second ruleset should use explicit values for both name and description
        assert result[1].tool_name == "customtoolname"  # Note: also tests lowercase conversion
        assert result[1].description == "Custom description"
        
        # Third ruleset should use explicit name but default description
        assert result[2].tool_name == "thirdtool"  # Note: also tests lowercase conversion
        assert result[2].description == "Another default description"
        
        # Verify rulesetPath is set correctly
        assert result[0].rulesetPath == "/test/v1/ruleset1"
        assert result[1].rulesetPath == "/test/v1/ruleset2"
        assert result[2].rulesetPath == "/test/v1/ruleset3"
        
    finally:
        # Restore the original method
        manager.get_input_schema = original_get_input_schema

# Run the tests
if __name__ == '__main__':
    pytest.main()
