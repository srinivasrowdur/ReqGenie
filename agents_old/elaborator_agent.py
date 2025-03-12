"""Requirement Elaborator Agent"""
from typing import Dict, List, Any, Union
from pydantic import BaseModel
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent, RequirementGuardrailOutput
# Import directly from openai_agents
from openai_agents import trace, Runner

class ElaborationOutput(BaseModel):
    """Structured output for elaboration results"""
    functional_requirements: List[str]
    assumptions: List[str]
    edge_cases: List[str]
    acceptance_criteria: List[str]
    metadata: Dict[str, Any] = {}

class ElaboratorAgent(BaseAgent):
    """Agent for elaborating high-level requirements into detailed specifications"""
    
    INSTRUCTIONS = """You are a requirement analysis expert. When given a single line requirement and application type:
        1. Expand it into detailed functional requirements, considering:
           - If Web Application: UI/UX, frontend components, user interactions
           - If Web Service: API endpoints, data formats, integration points
        2. Consider provided Non-Functional Requirements (NFRs)
        3. List any assumptions made
        4. Identify potential edge cases
        5. Suggest acceptance criteria"""

    def __init__(self):
        """Initialize the ElaboratorAgent with input guardrails"""
        super().__init__(
            name="Requirement Elaborator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            input_guardrails=[self.requirement_format_guardrail()],
            output_guardrails=[self.output_quality_guardrail()],
            structured_output=ElaborationOutput
        )

    async def elaborate_requirements(self, requirement: str, app_type: str):
        """
        Elaborate the given requirement based on application type with guardrails.
        Returns the elaboration result.
        """
        initial_prompt = f"Requirement: {requirement}\nApplication Type: {app_type}"
        
        # Use trace to track this operation
        with trace("Requirement Elaboration"):
            return await self.run(initial_prompt)

    async def analyze_nfr(self, nfr_content: str, app_type: str):
        """
        Analyze non-functional requirements with guardrails.
        Returns the analysis result.
        """
        nfr_prompt = self.get_nfr_analysis_prompt(nfr_content, app_type)
        
        # Use trace to track this operation
        with trace("NFR Analysis"):
            return await self.run(nfr_prompt)

    async def process_requirements_parallel(self, requirement: str, app_type: str, nfr_content: str = None):
        """
        Process functional and non-functional requirements in parallel
        """
        # Use trace to track this parallel operation
        with trace("Parallel Requirements Processing"):
            tasks = [self.elaborate_requirements(requirement, app_type)]
            
            if nfr_content:
                tasks.append(self.analyze_nfr(nfr_content, app_type))
            
            # Run both tasks in parallel
            results = await asyncio.gather(*tasks)
            
            # Return the results (first is always elaboration, second is NFR if provided)
            if len(results) == 1:
                return results[0]
            else:
                return results[0], results[1]

    @staticmethod
    def get_nfr_analysis_prompt(nfr_content: str, app_type: str) -> str:
        """Returns the NFR analysis prompt template."""
        return f"""Original NFR Document Content:
        {nfr_content}

        Analyze these Non-Functional Requirements for a {app_type}. 
        Structure your analysis as follows:

        1. NFR CATEGORIES IDENTIFICATION
        First, clearly identify and list all NFR categories present in the document (e.g., Performance, Security, Scalability, etc.)

        2. DETAILED CATEGORY ANALYSIS
        For each identified category, provide:
           a) Category Name
           b) Description
           c) Specific Requirements List
           d) Quantifiable Metrics
           e) Implementation Guidelines
           f) Validation Criteria
           g) Dependencies with other NFRs

        3. CROSS-CUTTING CONCERNS
           - How different NFR categories interact
           - Potential conflicts between categories
           - Priority order of NFR categories

        4. IMPLEMENTATION IMPACT
           - Impact on system architecture
           - Impact on development process
           - Resource requirements per category

        Format the response in a clear, categorical structure that can be easily referenced in subsequent analyses.""" 