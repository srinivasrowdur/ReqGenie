"""Requirement Finalizer Agent"""
from swarm import Agent, Swarm
from typing import Generator, Dict, Optional

class FinalizerAgent:
    INSTRUCTIONS = """You are a senior business analyst who finalizes requirements..."""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Requirement Finalizer",
            instructions=self.INSTRUCTIONS
        )
        self.client = client

    def finalize_requirements(
        self,
        original_requirement: str,
        elaboration: str,
        validation: str,
        nfr_data: Optional[Dict[str, str]] = None
    ) -> Generator:
        """
        Create final requirements document incorporating all analyses.
        
        Args:
            original_requirement: The initial requirement
            elaboration: Elaborated requirements
            validation: Validation feedback
            nfr_data: Optional dict containing NFR document and analysis
                     Format: {'document': str, 'analysis': str}
        
        Returns:
            Generator for the finalization stream
        """
        # Build NFR section if NFR data is provided
        nfr_section = ""
        if nfr_data:
            nfr_section = f"""
            ORIGINAL NFR DOCUMENT:
            {nfr_data.get('document', '')}

            NFR ANALYSIS:
            {nfr_data.get('analysis', '')}
            """

        final_prompt = self._construct_final_prompt(
            original_requirement=original_requirement,
            elaboration=elaboration,
            validation=validation,
            nfr_section=nfr_section
        )
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": final_prompt}],
            model="gpt-4o-mini",
            stream=True
        )

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

    def get_agent(self):
        return self.agent 