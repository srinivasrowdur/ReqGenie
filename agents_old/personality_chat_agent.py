"""Personality-based Chat Agent"""
from typing import Dict, List, Any, Union, Optional, Generator
from pydantic import BaseModel
import asyncio

# Import our local BaseAgent class
from .base_agent import BaseAgent
# Import directly from openai_agents
from openai_agents import trace, Runner

class ChatResponseOutput(BaseModel):
    """Structured output for chat responses"""
    message: str
    communication_tips: List[str]
    suggested_phrases: List[str]
    metadata: Dict[str, Any] = {}

class PersonalityChatAgent(BaseAgent):
    """Agent for personality-based communication advice"""
    
    INSTRUCTIONS = """You are an AI sales communication advisor helping users interact effectively with the profiled person.
    You MUST:
    1. Provide strategic communication advice based on the person's DISC type and behavioral traits
    2. Suggest persuasive approaches that align with their motivations and values
    3. Recommend negotiation tactics that match their business style
    4. Highlight potential objections and how to address them
    5. Guide timing and pacing based on their preferences
    6. Offer specific phrases and approaches that would resonate
    
    Format your responses in a clear, actionable way that helps the user improve their communication strategy."""

    def __init__(self):
        """Initialize the PersonalityChatAgent"""
        super().__init__(
            name="Sales Communication Advisor",
            instructions=self.INSTRUCTIONS,
            model="gpt-4o-mini",
            structured_output=ChatResponseOutput
        )

    async def generate_response(
        self,
        user_message: str,
        profile_data: Dict,
        chat_history: List = None
    ) -> ChatResponseOutput:
        """Generate a response based on personality profile data
        
        Args:
            user_message: The user's message
            profile_data: Personality profile data
            chat_history: Optional chat history
            
        Returns:
            Structured chat response
        """
        with trace("Personality-Based Chat Response"):
            # Build the context from the personality profile
            personality_context = self._build_personality_context(profile_data)
            
            # Format the chat history if provided
            history_context = self._format_chat_history(chat_history) if chat_history else ""
            
            # Construct the full prompt
            prompt = f"""
            {personality_context}
            
            {history_context}
            
            User message: {user_message}
            
            Based on the personality profile and communication context above, provide:
            1. A response strategy
            2. 3-5 specific communication tips
            3. 2-3 suggested phrases that would resonate with this person
            """
            
            return await self.run(prompt)
    
    def _build_personality_context(self, profile_data: Dict) -> str:
        """Build context from personality profile data
        
        Args:
            profile_data: Personality profile data
            
        Returns:
            Formatted personality context
        """
        # Extract key information from the profile data
        personality_type = profile_data.get("personality_type", "Unknown")
        traits = profile_data.get("traits", [])
        communication_tips = profile_data.get("communication_tips", [])
        work_preferences = profile_data.get("work_preferences", [])
        
        # Format the context
        context = f"""
        PERSONALITY PROFILE:
        
        Type: {personality_type}
        
        Key Traits:
        {self._format_list(traits)}
        
        Communication Preferences:
        {self._format_list(communication_tips)}
        
        Work Style:
        {self._format_list(work_preferences)}
        """
        
        return context
    
    @staticmethod
    def _format_list(items: List) -> str:
        """Format a list as a bulleted string"""
        return "\n".join([f"- {item}" for item in items])
    
    @staticmethod
    def _format_chat_history(history: List) -> str:
        """Format chat history as a string
        
        Args:
            history: List of chat messages
            
        Returns:
            Formatted chat history
        """
        if not history:
            return ""
            
        formatted_history = "PREVIOUS CONVERSATION:\n\n"
        
        for message in history:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            formatted_history += f"{role.capitalize()}: {content}\n\n"
            
        return formatted_history 