#!/usr/bin/env python3
"""
Elaborator Agent for ReqGenie

This agent takes a requirement as input and elaborates on it, providing more details
and structured information.
"""
import os
import asyncio
from typing import Optional, List, Dict, Any, AsyncIterator
from pydantic import BaseModel, Field
from agents import Agent, Runner, StreamEvent


class ElaborationOutput(BaseModel):
    """Structured output for the elaboration process"""
    overview: str = Field(..., description="A brief overview of the elaborated requirement")
    functional_requirements: List[str] = Field(..., description="List of detailed functional requirements")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies and prerequisites")
    considerations: List[str] = Field(default_factory=list, description="Additional considerations and notes")
    
    def __str__(self) -> str:
        """String representation of the output for easy printing"""
        output = [
            "# Elaborated Requirement\n",
            f"## Overview\n{self.overview}\n",
            "## Functional Requirements\n"
        ]
        
        for i, req in enumerate(self.functional_requirements, 1):
            output.append(f"{i}. {req}\n")
        
        if self.dependencies:
            output.append("\n## Dependencies\n")
            for i, dep in enumerate(self.dependencies, 1):
                output.append(f"{i}. {dep}\n")
        
        if self.considerations:
            output.append("\n## Considerations\n")
            for i, consideration in enumerate(self.considerations, 1):
                output.append(f"{i}. {consideration}\n")
        
        return "".join(output)


class ElaboratorAgent:
    """Agent for elaborating on software requirements"""
    
    def __init__(self, model: str = "gpt-4o"):
        """Initialize the agent with the specified model"""
        self.model = model
        self.system_prompt = """
        You are a Senior Requirements Analyst specialized in elaborating software requirements.
        Your task is to take a brief requirement description and transform it into a detailed,
        comprehensive elaboration that provides clarity for developers.
        
        For each requirement, you should:
        1. Provide a clear overview of the requirement
        2. Break down the requirement into specific functional aspects
        3. Identify dependencies and prerequisites
        4. Note any important considerations or potential challenges
        
        Structure your response in the following format:
        
        Overview: A summary of the requirement
        
        Functional Requirements:
        - Detailed requirement 1
        - Detailed requirement 2
        - ...
        
        Dependencies:
        - Dependency 1
        - Dependency 2
        - ...
        
        Considerations:
        - Consideration 1
        - Consideration 2
        - ...
        
        Ensure your elaboration is specific, actionable, and provides sufficient detail for
        developers to understand what needs to be built.
        """
    
    async def elaborate_requirement(self, requirement: str, app_type: Optional[str] = None, stream: bool = False) -> Any:
        """
        Elaborate on a requirement, providing more details and structure
        
        Args:
            requirement: The original requirement text
            app_type: Optional application type for context
            stream: Whether to stream the response
        
        Returns:
            ElaborationOutput or a stream of events if stream=True
        """
        # Create the agent with very clear formatting instructions
        system_prompt = self.system_prompt + """
        You MUST format your response EXACTLY as follows:

        Overview: [Your comprehensive overview goes here, all in one paragraph]

        Functional Requirements:
        - [First functional requirement]
        - [Second functional requirement]
        - [Third functional requirement]
        - [And so on...]

        Dependencies:
        - [First dependency]
        - [Second dependency]
        - [And so on...]

        Considerations:
        - [First consideration]
        - [Second consideration]
        - [And so on...]

        DO NOT deviate from this format. Ensure each section has content and uses the exact headings above.
        """
        
        agent = Agent(
            name="RequirementElaborator",
            instructions=system_prompt,
            model=self.model
        )
        
        # Prepare the input prompt
        input_prompt = f"Requirement: {requirement}\n"
        if app_type:
            input_prompt += f"Application Type: {app_type}\n"
        
        input_prompt += """
        Please elaborate on this requirement, providing a comprehensive analysis.
        
        Your response MUST follow this EXACT format:
        
        Overview: [comprehensive overview]
        
        Functional Requirements:
        - [detailed requirement 1]
        - [detailed requirement 2]
        - ... (at least 3-5 requirements)
        
        Dependencies:
        - [dependency 1]
        - [dependency 2]
        - ...
        
        Considerations:
        - [consideration 1]
        - [consideration 2]
        - ...
        """
        
        # Run the agent
        if stream:
            return await self._stream_elaboration(agent, input_prompt)
        else:
            result = await Runner.run(agent, input_prompt)
            # Parse the structured text output into our model
            return self._parse_output(result.final_output)
    
    async def _stream_elaboration(self, agent, input_prompt) -> AsyncIterator[StreamEvent]:
        """Return a streaming response from the agent"""
        result = Runner.run_streamed(agent, input_prompt)
        return result.stream_events()
    
    def _parse_output(self, text_output: str) -> ElaborationOutput:
        """Parse text output into structured ElaborationOutput model"""
        # Default values
        overview = ""
        functional_reqs = []
        dependencies = []
        considerations = []
        
        # Processing state
        current_section = None
        
        # Process each line
        for line in text_output.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check for section headers
            if line.lower().startswith('overview:'):
                current_section = 'overview'
                overview = line[len('overview:'):].strip()
            elif line.lower() == 'overview':
                current_section = 'overview'
            elif line.lower().startswith('functional requirements:') or line.lower() == 'functional requirements':
                current_section = 'functional'
            elif line.lower().startswith('dependencies:') or line.lower() == 'dependencies':
                current_section = 'dependencies'
            elif line.lower().startswith('considerations:') or line.lower() == 'considerations':
                current_section = 'considerations'
            # Process line based on current section
            elif current_section == 'overview' and not line.startswith('-'):
                overview += " " + line
            elif current_section == 'functional' and line.startswith('-'):
                functional_reqs.append(line[1:].strip())
            elif current_section == 'dependencies' and line.startswith('-'):
                dependencies.append(line[1:].strip())
            elif current_section == 'considerations' and line.startswith('-'):
                considerations.append(line[1:].strip())
        
        # Create and return the model
        return ElaborationOutput(
            overview=overview,
            functional_requirements=functional_reqs,
            dependencies=dependencies,
            considerations=considerations
        )


async def main():
    """Example usage of the ElaboratorAgent"""
    elaborator = ElaboratorAgent()
    
    # Example requirement
    requirement = "Create a user registration form with validation"
    app_type = "Web Application"
    
    print(f"Processing requirement: '{requirement}'")
    print(f"App type: {app_type}\n")
    
    # Get non-streaming result
    elaboration = await elaborator.elaborate_requirement(requirement, app_type)
    print(f"Elaboration result:\n{elaboration}\n")
    
    # Example of streaming output
    print("Streaming example:")
    stream = await elaborator.elaborate_requirement(requirement, app_type, stream=True)
    
    async for event in stream:
        if event.type == "raw_response_event":
            # Extract content from the event
            if hasattr(event.data, "content") and event.data.content:
                print(event.data.content, end="", flush=True)
            elif hasattr(event.data, "delta") and hasattr(event.data.delta, "content") and event.data.delta.content:
                print(event.data.delta.content, end="", flush=True)
            elif hasattr(event.data, "choices") and event.data.choices:
                # Handle OpenAI API format
                for choice in event.data.choices:
                    if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                        print(choice.delta.content, end="", flush=True)
        elif event.type == "run_item_stream_event" and event.name == "output" and event.item and hasattr(event.item, "output"):
            print("\n\nStructured output:", event.item.output)


if __name__ == "__main__":
    asyncio.run(main()) 