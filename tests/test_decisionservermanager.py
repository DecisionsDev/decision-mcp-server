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

# Run the tests
if __name__ == '__main__':
    pytest.main()
