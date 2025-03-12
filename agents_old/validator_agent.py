"""Requirement Validator Agent"""
from typing import Dict, List, Any, Union
from pydantic import BaseModel
import asyncio

from .base_agent import BaseAgent
from agents import trace, Runner

class ValidationOutput(BaseModel):
    """Structured output for validation results"""
    completeness_score: int  # 1-10
    consistency_score: int   # 1-10
    testability_score: int   # 1-10
    nfr_compliance_score: int  # 1-10
    overall_quality_score: int  # 1-10
    issues: List[Dict[str, str]]
    recommendations: List[str]
    metadata: Dict[str, Any] = {}

class ValidatorAgent(BaseAgent):
    """Agent that validates requirements using the LLM-as-a-judge pattern"""
    
    INSTRUCTIONS = """You are a senior technical reviewer. Review the elaborated requirements and:
        1. Identify any gaps and inconsistencies
        2. Check if all edge cases are covered
        3. Validate if the acceptance criteria are testable
        4. Verify compliance with Non-Functional Requirements (NFRs)
        5. Provide specific improvement suggestions
        
        Structure your review as follows:
        
        A. COMPLETENESS ANALYSIS
        - Identify missing requirements
        - Check for undefined terms or concepts
        - Verify all user roles are defined
        - Ensure all scenarios are covered
        
        B. CONSISTENCY CHECK
        - Check for conflicting requirements
        - Verify terminology consistency
        - Validate business rule consistency
        - Check for technical feasibility
        
        C. TESTABILITY REVIEW
        - Evaluate measurability of requirements
        - Check for clear success criteria
        - Identify untestable requirements
        - Suggest improvements for testability
        
        D. NFR COMPLIANCE
        - Verify alignment with NFRs
        - Identify NFR conflicts
        - Check NFR feasibility
        - Suggest NFR improvements
        
        E. EDGE CASES AND RISKS
        - List potential edge cases
        - Identify security concerns
        - Highlight performance risks
        - Note integration challenges
        
        F. IMPROVEMENT RECOMMENDATIONS
        - Specific suggestions for each issue
        - Priority of improvements
        - Implementation considerations
        - Risk mitigation strategies"""

    def __init__(self):
        """Initialize the ValidatorAgent with structured output"""
        super().__init__(
            name="Requirement Validator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=ValidationOutput
        )
        
        # Create the judge agent separately - using a more powerful model for evaluation
        self.judge_agent = BaseAgent(
            name="Requirement Quality Judge",
            instructions="""You are a senior requirements quality judge.
            Evaluate the validation report provided and assign scores from 1-10 for each category.
            For each issue found, provide specific recommendations for improvement.
            Be critical but fair in your assessment.""",
            model="gpt-4o"
        )

    async def validate_requirements(self, elaboration: str, nfr_analysis: str = ""):
        """
        Validate the elaborated requirements using the LLM-as-a-judge pattern.
        
        Args:
            elaboration: The elaborated requirements
            nfr_analysis: Optional NFR analysis
            
        Returns:
            Validation result with scores and recommendations
        """
        # Use trace to track this operation
        with trace("Requirements Validation"):
            nfr_section = f"\nNon-Functional Requirements Analysis:\n{nfr_analysis}" if nfr_analysis else ""
            validation_prompt = f"""
            Functional Requirements:
            {elaboration}
            {nfr_section}
            
            Validate both functional and non-functional requirements, considering:
            1. Completeness and clarity
            2. Consistency between functional and non-functional requirements
            3. Feasibility of implementation
            4. Testability of all requirements
            """
            
            # Get initial validation
            validation_result = await self.run(validation_prompt)
            
            # If the validation is already a structured output, return it directly
            if isinstance(validation_result, ValidationOutput):
                return validation_result
                
            # Otherwise, send to the judge for scoring and structured analysis
            judge_prompt = f"""
            Original Requirements:
            {elaboration}
            
            {nfr_section}
            
            Validation Report:
            {validation_result}
            
            Please evaluate this validation report and provide scores from 1-10 for:
            1. Completeness (how well requirements cover all aspects)
            2. Consistency (how well requirements align with each other)
            3. Testability (how well requirements can be verified)
            4. NFR Compliance (how well requirements meet non-functional needs)
            5. Overall Quality
            
            For each issue identified, provide specific recommendations for improvement.
            """
            
            # Use the judge to evaluate the validation
            with trace("Judge Evaluation"):
                return await self.judge_agent.run(judge_prompt)
        
    async def validate_functional(self, elaboration: str) -> ValidationOutput:
        """Validate just the functional requirements"""
        with trace("Functional Validation"):
            return await self.run(f"Functional Requirements:\n{elaboration}")
        
    async def validate_nfr(self, nfr_analysis: str) -> ValidationOutput:
        """Validate just the non-functional requirements"""
        with trace("NFR Validation"):
            return await self.run(f"Non-Functional Requirements:\n{nfr_analysis}") 