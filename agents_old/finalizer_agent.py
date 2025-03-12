"""Requirement Finalizer Agent"""
from typing import Dict, List, Generator, Union, Any, Optional
from pydantic import BaseModel
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent
# Import directly from agents package
from agents import trace, Runner

class FinalSpecOutput(BaseModel):
    """Structured output for final requirement specifications"""
    executive_summary: str
    use_cases: List[Dict[str, Any]]
    functional_requirements: List[Dict[str, Any]]
    non_functional_requirements: Optional[List[Dict[str, Any]]]
    implementation_considerations: Dict[str, Any]
    acceptance_criteria: List[Dict[str, Any]]
    assumptions_and_constraints: List[str]
    metadata: Dict[str, Any] = {}

class FinalizerAgent(BaseAgent):
    """Agent for finalizing requirement specifications with output guardrails"""
    
    INSTRUCTIONS = """You are a senior business analyst who finalizes requirements. Your task is to:
        1. Review all inputs (original requirement, elaboration, validation, NFRs)
        2. Create a comprehensive final requirements document
        3. Ensure all stakeholder needs are addressed
        4. Include clear acceptance criteria
        5. Identify assumptions and constraints
        6. Make it implementation-ready"""

    def __init__(self):
        """Initialize the FinalizerAgent with output guardrails"""
        super().__init__(
            name="Requirement Finalizer",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            output_guardrails=[self.output_quality_guardrail()],
            structured_output=None  # We'll stream unstructured output for better UI experience
        )

    async def finalize_requirements(
        self,
        original_requirement: str,
        elaboration: str,
        validation: Any,
        nfr_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Create final requirements document incorporating all analyses with output guardrails.
        
        Args:
            original_requirement: The initial requirement
            elaboration: Elaborated requirements
            validation: Validation feedback (can be structured or string)
            nfr_data: Optional dict containing NFR document, analysis and validation
                     Format: {'document': str, 'analysis': str, 'validation': Any}
        
        Returns:
            Final specification document
        """
        with trace("Finalizing Requirements"):
            # Build NFR section if NFR data is provided
            nfr_section = ""
            if nfr_data:
                nfr_document = nfr_data.get('document', '')
                nfr_analysis = nfr_data.get('analysis', '')
                nfr_validation = nfr_data.get('validation', '')
                
                nfr_section = f"""
                ORIGINAL NFR DOCUMENT:
                {nfr_document}

                NFR ANALYSIS:
                {nfr_analysis}
                
                NFR VALIDATION:
                {nfr_validation}
                """

            # Convert validation to string if it's a structured object
            validation_str = str(validation) if not isinstance(validation, str) else validation

            final_prompt = self._construct_final_prompt(
                original_requirement=original_requirement,
                elaboration=elaboration,
                validation=validation_str,
                nfr_section=nfr_section
            )
            
            return await self.run(final_prompt)

    def _construct_final_prompt(
        self,
        original_requirement: str,
        elaboration: str,
        validation: str,
        nfr_section: str
    ) -> str:
        """
        Construct the final requirements prompt.
        
        Args:
            original_requirement: The initial requirement
            elaboration: Elaborated requirements
            validation: Validation feedback
            nfr_section: NFR-related content
            
        Returns:
            Formatted prompt for final requirements
        """
        return f"""
        Review and incorporate ALL of the following inputs to create the final requirements specification:

        ORIGINAL REQUIREMENT:
        {original_requirement}

        ELABORATED REQUIREMENTS:
        {elaboration}

        VALIDATION FEEDBACK:
        {validation}

        {nfr_section}

        Based on ALL the above analyses, create a comprehensive final requirements document that incorporates 
        and refines these insights. Follow this exact structure:

        A. EXECUTIVE SUMMARY
        [Brief overview, objectives, stakeholders, NFR impact summary]

        B. USE CASES
        1. PlantUML Diagram
        [Create comprehensive use case diagram]

        2. Detailed Use Cases
        [For EACH use case provide complete documentation with all specified sections]

        C. FUNCTIONAL REQUIREMENTS
        [Map requirements to use cases, core functionality, interactions, behaviors]

        D. NON-FUNCTIONAL REQUIREMENTS
        [Detail each NFR category with specifications, cross-cutting concerns, compliance matrix]

        E. IMPLEMENTATION CONSIDERATIONS
        [Technical approach, integration strategy, success factors, risk mitigation]

        F. ACCEPTANCE CRITERIA
        [Criteria per use case, NFR criteria, testing requirements, benchmarks]

        G. ASSUMPTIONS AND CONSTRAINTS
        [Business context, technical constraints, dependencies, risks]

        IMPORTANT GUIDELINES:
        1. Every use case must be fully detailed with no summarization
        2. All NFRs must be explicitly addressed in relevant use cases
        3. NFR requirements must be integrated throughout all sections
        4. Clear traceability must exist between requirements, NFRs, and use cases
        5. No content from the NFR analysis should be lost or summarized
        """ 