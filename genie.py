from dotenv import load_dotenv
import os
import json
from jira_service import JiraService
from agents.elaborator_agent import ElaboratorAgent
from agents.validator_agent import ValidatorAgent
from agents.finalizer_agent import FinalizerAgent
from agents.test_generator_agent import TestGeneratorAgent
from agents.code_generator_agent import CodeGeneratorAgent
from agents.code_reviewer_agent import CodeReviewerAgent
from agents.jira_agent import JiraAgent

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
def create_agents():
    elaborator = ElaboratorAgent().get_agent()
    validator = ValidatorAgent().get_agent()
    finalizer = FinalizerAgent().get_agent()
    test_generator = TestGeneratorAgent().get_agent()
    code_generator = CodeGeneratorAgent().get_agent()
    code_reviewer = CodeReviewerAgent().get_agent()
    jira_creator = JiraAgent().get_agent()
    
    return elaborator, validator, finalizer, test_generator, code_generator, code_reviewer, jira_creator

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
            if isinstance(chunk, dict):
                if "content" in chunk and chunk["content"]:
                    full_response.append(chunk["content"])
            elif isinstance(chunk, str) and chunk:
                full_response.append(chunk)
            
            if full_response:
                message_placeholder.markdown(''.join(filter(None, full_response)) + "▌")
        except Exception as e:
            st.error(f"Streaming error: {str(e)}")
    
    return handle_chunk, full_response

# Define dynamic tab names based on NFR presence
def get_tab_names(has_nfrs):
    base_tabs = ["Requirements"]
    if has_nfrs:
        base_tabs.append("NFR Analysis")
    return base_tabs + ["Validation", "Final Specs", "Test Cases", "Code", "Review"]

