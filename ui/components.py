import streamlit as st
import streamlit_shadcn_ui as ui

def inject_premium_css():
    st.markdown("""
        <style>
        /* Premium Aura: Colorful & Soothing Gradient - RESTORED */
        .stApp {
            background: linear-gradient(135deg, #060b26 0%, #1e3a8a 40%, #0d9488 100%);
            background-attachment: fixed;
        }
        
        /* THE 'ULTIMATE VISIBILITY' OVERRIDE FOR COLORFUL BACKGROUNDS */
        /* Forces bright white text with dark shadows to ensure readability */
        html, body, .stMarkdown p, .stMarkdown span, .stMarkdown li, div.stChatMessage p, label p, [data-testid="stWidgetLabel"] p {
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.8) !important;
        }

        /* Bold Widget Labels in White */
        [data-testid="stWidgetLabel"] p, label {
            color: #ffffff !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
        }

        /* Radio Button Visibility (Male/Female) */
        div[data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
            font-weight: 800 !important;
            text-shadow: 0px 2px 4px rgba(0,0,0,1) !important;
        }

        /* Chat Message Bubbles - Soothing Glassmorphism */
        div.stChatMessage {
            background: rgba(255, 255, 255, 0.12) !important;
            backdrop-filter: blur(20px);
            border-radius: 12px;
            padding: 15px 20px !important;
            margin-bottom: 15px !important;
            border: 1px solid rgba(255, 255, 255, 0.25);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }

        /* Sidebar: Soothing Blue Contrast */
        [data-testid="stSidebar"] {
            background: #060b26 !important;
            border-right: 2px solid rgba(255, 255, 255, 0.2);
        }

        /* Vivid Sidebar Headers */
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #38bdf8 !important;
            font-weight: 950 !important;
            text-transform: uppercase;
        }

        /* Glowing Soothing Buttons */
        .stButton>button {
            background: linear-gradient(90deg, #3b82f6 0%, #2dd4bf 100%) !important;
            color: #ffffff !important;
            font-weight: 900 !important;
            border: 1px solid #ffffff !important;
            text-transform: uppercase;
        }

        /* Header Title */
        h1 {
            background: linear-gradient(90deg, #ffffff 0%, #38bdf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem !important;
            font-weight: 950 !important;
        }
        
        /* Fix for input box - ensure black text on light bg for inputs */
        input, textarea, select {
            color: #000000 !important;
            background-color: #ffffff !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    ui.badges(badge_list=[("Status", "Premium"), ("Mode", "Multimodal")], key="header_badges")
    st.title("PROFESSIONAL MULTIMODAL STUDIO")
    st.markdown("---")

def render_prompt_guide():
    # Identify the current mode
    mode = st.session_state.get("current_input_mode", "Text")
    
    # Define high-end contextual tips
    tips = {
        "Text": {
            "label": "ELITE RESEARCHER",
            "icon": "📝",
            "color": "#2563eb",
            "text": "Be specific about tone and structure for insightful results.",
            "example": "'Write a structured AI ethics report in a formal tone.'"
        },
        "Image": {
            "label": "DIGITAL ARTIST",
            "icon": "🎨",
            "color": "#7c3aed",
            "text": "Define textures, lighting, and artistic styles (e.g. 8k, bokeh).",
            "example": "'Oil painting of a neon city, soft morning light, highly detailed.'"
        },
        "Video": {
            "label": "CINEMATOGRAPHER",
            "icon": "🎬",
            "color": "#dc2626",
            "text": "Describe camera movement, lighting, and specific scene dynamics.",
            "example": "'Cinematic tracking shot, golden hour, slow motion mountain pan.'"
        }
    }
    
    tip = tips.get(mode, tips["Text"])
    
    # Render the Smart Contextual Ribbon
    st.markdown(f"""
        <div style="
            background: #f8fafc; 
            padding: 12px 20px; 
            border-radius: 10px; 
            border: 2px solid #000000;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            box-shadow: 4px 4px 0px #000000;
        ">
            <div style="font-size: 1.5rem; margin-right: 15px;">{tip['icon']}</div>
            <div>
                <div style="color: {tip['color']}; font-weight: 900; font-size: 0.75rem; letter-spacing: 0.1rem; text-transform: uppercase; margin-bottom: 2px;">
                    {tip['label']} GUIDANCE
                </div>
                <div style="color: #000000; font-size: 0.9rem; font-weight: 700;">
                    {tip['text']}
                </div>
                <div style="color: #475569; font-size: 0.8rem; font-style: italic; margin-top: 2px;">
                    Try: {tip['example']}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎯 INPUT SELECTION")
        input_mode = st.session_state.get("current_input_mode", "Text")
        new_input_mode = ui.tabs(options=["Text", "Image", "Video"], default_value=input_mode, key="input_mode_tabs")
        
        if new_input_mode != input_mode:
            st.session_state.current_input_mode = new_input_mode
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎯 TARGET OUTPUT")
        target_output = ui.tabs(options=["Text", "Image", "Audio", "Video"], default_value="Text", key="target_output_tabs")
        
        st.markdown("---")
        
        if input_mode == "Image":
            st.markdown("### 🖼 UPLOAD IMAGE")
            st.file_uploader("Drop image here", type=["png", "jpg", "jpeg", "webp", "bmp"], key="sidebar_img_upload")
        elif input_mode == "Video":
            st.markdown("### 🎥 UPLOAD VIDEO")
            st.file_uploader("Drop video here", type=["mp4", "mov", "avi", "mkv", "webm"], key="sidebar_vid_upload")
        
        st.markdown("### 🎙 VOICE CONTROL")
        # Gender selection removed as requested. Permanent Female Persona active.
        st.selectbox("Video Style", ["Natural", "Animation"], index=0, key="video_style_select")

        st.markdown("---")
        if st.button("🗑 CLEAR CHAT", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        return {
            "temperature": 0.7, 
            "max_tokens": 2048, 
            "target_output": target_output, 
            "video_style": st.session_state.get("video_style_select"),
            "voice_gender": "Female", # Locked to Female
            "voice_engine": "Standard (Free)"
        }
