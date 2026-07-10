# Copyright contributors to the IBM ODM MCP Server project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import types

import pytest

# Patch mcp.types before importing the class under test
class DummyTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.input_schema = inputSchema

dummy_types = types.SimpleNamespace(Tool=DummyTool)
sys.modules['mcp_types'] = dummy_types

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
    assert desc.tool_description.input_schema == input_schema