if st.button("Analyze"):
    if requirement:
        try:
            # Create agents
            elaborator, validator, finalizer, test_generator, code_generator, code_reviewer, jira_creator = create_agents()
            
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
                initial_prompt = f"Requirement: {requirement}\nApplication Type: {app_type}"
                elaboration_stream = client.run(
                    agent=elaborator,
                    messages=[{"role": "user", "content": initial_prompt}],
                    stream=True
                )
                for chunk in elaboration_stream:
                    handle_chunk(chunk)
                elaboration = ''.join(filter(None, elaboration_content))
                st.sidebar.success("✅ Functional Requirements Analysis Complete")
            current_tab += 1

            # NFR Analysis (only if NFRs are provided)
            nfr_analysis = ""
            if has_nfrs:
                with tabs[current_tab]:
                    st.subheader("Non-Functional Requirements Analysis")
                    handle_chunk, nfr_analysis_content = stream_content(tabs[current_tab])
                    nfr_prompt = ElaboratorAgent.get_nfr_analysis_prompt(nfr_content, app_type)
                    
                    nfr_analysis_stream = client.run(
                        agent=elaborator,
                        messages=[{"role": "user", "content": nfr_prompt}],
                        stream=True
                    )
                    for chunk in nfr_analysis_stream:
                        handle_chunk(chunk)
                    nfr_analysis = ''.join(filter(None, nfr_analysis_content))
                    st.sidebar.success("✅ NFR Analysis Complete")
                current_tab += 1

            # Validation
            with tabs[current_tab]:
                st.subheader("Validation Review")
                handle_chunk, validation_content = stream_content(tabs[current_tab])
                
                nfr_section = f"\nNon-Functional Requirements Analysis:\n{nfr_analysis}" if has_nfrs else ""
                validation_prompt = f"""
                Functional Requirements:
                {elaboration}
                {nfr_section}
                
                Validate both functional and non-functional requirements, considering:
                1. Completeness and clarity
                2. Consistency between functional and non-functional requirements
                3. Feasibility of implementation
                4. Testability of all requirements
                """
                
                validation_stream = client.run(
                    agent=validator,
                    messages=[{"role": "user", "content": validation_prompt}],
                    stream=True
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
                
                # Modified NFR section for final requirements
                nfr_section = ""
                if has_nfrs:
                    nfr_section = f"""
                    ORIGINAL NFR DOCUMENT:
                    {nfr_content}

                    NFR ANALYSIS:
                    {nfr_analysis}
                    """
                
                final_prompt = f"""
                Review and incorporate ALL of the following inputs to create the final requirements specification:

                ORIGINAL REQUIREMENT:
                {requirement}

                ELABORATED REQUIREMENTS:
                {elaboration}

                VALIDATION FEEDBACK:
                {validation}

                {nfr_section}

                Based on ALL the above analyses, create a comprehensive final requirements document that incorporates and refines these insights. Organize the document as follows:

                A. EXECUTIVE SUMMARY
                - Brief overview of the requirement
                - Key objectives and scope derived from the elaborated requirements
                - Primary stakeholders identified in the analysis
                - Summary of key NFRs and their impact

                B. USE CASES
                1. Create a comprehensive use case diagram in PlantUML format showing all core and supporting use cases identified in the elaborated requirements.

                2. IMPORTANT: You MUST provide complete detailed documentation for EVERY SINGLE use case shown in the diagram. For each and every use case, without exception, provide this complete documentation:
                   - Use Case Name
                   - Actors (all stakeholders involved)
                   - Preconditions (complete list)
                   - Main Flow (detailed step-by-step)
                   - Alternate Flows (all variations and edge cases from elaboration)
                   - Exception Flows (all error scenarios based on validation feedback)
                   - Postconditions (all end states)
                   - NFR Considerations (specific NFR requirements for this use case, referencing the NFR analysis)
                   - Business Rules (any rules or constraints specific to this use case)
                   - Related Requirements (trace to specific elaborated requirements)
                   - NFR Compliance Requirements (detailed NFR requirements specific to this use case)

                C. FUNCTIONAL REQUIREMENTS
                - Map each elaborated requirement to corresponding use cases
                - Core functionality (from elaborated requirements)
                - User interactions (from elaborated requirements)
                - System behaviors (incorporating validation feedback)
                - Data handling requirements
                - Integration points

                D. NON-FUNCTIONAL REQUIREMENTS
                For each NFR identified in the analysis:
                1. Detailed Specification
                   - Category and description
                   - Specific requirements
                   - Measurement criteria
                   - Implementation guidelines
                   - Impact on functional requirements
                   - Validation methods

                2. Cross-cutting Concerns
                   - Dependencies between NFRs
                   - Impact on architecture
                   - Implementation priorities
                   - Risk factors

                3. Compliance Matrix
                   - Map each NFR to affected use cases
                   - Success criteria for each NFR
                   - Verification methods
                   - Testing requirements

                E. IMPLEMENTATION CONSIDERATIONS
                - Technical approach addressing both functional and NFR requirements
                - Integration strategy considering NFR constraints
                - Critical success factors
                - Risk mitigation strategies for identified concerns
                - NFR implementation priorities and dependencies

                F. ACCEPTANCE CRITERIA
                - Detailed criteria for each use case
                - NFR-specific acceptance criteria
                - Testing and validation requirements
                - Performance benchmarks
                - Security requirements
                - Other NFR validation criteria

                G. ASSUMPTIONS AND CONSTRAINTS
                - Document all assumptions
                - Technical constraints
                - NFR-related constraints
                - Dependencies
                - Risk factors

                Ensure that:
                1. Every use case is fully detailed with no summarization
                2. All NFRs are explicitly addressed in relevant use cases
                3. NFR requirements are integrated throughout all sections
                4. Clear traceability exists between requirements, NFRs, and use cases
                5. No content from the NFR analysis is lost or summarized
                """
                
                final_stream = client.run(
                    agent=finalizer,
                    messages=[{"role": "user", "content": final_prompt}],
                    stream=True
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
                
                nfr_test_section = f"\nNon-Functional Requirements:\n{nfr_analysis}" if has_nfrs else ""
                test_prompt = f"""
                Original Requirement: {requirement}
                Final Requirements: {final_requirements}
                {nfr_test_section}
                Programming Language: {programming_language}
                """
                
                test_stream = client.run(
                    agent=test_generator,
                    messages=[{"role": "user", "content": test_prompt}],
                    stream=True
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
                
                nfr_code_section = f"\nNon-Functional Requirements:\n{nfr_analysis}" if has_nfrs else ""
                code_prompt = f"""
                Based on the specifications, generate code in {programming_language}.
                Application Type: {app_type}
                
                Functional Requirements:
                {final_requirements}
                {nfr_code_section}
                
                If Web Application:
                - Include frontend code (HTML/CSS if needed)
                - Include necessary routing
                - Include user interface components
                
                If Web Service:
                - Focus on API endpoints
                - Include request/response handling
                - Include data models
                """
                
                code_stream = client.run(
                    agent=code_generator,
                    messages=[{"role": "user", "content": code_prompt}],
                    stream=True
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
                
                nfr_review_section = f"\nNon-Functional Requirements:\n{nfr_analysis}" if has_nfrs else ""
                review_prompt = f"""
                Requirements: {final_requirements}
                {nfr_review_section}
                Generated Code: {generated_code}
                Test Cases: {test_cases}
                """
                
                review_stream = client.run(
                    agent=code_reviewer,
                    messages=[{"role": "user", "content": review_prompt}],
                    stream=True
                )
                for chunk in review_stream:
                    handle_chunk(chunk)
                st.sidebar.success("✅ Code Review Complete")

            # Create Jira tickets if enabled
            if update_jira and jira_project:
                with st.spinner("Creating Jira tickets..."):
                    try:
                        # Validate Jira configuration first
                        jira_service = JiraService()
                        jira_service.test_connection()
                        jira_service.validate_project(jira_project)
                        
                        # Create a new section for Jira tickets
                        st.subheader("Jira Tickets Created")
                        handle_chunk, jira_content = stream_content(st)
                        
                        jira_prompt = f"""IMPORTANT: Respond ONLY with valid JSON. Do not include any other text.

                        Create Jira tickets for the following requirements:
                        
                        Original Requirement: {requirement}
                        
                        Elaborated Requirements: {elaboration}
                        
                        Final Requirements: {final_requirements}
                        
                        Test Cases: {test_cases}
                        
                        NFR Analysis: {nfr_analysis if has_nfrs else "No NFRs provided"}
                        
                        Project Key: {jira_project}
                        Component: {jira_component}

                        Remember:
                        1. Response must be ONLY valid JSON
                        2. Follow the exact structure provided
                        3. No text before or after the JSON
                        4. All JSON strings must be properly escaped
                        """
                        
                        # Run the Jira agent to get the stream
                        jira_stream = client.run(
                            agent=jira_creator,
                            messages=[{"role": "user", "content": jira_prompt}],
                            stream=True
                        )
                        
                        # Collect all chunks
                        full_response = []
                        for chunk in jira_stream:
                            handle_chunk(chunk)
                            if isinstance(chunk, dict) and "content" in chunk:
                                full_response.append(chunk["content"])
                            elif isinstance(chunk, str):
                                full_response.append(chunk)
                        
                        # Join and clean the response
                        json_str = ''.join(filter(None, full_response))
                        
                        # Try to find JSON in the response
                        try:
                            # Remove any text before the first {
                            json_start = json_str.find('{')
                            if json_start != -1:
                                json_str = json_str[json_start:]
                            
                            # Remove any text after the last }
                            json_end = json_str.rfind('}')
                            if json_end != -1:
                                json_str = json_str[:json_end + 1]
                            
                            # Debug output
                            st.text("Attempting to parse JSON:")
                            st.code(json_str, language='json')
                            
                            # Parse JSON
                            jira_tickets = json.loads(json_str)
                            
                            # Validate JSON structure
                            required_keys = ["epic", "stories", "tasks", "tests"]
                            missing_keys = [key for key in required_keys if key not in jira_tickets]
                            if missing_keys:
                                raise ValueError(f"Missing required keys in JSON: {missing_keys}")
                            
                            # Create tickets in Jira
                            with st.spinner("Creating tickets in Jira..."):
                                # Create epic
                                epic_key = jira_service.create_epic(
                                    jira_project,
                                    jira_tickets["epic"]["summary"],
                                    jira_tickets["epic"]["description"]
                                )
                                st.success(f"Created Epic: {epic_key}")
                                
                                # Create stories
                                for story in jira_tickets["stories"]:
                                    story_key = jira_service.create_story(
                                        jira_project,
                                        story["summary"],
                                        story["description"],
                                        epic_key,
                                        story.get("story_points")
                                    )
                                    st.success(f"Created Story: {story_key}")
                                    
                                    # Create tasks for this story
                                    for task in jira_tickets["tasks"]:
                                        task_key = jira_service.create_task(
                                            jira_project,
                                            task["summary"],
                                            task["description"],
                                            story_key
                                        )
                                        st.success(f"Created Task: {task_key}")
                                    
                                    # Create test cases for this story
                                    for test in jira_tickets["tests"]:
                                        test_key = jira_service.create_task(
                                            jira_project,
                                            test["summary"],
                                            test["description"],
                                            story_key
                                        )
                                        st.success(f"Created Test: {test_key}")
                                
                                st.success(f"Successfully created all Jira tickets under Epic: {epic_key}")
                                
                        except json.JSONDecodeError as e:
                            st.error(f"Invalid JSON format: {str(e)}")
                            st.error("Raw response received:")
                            st.code(json_str)
                            raise Exception("Invalid JSON response from Jira agent")
                        except ValueError as e:
                            st.error(f"Invalid JSON structure: {str(e)}")
                            st.error("JSON received:")
                            st.code(json_str)
                            raise Exception(f"Invalid JSON structure: {str(e)}")
                            
                    except ValueError as e:
                        st.error(f"Jira Configuration Error: {str(e)}")
                        st.error("Please check your Jira settings in the .env file")
                    except ConnectionError as e:
                        st.error(f"Jira Connection Error: {str(e)}")
                        st.error("Please verify your Jira URL and credentials")
                    except Exception as e:
                        st.error(f"Error creating Jira tickets: {str(e)}")
                        st.error("Please check the error message and try again")

            # Show completion message
            st.sidebar.success("✨ Analysis Complete!")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.sidebar.error("❌ Process failed")