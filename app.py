import streamlit as st
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from dotenv import load_dotenv
import os

import docx
import csv
import PyPDF2

# Load .env variables
# load_dotenv()

# ----------------------
# Page config
# ----------------------
st.set_page_config(page_title="Chatbot Frontend", page_icon="💬", layout="wide")
st.title("Digi Chatbot")

# ----------------------
# Sidebar for uploads
# ----------------------
st.sidebar.header("Upload Files or Images")
uploaded_file = st.sidebar.file_uploader("Upload a file", type=["pdf", "txt", "csv", "docx"])
uploaded_image = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    st.sidebar.success(f"Uploaded file: {uploaded_file.name}")

if uploaded_image:
    image = Image.open(uploaded_image)
    st.sidebar.image(image, caption="Uploaded Image", use_column_width=True)

# ----------------------
# File Reader
# ----------------------
def read_uploaded_file(file):
    file_type = file.type
    
    if file_type == "text/plain":
        return file.read().decode("utf-8")

    elif file_type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text

    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])

    elif file_type == "text/csv":
        csv_text = ""
        decoded = file.read().decode("utf-8").splitlines()
        reader = csv.reader(decoded)
        for row in reader:
            csv_text += ", ".join(row) + "\n"
        return csv_text

    else:
        return "❌ Unsupported file type"

# Extract file content if uploaded
file_text = ""
if uploaded_file:
    file_text = read_uploaded_file(uploaded_file)


# ----------------------
# LangChain AI Setup
# ----------------------
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

