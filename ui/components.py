import streamlit as st
import streamlit_shadcn_ui as ui
from core.utils import run_diagnostics

ROUTE_MAP = {
    "Text": ["Text", "Image", "Audio", "Video"],
    "Image": ["Text", "Video"],
    "Video": ["Text"],
}

FALLBACK_CHAINS = {
    ("Text", "Text"): ["Groq", "Gemini", "OpenRouter", "HuggingFace"],
    ("Text", "Image"): ["HuggingFace", "OpenRouter", "Pollinations"],
    ("Text", "Audio"): ["Edge-TTS", "HuggingFace TTS", "gTTS"],
    ("Text", "Video"): ["HuggingFace", "OpenRouter", "Pexels/Pollinations"],
    ("Image", "Text"): ["Gemini Vision", "Groq Vision", "OpenRouter Vision", "HuggingFace Vision"],
    ("Image", "Video"): ["Gemini Vision Caption", "HuggingFace Image-to-Video", "Text-to-Video Fallback"],
    ("Video", "Text"): ["Gemini Vision", "OpenRouter Vision", "HuggingFace Vision"],
}

def inject_premium_css():
    st.markdown("""
        <style>
        /* LIGHT PREMIUM THEME */
        .stApp {
            background-color: #F8FAFC;
            background-image: radial-gradient(at 0% 0%, hsla(202,100%,95%,1) 0, transparent 50%), 
                              radial-gradient(at 100% 100%, hsla(202,100%,98%,1) 0, transparent 50%);
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0;
        }
        
        /* Card Styling */
        .ui-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        }
        
        /* Typography */
        h1, h2, h3, p, span, li, label, div {
            color: #0F172A !important;
            font-family: 'Inter', -apple-system, sans-serif;
        }
        
        .stMarkdown p {
            color: #475569 !important;
        }
        
        /* Buttons */
        .stButton>button {
            border-radius: 8px !important;
            background: #2563EB !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 10px 20px !important;
            transition: all 0.2s ease;
        }
        
        .stButton>button:hover {
            background: #1D4ED8 !important;
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
        }
        
        /* Tabs Fix for Light Theme */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #F1F5F9;
            padding: 4px;
            border-radius: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 35px;
            background-color: transparent;
            border-radius: 6px;
            color: #64748B !important;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #2563EB !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        /* Chat Input Fix */
        [data-testid="stChatInput"] {
            border-radius: 12px !important;
            border: 1px solid #E2E8F0 !important;
            background: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown(f"""
        <div style="margin-bottom: 30px;">
            <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 5px; color: #0F172A !important;">
                Professional Multimodal Studio
            </h1>
            <p style="font-size: 1.1rem; color: #64748B !important;">
                Generate text, images, audio, and video with intelligent provider fallback.
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_prompt_guide():
    mode = st.session_state.get("current_input_mode", "Text")
    tips = {
        "Text": {
            "label": "ELITE RESEARCHER", "icon": "📝", "color": "#2563EB",
            "text": "Be specific about tone and structure for insightful results.",
            "example": "'Write a structured AI ethics report in a formal tone.'"
        },
        "Image": {
            "label": "DIGITAL ARTIST", "icon": "🎨", "color": "#7C3AED",
            "text": "Define textures, lighting, and artistic styles (e.g. 8k, bokeh).",
            "example": "'Oil painting of a neon city, soft morning light, highly detailed.'"
        },
        "Video": {
            "label": "CINEMATOGRAPHER", "icon": "🎬", "color": "#DC2626",
            "text": "Describe camera movement, lighting, and specific scene dynamics.",
            "example": "'Cinematic tracking shot, golden hour, slow motion mountain pan.'"
        }
    }
    tip = tips.get(mode, tips["Text"])
    
    st.markdown(f"""
        <div style="
            background: #FFFFFF; 
            padding: 15px 25px; 
            border-radius: 12px; 
            border: 1px solid #E2E8F0;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        ">
            <div style="font-size: 1.8rem; margin-right: 20px;">{tip['icon']}</div>
            <div>
                <div style="color: {tip['color']}; font-weight: 800; font-size: 0.75rem; letter-spacing: 0.05rem; text-transform: uppercase; margin-bottom: 4px;">
                    {tip['label']} GUIDANCE
                </div>
                <div style="color: #0F172A; font-size: 0.95rem; font-weight: 600;">
                    {tip['text']}
                </div>
                <div style="color: #64748B; font-size: 0.8rem; font-style: italic; margin-top: 4px;">
                    Try: {tip['example']}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🎯 Studio Control")
        
        # CARD 1: INPUT SELECTION
        with st.container():
            st.markdown("**1. INPUT MODE**")
            input_mode = st.session_state.get("current_input_mode", "Text")
            new_input_mode = ui.tabs(options=["Text", "Image", "Video"], default_value=input_mode, key="input_mode_tabs")
            
            if new_input_mode != input_mode:
                st.session_state.current_input_mode = new_input_mode
                st.session_state.target_output = ROUTE_MAP[new_input_mode][0]
                st.rerun()
        
        st.markdown("---")
        
        # CARD 2: TARGET OUTPUT
        with st.container():
            st.markdown("**2. TARGET OUTPUT**")
            allowed_outputs = ROUTE_MAP.get(input_mode, ["Text"])
            current_target = st.session_state.get("target_output", "Text")
            if current_target not in allowed_outputs:
                 current_target = allowed_outputs[0]
                 st.session_state.target_output = current_target

            target_output = ui.tabs(options=allowed_outputs, default_value=current_target, key="target_output_tabs")
            if target_output != current_target:
                st.session_state.target_output = target_output
                st.rerun()

        st.markdown("---")
        
        # CARD 3: MEDIA UPLOAD (Conditional)
        if input_mode == "Image":
            st.markdown("**3. SOURCE IMAGE**")
            st.file_uploader("Upload reference", type=["png", "jpg", "jpeg", "webp"], key="sidebar_img_upload")
            st.markdown("---")
        elif input_mode == "Video":
            st.markdown("**3. SOURCE VIDEO**")
            st.file_uploader("Upload reference", type=["mp4", "mov", "avi"], key="sidebar_vid_upload")
            st.markdown("---")
        
        # CARD 4: SETTINGS
        with st.container():
            st.markdown("**GEN SETTINGS**")
            video_style = st.selectbox("Style", ["Natural", "Animation"], index=0, key="video_style_select")
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1, key="temp_slider")

        st.markdown("---")
        
        # CARD 5: ROUTE SUMMARY
        chain = FALLBACK_CHAINS.get((input_mode, target_output), ["Unknown"])
        chain_str = " → ".join(chain)
        st.markdown(f"""
            <div style="background: #F1F5F9; padding: 12px; border-radius: 8px; border-left: 4px solid #38BDF8;">
                <div style="font-size: 0.7rem; font-weight: 800; color: #64748B; text-transform: uppercase;">Active Route</div>
                <div style="font-size: 0.9rem; font-weight: 700; color: #0F172A;">{input_mode} ➞ {target_output}</div>
                <div style="font-size: 0.65rem; color: #64748B; margin-top: 5px;">Fallback Chain:</div>
                <div style="font-size: 0.75rem; color: #0F172A; font-family: monospace;">{chain_str}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        
        # CARD 6: DEVELOPER TOOLS (Collapsed)
        with st.expander("🛠 DEVELOPER TOOLS", expanded=False):
            if st.button("🔍 Run System Diagnostics", use_container_width=True):
                with st.status("Verifying environment..."):
                    results = run_diagnostics()
                    for name, data in results.items():
                        if data["configured"]:
                            st.success(f"{name}: Configured")
                        else:
                            st.error(f"{name}: Missing")
            
            st.info("Logs are available in `logs/` directory.")

        if st.button("🗑 CLEAR CHAT", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        return {
            "temperature": temperature, 
            "max_tokens": 2048, 
            "target_output": st.session_state.target_output, 
            "video_style": video_style,
            "voice_gender": "Female",
            "voice_engine": "Standard (Free)"
        }
