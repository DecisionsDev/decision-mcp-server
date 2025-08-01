import mcp.types as types
class DecisionServiceDescription:
    """
    Represents a decision service description for a specific tool.
    This class encapsulates the metadata and tool description for a decision service.
    """
    def __init__(self, tool_name, ruleset, input_schema, callback_name= None):
        self.tool_name = tool_name
        self.engine = "odm"
        self.rulesetPath = "/" + ruleset["id"]
        self.callbackName = callback_name
        self.ruleset = ruleset

        self.toolDescription =   types.Tool (
            name=tool_name,
            description=ruleset["description"],
            inputSchema= input_schema,
        )

   