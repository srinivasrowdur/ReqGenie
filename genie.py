from dotenv import load_dotenv
import os
import json
import tempfile
import subprocess
import sys
from jira_service import JiraService
from agents.elaborator_agent import ElaboratorAgent
from agents.validator_agent import ValidatorAgent
from agents.finalizer_agent import FinalizerAgent
from agents.test_generator_agent import TestGeneratorAgent
from agents.code_generator_agent import CodeGeneratorAgent
from agents.code_reviewer_agent import CodeReviewerAgent
from agents.jira_agent import JiraAgent
from agents.diagram_agent import DiagramAgent

# Load environment variables before any other imports
load_dotenv()

import streamlit as st
from swarm import Swarm, Agent
from streamlit_extras.stateful_button import button
import time
from PyPDF2 import PdfReader

# Initialize Swarm client
client = Swarm()

# Initialize agents
def create_agents(client: Swarm):
    elaborator = ElaboratorAgent(client)
    validator = ValidatorAgent(client)
    finalizer = FinalizerAgent(client)
    test_generator = TestGeneratorAgent(client)
    code_generator = CodeGeneratorAgent(client)
    code_reviewer = CodeReviewerAgent(client)
    jira_creator = JiraAgent(client)
    diagram_generator = DiagramAgent(client)
    
    return elaborator, validator, finalizer, test_generator, code_generator, code_reviewer, jira_creator, diagram_generator

# Set page config
st.set_page_config(
    page_title="ReqGenie",
    page_icon="🧞",
    layout="wide",
    menu_items=None
)

# Hide Streamlit style elements
hide_st_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Create UI
st.title("Requirement Analysis Genie")
st.write("This is a demo of orchestrated agents that can analyse requirements, validate them and generate sample code.")
st.write("Enter a requirement and get detailed analysis - (no need to upload documents!)")

# Add settings in sidebar
st.sidebar.title("Settings")
with st.sidebar:
    app_type = st.selectbox(
        "Select Application Type",
        ["Web Application", "Web Service"],
        key="app_type"
    )
    programming_language = st.selectbox(
        "Select Programming Language",
        ["Python", "JavaScript", "Java", "C#"],
        key="language"
    )
    cloud_environment = st.selectbox(
        "Select Cloud Environment",
        ["GCP", "AWS", "Azure"],
        index=0,  # Default to GCP
        key="cloud_env"
    )
    
    # Add NFR file upload
    st.markdown("---")
    st.subheader("Non-Functional Requirements")
    nfr_file = st.file_uploader("Upload NFR document", type=['txt', 'md', 'pdf'])
    nfr_content = ""
    if nfr_file is not None:
        if nfr_file.type == "application/pdf":
            pdf_reader = PdfReader(nfr_file)
            for page in pdf_reader.pages:
                nfr_content += page.extract_text()
        else:
            nfr_content = nfr_file.getvalue().decode()
        st.success("NFR document loaded!")
    
    # Add Jira integration toggle and settings
    st.markdown("---")
    update_jira = st.toggle('Update Jira', value=False, help='Toggle to enable/disable Jira updates')
    if update_jira:
        st.info("Jira updates will be created for the requirements")
        
        # Add Jira configuration fields
        jira_project = st.text_input(
            "Jira Project Key",
            value="SCRUM",
            help="Enter the project key where tickets should be created (e.g., PROJ)"
        )
        jira_component = st.text_input(
            "Component Name",
            value="frontend",
            help="Enter the component name for the tickets (optional)"
        )
        
        # Test Jira connection when configuration is provided
        if jira_project:
            try:
                jira_service = JiraService()
                if jira_service.test_connection():
                    if jira_service.validate_project(jira_project):
                        st.success("✅ Jira connection successful!")
            except ValueError as e:
                st.error(f"Configuration Error: {str(e)}")
            except ConnectionError as e:
                st.error(f"Connection Error: {str(e)}")
            except Exception as e:
                st.error(f"Jira Error: {str(e)}")

