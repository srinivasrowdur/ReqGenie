"""
Use case creation agent responsible for generating detailed use cases from requirements.
"""
# Import OpenAI Agents SDK
from agents import Agent
from prompts.usecase_prompt import USECASE_SYSTEM_PROMPT

def create_usecase_agent(model="o3-mini", language="English"):
    """Create a use case agent.
    
    Args:
        model: The model to use for the agent
        language: The language to use for generated content
        
    Returns:
        The use case agent
    """
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        language_instruction = """
        すべてのユースケースを日本語で生成してください。
        タイトル、説明、ステップ、代替フロー、前提条件などすべての内容を日本語で作成してください。
        """
    elif language == "Italian":
        language_instruction = """
        Genera tutti i casi d'uso in italiano.
        Titoli, descrizioni, passi, flussi alternativi, precondizioni e tutti gli altri contenuti devono essere in italiano.
        """
    
    # Combine original instructions with language-specific ones
    instructions = USECASE_SYSTEM_PROMPT
    if language_instruction:
        instructions = f"{instructions}\n\n{language_instruction}"
    
    return Agent(
        name="UseCaseCreator",
        instructions=instructions,
        model=model,
    )
    
def create_usecase_prompt(requirements_doc, language="English"):
    """Create a prompt for generating use cases from a requirements document.
    
    Args:
        requirements_doc: The requirements document to generate use cases from
        language: The language to use for generated content
        
    Returns:
        The use case prompt
    """
    language_instruction = ""
    if language != "English":
        if language == "Japanese":
            language_instruction = "すべてのユースケースを日本語で作成してください。"
        elif language == "Italian":
            language_instruction = "Crea tutti i casi d'uso in italiano."
    
    prompt = f"""
    Based on the following requirements document, create detailed use cases that capture the key user interactions and system behaviors:
    
    {requirements_doc}
    
    Please identify and create all necessary use cases to fully cover the functional requirements.
    """
    
    if language_instruction:
        prompt = f"{prompt}\n\n{language_instruction}"
    
    return prompt 