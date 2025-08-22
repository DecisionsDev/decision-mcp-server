#!/usr/bin/env python3
"""
Example script demonstrating how to use fetch_decision_rules as a tool
for decision explanation.

This script shows how to:
1. Import and use the fetch_decision_rules module
2. Process the rules to provide explanations for decisions
3. Format the explanations in a user-friendly way
"""

import json
from fetch_decision_rules import fetch_decision_rules


def explain_decision(rule_ids, decision_data):
    """
    Generate an explanation for a decision based on the rules that were triggered.
    
    Args:
        rule_ids (list or str): The ID(s) of the rules that were triggered
                               Can be a single rule ID string or a list of rule IDs
        decision_data (dict): Additional data about the decision
        
    Returns:
        str: A human-readable explanation of the decision
    """
    # Convert single rule ID to list for consistent processing
    if isinstance(rule_ids, str):
        rule_ids = [rule_ids]
    
    # Fetch all rules from the Decision Center
    print("Fetching rules from Decision Center...")
    rules = fetch_decision_rules(verbose=False)
    
    if not rules:
        return "No rules found to explain the decision."
    
    # Process each triggered rule
    explanations = []
    for i, rule_id in enumerate(rule_ids):
        # Check if the triggered rule exists in our rules dictionary
        if rule_id not in rules:
            explanations.append(f"Rule with ID '{rule_id}' not found in the Decision Center.")
            continue
        
        # Get the rule definition
        rule_def = rules[rule_id]["definition"]
        rule_link = rules[rule_id]["permaLink"]
        
        # Generate explanation based on rule type
        if "ActionRule" in rule_id:
            rule_explanation = explain_action_rule(rule_def, decision_data)
        elif "DecisionTable" in rule_id:
            rule_explanation = explain_decision_table(rule_def, decision_data)
        else:
            rule_explanation = f"Unknown rule type for rule ID: {rule_id}"
        
        # Add link to the rule in Decision Center
        rule_explanation += f"\n\nView rule in Decision Center: {rule_link}"
        
        # Add rule number if multiple rules
        if len(rule_ids) > 1:
            rule_explanation = f"Rule {i+1} of {len(rule_ids)}:\n" + rule_explanation
        
        explanations.append(rule_explanation)
    
    # Combine all explanations
    if len(rule_ids) > 1:
        combined_explanation = "Multiple rules were triggered in this decision:\n\n"
        combined_explanation += "\n\n" + "="*40 + "\n\n".join(explanations)
        return combined_explanation
    else:
        return explanations[0] if explanations else "No explanations generated."


def explain_action_rule(rule_def, decision_data):
    """
    Generate an explanation for an action rule.
    
    Args:
        rule_def (str): The definition of the action rule
        decision_data (dict): Additional data about the decision
        
    Returns:
        str: A human-readable explanation of the action rule
    """
    # Simple parsing of if-then structure
    if_part = ""
    then_part = ""
    
    if "if" in rule_def and "then" in rule_def:
        parts = rule_def.split("then", 1)
        if_part = parts[0].replace("if", "").strip()
        then_part = parts[1].strip()
    
    explanation = "Decision Explanation:\n\n"
    explanation += f"The decision was made because the following condition was met:\n{if_part}\n\n"
    explanation += f"This resulted in the following action:\n{then_part}"
    
    return explanation


def explain_decision_table(rule_def, decision_data):
    """
    Generate an explanation for a decision table rule.
    
    Args:
        rule_def (str): The definition of the decision table rule
        decision_data (dict): Additional data about the decision
        
    Returns:
        str: A human-readable explanation of the decision table rule
    """
    # For decision tables, we'll provide a simplified explanation
    # A more sophisticated implementation would parse the XML structure
    
    explanation = "Decision Explanation:\n\n"
    explanation += "The decision was made based on a decision table that evaluates "
    explanation += "multiple conditions such as debt-to-income ratio and credit score.\n\n"
    
    # Extract precondition if available
    if "<Preconditions>" in rule_def:
        try:
            precond_start = rule_def.find("<Preconditions>")
            precond_end = rule_def.find("</Preconditions>")
            precond_text = rule_def[precond_start:precond_end]
            
            # Extract the CDATA content
            cdata_start = precond_text.find("<![CDATA[")
            cdata_end = precond_text.find("]]>")
            if cdata_start > -1 and cdata_end > -1:
                precond = precond_text[cdata_start + 9:cdata_end].strip()
                explanation += f"The table was applied because: {precond}\n\n"
        except Exception:
            pass
    
    explanation += "For more details, please view the decision table in the Decision Center."
    
    return explanation


def main():
    """
    Main function demonstrating the use of the explanation tool.
    """
    # Example decision data
    decision_data = {
        "loan": {
            "amount": 1500000,
            "yearly_repayment": 75000,
            "approved": False,
            "messages": ["The loan cannot exceed 1,000,000"]
        },
        "borrower": {
            "credit_score": 720,
            "yearly_income": 100000
        }
    }
    
    # Example rule IDs that were triggered for this decision
    triggered_rule_ids = [
        "brm.ActionRule:45:45",  # Maximum amount rule
        "brm.ActionRule:46:46"   # Minimum income rule
    ]
    
    # Generate explanation for multiple rules
    explanation = explain_decision(triggered_rule_ids, decision_data)
    
    # Print the explanation
    print("\n" + "=" * 50)
    print(explanation)
    print("=" * 50)


if __name__ == "__main__":
    main()

# Made with Bob
