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
        instructions="""You are a requirement analysis expert. When given a requirement, application type, and non-functional requirements:
        1. Expand it into detailed functional requirements, considering:
           - If Web Application: UI/UX, frontend components, user interactions
           - If Web Service: API endpoints, data formats, integration points
        2. Ensure all requirements align with provided NFRs, specifically addressing:
           - Performance requirements
           - Security requirements
           - Scalability requirements
           - Any other specified NFRs
        3. List any assumptions made
        4. Identify potential edge cases
        5. Suggest acceptance criteria that includes NFR validation""",
    )
    
    validator = Agent(
        name="Requirement Validator",
        instructions="""You are a senior technical reviewer. Review the elaborated requirements and:
        1. Identify any gaps or inconsistencies
        2. Check if all edge cases are covered
        3. Validate if the acceptance criteria are testable
        4. Specifically verify that all NFRs are properly addressed:
           - Performance metrics are measurable
           - Security requirements are concrete
           - Other NFRs have clear validation criteria
        5. Provide specific improvement suggestions""",
    )

    finalizer = Agent(
        name="Requirement Finalizer",
        instructions="""You are a senior business analyst who creates comprehensive UML-style requirements specifications. 
        Given the elaborated requirements and validation feedback, create a detailed specification following this structure:

        1. System Overview
           - Purpose and Scope
           - System Context
           - Target Users/Actors

        2. Use Cases (for each major functionality):
           Use Case: [UC-ID] [Name]
           Description: [Brief description]
           Primary Actor: [Main actor]
           Secondary Actors: [Supporting actors if any]
           Preconditions: [List all preconditions]
           Postconditions: [List all postconditions]
           
           Main Flow:
           1. [Step-by-step actions]
           2. [Include user and system actions]
           
           Alternative Flows:
           A1. [Alternative scenario]
           A2. [Another alternative]
           
           Exception Flows:
           E1. [Error condition and handling]
           E2. [Another error scenario]
           
           Business Rules: [Related business rules]
           
           Non-Functional Requirements:
           - Performance criteria
           - Security requirements
           - Other specific NFRs

           Acceptance Criteria:
           - [Specific, measurable criteria]
           - [Including NFR validation]

        3. Data Requirements
           - Data Entities
           - Data Validation Rules
           - Data Privacy Requirements

        4. Interface Requirements
           - User Interface
           - API Specifications
           - External System Interfaces

        5. Technical Constraints
           - System Requirements
           - Performance Bounds
           - Security Controls

        6. Traceability Matrix
           - Requirements to Use Cases
           - Requirements to Test Cases
           - NFR Implementation Mapping

        Format your response using Markdown for better readability.
        Include diagrams descriptions where applicable (activity, sequence).
        Ensure all requirements are testable and measurable."""
    )

    test_generator = Agent(
        name="Test Case Generator",
        instructions="""You are a QA expert who creates comprehensive test cases. Based on the final requirements:
        1. Create detailed test cases covering:
           - Happy path scenarios
           - Edge cases
           - Error scenarios
           - Security considerations
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
        maintainable code across Python, Java, and Kotlin. You're known for creating robust 
        web applications that strictly adhere to requirements while maintaining high test coverage.""",
        tools=["Web Development", "Test-Driven Development", "API Design", "Database Design"],
        verbose=True,
        allow_delegation=False,
        instructions="""
        Follow this process strictly when generating code:

        1. Requirements Analysis:
           - Review and understand all validated requirements including NFRs
           - Implement specific measures to meet performance requirements
           - Add security controls as specified in NFRs
           - Include monitoring and metrics collection for NFR validation

        2. Test Cases Implementation:
           - Create unit tests based on provided test scenarios
           - Include test cases for both happy path and edge cases
           - Use appropriate testing framework for the selected language:
             * Python: pytest
             * Java: JUnit
             * Kotlin: JUnit/KotlinTest

        3. Web Application Implementation:
           - Create a well-structured web application following MVC/MVVM pattern
           - Implement all required endpoints/routes
           - Include proper input validation and error handling
           - Add security measures (XSS protection, CSRF tokens, input sanitization)
           - Implement proper session management if required
           - Add database integration where needed
           - Include clear documentation and API endpoints description

        4. Code Organization:
           - Organize code into logical components/modules
           - Follow language-specific best practices and conventions
           - Include necessary dependencies and setup instructions
           - Provide clear file structure
           - Add comprehensive comments explaining complex logic

        5. Quality Assurance:
           - Ensure all test cases are implemented
           - Verify code meets security best practices
           - Include error handling for edge cases
           - Add logging for important operations
           - Follow SOLID principles

        Output Format:
        1. First output test cases implementation
        2. Then output the main application code
        3. Include setup instructions and dependencies
        4. Add API documentation if applicable
        5. Explain any important implementation decisions

        Remember: The code must be complete enough to run and test, with all necessary imports and configurations.
        """
    )

    code_reviewer = Agent(
        name="Code Reviewer",
        instructions="""You are a senior software engineer specializing in Python code review. Given the requirements, NFRs, and generated code:
        1. Review the code for:
           - Compliance with functional requirements
           - Adherence to specified NFRs
           - Code quality and best practices
           - Performance against specified metrics
           - Security compliance with requirements
           - Test coverage including NFR validation
        
        2. Provide detailed feedback on:
           - NFR compliance issues
           - Performance optimization needs
           - Security implementation gaps
           - Scalability concerns
           - Monitoring and metrics coverage
        
        3. Format your response as:
           ## Requirements Compliance
           - List of met/unmet functional requirements
           - List of met/unmet NFRs
           
           ## Performance & Scalability
           - Analysis of performance requirements
           - Scalability implementation review
           
           ## Security Review
           - Security requirements compliance
           - Security implementation quality
           
           ## Recommended Changes
           - Specific code changes with examples""",
    )

    nfr_elaborator = Agent(
        name="NFR Elaborator",
        instructions="""You are a non-functional requirements specialist. When given NFR specifications:
        1. Analyze and elaborate each NFR category:
           - Performance requirements (response times, throughput, etc.)
           - Security requirements (authentication, encryption, etc.)
           - Scalability requirements (load handling, concurrent users)
           - Reliability requirements (uptime, fault tolerance)
           - Maintainability requirements
           - Other specified NFRs
        2. For each NFR:
           - Define specific, measurable criteria
           - Specify validation methods
           - Identify implementation requirements
           - List monitoring requirements
        3. Integrate NFRs with functional requirements:
           - Identify dependencies
           - Highlight conflicts
           - Suggest implementation priorities""",
    )
    
    return elaborator, validator, finalizer, test_generator, code_generator, code_reviewer, nfr_elaborator

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
st.write("Enter a requirement and get detailed analysis")

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
    
    # Add file uploader for NFRs
    st.sidebar.subheader("Non-Functional Requirements")
    nfr_file = st.file_uploader("Upload NFR document (optional)", type=['txt', 'md', 'pdf'])
    
    # Read NFR file content if uploaded
    nfr_content = ""
    if nfr_file is not None:
        if nfr_file.type == "application/pdf":
            pdf_reader = PdfReader(nfr_file)
            nfr_content = ""
            for page in pdf_reader.pages:
                nfr_content += page.extract_text()
        else:
            nfr_content = nfr_file.getvalue().decode("utf-8")
        st.sidebar.success("NFR file loaded successfully!")

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

