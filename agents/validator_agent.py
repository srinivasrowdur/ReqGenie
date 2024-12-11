"""Requirement Validator Agent"""
from swarm import Agent, Swarm
from typing import Generator

class ValidatorAgent:
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

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Requirement Validator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini"
        )
        self.client = client

    def validate_requirements(self, elaboration: str, nfr_analysis: str = "") -> Generator:
        """
        Validate the elaborated requirements and NFR analysis.
        
        Args:
            elaboration: The elaborated requirements
            nfr_analysis: Optional NFR analysis
            
        Returns:
            Generator for the validation stream
        """
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
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": validation_prompt}],
            stream=True
        )

    def get_agent(self):
        return self.agent 