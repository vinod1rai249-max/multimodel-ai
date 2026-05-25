import streamlit as st
import os
from ui.components import inject_premium_css, render_header, render_sidebar
from ui.state import get_messages

def render_metadata_card(msg):
    # Helper to get attribute/key safely
    def get_attr(obj, attr, default=None):
        return getattr(obj, attr) if hasattr(obj, attr) else obj.get(attr, default)

    role = get_attr(msg, "role")
    provider = get_attr(msg, "provider")
    fallback_used = get_attr(msg, "fallback_used", False)
    model = get_attr(msg, "model")
    content = get_attr(msg, "content", "")
    media_type = get_attr(msg, "media_type")
    trace_id = get_attr(msg, "trace_id")
    latency = get_attr(msg, "latency", 0.0)
    input_type = get_attr(msg, "input_type")
    output_type = get_attr(msg, "output_type")
    failed_providers = get_attr(msg, "failed_providers", [])

    if role != "assistant" or not provider:
        return

    status_text = "✅ SUCCESS" if not fallback_used else "⚠️ FALLBACK ACTIVE"

    # Extract metadata safely
    metadata = get_attr(msg, "metadata", {})
    is_real_video = metadata.get("is_real_video", False)
    response_type = "video" if is_real_video else ("storyboard" if media_type == "storyboard" or "storyboard" in content.lower() else "text")

    # Use native Streamlit components for the card
    with st.container():
        st.markdown(f"***")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{status_text}**")
            st.markdown(f"**Provider Used:** `{provider.upper()}`")
            st.markdown(f"**Model Used:** `{model}`")
            st.markdown(f"**Response Type:** `{response_type.upper()}`")
        with col2:
            st.markdown(f"**Real Video:** `{'Yes' if is_real_video else 'No'}`")
            st.markdown(f"**Fallback Used:** `{'Yes' if fallback_used else 'No'}`")
            st.markdown(f"**Trace ID:** `{trace_id}`")

        st.caption(f"Latency: {latency:.2f}s | Route: {input_type} ➞ {output_type}")

        if failed_providers:
            with st.expander("🔍 VIEW FALLBACK DETAILS", expanded=False):
                st.markdown("### ❌ Failed Providers")
                for fail in failed_providers:
                    st.error(f"**{fail['provider']}** ({fail['model']}): {fail['message']}")
        st.markdown(f"***")


def render_main_layout():
    inject_premium_css()
    params = render_sidebar()
    render_header()
    
    # Render chat history
    for msg in get_messages():
        # Helper to get attribute/key safely
        def get_attr(obj, attr, default=None):
            return getattr(obj, attr) if hasattr(obj, attr) else obj.get(attr, default)

        role = get_attr(msg, "role")
        content = get_attr(msg, "content", "")
        provider = get_attr(msg, "provider")
        model = get_attr(msg, "model")
        fallback_used = get_attr(msg, "fallback_used", False)
        media_path = get_attr(msg, "media_path")
        media_type = get_attr(msg, "media_type")

        with st.chat_message(role):
            if role == "assistant" and provider:
                badge_color = "#F59E0B" if fallback_used else "#2563EB"
                st.markdown(f"""
                    <div style="display: inline-block; background: {badge_color}; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800; margin-bottom: 8px; text-transform: uppercase;">
                        {provider} | {model}
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown(content)
            
            # Rendering Flow: 
            # 1. If media_path exists and is a file, handle based on media_type
            # 2. If media_type is "video", use st.video()
            # 3. If media_type is "storyboard", it is already rendered as markdown above
            if media_path and os.path.exists(media_path):
                if media_type == "image":
                    st.image(media_path)
                elif media_type == "audio":
                    st.audio(media_path)
                elif media_type == "video":
                    st.video(media_path)
            
            if role == "assistant":
                render_metadata_card(msg)
    
    return params
