import streamlit as st
from PIL import Image
import os

from functionalities import (
    analyze_image_with_ai,
    read_uploaded_file,
    ask_ai
)

def handle_quick_action(user_msg, combined_context):
    st.session_state.messages.append({"role": "user", "content": user_msg})
    ai_response = ask_ai(user_msg, combined_context)
    st.session_state.messages.append({"role": "bot", "content": ai_response})

# ----------------------
# Page Configuration
# ----------------------
st.set_page_config(
    page_title="Toyota Digi Chatbot",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------
# Custom Styling (Toyota Colors)
# ----------------------
st.markdown("""
    <style>
    /* Toyota Red: #EB0A1E, Dark Gray: #2D2D2D, Light Gray: #F7F7F7 */
    .main {
        background-color: #F7F7F7;
    }
    .stButton>button {
        background-color: #EB0A1E;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #C4060F;
        box-shadow: 0 4px 12px rgba(235, 10, 30, 0.3);
    }
    .chat-message {
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .user-message {
        border-left: 4px solid #EB0A1E;
    }
    .bot-message {
        border-left: 4px solid #2D2D2D;
    }
    .sidebar .sidebar-content {
        background-color: #FFFFFF;
    }
    h1, h2, h3 {
        color: #2D2D2D;
    }
    .logo-container {
        text-align: center;
        padding: 20px 0;
        background-color: #EB0A1E;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .logo-placeholder {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------
# Header with Logo Placeholder
# ----------------------
col_logo, col_title = st.columns([1, 3])

with col_logo:
    # Logo placeholder - replace 'path/to/your/logo.png' with your actual logo path
    logo_path = "./toyota-white.png"  # Change this to your logo file path
    
    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        st.image(logo, width=250)
    else:
        # Placeholder for logo
        st.markdown("""
            <div class="logo-container">
                <div class="logo-placeholder">
                    <h2 style="color: #EB0A1E; margin: 0;">YOUR LOGO</h2>
                    <p style="color: #666; font-size: 12px; margin: 5px 0 0 0;">Place logo.png in root directory</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

with col_title:
    st.title(" Toyota Assistant")
    st.markdown("**Your intelligent automotive companion**")

st.divider()

# ----------------------
# Sidebar for File Uploads
# ----------------------
with st.sidebar:
    st.header("📁 Upload Document")
    st.markdown("Upload documents, images, receipts, or handwritten notes for analysis")
    
    st.subheader("📄 Document Upload")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "txt", "csv", "docx"],
        help="Supports PDF, TXT, CSV, and DOCX files"
    )
    
    st.subheader("🖼️ Image Upload")
    uploaded_image = st.file_uploader(
        "Choose an image",
        type=["png", "jpg", "jpeg"],
        help="Supports handwriting and receipt recognition"
    )
    
    st.divider()

# ----------------------
# Process Uploaded Files
# ----------------------
file_text = ""
image_analysis = ""

if uploaded_file:
    with st.sidebar:
        st.success(f"✅ File loaded: **{uploaded_file.name}**")
        with st.spinner("📄 Analyzing document..."):
            file_text = read_uploaded_file(uploaded_file)
            st.info("📊 Content extracted successfully")
        
        with st.expander("📖 View Document Content"):
            preview_text = file_text[:2000] + "..." if len(file_text) > 2000 else file_text
            st.text_area("Content Preview", preview_text, height=200, disabled=True)

if uploaded_image:
    with st.sidebar:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        with st.spinner("🔍 Analyzing image..."):
            image_analysis = analyze_image_with_ai(uploaded_image)
        st.success("✅ Image analyzed successfully!")
        
        with st.expander("🔎 View Image Analysis"):
            st.write(image_analysis)

# Combine context
combined_context = ""
if file_text:
    combined_context += f"FILE CONTENT:\n{file_text}\n\n"
if image_analysis:
    combined_context += f"IMAGE ANALYSIS:\n{image_analysis}\n\n"

# ----------------------
# Initialize Session State
# ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------
# Main Chat Interface
# ----------------------
st.subheader("💬 Chat Interface")

# Display chat history
chat_container = st.container()
with chat_container:
    if len(st.session_state.messages) == 0:
        st.info("👋 Welcome! How can I assist you today?")
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong><br>{msg['content']}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>🤖 Assistant:</strong><br>{msg['content']}
                </div>
            """, unsafe_allow_html=True)

# Chat input form
with st.form(key="chat_input_form", clear_on_submit=True):
    col_input, col_send = st.columns([5, 1])
    
    with col_input:
        user_input = st.text_input(
            "Type your message",
            placeholder="Ask me anything about Toyota vehicles, services, or upload documents...",
            label_visibility="collapsed"
        )
    
    with col_send:
        submitted = st.form_submit_button("Send ➤", use_container_width=True)

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    ai_response = ask_ai(user_input, combined_context, st.session_state.messages)
    st.session_state.messages.append({"role": "bot", "content": ai_response})
    st.rerun()

# ----------------------
# Quick Action Buttons
# ----------------------
st.divider()
st.subheader("⚡ Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📞 Ask A Representative", use_container_width=True):
        handle_quick_action("I want to ask a representative.", combined_context)
        st.rerun()

with col2:
    if st.button("🚗 Book A Test Drive", use_container_width=True):
        handle_quick_action("I want to book a test drive.", combined_context)
        st.rerun()

with col3:
    if st.button("🎁 Explore Promos", use_container_width=True):
        handle_quick_action("I want to explore current promotions.", combined_context)
        st.rerun()

with col4:
    if st.button("🔧 Service Booking", use_container_width=True):
        handle_quick_action("I want to book a service appointment.", combined_context)
        st.rerun()

