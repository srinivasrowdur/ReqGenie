"""
Requirements evaluator agent responsible for evaluating and providing feedback on requirements documents.
"""
# Import OpenAI Agents SDK
from agents import Agent
from prompts.evaluator_prompt import EVALUATOR_SYSTEM_PROMPT
from models.requirements_evaluation import RequirementsEvaluation

def create_evaluator_agent(model="o3-mini", language="English"):
    """Create a requirements evaluator agent.
    
    Args:
        model: The model to use for the agent
        language: The language to use for generated content
        
    Returns:
        The evaluator agent
    """
    # Add language-specific instructions
    language_instruction = ""
    if language == "Japanese":
        language_instruction = """
        すべてのフィードバックを日本語で提供してください。
        評価結果、改善点、具体的なフィードバックはすべて日本語で記述してください。
        """
    elif language == "Italian":
        language_instruction = """
        Fornisci tutti i feedback in italiano.
        I risultati della valutazione, le aree di miglioramento e i feedback specifici devono essere tutti in italiano.
        """
    
    # Combine original instructions with language-specific ones
    instructions = EVALUATOR_SYSTEM_PROMPT
    if language_instruction:
        instructions = f"{instructions}\n\n{language_instruction}"
    
    return Agent[RequirementsEvaluation](
        name="RequirementsEvaluator",
        instructions=instructions,
        output_type=RequirementsEvaluation,
        model=model,
    )
    
def create_evaluation_prompt(requirements_doc, language="English"):
    """Create a prompt for evaluating a requirements document.
    
    Args:
        requirements_doc: The requirements document to evaluate
        language: The language to use for generated content
        
    Returns:
        The evaluation prompt
    """
    language_instruction = ""
    if language != "English":
        if language == "Japanese":
            language_instruction = "評価結果を日本語で提供してください。"
        elif language == "Italian":
            language_instruction = "Fornisci la valutazione in italiano."
    
    prompt = f"Review this requirements document:\n\n{requirements_doc}"
    
    if language_instruction:
        prompt = f"{prompt}\n\n{language_instruction}"
    
    return prompt
    
def create_feedback_prompt(evaluation, original_prompt, language="English"):
    """Create a prompt for incorporating feedback into a requirements document.
    
    Args:
        evaluation: The evaluation result
        original_prompt: The original prompt used to generate the requirements
        language: The language to use for generated content
        
    Returns:
        The feedback prompt
    """
    improvement_areas_text = ""
    for area in evaluation.improvement_areas:
        improvement_areas_text += f"- {area}\n"
    
    language_instruction = ""
    if language != "English":
        if language == "Japanese":
            language_instruction = "改善された要件ドキュメントを日本語で提供してください。"
        elif language == "Italian":
            language_instruction = "Fornisci il documento dei requisiti migliorato in italiano."
    
    prompt = f"""
    Please improve the requirements document based on this feedback:
    
    {evaluation.feedback}
    
    Areas to improve:
    {improvement_areas_text}
    """
    
    if language_instruction:
        prompt = f"{prompt}\n\n{language_instruction}"
    
    return prompt 