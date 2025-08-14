import pytest
from unittest.mock import Mock, patch
import os
import argparse
from decision_mcp_server.DecisionMCPServer import DecisionMCPServer, parse_arguments, create_credentials
from decision_mcp_server.Credentials import Credentials
import mcp.types as types
from mcp.server import Server
import json

# Test fixtures
@pytest.fixture
def mock_credentials():
    return Credentials(
        odm_url="http://test:9060/res",
        username="test_user",
        password="test_pass"
    )

@pytest.fixture
def mock_server():
    return Mock(spec=Server)

@pytest.fixture
def decision_server(mock_credentials, mock_server):
    server = DecisionMCPServer(credentials=mock_credentials, traces_dir=None)
    server.server = mock_server
    server.manager = Mock()
    return server

# Test DecisionMCPServer initialization
def test_server_initialization(decision_server):
    assert isinstance(decision_server.notes, dict)
    assert isinstance(decision_server.repository, dict)
    assert decision_server.server is not None
    assert decision_server.credentials is not None

# Test argument parsing
@pytest.mark.parametrize("args,expected", [
    (
        ["--url", "http://test-odm:9060/res"],
        {"url": "http://test-odm:9060/res"}
    ),
    (
        ["--username", "testuser", "--password", "testpass"],
        {"username": "testuser", "password": "testpass"}
    ),
    (
        ["--zenapikey", "test-key"],
        {"zenapikey": "test-key"}
    ),
    (
        ["--client_id", "test-client", "--client_secret", "test-secret", "--token_url", "http://op/token", "--scope", "openid"],
        {"client_id": "test-client", "client_secret": "test-secret", "token_url": "http://op/token", "scope": "openid"}
    ),
    (
        ["--traces-dir", "/custom/traces/dir"],
        {"traces_dir": "/custom/traces/dir"}
    ),
    (
        ["--trace-enable", "True"],
        {"trace_enable": "True"}  # Explicitly enabled
    ),
    (
        ["--trace-enable", "False"],
        {"trace_enable": "False"}  # Explicitly disabled
    ),
    (
        ["--trace-maxsize", "100"],
        {"trace_maxsize": 100}
    ),
    (
        ["--log-level", "DEBUG"],
        {"log_level": "DEBUG"}  # Test log level argument
    ),
    (
        [],  # No arguments
        {"trace_enable": "False", "trace_maxsize": 50, "log_level": "INFO"}  # Default values
    ),
])
def test_parse_arguments(args, expected):  # Added 'expected' parameter
    with patch('sys.argv', ['script'] + args):
        parsed_args = parse_arguments()
        for key, value in expected.items():
            assert getattr(parsed_args, key) == value

# Test credentials creation
def test_create_credentials_basic_auth():
    args = argparse.Namespace(
        url="http://test:9060/res",
        runtime_url=None,
        username="test_user",
        password="test_pass",
        zenapikey=None,
        client_id=None,
        client_secret=None,
        verifyssl="True",
        ssl_cert_path=None
    )
    credentials = create_credentials(args)
    assert credentials.odm_url == "http://test:9060/res"
    assert credentials.username == "test_user"
    assert credentials.password == "test_pass"

def test_create_credentials_zen_api():
    args = argparse.Namespace(
        url="http://test:9060/res",
        runtime_url="http://test:9060/DecisionService",
        username="test_user",
        zenapikey="test-key",
        client_id=None,
        client_secret=None,
        verifyssl="True",
        ssl_cert_path=None
    )
    credentials = create_credentials(args)
    assert credentials.zenapikey == "test-key"

def test_create_credentials_openid():
    args = argparse.Namespace(
        url="http://test:9060/res",
        runtime_url="http://test:9060/DecisionService",
        username=None,
        password=None,
        zenapikey=None,
        client_id="test-client",
        client_secret="test-secret",
        token_url="http://op/token",
        scope="openid",
        verifyssl="True",
        ssl_cert_path=None
    )
    credentials = create_credentials(args)
    assert credentials.client_id == "test-client"
    assert credentials.client_secret == "test-secret"
    assert credentials.token_url == "http://op/token"
    assert credentials.scope == "openid"

# Test error cases
def test_create_credentials_missing_basic_auth():
    args = argparse.Namespace(
        url="http://test:9060/res",
        runtime_url=None,
        username=None,
        password=None,
        zenapikey=None,
        client_id=None,
        client_secret=None,
        verifyssl="True"
    )
    with pytest.raises(ValueError) as exc_info:
        create_credentials(args)
    assert str(exc_info.value) == "Username and password must be provided for basic authentication."

