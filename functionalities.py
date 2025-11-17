from PIL import Image
import os
import streamlit as st
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from io import BytesIO
import base64
import docx
import csv
import PyPDF2
import pdf2image

from dotenv import load_dotenv
load_dotenv()



llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def encode_image_to_base64(image_file):
    """Convert image to base64 string for OpenAI API"""
    image = Image.open(image_file)
    buffered = BytesIO()
    image.save(buffered, format=image.format if image.format else "PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_image_with_ai(image_file):
    """Analyze image using OpenAI Vision API - supports any type of image including handwritten text and receipts"""
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image_file)
        
        # Create a ChatOpenAI instance with vision capabilities
        llm_vision = ChatOpenAI(
            model="gpt-4o",  # gpt-4o supports vision
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create message with image
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": """You are an advanced OCR and image analysis system. Analyze this image thoroughly and extract ALL information:

                    PRIMARY TASKS:
                    1. **Text Extraction (OCR)**: Extract ALL visible text, including:
                       - Printed text
                       - HANDWRITTEN text (cursive, print, notes)
                       - Text in any language
                       - Numbers, dates, codes
                    
                    2. **Document Analysis**: If this is a document, identify:
                       - Document type (receipt, invoice, form, letter, note, etc.)
                       - Key information (dates, amounts, names, addresses, phone numbers)
                       - Line items, totals, calculations
                       - Signatures or stamps
                    
                    3. **Receipt/Invoice Analysis**: If this is a receipt or invoice, extract:
                       - Store/business name and location
                       - Date and time of transaction
                       - Itemized list with prices
                       - Subtotals, taxes, discounts
                       - Total amount
                       - Payment method
                       - Receipt/transaction number
                    
                    4. **Visual Content**: Describe what you see:
                       - Objects, products, people, scenes
                       - Brands, logos, labels
                       - Colors, layout, condition
                       - Any relevant visual details
                    
                    5. **Handwritten Notes**: Pay special attention to handwritten content:
                       - Transcribe handwritten text as accurately as possible
                       - Note if handwriting is unclear
                       - Capture margin notes, annotations, signatures
                    
                    Provide a comprehensive, structured analysis with all extracted information."""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        )
        
        # Get response
        response = llm_vision.invoke([message])
        return response.content
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"
        
def analyze_pdf_with_ai(pdf_file):
    """Analyze PDF using OpenAI Vision API - converts PDF pages to images for visual analysis including handwritten content"""
    try:
        # First extract text using PyPDF2
        reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        
        # Try to convert PDF to images for vision analysis (if pdf2image is available)
        try:
            from pdf2image import convert_from_bytes
            
            pdf_file.seek(0)  # Reset file pointer
            pdf_bytes = pdf_file.read()
            
            # Convert first 3 pages to images (to avoid token limits)
            images = convert_from_bytes(pdf_bytes, first_page=1, last_page=min(3, len(reader.pages)))
            
            llm_vision = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
            visual_analysis = ""
            for i, img in enumerate(images):
                # Convert PIL image to base64
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                message = HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"""Analyze page {i+1} of this PDF document. Extract ALL information including:
                            - Printed text
                            - Handwritten text, notes, or annotations
                            - Tables, charts, diagrams
                            - Signatures, stamps, marks
                            - Any visual elements
                            
                            Provide a comprehensive analysis of this page."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                )
                
                response = llm_vision.invoke([message])
                visual_analysis += f"\n--- PAGE {i+1} VISUAL ANALYSIS ---\n{response.content}\n"
            
            return f"TEXT EXTRACTION:\n{extracted_text}\n\nVISUAL ANALYSIS (with handwriting detection):\n{visual_analysis}"
            
        except ImportError:
            # If pdf2image is not available, return only text extraction
            return f"TEXT EXTRACTION:\n{extracted_text}\n\n(Note: Install 'pdf2image' and 'poppler' for handwriting and visual analysis of PDFs)"
            
    except Exception as e:
        return f"Error analyzing PDF: {str(e)}"
    
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
    
    
def ask_ai(question, documents=""):
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

    try:
        return ai_chain.invoke({"question": question, "documents": documents})
    except Exception as e:
        return f"Error: {e}"
    
    
    