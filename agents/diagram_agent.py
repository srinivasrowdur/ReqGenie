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
from diagrams.aws.analytics import Redshift, Athena
from diagrams.aws.ml import SageMaker""",
            
            "azure": """from diagrams import Diagram, Cluster, Edge
from diagrams.azure.compute import AppServices, FunctionApps, AKS, ContainerInstances
from diagrams.azure.database import DatabaseForPostgresqlServers, CosmosDb, CacheForRedis
from diagrams.azure.network import LoadBalancers, ApplicationGateway, VirtualNetworks, CDNProfiles
from diagrams.azure.security import KeyVaults, ActiveDirectory
from diagrams.azure.storage import StorageAccounts, BlobStorage
from diagrams.azure.web import AppServicePlans
from diagrams.azure.analytics import Databricks, HDInsightClusters
from diagrams.azure.integration import ServiceBus, EventGrids
from diagrams.azure.monitoring import ApplicationInsights"""
        }

        # Platform-specific example diagrams
        platform_examples = {
            "gcp": """
with Diagram("GCP Architecture", show=False):
    # Define network components
    dns = DNS("dns")
    lb = LoadBalancing("lb")
    api = APIGateway("api gateway")
    
    with Cluster("Security"):
        security = [
            IAP("iap"),
            KMS("kms"),
            SecurityCommandCenter("security")
        ]
    
    with Cluster("Services"):
        compute = [
            AppEngine("service1"),
            Run("service2"),
            Functions("service3")
        ]
        
        # Correct way to connect security to services
        for sec in security:
            for svc in compute:
                sec >> Edge(color="red", label="protects") >> svc
        
        with Cluster("Data Layer"):
            pubsub = PubSub("events")
            
            with Cluster("Processing"):
                flow = Dataflow("stream")
                # Single node to multiple nodes (works fine)
                flow >> [
                    BigQuery("warehouse"),
                    GCS("storage")
                ]
            
            with Cluster("Database"):
                db_primary = SQL("primary")
                # Use - for replication links
                db_primary - SQL("replica")
    
    # Operations
    monitoring = Monitoring("monitoring")
    logging = Logging("logging")
    
    # Connect components correctly
    dns >> lb >> api
    
    # Connect API to compute services individually
    for svc in compute:
        api >> svc
        
    # Connect compute to data services
    for svc in compute:
        svc >> pubsub
        svc >> db_primary
    
    # Connect monitoring
    for svc in compute:
        svc >> Edge(color="blue", style="dashed") >> monitoring
        svc >> Edge(color="blue", style="dashed") >> logging
""",
            "aws": """
with Diagram("AWS Architecture", show=False):
    route53 = Route53("dns")
    lb = ELB("lb")
    
    with Cluster("VPC"):
        api = APIGateway("api")
        
        with Cluster("Services"):
            services = [
                ECS("service1"),
                Lambda("service2"),
                EKS("service3")
            ]
        
        with Cluster("Security"):
            security = [
                IAM("iam"),
                WAF("waf"),
                Shield("shield")
            ]
            
            # Correct way to connect security to services
            for sec in security:
                for svc in services:
                    sec >> Edge(color="red", label="protects") >> svc
        
        with Cluster("Data Layer"):
            queue = SQS("queue")
            topic = SNS("notifications")
            
            with Cluster("Database"):
                db_primary = RDS("primary")
                db_primary - RDS("replica")
            
            with Cluster("Cache"):
                cache = ElastiCache("redis")
    
    # Connect components correctly
    route53 >> lb >> api
    
    # Connect API to services individually
    for svc in services:
        api >> svc
        svc >> queue
        svc >> cache
""",
            "azure": """
with Diagram("Azure Architecture", show=False):
    gateway = ApplicationGateway("gateway")
    
    with Cluster("Platform"):
        with Cluster("Security"):
            security = [
                KeyVaults("keyvault"),
                ActiveDirectory("aad")
            ]
        
        with Cluster("Frontend"):
            front = [
                AppServices("app1"),
                AppServices("app2")
            ]
        
        with Cluster("Processing"):
            functions = [
                FunctionApps("func1"),
                FunctionApps("func2")
            ]
            
            # Correct way to connect security to frontend and functions
            for sec in security:
                for f in front:
                    sec >> Edge(color="red", label="protects") >> f
                for func in functions:
                    sec >> Edge(color="red", label="protects") >> func
            
            with Cluster("Events"):
                bus = ServiceBus("events")
                grid = EventGrids("grid")
            
            with Cluster("Data Store"):
                cosmos = CosmosDb("nosql")
                sql = DatabaseForPostgresqlServers("sql")
                cache = CacheForRedis("cache")
    
    with Cluster("Monitoring"):
        insights = ApplicationInsights("monitoring")
    
    # Connect components correctly
    gateway >> front[0]
    gateway >> front[1]
    
    # Connect frontend to functions
    for f in front:
        for func in functions:
            f >> Edge(color="blue") >> func
    
    # Connect functions to data services
    for func in functions:
        func >> bus
        func >> cosmos
        func >> cache
        
    # Connect monitoring
    for f in front:
        f >> Edge(style="dashed") >> insights
    for func in functions:
        func >> Edge(style="dashed") >> insights
"""
        }

        diagram_prompt = f"""Generate Python code for a diagram using the 'diagrams' library.
Do not include markdown code block markers (```).

Use these imports:
{platform_imports.get(platform.lower(), platform_imports['gcp'])}

CRITICAL RULES:
1. Use EXACTLY this format for the Diagram instantiation:
   with Diagram(name="Architecture", direction="TB", filename="diagram.png", show=False):

2. NEVER connect lists directly to lists! This will cause TypeError.
   INCORRECT: ❌
   [node1, node2] >> [node3, node4]  # This will fail!
   
   CORRECT: ✅
   # Method 1: Connect each source to each target using loops
   for source in [node1, node2]:
       for target in [node3, node4]:
           source >> target

   # Method 2: Connect individual elements
   node1 >> node3
   node1 >> node4
   node2 >> node3
   node2 >> node4

3. Valid connection patterns:
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

4. For bidirectional connections with lists:
   # INCORRECT: ❌
   [node1, node2] << Edge(label="connects") << [node3, node4]
   
   # CORRECT: ✅
   for source in [node1, node2]:
       for target in [node3, node4]:
           source << Edge(label="connects") << target

Here's a reference example for {platform}:
{platform_examples.get(platform.lower(), platform_examples['gcp'])}

Example of correct list-to-list connection:
'''
# Define service groups
frontend = [AppEngine("fe1"), AppEngine("fe2")]
backend = [Functions("be1"), Functions("be2")]

# Connect groups correctly using loops
for f in frontend:
    for b in backend:
        f >> Edge(color="blue", label="calls") >> b

# Or connect specific paths
frontend[0] >> backend[0]
frontend[1] >> backend[1]
'''

Make sure to:
1. Use meaningful cluster names
2. Properly nest related services
3. Show clear data flow between components
4. Group related services in clusters
5. Use descriptive labels
6. Maintain proper hierarchy
7. NEVER connect lists directly - use loops or individual connections
8. Use appropriate services for {platform}
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
        
        # Remove any leading/trailing whitespace
        code = code.strip()
        
        return code

    def get_agent(self):
        return self.agent