import streamlit as st
from ui.components import inject_premium_css, render_header, render_sidebar
from ui.state import get_messages

def render_main_layout():
    inject_premium_css()
    params = render_sidebar()
    render_header()
    
    # Render chat history
    for msg in get_messages():
        with st.chat_message(msg.role):
            if msg.model:
                st.caption(f"🚀 Model: {msg.model}")
            st.markdown(msg.content)
            if msg.media_path:
                import os
                if os.path.exists(msg.media_path):
                    with open(msg.media_path, "rb") as f:
                        media_bytes = f.read()
                    
                    if msg.media_type == "image":
                        st.image(media_bytes)
                    elif msg.media_type == "audio":
                        # Passing bytes directly ensures the latest audio is always played
                        st.audio(media_bytes)
                    elif msg.media_type == "video":
                        st.video(media_bytes)
                else:
                    st.error("Media file not found in cache. It may have been deleted.")
    
    return params

# Input section is now integrated into main for state consistency
