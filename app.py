#!/usr/bin/env python3
"""
Requirement Analysis Genie

A Streamlit app that uses the OpenAI Agents SDK to elaborate and refine requirements
using the LLM as a judge pattern for iterative improvement, with automatic handoff
to a use case creation agent.
"""
import os
import asyncio
import traceback
import streamlit as st
from dotenv import load_dotenv

# Import utilities
from utils.async_helpers import run_async
from utils.stream_helpers import stream_content_to_placeholder
from utils.language_helpers import get_ui_text, get_language_instruction
from utils.diagram_helpers import render_diagram, get_image_base64, auto_correct_diagram_code, render_structured_diagram

# Import agents (renamed from agents to smartagents)
from smartagents.elaborator_agent import create_elaborator_agent, create_elaboration_prompt
from smartagents.evaluator_agent import create_evaluator_agent, create_evaluation_prompt, create_feedback_prompt
from smartagents.usecase_agent import create_usecase_agent
from smartagents.processor_agent import create_processor_agent
from smartagents.testcase_agent import create_testcase_agent, create_testcase_prompt
from smartagents.code_agent import create_code_agent, create_code_prompt
from smartagents.diagram_agent import create_diagram_agent, create_diagram_prompt

# Import external dependencies 
from agents import Runner, TResponseInputItem

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Requirement Analysis Genie",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Define language variable early to avoid the "name 'language' is not defined" error
language = "English"  # Default language

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
    
    # Sidebar setup for settings - MOVED UP to define language before it's used
    st.sidebar.title("📋 Settings & Controls")
    
    # Language selection - MOVED UP to define before usage
    language = st.sidebar.selectbox(
        "Output Language:",
        ["English", "Japanese", "Italian"],
        index=0,
        help="Language for generated content (requirements, use cases, etc.) - UI remains in English"
    )
    
    # Application type selection (moved to sidebar)
    app_type = st.sidebar.selectbox(
        "Application Type:",
        ["Web Application", "Mobile App", "Desktop Application", "API/Service"]
    )
    
    # Cloud environment selection for architecture diagrams
    cloud_env = st.sidebar.selectbox(
        "Cloud Environment:",
        ["AWS", "GCP", "Azure"],
        index=1,  # Default to GCP
        help="Cloud environment for architecture diagrams"
    )

    # Model selection
    model = st.sidebar.selectbox(
        "Model:",
        ["o3-mini", "gpt-3.5-turbo-0125", "gpt-4o"],
        index=0,
        help="Choose the model to use for all agents"
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
    
    # Add options for test cases and code generation
    generate_test_cases = st.sidebar.checkbox("Generate Test Cases", value=False,
                                            help="Automatically generate test cases after requirements are finalized")
    
    generate_code = st.sidebar.checkbox("Generate Sample Code", value=False,
                                      help="Automatically generate sample code implementation after requirements are finalized")
    
    # Add option for diagram generation
    generate_diagram = st.sidebar.checkbox("Generate Architecture Diagram", value=True,
                                         help="Automatically generate architecture diagram after requirements are finalized")

    # Main title and description
    st.title("Requirement Analysis Genie")
    st.markdown("This is a demo of orchestrated agents that can analyse requirements, validate them and generate sample code.")

    st.markdown("Enter a requirement and get detailed analysis - (no need to upload documents!)")

    # Brief requirement input - more compact - KEEP UI IN ENGLISH
    st.markdown(f"### Enter your requirement:")
    prompt = st.text_area(
        "Requirement",
        value="",
        height=100,
        label_visibility="collapsed",
        placeholder="Example: Create a secure login screen with email and password authentication, including input validation and error handling."
    )

    # Create column for button
    col1, col2 = st.columns([1, 5])
    
    with col1:
        # Analyze button - KEEP UI IN ENGLISH
        analyze_button = st.button("Analyze", type="primary")
    
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

    async def iterative_requirements_elaboration(user_prompt, app_type, output_container, 
                                               model="o3-mini", max_iterations=3, create_use_cases=True,
                                               create_test_cases=False, create_code=False, create_diagram=True, 
                                               cloud_env="GCP", language="English"):
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
        
        # Create the agents
        if DEBUG:
            with debug_container:
                st.info("Creating agents...")
        
        elaborator_agent = create_elaborator_agent(model=model, language=language)
        evaluator_agent = create_evaluator_agent(model=model, language=language)
        usecase_agent = create_usecase_agent(model=model, language=language)
        final_agent = create_processor_agent(usecase_agent, model=model, language=language)
        
        # Create test case and code agents if needed
        testcase_agent = None
        code_agent = None
        diagram_agent = None
        
        if create_test_cases:
            testcase_agent = create_testcase_agent(model=model, language=language)
            if DEBUG:
                with debug_container:
                    st.info("Test case agent created")
                    
        if create_code:
            code_agent = create_code_agent(model=model, language=language)
            if DEBUG:
                with debug_container:
                    st.info("Code generator agent created")
        
        if create_diagram:
            diagram_agent = create_diagram_agent(model=model, language=language)
            if DEBUG:
                with debug_container:
                    st.info("Diagram generator agent created")
        
        if DEBUG:
            with debug_container:
                st.success("Agents created successfully")
        
        # Construct the initial prompt
        elaboration_prompt = create_elaboration_prompt(user_prompt, app_type, language=language)
        
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
                elaboration_text = await stream_content_to_placeholder(
                    elaboration_result, 
                    streaming_placeholder, 
                    DEBUG, 
                    debug_container
                )
                
                # Store this version
                versions.append(elaboration_text)
                
                # Create input items for the evaluator
                eval_inputs = [{"content": create_evaluation_prompt(elaboration_text, language=language), "role": "user"}]
                
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
                feedback_prompt = create_feedback_prompt(evaluation, elaboration_prompt, language=language)
                
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
                use_cases_content = await stream_content_to_placeholder(
                    usecase_result, 
                    usecase_placeholder, 
                    DEBUG, 
                    debug_container
                )
                
                status_area.success("✅ Use cases generated successfully!")
            
            # Generate test cases if requested and we have a final document
            test_cases_content = None
            if create_test_cases and final_document and testcase_agent:
                status_area.info("🔄 Generating test cases from requirements...")
                
                # Create placeholder for test case streaming
                testcase_placeholder = output_container.empty()
                testcase_placeholder.info("💭 Creating test cases...")
                
                # Set up input for the test case agent
                testcase_input = [
                    {"content": create_testcase_prompt(final_document, language=language), "role": "user"}
                ]
                
                if DEBUG:
                    with debug_container:
                        st.info("Running test case generator agent")
                
                # Call the test case agent
                testcase_result = Runner.run_streamed(testcase_agent, testcase_input)
                test_cases_content = await stream_content_to_placeholder(
                    testcase_result, 
                    testcase_placeholder, 
                    DEBUG, 
                    debug_container
                )
                
                status_area.success("✅ Test cases generated successfully!")
            
            # Generate code if requested and we have a final document
            code_content = None
            if create_code and final_document and code_agent:
                status_area.info("🔄 Generating sample code implementation...")
                
                # Create placeholder for code streaming
                code_placeholder = output_container.empty()
                code_placeholder.info("💭 Creating code implementation...")
                
                # Set up input for the code agent
                code_input = [
                    {"content": create_code_prompt(final_document, app_type, language=language), "role": "user"}
                ]
                
                if DEBUG:
                    with debug_container:
                        st.info("Running code generator agent")
                
                # Call the code agent
                code_result = Runner.run_streamed(code_agent, code_input)
                code_content = await stream_content_to_placeholder(
                    code_result, 
                    code_placeholder, 
                    DEBUG, 
                    debug_container
                )
                
                status_area.success("✅ Sample code generated successfully!")
            
            # Generate architecture diagram if requested and we have a final document
            diagram_output = None
            diagram_image_path = None
            if create_diagram and final_document and diagram_agent:
                status_area.info(f"🔄 Generating architecture diagram for {cloud_env}...")
                
                # Create placeholder for diagram streaming
                diagram_placeholder = output_container.empty()
                diagram_placeholder.info("💭 Creating architecture diagram...")
                
                # Set up input for the diagram agent
                diagram_input = [
                    {"content": create_diagram_prompt(final_document, app_type, cloud_env, language=language), "role": "user"}
                ]
                
                if DEBUG:
                    with debug_container:
                        st.info("Running diagram generator agent")
                
                # Call the diagram agent
                try:
                    diagram_result = await Runner.run(diagram_agent, diagram_input)
                    diagram_output = diagram_result.final_output
                    
                    # Debug information
                    if DEBUG:
                        with debug_container:
                            st.info(f"Diagram output: {diagram_output}")
                    
                    # Attempt to render the diagram
                    if diagram_output and hasattr(diagram_output, 'imports'):
                        # This is our new structured output
                        diagram_placeholder.info("💭 Generating and rendering diagram from structured output...")
                        
                        try:
                            # Use our new render_structured_diagram function
                            success, result = render_structured_diagram(diagram_output)
                            
                            if success:
                                diagram_image_path = result
                                diagram_placeholder.success("✅ Diagram rendered successfully!")
                            else:
                                diagram_placeholder.error(f"⚠️ {result}")
                        except Exception as e:
                            diagram_placeholder.error(f"⚠️ Error rendering diagram: {str(e)}")
                            if DEBUG:
                                with debug_container:
                                    st.error(f"Diagram rendering error: {traceback.format_exc()}")
                    
                    # Compatibility with old format - will be removed once transition is complete
                    elif diagram_output and hasattr(diagram_output, 'diagram_code'):
                        # Old direct code approach
                        diagram_code = diagram_output.diagram_code
                        diagram_placeholder.info("💭 Validating and rendering diagram...")
                        
                        # First try to validate and render
                        try:
                            success, result = render_diagram(diagram_code)
                            
                            # If validation fails, try auto-correction using the LLM as judge pattern
                            if not success:
                                diagram_placeholder.warning(f"⚠️ {result}")
                                diagram_placeholder.info("💭 Attempting to auto-correct diagram code...")
                                
                                # Use the diagram agent to auto-correct
                                correction_success, corrected_result = await auto_correct_diagram_code(
                                    diagram_code, 
                                    final_document, 
                                    app_type, 
                                    cloud_env, 
                                    diagram_agent
                                )
                                
                                if correction_success:
                                    # Update the diagram code with the corrected version
                                    diagram_code = corrected_result
                                    diagram_output.diagram_code = corrected_result
                                    
                                    # Try rendering again with the corrected code
                                    success, result = render_diagram(diagram_code)
                                    if success:
                                        diagram_image_path = result
                                        diagram_placeholder.success("✅ Diagram auto-corrected and rendered successfully!")
                                    else:
                                        diagram_placeholder.error(f"⚠️ Auto-correction failed to resolve all issues: {result}")
                                else:
                                    diagram_placeholder.error(f"⚠️ Auto-correction failed: {corrected_result}")
                            else:
                                # Original code was valid
                                diagram_image_path = result
                                diagram_placeholder.success("✅ Diagram rendered successfully!")
                                
                        except Exception as e:
                            diagram_placeholder.error(f"⚠️ Error rendering diagram: {str(e)}")
                            if DEBUG:
                                with debug_container:
                                    st.error(f"Diagram rendering error: {traceback.format_exc()}")
                    else:
                        diagram_placeholder.error("⚠️ Invalid diagram output format")
                        if DEBUG:
                            with debug_container:
                                st.error(f"Invalid diagram output format: {diagram_output}")
                except Exception as e:
                    diagram_placeholder.error(f"⚠️ Error generating diagram: {str(e)}")
                    if DEBUG:
                        with debug_container:
                            st.error(f"Diagram generation error: {traceback.format_exc()}")
                
                status_area.success("✅ Architecture diagram processing completed!")
            
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
                        
                        # Add download button for the final document - Keep UI text in English
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
                    
                    if test_cases_content:
                        st.markdown(test_cases_content)
                        
                        # Add download button for test cases - Keep UI text in English
                        st.download_button(
                            label="📥 Download Test Cases",
                            data=test_cases_content,
                            file_name="test_cases.md",
                            mime="text/markdown",
                            key="download_test_cases"
                        )
                    else:
                        st.info("Test case generation was not enabled. Enable it in the sidebar settings to generate test cases.")
                
                # Code tab - placeholder for now
                with tabs[4]:
                    st.markdown("## Sample Code")
                    
                    if code_content:
                        st.markdown(code_content)
                        
                        # Add download button for code - Keep UI text in English
                        st.download_button(
                            label="📥 Download Sample Code",
                            data=code_content,
                            file_name="sample_code.md",
                            mime="text/markdown",
                            key="download_code"
                        )
                    else:
                        st.info("Code generation was not enabled. Enable it in the sidebar settings to generate sample code.")
                
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
                
                # Architecture tab - Show the generated architecture diagram
                with tabs[6]:
                    st.markdown("## Architecture Diagram")
                    
                    try:
                        if diagram_output:
                            # Get attributes from DiagramOutput class
                            explanation = diagram_output.explanation
                            diagram_code = diagram_output.diagram_code
                            diagram_type = diagram_output.diagram_type
                            
                            # Display diagram type and explanation
                            st.markdown(f"### {diagram_type}")
                            st.markdown("### Diagram Explanation")
                            st.markdown(explanation)
                            
                            # Display rendered image if available
                            if diagram_image_path and os.path.exists(diagram_image_path):
                                st.markdown("### Diagram")
                                st.image(diagram_image_path, caption=f"{app_type} Architecture on {cloud_env}")
                                
                                # Provide download option for the image
                                with open(diagram_image_path, "rb") as img_file:
                                    st.download_button(
                                        label="📥 Download Diagram Image",
                                        data=img_file,
                                        file_name="architecture_diagram.png",
                                        mime="image/png",
                                        key="download_diagram_img"
                                    )
                            
                            # Display the code
                            st.markdown("### Diagram Code")
                            st.code(diagram_code, language="python")
                            
                            # Add download button for the diagram code
                            st.download_button(
                                label="📥 Download Diagram Code",
                                data=diagram_code,
                                file_name="architecture_diagram.py",
                                mime="text/plain",
                                key="download_diagram_code"
                            )
                        else:
                            st.info("Diagram generation was not enabled or failed. Enable it in the sidebar settings to generate architecture diagrams.")
                    except Exception as e:
                        st.error(f"Error displaying diagram: {str(e)}")
                        if DEBUG:
                            with st.expander("Error Details", expanded=False):
                                st.error(traceback.format_exc())
                
                # Use Cases tab - if we have use cases
                if create_use_cases and use_cases_content and len(tab_titles) > 7:
                    with tabs[7]:
                        st.markdown("## Use Cases")
                        
                        if use_cases_content:
                            st.markdown(use_cases_content)
                            
                            # Add download button for use cases - Keep UI text in English
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
                model,
                max_iterations,
                generate_use_cases,
                generate_test_cases,
                generate_code,
                generate_diagram,
                cloud_env,
                language
            ))

except Exception as e:
    st.error(f"Critical error in application: {str(e)}")
    if 'DEBUG' in locals() and DEBUG:
        with st.expander("Error Details", expanded=False):
            st.error(traceback.format_exc())

if __name__ == "__main__":
    # This code will only run when this module is executed directly
    st.sidebar.info("Running as main application") 