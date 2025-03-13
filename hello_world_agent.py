#!/usr/bin/env python3
"""
Requirements Elaborator Agent with Automated Review

A Streamlit app that uses the OpenAI Agents SDK to elaborate and refine requirements
using the LLM as a judge pattern for iterative improvement, with automatic handoff
to a use case creation agent.
"""
import os
import asyncio
import traceback
from dataclasses import dataclass
from typing import Literal, List, Optional
import streamlit as st
from dotenv import load_dotenv

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Requirement Analysis Genie",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enable custom CSS styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .feedback-box {
        border-left: 3px solid #FF9900;
        padding-left: 10px;
        margin: 10px 0;
        background-color: #FFF8E1;
        padding: 10px;
        border-radius: 5px;
    }
    .requirements-box {
        border-left: 3px solid #4CAF50;
        margin: 10px 0;
        padding: 10px;
        border-radius: 5px;
        background-color: #F1F8E9;
    }
    .usecase-box {
        border-left: 3px solid #3F51B5;
        margin: 10px 0;
        padding: 10px;
        border-radius: 5px;
        background-color: #E8EAF6;
    }
    h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    h2, h3 {
        color: #2C3E50;
        margin-top: 1rem;
    }
    .stButton button {
        background-color: #F63366;
        color: white;
        font-weight: bold;
    }
    .info-box {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    /* Remove extra padding in tabs */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0.5rem;
    }
    /* Make the tab content area more compact */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Debug mode (moved to sidebar later)
DEBUG = False