# Test SSL verification
@pytest.mark.parametrize("verify_ssl,expected", [
    ("True", True),
    ("False", False)
])
def test_ssl_verification(verify_ssl, expected):
    args = argparse.Namespace(
        url="http://test:9060/res",
        runtime_url=None,
        username="test_user",
        password="test_pass",
        zenapikey=None,        # Added missing required args
        client_id=None,        # Added missing required args
        client_secret=None,    # Added missing required args
        verifyssl=verify_ssl,
        ssl_cert_path=None
    )
    credentials = create_credentials(args)
    assert credentials.verify_ssl == expected

# Test environment variables
def test_environment_variables():
    with patch.dict(os.environ, {
        'ODM_URL': 'http://env-test:9060/res',
        'ODM_USERNAME': 'env_user',
        'ODM_PASSWORD': 'env_pass',
        'TRACES_DIR': '/env/traces/dir',
        'TRACE_ENABLE': 'True',  # Testing explicit enable since default is now False
        'TRACE_MAXSIZE': '200',
        'LOG_LEVEL': 'DEBUG'
    }), patch('sys.argv', ['script']):  # Added sys.argv patch
        args = parse_arguments()
        assert args.url == 'http://env-test:9060/res'
        assert args.username == 'env_user'
        assert args.password == 'env_pass'
        assert args.traces_dir == '/env/traces/dir'
        assert args.trace_enable == "True"  # Should be "True" string because we set it explicitly
        assert args.trace_maxsize == 200
        assert args.log_level == 'DEBUG'

class DummyTool:
    def __init__(self, name, description, input_schema):
        self.name = name
        self.description = description
        self.inputSchema = input_schema

# Mock the types module
@pytest.fixture
def mock_types():
    mock = Mock()
    mock.Tool = DummyTool
    return mock

@pytest.fixture
def mock_manager():
    manager = Mock()
    # Setup mock rulesets
    manager.fetch_rulesets.return_value = [
        {"id": "rule1", "description": "First ruleset"},
        {"id": "rule2", "description": "Second ruleset"}
    ]
    # Setup mock tools
    manager.generate_tools_format.return_value = [
        Mock(
            tool_name="tool1",
            tool_description=DummyTool(
                name="tool1",
                description="First tool",
                input_schema={"type": "object"}
            )
        ),
        Mock(
            tool_name="tool2",
            tool_description=DummyTool(
                name="tool2",
                description="Second tool",
                input_schema={"type": "object"}
            )
        )
    ]
    return manager

@pytest.fixture
def server(mock_manager):
    credentials = Credentials(
        odm_url="http://test:9060/res",
        username="test",
        password="test"
    )
    server = DecisionMCPServer(credentials=credentials, traces_dir=None, trace_enable=True, trace_maxsize=50)  # Explicitly enable traces for testing
    server.manager = mock_manager
    return server

@pytest.mark.asyncio
async def test_list_tools(server, mock_manager):
    # Execute
    tools = await server.list_tools()

    # Verify
    assert len(tools) == 2
    assert mock_manager.fetch_rulesets.called
    assert mock_manager.generate_tools_format.called
    
    # Verify tool properties
    assert tools[0].name == "tool1"
    assert tools[1].name == "tool2"
    
    # Verify repository updates
    assert len(server.repository) == 2
    assert "tool1" in server.repository
    assert "tool2" in server.repository

@pytest.mark.asyncio
async def test_list_tools_empty(server, mock_manager):
    # Setup empty response
    mock_manager.fetch_rulesets.return_value = []
    mock_manager.generate_tools_format.return_value = []

    # Execute
    tools = await server.list_tools()

    # Verify
    assert len(tools) == 0
    assert len(server.repository) == 0

@pytest.mark.asyncio
async def test_list_tools_error_handling(server, mock_manager):
    # Setup error condition
    mock_manager.fetch_rulesets.side_effect = Exception("Failed to fetch rulesets")

    # Verify error is propagated
    with pytest.raises(Exception) as exc_info:
        await server.list_tools()
    assert str(exc_info.value) == "Failed to fetch rulesets"

