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
import pandas as pd
import altair as alt

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

# Add custom CSS for modern styling
st.markdown("""
<style>
    /* Modern styling */
    .stApp {
        background-color: #f8f9fa;
    }
    .main {
        padding: 2rem;
    }
    /* Profile card styling */
    .profile-card {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Metric styling */
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    /* Tag styling */
    .tag {
        background-color: #e9ecef;
        padding: 0.4rem 1rem;
        border-radius: 15px;
        display: inline-block;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    /* Section headers */
    .section-header {
        color: #495057;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
    }
    /* Profile confidence badge */
    .confidence-badge {
        background-color: #e7f3ff;
        color: #0366d6;
        padding: 0.4rem 1rem;
        border-radius: 15px;
        float: right;
        font-size: 0.9rem;
    }
    /* List items */
    .list-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #f1f3f5;
    }
    .list-item:last-child {
        border-bottom: none;
    }
    /* Hide Streamlit components */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Additional styles for new components */
    .tip-card {
        background: white;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }
    .tip-number {
        background: #0366d6;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
    }
    .timeline-item {
        display: flex;
        margin: 1rem 0;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .timeline-marker {
        color: #0366d6;
        margin-right: 1rem;
        font-size: 1.2rem;
    }
    .nego-card {
        background: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .strategy-card {
        background: white;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .strategy-content {
        display: flex;
        align-items: center;
    }
    .strategy-icon {
        margin-right: 1rem;
        font-size: 1.5rem;
    }
    /* Sidebar styling */
    .sidebar-profile {
        padding: 1rem;
        background: white;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
    }
    .sidebar-nav {
        margin-top: 1rem;
    }
    .sidebar-nav label {
        font-weight: 600;
        color: #1f2937;
    }
    /* Main content area */
    .main-content {
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Chart container */
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Sales card styling */
    .sales-card, .demo-card, .pricing-card, .trust-card {
        background: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }
    .sales-icon, .demo-icon, .pricing-icon, .trust-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
        min-width: 2rem;
        text-align: center;
    }
    /* Add different background colors for different card types */
    .sales-card { border-left: 4px solid #0366d6; }
    .demo-card { border-left: 4px solid #2ea44f; }
    .pricing-card { border-left: 4px solid #d73a49; }
    .trust-card { border-left: 4px solid #6f42c1; }
    /* Additional card styles */
    .action-card, .collab-card, .followup-card {
        background: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }
    .action-icon, .collab-icon, .followup-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
        min-width: 2rem;
        text-align: center;
    }
    /* Unique border colors for each type */
    .action-card { border-left: 4px solid #ff9800; }
    .collab-card { border-left: 4px solid #4caf50; }
    .followup-card { border-left: 4px solid #9c27b0; }
    /* Enhanced sidebar styling */
    .sidebar-profile {
        background: linear-gradient(to bottom right, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        text-align: center;
    }
    .sidebar-nav {
        margin-top: 2rem;
    }
    .sidebar-nav h3 {
        color: #1a1f36;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        padding-left: 0.5rem;
    }
    /* Section header styling */
    .section-header {
        background: linear-gradient(90deg, #0366d6 0%, #0378d6 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(3, 102, 214, 0.2);
    }
    .impression-card {
        background: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        border-left: 4px solid #00bcd4;
    }
    .impression-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
        min-width: 2rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

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

def display_profile_content(data: dict, section: str):
    """Common function to display profile content based on selected section"""
    content = data.get('content', {})
    
    # Helper function to safely get phrases
    def get_phrases(key):
        return content.get(key, {}).get('phrase', [])
    
    # Helper function to display cards
    def display_cards(points, card_class, icon, icon_class):
        if points:
            for point in points:
                st.markdown(f"""
                    <div class="{card_class}">
                        <div class="{icon_class}">{icon}</div>
                        <div class="{card_class}-content">{point}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No data available for this section")

    if section == "Behavioral Traits":
        st.markdown("## Behavioral Traits")
        if data.get("personalities", {}).get("behavioral_traits"):
            traits = data["personalities"]["behavioral_traits"]
            
            # Create DataFrame for chart
            chart_data = pd.DataFrame({
                'Trait': list(traits.keys()),
                'Value': list(traits.values())
            })
            
            # Base chart configuration
            base = alt.Chart(chart_data).encode(
                x=alt.X('Value:Q', 
                    scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(grid=False)
                ),
                y=alt.Y('Trait:N', 
                    sort='-x',
                    axis=alt.Axis(grid=False)
                )
            ).properties(
                height=400
            )
            
            # Bar layer
            bars = base.mark_bar().encode(
                color=alt.value('#1a73e8')  # Google Blue
            )
            
            # Text layer with percentage format
            text = base.mark_text(
                align='left',
                baseline='middle',
                dx=5,  # Offset from end of bar
                fontSize=14,
                font='Roboto',
                color='#5f6368'
            ).encode(
                text=alt.Text('Value:Q', format='.0f') # Remove suffix, add % in the string
            ).transform_calculate(
                text="datum.Value + '%'"  # Add percentage sign this way
            )
            
            # Combine layers and configure
            chart = alt.layer(bars, text).properties(
                padding={'left': 30, 'right': 30, 'top': 20, 'bottom': 20}
            ).configure_view(
                strokeWidth=0
            ).configure_axis(
                labelFontSize=14,
                titleFontSize=16,
                labelFont='Roboto',
                labelColor='#5f6368',
                domainWidth=0.5,
                domainColor='#e0e0e0'
            )
            
            # Display chart
            st.altair_chart(chart, use_container_width=True)
            
            # Add Material Design styling
            st.markdown("""
            <style>
                /* Material Design Typography */
                h2 {
                    font-family: 'Google Sans', 'Roboto', sans-serif;
                    font-size: 24px;
                    font-weight: 500;
                    color: #202124;
                    margin-bottom: 24px;
                }
                
                /* Material Design Cards */
                .trait-card {
                    background: white;
                    border-radius: 8px;
                    padding: 24px;
                    margin: 16px 0;
                    box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 
                               0 1px 3px 1px rgba(60,64,67,0.15);
                }
            </style>
            """, unsafe_allow_html=True)
    
    elif section == "Communication Style":
        st.markdown("## Communication Style")
        
        # Material Design card style
        st.markdown("""
        <style>
        .communication-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 8px 0;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
        }
        .do-item {
            color: #1e8e3e;  /* Google Green */
            padding: 8px 0;
            display: flex;
            align-items: center;
        }
        .dont-item {
            color: #d93025;  /* Google Red */
            padding: 8px 0;
            display: flex;
            align-items: center;
        }
        .item-icon {
            margin-right: 12px;
            font-size: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="communication-card">', unsafe_allow_html=True)
            st.markdown("### Do's")
            for do in data['content']['recommendations']['do']:
                st.markdown(f'<div class="do-item"><span class="item-icon">✓</span>{do}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="communication-card">', unsafe_allow_html=True)
            st.markdown("### Don'ts")
            for dont in data['content']['recommendations']['dont']:
                st.markdown(f'<div class="dont-item"><span class="item-icon">✕</span>{dont}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif section == "Strategic Tips":
        st.markdown("## Strategic Tips")
        
        # Material Design card style for tips
        st.markdown("""
        <style>
        .strategy-card {
            background: white;
            border-radius: 8px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
            display: flex;
            align-items: flex-start;
        }
        .tip-number {
            background: #1a73e8;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            flex-shrink: 0;
            font-family: 'Google Sans', sans-serif;
        }
        .tip-content {
            color: #3c4043;
            font-size: 16px;
            line-height: 1.5;
        }
        </style>
        """, unsafe_allow_html=True)
        
        tips = data['content'].get('profile', {}).get('overview', [])
        for idx, tip in enumerate(tips, 1):
            st.markdown(f"""
                <div class="strategy-card">
                    <div class="tip-number">{idx}</div>
                    <div class="tip-content">{tip}</div>
                </div>
            """, unsafe_allow_html=True)
    
    elif section == "Meeting Approach":
        st.markdown("## Meeting Approach")
        
        # Material Design timeline style
        st.markdown("""
        <style>
        .timeline-item {
            background: white;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
            display: flex;
            align-items: center;
            border-left: 4px solid #1a73e8;
        }
        .timeline-marker {
            color: #1a73e8;
            font-size: 20px;
            margin-right: 16px;
            min-width: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .timeline-content {
            color: #3c4043;
            font-size: 16px;
            line-height: 1.5;
        }
        </style>
        """, unsafe_allow_html=True)
        
        points = get_phrases('meeting')
        for point in points:
            st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-marker">→</div>
                    <div class="timeline-content">{point}</div>
                </div>
            """, unsafe_allow_html=True)
    
    elif section == "Negotiation Style":
        st.markdown("## Negotiation Style")
        
        # Material Design negotiation cards
        st.markdown("""
        <style>
        .nego-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 12px 0;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
            border-left: 4px solid #fbbc04;  /* Google Yellow */
        }
        .nego-content {
            color: #3c4043;
            font-size: 16px;
            line-height: 1.5;
            display: flex;
            align-items: center;
        }
        .nego-icon {
            color: #fbbc04;
            margin-right: 16px;
            font-size: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        points = get_phrases('negotiating')
        cols = st.columns(2)
        for idx, point in enumerate(points):
            with cols[idx % 2]:
                st.markdown(f"""
                    <div class="nego-card">
                        <div class="nego-content">
                            <span class="nego-icon">💡</span>
                            {point}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    elif section == "Content Strategy":
        st.markdown("## Content Strategy")
        
        # Material Design strategy cards
        st.markdown("""
        <style>
        .content-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 12px 0;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
            border-left: 4px solid #34a853;  /* Google Green */
        }
        .content-wrapper {
            display: flex;
            align-items: flex-start;
        }
        .content-icon {
            background: #34a853;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            flex-shrink: 0;
        }
        .content-text {
            color: #3c4043;
            font-size: 16px;
            line-height: 1.5;
        }
        </style>
        """, unsafe_allow_html=True)
        
        points = get_phrases('communication')
        for point in points:
            st.markdown(f"""
                <div class="content-card">
                    <div class="content-wrapper">
                        <div class="content-icon">📋</div>
                        <div class="content-text">{point}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    # Additional sections using the helper functions
    elif section == "Sales Approach":
        st.markdown("## Sales Playbook")
        points = get_phrases('selling')
        display_cards(points, "sales-card", "💼", "sales-icon")
    
    elif section == "Product Demo":
        st.markdown("## Product Presentation Guide")
        points = get_phrases('product_demo')
        display_cards(points, "demo-card", "🎯", "demo-icon")
    
    elif section == "Pricing":
        st.markdown("## Pricing Strategy")
        points = get_phrases('pricing')
        display_cards(points, "pricing-card", "💰", "pricing-icon")
    
    elif section == "Building Trust":
        st.markdown("## Trust Building Approach")
        points = get_phrases('building_trust')
        display_cards(points, "trust-card", "🤝", "trust-icon")
    
    elif section == "Working Together":
        st.markdown("## Working Style")
        points = get_phrases('working_together')
        display_cards(points, "collab-card", "👥", "collab-icon")
    
    elif section == "Following Up":
        st.markdown("## Follow-up Strategy")
        points = get_phrases('following_up')
        display_cards(points, "followup-card", "📞", "followup-icon")
    
    elif section == "First Impressions":
        st.markdown("## First Impressions")
        points = get_phrases('first_impression')
        if not points:
            points = get_phrases('first_impressions')
        display_cards(points, "impression-card", "👋", "impression-icon")
    
    elif section == "Driving Action":
        st.markdown("## Action Drivers")
        
        # Material Design action cards
        st.markdown("""
        <style>
        .action-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 12px 0;
            box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
            border-left: 4px solid #ea4335;  /* Google Red */
        }
        .action-content {
            display: flex;
            align-items: flex-start;
            color: #3c4043;
            font-size: 16px;
            line-height: 1.5;
        }
        .action-icon {
            background: #ea4335;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            flex-shrink: 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Try different possible keys for action drivers
        points = get_phrases('driving_action')
        if not points:
            points = get_phrases('action_drivers')
        if not points:
            points = get_phrases('actions')
            
        if points:
            for point in points:
                st.markdown(f"""
                    <div class="action-card">
                        <div class="action-content">
                            <div class="action-icon">⚡</div>
                            <div>{point}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No action drivers data available for this profile.")

def display_profile_sidebar(data: dict):
    """Common function to display profile sidebar"""
    with st.sidebar:
        # Add essential CSS only
        st.markdown("""
        <style>
            /* Clean sidebar styling */
            .stRadio > label {
                background: white;
                padding: 12px;
                border-radius: 8px;
                margin: 4px 0;
                border: 1px solid #e0e0e0;
                transition: all 0.2s ease;
            }
            .stRadio > label:hover {
                background: #f0f7ff;
                border-color: #0366d6;
            }
            .stRadio > label[data-checked="true"] {
                background: #0366d6;
                color: white;
                border-color: #0366d6;
            }
            /* Remove extra spacing */
            .block-container {
                padding-top: 0;
                padding-bottom: 1rem;
            }
        </style>
        """, unsafe_allow_html=True)

        # Profile Information
        if data.get("photo_url"):
            st.image(data["photo_url"], width=200)
        
        # Name and Type
        st.markdown(f"### {data.get('first_name', '')} {data.get('last_name', '')}")
        if data.get("personalities"):
            pers = data["personalities"]
            st.markdown(f"**Type:** {pers.get('disc_type', 'N/A')}")
            st.markdown(f"**Archetype:** {pers.get('archetype', 'N/A')}")
        
        # DISC wheel
        if data.get("images", {}).get("disc_map"):
            st.image(data["images"]["disc_map"], width=200)
        
        st.divider()
        
        # Navigation Section
        st.markdown("### 🎯 Engagement Insights")
        
        # Section options with clear naming
        section_options = {
            "🧠 Personality DNA": "Behavioral Traits",
            "💡 Communication Blueprint": "Communication Style",
            "🎯 Success Strategies": "Strategic Tips",
            "🤝 Meeting Mastery": "Meeting Approach",
            "💰 Deal Dynamics": "Negotiation Style",
            "📊 Engagement Roadmap": "Content Strategy",
            "💼 Sales Playbook": "Sales Approach",
            "🎯 Product Demo": "Product Demo",
            "💰 Pricing Talk": "Pricing",
            "🤝 Trust Building": "Building Trust",
            "⚡ Action Drivers": "Driving Action",
            "👥 Working Style": "Working Together",
            "📝 First Impressions": "First Impressions",
            "📞 Follow-up Guide": "Following Up"
        }
        
        # Radio button for section selection
        section = st.radio(
            label="Profile Sections",
            options=list(section_options.keys()),
            key="section_selector",
            format_func=lambda x: x,
            label_visibility="collapsed"
        )
        
        return section_options[section]

# Main content area - for new analysis
if selected_profile == "New Analysis":
    linkedin_url = st.text_input(
        "Enter LinkedIn Profile URL:",
        placeholder="https://www.linkedin.com/in/username"
    )
    
    if st.button("Analyze Profile", type="primary"):
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
                        if "data" in profile_data:
                            data = profile_data["data"]
                            section = display_profile_sidebar(data)
                            display_profile_content(data, section)

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
        if "data" in profile_data:
            data = profile_data["data"]
            section = display_profile_sidebar(data)
            display_profile_content(data, section)

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

def get_available_sections(data: dict) -> dict:
    """Get only sections that have data available"""
    content = data.get('content', {})
    
    # Helper function to check if section has data
    def has_data(key):
        return bool(content.get(key, {}).get('phrase', []))
    
    all_sections = {
        "🧠 Personality DNA": "Behavioral Traits",
        "💡 Communication Blueprint": "Communication Style",
        "🎯 Success Strategies": "Strategic Tips",
        "🤝 Meeting Mastery": "Meeting Approach",
        "💰 Deal Dynamics": "Negotiation Style",
        "📊 Engagement Roadmap": "Content Strategy",
        "💼 Sales Playbook": "Sales Approach",
        "🎯 Product Demo": "Product Demo",
        "💰 Pricing Talk": "Pricing",
        "🤝 Trust Building": "Building Trust",
        "⚡ Action Drivers": "Driving Action",
        "👥 Working Style": "Working Together",
        "📝 First Impressions": "First Impressions",
        "📞 Follow-up Guide": "Following Up"
    }
    
    # Filter sections based on data availability
    available_sections = {}
    for display_name, internal_name in all_sections.items():
        section_key = internal_name.lower().replace(' ', '_')
        if has_data(section_key) or internal_name in ["Behavioral Traits", "Communication Style"]:
            available_sections[display_name] = internal_name
    
    return available_sections