"""
Architecture diagram generator agent responsible for creating architecture diagrams.
"""
# Import OpenAI Agents SDK
from agents import Agent
from prompts.diagram_prompt import DIAGRAM_SYSTEM_PROMPT
from models.diagram_output import DiagramOutput

def create_diagram_agent(model="o3-mini", language="English"):
    """Create a diagram generator agent.
    
    Args:
        model: The model to use for the agent
        language: The language to use for explanations
        
    Returns:
        The diagram generator agent
    """
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        language_instruction = """
        解説文とコメントを日本語で作成してください。
        コード自体は英語で記述し、Pythonの標準的な命名規則に従ってください。
        """
    elif language == "Italian":
        language_instruction = """
        Fornisci spiegazioni e commenti in italiano.
        Il codice stesso dovrebbe essere in inglese e seguire le convenzioni di denominazione standard di Python.
        """
    
    # Our updated instructions that return structured JSON instead of raw code
    instructions = """You are an expert in creating serverless architecture diagrams.
    
    You MUST respond with a structured JSON object containing:
    
    1. imports: An array of properly formatted import statements
    2. nodes: An array of node objects for the diagram
    3. clusters: An array of cluster objects
    4. connections: An array of connection objects
    
    ⚠️ CRITICAL - IMPORT FORMAT REQUIREMENTS ⚠️
    
    Each import MUST:
    - Be a separate string in the "imports" array
    - Follow EXACTLY the pattern: "from X import Y"
    - Use ONLY the correct import paths listed below
    - NEVER combine multiple import statements in one string
    
    CORRECT FORMAT:
    "imports": [
        "from diagrams import Diagram, Cluster, Edge",
        "from diagrams.gcp.compute import Functions",
        "from diagrams.gcp.api import APIGateway"
    ]
    
    INCORRECT FORMAT:
    "imports": [
        "from diagrams import Diagram, Cluster from diagrams.gcp.compute import Functions",
        "import diagrams.gcp.api.APIGateway",
        "Functions from diagrams.gcp.compute"
    ]
    
    For GCP services, use ONLY these import paths:
    - from diagrams import Diagram, Cluster, Edge
    - from diagrams.gcp.compute import Functions, Run, AppEngine, ComputeEngine
    - from diagrams.gcp.api import APIGateway, Endpoints
    - from diagrams.gcp.database import Firestore, SQL, BigTable
    - from diagrams.gcp.storage import Storage
    - from diagrams.gcp.analytics import PubSub, BigQuery
    - from diagrams.gcp.security import Iam, KMS
    - from diagrams.gcp.operations import Monitoring, Logging
    
    For AWS services, use ONLY these import paths:
    - from diagrams import Diagram, Cluster, Edge
    - from diagrams.aws.compute import Lambda, EC2
    - from diagrams.aws.integration import APIGateway
    - from diagrams.aws.database import DynamodbTable, RDS
    - from diagrams.aws.storage import S3
    - from diagrams.aws.integration import SQS
    - from diagrams.aws.security import Cognito, IAM
    - from diagrams.aws.management import Cloudwatch
    
    For Azure services, use ONLY these import paths:
    - from diagrams import Diagram, Cluster, Edge
    - from diagrams.azure.compute import FunctionApps, VM
    - from diagrams.azure.web import AppService, APIManagement
    - from diagrams.azure.database import CosmosDb, SQLDatabase
    - from diagrams.azure.storage import StorageAccounts
    - from diagrams.azure.integration import ServiceBus
    - from diagrams.azure.security import KeyVault
    - from diagrams.azure.monitor import ApplicationInsights
    
    Your complete response MUST be valid JSON following EXACTLY this structure:
    
    {
        "imports": [
            "from diagrams import Diagram, Cluster, Edge",
            "from diagrams.gcp.compute import Functions",
            "from diagrams.gcp.api import APIGateway"
        ],
        "nodes": [
            {
                "name": "api",
                "type": "APIGateway",
                "label": "API Gateway",
                "cluster": null
            },
            {
                "name": "auth_fn",
                "type": "Functions", 
                "label": "Auth Function",
                "cluster": "Backend Services"
            }
        ],
        "clusters": [
            {
                "name": "backend",
                "label": "Backend Services",
                "parent": null
            }
        ],
        "connections": [
            {
                "from": "api",
                "to": "auth_fn",
                "edge_attrs": {
                    "color": "blue",
                    "label": "API requests"
                }
            }
        ]
    }
    
    DO NOT include any text or explanation before or after the JSON.
    ONLY return the structured JSON object.
    """
    
    # Combine original instructions with language-specific ones
    if language_instruction:
        instructions = f"{instructions}\n\n{language_instruction}"
    
    # Create the agent with structured output type
    return Agent(
        name="DiagramGenerator",
        instructions=instructions,
        output_type=DiagramOutput,
        model=model,
    )
    
def create_diagram_prompt(requirements_doc, app_type, cloud_env, language="English"):
    """Create a prompt for generating architecture diagrams.
    
    Args:
        requirements_doc: The requirements document to generate diagrams from
        app_type: The type of application
        cloud_env: The cloud environment (AWS, GCP, Azure)
        language: The language to use for explanations
        
    Returns:
        The diagram prompt
    """
    language_instruction = ""
    if language != "English":
        if language == "Japanese":
            language_instruction = "解説文とコメントを日本語で提供してください。構造化されたデータは英語のままで構いません。"
        elif language == "Italian":
            language_instruction = "Fornisci spiegazioni e commenti in italiano. I dati strutturati possono rimanere in inglese."
    
    prompt = f"""Analyze the following requirements and create an architecture diagram for a {app_type} deployed on {cloud_env}:

{requirements_doc}

Create a detailed architecture diagram showing all components, their relationships, and data flows. Design an efficient
and secure architecture that follows best practices for {cloud_env}.

Include these key components as appropriate:
- API/Interface layer
- Compute/Processing services
- Storage solutions
- Database services
- Security components
- Monitoring/Logging
- Integration with other systems if needed

Follow these design principles:
1. Use {cloud_env}-native services where possible
2. Group related components in logical clusters
3. Show clear data flows between components
4. Design for scalability and reliability
5. Include security and monitoring components

Return a structured response that I can convert to a diagram using the 'diagrams' Python library.
"""
    
    if language_instruction:
        prompt = f"{prompt}\n\n{language_instruction}"
    
    return prompt 