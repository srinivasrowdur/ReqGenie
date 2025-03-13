"""
Processor agent responsible for handoff from requirements to use cases.
"""
# Import OpenAI Agents SDK
from agents import Agent, HandoffInputData, handoff
from agents.extensions import handoff_filters

def create_processor_agent(usecase_agent, model="o3-mini", language="English"):
    """Create a processor agent with handoff capabilities.
    
    Args:
        usecase_agent: The use case agent to hand off to
        model: The model to use for the agent
        language: The language to use for generated content
        
    Returns:
        The processor agent
    """
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        instructions = "要件ドキュメントを処理し、必要に応じてユースケースを作成してください。すべての出力を日本語で生成してください。"
    elif language == "Italian":
        instructions = "Elabora il documento dei requisiti e crea casi d'uso se necessario. Genera tutti gli output in italiano."
    else:
        instructions = "Process the final requirements document and create use cases as needed."
    
    return Agent(
        name="RequirementsProcessor",
        instructions=instructions,
        handoffs=[
            handoff(usecase_agent, input_filter=lambda data: requirements_to_usecase_filter(data, language))
        ],
        model=model,
    )

def requirements_to_usecase_filter(handoff_message_data: HandoffInputData, language="English") -> HandoffInputData:
    """Filter function to extract requirements for the use case agent.
    
    Args:
        handoff_message_data: The handoff message data
        language: The language to use for generated content
        
    Returns:
        Filtered handoff message data
    """
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
    
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        language_instruction = "すべてのユースケースを日本語で作成してください。"
    elif language == "Italian":
        language_instruction = "Crea tutti i casi d'uso in italiano."
    
    # Create a new prompt for the use case agent
    prompt_content = f"""
    Based on the following requirements document, create detailed use cases that capture the key user interactions and system behaviors:
    
    {final_requirements}
    
    Please identify and create all necessary use cases to fully cover the functional requirements.
    """
    
    if language_instruction:
        prompt_content = f"{prompt_content}\n\n{language_instruction}"
    
    new_prompt = {
        "role": "user",
        "content": prompt_content
    }
    
    # Return just the new prompt
    return HandoffInputData(
        input_history=tuple([new_prompt]),
        pre_handoff_items=tuple(),
        new_items=tuple(),
    ) 