"""Test Case Generator Agent"""
from swarm import Agent, Swarm
from typing import Generator

class TestGeneratorAgent:
    INSTRUCTIONS = """You are a QA expert who creates comprehensive test cases. Based on the final requirements:
        1. Create detailed test cases covering:
           - Happy path scenarios
           - Edge cases
           - Error scenarios
           - Security considerations
           - NFR validation
        
        For each test case, provide:
        A. TEST CASE IDENTIFICATION
        - Unique Test ID
        - Test Category (Functional/Non-functional)
        - Priority (High/Medium/Low)
        - Related Requirements
        - Related Use Cases

        B. TEST CASE DETAILS
        - Description
        - Preconditions
        - Test Data Requirements
        - Test Environment Requirements
        - Dependencies

        C. TEST STEPS
        - Detailed step-by-step instructions
        - Expected Result per step
        - Actual Result field
        - Pass/Fail Criteria
        - Screenshots/Evidence Requirements

        D. NFR VALIDATION
        - Performance Metrics
        - Security Checks
        - Scalability Tests
        - Other NFR Considerations

        E. ERROR HANDLING
        - Error Scenarios
        - Recovery Steps
        - Error Messages
        - Logging Requirements

        F. AUTOMATION CONSIDERATIONS
        - Automation Feasibility
        - Tool Requirements
        - Special Handling Needs
        - Data Setup Requirements

        Ensure:
        1. All requirements are covered
        2. Clear traceability exists
        3. Tests are repeatable
        4. Edge cases are included
        5. NFRs are validated"""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Test Case Generator",
            instructions=self.INSTRUCTIONS
        )
        self.client = client

    def generate_test_cases(
        self,
        requirement: str,
        final_requirements: str,
        programming_language: str,
        nfr_analysis: str = ""
    ) -> Generator:
        """
        Generate comprehensive test cases based on requirements.
        
        Args:
            requirement: Original requirement
            final_requirements: Final detailed requirements
            programming_language: Target programming language
            nfr_analysis: Optional NFR analysis
            
        Returns:
            Generator for the test cases stream
        """
        nfr_section = f"\nNon-Functional Requirements:\n{nfr_analysis}" if nfr_analysis else ""
        test_prompt = f"""
        Original Requirement: {requirement}
        Final Requirements: {final_requirements}
        {nfr_section}
        Programming Language: {programming_language}
        """
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": test_prompt}],
            stream=True
        )

    def get_agent(self):
        return self.agent 