# Input field with default text
requirement = st.text_input(
    "Enter your requirement:",
    value="Create a secure login screen with email and password authentication, including input validation and error handling.",
    key="requirement_input"
)

def stream_content(tab_placeholder):
    """Improved streaming function with better UI"""
    message_placeholder = tab_placeholder.empty()
    full_response = []

    def handle_chunk(chunk):
        try:
            content = None
            if isinstance(chunk, dict) and "content" in chunk:
                content = chunk["content"]
            elif isinstance(chunk, str):
                content = chunk
                
            if content is not None:  # Only append and update if content exists
                full_response.append(content)
                message_placeholder.markdown(''.join(full_response))
        except Exception as e:
            st.error(f"Streaming error: {str(e)}")
    
    return handle_chunk, full_response

# Define dynamic tab names based on NFR presence
def get_tab_names(has_nfrs):
    base_tabs = ["Requirements"]
    if has_nfrs:
        base_tabs.append("NFR Analysis")
    return base_tabs + ["Validation", "Final Specs", "Test Cases", "Code", "Review", "Architecture"]

if st.button("Analyze"):
    if requirement:
        try:
            # Create agents with client
            elaborator, validator, finalizer, test_generator, code_generator, code_reviewer, jira_creator, diagram_generator = create_agents(client)
            
            # Determine if we have NFRs and create tabs accordingly
            has_nfrs = bool(nfr_content.strip())
            TAB_NAMES = get_tab_names(has_nfrs)
            tabs = st.tabs([name for name in TAB_NAMES])
            
            # Track current tab index
            current_tab = 0
            
            # Elaboration of functional requirements
            with tabs[current_tab]:
                st.subheader("Elaborated Functional Requirements")
                handle_chunk, elaboration_content = stream_content(tabs[current_tab])
                
                # Get the stream directly from the agent
                elaboration_stream = elaborator.elaborate_requirements(requirement, app_type)
                
                # Stream the chunks for UI updates
                for chunk in elaboration_stream:
                    handle_chunk(chunk)
                
                # Store the elaboration for later use
                elaboration = ''.join(filter(None, elaboration_content))
                st.sidebar.success("✅ Functional Requirements Analysis Complete")
            current_tab += 1

            # NFR Analysis (only if NFRs are provided)
            nfr_analysis = ""
            if has_nfrs:
                with tabs[current_tab]:
                    st.subheader("Non-Functional Requirements Analysis")
                    handle_chunk, nfr_analysis_content = stream_content(tabs[current_tab])
                    
                    # Get the stream directly from the agent
                    nfr_stream = elaborator.analyze_nfr(nfr_content, app_type)
                    for chunk in nfr_stream:
                        handle_chunk(chunk)
                    
                    nfr_analysis = ''.join(filter(None, nfr_analysis_content))
                    st.sidebar.success("✅ NFR Analysis Complete")
                current_tab += 1

            # Validation
            with tabs[current_tab]:
                st.subheader("Validation Review")
                handle_chunk, validation_content = stream_content(tabs[current_tab])
                
                # Get validation stream from the agent
                validation_stream = validator.validate_requirements(
                    elaboration=elaboration,
                    nfr_analysis=nfr_analysis if has_nfrs else ""
                )
                
                for chunk in validation_stream:
                    handle_chunk(chunk)
                validation = ''.join(filter(None, validation_content))
                st.sidebar.success("✅ Validation Complete")
            current_tab += 1

            # Final requirements
            with tabs[current_tab]:
                st.subheader("Final Requirements")
                handle_chunk, final_content = stream_content(tabs[current_tab])
                
                # Prepare NFR data if available
                nfr_data = None
                if has_nfrs:
                    nfr_data = {
                        'document': nfr_content,
                        'analysis': nfr_analysis
                    }
                
                # Get finalization stream from the agent
                final_stream = finalizer.finalize_requirements(
                    original_requirement=requirement,
                    elaboration=elaboration,
                    validation=validation,
                    nfr_data=nfr_data
                )
                
                for chunk in final_stream:
                    handle_chunk(chunk)
                final_requirements = ''.join(filter(None, final_content))
                st.sidebar.success("✅ Final Requirements Complete")
            current_tab += 1

            # Test Cases
            with tabs[current_tab]:
                st.subheader("Test Cases")
                handle_chunk, test_content = stream_content(tabs[current_tab])
                
                # Get test cases stream from the agent
                test_stream = test_generator.generate_test_cases(
                    requirement=requirement,
                    final_requirements=final_requirements,
                    programming_language=programming_language,
                    nfr_analysis=nfr_analysis if has_nfrs else ""
                )
                
                for chunk in test_stream:
                    handle_chunk(chunk)
                test_cases = ''.join(filter(None, test_content))
                st.sidebar.success("✅ Test Cases Generated")
            current_tab += 1

            # Code Generation
            with tabs[current_tab]:
                st.subheader("Generated Code")
                handle_chunk, code_content = stream_content(tabs[current_tab])
                
                # Get code generation stream from the agent
                code_stream = code_generator.generate_code(
                    final_requirements=final_requirements,
                    programming_language=programming_language,
                    app_type=app_type,
                    nfr_analysis=nfr_analysis if has_nfrs else None
                )
                
                for chunk in code_stream:
                    handle_chunk(chunk)
                generated_code = ''.join(filter(None, code_content))
                st.sidebar.success("✅ Code Generated")
            current_tab += 1

            # Code Review
            with tabs[current_tab]:
                st.subheader("Code Review Analysis")
                handle_chunk, review_content = stream_content(tabs[current_tab])
                
                review_stream = code_reviewer.review_code(
                    final_requirements=final_requirements,
                    generated_code=generated_code,
                    test_cases=test_cases,
                    nfr_analysis=nfr_analysis if has_nfrs else ""
                )
                
                for chunk in review_stream:
                    handle_chunk(chunk)
                st.sidebar.success("✅ Code Review Complete")
            current_tab += 1

            # Generate Architecture Diagram
            with tabs[current_tab]:
                st.subheader("Architecture Diagram")
                handle_chunk, diagram_content = stream_content(tabs[current_tab])
                
                # Get diagram code stream from the agent
                diagram_stream = diagram_generator.generate_diagram(
                    requirement=requirement,
                    architecture_type=app_type,
                    platform=cloud_environment.lower(),
                    style={"direction": "TB", "show_labels": True}
                )
                
                for chunk in diagram_stream:
                    handle_chunk(chunk)
                
                # Get the complete diagram code
                diagram_code = ''.join(filter(None, diagram_content))
                
                # Show the diagram code in an expandable section
                with st.expander("View Diagram Code"):
                    st.code(diagram_code, language="python")
                
                try:
                    with st.spinner("Generating diagram..."):
                        # Create a temporary directory for diagram generation
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Create paths
                            temp_py_path = os.path.join(temp_dir, "diagram.py")
                            
                            # Save the code
                            with open(temp_py_path, "w") as f:
                                f.write(diagram_code)
                            
                            # Execute the diagram code using subprocess
                            process = subprocess.run(
                                [sys.executable, temp_py_path],
                                cwd=temp_dir,
                                capture_output=True,
                                text=True
                            )
                            
                            if process.returncode != 0:
                                st.error("Error executing diagram code:")
                                st.error(process.stderr)
                            else:
                                # Look for the generated diagram
                                diagram_files = [f for f in os.listdir(temp_dir) if f.endswith('.png')]
                                if diagram_files:
                                    diagram_path = os.path.join(temp_dir, diagram_files[0])
                                    with open(diagram_path, "rb") as f:
                                        st.image(f.read())
                                else:
                                    st.error("No diagram file generated")
                                    st.error("Directory contents:")
                                    st.code('\n'.join(os.listdir(temp_dir)))
                                    st.error("Process output:")
                                    st.code(process.stdout)
                                
                except Exception as e:
                    st.error(f"Error generating diagram: {str(e)}")
                
                st.sidebar.success("✅ Architecture Diagram Generated")

            # Show completion message
            st.sidebar.success("✨ Analysis Complete!")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.sidebar.error("❌ Process failed")