from dotenv import load_dotenv
import os
import streamlit as st
from crystal_service import CrystalService
from agents.crystal_agent import CrystalAgent
from swarm import Swarm

# Load environment variables
load_dotenv()

# Initialize Swarm client
client = Swarm()

# Initialize Crystal service and agent
crystal_service = CrystalService()
crystal_agent = CrystalAgent(client)

# Set page config
st.set_page_config(
    page_title="Crystal Profile Analyzer",
    page_icon="💎",
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
st.title("Crystal Profile Analyzer")
st.write("Analyze personality profiles using Crystal Knows API")

# Add settings in sidebar
st.sidebar.title("Settings")
with st.sidebar:
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["LinkedIn Profile", "Email", "Text Analysis"],
        key="analysis_type"
    )
    
    analysis_purpose = st.selectbox(
        "Analysis Purpose",
        ["communication", "sales", "training"],
        key="purpose"
    )
    
    # Test Crystal connection
    try:
        if crystal_service.test_connection():
            st.success("✅ Crystal API connection successful!")
    except Exception as e:
        st.error(f"Crystal API Error: {str(e)}")

# Main content area
if analysis_type == "LinkedIn Profile":
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
                    
                    # Get agent analysis
                    analysis_stream = crystal_agent.analyze_profile(
                        identifier=linkedin_url,
                        identifier_type="linkedin",
                        purpose=analysis_purpose
                    )
                    
                    # Display results in tabs
                    profile_tab, analysis_tab = st.tabs(["Profile Data", "Analysis"])
                    
                    with profile_tab:
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
                                disc = data["personalities"]["disc_degrees"]
                                cols = st.columns(4)
                                for type_, value in disc.items():
                                    cols["disc".index(type_)].metric(type_.upper(), f"{value}%")

                            # Create tabs for detailed information
                            detail_tabs = st.tabs([
                                "💪 Strengths", 
                                "🎯 Recommendations", 
                                "🤝 Communication", 
                                "💼 Business", 
                                "⚠️ Potential Blindspots"
                            ])

                            # Strengths tab
                            with detail_tabs[0]:
                                if "content" in data and "strengths" in data["content"]:
                                    for strength in data["content"]["strengths"]["phrase"]:
                                        st.markdown(f"✓ {strength}")

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
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("#### Building Trust")
                                        for point in data["content"]["building_trust"]["phrase"]:
                                            st.markdown(f"• {point}")
                                    with col2:
                                        st.markdown("#### Communication Style")
                                        for point in data["content"]["communication"]["phrase"]:
                                            st.markdown(f"• {point}")

                            # Business tab
                            with detail_tabs[3]:
                                if "content" in data:
                                    cols = st.columns(2)
                                    with cols[0]:
                                        st.markdown("#### Meeting Style")
                                        for point in data["content"]["meeting"]["phrase"]:
                                            st.markdown(f"• {point}")
                                    with cols[1]:
                                        st.markdown("#### Negotiation Style")
                                        for point in data["content"]["negotiating"]["phrase"]:
                                            st.markdown(f"• {point}")

                            # Blindspots tab
                            with detail_tabs[4]:
                                if "content" in data and "blindspots" in data["content"]:
                                    for blindspot in data["content"]["blindspots"]["phrase"]:
                                        st.markdown(f"⚠️ {blindspot}")

                            # Add Crystal profile link
                            if data.get("url"):
                                st.markdown("---")
                                st.markdown(f"[View Full Crystal Profile]({data['url']})")

                        else:
                            st.error("Invalid profile data format received")
                    
                    with analysis_tab:
                        st.subheader("AI Analysis")
                        
                        # Create placeholder for streaming content
                        analysis_placeholder = st.empty()
                        full_analysis = []
                        
                        # Stream analysis content with None check
                        for chunk in analysis_stream:
                            if isinstance(chunk, dict) and "content" in chunk:
                                content = chunk["content"]
                                if content is not None:  # Add None check
                                    full_analysis.append(content)
                            elif isinstance(chunk, str) and chunk is not None:  # Add None check
                                full_analysis.append(chunk)
                            
                            # Only update if we have content
                            if full_analysis:
                                analysis_placeholder.markdown(''.join(full_analysis))
                        
                        # Only add download button if we have content
                        if full_analysis:
                            st.download_button(
                                "Download Analysis",
                                ''.join(full_analysis),
                                file_name="crystal_analysis.txt",
                                mime="text/plain"
                            )
                
                st.sidebar.success("✨ Analysis Complete!")
                
            except Exception as e:
                st.error(f"Error analyzing profile: {str(e)}")
                st.sidebar.error("❌ Analysis failed")

elif analysis_type == "Email":
    email = st.text_input(
        "Enter Email Address:",
        placeholder="example@domain.com"
    )
    
    if st.button("Analyze Profile"):
        if email:
            try:
                with st.spinner("Fetching profile data..."):
                    # Get profile data
                    profile_data = crystal_service.get_profile_by_email(email)
                    
                    # Get agent analysis
                    analysis_stream = crystal_agent.analyze_profile(
                        identifier=email,
                        identifier_type="email",
                        purpose=analysis_purpose
                    )
                    
                    # Display results in tabs
                    profile_tab, analysis_tab = st.tabs(["Profile Data", "Analysis"])
                    
                    with profile_tab:
                        st.subheader("Crystal Profile Data")
                        st.json(profile_data)
                    
                    with analysis_tab:
                        st.subheader("AI Analysis")
                        analysis_placeholder = st.empty()
                        full_analysis = []
                        
                        # Stream analysis content with None check
                        for chunk in analysis_stream:
                            if isinstance(chunk, dict) and "content" in chunk:
                                content = chunk["content"]
                                if content is not None:
                                    full_analysis.append(content)
                            elif isinstance(chunk, str) and chunk is not None:
                                full_analysis.append(chunk)
                            
                            if full_analysis:
                                analysis_placeholder.markdown(''.join(full_analysis))
                        
                        if full_analysis:
                            st.download_button(
                                "Download Analysis",
                                ''.join(full_analysis),
                                file_name="crystal_analysis.txt",
                                mime="text/plain"
                            )
                
                st.sidebar.success("✨ Analysis Complete!")
                
            except Exception as e:
                st.error(f"Error analyzing profile: {str(e)}")
                st.sidebar.error("❌ Analysis failed")

else:  # Text Analysis
    text_input = st.text_area(
        "Enter Text to Analyze:",
        placeholder="Enter text content for personality analysis...",
        height=200
    )
    
    metadata = st.text_input(
        "Optional Metadata (JSON):",
        placeholder='{"context": "job_application", "role": "developer"}'
    )
    
    if st.button("Analyze Text"):
        if text_input:
            try:
                with st.spinner("Analyzing text..."):
                    # Parse metadata if provided
                    metadata_dict = json.loads(metadata) if metadata else None
                    
                    # Analyze text
                    analysis_result = crystal_service.analyze_text(
                        text=text_input,
                        metadata=metadata_dict
                    )
                    
                    # Display results
                    st.subheader("Text Analysis Results")
                    st.json(analysis_result)
                    
            except Exception as e:
                st.error(f"Error analyzing text: {str(e)}")

# Add helpful information
with st.expander("ℹ️ About Crystal Profile Analysis"):
    st.write("""
    This tool uses Crystal Knows API to analyze personality profiles based on:
    - LinkedIn profiles
    - Email addresses
    - Text content
    
    The analysis provides insights into:
    - DISC personality type
    - Communication style
    - Core values
    - Work preferences
    - Personality traits
    
    Use this information to better understand and communicate with others.
    """) 