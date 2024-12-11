from dotenv import load_dotenv
import os
import streamlit as st
from crystal_service import CrystalService
from agents.crystal_agent import CrystalAgent
from agents.personality_chat_agent import PersonalityChatAgent
from swarm import Swarm
import json
import pathlib
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Swarm client
client = Swarm()

# Initialize Crystal service and agent
crystal_service = CrystalService()
crystal_agent = CrystalAgent(client)

# Add after other agent initializations
chat_agent = PersonalityChatAgent(client)

# Create profiles directory if it doesn't exist
PROFILES_DIR = pathlib.Path("profiles")
PROFILES_DIR.mkdir(exist_ok=True)

# At the top of the file, after initializing services
DEFAULT_PURPOSE = "communication"  # Add default purpose

# Function to save profile
def save_profile(profile_data: dict) -> str:
    """Save profile to disk and return filename"""
    if "data" in profile_data:
        data = profile_data["data"]
        # Create filename with just first and last name
        name = f"{data.get('first_name', 'unknown')}_{data.get('last_name', 'user')}"
        filename = f"{name}.json"
        
        # Save profile
        filepath = PROFILES_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(profile_data, f, indent=2)
        return filename
    return None

# Function to load profile
def load_profile(filename: str) -> dict:
    """Load profile from disk"""
    filepath = PROFILES_DIR / filename
    with open(filepath, 'r') as f:
        return json.load(f)

# Function to get all saved profiles
def get_saved_profiles() -> list:
    """Get list of saved profile files and return clean names"""
    profiles = []
    for f in PROFILES_DIR.glob("*.json"):
        # Remove .json extension and replace underscores with spaces
        name = f.stem.replace('_', ' ')
        profiles.append((name, f.name))  # Store both display name and filename
    return sorted(profiles)

# Set page config
st.set_page_config(
    page_title="Sales Engagement Genie",
    page_icon="🧞‍♂️",
    layout="wide",
    menu_items=None
)

# Hide Streamlit style elements
hide_st_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Create UI
st.title("🧞‍♂️ Sales Engagement Genie ✨")
st.write("Analyze personality profiles to enhance your sales conversations")

# Add settings in sidebar
with st.sidebar:
    # Profile Management
    st.subheader("Profile Management")
    saved_profiles = get_saved_profiles()
    if saved_profiles:
        # Create a list of display names and a mapping to filenames
        display_names = ["New Analysis"] + [profile[0] for profile in saved_profiles]
        filename_map = {profile[0]: profile[1] for profile in saved_profiles}
        
        selected_display = st.selectbox(
            "Select Profile",
            display_names,
            key="profile_selector"
        )
        
        # Convert display name back to filename when needed
        selected_profile = "New Analysis" if selected_display == "New Analysis" else filename_map[selected_display]
    else:
        selected_profile = "New Analysis"
        st.info("No saved profiles yet")
    
    st.divider()