@pytest.mark.asyncio
async def test_call_tool_success(server, mock_manager):
    # Setup mock response
    mock_manager.invokeDecisionService.return_value = {
        "result": "decision_result",
        "__DecisionID__": "123"  # This should be removed in response
    }

    # Setup test data
    tool_name = "tool1"
    arguments = {"input": "test_value"}
    
    # Add tool to repository
    server.repository[tool_name] = Mock(rulesetPath="/test/path")

    # Execute
    result = await server.call_tool(tool_name, arguments)

    # Verify
    assert mock_manager.invokeDecisionService.called
    assert mock_manager.invokeDecisionService.call_args[1] == {
        "rulesetPath": "/test/path",
        "decisionInputs": arguments
    }
    
    # Verify response format
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert result[0].type == "text"
    
    # Verify response content
    response_data = json.loads(result[0].text)
    assert response_data["result"] == "decision_result"
    assert "__DecisionID__" not in response_data

@pytest.mark.asyncio
async def test_call_tool_unknown_tool(server):
    # Try to call non-existent tool
    with pytest.raises(ValueError) as exc_info:
        await server.call_tool("unknown_tool", {})
    assert str(exc_info.value) == "Unknown tool: unknown_tool"

@pytest.mark.asyncio
async def test_call_tool_error_handling(server, mock_manager):
    # Setup
    tool_name = "tool1"
    server.repository[tool_name] = Mock(rulesetPath="/test/path")
    mock_manager.invokeDecisionService.side_effect = Exception("Decision service error")

    # Verify error is propagated
    with pytest.raises(Exception) as exc_info:
        await server.call_tool(tool_name, {})
    assert str(exc_info.value) == "Decision service error"

@pytest.mark.asyncio
async def test_call_tool_non_dict_response(server, mock_manager):
    # Setup mock response as string
    mock_manager.invokeDecisionService.return_value = "string_response"
    tool_name = "tool1"
    server.repository[tool_name] = Mock(rulesetPath="/test/path")

    # Execute
    result = await server.call_tool(tool_name, {})

    # Verify string handling
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert result[0].text == "string_response"

# Test trace functionality with new parameters
@pytest.fixture
def server_with_traces_enabled():
    credentials = Credentials(
        odm_url="http://test:9060/res",
        username="test",
        password="test"
    )
    # Explicitly enable traces for testing
    server = DecisionMCPServer(credentials=credentials, traces_dir=None, trace_enable=True, trace_maxsize=10)
    server.manager = Mock()
    return server

@pytest.fixture
def server_with_traces_disabled():
    credentials = Credentials(
        odm_url="http://test:9060/res",
        username="test",
        password="test"
    )
    # Default behavior is traces disabled, but we're explicit here for clarity in tests
    server = DecisionMCPServer(credentials=credentials, traces_dir=None, trace_enable=False, trace_maxsize=10)
    server.manager = Mock()
    return server

@pytest.mark.asyncio
async def test_call_tool_with_traces_enabled(server_with_traces_enabled):
    # Setup mock response
    server_with_traces_enabled.manager.invokeDecisionService.return_value = {
        "result": "decision_result",
        "__DecisionID__": "123"
    }
    
    # Setup test data
    tool_name = "tool1"
    arguments = {"input": "test_value"}
    
    # Add tool to repository
    server_with_traces_enabled.repository[tool_name] = Mock(rulesetPath="/test/path")
    
    # Execute
    result = await server_with_traces_enabled.call_tool(tool_name, arguments)
    
    # Verify trace storage was used
    assert server_with_traces_enabled.execution_traces is not None
    
    # Verify response
    assert len(result) == 1
    assert result[0].type == "text"

@pytest.mark.asyncio
async def test_call_tool_with_traces_disabled(server_with_traces_disabled):
    # Setup mock response
    server_with_traces_disabled.manager.invokeDecisionService.return_value = {
        "result": "decision_result",
        "__DecisionID__": "123"
    }
    
    # Setup test data
    tool_name = "tool1"
    arguments = {"input": "test_value"}
    
    # Add tool to repository
    server_with_traces_disabled.repository[tool_name] = Mock(rulesetPath="/test/path")
    
    # Execute
    result = await server_with_traces_disabled.call_tool(tool_name, arguments)
    
    # Verify trace storage was not used
    assert server_with_traces_disabled.execution_traces is None
    
    # Verify response
    assert len(result) == 1
    assert result[0].type == "text"

@pytest.mark.asyncio
async def test_list_execution_traces_with_traces_disabled(server_with_traces_disabled):
    # Execute
    traces = await server_with_traces_disabled.list_execution_traces()
    
    # Verify empty list is returned when traces are disabled
    assert len(traces) == 0

@pytest.mark.asyncio
async def test_get_execution_trace_with_traces_disabled(server_with_traces_disabled):
    # Execute
    trace = await server_with_traces_disabled.get_execution_trace("any_id")
    
    # Verify None is returned when traces are disabled
    assert trace is None