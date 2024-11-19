import requests
from requests.auth import HTTPBasicAuth
import json
import os
from typing import Dict, Any

class JiraService:
    def __init__(self):
        self.base_url = os.getenv('JIRA_BASE_URL')
        self.auth = HTTPBasicAuth(
            os.getenv('JIRA_EMAIL'),
            os.getenv('JIRA_API_TOKEN')
        )
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Jira issue with the given payload."""
        url = f"{self.base_url}/rest/api/3/issue"
        
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=self.headers,
            auth=self.auth
        )
        response.raise_for_status()
        return response.json()

    def create_link(self, outward_issue: str, inward_issue: str, link_type: str) -> None:
        """Create a link between two issues."""
        url = f"{self.base_url}/rest/api/3/issueLink"
        
        payload = {
            "outwardIssue": {"key": outward_issue},
            "inwardIssue": {"key": inward_issue},
            "type": {"name": link_type}
        }
        
        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=self.headers,
            auth=self.auth
        )
        response.raise_for_status()

    def create_epic(self, project_key: str, summary: str, description: str) -> str:
        """Create an epic and return its key."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"text": description, "type": "text"}]
                        }
                    ]
                },
                "issuetype": {"name": "Epic"}
            }
        }
        
        response = self.create_issue(payload)
        return response["key"]

    def create_story(self, project_key: str, summary: str, description: str, 
                    epic_key: str, story_points: int = None) -> str:
        """Create a story and return its key."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"text": description, "type": "text"}]
                        }
                    ]
                },
                "issuetype": {"name": "Story"},
                "customfield_10014": story_points,  # Story points field
                "customfield_10011": epic_key  # Epic link field
            }
        }
        
        response = self.create_issue(payload)
        return response["key"]

    def create_task(self, project_key: str, summary: str, description: str, 
                   parent_key: str) -> str:
        """Create a subtask and return its key."""
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"text": description, "type": "text"}]
                        }
                    ]
                },
                "issuetype": {"name": "Sub-task"},
                "parent": {"key": parent_key}
            }
        }
        
        response = self.create_issue(payload)
        return response["key"] 