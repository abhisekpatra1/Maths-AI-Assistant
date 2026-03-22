"""
Streamlit Frontend for Document RAG System
User interface for document upload, chat, and report generation
"""

import streamlit as st
import requests
import uuid
from typing import List
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Mathematics Portal | Department Resources & Research Hub",
    page_icon="Ω",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #22a178;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #013606;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #080808;
        margin-right: 2rem;
    }
    .source-box {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
    }
    /* NEW: Better styling for full content display */
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'documents_uploaded' not in st.session_state:
    st.session_state.documents_uploaded = False

# Sidebar
with st.sidebar:
    #st.image("https://drive.google.com/file/d/1Rh_lvRtS-lnUVE_nx3L27Qu7Qftm1skK/view?usp=sharing", use_column_width=True)
    st.title("AI Math Assistant")
    st.markdown("---")
    
    st.subheader("📁 Document Upload")
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "docx", "xlsx", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Supported formats: PDF, Word, Excel, Images"
    )
    
    if uploaded_files and st.button("Process Documents", type="primary"):
        with st.spinner("Processing documents..."):
            try:
                # Prepare files for upload
                files = [
                    ("files", (file.name, file.getvalue(), file.type))
                    for file in uploaded_files
                ]
                
                # Upload to backend
                response = requests.post(
                    f"{API_BASE_URL}/upload",
                    params={"session_id": st.session_state.session_id},
                    files=files
                )
                
                if response.status_code == 200:
                    st.session_state.documents_uploaded = True
                    st.success(f"Processed {len(uploaded_files)} documents!")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"Connection error: {str(e)}")
                st.info("Make sure the backend server is running on http://localhost:8000")
    
    st.markdown("---")
    
    # Session info
    st.subheader("Session Info")
    st.text(f"ID: {st.session_state.session_id[:8]}...")
    st.text(f"Documents: {'✓' if st.session_state.documents_uploaded else '✗'}")
    
    if st.button("Clear Session"):
        st.session_state.chat_history = []
        st.session_state.documents_uploaded = False
        st.rerun()
    
    st.markdown("---")
    st.caption("Mathematics Portal AI Assistant v1.0")

# Main content
st.markdown('<h1 class="main-header">Mathematics Department AI Assistant</h1>', unsafe_allow_html=True)

# Create tabs
tab1 = st.tabs(["💬 Chat"])[0]

# Tab 1: Chat Interface - REPLACE YOUR EXISTING TAB1 CODE WITH THIS
with tab1:
    if not st.session_state.documents_uploaded:
        st.info("Please upload documents using the sidebar to start chatting.")
    else:
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message_index, message in enumerate(st.session_state.chat_history):
                if message['role'] == 'user':
                    st.markdown(
                        f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Display assistant message
                    st.markdown(
                        f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Display detailed citations in the main (outer) expander
                    citations = message.get('sources', []) or message.get('citations', [])
                    if citations:
                        with st.expander(f"📚 View Sources ({len(citations)} citations)", expanded=False):
                            for i, citation in enumerate(citations, 1):
                                if "Content: " in citation:
                                    # Split citation into header and content
                                    parts = citation.split("\nContent: ", 1)
                                    header = parts[0]
                                    content = parts[1] if len(parts) > 1 else ""
                                    
                                    st.markdown(f"**Source {i}:** `{header}`")
                                    
                                    # We create a unique key for each checkbox to avoid state conflicts
                                    unique_key = f"show_content_{message_index}_{i}"
                                    if st.checkbox("Show Full Chunk Content", key=unique_key):
                                        st.code(content, language=None)
                                    
                                    st.markdown("---")
                                else:
                                    st.markdown(f"- {citation}")
                                    st.markdown("---")
                            
        # Chat input
        st.markdown("---")
        col1, col2 = st.columns([6, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask a question about your documents:",
                key="user_input",
                placeholder="Ask your querry....",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("Send", type="primary", use_container_width=True)
        
        if send_button and user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            with st.spinner("Searching documents and generating answer..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={"session_id": st.session_state.session_id, "message": user_input}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': data['response'],
                            'sources': data.get('sources', []),
                            'citations': data.get('citations', [])
                        })
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
            
            st.rerun()



