"""Requirement Elaborator Agent"""
from swarm import Agent

class ElaboratorAgent:
    INSTRUCTIONS = """You are a requirement analysis expert. When given a single line requirement and application type:
        1. Expand it into detailed functional requirements, considering:
           - If Web Application: UI/UX, frontend components, user interactions
           - If Web Service: API endpoints, data formats, integration points
        2. Consider provided Non-Functional Requirements (NFRs)
        3. List any assumptions made
        4. Identify potential edge cases
        5. Suggest acceptance criteria"""

    def __init__(self):
        self.agent = Agent(
            name="Requirement Elaborator",
            instructions=self.INSTRUCTIONS
        )

    def get_agent(self):
        return self.agent

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