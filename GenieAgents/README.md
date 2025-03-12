# GenieAgents

This directory contains the core agent implementations for ReqGenie, a requirements analysis and generation system.

## Architecture

The system uses a deterministic flow of specialized agents to process requirements:

1. **ElaboratorAgent**: Expands and elaborates on initial requirements
2. **ValidatorAgent**: Validates the elaborated requirements
3. **FinalizerAgent**: Creates a final specification from validated requirements
4. **TestGeneratorAgent**: Generates test cases from the final specification
5. **CodeGeneratorAgent**: Generates sample code based on the requirements
6. **CodeReviewerAgent**: Reviews the generated code
7. **JiraAgent**: Creates Jira tickets from the requirements
8. **DiagramAgent**: Generates architecture diagrams

## Formatted Output

The system now includes an `OutputFormatter` class that converts structured JSON output into human-readable formatted text. This is particularly useful for displaying results in user interfaces like Streamlit.

### Using the OutputFormatter

The `OutputFormatter` class provides methods to format different types of structured output:

```python
from GenieAgents.output_formatter import OutputFormatter

# Format any type of output
formatted_text = OutputFormatter.format_any_output(structured_output)

# Format specific output types
formatted_elaboration = OutputFormatter.format_elaboration(elaboration_data)
formatted_test_cases = OutputFormatter.format_test_cases(test_case_data)
formatted_validation = OutputFormatter.format_validation(validation_data)
formatted_jira_tickets = OutputFormatter.format_jira_tickets(jira_data)
formatted_code_review = OutputFormatter.format_code_review(review_data)
formatted_final_spec = OutputFormatter.format_final_spec(spec_data)
```

### Streaming with Formatted Output

When using streaming with agents, you can use the `StreamingHandler` class to automatically format the output:

```python
from examples.streaming_example import stream_with_handler
from GenieAgents.elaborator_agent import ElaboratorAgent, ElaborationOutput

# Create the agent
agent = ElaboratorAgent()

# Stream with formatted output
result = await stream_with_handler(
    agent, 
    input_prompt, 
    ElaborationOutput,  # Optional: provide the output model for structured parsing
    debug_mode=False,
    use_formatted_output=True  # Enable formatted output
)

# The result will be formatted text instead of JSON
print(result)
```

### In Streamlit Applications

The Streamlit application (`genie.py`) has been updated to use the formatter automatically. When displaying results, it now uses `st.markdown()` instead of `st.write()` to properly render the formatted text with Markdown formatting.

## Configuration

The `RequirementProcessor` class now accepts a `use_formatted_output` parameter (default: `True`) that controls whether the results are automatically formatted:

```python
from GenieAgents.requirement_processor import RequirementProcessor

# Create processor with automatic formatting
processor = RequirementProcessor(use_formatted_output=True)

# Process requirements
results = await processor.process(
    requirement="Create a login system",
    app_type="Web Application"
)

# Results will be formatted text instead of JSON
```

## Command Line Example

To see the formatter in action, run the streaming example:

```bash
# Run with formatted output (default)
python examples/streaming_example.py

# Run with JSON output
python examples/streaming_example.py --json

# Enable debug mode
python examples/streaming_example.py --debug
``` 