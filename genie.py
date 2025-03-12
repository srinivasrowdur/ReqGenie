from dotenv import load_dotenv
import os
import json
import tempfile
import subprocess
import sys
from jira_service import JiraService

# Add the current directory to the path to make local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from GenieAgents.requirement_processor import RequirementProcessor
from GenieAgents.output_formatter import OutputFormatter

# Load environment variables before any other imports
load_dotenv()

import streamlit as st
# Import directly from agents package
from agents import Agent, Runner
from streamlit_extras.stateful_button import button
import time
from PyPDF2 import PdfReader
import asyncio
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize the requirement processor
processor = RequirementProcessor()

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

def run_async(coroutine):
    """Run an async function from a synchronous context"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

async def stream_with_ui_updates(coroutine, placeholder, message="Processing..."):
    """Improved streaming function with better UI"""
    try:
        # Create a progress bar
        progress_bar = placeholder.progress(0)
        
        # Start the coroutine
        result = await coroutine
        
        # Update progress to complete
        progress_bar.progress(100)
        placeholder.empty()  # Clear the progress bar
        
        # Format the result if it's structured data
        if isinstance(result, dict) or hasattr(result, 'dict'):
            try:
                # Convert to dict if it's a Pydantic model
                data = result.dict() if hasattr(result, 'dict') else result
                return OutputFormatter.format_any_output(data)
            except Exception as e:
                st.warning(f"Could not format structured output: {str(e)}")
                return result
        return result
        
    except Exception as e:
        placeholder.empty()
        st.error(f"Streaming error: {str(e)}")
        return f"Error: {str(e)}"

# Define dynamic tab names based on NFR presence
def get_tab_names(has_nfrs):
    base_tabs = ["Requirements"]
    if has_nfrs:
        base_tabs.append("NFR Analysis")
    return base_tabs + ["Validation", "Final Specs", "Test Cases", "Code", "Review", "Architecture"]

if st.button("Analyze"):
    if requirement:
        try:
            # Determine if we have NFRs and create tabs accordingly
            has_nfrs = bool(nfr_content.strip())
            TAB_NAMES = get_tab_names(has_nfrs)
            tabs = st.tabs([name for name in TAB_NAMES])
            
            # Track current tab index
            current_tab = 0
            
            # Prepare Jira configuration if needed
            jira_config = None
            if update_jira:
                jira_config = {
                    "project": jira_project,
                    "component": jira_component
                }
            
            # Run the full processing pipeline asynchronously
            def process_requirement():
                results = run_async(processor.process(
                    requirement=requirement,
                    app_type=app_type,
                    nfr_content=nfr_content if has_nfrs else None,
                    jira_config=jira_config,
                    language=programming_language,
                    cloud_env=cloud_environment
                ))
                
                # Format all results for better display
                formatted_results = {}
                for key, value in results.items():
                    if value is not None:
                        formatted_results[key] = OutputFormatter.format_any_output(value)
                    else:
                        formatted_results[key] = None
                
                return formatted_results
            
            # Start processing with a spinner
            with st.spinner("Processing your requirement..."):
                results = process_requirement()
            
            # Display results in respective tabs
            
            # Elaboration tab
            with tabs[current_tab]:
                st.subheader("Elaborated Functional Requirements")
                st.markdown(results["elaboration"])
                st.sidebar.success("✅ Functional Requirements Analysis Complete")
            current_tab += 1
            
            # NFR Analysis tab (if available)
            if has_nfrs:
                with tabs[current_tab]:
                    st.subheader("Non-Functional Requirements Analysis")
                    st.markdown(results["nfr_analysis"])
                    st.sidebar.success("✅ NFR Analysis Complete")
                current_tab += 1
            
            # Validation tab
            with tabs[current_tab]:
                st.subheader("Validation Review")
                st.markdown(results["func_validation"])
                if results["nfr_validation"]:
                    st.subheader("NFR Validation")
                    st.markdown(results["nfr_validation"])
                st.sidebar.success("✅ Validation Complete")
            current_tab += 1
            
            # Final Requirements tab
            with tabs[current_tab]:
                st.subheader("Final Requirements")
                st.markdown(results["final_spec"])
                st.sidebar.success("✅ Final Requirements Complete")
            current_tab += 1
            
            # Test Cases tab
            with tabs[current_tab]:
                st.subheader("Test Cases")
                st.markdown(results["tests"])
                st.sidebar.success("✅ Test Cases Generated")
            current_tab += 1
            
            # Code tab
            with tabs[current_tab]:
                st.subheader("Generated Code")
                st.markdown(results["code"])
                st.sidebar.success("✅ Code Generated")
            current_tab += 1
            
            # Code Review tab
            with tabs[current_tab]:
                st.subheader("Code Review")
                st.markdown(results["review"])
                st.sidebar.success("✅ Code Review Complete")
            current_tab += 1
            
            # Diagram tab
            with tabs[current_tab]:
                st.subheader("Architecture Diagram")
                try:
                    # Try to display the diagram if it's available
                    if "diagram_code" in results["diagrams"]:
                        st.code(results["diagrams"], language="python")
                        
                        # Try to render the diagram if possible
                        try:
                            with tempfile.NamedTemporaryFile(suffix='.py') as f:
                                f.write(results["diagrams"].encode('utf-8'))
                                f.flush()
                                
                                # Try to execute the diagram code to generate an image
                                result = subprocess.run(
                                    [sys.executable, f.name],
                                    capture_output=True,
                                    text=True
                                )
                                
                                if result.returncode == 0:
                                    # If successful, display the generated image
                                    st.image("diagram.png")
                                else:
                                    st.error(f"Error generating diagram: {result.stderr}")
                        except Exception as e:
                            st.error(f"Error rendering diagram: {str(e)}")
                    else:
                        st.markdown(results["diagrams"])
                except Exception as e:
                    st.error(f"Error with diagram: {str(e)}")
                    
                st.sidebar.success("✅ Architecture Diagram Generated")
            current_tab += 1
            
            # Jira Tickets tab (if configured)
            if jira_config:
                with tabs[current_tab]:
                    st.subheader("Jira Tickets")
                    st.markdown(results["jira"])
                    st.sidebar.success("✅ Jira Tickets Created")
                current_tab += 1
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.sidebar.error("❌ Process failed")