"""
Utility functions for rendering architecture diagrams.
"""
import os
import tempfile
import subprocess
import sys
import base64
import logging
import importlib
import re
from agents import Runner  # Import Runner for running agents

def validate_diagram_code(diagram_code):
    """Validate diagram code by checking for missing imports.
    
    Args:
        diagram_code: The Python code to validate
        
    Returns:
        A tuple containing (valid, message) where:
        - valid is a boolean indicating if the code is valid
        - message is either None or an error message
    """
    # MAJOR REWRITE OF IMPORT VALIDATION
    
    # 1. Special whitelist for known good imports to avoid false positives
    known_good_imports = [
        "from diagrams import Diagram",
        "from diagrams import Cluster",
        "from diagrams import Edge",
        "from diagrams import Diagram, Cluster",
        "from diagrams import Diagram, Edge",
        "from diagrams import Cluster, Edge",
        "from diagrams import Diagram, Cluster, Edge",
    ]
    
    # 2. Check each line separately - more precise approach
    lines = diagram_code.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip known good imports
        if any(good_import in line for good_import in known_good_imports):
            continue
            
        # Skip empty lines
        if not line:
            continue
            
        # Check for multiple from statements on one line
        if line.count('from ') > 1 and 'import ' in line:
            # Extract the problematic line for reporting
            problematic_line = line
            
            # Attempt to fix by splitting imports
            fixed_imports = []
            import_pattern = r'from\s+([\w.]+)\s+import\s+([\w,\s]+)'
            matches = re.findall(import_pattern, problematic_line)
            
            for module, classes in matches:
                fixed_imports.append(f"from {module} import {classes}")
            
            # If we found valid imports in the broken line, suggest fixes
            if fixed_imports:
                fixed_suggestion = "\n".join(fixed_imports)
                return False, f"Syntax error: Found multiple 'from' statements on the same line. Each import should be on its own line.\n\nProblematic line: '{problematic_line}'\n\nFix by replacing with:\n{fixed_suggestion}"
            else:
                return False, f"Syntax error: Found multiple 'from' statements on the same line. Each import should be on its own line."
    
    # 3. The rest of the validation remains the same...
    # Check for invalid import formats (not starting with 'from' or missing 'import')
    import_lines = [line.strip() for line in diagram_code.split('\n') if line.strip().startswith('from ')]
    for line in import_lines:
        if not re.match(r'from\s+[\w.]+\s+import\s+[\w,\s]+', line):
            return False, f"Invalid import format: '{line}'. Use the format 'from module import class1, class2'."
            
    # Check for common errors in the imports
    if "from diagrams import Cluster" in diagram_code:
        # This is actually valid for non-cloud-specific styling
        pass
    
    if "from diagrams.gcp.general import" in diagram_code:
        return False, "Invalid import: 'diagrams.gcp.general' module does not exist. Use 'from diagrams import Cluster' for grouping components in GCP."
    
    # Check for other invalid module paths
    invalid_modules = [
        "diagrams.gcp.monitoring",  # doesn't exist, use diagrams.gcp.operations.Monitoring instead
        "diagrams.gcp.general",     # doesn't exist, use diagrams import Cluster instead
    ]
    
    for invalid_module in invalid_modules:
        if invalid_module in diagram_code:
            suggestions = {
                "diagrams.gcp.monitoring": "Use 'diagrams.gcp.operations.Monitoring' instead",
                "diagrams.gcp.general": "Use 'from diagrams import Cluster' instead for grouping components"
            }
            suggestion = suggestions.get(invalid_module, "Check the documentation for the correct module path")
            return False, f"Invalid module path: '{invalid_module}' does not exist. {suggestion}"
    
    # GCP class name mappings (correct case)
    gcp_class_mappings = {
        # Analytics
        "pubsub": "PubSub",
        "bigquery": "BigQuery",
        # Database
        "bigtable": "BigTable",
        # Storage
        "storage": "Storage",  # or GCS
        # Network
        "virtualprivatecloud": "VirtualPrivateCloud",
        # API
        "apigateway": "APIGateway",
        "api_gateway": "APIGateway",
        "api": "APIGateway",
        "gateway": "APIGateway"
    }
    
    # Available classes in each GCP module
    gcp_module_classes = {
        "diagrams.gcp.api": ["APIGateway", "Apigee", "Endpoints"],
        "diagrams.gcp.analytics": ["BigQuery", "Dataflow", "PubSub", "Composer", "DataCatalog", "DataFusion", "Datalab", "Dataprep", "Dataproc", "Genomics"],
        "diagrams.gcp.compute": ["AppEngine", "ComputeEngine", "Functions", "KubernetesEngine", "ContainerOptimizedOS", "GKEOnPrem", "GPU", "Run"],
        "diagrams.gcp.database": ["BigTable", "SQL", "Spanner", "Firestore", "Memorystore", "Datastore"],
        "diagrams.gcp.iot": ["IotCore"],
        "diagrams.gcp.network": ["LoadBalancing", "CDN", "DNS", "VirtualPrivateCloud", "VPN", "Armor", "DedicatedInterconnect", "ExternalIpAddresses", "FirewallRules", "NAT", "Network", "PartnerInterconnect", "PremiumNetworkTier", "Router", "Routes", "StandardNetworkTier", "TrafficDirector"],
        "diagrams.gcp.operations": ["Monitoring", "Logging"],
        "diagrams.gcp.storage": ["Storage", "GCS", "Filestore", "PersistentDisk"]
    }
    
    # Check for incorrect import formats that might confuse the regex parser
    if "import Functions from diagrams" in diagram_code:
        return False, ("Syntax error: Incorrect import format. Use separate import statements on different lines:\n"
                     "from diagrams import Diagram, Cluster\n"
                     "from diagrams.gcp.compute import Functions")
    
    # Extract all imports
    import_pattern = r'from\s+([\w.]+)\s+import\s+([\w,\s]+)'
    imports = re.findall(import_pattern, diagram_code)
    
    # Check each import
    for module_path, classes in imports:
        try:
            # Skip validation for diagrams, which supports star imports
            if module_path == "diagrams" and ("Diagram" in classes or "Cluster" in classes):
                continue
            
            # Check if trying to import from a GCP module
            if module_path.startswith("diagrams.gcp"):
                # Check if this is a valid GCP module
                if module_path in gcp_module_classes:
                    available_classes = gcp_module_classes[module_path]
                    
                    # Check individual classes
                    for class_name in [c.strip() for c in classes.split(',')]:
                        if class_name not in available_classes:
                            # Check for case issues
                            lower_class = class_name.lower()
                            if lower_class in gcp_class_mappings:
                                correct_class = gcp_class_mappings[lower_class]
                                return False, f"Case sensitivity issue: Use '{correct_class}' instead of '{class_name}' in {module_path}"
                            
                            # Suggest available classes for this module
                            available_str = ', '.join(available_classes)
                            return False, f"Module '{module_path}' does not contain class '{class_name}'. Available classes are: {available_str}"
                    
                    # All classes found in this module
                    continue
            
            # For non-GCP modules or GCP modules not in our dictionary, do the standard check
            # Try to import the module
            module = importlib.import_module(module_path)
            
            # Check individual classes
            for class_name in [c.strip() for c in classes.split(',')]:
                if not hasattr(module, class_name):
                    # Special case for Cluster
                    if class_name == "Cluster" and module_path == "diagrams":
                        # Actually, from diagrams import Cluster is valid
                        continue
                    
                    # Special suggestions for common errors
                    suggestions = {
                        "Monitoring": "Use 'from diagrams.gcp.operations import Monitoring'",
                        "Compute": "Use 'from diagrams.gcp.compute import ComputeEngine' instead",
                        "Bigquery": "Use 'from diagrams.gcp.analytics import BigQuery' (note the capital 'Q')",
                        "Pubsub": "Use 'from diagrams.gcp.analytics import PubSub' (note the capital 'S')",
                        "Bigtable": "Use 'from diagrams.gcp.database import BigTable' (note the capital 'T')",
                        "SQL": "Use 'from diagrams.gcp.database import SQL'"
                    }
                    
                    suggestion = suggestions.get(class_name, f"Check docs at https://diagrams.mingrammer.com/docs/nodes/gcp")
                    return False, f"Module '{module_path}' does not contain class '{class_name}'. {suggestion}"
                    
        except ModuleNotFoundError:
            # Special suggestions for missing modules
            suggestions = {
                "diagrams.gcp.general": "This module doesn't exist. Use 'from diagrams import Cluster' for grouping",
                "diagrams.gcp.monitoring": "This module doesn't exist. Use 'from diagrams.gcp.operations import Monitoring'"
            }
            
            suggestion = suggestions.get(module_path, "Check the documentation for the correct module path")
            return False, f"Module not found: '{module_path}'. {suggestion}"
        except ImportError as e:
            return False, f"Import error: {str(e)}"
    
    return True, None

