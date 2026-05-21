import streamlit as st
import asyncio
import sys
import socket

# Windows-specific fix for asyncio DNS and connection noise
if sys.platform == "win32":
    # 1. Force the SelectorEventLoop for better stability on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 2. Patch ProactorEventLoop to silence WinError 10054 (Connection Reset)
    # This is a known issue in Python on Windows when servers close connections abruptly.
    from asyncio.proactor_events import _ProactorBasePipeTransport
    
    def patched_call_connection_lost(self, exc):
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except (ConnectionResetError, OSError):
            pass # Silence the error
        self._call_connection_lost_orig(exc)

    if not hasattr(_ProactorBasePipeTransport, "_call_connection_lost_orig"):
        _ProactorBasePipeTransport._call_connection_lost_orig = _ProactorBasePipeTransport._call_connection_lost
        _ProactorBasePipeTransport._call_connection_lost = patched_call_connection_lost

from ui.state import init_state, add_message, get_messages
from ui.layout import render_main_layout
from ui.components import render_prompt_guide
from core.orchestrator import orchestrator
from core.logger import app_logger

# Set page config first
st.set_page_config(
    page_title="Multimodal AI Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

async def process_request(prompt: str, target_output: str, params: dict, uploaded_file=None):
    try:
        # Extract parameters from the returned params dictionary
        # Gender is now hard-locked to Female in the UI and Providers
        sel_gender = "Female"
        sel_engine = params.get("voice_engine", "Standard (Free)")
        
        # LOGGING FOR AUDIT: Prove the sidebar values are being read
        app_logger.info(f"UI AUDIT: Requested Output={target_output} | Engine={sel_engine}")

        # Read image bytes if provided
        image_bytes = None
        if uploaded_file:
            image_bytes = uploaded_file.getvalue()

        # Call the orchestrator
        result = await orchestrator.generate(
            prompt=prompt,
            output_type=target_output.lower(),
            image_bytes=image_bytes,
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 2048),
            video_style=params.get("video_style", "Natural"),
            voice_gender="Female", # Hard-locked
            voice_engine=sel_engine
        )
        
        # Add assistant message to state
        content = ""
        media_path = None
        media_type = None
        
        # PROOF OF WORK: Explicitly label the active engine in the UI
        verification_label = f" [ENGINE: {result.provider.upper()}] "
        
        if result.content_type == "text":
            content = result.content
        else:
            content = f"Generated {result.content_type} {verification_label} based on your prompt."
            media_path = result.content
            media_type = result.content_type
            
        add_message("assistant", content, media_path=media_path, media_type=media_type, model=result.model)
        return True
    except Exception as e:
        error_msg = str(e)
        app_logger.critical(f"🛑 [PROCESS ERROR] Critical failure in request handling: {error_msg}")
        app_logger.debug(f"TRACEBACK:\n", exc_info=True)
        
        # User-friendly but informative UI error
        friendly_error = f"❌ **System Alert:** {error_msg[:100]}..."
        if "API Key" in error_msg:
            friendly_error = "🔑 **API Configuration Error:** Please check your keys in the .env file."
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            friendly_error = "⏳ **Resource Limit Reached:** The primary AI engine is busy. Please try again in a moment."
            
        add_message("assistant", friendly_error)
        return False

from core.utils import run_diagnostics

def main():
    init_state()
    params = render_main_layout()
    
    # Add diagnostic button in sidebar
    with st.sidebar:
        if st.button("🔍 Run Network Diagnostics", use_container_width=True):
            with st.status("Checking API connectivity..."):
                results = run_diagnostics()
                for name, status in results.items():
                    if status:
                        st.success(f"{name}: Connected")
                    else:
                        st.error(f"{name}: Connection Failed (DNS)")
    
    # Retrieve uploaded file based on current mode using keys from ui/components.py
    uploaded_file = None
    current_mode = st.session_state.get("current_input_mode", "Text")
    
    if current_mode == "Image":
        uploaded_file = st.session_state.get("sidebar_img_upload")
    if current_mode == "Video":
        uploaded_file = st.session_state.get("sidebar_vid_upload")

    render_prompt_guide()
    prompt = st.chat_input(f"Send a message ({st.session_state.current_input_mode} mode)...")


    if prompt:
        app_logger.info(f"User prompt: {prompt} | Target: {params['target_output']}")
        
        # Add user message to state
        add_message("user", prompt)
        
        # Run async process
        with st.chat_message("assistant"):
            status_container = st.empty()
            with status_container.status(f"🚀 Multimodal Engine: Processing {params['target_output']}...", expanded=True) as status:
                st.write(f"🔍 Analyzing prompt: '{prompt[:50]}...'")
                if uploaded_file:
                    st.write("🖼 Image data detected. Switching to Animation Engine...")
                else:
                    st.write("📝 Text detected. Routing to Generation Engine...")
                
                # Use asyncio.run for a cleaner, more reliable execution in Streamlit
                asyncio.run(process_request(prompt, params['target_output'], params, uploaded_file))
                status.update(label="✅ Generation Complete!", state="complete", expanded=False)
                
        # Rerun to update chat history in UI
        st.rerun()

if __name__ == "__main__":
    main()