# Define tab names
TAB_NAMES = ["Requirements", "Validation", "Final Specs", "Test Cases", "Code", "Review"]

if st.button("Analyze"):
    if requirement:
        try:
            # Create agents first
            elaborator, validator, finalizer, test_generator, code_generator, code_reviewer, nfr_elaborator = create_agents()
            
            # Include NFRs in the initial context if provided
            nfr_context = f"\nNon-Functional Requirements:\n{nfr_content}" if nfr_content else ""
            initial_context = f"Requirement: {requirement}\nApplication Type: {app_type}{nfr_context}"

            # Create tabs
            tabs = st.tabs([f"{name}" for name in TAB_NAMES])
            
            # Elaboration
            with tabs[0]:
                st.subheader("Requirements Analysis")
                handle_chunk, elaboration_content = stream_content(tabs[0])
                elaboration_stream = client.run(
                    agent=elaborator,
                    messages=[{"role": "user", "content": initial_context}],
                    stream=True
                )
                for chunk in elaboration_stream:
                    handle_chunk(chunk)
                elaboration = ''.join(filter(None, elaboration_content))
                
                # Process NFRs if available
                nfr_elaboration = ""
                if nfr_content:
                    nfr_handle_chunk, nfr_content_processed = stream_content(tabs[0])
                    nfr_stream = client.run(
                        agent=nfr_elaborator,
                        messages=[{"role": "user", "content": nfr_content}],
                        stream=True
                    )
                    for chunk in nfr_stream:
                        nfr_handle_chunk(chunk)
                    nfr_elaboration = ''.join(filter(None, nfr_content_processed))
                    
                    # Update elaboration to include NFRs
                    elaboration = f"{elaboration}\n\n{nfr_elaboration}"
                
                st.sidebar.success("✅ Requirements Analysis Complete")

            # Validation
            with tabs[1]:
                st.subheader("Validation Review")
                handle_chunk, validation_content = stream_content(tabs[1])
                validation_stream = client.run(
                    agent=validator,
                    messages=[{"role": "user", "content": elaboration}],
                    stream=True
                )
                for chunk in validation_stream:
                    handle_chunk(chunk)
                validation = ''.join(filter(None, validation_content))
                st.sidebar.success("✅ Validation Complete")

            # Final requirements
            final_context = f"""
            Original Requirement:
            {requirement}

            Elaborated Requirements:
            {elaboration}

            Validation Feedback:
            {validation}
            """

            with tabs[2]:
                st.subheader("Final Requirements")
                handle_chunk, final_content = stream_content(tabs[2])
                final_stream = client.run(
                    agent=finalizer,
                    messages=[{"role": "user", "content": final_context}],
                    stream=True
                )
                for chunk in final_stream:
                    handle_chunk(chunk)
                final_requirements = ''.join(filter(None, final_content))
                st.sidebar.success("✅ Final Requirements Complete")

            # Generate test cases with streaming
            test_context = f"""
            Original Requirement: {requirement}
            Final Requirements: {final_requirements}
            Programming Language: {programming_language}
            """

            with tabs[3]:
                st.subheader("Test Cases")
                handle_chunk, test_content = stream_content(tabs[3])
                test_stream = client.run(
                    agent=test_generator,
                    messages=[{"role": "user", "content": test_context}],
                    stream=True
                )
                for chunk in test_stream:
                    handle_chunk(chunk)
                test_cases = ''.join(filter(None, test_content))
                st.sidebar.success("✅ Test Cases Generated")

            # Generate code with streaming
            with tabs[4]:
                st.subheader("Generated Code")
                handle_chunk, code_content = stream_content(tabs[4])
                
                # Modify the prompt to include app type
                code_prompt = f"""Based on the specifications, generate code in {programming_language}.
                Application Type: {app_type}
                
                If Web Application:
                - Include frontend code (HTML/CSS if needed)
                - Include necessary routing
                - Include user interface components
                
                If Web Service:
                - Focus on API endpoints
                - Include request/response handling
                - Include data models
                
                Previous specifications:
                {final_requirements}
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

            # Code review with streaming
            review_context = f"""
            Requirements: {final_requirements}
            Generated Code: {generated_code}
            Test Cases: {test_cases}
            """

            with tabs[5]:
                st.subheader("Code Review Analysis")
                handle_chunk, review_content = stream_content(tabs[5])
                review_stream = client.run(
                    agent=code_reviewer,
                    messages=[{"role": "user", "content": review_context}],
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