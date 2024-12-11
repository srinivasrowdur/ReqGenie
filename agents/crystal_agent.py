"""Crystal Knows Personality Analysis Agent"""
from swarm import Agent, Swarm
from typing import Generator, Optional, Dict
import json

class CrystalAgent:
    INSTRUCTIONS = """You are a personality analysis specialist using Crystal Knows API.
    You MUST respond with ONLY valid JSON in the exact format shown below, with no additional text or formatting:

    {
        "profile_request": {
            "type": "email|linkedin|text",
            "value": "search value or text to analyze",
            "metadata": {
                "optional": "metadata fields"
            }
        },
        "analysis_requirements": {
            "purpose": "communication|sales|training",
            "focus_areas": ["personality_traits", "communication_tips"]
        }
    }"""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Crystal Personality Analyzer",
            instructions=self.INSTRUCTIONS
        )
        self.client = client

    def analyze_profile(
        self,
        identifier: str,
        identifier_type: str = "email",
        purpose: str = "communication",
        metadata: Optional[Dict] = None
    ) -> Generator:
        """
        Analyze a personality profile using Crystal Knows API.
        
        Args:
            identifier: Email, LinkedIn URL, or text to analyze
            identifier_type: Type of identifier ('email', 'linkedin', or 'text')
            purpose: Purpose of analysis ('communication', 'sales', or 'training')
            metadata: Optional metadata for text analysis
        """
        crystal_prompt = f"""RESPOND ONLY WITH VALID JSON IN THIS EXACT FORMAT:
        {{
            "profile_request": {{
                "type": "{identifier_type}",
                "value": "{identifier}",
                "metadata": {json.dumps(metadata) if metadata else "{}"}
            }},
            "analysis_requirements": {{
                "purpose": "{purpose}",
                "focus_areas": [
                    "personality_traits",
                    "communication_tips",
                    "work_preferences"
                ]
            }}
        }}

        Create a Crystal Knows analysis request for:
        Identifier: {identifier}
        Type: {identifier_type}
        Purpose: {purpose}

        IMPORTANT:
        1. Respond ONLY with the JSON structure shown above
        2. Do not include any text before or after the JSON
        3. Ensure all JSON strings are properly escaped
        4. Valid identifier types are: email, linkedin, text
        5. Valid purposes are: communication, sales, training
        """

        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": crystal_prompt}],
            stream=True
        )

    def get_agent(self):
        return self.agent 