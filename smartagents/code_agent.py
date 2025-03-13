"""
Code generator agent responsible for creating sample code implementations from requirements.
"""
# Import OpenAI Agents SDK
from agents import Agent
from prompts.code_prompt import CODE_SYSTEM_PROMPT

def create_code_agent(model="o3-mini", language="English"):
    """Create a code generator agent.
    
    Args:
        model: The model to use for the agent
        language: The language to use for generated content
        
    Returns:
        The code generator agent
    """
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        language_instruction = """
        コードのコメントやドキュメントを日本語で生成してください。
        変数名やクラス名などのコード自体は適切なプログラミング規約に従ってください。
        README.mdやドキュメンテーションは日本語で提供してください。
        """
    elif language == "Italian":
        language_instruction = """
        Genera i commenti nel codice e la documentazione in italiano.
        Il codice stesso (nomi di variabili, classi, ecc.) dovrebbe seguire le convenzioni di programmazione appropriate.
        Fornisci il README.md e la documentazione in italiano.
        """
    
    # Combine original instructions with language-specific ones
    instructions = CODE_SYSTEM_PROMPT
    if language_instruction:
        instructions = f"{instructions}\n\n{language_instruction}"
    
    return Agent(
        name="CodeGenerator",
        instructions=instructions,
        model=model,
    )
    
def create_code_prompt(requirements_doc, app_type, language="English"):
    """Create a prompt for generating code from a requirements document.
    
    Args:
        requirements_doc: The requirements document to generate code from
        app_type: The type of application
        language: The language to use for generated content
        
    Returns:
        The code prompt
    """
    language_instruction = ""
    if language != "English":
        if language == "Japanese":
            language_instruction = """
            コードのコメントとドキュメンテーション（README.mdを含む）を日本語で作成してください。
            コード自体（変数名、関数名など）は適切なプログラミング規約に従ってください。
            """
        elif language == "Italian":
            language_instruction = """
            Crea commenti nel codice e documentazione (incluso README.md) in italiano.
            Il codice stesso (nomi di variabili, funzioni, ecc.) dovrebbe seguire le convenzioni di programmazione appropriate.
            """
    
    prompt = f"""
    Based on the following requirements document, generate sample code that implements the key functionality:
    
    {requirements_doc}
    
    Application Type: {app_type}
    
    Please provide well-structured, commented code that follows best practices for the specified application type.
    Include a README.md with instructions for setup and an explanation of the code structure.
    """
    
    if language_instruction:
        prompt = f"{prompt}\n\n{language_instruction}"
    
    return prompt 