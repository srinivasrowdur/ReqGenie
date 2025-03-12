"""
Output Formatter

Utilities for formatting structured output into readable text formats.
"""
from typing import Dict, List, Any, Optional, Union
import json

class OutputFormatter:
    """Format structured output into human-readable text"""
    
    @classmethod
    def format_elaboration(cls, data: Dict[str, Any]) -> str:
        """Format elaboration output to text"""
        formatted_text = "# Elaborated Requirements\n\n"
        
        # Format functional requirements
        if "functional_requirements" in data and data["functional_requirements"]:
            formatted_text += "## Functional Requirements\n\n"
            for i, req in enumerate(data["functional_requirements"], 1):
                formatted_text += f"{i}. {req}\n"
            formatted_text += "\n"
        
        # Format assumptions
        if "assumptions" in data and data["assumptions"]:
            formatted_text += "## Assumptions\n\n"
            for i, assumption in enumerate(data["assumptions"], 1):
                formatted_text += f"{i}. {assumption}\n"
            formatted_text += "\n"
        
        # Format edge cases
        if "edge_cases" in data and data["edge_cases"]:
            formatted_text += "## Edge Cases\n\n"
            for i, edge_case in enumerate(data["edge_cases"], 1):
                formatted_text += f"{i}. {edge_case}\n"
            formatted_text += "\n"
        
        # Format acceptance criteria
        if "acceptance_criteria" in data and data["acceptance_criteria"]:
            formatted_text += "## Acceptance Criteria\n\n"
            for i, criteria in enumerate(data["acceptance_criteria"], 1):
                formatted_text += f"{i}. {criteria}\n"
        
        return formatted_text
    
    @classmethod
    def format_test_cases(cls, data: Dict[str, Any]) -> str:
        """Format test case output to text"""
        formatted_text = "# Test Cases\n\n"
        
        # Format test suites
        if "test_suites" in data and data["test_suites"]:
            formatted_text += "## Test Suites\n\n"
            for i, suite in enumerate(data["test_suites"], 1):
                suite_id = suite.get("id", f"TS-{i}")
                suite_name = suite.get("name", f"Test Suite {i}")
                formatted_text += f"### {suite_id}: {suite_name}\n\n"
                
                description = suite.get("description", "")
                if description:
                    formatted_text += f"{description}\n\n"
        
        # Format test cases
        if "test_cases" in data and data["test_cases"]:
            formatted_text += "## Test Cases\n\n"
            for i, test in enumerate(data["test_cases"], 1):
                test_id = test.get("id", f"TC-{i}")
                test_name = test.get("name", f"Test Case {i}")
                formatted_text += f"### {test_id}: {test_name}\n\n"
                
                # Test description
                description = test.get("description", "")
                if description:
                    formatted_text += f"**Description**: {description}\n\n"
                
                # Test steps
                steps = test.get("steps", [])
                if steps:
                    formatted_text += "**Steps**:\n"
                    for j, step in enumerate(steps, 1):
                        formatted_text += f"{j}. {step}\n"
                    formatted_text += "\n"
                
                # Expected results
                expected = test.get("expected_result", "")
                if expected:
                    formatted_text += f"**Expected Result**: {expected}\n\n"
        
        # Format edge cases
        if "edge_cases" in data and data["edge_cases"]:
            formatted_text += "## Edge Cases\n\n"
            for i, edge_case in enumerate(data["edge_cases"], 1):
                edge_id = edge_case.get("id", f"EC-{i}")
                edge_name = edge_case.get("name", f"Edge Case {i}")
                formatted_text += f"### {edge_id}: {edge_name}\n\n"
                
                description = edge_case.get("description", "")
                if description:
                    formatted_text += f"{description}\n\n"
                
                # Test data
                test_data = edge_case.get("test_data", "")
                if test_data:
                    formatted_text += f"**Test Data**: {test_data}\n\n"
        
        return formatted_text
    
    @classmethod
    def format_validation(cls, data: Dict[str, Any]) -> str:
        """Format validation output to text"""
        formatted_text = "# Validation Results\n\n"
        
        # Format scores
        if "completeness_score" in data:
            formatted_text += "## Quality Scores\n\n"
            formatted_text += f"- Completeness: {data.get('completeness_score', 'N/A')}/10\n"
            formatted_text += f"- Consistency: {data.get('consistency_score', 'N/A')}/10\n"
            formatted_text += f"- Testability: {data.get('testability_score', 'N/A')}/10\n"
            formatted_text += f"- NFR Compliance: {data.get('nfr_compliance_score', 'N/A')}/10\n"
            formatted_text += f"- Overall Quality: {data.get('overall_quality_score', 'N/A')}/10\n\n"
        
        # Format issues
        if "issues" in data and data["issues"]:
            formatted_text += "## Issues\n\n"
            for i, issue in enumerate(data["issues"], 1):
                category = issue.get("category", "General")
                description = issue.get("description", "No description provided")
                formatted_text += f"{i}. **{category}**: {description}\n"
            formatted_text += "\n"
        
        # Format recommendations
        if "recommendations" in data and data["recommendations"]:
            formatted_text += "## Recommendations\n\n"
            for i, recommendation in enumerate(data["recommendations"], 1):
                formatted_text += f"{i}. {recommendation}\n"
        
        return formatted_text
    
    @classmethod
    def format_jira_tickets(cls, data: Dict[str, Any]) -> str:
        """Format Jira ticket output to text"""
        formatted_text = "# Jira Tickets\n\n"
        
        # Format tickets
        if "tickets" in data and data["tickets"]:
            for i, ticket in enumerate(data["tickets"], 1):
                ticket_type = ticket.get("type", "Task")
                summary = ticket.get("summary", f"Ticket {i}")
                formatted_text += f"## {ticket_type}: {summary}\n\n"
                
                # Description
                description = ticket.get("description", "")
                if description:
                    formatted_text += f"**Description**:\n{description}\n\n"
                
                # Priority
                priority = ticket.get("priority", "")
                if priority:
                    formatted_text += f"**Priority**: {priority}\n"
                
                # Story Points
                points = ticket.get("story_points", "")
                if points:
                    formatted_text += f"**Story Points**: {points}\n"
                
                # Acceptance Criteria
                criteria = ticket.get("acceptance_criteria", [])
                if criteria:
                    formatted_text += "\n**Acceptance Criteria**:\n"
                    for j, criterion in enumerate(criteria, 1):
                        formatted_text += f"{j}. {criterion}\n"
                
                formatted_text += "\n---\n\n"
        
        return formatted_text
    
    @classmethod
    def format_code_review(cls, data: Dict[str, Any]) -> str:
        """Format code review output to text"""
        formatted_text = "# Code Review\n\n"
        
        # Format scores
        if "quality_score" in data:
            formatted_text += "## Quality Scores\n\n"
            formatted_text += f"- Code Quality: {data.get('quality_score', 'N/A')}/10\n"
            formatted_text += f"- Maintainability: {data.get('maintainability_score', 'N/A')}/10\n"
            formatted_text += f"- Security: {data.get('security_score', 'N/A')}/10\n"
            formatted_text += f"- Performance: {data.get('performance_score', 'N/A')}/10\n\n"
        
        # Format issues
        if "issues" in data and data["issues"]:
            formatted_text += "## Issues\n\n"
            for i, issue in enumerate(data["issues"], 1):
                category = issue.get("category", "General")
                description = issue.get("description", "No description provided")
                formatted_text += f"{i}. **{category}**: {description}\n"
            formatted_text += "\n"
        
        # Format recommendations
        if "recommendations" in data and data["recommendations"]:
            formatted_text += "## Recommendations\n\n"
            for i, recommendation in enumerate(data["recommendations"], 1):
                formatted_text += f"{i}. {recommendation}\n"
        
        return formatted_text
    
    @classmethod
    def format_final_spec(cls, data: Dict[str, Any]) -> str:
        """Format final specification output to text"""
        formatted_text = "# Final Requirements Specification\n\n"
        
        # Executive Summary
        if "executive_summary" in data:
            formatted_text += "## Executive Summary\n\n"
            formatted_text += f"{data['executive_summary']}\n\n"
        
        # Use Cases
        if "use_cases" in data and data["use_cases"]:
            formatted_text += "## Use Cases\n\n"
            for i, use_case in enumerate(data["use_cases"], 1):
                uc_id = use_case.get("id", f"UC-{i}")
                uc_name = use_case.get("name", f"Use Case {i}")
                formatted_text += f"### {uc_id}: {uc_name}\n\n"
                
                # Description
                description = use_case.get("description", "")
                if description:
                    formatted_text += f"**Description**: {description}\n\n"
                
                # Actors
                actors = use_case.get("actors", [])
                if actors:
                    formatted_text += "**Actors**: " + ", ".join(actors) + "\n\n"
                
                # Flow
                flow = use_case.get("flow", [])
                if flow:
                    formatted_text += "**Flow**:\n"
                    for j, step in enumerate(flow, 1):
                        formatted_text += f"{j}. {step}\n"
                    formatted_text += "\n"
        
        # Functional Requirements
        if "functional_requirements" in data and data["functional_requirements"]:
            formatted_text += "## Functional Requirements\n\n"
            for i, req in enumerate(data["functional_requirements"], 1):
                req_id = req.get("id", f"FR-{i}")
                req_description = req.get("description", "")
                formatted_text += f"### {req_id}\n\n{req_description}\n\n"
        
        # Non-Functional Requirements
        if "non_functional_requirements" in data and data["non_functional_requirements"]:
            formatted_text += "## Non-Functional Requirements\n\n"
            for i, nfr in enumerate(data["non_functional_requirements"], 1):
                nfr_type = nfr.get("type", "General")
                nfr_description = nfr.get("description", "")
                formatted_text += f"### {nfr_type}\n\n{nfr_description}\n\n"
        
        # Implementation Considerations
        if "implementation_considerations" in data:
            formatted_text += "## Implementation Considerations\n\n"
            for key, value in data["implementation_considerations"].items():
                formatted_text += f"### {key}\n\n"
                if isinstance(value, str):
                    formatted_text += f"{value}\n\n"
                elif isinstance(value, list):
                    for item in value:
                        formatted_text += f"- {item}\n"
                    formatted_text += "\n"
        
        # Acceptance Criteria
        if "acceptance_criteria" in data and data["acceptance_criteria"]:
            formatted_text += "## Acceptance Criteria\n\n"
            for i, criteria in enumerate(data["acceptance_criteria"], 1):
                ac_id = criteria.get("id", f"AC-{i}")
                ac_description = criteria.get("description", "")
                formatted_text += f"### {ac_id}\n\n{ac_description}\n\n"
        
        # Assumptions and Constraints
        if "assumptions_and_constraints" in data and data["assumptions_and_constraints"]:
            formatted_text += "## Assumptions and Constraints\n\n"
            for i, item in enumerate(data["assumptions_and_constraints"], 1):
                formatted_text += f"{i}. {item}\n"
        
        return formatted_text
    
    @classmethod
    def format_structured_output(cls, data: Dict[str, Any], output_type: str = None) -> str:
        """Format any structured output to text based on its detected type"""
        if not data:
            return "No data available."
        
        # Try to determine the output type from the content if not specified
        if not output_type:
            if "test_suites" in data and "test_cases" in data:
                output_type = "test_cases"
            elif "quality_score" in data and "maintainability_score" in data:
                output_type = "code_review"
            elif "functional_requirements" in data and "assumptions" in data:
                output_type = "elaboration"
            elif "completeness_score" in data:
                output_type = "validation"
            elif "tickets" in data:
                output_type = "jira_tickets"
            elif "executive_summary" in data and "functional_requirements" in data:
                output_type = "final_spec"
        
        # Format based on determined type
        if output_type == "elaboration":
            return cls.format_elaboration(data)
        elif output_type == "test_cases":
            return cls.format_test_cases(data)
        elif output_type == "validation":
            return cls.format_validation(data)
        elif output_type == "jira_tickets":
            return cls.format_jira_tickets(data)
        elif output_type == "code_review":
            return cls.format_code_review(data)
        elif output_type == "final_spec":
            return cls.format_final_spec(data)
        
        # Default formatting if type can't be determined
        try:
            return "# Structured Output\n\n" + json.dumps(data, indent=2)
        except:
            return str(data)
    
    @classmethod
    def format_any_output(cls, output: Union[Dict[str, Any], str, Any], output_type: str = None) -> str:
        """Format any output to text, handling various input types"""
        # If it's already a string, just return it
        if isinstance(output, str):
            return output
        
        # If it's a dict, format it as structured output
        if isinstance(output, dict):
            return cls.format_structured_output(output, output_type)
        
        # If it's a Pydantic model or has a dict method, convert to dict first
        if hasattr(output, "dict") and callable(getattr(output, "dict")):
            return cls.format_structured_output(output.dict(), output_type)
        
        # Fallback to string representation
        return str(output) 