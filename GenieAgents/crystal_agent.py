"""Crystal Knows Personality Analysis Agent"""
from typing import Dict, List, Any, Union, Optional, Generator
from pydantic import BaseModel
import asyncio
import json

# Import our local BaseAgent class
from .base_agent import BaseAgent
# Import directly from openai_agents
from openai_agents import trace, Runner

class PersonalityProfileOutput(BaseModel):
    """Structured output for personality profile analysis"""
    personality_type: str
    traits: List[str]
    communication_tips: List[str]
    work_preferences: List[str]
    metadata: Optional[Dict[str, Any]] = None

class CrystalAgent(BaseAgent):
    """Agent for personality analysis using Crystal Knows methodology"""
    
    INSTRUCTIONS = """You are a personality analysis specialist using Crystal Knows methodology.
    Analyze the provided text or profile information to determine:
    1. DISC personality type (Dominant, Influential, Steady, or Conscientious)
    2. Key personality traits and characteristics
    3. Communication preferences and tips
    4. Work style and collaboration preferences
    """

    def __init__(self):
        """Initialize the CrystalAgent"""
        super().__init__(
            name="Crystal Personality Analyzer",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=PersonalityProfileOutput
        )

    async def analyze_profile(
        self,
        identifier: str,
        identifier_type: str = "text",
        purpose: str = "communication",
        metadata: Optional[Dict] = None
    ) -> PersonalityProfileOutput:
        """Analyze a personality profile based on text or other identifiers
        
        Args:
            identifier: The text or identifier to analyze
            identifier_type: Type of identifier (text, email, linkedin)
            purpose: Purpose of analysis (communication, sales, training)
            metadata: Optional metadata for the analysis
            
        Returns:
            Personality profile analysis
        """
        with trace("Personality Analysis"):
            analysis_prompt = self._construct_analysis_prompt(
                identifier, identifier_type, purpose, metadata or {}
            )
            return await self.run(analysis_prompt)
    
    def _construct_analysis_prompt(
        self,
        identifier: str,
        identifier_type: str,
        purpose: str,
        metadata: Dict
    ) -> str:
        """Construct the personality analysis prompt
        
        Args:
            identifier: The text or identifier to analyze
            identifier_type: Type of identifier
            purpose: Purpose of analysis
            metadata: Additional metadata
            
        Returns:
            Formatted prompt for personality analysis
        """
        return f"""
        Please analyze the following {identifier_type} for personality insights:
        
        {identifier}
        
        Purpose of analysis: {purpose}
        
        Additional context: {json.dumps(metadata) if metadata else "None"}
        
        Provide a detailed personality profile including DISC type, key traits, 
        communication preferences, and work style.
        """ 