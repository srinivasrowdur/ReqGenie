import requests
from requests.auth import HTTPBasicAuth
import json
import os
from typing import Dict, Any
from datetime import datetime

class JiraService:
    def __init__(self):
        self.base_url = os.getenv('JIRA_BASE_URL')
        self.email = os.getenv('JIRA_EMAIL')
        self.api_token = os.getenv('JIRA_API_TOKEN')
        
        # Validate configuration
        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Missing required Jira configuration. Please check your .env file.")
        
        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def test_connection(self) -> bool:
        """Test the Jira connection and credentials."""
        try:
            url = f"{self.base_url}/rest/api/3/myself"
            response = requests.get(
                url,
                headers=self.headers,
                auth=self.auth
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Jira: {str(e)}")

    def validate_project(self, project_key: str) -> bool:
        """Validate if the project exists and is accessible."""
        try:
            url = f"{self.base_url}/rest/api/3/project/{project_key}"
            response = requests.get(
                url,
                headers=self.headers,
                auth=self.auth
            )
            response.raise_for_status()
            
            # Get available issue types for the project
            self.issue_types = self._get_project_issue_types(project_key)
            return True
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Invalid or inaccessible project key '{project_key}': {str(e)}")

    def _get_project_issue_types(self, project_key: str) -> Dict[str, str]:
        """Get available issue types for the project."""
        url = f"{self.base_url}/rest/api/3/project/{project_key}"
        response = requests.get(
            url,
            headers=self.headers,
            auth=self.auth
        )
        response.raise_for_status()
        project_data = response.json()
        
        # Create a mapping of issue type names to IDs
        return {
            issueType['name'].lower(): issueType['id']
            for issueType in project_data['issueTypes']
        } if 'issueTypes' in project_data else {}

    def _create_description(self, text: str) -> Dict:
        """Create a properly formatted description for Jira."""
        return {
            "content": [
                {
                    "content": [
                        {
                            "text": text,
                            "type": "text"
                        }
                    ],
                    "type": "paragraph"
                }
            ],
            "type": "doc",
            "version": 1
        }

    def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Jira issue with the given payload."""
        try:
            url = f"{self.base_url}/rest/api/3/issue"
            
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=self.headers,
                auth=self.auth
            )
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    error_msg = "Authentication failed. Please check your Jira credentials."
                elif e.response.status_code == 403:
                    error_msg = "Permission denied. Please check your Jira access rights."
                elif e.response.status_code == 404:
                    error_msg = "Invalid Jira URL or endpoint not found."
                elif e.response.status_code == 400:
                    error_msg = f"Invalid request: {e.response.text}"
            raise Exception(f"Failed to create Jira issue: {error_msg}")

    def create_epic(self, project_key: str, summary: str, description: str) -> str:
        """Create an epic and return its key."""
        epic_type_id = self.issue_types.get('epic')
        if not epic_type_id:
            raise ValueError("Epic issue type not found in project")
            
        payload = {
            "fields": {
                "project": {
                    "key": project_key
                },
                "summary": summary,
                "description": self._create_description(description),
                "issuetype": {
                    "id": epic_type_id
                },
                "labels": ["ReqGenie"]
            },
            "update": {}
        }
        
        response = self.create_issue(payload)
        return response["key"]

    def create_story(self, project_key: str, summary: str, description: str, 
                    epic_key: str, story_points: int = None) -> str:
        """Create a story and return its key."""
        story_type_id = self.issue_types.get('story')
        if not story_type_id:
            raise ValueError("Story issue type not found in project")
            
        payload = {
            "fields": {
                "project": {
                    "key": project_key
                },
                "summary": summary,
                "description": self._create_description(description),
                "issuetype": {
                    "id": story_type_id
                },
                "labels": ["ReqGenie"]
            },
            "update": {}
        }
        
        response = self.create_issue(payload)
        return response["key"]

    def create_task(self, project_key: str, summary: str, description: str, 
                   parent_key: str) -> str:
        """Create a task and return its key."""
        task_type_id = self.issue_types.get('task')
        if not task_type_id:
            raise ValueError("Task issue type not found in project")
            
        payload = {
            "fields": {
                "project": {
                    "key": project_key
                },
                "summary": summary,
                "description": self._create_description(description),
                "issuetype": {
                    "id": task_type_id
                },
                "labels": ["ReqGenie"]
            },
            "update": {
                "issuelinks": [{
                    "add": {
                        "type": {
                            "name": "Relates"
                        },
                        "outwardIssue": {
                            "key": parent_key
                        }
                    }
                }]
            }
        }
        
        response = self.create_issue(payload)
        return response["key"] 
        return response["key"] 