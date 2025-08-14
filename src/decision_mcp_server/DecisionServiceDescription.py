import mcp.types as types
class DecisionServiceDescription:
    """
    Represents a decision service description for a specific tool.
    This class encapsulates the metadata and tool description for a decision service.
    Attributes:
        tool_name (str): The name of the tool associated with the decision service.
        engine (str): The engine used for decision processing (default is "odm").
        rulesetPath (str): The path to the ruleset, constructed from the ruleset's ID.
        ruleset (dict): The ruleset metadata dictionary.
        tool_description (types.Tool): An object describing the tool, including its name, description, and input schema.

    Args:
        tool_name (str): The name of the tool.
        ruleset (dict): The ruleset metadata, must contain at least "id" and "description" keys.
        input_schema (dict): The schema describing the expected input for the tool.
    """
    def __init__(self, tool_name, ruleset, description, input_schema):
        self.tool_name = tool_name
        self.engine = "odm"
        self.description = description
        self.rulesetPath = "/" + str(ruleset["id"])
        self.ruleset = ruleset

        self.tool_description = types.Tool(
            name=tool_name,
            description=description,
            inputSchema=input_schema,
        )

   