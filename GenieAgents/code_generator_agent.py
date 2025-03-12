"""Code Generator Agent"""
from typing import Dict, List, Any, Union, Optional
from pydantic import BaseModel
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent
# Import directly from agents package
from agents import trace, Runner

class CodeOutput(BaseModel):
    """Structured output for generated code"""
    code: str
    language: str
    files: List[Dict[str, str]]
    metadata: Optional[Dict[str, Any]] = None

class CodeGeneratorAgent(BaseAgent):
    """Agent for generating code based on requirements"""
    
    INSTRUCTIONS = """You are an expert software developer. Your task is to:
        1. Analyze the requirements specification
        2. Generate high-quality, production-ready code
        3. Follow best practices for the specified language
        4. Include comments and documentation
        5. Implement proper error handling and validation"""

    def __init__(self):
        """Initialize the CodeGeneratorAgent"""
        super().__init__(
            name="Code Generator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=None  # Code is better as unstructured text
        )

    async def generate(self, final_spec: str, language: str = "Python") -> str:
        """Generate code from the final requirements specification
        
        Args:
            final_spec: The final requirements specification
            language: The programming language to use
            
        Returns:
            Generated code
        """
        with trace("Code Generation"):
            code_prompt = self._construct_code_prompt(final_spec, language)
            return await self.run(code_prompt)
    
    def _construct_code_prompt(self, final_spec: str, language: str) -> str:
        """Construct the code generation prompt
        
        Args:
            final_spec: The final requirements specification
            language: The programming language to use
            
        Returns:
            Formatted prompt for code generation
        """
        return f"""
        Based on the following final requirements specification, generate {language} code:
        
        {final_spec}
        
        Create production-ready code that:
        
        1. Implements all functional requirements
        2. Follows best practices for {language}
        3. Includes proper error handling
        4. Has clear comments and documentation
        5. Is maintainable and extensible
        
        Return only the code, formatted with appropriate syntax highlighting. Include any necessary setup files (e.g., package.json, requirements.txt) as needed.
        """ 