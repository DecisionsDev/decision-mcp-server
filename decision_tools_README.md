# Decision Center API Tools

This package provides tools for interacting with IBM ODM Decision Center API and generating explanations for decisions.

## Components

### 1. `fetch_decision_rules.py`

A Python module that fetches business rules from IBM ODM Decision Center API and extracts relevant information for decision explanation purposes.

#### Features:
- Connects to Decision Center API using Basic Authentication
- Retrieves rules for a specific project
- Extracts rule information (internalId, permaLink, definition)
- Can be used as a standalone script or imported as a module

#### Usage as a standalone script:
```bash
python fetch_decision_rules.py
```

#### Usage as an imported module:
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

### 2. `example_decision_explanation.py`

An example script demonstrating how to use `fetch_decision_rules.py` as a tool for decision explanation.

#### Features:
- Imports and uses the fetch_decision_rules module
- Processes rules to provide explanations for decisions
- Formats explanations in a user-friendly way
- Handles different rule types (Action Rules and Decision Tables)

#### Usage:
```bash
python example_decision_explanation.py
```

## Integration

These tools can be integrated into larger systems for decision explanation purposes:

1. **Decision Service Integration**: When a decision service returns a result, include the ID of the triggered rule(s)
2. **Explanation Generation**: Use the rule ID to fetch the rule definition and generate an explanation
3. **User Interface**: Display the explanation to the user along with a link to view the rule in Decision Center

## Requirements

- Python 3.6+
- `requests` library
- Access to an IBM ODM Decision Center instance

## Configuration

By default, the tools connect to a Decision Center instance running on `localhost:9060` with the following credentials:
- Username: `odmAdmin`
- Password: `odmAdmin`

You can customize these settings by passing parameters to the `fetch_decision_rules` function.

## Example Output

```
Decision Explanation:

The decision was made because the following condition was met:
the amount of 'the loan' is more than 1,000,000

This resulted in the following action:
add "The loan cannot exceed 1,000,000" to the messages of 'the loan' ;
reject 'the loan' ;

View rule in Decision Center: https://localhost:9453/decisioncenter/t/library/editor?datasource=jdbc%2FilogDataSource&id=brm.ActionRule:45:45&baselineId=brm.Branch:75:75