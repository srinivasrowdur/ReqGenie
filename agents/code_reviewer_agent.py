"""Code Reviewer Agent"""
from swarm import Agent, Swarm
from typing import Generator

class CodeReviewerAgent:
    INSTRUCTIONS = """You are a senior software engineer specializing in code review. Review the code for:
        
        A. FUNCTIONAL COMPLIANCE
        1. Requirements Coverage
           - All functional requirements implemented
           - Correct business logic
           - Proper error handling
           - Complete feature implementation

        2. NFR Implementation
           - Performance optimizations
           - Security measures
           - Scalability considerations
           - Other NFR compliance

        B. CODE QUALITY
        1. Architecture
           - Design patterns usage
           - Code organization
           - Component separation
           - Dependency management

        2. Best Practices
           - Coding standards
           - Naming conventions
           - Documentation
           - Error handling patterns

        3. Performance
           - Algorithm efficiency
           - Resource usage
           - Memory management
           - Query optimization

        C. SECURITY REVIEW
        1. Vulnerabilities
           - Input validation
           - Authentication/Authorization
           - Data protection
           - API security

        2. Best Practices
           - Secure coding patterns
           - Encryption usage
           - Session management
           - Access control

        D. TEST COVERAGE
        1. Unit Tests
           - Code coverage
           - Test quality
           - Edge cases
           - Mocking strategy

        2. Integration Tests
           - API testing
           - Component integration
           - Error scenarios
           - Performance testing

        E. MAINTAINABILITY
        1. Code Structure
           - Modularity
           - Reusability
           - Extensibility
           - Configurability

        2. Documentation
           - Code comments
           - API documentation
           - Setup instructions
           - Deployment guides

        Provide detailed feedback on:
        1. Critical issues
        2. Improvement suggestions
        3. Best practice violations
        4. Security concerns
        5. Performance optimizations"""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Code Reviewer",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini"
        )
        self.client = client

    def review_code(
        self,
        final_requirements: str,
        generated_code: str,
        test_cases: str,
        nfr_analysis: str = ""
    ) -> Generator:
        """
        Review generated code against requirements.
        
        Args:
            final_requirements: Final detailed requirements
            generated_code: Generated code to review
            test_cases: Generated test cases
            nfr_analysis: Optional NFR analysis
            
        Returns:
            Generator for the review stream
        """
        nfr_section = f"\nNon-Functional Requirements:\n{nfr_analysis}" if nfr_analysis else ""
        review_prompt = f"""
        Requirements: {final_requirements}
        {nfr_section}
        Generated Code: {generated_code}
        Test Cases: {test_cases}
        """
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": review_prompt}],
            stream=True
        )

    def get_agent(self):
        return self.agent 