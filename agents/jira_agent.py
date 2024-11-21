"""Jira Ticket Creator Agent"""
from swarm import Agent, Swarm
from typing import Generator, Optional, Dict
import json

class JiraAgent:
    INSTRUCTIONS = """You are a Jira integration specialist. Your task is to create Jira tickets based on requirements analysis.
    You MUST respond with ONLY valid JSON in the exact format shown below, with no additional text or formatting:

    {
        "epic": {
            "type": "epic",
            "summary": "Main epic title",
            "description": "Detailed epic description"
        },
        "stories": [
            {
                "type": "story",
                "summary": "Story title",
                "description": "As a [user], I want [feature] so that [benefit]",
                "story_points": 5
            }
        ],
        "tasks": [
            {
                "type": "task",
                "summary": "Task title",
                "description": "Technical implementation details"
            }
        ],
        "tests": [
            {
                "type": "test",
                "summary": "Test case title",
                "description": "Test case details"
            }
        ]
    }"""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Jira Ticket Creator",
            instructions=self.INSTRUCTIONS
        )
        self.client = client

    def create_tickets(
        self,
        requirement: str,
        elaboration: str,
        final_requirements: str,
        test_cases: str,
        project_key: str,
        component: str,
        nfr_analysis: Optional[str] = None
    ) -> Dict:
        """
        Create Jira tickets based on requirements analysis.
        Returns the complete JSON response instead of a stream.
        """
        jira_prompt = f"""RESPOND ONLY WITH VALID JSON IN THIS EXACT FORMAT:
        {{
            "epic": {{
                "type": "epic",
                "summary": "Main epic title",
                "description": "Detailed epic description"
            }},
            "stories": [
                {{
                    "type": "story",
                    "summary": "Story title",
                    "description": "As a [user], I want [feature] so that [benefit]",
                    "story_points": 5
                }}
            ],
            "tasks": [
                {{
                    "type": "task",
                    "summary": "Task title",
                    "description": "Technical implementation details"
                }}
            ],
            "tests": [
                {{
                    "type": "test",
                    "summary": "Test case title",
                    "description": "Test case details"
                }}
            ]
        }}

        Create Jira tickets for:
        
        Original Requirement: {requirement}
        
        Elaborated Requirements: {elaboration}
        
        Final Requirements: {final_requirements}
        
        Test Cases: {test_cases}
        
        NFR Analysis: {nfr_analysis if nfr_analysis else "No NFRs provided"}
        
        Project Key: {project_key}
        Component: {component}

        IMPORTANT:
        1. Respond ONLY with the JSON structure shown above
        2. Do not include any text before or after the JSON
        3. Ensure all JSON strings are properly escaped
        4. Include at least one story, task, and test case
        5. Make sure the epic summary matches the main requirement
        6. Story descriptions must follow "As a [user]..." format
        7. All descriptions must be clear and detailed
        """
        
        # Collect the complete response using streaming
        full_response = []
        stream = self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": jira_prompt}],
            stream=True
        )
        
        for chunk in stream:
            if isinstance(chunk, dict) and "content" in chunk:
                full_response.append(chunk["content"])
            elif isinstance(chunk, str):
                full_response.append(chunk)

        # Join all chunks into a single string
        content = ''.join(filter(None, full_response))

        # Parse and validate JSON
        try:
            # Try to find JSON in the response
            json_start = content.find('{')
            if json_start != -1:
                content = content[json_start:]
            
            json_end = content.rfind('}')
            if json_end != -1:
                content = content[:json_end + 1]

            tickets = json.loads(content)
            required_keys = ["epic", "stories", "tasks", "tests"]
            missing_keys = [key for key in required_keys if key not in tickets]
            if missing_keys:
                raise ValueError(f"Missing required keys in JSON: {missing_keys}")
            return tickets
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}\nResponse: {content}")

    def get_agent(self):
        return self.agent