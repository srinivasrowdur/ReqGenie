"""Test Generator Agent"""
from typing import Dict, List, Any, Union, Optional
from pydantic import BaseModel, Field
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent

# Direct imports from the agents package
from agents import trace, Runner

class TestCaseOutput(BaseModel):
    """Structured output for test cases"""
    test_suites: Optional[List[Dict[str, Any]]] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    edge_cases: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class TestGeneratorAgent(BaseAgent):
    """Agent for generating test cases based on requirements"""
    
    INSTRUCTIONS = """You are a test engineering expert. Your task is to:
        1. Analyze the requirements specification
        2. Generate comprehensive test cases
        3. Identify edge cases and boundary conditions
        4. Create verification steps for each test case
        5. Provide expected results"""

    def __init__(self):
        """Initialize the TestGeneratorAgent"""
        super().__init__(
            name="Test Generator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=TestCaseOutput
        )

    async def generate(self, final_spec: str) -> TestCaseOutput:
        """Generate test cases from the final requirements specification
        
        Args:
            final_spec: The final requirements specification
            
        Returns:
            Test cases output
        """
        with trace("Test Case Generation"):
            test_prompt = self._construct_test_prompt(final_spec)
            return await self.run(test_prompt)
    
    def _construct_test_prompt(self, final_spec: str) -> str:
        """Construct the test case generation prompt
        
        Args:
            final_spec: The final requirements specification
            
        Returns:
            Formatted prompt for test generation
        """
        return f"""
        Based on the following final requirements specification, generate comprehensive test cases:
        
        {final_spec}
        
        Create the following:
        
        1. Test Suites: Group test cases by feature or functionality
        2. Test Cases: Include ID, name, purpose, and steps
        3. Edge Cases: Identify boundary conditions and error scenarios
        4. Expected Results: Clearly describe what success looks like
        5. Test Data: Provide sample data for each test case
        
        Format your response as structured test documentation that can be directly used by a QA team.
        """ 