try:
    # Load environment variables
    load_dotenv()

    # Main title and description
    st.title("Requirement Analysis Genie")
    st.markdown("This is a demo of orchestrated agents that can analyse requirements, validate them and generate sample code.")

    st.markdown("Enter a requirement and get detailed analysis - (no need to upload documents!)")

    # Brief requirement input - more compact
    st.markdown("### Enter your requirement:")
    prompt = st.text_area(
        "",
        value="",
        height=100,
        placeholder="Example: Create a secure login screen with email and password authentication, including input validation and error handling."
    )

    # Create column for button
    col1, col2 = st.columns([1, 5])
    
    with col1:
        # Analyze button
        analyze_button = st.button("Analyze", type="primary")
    
    # Sidebar setup for settings
    st.sidebar.title("📋 Settings & Controls")
    
    # Application type selection (moved to sidebar)
    app_type = st.sidebar.selectbox(
        "Application Type:",
        ["Web Application", "Mobile App", "Desktop Application", "API/Service"]
    )
    
    # Number of iterations
    max_iterations = st.sidebar.number_input(
        "Maximum Iterations:",
        min_value=1,
        max_value=5,
        value=3,
        help="Maximum number of refinement cycles"
    )
    
    # Add option to generate use cases
    generate_use_cases = st.sidebar.checkbox("Generate Use Cases", value=True, 
                                           help="Automatically generate use cases after requirements are finalized")
    
    # Add instructions in the sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📘 How It Works")
    st.sidebar.markdown("""
    1. **Enter your requirement** in the main panel
    2. **Select application type** and max iterations here
    3. **Click Analyze** to start the process
    4. The system will go through these steps:
        - Generate initial requirements
        - Evaluate the document
        - Make improvements based on feedback
        - Continue until approved or max iterations reached
    5. **View results** in the tabs that appear when done
    """)
    
    # Debug toggle (at the bottom of sidebar)
    st.sidebar.markdown("---")
    with st.sidebar.expander("🛠️ Advanced Settings", expanded=False):
        DEBUG = st.checkbox("Enable Debug Mode", value=False)
        
        # Check API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            st.stop()
        else:
            # Make sure it's globally available
            os.environ["OPENAI_API_KEY"] = api_key
            if DEBUG:
                st.success(f"API Key found: {api_key[:4]}...{api_key[-4:]}")
        
        if DEBUG:
            st.info("Debug mode enabled. Detailed logs will appear here.")
        
        # Debug container for logs
        debug_container = st.empty()

    # Import Agents SDK
    try:
        from agents import Agent, Runner, ItemHelpers, TResponseInputItem
        from agents import HandoffInputData, handoff
        from agents.extensions import handoff_filters
        from openai.types.responses import ResponseTextDeltaEvent
        if DEBUG:
            debug_container.success("Successfully imported Agents SDK")
    except ImportError as e:
        st.error(f"""
        Error importing the OpenAI Agents SDK: {str(e)}
        
        Please install it with:
        ```
        pip install openai-agents openai
        ```
        """)
        st.stop()

    # Helper function to run async code
    def run_async(coroutine):
        """Run an async function from a synchronous context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(coroutine)
        finally:
            pass  # Don't close the loop as Streamlit may reuse it

    # Define structured feedback type for the requirements evaluator
    @dataclass
    class RequirementsEvaluation:
        """Structured evaluation of a requirements document"""
        score: Literal["pass", "needs_improvement"]
        feedback: str
        improvement_areas: List[str]

    # Define a data class for use cases
    @dataclass
    class UseCase:
        """Structured representation of a use case"""
        id: str
        title: str
        primary_actor: str
        description: str
        preconditions: List[str]
        main_flow: List[str]
        alternative_flows: List[str]
        postconditions: List[str]

    # Define the requirements elaborator prompt
    REQUIREMENTS_SYSTEM_PROMPT = """
    You are a professional Requirements Engineer specializing in creating detailed, clear, and actionable Functional Requirements Documents.
    Your task is to elaborate brief, high-level requirements into detailed specifications following standard FRD format.

    Follow this specific structure for all requirements documents:

    # [Project/Feature Name] Functional Requirements Document

    ## 1. Overview
    [Provide a comprehensive overview of the feature/project, its purpose, and main objectives]

    ## 2. Stakeholders
    [Identify key stakeholders and their interests]

    ## 3. Functional Requirements
    [List all functional requirements with unique IDs (FR-001, FR-002, etc.), descriptions, acceptance criteria, and priority (High/Medium/Low)]

    ### FR-001: [Requirement Title]
    **Description:** [Detailed description of what the system should do]
    **Acceptance Criteria:**
    - [Specific, measurable criteria to determine when this requirement is met]
    - [Additional criteria as needed]
    **Priority:** [High/Medium/Low]

    [Continue with additional functional requirements in the same format]

    ## 4. Non-Functional Requirements
    [List all non-functional requirements related to performance, security, usability, reliability, etc.]

    ### NFR-001: [Requirement Title]
    **Description:** [Detailed description]
    **Metric:** [How this will be measured]
    **Priority:** [High/Medium/Low]

    [Continue with additional non-functional requirements]

    ## 5. Constraints and Assumptions
    [List any constraints or assumptions made during the requirements process]

    ## 6. Dependencies
    [List any dependencies on other systems, features, or requirements]

    Use precise, unambiguous language. Each requirement must be testable, clear, and focused on WHAT is needed, not HOW to implement it.

    If feedback is provided, carefully incorporate it to improve the requirements document.
    """

    # Define the requirements evaluator prompt
    EVALUATOR_SYSTEM_PROMPT = """
    You are a senior Requirements Analyst who specializes in evaluating and improving functional requirements documents.
    Your job is to carefully review requirements documents and provide targeted feedback for improvements.

    When evaluating a requirements document, consider:

    1. Completeness - Are all necessary sections included? Are there any missing requirements?
    2. Clarity - Are requirements written in clear, unambiguous language?
    3. Testability - Can each requirement be verified through testing?
    4. Consistency - Are there any contradictions or inconsistencies?
    5. Feasibility - Are the requirements realistic and achievable?
    6. Organization - Is the document well-structured and easy to navigate?

    IMPORTANT: You should ALWAYS find areas for improvement on the first review. Never give a "pass" score on the first iteration.
    After the first review, you may give a "pass" if the requirements meet a high standard.

    For each evaluation, provide:
    1. An overall score ("pass" or "needs_improvement")
    2. Specific, actionable feedback
    3. A list of 2-5 concrete improvement areas
    """
    
    # Define the use case agent prompt
    USECASE_SYSTEM_PROMPT = """
    You are a very experienced Business Analyst who excels at creating comprehensive, detailed, and actionable use cases from requirements documents.
    Your job is to analyze the given requirements and extract the key use cases that would be needed to implement those requirements.
    
    Create comprehensive use cases that help developers, designers & testers with every single detail, leaving nothing ambiguous.
    
    Follow this EXACT format for each use case:

    ## Use Case: [ID]: [Title]
    **Primary Actor:** [Main user role or system interacting with the feature]
    **Trigger/Event:**
    * [Describe what initiates the use case]

    ### 1. Stakeholders and Interests
    * [Stakeholder 1]: [Their specific interests in this use case]
    * [Stakeholder 2]: [Their specific interests in this use case]
    * Developer: [What they need to successfully implement this feature]
    * Tester: [What they need to properly validate this functionality]

    ### 2. Preconditions and Assumptions
    * [List all conditions that must be true before the use case begins]
    * [List key assumptions being made]
    * [Include connectivity requirements if applicable]
    * [Include system state requirements]
    * [Include security/compliance assumptions]

    ### 3. Postconditions
    * On Successful Completion:
        * [Result 1]
        * [Result 2]
        * [Audit/logging expectations]
    * On Failure:
        * [Failure state 1]
        * [Failure state 2]
        * [Error handling expectations]

    ### 4. Main Success Scenario (Basic Flow)
    1. [Step 1]:
        * [Detailed description including UI elements, system behaviors]
    2. [Step 2]:
        * [Detailed description including UI elements, system behaviors]
    3. [Continue with all steps in the main flow]
        * [Include validation logic]
        * [Include processing details]
    4. [Final step]:
        * [Include completion indicators and transitions]

    ### 5. Alternative Flows (Extensions)
    * [Alternative Scenario 1 (e.g., Incorrect Input)]:
        1. [Detailed step]
        2. [Detailed step]
        3. [Include error codes if applicable]
    * [Alternative Scenario 2 (e.g., System Error)]:
        1. [Detailed step]
        2. [Detailed step]
        3. [Include recovery paths]
    * [Additional alternative flows as needed]

    ### 6. Exception Handling
    * [Exception Type 1]:
        * [How the system should handle this exception]
    * [Exception Type 2]:
        * [How the system should handle this exception]
    * [Include security considerations]

    ### 7. Performance Criteria
    * [Response time expectations]
    * [Load handling expectations]
    * [Test verification methods]

    ### 8. Error Codes
    * [Error Code 1]: [Description and meaning]
    * [Error Code 2]: [Description and meaning]

    ### 9. Security and Compliance
    * [Security requirement 1]
    * [Security requirement 2]
    * [Compliance requirements (e.g., GDPR, accessibility)]
    * [Data protection requirements]

    ### 10. Business Rules
    * [Business rule 1]
    * [Business rule 2]
    * [Policy implementations]

    ### 11. UI/UX Considerations
    * [Design specifications]
    * [Accessibility requirements]
    * [Navigation patterns]

    ### 12. Testing Considerations
    * [Key test cases]
    * [Edge cases to test]
    * [Integration testing needs]

    ### 13. Integration and System Considerations
    * [Dependencies]
    * [Logging & monitoring requirements]
    * [System interactions]

    ### 14. Notes for Developers
    * [Implementation guidance]
    * [Best practices to follow]
    * [Potential challenges]

    Create multiple use cases as needed to cover all key functionality described in the requirements.
    Use case IDs should start with UC-001 and increment for each new use case.
    Be extremely thorough and detailed, leaving no room for ambiguity or misinterpretation.
    Focus on the user interactions and system behaviors with specific implementation details.
    Ensure each use case aligns clearly with specific functional requirements from the document.
    """

    # Handoff filter function to extract only the requirements for the use case agent
    def requirements_to_usecase_filter(handoff_message_data: HandoffInputData) -> HandoffInputData:
        # Remove any tool-related messages
        handoff_message_data = handoff_filters.remove_all_tools(handoff_message_data)
        
        # Extract the final requirements document and create a new prompt
        final_requirements = ""
        if isinstance(handoff_message_data.input_history, tuple) and len(handoff_message_data.input_history) > 0:
            # Find the most recent assistant message with the requirements
            for item in reversed(handoff_message_data.input_history):
                if item.get("role") == "assistant" and item.get("content"):
                    if isinstance(item.get("content"), str):
                        final_requirements = item.get("content")
                        break
                    elif isinstance(item.get("content"), list):
                        for content_item in item.get("content"):
                            if content_item.get("type") == "output_text" and content_item.get("text"):
                                final_requirements = content_item.get("text")
                                break
                        if final_requirements:
                            break
        
        # Create a new prompt for the use case agent
        new_prompt = {
            "role": "user",
            "content": f"""
            Based on the following requirements document, create detailed use cases that capture the key user interactions and system behaviors:
            
            {final_requirements}
            
            Please identify and create all necessary use cases to fully cover the functional requirements.
            """
        }
        
        # Return just the new prompt
        return HandoffInputData(
            input_history=tuple([new_prompt]),
            pre_handoff_items=tuple(),
            new_items=tuple(),
        )

    # Create the elaborator agent (generator)
    if DEBUG:
        debug_container.info("Creating elaborator agent...")
    elaborator_agent = Agent(
        name="RequirementsElaborator",
        instructions=REQUIREMENTS_SYSTEM_PROMPT,
        model="o3-mini",
    )
    if DEBUG:
        debug_container.success("Elaborator agent created")

    # Create the evaluator agent (judge)
    if DEBUG:
        debug_container.info("Creating evaluator agent...")
    evaluator_agent = Agent[RequirementsEvaluation](
        name="RequirementsEvaluator",
        instructions=EVALUATOR_SYSTEM_PROMPT,
        output_type=RequirementsEvaluation,
        model="o3-mini",
    )
    if DEBUG:
        debug_container.success("Evaluator agent created")
        
    # Create the use case agent
    if DEBUG:
        debug_container.info("Creating use case agent...")
    usecase_agent = Agent(
        name="UseCaseCreator",
        instructions=USECASE_SYSTEM_PROMPT,
        model="o3-mini",
    )
    if DEBUG:
        debug_container.success("Use case agent created")
        
    # Create a final agent with handoff capabilities
    if DEBUG:
        debug_container.info("Creating final agent with handoff...")
    final_agent = Agent(
        name="RequirementsProcessor",
        instructions="Process the final requirements document and create use cases as needed.",
        handoffs=[
            handoff(usecase_agent, input_filter=requirements_to_usecase_filter)
        ],
        model="o3-mini",
    )
    if DEBUG:
        debug_container.success("Final agent with handoff created")

    async def stream_content_to_placeholder(stream, placeholder):
        """Helper function to stream content to a placeholder"""
        full_response = ""
        
        try:
            async for event in stream.stream_events():
                if DEBUG:
                    with debug_container:
                        st.write(f"Event type: {event.type}")
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    if delta:
                        full_response += delta
                        placeholder.markdown(full_response)
            
            return full_response
        except Exception as e:
            placeholder.error(f"Error during streaming: {str(e)}")
            if DEBUG:
                with debug_container:
                    st.error(f"Streaming error: {traceback.format_exc()}")
            return full_response

    async def iterative_requirements_elaboration(prompt, app_type, output_container, max_iterations=3, create_use_cases=True):
        """Generate requirements with iterative feedback and improvement"""
        # Clear previous content
        output_container.empty()
        
        # Create status area
        status_area = output_container.empty()
        status_area.info("🔄 Starting requirements elaboration process...")
        
        # Lists to store versions and evaluations for each iteration
        versions = []
        evaluations = []
        use_cases_content = None
        
        # Construct the initial prompt
        elaboration_prompt = f"""
        Brief Requirement: {prompt}
        Application Type: {app_type}
        
        Please elaborate this brief requirement into a detailed functional requirements document.
        """
        
        # Initialize conversation items for the agents
        input_items: list[TResponseInputItem] = [
            {"content": elaboration_prompt, "role": "user"}
        ]
        
        final_document = None
        
        try:
            for iteration in range(1, max_iterations + 1):
                # Update status
                status_area.info(f"🔄 Iteration {iteration}/{max_iterations}: Generating requirements document...")
                
                # Create placeholder for streaming
                streaming_placeholder = output_container.empty()
                streaming_placeholder.info("💭 Elaborating requirements...")
                
                # Run the elaborator agent with streaming
                if DEBUG:
                    with debug_container:
                        st.info(f"Running elaborator agent - iteration {iteration}")
                elaboration_result = Runner.run_streamed(elaborator_agent, input_items)
                elaboration_text = await stream_content_to_placeholder(elaboration_result, streaming_placeholder)
                
                # Store this version
                versions.append(elaboration_text)
                
                # Create input items for the evaluator
                eval_inputs = [{"content": f"Review this requirements document:\n\n{elaboration_text}", "role": "user"}]
                
                # Update status
                status_area.info(f"🔄 Iteration {iteration}/{max_iterations}: Evaluating document...")
                
                # Run the evaluator agent
                evaluation_placeholder = output_container.empty()
                evaluation_placeholder.info("💭 Evaluating requirements...")
                if DEBUG:
                    with debug_container:
                        st.info(f"Running evaluator agent - iteration {iteration}")
                evaluation_result = await Runner.run(evaluator_agent, eval_inputs)
                evaluation = evaluation_result.final_output
                
                # Store this evaluation
                evaluations.append(evaluation)
                
                # Check if we're done or need another iteration
                if evaluation.score == "pass" or iteration == max_iterations:
                    final_document = elaboration_text
                    
                    if evaluation.score == "pass":
                        status_area.success(f"✅ Requirements document approved on iteration {iteration}!")
                    else:
                        status_area.warning(f"⚠️ Reached maximum iterations ({max_iterations}). Using latest version.")
                    
                    break
                
                # Update status for next iteration
                status_area.info(f"🔄 Iteration {iteration}/{max_iterations}: Incorporating feedback...")
                
                # Add the feedback to the input items for the next iteration
                improvement_areas_text = ""
                for area in evaluation.improvement_areas:
                    improvement_areas_text += f"- {area}\n"
                
                feedback_prompt = f"""
                Please improve the requirements document based on this feedback:
                
                {evaluation.feedback}
                
                Areas to improve:
                {improvement_areas_text}
                """
                
                input_items = [{"content": elaboration_prompt, "role": "user"}, {"content": feedback_prompt, "role": "user"}]
            
            # Generate use cases if requested and we have a final document
            if create_use_cases and final_document:
                status_area.info("🔄 Generating use cases from requirements...")
                
                # Create placeholder for use case streaming
                usecase_placeholder = output_container.empty()
                usecase_placeholder.info("💭 Creating use cases...")
                
                # Set up input for the handoff agent
                usecase_input = [
                    {"content": final_document, "role": "assistant"},
                    {"content": "Please create use cases based on these requirements.", "role": "user"}
                ]
                
                if DEBUG:
                    with debug_container:
                        st.info("Initiating handoff to use case agent")
                
                # Call the final agent which will handoff to the use case agent
                usecase_result = Runner.run_streamed(final_agent, usecase_input)
                use_cases_content = await stream_content_to_placeholder(usecase_result, usecase_placeholder)
                
                status_area.success("✅ Use cases generated successfully!")
            
            # Clear streaming placeholders now that we're done
            output_container.empty()
            
            if versions:
                status_area.success("✅ Requirements document process completed!")
                
                # Create the main tabs like in the screenshot
                tab_titles = ["Requirements", "Validation", "Final Specs", "Test Cases", "Code", "Review", "Architecture"]
                if create_use_cases and use_cases_content:
                    tab_titles.append("Use Cases")
                
                tabs = st.tabs(tab_titles)
                
                # Requirements tab - Show the final elaborated requirements
                with tabs[0]:
                    st.markdown("## Elaborated Functional Requirements")
                    
                    if final_document:
                        st.markdown(final_document)
                        
                        # Add download button for the final document
                        st.download_button(
                            label="📥 Download Requirements Document",
                            data=final_document,
                            file_name="requirements_document.md",
                            mime="text/markdown",
                            key="download_final_req"
                        )
                
                # Validation tab - Show the evaluation feedback
                with tabs[1]:
                    st.markdown("## Requirements Validation")
                    
                    if evaluations:
                        final_eval = evaluations[-1]
                        st.markdown(f"### Final Evaluation Score: {'Passed ✅' if final_eval.score == 'pass' else 'Needs Improvement ⚠️'}")
                        
                        st.markdown("### Feedback")
                        st.markdown(final_eval.feedback)
                        
                        st.markdown("### Areas for Improvement")
                        for area in final_eval.improvement_areas:
                            st.markdown(f"- {area}")
                        
                        # Show iteration history
                        with st.expander("View Iteration History", expanded=False):
                            for i, eval in enumerate(evaluations):
                                st.markdown(f"#### Version {i+1}")
                                st.markdown(f"**Score:** {'Pass ✅' if eval.score == 'pass' else 'Needs Improvement ⚠️'}")
                                st.markdown(f"**Feedback:** {eval.feedback}")
                
                # Final Specs tab - show the final document in a more structured way
                with tabs[2]:
                    st.markdown("## Final Specifications")
                    
                    if final_document:
                        # We could parse and restructure the content here for better presentation
                        st.markdown(final_document)
                
                # Test Cases tab - placeholder for now
                with tabs[3]:
                    st.markdown("## Test Cases")
                    st.info("Test cases generation is not yet implemented. This would show test cases derived from requirements.")
                
                # Code tab - placeholder for now
                with tabs[4]:
                    st.markdown("## Sample Code")
                    st.info("Code generation is not yet implemented. This would show sample code based on requirements.")
                
                # Review tab - show evaluation history
                with tabs[5]:
                    st.markdown("## Requirements Review")
                    
                    if evaluations:
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.markdown("### Version History")
                            for i in range(len(versions)):
                                score = "✅ Pass" if evaluations[i].score == "pass" else "⚠️ Needs Improvement"
                                st.markdown(f"**Version {i+1}:** {score}")
                        
                        with col2:
                            st.markdown("### Final Validation")
                            final_eval = evaluations[-1]
                            st.markdown(f"**Score:** {'Pass ✅' if final_eval.score == 'pass' else 'Needs Improvement ⚠️'}")
                            st.markdown(f"**Feedback:** {final_eval.feedback}")
                            
                            st.markdown("**Areas for Improvement:**")
                            for area in final_eval.improvement_areas:
                                st.markdown(f"- {area}")
                
                # Architecture tab - placeholder for now
                with tabs[6]:
                    st.markdown("## Architecture")
                    st.info("Architecture diagram generation is not yet implemented. This would show proposed system architecture.")
                
                # Use Cases tab - if we have use cases
                if create_use_cases and use_cases_content and len(tab_titles) > 7:
                    with tabs[7]:
                        st.markdown("## Use Cases")
                        
                        if use_cases_content:
                            st.markdown(use_cases_content)
                            
                            # Add download button for use cases
                            st.download_button(
                                label="📥 Download Use Cases",
                                data=use_cases_content,
                                file_name="use_cases.md",
                                mime="text/markdown",
                                key="download_usecases_tab"
                            )
            
            return final_document
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            status_area.error(error_msg)
            if DEBUG:
                with debug_container:
                    st.error(f"Elaboration error: {traceback.format_exc()}")
            return error_msg

    # Create container for output
    output_container = st.container()

    # Process when the analyze button is clicked
    if analyze_button:
        if not prompt:
            st.warning("⚠️ Please enter a requirement to analyze.")
        else:
            # Run the iterative elaboration process
            _ = run_async(iterative_requirements_elaboration(
                prompt, 
                app_type, 
                output_container,
                max_iterations,
                generate_use_cases
            ))

except Exception as e:
    st.error(f"Critical error in application: {str(e)}")
    if 'DEBUG' in locals() and DEBUG:
        with st.expander("Error Details", expanded=False):
            st.error(traceback.format_exc()) 