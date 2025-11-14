import streamlit as st
from PIL import Image

# Page config
st.set_page_config(page_title="Chatbot Frontend", page_icon="💬", layout="wide")

# Title
st.title("💬 Streamlit Chatbot")

# Sidebar for uploads
st.sidebar.header("Upload Files or Images")

uploaded_file = st.sidebar.file_uploader("Upload a file", type=["pdf", "txt", "csv"])
uploaded_image = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    st.sidebar.success(f"Uploaded file: {uploaded_file.name}")

if uploaded_image:
    image = Image.open(uploaded_image)
    st.sidebar.image(image, caption="Uploaded Image", use_column_width=True)

# Chat container
st.subheader("Chat with Bot")
chat_container = st.container()

# Store messages in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Bot:** {msg['content']}")

# Input box
user_input = st.text_input("Type your message:", key="input")

if st.button("Send"):
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Placeholder bot reply (to be replaced with backend)
        bot_reply = "This is a placeholder response."

        st.session_state.messages.append({"role": "bot", "content": bot_reply})

        # Clear input
        st.session_state.input = ""
        st.experimental_rerun()
