import streamlit as st
from dotenv import load_dotenv
import os
from swarm import Swarm, Agent

# Load environment variables
load_dotenv()

# Initialize Swarm client
client = Swarm()

# Initialize agents
def create_agents():
    elaborator = Agent(
        name="Requirement Elaborator",
        instructions="""You are a requirement analysis expert. When given a single line requirement:
        1. Expand it into detailed functional requirements
        2. List any assumptions made
        3. Identify potential edge cases
        4. Suggest acceptance criteria""",
    )
    
    validator = Agent(
        name="Requirement Validator",
        instructions="""You are a senior technical reviewer. Review the elaborated requirements and:
        1. Identify any gaps or inconsistencies
        2. Check if all edge cases are covered
        3. Validate if the acceptance criteria are testable
        4. Provide specific improvement suggestions""",
    )

    finalizer = Agent(
        name="Requirement Finalizer",
        instructions="""You are a senior business analyst who finalizes requirements. Given the elaborated requirements and validation feedback:
        1. Incorporate the validator's feedback
        2. Refine and consolidate the requirements
        3. Present a clear, final set of requirements in a structured format
        4. Include:
           - Final functional requirements
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
        name="Code Generator",
        instructions="""You are a Python expert who specializes in building multi-agent LLM systems using LangGraph, Streamlit, and LangChain. Based on the final requirements:
        1. Generate production-ready Python code that implements a supervisor-based multi-agent system using:
           - LangGraph for creating and managing the multi-agent workflow
           - Streamlit for the user interface
           - LangChain for LLM interactions
           - OpenAI's models as the base LLM
        
        2. Implement the following architectural components:
           - A supervisor agent that coordinates the workflow between other agents
           - Individual specialized agents as worker nodes
           - State management using LangGraph's StateGraph
           - Proper message passing between agents
           - Clear control flow using graph edges
        
        3. Include in the implementation:
           - All necessary imports (langchain, langgraph, streamlit, etc.)
           - Environment variable handling for API keys
           - State class definitions for the graph
           - Agent node definitions
           - Graph construction and edge definitions
           - Proper error handling and user feedback
           - Input validation
           - Clear documentation and comments
           - Type hints where appropriate
        
        4. Structure the code following these guidelines:
           - Define clear state schemas for agent communication
           - Implement proper message passing between agents
           - Use Streamlit components for UI elements
           - Separate UI logic from agent/business logic
           - Include loading and configuration of LLM models
        
        5. Follow PEP 8 style guidelines and break down complex functionality into smaller functions
        
        6. Include example environment variables needed in a .env file
        
        7. Provide a brief explanation of the multi-agent architecture chosen and why""",
    )

    code_reviewer = Agent(
        name="Code Reviewer",
        instructions="""You are a senior software engineer specializing in Python code review. Given the requirements and generated code:
        1. Review the code for:
           - Compliance with requirements
           - Code quality and best practices
           - Potential bugs or issues
           - Security vulnerabilities
           - Performance considerations
           - Test coverage
        
        2. Provide detailed feedback on:
           - Missing functionality
           - Code structure improvements
           - Security recommendations
           - Performance optimizations
           - Error handling improvements
        
        3. Format your response as:
           ## Requirements Compliance
           - List of met/unmet requirements
           
           ## Code Quality Issues
           - Identified issues with specific line references
           
           ## Security & Performance
           - Security concerns
           - Performance improvement suggestions
           
           ## Recommended Changes
           - Specific code changes with examples""",
    )
    
    return elaborator, validator, finalizer, test_generator, code_generator, code_reviewer

# Create UI
st.title("Requirement Analysis Genie")
st.write("Enter a requirement and get detailed analysis")

# Input field
requirement = st.text_input("Enter your requirement:")

if st.button("Analyze"):
    if requirement:
        with st.spinner("Analyzing..."):
            try:
                # Create agents
                elaborator, validator, finalizer, test_generator, code_generator, code_reviewer = create_agents()
                
                # Get elaboration
                elaboration = client.run(
                    agent=elaborator,
                    messages=[{"role": "user", "content": requirement}]
                )
                
                # Get validation
                validation = client.run(
                    agent=validator,
                    messages=[{"role": "user", "content": elaboration.messages[-1]["content"]}]
                )

                # Prepare context for finalizer
                final_context = f"""
                Original Requirement:
                {requirement}

                Elaborated Requirements:
                {elaboration.messages[-1]["content"]}

                Validation Feedback:
                {validation.messages[-1]["content"]}
                """

                # Get final requirements
                final_requirements = client.run(
                    agent=finalizer,
                    messages=[{"role": "user", "content": final_context}]
                )

                # Generate test cases and code based on final requirements
                test_context = f"""
                Original Requirement:
                {requirement}

                Final Requirements:
                {final_requirements.messages[-1]["content"]}
                """

                # Run test generator and code generator in parallel
                test_cases = client.run(
                    agent=test_generator,
                    messages=[{"role": "user", "content": test_context}]
                )

                generated_code = client.run(
                    agent=code_generator,
                    messages=[{"role": "user", "content": test_context}]
                )
                
                # Get code review
                review_context = f"""
                Requirements:
                {final_requirements.messages[-1]["content"]}

                Generated Code:
                {generated_code.messages[-1]["content"]}

                Test Cases:
                {test_cases.messages[-1]["content"]}
                """

                code_review = client.run(
                    agent=code_reviewer,
                    messages=[{"role": "user", "content": review_context}]
                )

                # Display results with tabs
                tabs = st.tabs(["Elaboration", "Validation", "Final Requirements", "Test Cases", "Generated Code", "Code Review"])
                
                with tabs[0]:
                    st.subheader("Elaborated Requirements")
                    st.write(elaboration.messages[-1]["content"])
                
                with tabs[1]:
                    st.subheader("Validation Review")
                    st.write(validation.messages[-1]["content"])

                with tabs[2]:
                    st.subheader("Final Requirements")
                    st.write(final_requirements.messages[-1]["content"])

                with tabs[3]:
                    st.subheader("Test Cases")
                    st.write(test_cases.messages[-1]["content"])

                with tabs[4]:
                    st.subheader("Generated Python Code")
                    st.code(generated_code.messages[-1]["content"], language="python")

                with tabs[5]:
                    st.subheader("Code Review Analysis")
                    st.write(code_review.messages[-1]["content"])
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")