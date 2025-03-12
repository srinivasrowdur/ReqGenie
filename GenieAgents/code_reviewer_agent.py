"""Code Reviewer Agent"""
from typing import Dict, List, Any, Union, Optional
from pydantic import BaseModel
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent
# Import directly from agents package
from agents import trace, Runner

class CodeReviewOutput(BaseModel):
    """Structured output for code review"""
    quality_score: int  # 1-10
    maintainability_score: int  # 1-10
    security_score: int  # 1-10
    performance_score: int  # 1-10
    issues: Optional[List[Dict[str, str]]] = None
    recommendations: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class CodeReviewerAgent(BaseAgent):
    """Agent for reviewing code quality and providing feedback"""
    
    INSTRUCTIONS = """You are an expert code reviewer. Your task is to:
        1. Analyze the generated code against requirements
        2. Identify quality issues, bugs, and vulnerabilities
        3. Suggest improvements for better performance and maintainability
        4. Check if all requirements are implemented correctly
        5. Provide constructive feedback"""

    def __init__(self):
        """Initialize the CodeReviewerAgent"""
        super().__init__(
            name="Code Reviewer",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=CodeReviewOutput
        )
        
        # Create a judge agent for providing final scores
        self.judge_agent = BaseAgent(
            name="Code Quality Judge",
            instructions="""You are a senior code quality judge.
            Evaluate the code review provided and assign scores from 1-10 for each category.
            Be critical but fair in your assessment.""",
            model="gpt-4o"
        )

    async def review(self, code: str) -> CodeReviewOutput:
        """Review the generated code for quality and correctness
        
        Args:
            code: The generated code
            
        Returns:
            Code review output
        """
        with trace("Code Review"):
            review_prompt = self._construct_review_prompt(code)
            review_result = await self.run(review_prompt)
            
            # If already structured, return directly
            if isinstance(review_result, CodeReviewOutput):
                return review_result
                
            # Otherwise, pass to judge for scoring
            with trace("Judge Evaluation"):
                judge_prompt = f"""
                Code:
                ```
                {code[:1000]}... [truncated for brevity]
                ```
                
                Review:
                {review_result}
                
                Please evaluate this code review and provide scores from 1-10 for:
                1. Quality (how well the code is written)
                2. Maintainability (how easy it is to maintain)
                3. Security (how secure the code is)
                4. Performance (how efficiently the code runs)
                
                For each issue identified, provide specific recommendations for improvement.
                """
                
                return await self.judge_agent.run(judge_prompt)
    
    def _construct_review_prompt(self, code: str) -> str:
        """Construct the code review prompt
        
        Args:
            code: The generated code
            
        Returns:
            Formatted prompt for code review
        """
        return f"""
        Review the following code thoroughly:
        
        ```
        {code}
        ```
        
        Provide a comprehensive code review that includes:
        
        1. Code Quality: Assess the overall quality, readability, and structure
        2. Bug Detection: Identify potential bugs or logic errors
        3. Security Analysis: Check for security vulnerabilities
        4. Performance Evaluation: Identify performance issues or bottlenecks
        5. Best Practices: Check if code follows language-specific best practices
        6. Improvement Suggestions: Specific suggestions to improve the code
        
        Format your review as a detailed report that a developer can use to improve the code.
        """ 