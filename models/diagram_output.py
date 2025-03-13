from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import re
import os

class DiagramNode(BaseModel):
    """A node in the diagram"""
    name: str = Field(..., description="The variable name for this node (must be a valid Python identifier)")
    type: str = Field(..., description="The class type of this node (e.g., 'Functions', 'APIGateway')")
    label: str = Field(..., description="The display label for this node")
    cluster: Optional[str] = Field(None, description="The cluster this node belongs to (or null)")

class DiagramCluster(BaseModel):
    """A cluster in the diagram"""
    name: str = Field(..., description="The name identifier for this cluster")
    label: str = Field(..., description="The display label for this cluster")
    parent: Optional[str] = Field(None, description="The parent cluster (or null for top-level)")

class DiagramConnection(BaseModel):
    """A connection between nodes in the diagram"""
    from_node: str = Field(..., description="The source node name", alias="from")
    to_node: str = Field(..., description="The target node name", alias="to")
    edge_attrs: Optional[Dict[str, str]] = Field(None, description="Edge attributes like color and label")

class DiagramOutput(BaseModel):
    """Structured output for generated diagrams"""
    diagram_type: Optional[str] = Field(None, description="Type of the architecture diagram (e.g., 'Cloud Architecture Diagram')")
    explanation: Optional[str] = Field(None, description="Detailed explanation of the diagram and its components")
    imports: List[str] = Field(..., description="List of import statements")
    nodes: List[DiagramNode] = Field(..., description="List of nodes in the diagram")
    clusters: List[DiagramCluster] = Field(..., description="List of clusters in the diagram")
    connections: List[DiagramConnection] = Field(..., description="List of connections between nodes")
    
    def generate_diagram_code(self) -> str:
        """Convert the structured representation to Python code"""
        # COMPLETELY NEW APPROACH: Build code from scratch with explicit control over newlines
        code = []
        
        # Validate our imports and ensure they're properly formatted
        if not self.imports or not isinstance(self.imports, list):
            # Default fallback imports if none are provided
            validated_imports = [
                "from diagrams import Diagram, Cluster, Edge",
                "from diagrams.gcp.compute import Functions",
                "from diagrams.gcp.database import SQL"
            ]
        else:
            # Filter and clean imports
            validated_imports = []
            
            # Ensure the basic diagrams import is always present
            basic_import_found = False
            for item in self.imports:
                if not isinstance(item, str):
                    continue
                    
                # Handle surrounding quotes
                cleaned_item = item
                if (cleaned_item.startswith("'") and cleaned_item.endswith("'")) or (cleaned_item.startswith('"') and cleaned_item.endswith('"')):
                    cleaned_item = cleaned_item[1:-1].strip()
                
                # Check if this is a basic diagrams import
                if "from diagrams import" in cleaned_item and "Diagram" in cleaned_item:
                    basic_import_found = True
                
                # Skip invalid formats
                if not (cleaned_item.startswith('from ') and ' import ' in cleaned_item):
                    continue
                
                # Clean up any whitespace issues
                cleaned_import = cleaned_item.strip()
                validated_imports.append(cleaned_import)
            
            # Add the basic import if it's not already there
            if not basic_import_found:
                validated_imports.insert(0, "from diagrams import Diagram, Cluster, Edge")
        
        # Add each import on its own line
        for import_stmt in validated_imports:
            code.append(import_stmt)
        
        # Debug logging to help diagnose import issues
        import logging
        logging.info(f"DIAGRAM IMPORTS: Using {len(validated_imports)} validated imports")
        for i, imp in enumerate(validated_imports):
            logging.info(f"  Import #{i+1}: '{imp}'")
        
        # Add a blank line after imports
        code.append("")
        
        # Add code to get current directory for absolute path
        code.append("import os")
        code.append("current_dir = os.getcwd()")
        code.append("output_path = os.path.join(current_dir, 'diagram')")
        code.append("")
        
        # Create diagram with title if available
        diagram_title = self.diagram_type or "Architecture Diagram"
        code.append(f'with Diagram("{diagram_title}", show=False, filename="diagram", outformat="png", direction="LR"):')
        
        # Create cluster definitions with proper indentation
        current_indent = "    "
        for cluster in self.clusters:
            cluster_def = f'{current_indent}with Cluster("{cluster.label}"):'
            code.append(cluster_def)
            code.append(f'{current_indent}    pass  # {cluster.label} services')
        
        # Add a blank line before nodes
        code.append("")
        
        # Create nodes at the correct indentation level
        for node in self.nodes:
            cluster = node.cluster
            indent = current_indent
            if cluster:
                # Find the cluster this node belongs to and adjust indentation
                for c in self.clusters:
                    if c.label == cluster:
                        indent += "    "
                        break
            node_def = f'{indent}{node.name} = {node.type}("{node.label}")'
            code.append(node_def)
        
        # Add a blank line before connections
        code.append("")
        
        # Create connections - simplified approach following the sample code
        for conn in self.connections:
            edge_attrs = conn.edge_attrs or {}
            attrs = ", ".join(f'{k}="{v}"' for k, v in edge_attrs.items())
            
            # Simplified connection formatting
            if attrs:
                conn_line = f'{current_indent}{conn.from_node} >> Edge({attrs}) >> {conn.to_node}'
            else:
                conn_line = f'{current_indent}{conn.from_node} >> {conn.to_node}'
                
            code.append(conn_line)
        
        # Join the code lines with explicit newlines
        final_code = '\n'.join(code)
        
        # Final validation - try to compile the code to catch syntax errors
        try:
            compile(final_code, '<string>', 'exec')
        except Exception as e:
            # Log the error but return the code anyway - the validation in render_diagram will catch it
            import logging
            logging.error(f"Generated diagram code has errors: {str(e)}")
        
        return final_code
        
    @property
    def diagram_code(self) -> str:
        """Generate and return the diagram code"""
        return self.generate_diagram_code() 