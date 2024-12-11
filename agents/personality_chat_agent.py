"""Personality-based Chat Agent"""
from swarm import Agent, Swarm
from typing import Generator

class PersonalityChatAgent:
    INSTRUCTIONS = """You are an AI sales communication advisor helping users interact effectively with the profiled person.
    You MUST:
    1. Provide strategic communication advice based on the person's DISC type and behavioral traits
    2. Suggest persuasive approaches that align with their motivations and values
    3. Recommend negotiation tactics that match their business style
    4. Highlight potential objections and how to address them
    5. Guide timing and pacing based on their preferences
    6. Offer specific phrases and approaches that would resonate
    
    Format your responses in a clear, actionable way that helps the user improve their communication strategy."""

    def __init__(self, client: Swarm):
        self.agent = Agent(
            name="Sales Communication Advisor",
            instructions=self.INSTRUCTIONS,
            model="gpt-4"
        )
        self.client = client

    def generate_response(
        self,
        user_message: str,
        profile_data: dict,
        chat_history: list = None
    ) -> Generator:
        """Generate strategic communication advice based on personality profile."""
        
        # Get data safely
        data = profile_data.get('data', {})
        personalities = data.get('personalities', {})
        
        # Extract key personality aspects
        personality_context = self._build_personality_context(profile_data)
        
        chat_prompt = f"""
        PERSONALITY PROFILE:
        {personality_context}

        USER MESSAGE: {user_message}

        PREVIOUS CONVERSATION:
        {self._format_chat_history(chat_history) if chat_history else 'No previous messages'}

        Provide strategic advice that:
        1. Aligns with their {personalities.get('disc_type', 'unknown')} communication preferences
        2. Considers their {personalities.get('archetype', 'unknown')} archetype tendencies
        3. Leverages their behavioral traits and motivations
        4. Matches their business and negotiation style
        5. Addresses potential objections or concerns

        Here are some strategic questions you can ask to improve your sales approach:

        Negotiation Strategy:
        • "What concessions or compromises might appeal to this personality type?"
        • "What's their likely walkaway point or bottom line based on their traits?"
        • "How should I frame the ROI discussion given their decision-making style?"
        • "What negotiation tactics should I avoid with this personality?"

        Communication Approach:
        • "What key phrases would resonate with their communication style?"
        • "How should I structure my pitch considering their DISC type?"
        • "What communication style mistakes should I avoid?"
        • "How can I build trust quickly with this personality type?"

        Meeting & Process:
        • "What meeting format would they prefer?"
        • "How should I pace the conversation given their preferences?"
        • "What's the optimal timeline for concluding negotiations?"
        • "When and how should I discuss pricing?"

        Objection Handling:
        • "What are likely objections based on their behavioral traits?"
        • "How should I address concerns about [specific aspect]?"
        • "What validation or proof points would they value most?"
        • "How do I overcome resistance while maintaining rapport?"

        Closing Strategy:
        • "What closing approach would be most effective?"
        • "What follow-up cadence would work best?"
        • "How do I know when they're ready to move forward?"
        • "What signs indicate they're not fully convinced?"

        Provide specific, actionable advice that helps the user communicate more effectively with {data.get('first_name', 'unknown')}.
        """

        return self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": chat_prompt}],
            stream=True
        )

    def _build_personality_context(self, profile_data: dict) -> str:
        """Build a comprehensive personality context from profile data."""
        data = profile_data.get("data", {})
        personalities = data.get("personalities", {})
        content = data.get("content", {})
        
        context = f"""
        CORE TRAITS:
        - DISC Type: {personalities.get('disc_type')}
        - Archetype: {personalities.get('archetype')}
        - Myers-Briggs: {personalities.get('myers_briggs_type')}
        
        COMMUNICATION STYLE:
        {self._format_list(content.get('communication', {}).get('phrase', []))}
        
        BEHAVIORAL TRAITS:
        {self._format_dict(personalities.get('behavioral_traits', {}))}
        
        STRENGTHS:
        {self._format_list(content.get('strengths', {}).get('phrase', []))}
        
        MOTIVATIONS:
        {self._format_list(content.get('motivation', {}).get('phrase', []))}
        
        COMMUNICATION PREFERENCES:
        - Building Trust: {self._format_list(content.get('building_trust', {}).get('phrase', []))}
        - Working Together: {self._format_list(content.get('working_together', {}).get('phrase', []))}
        
        BUSINESS STYLE:
        - Meeting Style: {self._format_list(content.get('meeting', {}).get('phrase', []))}
        - Negotiation: {self._format_list(content.get('negotiating', {}).get('phrase', []))}
        """
        return context

    @staticmethod
    def _format_list(items: list) -> str:
        """Format a list of items into a bullet-point string."""
        return "\n".join([f"- {item}" for item in items]) if items else "N/A"

    @staticmethod
    def _format_dict(data: dict) -> str:
        """Format a dictionary into a bullet-point string."""
        return "\n".join([f"- {k}: {v}" for k, v in data.items()]) if data else "N/A"

    @staticmethod
    def _format_chat_history(history: list) -> str:
        """Format chat history into a readable string."""
        if not history:
            return ""
        return "\n".join([f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}" 
                         for msg in history]) 