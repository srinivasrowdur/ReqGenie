from dotenv import load_dotenv
import os

# Load environment variables before any other imports
load_dotenv()

import streamlit as st
from swarm import Swarm, Agent
from streamlit_extras.stateful_button import button
import time
from PyPDF2 import PdfReader
from agent_instructions import (
    ELABORATOR_INSTRUCTIONS,
    VALIDATOR_INSTRUCTIONS,
    FINALIZER_INSTRUCTIONS,
    TEST_GENERATOR_INSTRUCTIONS,
    CODE_GENERATOR_INSTRUCTIONS,
    CODE_REVIEWER_INSTRUCTIONS,
    NFR_ANALYSIS_PROMPT_TEMPLATE
)

# Initialize Swarm client
client = Swarm()

# Initialize agents
def create_agents():
    elaborator = Agent(
        name="Requirement Elaborator",
        instructions=ELABORATOR_INSTRUCTIONS,
    )
    
    validator = Agent(
        name="Requirement Validator",
        instructions=VALIDATOR_INSTRUCTIONS,
    )

    finalizer = Agent(
        name="Requirement Finalizer",
        instructions=FINALIZER_INSTRUCTIONS,
    )

    test_generator = Agent(
        name="Test Case Generator",
        instructions=TEST_GENERATOR_INSTRUCTIONS,
    )

    code_generator = Agent(
        role=CODE_GENERATOR_INSTRUCTIONS["role"],
        goal=CODE_GENERATOR_INSTRUCTIONS["goal"],
        backstory=CODE_GENERATOR_INSTRUCTIONS["backstory"],
        instructions=CODE_GENERATOR_INSTRUCTIONS["instructions"],
    )

    code_reviewer = Agent(
        name="Code Reviewer",
        instructions=CODE_REVIEWER_INSTRUCTIONS,
    )
    
    return elaborator, validator, finalizer, test_generator, code_generator, code_reviewer

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
            elaborator, validator, finalizer, test_generator, code_generator, code_reviewer = create_agents()
            
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
                    nfr_prompt = NFR_ANALYSIS_PROMPT_TEMPLATE.format(
                        nfr_content=nfr_content,
                        app_type=app_type
                    )
                    
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

                    DETAILED NFR ANALYSIS:
                    {nfr_analysis}

                    IMPORTANT: Each NFR category identified in the analysis must be explicitly addressed in all relevant sections below.
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
                1. First create a comprehensive use case diagram in PlantUML format.

                2. CRITICAL: For EACH use case in the diagram, provide exhaustive documentation including NFR considerations for EVERY identified NFR category:

                   Use Case Documentation Template:
                   a) Basic Information:
                      - Use Case Name
                      - Actors
                      - Description
                   
                   b) Flow Details:
                      - Preconditions
                      - Main Flow (step-by-step)
                      - Alternate Flows
                      - Exception Flows
                      - Postconditions
                   
                   c) NFR Category Implementation (MUST cover EACH identified NFR category):
                      For each NFR category identified in the analysis:
                      - Specific Requirements for this category in this use case
                      - Implementation Guidelines
                      - Success Criteria
                      - Validation Method
                      - Impact on Use Case Flow
                   
                   d) Business Rules & Constraints:
                      - Functional Rules
                      - NFR-specific Rules per Category
                      - Technical Constraints
                   
                   e) Traceability:
                      - Related Functional Requirements
                      - Related NFR Categories
                      - Validation Points

                C. FUNCTIONAL REQUIREMENTS
                - Map each elaborated requirement to corresponding use cases
                - Core functionality (from elaborated requirements)
                - User interactions (from elaborated requirements)
                - System behaviors (incorporating validation feedback)
                - Data handling requirements
                - Integration points
                - Impact of each NFR category on functional requirements
                - NFR category-specific constraints on functionality
                - Cross-cutting concerns per NFR category

                D. NON-FUNCTIONAL REQUIREMENTS
                MUST provide separate detailed sections for EACH identified NFR category:

                For each NFR Category:
                1. Category-Specific Requirements
                   - Detailed specifications
                   - Quantifiable metrics
                   - Implementation guidelines
                   - Validation criteria

                2. Use Case Impact Matrix
                   - How this NFR category affects each use case
                   - Specific requirements per use case
                   - Implementation priorities
                   - Success criteria

                3. Integration Considerations
                   - Impact on other NFR categories
                   - Technical constraints
                   - Implementation dependencies
                   - Risk factors

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

                CRITICAL REQUIREMENTS:
                1. Every NFR category must be explicitly addressed in each use case
                2. Each use case must detail how it implements every NFR category
                3. Provide clear traceability between NFR categories and use cases
                4. Include category-specific metrics and validation criteria
                5. Document category interactions and dependencies
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

            # Show completion message
            st.sidebar.success("✨ Analysis Complete!")
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.sidebar.error("❌ Process failed")