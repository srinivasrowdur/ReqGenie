"""Base Agent Architecture

This module defines the base agent class and common functionality
for all specialized agents in the ReqGenie system.
"""
from typing import List, Optional, Any, Dict, Union, Callable, TypeVar
from pydantic import BaseModel
import asyncio

# Import directly from agents package
from agents import (
    Agent, 
    Runner, 
    GuardrailFunctionOutput, 
    RunContextWrapper,
    input_guardrail, 
    output_guardrail, 
    trace
)

T = TypeVar('T')

class AgentOutput(BaseModel):
    """Base model for structured agent outputs"""
    content: str
    metadata: Dict[str, Any] = {}

class RequirementGuardrailOutput(BaseModel):
    """Output model for requirement guardrails"""
    is_valid: bool
    reasoning: str
    suggestions: List[str] = []

class BaseAgent:
    """Base agent class that all specialized agents will inherit from
    
    This class wraps the openai-agents SDK to provide a consistent interface
    for all ReqGenie agents.
    """
    
    # Default model to use for the agent
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(
        self, 
        name: str,
        instructions: str,
        model: str = None,
        input_guardrails: List[Callable] = None,
        output_guardrails: List[Callable] = None,
        structured_output: Any = None
    ):
        """Initialize a base agent with common configuration
        
        Args:
            name: Agent name
            instructions: Agent system instructions
            model: Model to use (defaults to DEFAULT_MODEL)
            input_guardrails: List of input guardrail functions
            output_guardrails: List of output guardrail functions
            structured_output: Pydantic model for structured output
        """
        self.name = name
        self.instructions = instructions
        self.model = model or self.DEFAULT_MODEL
        
        # Create the agent using openai-agents SDK
        self.agent = Agent(
            name=name,
            instructions=instructions,
            model=self.model,
            input_guardrails=input_guardrails or [],
            output_guardrails=output_guardrails or [],
            output_type=structured_output
        )
    
    async def run(self, input_data: Union[str, List], stream: bool = False) -> Any:
        """Run the agent with the given input
        
        Args:
            input_data: Input data for the agent
            stream: Whether to stream the output
            
        Returns:
            Agent output or stream
        """
        # Convert input to proper format for openai-agents
        formatted_input = input_data
        
        # Run the agent using Runner
        result = await Runner.run(
            self.agent,
            formatted_input,
            stream=stream
        )
        
        # Handle streaming vs. non-streaming outputs
        if stream:
            return result
        else:
            return result.final_output
    
    @staticmethod
    def requirement_format_guardrail():
        """Create a requirement format validation guardrail
        
        This checks if the input requirement has the proper format
        and is detailed enough to proceed.
        """
        guardrail_agent = Agent(
            name="Requirement Format Validator",
            instructions="""
            Check if the provided requirement is properly formatted and detailed enough:
            1. Must be at least 10 words
            2. Must describe a software feature or functionality
            3. Must not be vague or ambiguous
            4. Must not contain prohibited content
            """,
            output_type=RequirementGuardrailOutput
        )
        
        @input_guardrail
        async def validate_requirement_format(
            context: RunContextWrapper[None], 
            agent: Agent, 
            input_data: Union[str, List]
        ) -> GuardrailFunctionOutput:
            """Input guardrail that validates requirement format"""
            # Extract the text content from the input
            content = input_data if isinstance(input_data, str) else str(input_data)
            
            # Use context.run instead of context.client.run
            result = await Runner.run(guardrail_agent, content, context=context.context)
            validation_result = result.final_output_as(RequirementGuardrailOutput)
            
            return GuardrailFunctionOutput(
                output_info=validation_result,
                tripwire_triggered=not validation_result.is_valid
            )
        
        return validate_requirement_format
    
    @staticmethod
    def output_quality_guardrail():
        """Create an output quality validation guardrail
        
        This checks if the agent's output meets quality standards.
        """
        @output_guardrail
        async def validate_output_quality(
            context: RunContextWrapper[None],
            agent: Agent,
            output: str
        ) -> bool:
            """Output guardrail that checks quality standards"""
            # Simple quality check - can be expanded
            min_length = 100
            required_sections = ["Requirements", "Assumptions", "Edge Cases"]
            
            # Check minimum length
            if len(output) < min_length:
                return False
                
            # Check if all required sections are present
            for section in required_sections:
                if section.lower() not in output.lower():
                    return False
                    
            return True
            
        return validate_output_quality

def create_output_quality_guardrail(min_length: int = 100, required_sections: List[str] = None):
    """Create an output quality validation guardrail
    
    This checks if the agent's output meets quality standards.
    """
    sections = required_sections or ["Requirements", "Assumptions", "Edge Cases"]
    
    @output_guardrail
    async def validate_output_quality(
        context: RunContextWrapper[None],
        agent: Agent,
        output: str
    ) -> bool:
        """Output guardrail that checks quality standards"""
        # Check minimum length
        if len(output) < min_length:
            return False
            
        # Check if all required sections are present
        for section in sections:
            if section.lower() not in output.lower():
                return False
                
        return True
        
    return validate_output_quality

async def run_with_output_type(agent: Agent, input_data: Union[str, List[Dict]], output_type: Type[T] = None) -> T:
    """Run an agent and convert its output to the specified type"""
    result = await Runner.run(agent, input_data)
    
    if output_type:
        return result.final_output_as(output_type)
    
    return result.final_output

async def run_streaming(agent: Agent, input_data: Union[str, List[Dict]]):
    """Run an agent with streaming output"""
    # The new SDK doesn't have direct streaming, so simulate with result directly
    result = await Runner.run(agent, input_data)
    return result.final_output 