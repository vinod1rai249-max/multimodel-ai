import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str
    media_path: Optional[str] = None
    media_type: Optional[str] = None # "image", "audio", "video"
    provider: Optional[str] = None
    model: Optional[str] = None
    trace_id: Optional[str] = None
    fallback_used: bool = False
    failed_providers: List[Dict[str, Any]] = Field(default_factory=list)
    latency: float = 0.0
    input_type: Optional[str] = None
    output_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_input_mode" not in st.session_state:
        st.session_state.current_input_mode = "Text"
    if "target_output" not in st.session_state:
        st.session_state.target_output = "Text"

def add_message(role: str, content: str, **kwargs):
    msg = ChatMessage(role=role, content=content, **kwargs)
    st.session_state.messages.append(msg)

def get_messages() -> List[ChatMessage]:
    return st.session_state.get("messages", [])

def clear_messages():
    st.session_state.messages = []
