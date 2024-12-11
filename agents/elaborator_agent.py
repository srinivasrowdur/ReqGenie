"""Requirement Elaborator Agent"""
from swarm import Agent, Swarm
from typing import Dict, List, Tuple, Generator

class ElaboratorAgent:
    INSTRUCTIONS = """You are a requirement analysis expert. When given a single line requirement and application type:
        1. Expand it into detailed functional requirements, considering:
           - If Web Application: UI/UX, frontend components, user interactions
           - If Web Service: API endpoints, data formats, integration points
        2. Consider provided Non-Functional Requirements (NFRs)
        3. List any assumptions made
        4. Identify potential edge cases
        5. Suggest acceptance criteria"""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Requirement Elaborator",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini"
        )
        self.client = client

    def elaborate_requirements(self, requirement: str, app_type: str) -> Generator:
        """
        Elaborate the given requirement based on application type.
        Returns the raw stream from the agent.
        """
        initial_prompt = f"Requirement: {requirement}\nApplication Type: {app_type}"
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": initial_prompt}],
            stream=True
        )

    def analyze_nfr(self, nfr_content: str, app_type: str) -> Generator:
        """
        Analyze non-functional requirements.
        Returns the raw stream from the agent.
        """
        nfr_prompt = self.get_nfr_analysis_prompt(nfr_content, app_type)
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": nfr_prompt}],
            stream=True
        )

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