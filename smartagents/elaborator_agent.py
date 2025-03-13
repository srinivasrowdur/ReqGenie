"""
Requirements elaborator agent responsible for creating detailed requirements documents.
"""
# Import OpenAI Agents SDK
from agents import Agent
from prompts.elaborator_prompt import REQUIREMENTS_SYSTEM_PROMPT

def create_elaborator_agent(model="o3-mini", language="English"):
    """Create a requirements elaborator agent.
    
    Args:
        model: The model to use for the agent
        language: The language to use for generated content
        
    Returns:
        The elaborator agent
    """
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        language_instruction = """
        すべてのコンテンツを日本語で生成してください。
        要件ドキュメントは完全に日本語で作成し、専門用語も適切に日本語に翻訳してください。
        """
    elif language == "Italian":
        language_instruction = """
        Genera tutti i contenuti in italiano.
        Il documento dei requisiti deve essere completamente in italiano, con i termini tecnici tradotti appropriatamente.
        """
    
    # Combine original instructions with language-specific ones
    instructions = REQUIREMENTS_SYSTEM_PROMPT
    if language_instruction:
        instructions = f"{instructions}\n\n{language_instruction}"
    
    return Agent(
        name="RequirementsElaborator",
        instructions=instructions,
        model=model,
    )
    
def create_elaboration_prompt(requirement, app_type, language="English"):
    """Create a prompt for elaborating a requirement.
    
    Args:
        requirement: The requirement to elaborate
        app_type: The type of application
        language: The language to use for generated content
        
    Returns:
        The elaboration prompt
    """
    language_instruction = ""
    if language != "English":
        if language == "Japanese":
            language_instruction = "すべての出力を日本語で生成してください。"
        elif language == "Italian":
            language_instruction = "Genera tutti gli output in italiano."
    
    prompt = f"""
    Brief Requirement: {requirement}
    Application Type: {app_type}
    
    Please elaborate this brief requirement into a detailed functional requirements document.
    """
    
    if language_instruction:
        prompt = f"{prompt}\n\n{language_instruction}"
    
    return prompt 