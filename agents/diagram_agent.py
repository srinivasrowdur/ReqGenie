"""Diagram Generator Agent"""
from swarm import Agent, Swarm
from typing import Generator, Optional
import os
import re

class DiagramAgent:
    INSTRUCTIONS = """You are an expert in creating serverless architecture diagrams using the Python 'diagrams' library.
    You must generate valid Python code that creates clear and well-structured serverless architecture diagrams.
    
    Key capabilities:
    1. Create serverless diagrams for different cloud providers:
       - AWS: Lambda, API Gateway, DynamoDB, S3, SQS, SNS
       - GCP: Cloud Functions, Cloud Run, Firestore, Pub/Sub
       - Azure: Functions, Logic Apps, CosmosDB, Service Bus
    2. Illustrate event-driven architectures
    3. Show serverless data processing flows
    4. Demonstrate API and authentication flows
    5. Support for different diagram directions (TB, BT, LR, RL)
    6. Support for custom styling (colors, labels, edges)
    
    Follow these guidelines:
    1. Focus on serverless components and managed services
    2. Show event triggers and data flows clearly
    3. Create logical groupings using Clusters (e.g., compute, storage, events)
    4. Include authentication and authorization flows
    5. Show monitoring and logging connections
    6. Use appropriate styling for clarity
    7. Add clear node names and descriptions
    8. Include proper error handling flows
    9. Show scaling and concurrency patterns
    10. Never connect lists directly to lists - always use loops or individual connections
    11. Always use proper connection patterns:
        - Single to single: node1 >> node2
        - Single to multiple: node1 >> [node2, node3]
        - Multiple to single: [node1, node2] >> node3
        - Multiple to multiple: Use loops to connect each source to each target"""

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
            "gcp": """from diagrams import Diagram, Cluster, Edge
from diagrams.gcp.analytics import BigQuery, Dataflow, PubSub
from diagrams.gcp.compute import AppEngine, Functions, GKE, Run
from diagrams.gcp.database import BigTable, SQL, Spanner
from diagrams.gcp.network import LoadBalancing, CDN, DNS
from diagrams.gcp.security import IAP, KMS, SecurityCommandCenter
from diagrams.gcp.storage import GCS, Filestore
from diagrams.gcp.api import APIGateway
from diagrams.gcp.operations import Monitoring, Logging""",
            
            "aws": """from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2, ECS, Lambda, EKS
from diagrams.aws.network import ELB, VPC, APIGateway, CloudFront, Route53
from diagrams.aws.database import RDS, Dynamodb, ElastiCache
from diagrams.aws.security import IAM, Cognito, WAF, Shield, KMS
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudwatch, AutoScaling
from diagrams.aws.analytics import Redshift, Athena""",
            
            "azure": """from diagrams import Diagram, Cluster, Edge
from diagrams.azure.compute import AppServices, FunctionApps
from diagrams.azure.database import DatabaseForPostgresqlServers
from diagrams.azure.network import ApplicationGateway, LoadBalancers
from diagrams.azure.security import KeyVaults
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.web import AppServicePlans
from diagrams.azure.integration import ServiceBus"""
        }

        # Platform-specific example diagrams
        platform_examples = {
            "gcp": """
with Diagram("GCP Serverless Architecture", show=False):
    # Frontend/API Layer
    lb = LoadBalancing("HTTPS LB")
    api = APIGateway("API Gateway")
    
    with Cluster("Serverless Compute"):
        functions = [
            Functions("Auth Service"),
            Functions("Business Logic"),
            Functions("Data Handler")
        ]
        
        # Connect API to functions
        for fn in functions:
            api >> Edge(color="darkgreen") >> fn
    
    with Cluster("Data & Events"):
        pubsub = PubSub("Pub/Sub")
        
        with Cluster("Storage"):
            firestore = Firestore("Firestore")
            storage = GCS("Cloud Storage")
        
        # Connect functions to data services
        for fn in functions:
            fn >> Edge(color="blue") >> pubsub
            fn >> Edge(color="blue") >> firestore
            fn >> Edge(color="blue") >> storage
    
    # Monitoring & Logging
    monitoring = Monitoring("Cloud Monitoring")
    logging = Logging("Cloud Logging")
    
    # Main flow
    lb >> api
    
    # Monitoring connections
    for fn in functions:
        fn >> Edge(style="dotted") >> monitoring
        fn >> Edge(style="dotted") >> logging
""",

            "aws": """
with Diagram("AWS Serverless Architecture", show=False):
    # Frontend/API Layer
    cdn = CloudFront("CloudFront")
    api = APIGateway("API Gateway")
    
    with Cluster("Authentication"):
        cognito = Cognito("Cognito")
    
    with Cluster("Serverless Compute"):
        functions = [
            Lambda("Auth Handler"),
            Lambda("Business Logic"),
            Lambda("Event Handler")
        ]
        
        # Connect API to Lambda functions
        for fn in functions:
            api >> Edge(color="darkgreen") >> fn
            cognito >> Edge(color="red", style="dotted") >> fn
    
    with Cluster("Data & Events"):
        queue = SQS("SQS Queue")
        
        with Cluster("Storage"):
            dynamo = Dynamodb("DynamoDB")
            s3 = S3("S3 Bucket")
        
        # Connect functions to data services
        for fn in functions:
            fn >> Edge(color="blue") >> queue
            fn >> Edge(color="blue") >> dynamo
            fn >> Edge(color="blue") >> s3
    
    # Monitoring
    cloudwatch = Cloudwatch("CloudWatch")
    
    # Main flow
    cdn >> api
    
    # Monitoring connections
    for fn in functions:
        fn >> Edge(style="dotted") >> cloudwatch
""",

            "azure": """
with Diagram("Azure Serverless Architecture", show=False):
    # Frontend/API Layer
    cdn = CDNProfiles("CDN")
    gateway = ApplicationGateway("API Gateway")
    
    with Cluster("Authentication"):
        auth = ActiveDirectory("Azure AD")
    
    with Cluster("Serverless Compute"):
        functions = [
            FunctionApps("Auth Function"),
            FunctionApps("Business Logic"),
            FunctionApps("Event Handler")
        ]
        
        # Connect gateway to functions
        for fn in functions:
            gateway >> Edge(color="darkgreen") >> fn
            auth >> Edge(color="red", style="dotted") >> fn
    
    with Cluster("Data & Events"):
        servicebus = ServiceBus("Service Bus")
        
        with Cluster("Storage"):
            cosmos = CosmosDb("Cosmos DB")
            blob = BlobStorage("Blob Storage")
        
        # Connect functions to data services
        for fn in functions:
            fn >> Edge(color="blue") >> servicebus
            fn >> Edge(color="blue") >> cosmos
            fn >> Edge(color="blue") >> blob
    
    # Monitoring
    insights = ApplicationInsights("App Insights")
    
    # Main flow
    cdn >> gateway
    
    # Monitoring connections
    for fn in functions:
        fn >> Edge(style="dotted") >> insights
"""
        }

        diagram_prompt = f"""Generate Python code for a {architecture_type} diagram using the 'diagrams' library.
Requirements: {requirement}

Use these imports:
{platform_imports.get(platform.lower(), platform_imports['gcp'])}

CRITICAL RULES:
1. Use EXACTLY this format for the Diagram instantiation:
   with Diagram(name="{architecture_type}", direction="TB", filename="diagram.png", show=False):

2. The diagram MUST address these specific requirements:
   {requirement}

3. Use appropriate {platform.upper()} services that match the requirements

4. NEVER connect lists directly to lists! This will cause TypeError.
   INCORRECT: ❌
   [node1, node2] >> [node3, node4]  # This will fail!
   
   CORRECT: ✅
   # Method 1: Connect each source to each target using loops
   for source in [node1, node2]:
       for target in [node3, node4]:
           source >> target

5. Valid connection patterns:
   # Single node to single node
   node1 >> node2

   # Single node to multiple nodes (works)
   node1 >> [node2, node3]

   # Multiple nodes to single node (works)
   [node1, node2] >> node3

   # For list to list connections, ALWAYS use loops:
   for source in source_list:
       for target in target_list:
           source >> Edge(color="blue") >> target

Make sure to:
1. Use meaningful cluster names that match the requirements
2. Only include services that are relevant to the requirements
3. Show clear data flow between components as specified
4. Group related services in clusters based on the requirements
5. Use descriptive labels that match the requirement terminology
6. Maintain proper hierarchy
7. NEVER connect lists directly - use loops or individual connections
8. Use appropriate services for {platform} that fulfill the requirements
"""

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
        
        # Find the first 'from' or 'import' statement
        import_match = re.search(r'^(from|import)\s', code, re.MULTILINE)
        if import_match:
            start_idx = import_match.start()
            code = code[start_idx:]
        
        # Find the last line that looks like valid Python code
        lines = code.split('\n')
        valid_lines = []
        for line in lines:
            # Skip empty lines or explanatory text
            stripped = line.strip()
            if (not stripped or 
                stripped.startswith('#') or 
                any(keyword in stripped for keyword in ['from', 'import', 'with', 'def', 'class', ')', ']', '}', '>>', '=', '+', '-', '*', '/', '%', '|', '&', '^', '<', '>', ':', 'for', 'if', 'else', 'elif', 'while', 'try', 'except', 'finally'])):
                valid_lines.append(line)
        
        # Join the valid lines back together
        code = '\n'.join(valid_lines)
        
        # Remove any trailing text that's not code
        if 'with Diagram(' in code:
            last_brace = code.rfind('}')
            if last_brace != -1:
                code = code[:last_brace+1]
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        return code

    def get_agent(self):
        return self.agent