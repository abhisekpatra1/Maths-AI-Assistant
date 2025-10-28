"""
Streamlit Frontend for Medical Document RAG System
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
    page_title="Medical Document AI Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    st.title("🏥 Medical Assistant")
    st.markdown("---")
    
    st.subheader("📁 Document Upload")
    uploaded_files = st.file_uploader(
        "Upload medical documents",
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
    st.caption("Medical Document AI Assistant v1.0")

# Main content
st.markdown('<h1 class="main-header">Medical Document AI Assistant</h1>', unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["💬 Chat", "📄 Generate Report"])

# Tab 1: Chat Interface
with tab1:
    if not st.session_state.documents_uploaded:
        st.info("Please upload documents using the sidebar to start chatting.")
    else:
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(
                        f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                    if message.get('sources'):
                        with st.expander("View Sources"):
                            for source in message['sources']:
                                st.markdown(f"- {source}")
        
        # Chat input
        st.markdown("---")
        col1, col2 = st.columns([6, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask a question about your documents:",
                key="user_input",
                placeholder="e.g., What are the key clinical findings?",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("Send", type="primary", use_container_width=True)
        
        if send_button and user_input:
            # Add user message to history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Get response from backend
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={
                            "session_id": st.session_state.session_id,
                            "message": user_input
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': data['response'],
                            'sources': data.get('sources', [])
                        })
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
            
            st.rerun()

# Tab 2: Report Generation
with tab2:
    if not st.session_state.documents_uploaded:
        st.info(" Please upload documents using the sidebar to generate reports.")
    else:
        st.subheader("📄 Generate Medical Report")
        st.write("Select the sections you want to include in your report:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_intro = st.checkbox("Introduction", value=True)
            include_findings = st.checkbox("Clinical Findings", value=True)
            include_tables = st.checkbox("Patient Tables", value=True)
        
        with col2:
            include_graphs = st.checkbox("Graphs & Charts", value=True)
            include_summary = st.checkbox("Summary", value=True)
        
        # Build sections list
        sections = []
        if include_intro:
            sections.append("Introduction")
        if include_findings:
            sections.append("Clinical Findings")
        if include_tables:
            sections.append("Patient Tables")
        if include_graphs:
            sections.append("Graphs")
        if include_summary:
            sections.append("Summary")
        
        st.markdown("---")
        
        if st.button("Generate Report", type="primary", disabled=len(sections) == 0):
            if len(sections) == 0:
                st.warning("Please select at least one section.")
            else:
                with st.spinner("Generating report... This may take a moment."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/generate-report",
                            json={
                                "session_id": st.session_state.session_id,
                                "sections": sections
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success("The Report generated successfully!")
                            
                            # Extract filename from path
                            report_path = data['report_path']
                            filename = report_path.split('/')[-1]
                            
                            # Download button
                            download_url = f"{API_BASE_URL}/download-report/{st.session_state.session_id}/{filename}"
                            
                            st.markdown(f"""
                                <a href="{download_url}" target="_blank">
                                    <button style="
                                        background-color: #4CAF50;
                                        border: none;
                                        color: white;
                                        padding: 15px 32px;
                                        text-align: center;
                                        text-decoration: none;
                                        display: inline-block;
                                        font-size: 16px;
                                        margin: 4px 2px;
                                        cursor: pointer;
                                        border-radius: 8px;
                                    ">
                                        📥 Download Report PDF
                                    </button>
                                </a>
                            """, unsafe_allow_html=True)
                            
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                            
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")
        
        st.markdown("---")
        st.info("💡 **Tip:** The report will preserve exact content from your documents, with summaries generated only for sections where requested.")