import sys
import types

import pytest

# Patch mcp.types before importing the class under test
class DummyTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

dummy_types = types.SimpleNamespace(Tool=DummyTool)
sys.modules['mcp.types'] = dummy_types

from decision_mcp_server.DecisionServiceDescription import DecisionServiceDescription

def test_decision_service_description_initialization():
    tool_name = "test_tool"
    ruleset = {"id": "ruleset1", "description": "A test ruleset"}
    description = "A tool description"  # This should be a string
    input_schema = {"type": "object", "properties": {"foo": {"type": "string"}}}

    # Correct order of parameters: tool_name, ruleset, description, input_schema
    desc = DecisionServiceDescription(tool_name, ruleset, description, input_schema)
    
    assert desc.tool_name == tool_name
    assert desc.description == description
    assert desc.rulesetPath == "/ruleset1"
    assert desc.ruleset == ruleset
    assert desc.tool_description.name == tool_name
    assert desc.tool_description.description == description
    assert desc.tool_description.inputSchema == input_schema