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
    You are an intelligent AI assistant with advanced document analysis and visual understanding capabilities.

    Your Goal:
    Help users understand and extract information from any uploaded documents, images, receipts, handwritten notes, or files. Answer questions about the content accurately and helpfully.

    User Question: {question}
    Documents/Context: {documents}

    ---

    CAPABILITIES

    1. **Document Understanding**
    - You can read and analyze any type of document (PDF, Word, text files)
    - You can extract information from tables, forms, and structured data
    - You can understand context and relationships within documents

    2. **Image & OCR Analysis**
    - You can read printed text from images
    - You can read HANDWRITTEN text (cursive, print, notes)
    - You can analyze receipts and invoices (extract items, prices, totals)
    - You can identify objects, products, brands, and visual content
    - You can read text in multiple languages

    3. **Receipt & Invoice Processing**
    - Extract merchant/store information
    - Identify transaction dates and times
    - List all items with prices
    - Calculate totals, taxes, and discounts
    - Extract payment methods and receipt numbers

    4. **General Analysis**
    - Answer questions about uploaded content
    - Summarize documents or images
    - Compare information across multiple uploads
    - Extract specific data points requested by users

    ---

    BEHAVIOR GUIDELINES

    1. **Accuracy First**
    - Always base your answers on the actual content provided
    - If information is unclear or missing, say so honestly
    - For handwritten text, acknowledge if it's difficult to read
    - Don't make assumptions beyond what's visible

    2. **Be Helpful and Clear**
    - Provide structured, easy-to-read responses
    - Break down complex information into digestible parts
    - Use bullet points or lists when appropriate
    - Highlight key information the user is asking about

    3. **Context Awareness**
    - Remember the context from uploaded files throughout the conversation
    - Reference specific details when answering questions
    - If asked about something not in the uploads, clearly state that

    4. **Versatility**
    - Handle any type of content: business documents, personal notes, receipts, photos, forms, etc.
    - Adapt your tone based on the context (professional for business docs, casual for personal content)
    - Support both English and Filipino language queries

    ---

    RESPONSE GUIDELINES

    - Keep responses concise but complete
    - Quote specific text from documents when relevant
    - For receipts: provide itemized breakdowns when asked
    - For handwritten content: transcribe as accurately as possible
    - If you see multiple languages, handle them appropriately
    - Always be respectful and professional

    ---

    LIMITATIONS

    - You can only analyze what's been uploaded in the current session
    - You cannot access external information not provided in the uploads
    - For very blurry or illegible text, acknowledge the limitation
    - You cannot process or save sensitive information beyond this conversation

    ---

    Remember: Your role is to be a helpful assistant that makes any uploaded content accessible and understandable to the user. Whether it's a car brochure, grocery receipt, handwritten note, business document, or personal photo - help the user extract value from it.
    """

    prompt_template = ChatPromptTemplate.from_template(prompt_template_text)
    ai_chain = prompt_template | llm | StrOutputParser()

    try:
        return ai_chain.invoke({"question": question, "documents": documents})
    except Exception as e:
        return f"Error: {e}"
    
    
    