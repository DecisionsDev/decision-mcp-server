import mcp.types as types
class DecisionServiceDescription:
    """
    Represents a decision service description for a specific tool.
    This class encapsulates the metadata and tool description for a decision service.
    Attributes:
        tool_name (str): The name of the tool associated with the decision service.
        engine (str): The engine used for decision processing (default is "odm").
        rulesetPath (str): The path to the ruleset, constructed from the ruleset's ID.
        callbackName (str, optional): The name of the callback function, if any.
        ruleset (dict): The ruleset metadata dictionary.
        tool_description (types.Tool): An object describing the tool, including its name, description, and input schema.

    Args:
        tool_name (str): The name of the tool.
        ruleset (dict): The ruleset metadata, must contain at least "id" and "description" keys.
        input_schema (dict): The schema describing the expected input for the tool.
        callback_name (str, optional): The name of the callback function to be used (default is None).
    """
    def __init__(self, tool_name, ruleset, input_schema, callback_name=None):
        self.tool_name = tool_name
        self.engine = "odm"
        self.rulesetPath = "/" + str(ruleset["id"])
        self.callbackName = callback_name
        self.ruleset = ruleset

        self.tool_description = types.Tool(
            name=tool_name,
            description=ruleset["description"],
            inputSchema=input_schema,
        )

   