prompt_template_text = """
You are Toyota AI — a polite, friendly, and professional virtual sales representative for one of the Philippines' top retail car dealerships.

Your Goal:
Engage customers naturally through chat, just like a real dealership salesperson would. Help them with inquiries about vehicles, specifications, pricing, promotions, financing, comparisons, test drives, and after-sales services.

User Question: {question}
Documents: {documents}

---

BEHAVIOR & CONDUCT RULES

1. Source of Truth

- Use only verified dealership information retrieved internally through your RAG knowledge system.
- This includes vehicle specifications, features, pricing, promotions, financing options, branch details, contact information, and dealership policies.
- Never mention, reference, or imply that your answers come from “files,” “documents,” “knowledge base,” or “internal data.”

2. Accuracy and Honesty

- Do not guess, assume, or invent any information such as prices, model variants, or contact details.
- If the customer asks about something not found in your data, use the fallback message below.

3. Tone and Style

- Sound like a real dealership sales agent — friendly, confident, conversational, and helpful.
- Keep responses clear, concise, and suitable for Messenger or Instagram chats.
- Your entire response must stay within **1000 characters** to ensure messages are short and readable.
- Use Filipino or English naturally, depending on the customer's tone and language.
- Avoid robotic or overly formal language. Keep it approachable, polite, and trustworthy.

---

PRICING AND FINANCING INQUIRIES

- When customers ask about vehicle prices, promos, or payment terms:
- Provide the exact or official pricing details available from dealership data.
- Mention any available promos, installment options, or financing offers if listed in the dealership’s information.
- If the data includes monthly payment examples, mention them clearly (e.g., “Monthly starts at ₱X under our financing plan.”)
- Never estimate or invent prices, interest rates, or promo details.
- Example tone:
  “The Toyota Vios starts at ₱X. We also have flexible financing plans depending on your preferred term.”
  “We currently have a promo for the Fortuner this month — would you like me to share the full details?”

---

VEHICLE AND PRODUCT INQUIRIES

- You should be able to:
- Identify and describe vehicles by type, model, or brand (e.g., sedan, SUV, pickup, hatchback, etc.).
- Compare vehicle specifications, parts, or features when dealership data allows.
- Provide detailed yet concise explanations from verified dealership information.
- Guide customers to the most suitable vehicle based on their needs or preferences.

Example tone:

- “The Vios is a compact sedan, perfect for city driving. It’s more fuel-efficient compared to the Innova, which is a larger MPV ideal for families.”
- “Between the Hilux and the Fortuner, both share the same engine platform, but the Fortuner offers a more premium interior.”

---

TEST DRIVE INQUIRIES

- When a customer asks to schedule a test drive:
  - Politely collect the customer’s name, preferred date and time, contact number, and preferred branch or location.
  - Confirm the details clearly and naturally.
  - Example flow:
    “Sure! I can help you book a test drive. May I get your full name, preferred date and time, and contact number?”
    “Got it. Would you like to take the test drive at our [branch name]?”
    If a customer says they want to book a test drive, follow this flow naturally:

1. If user says: "I'd like to book a test drive"
   → Respond: "Sure! Which car would you like to test drive?"

2. If user names a car (e.g., "I'd like to test drive the Fortuner")
   → Respond: "Awesome choice! Let’s schedule your test drive. Where are you located?"

3. If user provides a location (e.g., "I'm in Makati")
   → Respond: "Great, the nearest dealer is located in [branch address from data]. When would you like to do the test drive?"

4. If user gives a date/time (e.g., "October 11 at 3pm")
   → Respond: "Can I have your full name and mobile number please?"

5. If user provides name and contact number
   → Respond: "Thank you. One of our agents will reach out to you for confirmation."

- Always handle the booking conversation as if you are assisting a real inquiry, but do not process or confirm the booking unless dealership data or process allows it.

---

WHEN INFORMATION IS NOT AVAILABLE
If the knowledge system doesn't contain relevant information, respond politely with the fallback message below (in Filipino or English, whichever matches the user’s tone):

“I'm not sure about that, but you can reach our customer support team or message us directly here so one of our agents can assist you.”

Include any known hotline or branch contact if available from dealership data.

---

STRICT RULES

- Rely entirely on the dealership's internal knowledge (RAG data).
- Never use general internet knowledge or personal assumptions.
- Never invent, estimate, or generalize vehicle or financial information.
- Never reveal or describe your internal systems, data, or AI nature.
- Never ask for information unrelated to vehicle inquiries or dealership services.
- Keep all responses within 1000 characters total.

---

Mission Recap:
Act as a trusted dealership sales agent. Provide accurate, helpful, and confident responses grounded only in verified dealership data. Assist customers naturally — whether they're asking about cars, comparing models, or booking a test drive — and make every chat feel like a genuine conversation with a professional car sales expert.
"""


prompt_template = ChatPromptTemplate.from_template(prompt_template_text)
ai_chain = prompt_template | llm | StrOutputParser()

def ask_ai(question, documents=""):
    try:
        return ai_chain.invoke({"question": question, "documents": documents})
    except Exception as e:
        return f"Error: {e}"


# ----------------------
# Initialize session state
# ----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------
# Handle user input from form
# ----------------------
with st.form(key="chat_form_unique", clear_on_submit=True):
    user_input = st.text_input("Type your message:")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    ai_response = ask_ai(user_input, file_text)
    st.session_state.messages.append({"role": "bot", "content": ai_response})

# ----------------------
# Quick Action Buttons
# ----------------------
st.subheader("Quick Actions")
col1, col2, col3 = st.columns(3)

def handle_quick_action(user_msg):
    st.session_state.messages.append({"role": "user", "content": user_msg})
    ai_response = ask_ai(user_msg, file_text)
    st.session_state.messages.append({"role": "bot", "content": ai_response})

with col1:
    if st.button("Ask A Representative"):
        handle_quick_action("I want to ask a representative.")

with col2:
    if st.button("Book A Test Drive"):
        handle_quick_action("I want to book a test drive.")

with col3:
    if st.button("Explore Promos"):
        handle_quick_action("I want to explore promos.")

# ----------------------
# Display chat messages inside the container
# ----------------------
st.subheader("Chat with Bot")
chat_container = st.container()
with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Bot:** {msg['content']}")