# Main content area - for new analysis
if selected_profile == "New Analysis":
    linkedin_url = st.text_input(
        "Enter LinkedIn Profile URL:",
        placeholder="https://www.linkedin.com/in/username"
    )
    
    if st.button("Analyze Profile"):
        if linkedin_url:
            try:
                with st.spinner("Fetching profile data..."):
                    # Get profile data
                    profile_data = crystal_service.get_profile_by_linkedin(linkedin_url)
                    
                    # Save profile
                    filename = save_profile(profile_data)
                    if filename:
                        st.success(f"Profile saved as: {filename}")
                        # Force a rerun to update the sidebar profile list
                        st.rerun()
                    
                    # Display results in tabs
                    profile_tab, chat_tab = st.tabs([
                        "Profile Data", 
                        f"Talk to {profile_data['data'].get('first_name', 'Profile')}"
                    ])
                    
                    with profile_tab:
                        # Display results - removed tabs, just show profile data
                        if "data" in profile_data:
                            data = profile_data["data"]
                            
                            # Header with photo and basic info
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                if data.get("photo_url"):
                                    st.image(data["photo_url"], width=200)
                            with col2:
                                st.title(f"{data.get('first_name', '')} {data.get('last_name', '')}")
                                if data.get("personalities"):
                                    pers = data["personalities"]
                                    st.subheader(f"Type: {pers.get('disc_type', 'N/A')} · Archetype: {pers.get('archetype', 'N/A')}")
                                    if pers.get("myers_briggs_type"):
                                        st.write(f"Myers-Briggs: {pers['myers_briggs_type']}")
                                
                                # Display qualities as tags
                                if data.get("qualities"):
                                    st.write("Key Qualities:")
                                    cols = st.columns(len(data["qualities"]))
                                    for idx, quality in enumerate(data["qualities"]):
                                        cols[idx].markdown(f"<div style='background-color: #f0f2f6; padding: 8px; border-radius: 15px; text-align: center'>{quality}</div>", unsafe_allow_html=True)

                                # Personality Overview
                                if "content" in data and "profile" in data["content"]:
                                    st.subheader("💡 Overview")
                                    for point in data["content"]["profile"]["overview"]:
                                        st.markdown(f"• {point}")

                                # Behavioral Traits
                                if data.get("personalities", {}).get("behavioral_traits"):
                                    st.subheader("🎯 Behavioral Traits")
                                    traits = data["personalities"]["behavioral_traits"]
                                    cols = st.columns(4)
                                    for idx, (trait, value) in enumerate(traits.items()):
                                        col = cols[idx % 4]
                                        col.metric(trait, f"{value}%")
                                        
                                # DISC Profile
                                if data.get("personalities", {}).get("disc_degrees"):
                                    st.subheader("📊 DISC Profile")
                                    
                                    # Add DISC Map image if available
                                    if data.get("images", {}).get("disc_map"):
                                        st.image(data["images"]["disc_map"], width=300)
                                    
                                    # DISC metrics
                                    disc = data["personalities"]["disc_degrees"]
                                    cols = st.columns(4)
                                    for type_, value in disc.items():
                                        cols["disc".index(type_)].metric(type_.upper(), f"{value}%")

                                # Create tabs for detailed information
                                detail_tabs = st.tabs([
                                    "💪 Strengths & Motivations", 
                                    "🎯 Recommendations", 
                                    "🤝 Communication", 
                                    "💼 Sales Approach", 
                                    "🤔 Behavior & Drainers",
                                    "⚠️ Potential Blindspots"
                                ])

                                # Strengths & Motivations tab
                                with detail_tabs[0]:
                                    if "content" in data:
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown("#### Strengths")
                                            for strength in data["content"]["strengths"]["phrase"]:
                                                st.markdown(f"✓ {strength}")
                                        with col2:
                                            st.markdown("#### Motivations")
                                            for motivation in data["content"]["motivation"]["phrase"]:
                                                st.markdown(f"🎯 {motivation}")

                                # Recommendations tab
                                with detail_tabs[1]:
                                    if "content" in data and "recommendations" in data["content"]:
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown("#### Do:")
                                            for do in data["content"]["recommendations"]["do"]:
                                                st.markdown(f"✓ {do}")
                                        with col2:
                                            st.markdown("#### Don't:")
                                            for dont in data["content"]["recommendations"]["dont"]:
                                                st.markdown(f"❌ {dont}")

                                # Communication tab
                                with detail_tabs[2]:
                                    if "content" in data:
                                        # First row
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown("#### Building Trust")
                                            for point in data["content"]["building_trust"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        with col2:
                                            st.markdown("#### Communication Style")
                                            for point in data["content"]["communication"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        
                                        st.markdown("---")
                                        
                                        # Second row
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown("#### Working Together")
                                            for point in data["content"]["working_together"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        with col2:
                                            st.markdown("#### Driving Action")
                                            for point in data["content"]["driving_action"]["phrase"]:
                                                st.markdown(f"• {point}")

                                # Sales Approach tab
                                with detail_tabs[3]:
                                    if "content" in data:
                                        # First row: Meeting and First Impressions
                                        cols = st.columns(2)
                                        with cols[0]:
                                            st.markdown("#### Meeting Style")
                                            for point in data["content"]["meeting"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        with cols[1]:
                                            st.markdown("#### First Impressions")
                                            for point in data["content"]["first_impressions"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        
                                        st.markdown("---")
                                        
                                        # Second row: Selling and Following Up
                                        cols = st.columns(2)
                                        with cols[0]:
                                            st.markdown("#### Selling Approach")
                                            for point in data["content"]["selling"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        with cols[1]:
                                            st.markdown("#### Following Up")
                                            for point in data["content"]["following_up"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        
                                        st.markdown("---")
                                        
                                        # Third row: Product Demo and Pricing
                                        cols = st.columns(2)
                                        with cols[0]:
                                            st.markdown("#### Product Demo")
                                            for point in data["content"]["product_demo"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        with cols[1]:
                                            st.markdown("#### Pricing Discussion")
                                            for point in data["content"]["pricing"]["phrase"]:
                                                st.markdown(f"• {point}")
                                        
                                        st.markdown("---")
                                        
                                        # Fourth row: Negotiation
                                        st.markdown("#### Negotiation Style")
                                        for point in data["content"]["negotiating"]["phrase"]:
                                            st.markdown(f"• {point}")

                                # Behavior & Drainers tab
                                with detail_tabs[4]:
                                    if "content" in data:
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown("#### Common Behaviors")
                                            for behavior in data["content"]["behavior"]["phrase"]:
                                                st.markdown(f"• {behavior}")
                                        with col2:
                                            st.markdown("#### Energy Drainers")
                                            for drainer in data["content"]["drainer"]["phrase"]:
                                                st.markdown(f"⚠️ {drainer}")

                                # Blindspots tab
                                with detail_tabs[5]:
                                    if "content" in data and "blindspots" in data["content"]:
                                        for blindspot in data["content"]["blindspots"]["phrase"]:
                                            st.markdown(f"⚠️ {blindspot}")

                        else:
                            st.error("Invalid profile data format received")
                    
                    with chat_tab:
                        st.info(f"💬 Have a conversation with {data.get('first_name', '')} based on their personality profile")
                        
                        # Sample questions dropdown
                        question_categories = {
                            "Select a sample question...": "",
                            "Negotiation Strategy": {
                                "What concessions might appeal?": "What concessions or compromises might appeal to this personality type?",
                                "Likely walkaway point?": "What's their likely walkaway point or bottom line based on their traits?",
                                "ROI discussion approach?": "How should I frame the ROI discussion given their decision-making style?"
                            },
                            "Communication Approach": {
                                "Key resonating phrases?": "What key phrases would resonate with their communication style?",
                                "Trust building strategy?": "How can I build trust quickly with this personality type?",
                                "Communication mistakes to avoid?": "What communication style mistakes should I avoid?"
                            },
                            "Meeting & Process": {
                                "Optimal meeting format?": "What meeting format would they prefer?",
                                "Timeline for negotiations?": "What's the optimal timeline for concluding negotiations?",
                                "Pricing discussion approach?": "When and how should I discuss pricing?"
                            },
                            "Objection Handling": {
                                "Likely objections?": "What are likely objections based on their behavioral traits?",
                                "Required proof points?": "What validation or proof points would they value most?",
                                "Handling resistance?": "How do I overcome resistance while maintaining rapport?"
                            },
                            "Closing Strategy": {
                                "Best closing approach?": "What closing approach would be most effective?",
                                "Ready to move signs?": "How do I know when they're ready to move forward?",
                                "Follow-up strategy?": "What follow-up cadence would work best?"
                            }
                        }
                        
                        # Two-level selectbox for categories and questions
                        selected_category = st.selectbox(
                            "Question Category:",
                            options=list(question_categories.keys()),
                            key="category_selector"
                        )
                        
                        if selected_category != "Select a sample question..." and selected_category in question_categories:
                            selected_question = st.selectbox(
                                "Sample Question:",
                                options=list(question_categories[selected_category].keys()),
                                key="question_selector"
                            )
                            
                            if selected_question:
                                # Auto-fill the text area with the selected question
                                user_message = st.text_area(
                                    "Your message:",
                                    value=question_categories[selected_category][selected_question],
                                    placeholder="Type your message here...",
                                    key="chat_input"
                                )
                        else:
                            user_message = st.text_area(
                                "Your message:",
                                placeholder="Type your message here or select a sample question above...",
                                key="chat_input"
                            )

                        # Initialize chat history in session state if it doesn't exist
                        if "chat_history" not in st.session_state:
                            st.session_state.chat_history = []
                        
                        # Display chat history
                        for message in st.session_state.chat_history:
                            if message["role"] == "user":
                                st.write(f"You: {message['content']}")
                            else:
                                st.write(f"🧞‍♂️ {data.get('first_name', '')}: {message['content']}")
                        
                        if st.button("Send", key="send_button"):
                            if user_message:
                                # Add user message to history
                                st.session_state.chat_history.append({"role": "user", "content": user_message})
                                
                                # Create a placeholder for the streaming response
                                response_placeholder = st.empty()
                                current_response = []

                                with st.spinner(f"Getting response from {data.get('first_name', '')}..."):
                                    # Generate response using personality chat agent
                                    response_stream = chat_agent.generate_response(
                                        user_message=user_message,
                                        profile_data=profile_data,
                                        chat_history=st.session_state.chat_history
                                    )
                                    
                                    # Stream the response
                                    for chunk in response_stream:
                                        if isinstance(chunk, dict) and "content" in chunk:
                                            content = chunk["content"]
                                            if content is not None:
                                                current_response.append(content)
                                                # Update the response in real-time
                                                response_placeholder.markdown(f"🧞‍♂️ {data.get('first_name', '')}: {''.join(current_response)}")
                                        elif isinstance(chunk, str) and chunk is not None:
                                            current_response.append(chunk)
                                            # Update the response in real-time
                                            response_placeholder.markdown(f"🧞‍♂️ {data.get('first_name', '')}: {''.join(current_response)}")
                                    
                                    # Get the complete response
                                    response = "".join(current_response)
                                    
                                    # Add response to history
                                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                                    
                                    # Force a rerun to update the chat history
                                    st.rerun()

                    st.sidebar.success("✨ Analysis Complete!")
            except Exception as e:
                st.error(f"Error analyzing profile: {str(e)}")
                st.sidebar.error("❌ Analysis failed")
else:
    # Load and display saved profile
    profile_data = load_profile(selected_profile)
    
    # Display results in tabs
    profile_tab, chat_tab = st.tabs([
        "Profile Data", 
        f"Talk to {profile_data['data'].get('first_name', 'Profile')}"
    ])
    
    with profile_tab:
        # Display profile data directly without tabs
        if "data" in profile_data:
            data = profile_data["data"]
            
            # Header with photo and basic info
            col1, col2 = st.columns([1, 3])
            with col1:
                if data.get("photo_url"):
                    st.image(data["photo_url"], width=200)
            with col2:
                st.title(f"{data.get('first_name', '')} {data.get('last_name', '')}")
                if data.get("personalities"):
                    pers = data["personalities"]
                    st.subheader(f"Type: {pers.get('disc_type', 'N/A')} · Archetype: {pers.get('archetype', 'N/A')}")
                    if pers.get("myers_briggs_type"):
                        st.write(f"Myers-Briggs: {pers['myers_briggs_type']}")
                
                # Display qualities as tags
                if data.get("qualities"):
                    st.write("Key Qualities:")
                    cols = st.columns(len(data["qualities"]))
                    for idx, quality in enumerate(data["qualities"]):
                        cols[idx].markdown(f"<div style='background-color: #f0f2f6; padding: 8px; border-radius: 15px; text-align: center'>{quality}</div>", unsafe_allow_html=True)

                # Personality Overview
                if "content" in data and "profile" in data["content"]:
                    st.subheader("💡 Overview")
                    for point in data["content"]["profile"]["overview"]:
                        st.markdown(f"• {point}")

                # Behavioral Traits
                if data.get("personalities", {}).get("behavioral_traits"):
                    st.subheader("🎯 Behavioral Traits")
                    traits = data["personalities"]["behavioral_traits"]
                    cols = st.columns(4)
                    for idx, (trait, value) in enumerate(traits.items()):
                        col = cols[idx % 4]
                        col.metric(trait, f"{value}%")
                        
                # DISC Profile
                if data.get("personalities", {}).get("disc_degrees"):
                    st.subheader("📊 DISC Profile")
                    
                    # Add DISC Map image if available
                    if data.get("images", {}).get("disc_map"):
                        st.image(data["images"]["disc_map"], width=300)
                    
                    # DISC metrics
                    disc = data["personalities"]["disc_degrees"]
                    cols = st.columns(4)
                    for type_, value in disc.items():
                        cols["disc".index(type_)].metric(type_.upper(), f"{value}%")

                # Create tabs for detailed information
                detail_tabs = st.tabs([
                    "💪 Strengths & Motivations", 
                    "🎯 Recommendations", 
                    "🤝 Communication", 
                    "💼 Sales Approach", 
                    "🤔 Behavior & Drainers",
                    "⚠️ Potential Blindspots"
                ])

                # Strengths & Motivations tab
                with detail_tabs[0]:
                    if "content" in data:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### Strengths")
                            for strength in data["content"]["strengths"]["phrase"]:
                                st.markdown(f"✓ {strength}")
                        with col2:
                            st.markdown("#### Motivations")
                            for motivation in data["content"]["motivation"]["phrase"]:
                                st.markdown(f"🎯 {motivation}")

                # Recommendations tab
                with detail_tabs[1]:
                    if "content" in data and "recommendations" in data["content"]:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### Do:")
                            for do in data["content"]["recommendations"]["do"]:
                                st.markdown(f"✓ {do}")
                        with col2:
                            st.markdown("#### Don't:")
                            for dont in data["content"]["recommendations"]["dont"]:
                                st.markdown(f"❌ {dont}")

                # Communication tab
                with detail_tabs[2]:
                    if "content" in data:
                        # First row
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### Building Trust")
                            for point in data["content"]["building_trust"]["phrase"]:
                                st.markdown(f"• {point}")
                        with col2:
                            st.markdown("#### Communication Style")
                            for point in data["content"]["communication"]["phrase"]:
                                st.markdown(f"• {point}")
                        
                        st.markdown("---")
                        
                        # Second row
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### Working Together")
                            for point in data["content"]["working_together"]["phrase"]:
                                st.markdown(f"• {point}")
                        with col2:
                            st.markdown("#### Driving Action")
                            for point in data["content"]["driving_action"]["phrase"]:
                                st.markdown(f"• {point}")

                # Sales Approach tab
                with detail_tabs[3]:
                    if "content" in data:
                        # First row: Meeting and First Impressions
                        cols = st.columns(2)
                        with cols[0]:
                            st.markdown("#### Meeting Style")
                            for point in data["content"]["meeting"]["phrase"]:
                                st.markdown(f"• {point}")
                        with cols[1]:
                            st.markdown("#### First Impressions")
                            for point in data["content"]["first_impressions"]["phrase"]:
                                st.markdown(f"• {point}")
                        
                        st.markdown("---")
                        
                        # Second row: Selling and Following Up
                        cols = st.columns(2)
                        with cols[0]:
                            st.markdown("#### Selling Approach")
                            for point in data["content"]["selling"]["phrase"]:
                                st.markdown(f"• {point}")
                        with cols[1]:
                            st.markdown("#### Following Up")
                            for point in data["content"]["following_up"]["phrase"]:
                                st.markdown(f"• {point}")
                        
                        st.markdown("---")
                        
                        # Third row: Product Demo and Pricing
                        cols = st.columns(2)
                        with cols[0]:
                            st.markdown("#### Product Demo")
                            for point in data["content"]["product_demo"]["phrase"]:
                                st.markdown(f"• {point}")
                        with cols[1]:
                            st.markdown("#### Pricing Discussion")
                            for point in data["content"]["pricing"]["phrase"]:
                                st.markdown(f"• {point}")
                        
                        st.markdown("---")
                        
                        # Fourth row: Negotiation
                        st.markdown("#### Negotiation Style")
                        for point in data["content"]["negotiating"]["phrase"]:
                            st.markdown(f"• {point}")

                # Behavior & Drainers tab
                with detail_tabs[4]:
                    if "content" in data:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### Common Behaviors")
                            for behavior in data["content"]["behavior"]["phrase"]:
                                st.markdown(f"• {behavior}")
                        with col2:
                            st.markdown("#### Energy Drainers")
                            for drainer in data["content"]["drainer"]["phrase"]:
                                st.markdown(f"⚠️ {drainer}")

                # Blindspots tab
                with detail_tabs[5]:
                    if "content" in data and "blindspots" in data["content"]:
                        for blindspot in data["content"]["blindspots"]["phrase"]:
                            st.markdown(f"⚠️ {blindspot}")

        else:
            st.error("Invalid profile data format received")

    with chat_tab:
        st.info(f"💬 Have a conversation with {data.get('first_name', '')} based on their personality profile")
        
        # Sample questions dropdown
        question_categories = {
            "Select a sample question...": "",
            "Negotiation Strategy": {
                "What concessions might appeal?": "What concessions or compromises might appeal to this personality type?",
                "Likely walkaway point?": "What's their likely walkaway point or bottom line based on their traits?",
                "ROI discussion approach?": "How should I frame the ROI discussion given their decision-making style?"
            },
            "Communication Approach": {
                "Key resonating phrases?": "What key phrases would resonate with their communication style?",
                "Trust building strategy?": "How can I build trust quickly with this personality type?",
                "Communication mistakes to avoid?": "What communication style mistakes should I avoid?"
            },
            "Meeting & Process": {
                "Optimal meeting format?": "What meeting format would they prefer?",
                "Timeline for negotiations?": "What's the optimal timeline for concluding negotiations?",
                "Pricing discussion approach?": "When and how should I discuss pricing?"
            },
            "Objection Handling": {
                "Likely objections?": "What are likely objections based on their behavioral traits?",
                "Required proof points?": "What validation or proof points would they value most?",
                "Handling resistance?": "How do I overcome resistance while maintaining rapport?"
            },
            "Closing Strategy": {
                "Best closing approach?": "What closing approach would be most effective?",
                "Ready to move signs?": "How do I know when they're ready to move forward?",
                "Follow-up strategy?": "What follow-up cadence would work best?"
            }
        }
        
        # Two-level selectbox for categories and questions
        selected_category = st.selectbox(
            "Question Category:",
            options=list(question_categories.keys()),
            key="category_selector"
        )
        
        if selected_category != "Select a sample question..." and selected_category in question_categories:
            selected_question = st.selectbox(
                "Sample Question:",
                options=list(question_categories[selected_category].keys()),
                key="question_selector"
            )
            
            if selected_question:
                # Auto-fill the text area with the selected question
                user_message = st.text_area(
                    "Your message:",
                    value=question_categories[selected_category][selected_question],
                    placeholder="Type your message here...",
                    key="chat_input"
                )
        else:
            user_message = st.text_area(
                "Your message:",
                placeholder="Type your message here or select a sample question above...",
                key="chat_input"
            )

        # Initialize chat history in session state if it doesn't exist
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.write(f"You: {message['content']}")
            else:
                st.write(f"🧞‍♂️ {data.get('first_name', '')}: {message['content']}")
        
        if st.button("Send", key="send_button"):
            if user_message:
                # Add user message to history
                st.session_state.chat_history.append({"role": "user", "content": user_message})
                
                # Create a placeholder for the streaming response
                response_placeholder = st.empty()
                current_response = []

                with st.spinner(f"Getting response from {data.get('first_name', '')}..."):
                    # Generate response using personality chat agent
                    response_stream = chat_agent.generate_response(
                        user_message=user_message,
                        profile_data=profile_data,
                        chat_history=st.session_state.chat_history
                    )
                    
                    # Stream the response
                    for chunk in response_stream:
                        if isinstance(chunk, dict) and "content" in chunk:
                            content = chunk["content"]
                            if content is not None:
                                current_response.append(content)
                                # Update the response in real-time
                                response_placeholder.markdown(f"🧞‍♂️ {data.get('first_name', '')}: {''.join(current_response)}")
                        elif isinstance(chunk, str) and chunk is not None:
                            current_response.append(chunk)
                            # Update the response in real-time
                            response_placeholder.markdown(f"🧞‍♂️ {data.get('first_name', '')}: {''.join(current_response)}")
                    
                    # Get the complete response
                    response = "".join(current_response)
                    
                    # Add response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    
                    # Force a rerun to update the chat history
                    st.rerun()