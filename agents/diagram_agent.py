"""Diagram Generator Agent"""
from swarm import Agent, Swarm
from typing import Generator, Optional, Dict
import json

class DiagramAgent:
    INSTRUCTIONS = """You are an expert in creating serverless architecture diagrams using the Python 'diagrams' library.
    You MUST respond with ONLY valid JSON in the exact format shown below, with no additional text or formatting:

    For GCP services, use these correct import paths:
    - from diagrams.gcp.compute import Functions, Run
    - from diagrams.gcp.api import APIGateway
    - from diagrams.gcp.database import Firestore
    - from diagrams.gcp.storage import Storage
    - from diagrams.gcp.analytics import Pubsub
    - from diagrams.gcp.security import Iam, KMS
    - from diagrams.gcp.operations import Monitoring

    For AWS services, use these correct import paths:
    - from diagrams.aws.compute import Lambda
    - from diagrams.aws.mobile import APIGateway
    - from diagrams.aws.database import DynamodbTable
    - from diagrams.aws.storage import SimpleStorageServiceS3
    - from diagrams.aws.integration import SimpleQueueServiceSqs
    - from diagrams.aws.security import Cognito, SecretsManager
    - from diagrams.aws.management import Cloudwatch

    {
        "imports": [
            "from diagrams import Diagram, Cluster, Edge",
            "from diagrams.gcp.compute import Functions",
            "from diagrams.gcp.api import APIGateway"
        ],
        "nodes": [
            {
                "name": "api_gateway",
                "type": "APIGateway",
                "label": "API Gateway",
                "cluster": null
            }
        ],
        "clusters": [
            {
                "name": "compute",
                "label": "Compute",
                "parent": null
            }
        ],
        "connections": [
            {
                "from": "api_gateway",
                "to": "auth_fn",
                "edge_attrs": {
                    "color": "blue",
                    "label": "API requests"
                }
            }
        ]
    }

    IMPORTANT:
    1. Use ONLY the correct import paths for the specified platform
    2. Group related services in logical clusters
    3. Show clear data flow between services
    4. Include monitoring and security services
    5. Use proper edge colors and labels
    6. All node names must be valid Python identifiers
    7. Keep the diagram clean and readable"""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Diagram Generator",
            instructions=self.INSTRUCTIONS
        )
        self.client = client

    def generate_diagram(
        self,
        requirement: str,
        architecture_type: str,
        platform: str = "gcp",
        style: Optional[dict] = None
    ) -> str:
        """Generate diagram code based on requirements."""
        diagram_prompt = f"""Analyze the following requirement and create a {platform.upper()} serverless architecture diagram:

        Requirement: {requirement}
        Architecture Type: {architecture_type}
        Platform: {platform}

        Create a serverless architecture using {platform.upper()} native services.
        Include API Gateway, Functions/Lambda, Database, Storage, Security, and Monitoring components.
        Show the data flow between services with proper edge colors and labels.
        Group related services in logical clusters.

        RESPOND ONLY WITH VALID JSON that defines the architecture diagram.
        """

        # Collect the complete response using streaming
        full_response = []
        stream = self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": diagram_prompt}],
            stream=True
        )
        
        for chunk in stream:
            if isinstance(chunk, dict) and "content" in chunk:
                full_response.append(chunk["content"])
            elif isinstance(chunk, str):
                full_response.append(chunk)

        # Join all chunks into a single string
        content = ''.join(filter(None, full_response))

        try:
            # Try to find JSON in the response
            json_start = content.find('{')
            if json_start != -1:
                content = content[json_start:]
            
            json_end = content.rfind('}')
            if json_end != -1:
                content = content[:json_end + 1]

            # Parse JSON
            json_content = json.loads(content)
            
            # Validate required keys
            required_keys = ["imports", "nodes", "clusters", "connections"]
            missing_keys = [key for key in required_keys if key not in json_content]
            if missing_keys:
                raise ValueError(f"Missing required keys in JSON: {missing_keys}")

            # Generate Python code from JSON with proper indentation
            code = []
            
            # Add imports on separate lines
            for import_stmt in json_content["imports"]:
                code.append(import_stmt)
            code.append("")
            
            # Create diagram
            code.append(f'with Diagram("{architecture_type}", show=False):')
            
            # Create cluster definitions with proper indentation
            current_indent = "    "
            for cluster in json_content["clusters"]:
                cluster_def = f'{current_indent}with Cluster("{cluster["label"]}"):'
                code.append(cluster_def)
                code.append(f'{current_indent}    pass  # {cluster["label"]} services')
            
            # Add a blank line before nodes
            code.append("")
            
            # Create nodes at the correct indentation level
            for node in json_content["nodes"]:
                cluster = node.get("cluster")
                indent = current_indent
                if cluster:
                    # Find the cluster this node belongs to and adjust indentation
                    for c in json_content["clusters"]:
                        if c["label"] == cluster:
                            indent += "    "
                            break
                node_def = f'{indent}{node["name"]} = {node["type"]}("{node["label"]}")'
                code.append(node_def)
            
            # Add a blank line before connections
            code.append("")
            
            # Create connections
            for conn in json_content["connections"]:
                edge_attrs = conn.get("edge_attrs", {})
                attrs = ", ".join(f'{k}="{v}"' for k, v in edge_attrs.items())
                edge = f'Edge({attrs})' if attrs else ''
                code.append(f'{current_indent}{conn["from"]} >> {edge} >> {conn["to"]}')
            
            # Join the code lines
            final_code = '\n'.join(code)
            
            # Validate the generated code
            try:
                compile(final_code, '<string>', 'exec')
            except IndentationError as e:
                raise ValueError(f"Generated code has invalid indentation: {str(e)}")
            
            return final_code
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}\nResponse: {content}")
        except KeyError as e:
            raise ValueError(f"Missing required key in JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error generating diagram code: {str(e)}")

    def get_agent(self):
        return self.agent