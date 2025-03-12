"""Diagram Generator Agent"""
from typing import Dict, List, Any, Union, Optional
from pydantic import BaseModel
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent
# Import directly from agents package
from agents import trace, Runner

class DiagramOutput(BaseModel):
    """Structured output for generated diagrams"""
    diagram_type: Optional[str] = None
    diagram_code: Optional[str] = None
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DiagramAgent(BaseAgent):
    """Agent for generating architecture diagrams based on requirements"""
    
    INSTRUCTIONS = """You are an architecture diagram expert. Your task is to:
        1. Analyze the requirements specification
        2. Generate architecture diagrams using Python code
        3. Create clear explanations for each diagram component
        4. Use appropriate diagram types for different aspects
        5. Ensure the diagrams are comprehensive and accurate"""

    def __init__(self):
        """Initialize the DiagramAgent"""
        super().__init__(
            name="Diagram Generator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=None  # Diagram code is better as unstructured text
        )

    async def generate(self, final_spec: str, app_type: str, cloud_env: str) -> str:
        """Generate architecture diagrams from the final requirements
        
        Args:
            final_spec: The final requirements specification
            app_type: The application type (Web Application or Web Service)
            cloud_env: The cloud environment (GCP, AWS, Azure)
            
        Returns:
            Generated diagram code
        """
        with trace("Diagram Generation"):
            diagram_prompt = self._construct_diagram_prompt(final_spec, app_type, cloud_env)
            return await self.run(diagram_prompt)
    
    def _construct_diagram_prompt(self, final_spec: str, app_type: str, cloud_env: str) -> str:
        """Construct the diagram generation prompt
        
        Args:
            final_spec: The final requirements specification
            app_type: The application type
            cloud_env: The cloud environment
            
        Returns:
            Formatted prompt for diagram generation
        """
        return f"""
        Based on the following final requirements, generate Python code for an architecture diagram:
        
        APPLICATION TYPE: {app_type}
        CLOUD ENVIRONMENT: {cloud_env}
        
        REQUIREMENTS:
        {final_spec}
        
        Generate Python code using the 'diagrams' library (https://diagrams.mingrammer.com/) that:
        
        1. Creates a clear, professional architecture diagram
        2. Shows all system components and their relationships
        3. Includes proper labeling and organization
        4. Uses appropriate {cloud_env} services/icons
        5. Matches the requirements for a {app_type}
        
        The code should be complete, executable Python that will generate a PNG file when run.
        Include necessary imports, proper initialization, and clear comments.
        
        Return only the Python code without explanations.
        """