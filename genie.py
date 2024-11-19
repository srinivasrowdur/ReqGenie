from dotenv import load_dotenv
import os

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
    elaborator = Agent(
        name="Requirement Elaborator",
        instructions="""You are a requirement analysis expert. When given a single line requirement and application type:
        1. Expand it into detailed functional requirements, considering:
           - If Web Application: UI/UX, frontend components, user interactions
           - If Web Service: API endpoints, data formats, integration points
        2. Consider provided Non-Functional Requirements (NFRs)
        3. List any assumptions made
        4. Identify potential edge cases
        5. Suggest acceptance criteria""",
    )
    
    validator = Agent(
        name="Requirement Validator",
        instructions="""You are a senior technical reviewer. Review the elaborated requirements and:
        1. Identify any gaps or inconsistencies
        2. Check if all edge cases are covered
        3. Validate if the acceptance criteria are testable
        4. Verify compliance with Non-Functional Requirements (NFRs)
        5. Provide specific improvement suggestions""",
    )

    finalizer = Agent(
        name="Requirement Finalizer",
        instructions="""You are a senior business analyst who finalizes requirements. Given the elaborated requirements and validation feedback:
        1. Incorporate the validator's feedback
        2. Refine and consolidate the requirements
        3. Present a clear, final set of requirements in a structured format
        4. Include:
           - Final functional requirements
           - Non-Functional Requirements compliance
           - Refined acceptance criteria
           - Key assumptions
           - Addressed edge cases""",
    )

    test_generator = Agent(
        name="Test Case Generator",
        instructions="""You are a QA expert who creates comprehensive test cases. Based on the final requirements:
        1. Create detailed test cases covering:
           - Happy path scenarios
           - Edge cases
           - Error scenarios
           - Security considerations
           - Non-Functional Requirements validation
        2. For each test case, specify:
           - Test ID
           - Description
           - Preconditions
           - Test steps
           - Expected results
           - Test type (Functional/Non-functional)
        3. Prioritize test cases (High/Medium/Low)""",
    )

    code_generator = Agent(
        role="Full Stack Web Developer",
        goal="Generate production-ready web application code with comprehensive test coverage",
        backstory="""You are a senior full-stack developer specializing in web applications. 
        You have extensive experience in test-driven development (TDD) and writing clean, 
        maintainable code across Python, Java, and Kotlin.""",
        instructions="""
        Follow this process strictly when generating code:

        1. Requirements Analysis:
           - Review and understand all validated requirements
           - Consider Non-Functional Requirements
           - Identify core functionality and technical constraints
           - Plan the application architecture based on requirements

        2. Test Cases Implementation:
           - Create unit tests based on provided test scenarios
           - Include test cases for both happy path and edge cases
           - Include NFR validation tests
           - Use appropriate testing framework for the selected language

        3. Web Application Implementation:
           - Create a well-structured web application following MVC/MVVM pattern
           - Implement all required endpoints/routes
           - Include proper input validation and error handling
           - Implement NFR requirements (performance, security, etc.)
           - Add security measures
           - Include clear documentation
        """
    )

    code_reviewer = Agent(
        name="Code Reviewer",
        instructions="""You are a senior software engineer specializing in code review. Given the requirements and generated code:
        1. Review the code for:
           - Compliance with functional requirements
           - Compliance with Non-Functional Requirements
           - Code quality and best practices
           - Security vulnerabilities
           - Performance considerations
           - Test coverage
        
        2. Provide detailed feedback on:
           - Missing functionality
           - NFR implementation
           - Code structure improvements
           - Security recommendations
           - Performance optimizations
        """
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
                    nfr_prompt = f"""Analyze these Non-Functional Requirements for a {app_type}:
                    
                    NFRs:
                    {nfr_content}
                    
                    Provide:
                    1. Detailed analysis of each NFR
                    2. Implementation considerations
                    3. Potential challenges
                    4. Measurement criteria"""
                    
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
                
                nfr_final_section = f"\nNon-Functional Requirements Analysis:\n{nfr_analysis}" if has_nfrs else ""
                final_prompt = f"""
                Review and incorporate the following analyses to create the final requirements specification:

                ORIGINAL REQUIREMENT:
                {requirement}

                ELABORATED REQUIREMENTS:
                {elaboration}

                VALIDATION FEEDBACK:
                {validation}
                {nfr_final_section}

                Based on the above analyses, create a comprehensive final requirements document that builds upon and refines these insights. Organize the document as follows:

                A. EXECUTIVE SUMMARY
                - Brief overview of the requirement
                - Key objectives and scope derived from the elaborated requirements
                - Primary stakeholders identified in the analysis

                B. USE CASES
                1. First, create a comprehensive use case diagram in PlantUML format showing ALL core and supporting use cases identified in the elaborated requirements.

                2. IMPORTANT: You MUST provide complete detailed documentation for EVERY SINGLE use case shown in the diagram. Do not summarize, abbreviate, or skip any use cases. Do not use phrases like "would be detailed similarly" or "etc."

                For each and every use case, without exception, provide this complete documentation:
                   - Use Case Name
                   - Actors (all stakeholders involved)
                   - Preconditions (complete list)
                   - Main Flow (detailed step-by-step)
                   - Alternate Flows (all variations and edge cases from elaboration)
                   - Exception Flows (all error scenarios based on validation feedback)
                   - Postconditions (all end states)
                   - NFR Considerations (specific NFR requirements for this use case)
                   - Business Rules (any rules or constraints specific to this use case)
                   - Related Requirements (trace to specific elaborated requirements)

                3. After documenting each use case, provide a traceability matrix showing how each use case maps to:
                   - Original requirements
                   - Elaborated requirements
                   - Validation points
                   - NFRs (if applicable)

                C. FUNCTIONAL REQUIREMENTS
                - Map each elaborated requirement to corresponding use cases
                - Core functionality (from elaborated requirements)
                - User interactions (from elaborated requirements)
                - System behaviors (incorporating validation feedback)
                - Data handling requirements
                - Integration points

                D. NON-FUNCTIONAL REQUIREMENTS
                - Include and categorize all NFRs from the analysis
                - For each NFR category:
                    * Detailed requirements
                    * Success criteria
                    * Measurement methods
                    * Implementation considerations
                - Address cross-cutting concerns identified in validation
                - Document NFR dependencies

                E. IMPLEMENTATION CONSIDERATIONS
                - Technical approach addressing validation feedback
                - Integration strategy
                - Critical success factors
                - Risk mitigation strategies for identified concerns

                F. ACCEPTANCE CRITERIA
                - Map acceptance criteria to specific use cases
                - Include acceptance criteria from elaborated requirements
                - Address validation concerns in criteria
                - Include NFR validation criteria
                - Testing considerations from validation feedback

                G. ASSUMPTIONS AND CONSTRAINTS
                - Document assumptions from elaborated requirements
                - Include constraints identified in validation
                - Technical environment considerations
                - Risk factors highlighted in validation

                Example PlantUML format:
                ```plantuml
                @startuml
                left to right direction
                actor "User" as user
                rectangle "System" {{
                  usecase "Main Function" as UC1
                  usecase "Secondary Function" as UC2
                  UC1 <-- user
                  UC1 <.. UC2 : extends
                }}
                @enduml
                ```

                Ensure that:
                1. All sections maintain consistency with the elaborated requirements
                2. Validation feedback is properly addressed and incorporated
                3. Each use case traces back to specific elaborated requirements
                4. All identified edge cases and concerns are covered
                5. The final document builds upon rather than replaces the previous analyses

                Additional Instructions:
                1. Do not use placeholder text or references to similar patterns
                2. Every use case shown in the PlantUML diagram must have its own complete documentation section
                3. Do not abbreviate or combine similar use cases
                4. Ensure each use case has unique, specific details derived from the requirements
                5. The use case documentation must be exhaustive and implementation-ready
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