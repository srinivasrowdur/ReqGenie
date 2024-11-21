"""Code Generator Agent"""
from swarm import Agent, Swarm
from typing import Generator, Optional

class CodeGeneratorAgent:
    ROLE = "Full Stack Web Developer"
    GOAL = "Generate production-ready web application code with comprehensive test coverage"
    BACKSTORY = """You are a senior full-stack developer specializing in web applications. 
    You have extensive experience in test-driven development (TDD) and writing clean, 
    maintainable code across Python, Java, and Kotlin."""
    
    INSTRUCTIONS = """
    Follow this process strictly when generating code:

    1. Requirements Analysis:
       - Review and understand all validated requirements
       - Consider Non-Functional Requirements
       - Identify core functionality and technical constraints
       - Plan the application architecture based on requirements

    2. Test Cases Implementation:
       - Create unit tests based on provided test scenarios
       - Include test cases for both happy path and edge cases
       - Include NFR validation tests
       - Use appropriate testing framework for the selected language

    3. Web Application Implementation:
       - Create a well-structured web application following MVC/MVVM pattern
       - Implement all required endpoints/routes
       - Include proper input validation and error handling
       - Implement NFR requirements (performance, security, etc.)
       - Add security measures
       - Include clear documentation
    """

    def __init__(self, client: Swarm):
        self.agent = Agent(
            role=self.ROLE,
            goal=self.GOAL,
            backstory=self.BACKSTORY,
            instructions=self.INSTRUCTIONS
        )
        self.client = client

    def generate_code(
        self,
        final_requirements: str,
        programming_language: str,
        app_type: str,
        nfr_analysis: Optional[str] = None
    ) -> Generator:
        """
        Generate code based on requirements.
        
        Args:
            final_requirements: Final detailed requirements
            programming_language: Target programming language
            app_type: Type of application (Web Application/Web Service)
            nfr_analysis: Optional NFR analysis
            
        Returns:
            Generator for the code stream
        """
        nfr_section = f"\nNon-Functional Requirements:\n{nfr_analysis}" if nfr_analysis else ""
        code_prompt = f"""
        Based on the specifications, generate code in {programming_language}.
        Application Type: {app_type}
        
        Final Requirements:
        {final_requirements}
        {nfr_section}
        
        If Web Application:
        - Include frontend code (HTML/CSS if needed)
        - Include necessary routing
        - Include user interface components
        
        If Web Service:
        - Focus on API endpoints
        - Include request/response handling
        - Include data models
        """
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": code_prompt}],
            stream=True
        )

    def get_agent(self):
        return self.agent 