"""Jira Agent for creating tickets from requirements"""
from typing import Dict, List, Any, Union
from pydantic import BaseModel
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent
# Import directly from agents package
from agents import trace, Runner

class JiraTicketOutput(BaseModel):
    """Structured output for Jira tickets"""
    tickets: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class JiraAgent(BaseAgent):
    """Agent for creating Jira tickets from requirements"""
    
    INSTRUCTIONS = """You are a Jira ticket creation expert. Your task is to:
        1. Analyze requirements and create appropriate Jira tickets
        2. Categorize tickets by type (Epic, Story, Task, Bug)
        3. Set appropriate priorities
        4. Create detailed descriptions with acceptance criteria
        5. Link related tickets together"""

    def __init__(self):
        """Initialize the JiraAgent"""
        super().__init__(
            name="Jira Ticket Creator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=JiraTicketOutput
        )

    async def create_tickets(self, 
                           final_spec: str, 
                           test_cases: str, 
                           jira_config: Dict[str, str]) -> JiraTicketOutput:
        """Create Jira tickets from requirements
        
        Args:
            final_spec: The final requirements specification
            test_cases: The test cases
            jira_config: Configuration for Jira ticket creation (project, component)
            
        Returns:
            Jira ticket output
        """
        with trace("Jira Ticket Creation"):
            jira_prompt = self._construct_jira_prompt(final_spec, test_cases, jira_config)
            return await self.run(jira_prompt)
    
    def _construct_jira_prompt(self, 
                              final_spec: str, 
                              test_cases: str, 
                              jira_config: Dict[str, str]) -> str:
        """Construct the Jira ticket creation prompt
        
        Args:
            final_spec: The final requirements specification
            test_cases: The test cases
            jira_config: Configuration for Jira ticket creation
            
        Returns:
            Formatted prompt for Jira ticket creation
        """
        project = jira_config.get("project", "PROJECT")
        component = jira_config.get("component", "")
        component_text = f"Component: {component}" if component else ""
        
        return f"""
        Create Jira tickets based on the following requirements and test cases:
        
        PROJECT: {project}
        {component_text}
        
        REQUIREMENTS:
        {final_spec}
        
        TEST CASES:
        {test_cases}
        
        Create the following ticket types:
        
        1. Epic: High-level feature/requirement
        2. Story: User-focused functionality
        3. Task: Technical implementation tasks
        4. Bug: Potential issues to address
        
        For each ticket include:
        - Summary
        - Description
        - Priority (High, Medium, Low)
        - Acceptance Criteria
        - Estimated Story Points (1, 2, 3, 5, 8, 13)
        - Component (if specified)
        
        Format the output as a structured collection of tickets that can be directly imported into Jira.
        """