import streamlit as st
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Message(BaseModel):
    role: str # "user" or "assistant"
    content: str
    media_path: Optional[str] = None
    media_type: Optional[str] = None # "image", "audio", "video"
    model: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False

    if "current_input_mode" not in st.session_state:
        st.session_state.current_input_mode = "Text" # Text, Image, Video

def add_message(role: str, content: str, media_path: Optional[str] = None, media_type: Optional[str] = None, model: Optional[str] = None):
    message = Message(role=role, content=content, media_path=media_path, media_type=media_type, model=model)
    st.session_state.messages.append(message)
    # Keep history under limit if needed (from config)
    # This can be handled here or in the orchestrator

def get_messages() -> List[Message]:
    return st.session_state.messages

def clear_messages():
    st.session_state.messages = []