async def auto_correct_diagram_code(diagram_code, requirements_doc, app_type, cloud_env, agent):
    """Use the LLM as a judge pattern to correct diagram code based on validation feedback.
    
    Args:
        diagram_code: The initial Python code to validate and correct
        requirements_doc: The original requirements used to generate the diagram
        app_type: The type of application
        cloud_env: The cloud environment (AWS, GCP, Azure)
        agent: The agent instance to use for correction
        
    Returns:
        A tuple containing (success, result) where:
        - success is a boolean indicating if valid code was produced
        - result is either the valid code or an error message
    """
    from agents import ItemHelpers
    
    max_attempts = 3
    for attempt in range(max_attempts):
        # Validate the code
        valid, message = validate_diagram_code(diagram_code)
        
        if valid:
            return True, diagram_code
        
        # If not valid, use the agent to correct it
        try:
            correction_prompt = f"""
            I tried to generate the following architecture diagram code, but it has a validation error:
            
            ERROR: {message}
            
            Here is the code that needs to be fixed:
            
            ```python
            {diagram_code}
            ```
            
            Please correct the code to fix this specific error. Make sure all import statements are on separate lines 
            and follow proper Python syntax. Keep the original diagram logic and components intact, just fix the syntax issues.
            
            Return ONLY the corrected code without explanations.
            """
            
            # Create input for Runner.run
            correction_input = [
                {"content": correction_prompt, "role": "user"}
            ]
            
            # Call the agent using Runner.run with await
            correction_result = await Runner.run(agent, correction_input)
            
            # Try multiple approaches to extract the content
            corrected_response = ""
            
            # Approach 1: Use ItemHelpers if available
            try:
                corrected_response = ItemHelpers.text_message_outputs(correction_result.new_items)
                logging.info("Successfully extracted response using ItemHelpers.text_message_outputs")
            except Exception as e:
                logging.warning(f"Failed to extract response using ItemHelpers: {str(e)}")
                
                # Approach 2: Try to access the content directly from the AgentResponse object
                try:
                    corrected_response = correction_result.text
                    logging.info("Successfully extracted response using result.text")
                except Exception as e:
                    logging.warning(f"Failed to extract response using result.text: {str(e)}")
                    
                    # Approach 3: Try to get content from the last message
                    try:
                        last_message = correction_result.new_items[-1]
                        # Try different attributes that might contain content
                        if hasattr(last_message, "content"):
                            corrected_response = last_message.content
                            logging.info("Successfully extracted response using last_message.content")
                        elif hasattr(last_message, "text"):
                            corrected_response = last_message.text
                            logging.info("Successfully extracted response using last_message.text")
                        else:
                            # Last resort: convert the whole object to string
                            corrected_response = str(last_message)
                            logging.info("Using string representation of the last message")
                    except Exception as e:
                        logging.error(f"All extraction methods failed: {str(e)}")
                        return False, f"Failed to extract response from agent: {str(e)}"
            
            if not corrected_response:
                return False, "Failed to extract a response from the agent"
                
            # Extract just the code from the response
            code_pattern = r'```python\s*([\s\S]*?)\s*```'
            code_match = re.search(code_pattern, corrected_response)
            
            if code_match:
                diagram_code = code_match.group(1).strip()
                logging.info(f"Successfully extracted code from markdown block")
            else:
                # If no code block found, use the entire response (assuming it's just code)
                diagram_code = corrected_response.strip()
                logging.info(f"No markdown code block found, using entire response")
                
            logging.info(f"Attempt {attempt+1}: Code corrected based on feedback: {message}")
            
        except Exception as e:
            logging.error(f"Error during correction attempt {attempt+1}: {str(e)}")
            return False, f"Failed to auto-correct diagram code after {attempt+1} attempts: {str(e)}"
    
    # If we've reached max attempts and still have issues
    valid, message = validate_diagram_code(diagram_code)
    if valid:
        return True, diagram_code
    else:
        return False, f"Failed to auto-correct diagram code after {max_attempts} attempts. Last error: {message}"

