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

# Utility function to run async code in Streamlit
def run_async(coro):
    """Run an async function from synchronous Streamlit code"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

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
                return run_async(processor.process(
                    requirement=requirement,
                    app_type=app_type,
                    nfr_content=nfr_content if has_nfrs else None,
                    jira_config=jira_config,
                    language=programming_language,
                    cloud_env=cloud_environment
                ))
            
            # Start processing with a spinner
            with st.spinner("Processing your requirement..."):
                results = process_requirement()
            
            # Display results in respective tabs
            
            # Elaboration tab
            with tabs[current_tab]:
                st.subheader("Elaborated Functional Requirements")
                st.write(results["elaboration"])
                st.sidebar.success("✅ Functional Requirements Analysis Complete")
            current_tab += 1
            
            # NFR Analysis tab (if available)
            if has_nfrs:
                with tabs[current_tab]:
                    st.subheader("Non-Functional Requirements Analysis")
                    st.write(results["nfr_analysis"])
                    st.sidebar.success("✅ NFR Analysis Complete")
                current_tab += 1
            
            # Validation tab
            with tabs[current_tab]:
                st.subheader("Validation Review")
                st.write(results["func_validation"])
                if results["nfr_validation"]:
                    st.subheader("NFR Validation")
                    st.write(results["nfr_validation"])
                st.sidebar.success("✅ Validation Complete")
            current_tab += 1
            
            # Final Requirements tab
            with tabs[current_tab]:
                st.subheader("Final Requirements")
                st.write(results["final_spec"])
                st.sidebar.success("✅ Final Requirements Complete")
            current_tab += 1
            
            # Test Cases tab
            with tabs[current_tab]:
                st.subheader("Test Cases")
                st.write(results["tests"])
                st.sidebar.success("✅ Test Cases Generated")
            current_tab += 1
            
            # Code tab
            with tabs[current_tab]:
                st.subheader("Sample Code")
                st.code(results["code"])
                st.sidebar.success("✅ Code Generated")
            current_tab += 1
            
            # Review tab
            with tabs[current_tab]:
                st.subheader("Code Review")
                st.write(results["review"])
                st.sidebar.success("✅ Code Review Complete")
            current_tab += 1
            
            # Architecture tab
            with tabs[current_tab]:
                st.subheader("Architecture Diagram")
                st.image(results["diagrams"])
                st.sidebar.success("✅ Architecture Diagram Generated")
            
            # Show Jira update info if applicable
            if update_jira and "jira" in results:
                st.sidebar.success(f"✅ Jira tickets created: {results['jira']}")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.sidebar.error("❌ Process failed")