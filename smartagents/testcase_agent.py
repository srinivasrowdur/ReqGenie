"""
Test case generator agent responsible for creating comprehensive test cases from requirements.
"""
# Import OpenAI Agents SDK
from agents import Agent
from prompts.testcase_prompt import TESTCASE_SYSTEM_PROMPT

def create_testcase_agent(model="o3-mini", language="English"):
    """Create a test case generator agent.
    
    Args:
        model: The model to use for the agent
        language: The language to use for generated content
        
    Returns:
        The test case generator agent
    """
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        language_instruction = """
        すべてのテストケースを日本語で生成してください。
        テスト目的、ステップ、期待される結果、テストデータなどすべての内容を日本語で作成してください。
        """
    elif language == "Italian":
        language_instruction = """
        Genera tutti i casi di test in italiano.
        Obiettivi del test, passi, risultati attesi, dati di test e tutti gli altri contenuti devono essere in italiano.
        """
    
    # Combine original instructions with language-specific ones
    instructions = TESTCASE_SYSTEM_PROMPT
    if language_instruction:
        instructions = f"{instructions}\n\n{language_instruction}"
    
    return Agent(
        name="TestCaseGenerator",
        instructions=instructions,
        model=model,
    )
    
def create_testcase_prompt(requirements_doc, language="English"):
    """Create a prompt for generating test cases from a requirements document.
    
    Args:
        requirements_doc: The requirements document to generate test cases from
        language: The language to use for generated content
        
    Returns:
        The test case prompt
    """
    language_instruction = ""
    if language != "English":
        if language == "Japanese":
            language_instruction = "すべてのテストケースを日本語で作成してください。"
        elif language == "Italian":
            language_instruction = "Crea tutti i casi di test in italiano."
    
    prompt = f"""
    Based on the following requirements document, create comprehensive test cases that verify all functional and non-functional requirements:
    
    {requirements_doc}
    
    Please ensure test cases have clear steps, expected results, and cover both positive and negative scenarios.
    """
    
    if language_instruction:
        prompt = f"{prompt}\n\n{language_instruction}"
    
    return prompt 