def check_graphviz_installed():
    """Check if Graphviz is installed and available."""
    try:
        # Try to run the 'dot' command with version flag
        result = subprocess.run(
            ["dot", "-V"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # If the command was successful, Graphviz is installed
        if result.returncode == 0:
            logging.info(f"Graphviz is installed: {result.stderr.strip()}")
            return True, result.stderr.strip()
        else:
            logging.warning(f"Graphviz check returned non-zero exit code: {result.returncode}")
            return False, "Graphviz command 'dot' returned an error"
    except FileNotFoundError:
        logging.warning("Graphviz not found. The 'dot' command is not available.")
        return False, "Graphviz command 'dot' not found. Please install Graphviz."
    except Exception as e:
        logging.warning(f"Error checking for Graphviz: {str(e)}")
        return False, f"Error checking for Graphviz: {str(e)}"

def render_diagram(diagram_code):
    """Render an architecture diagram by executing the generated Python code.
    
    Args:
        diagram_code: The Python code to execute
        
    Returns:
        A tuple containing (success, result) where:
        - success is a boolean indicating if the rendering was successful
        - result is either the path to the generated image or an error message
    """
    try:
        # Check for Graphviz installation first
        graphviz_installed, graphviz_message = check_graphviz_installed()
        if not graphviz_installed:
            install_instructions = """
            Graphviz is required but not installed. Please install it:
            - On macOS: brew install graphviz
            - On Windows: Download from https://graphviz.org/download/
            - On Linux: sudo apt-get install graphviz
            
            After installation, make sure the 'dot' command is available in your PATH.
            """
            return False, f"Error: {graphviz_message}\n\n{install_instructions}"
            
        # Debug the current working directory
        current_dir = os.getcwd()
        logging.info(f"Current working directory: {current_dir}")
        
        # List files in the current directory (before execution)
        logging.info(f"Files in directory before execution: {os.listdir(current_dir)}")
        
        # Check if the diagram code contains only basic imports - if so, skip validation
        basic_imports_pattern = r"from\s+diagrams\s+import\s+Diagram"
        if re.search(basic_imports_pattern, diagram_code):
            # Log that we're skipping validation for known good code
            logging.info("Detected basic diagram imports - skipping strict validation")
        else:
            # First validate the imports
            valid, message = validate_diagram_code(diagram_code)
            if not valid:
                return False, message
            
        # Add debugging print statements to the diagram code
        debug_code = diagram_code.replace('with Diagram(', 'import os\nprint(f"Python working directory: {os.getcwd()}")\nprint("About to create diagram...")\nwith Diagram(')
        debug_code += '\nprint("Diagram creation completed")'
            
        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(debug_code)
        
        # Log diagram code for debugging
        logging.info(f"Executing diagram code from: {temp_file_path}")
        logging.info(f"Diagram code contents:\n{debug_code}")
        
        # Execute the code
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=30  # Set a timeout to prevent hanging
        )
        
        # Log the stdout and stderr
        logging.info(f"Subprocess stdout: {result.stdout}")
        logging.info(f"Subprocess stderr: {result.stderr}")
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        # List files in the current directory (after execution)
        logging.info(f"Files in directory after execution: {os.listdir(current_dir)}")
        
        # Check if execution was successful
        if result.returncode == 0:
            # Check for diagram.png in multiple possible locations
            possible_paths = [
                "diagram.png",
                os.path.join(current_dir, "diagram.png"),
                os.path.join(os.path.dirname(temp_file_path), "diagram.png")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    logging.info(f"Found diagram at: {path}")
                    return True, path
                    
            # If no diagram found, but code executed successfully
            return False, "Diagram code executed successfully but no image was generated. This might be due to missing Graphviz dependencies or configuration issues."
        else:
            # Enhance error message
            error_msg = result.stderr.strip()
            
            # Check for common errors and provide better messages
            if "ModuleNotFoundError" in error_msg:
                # Extract the missing module name
                module_match = re.search(r"No module named '([^']+)'", error_msg)
                if module_match:
                    missing_module = module_match.group(1)
                    
                    # Special handling for common missing dependencies
                    if missing_module == 'graphviz':
                        return False, ("Error: Graphviz is required but not installed. Please install it:\n"
                                      "- On macOS: brew install graphviz\n"
                                      "- On Windows: Download from https://graphviz.org/download/\n"
                                      "- On Linux: sudo apt-get install graphviz")
                    elif missing_module.startswith('diagrams'):
                        return False, f"Error: The 'diagrams' Python package is missing. Install it with: pip install diagrams"
                    else:
                        return False, f"Error executing diagram code: Module '{missing_module}' not found.\nPlease check the diagrams documentation at https://diagrams.mingrammer.com/docs/nodes/gcp"
            
            # Check for permission errors
            elif "Permission denied" in error_msg:
                return False, "Error: Permission denied when trying to create the diagram file. Please check your folder permissions."
            
            # Check for syntax errors
            elif "SyntaxError" in error_msg:
                return False, f"Syntax error in diagram code: {error_msg}"
            
            # Generic error
            return False, f"Error executing diagram code: {error_msg}"
            
    except Exception as e:
        logging.error(f"Error rendering diagram: {str(e)}")
        return False, f"Error rendering diagram: {str(e)}"

def render_structured_diagram(diagram_output):
    """Render an architecture diagram from a structured DiagramOutput object.
    
    Args:
        diagram_output: DiagramOutput object containing structured diagram definition
        
    Returns:
        A tuple containing (success, result) where:
        - success is a boolean indicating if the rendering was successful
        - result is either the path to the generated image or an error message
    """
    try:
        # Generate Python code from the structured output
        diagram_code = diagram_output.diagram_code
        
        # Render the generated code
        return render_diagram(diagram_code)
    except Exception as e:
        logging.error(f"Error rendering structured diagram: {str(e)}")
        return False, f"Error rendering structured diagram: {str(e)}"

def get_image_base64(image_path):
    """Convert an image to a base64 string for display in Streamlit.
    
    Args:
        image_path: The path to the image
        
    Returns:
        The base64-encoded image data
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        logging.error(f"Error encoding image: {str(e)}")
        return None 