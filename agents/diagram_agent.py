"""Diagram Generator Agent"""
from swarm import Agent, Swarm
from typing import Generator, Optional
import os
import re

class DiagramAgent:
    INSTRUCTIONS = """You are an expert in creating architecture diagrams using the Python 'diagrams' library.
    You must generate valid Python code that creates clear and well-structured architecture diagrams.
    
    Key capabilities:
    1. Create diagrams for different cloud providers (AWS, GCP, Azure)
    2. Create diagrams for Kubernetes architectures
    3. Create diagrams for on-premises solutions
    4. Support for clustered services
    5. Support for different diagram directions (TB, BT, LR, RL)
    6. Support for custom styling (colors, labels, edges)
    
    Follow these guidelines:
    1. Always include proper imports
    2. Use appropriate node types for services
    3. Create logical groupings using Clusters
    4. Add meaningful labels and connections
    5. Use appropriate styling for clarity
    6. Include proper direction and layout
    7. Add clear node names and descriptions
    8. Use triple quotes for multi-line comments
    9. Ensure all strings are properly terminated"""

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
    ) -> Generator:
        """
        Generate diagram code based on requirements.
        """
        # Map platform to appropriate import paths
        platform_imports = {
            "gcp": """from diagrams import Diagram, Cluster
from diagrams.gcp.compute import AppEngine, Functions, KubernetesEngine
from diagrams.gcp.network import LoadBalancing, FirewallRules, VirtualPrivateCloud
from diagrams.gcp.database import SQL, Firestore
from diagrams.gcp.security import IAP, SecurityScanner
from diagrams.gcp.devtools import ContainerRegistry
from diagrams.gcp.storage import Storage""",
            
            "aws": """from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2, ECS, Lambda, ElasticBeanstalk
from diagrams.aws.network import ELB, VPC, APIGateway, CloudFront
from diagrams.aws.database import RDS, Dynamodb, ElastiCache
from diagrams.aws.security import IAM, Cognito, WAF, Shield
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.storage import S3
from diagrams.aws.network import Route53, PrivateSubnet, PublicSubnet
from diagrams.aws.management import Cloudwatch, AutoScaling""",
            
            "azure": """from diagrams import Diagram, Cluster
from diagrams.azure.compute import AppServices, FunctionApps, KubernetesServices, ContainerInstances
from diagrams.azure.database import SQLDatabases, CosmosDb, CacheForRedis
from diagrams.azure.network import LoadBalancers, ApplicationGateway, VirtualNetworks, CDNProfiles
from diagrams.azure.security import KeyVaults, ActiveDirectory, SecurityCenter
from diagrams.azure.storage import StorageAccounts, BlobStorage
from diagrams.azure.web import AppServicePlans, APIConnections
from diagrams.azure.identity import AppRegistrations, ManagedIdentities
from diagrams.azure.integration import APIManagement, ServiceBus"""
        }

        diagram_prompt = f"""Generate Python code for a diagram using the 'diagrams' library.
Do not include markdown code block markers (```).

Use these imports:
{platform_imports.get(platform.lower(), platform_imports['gcp'])}
from diagrams import Edge

IMPORTANT: Use EXACTLY this format for the Diagram instantiation:
with Diagram(name="Architecture", direction="TB", filename="diagram.png", show=False):

IMPORTANT CONNECTION RULES:
1. Cannot connect lists directly to lists
2. Must connect individual nodes or iterate through lists
3. Use these patterns for connections:
   # Single nodes
   node1 >> node2
   
   # Node to list
   node1 >> [node2, node3]
   
   # List to node
   [node1, node2] >> node3
   
   # For list to list, use a loop:
   for source in source_list:
       for target in target_list:
           source >> target

Example structure:
'''
from diagrams import Diagram, Cluster, Edge
[import statements...]

with Diagram(name="Architecture", direction="TB", filename="diagram.png", show=False):
    # External Services
    gateway = Gateway("API Gateway")
    
    # Frontend Cluster
    with Cluster("Frontend"):
        frontend = [
            WebServer("web1"),
            WebServer("web2")
        ]
        
        # Correct way to connect lists
        gateway >> frontend
        
        # For complex connections between lists
        for service in frontend:
            service >> database
'''

The code should:
1. Use logical clustering
2. Add meaningful edge colors and styles
3. Show clear data flow
4. Group related services
5. Use correct connection patterns
6. Set show=False to prevent popup window

Generate ONLY valid Python code that will work with the diagrams library."""
        
        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": diagram_prompt}],
            stream=True
        )

    @staticmethod
    def clean_code(code: str) -> str:
        """Clean the generated code by removing markdown and unnecessary text."""
        # Remove markdown code block markers
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*', '', code)
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        return code

    def get_agent(self):
        return self.agent