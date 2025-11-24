import streamlit as st
import tempfile
import os
import requests
from PyPDF2 import PdfReader
from docx import Document
import csv

# Set up the page
st.set_page_config(page_title="Local GPT Assistant", page_icon="🤖")
st.title("Personal Query Assistant")
st.write("Upload **multiple documents** and ask questions across all of them!")

# Initialize everything
if 'documents_processed' not in st.session_state:
    st.session_state.documents_processed = []  # List of file names
    st.session_state.all_documents = {}  # Dictionary to store each document's content
    st.session_state.total_text = ""  # Combined text from all documents

# File upload section
st.sidebar.header("📁 Upload Multiple Documents")
uploaded_files = st.sidebar.file_uploader(
    "Select multiple files (TXT, PDF, CSV, DOCX)",
    type=['txt', 'pdf', 'csv', 'docx'],
    accept_multiple_files=True,
    help="You can select multiple files at once!"
)

# Process files when button is clicked
if uploaded_files:
    st.sidebar.write(f"📂 **Selected files:** {len(uploaded_files)} files")
    for uploaded_file in uploaded_files:
        st.sidebar.write(f" - {uploaded_file.name}")

if uploaded_files and st.sidebar.button("Process All Files"):
    for uploaded_file in uploaded_files:
        # Skip if already processed
        if uploaded_file.name in st.session_state.documents_processed:
            st.sidebar.info(f"⏭️ {uploaded_file.name} already processed")
            continue
            
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        file_text = ""
        
        # Read the file based on type
        try:
            if uploaded_file.name.endswith('.pdf'):
                reader = PdfReader(tmp_file_path)
                for page in reader.pages:
                    file_text += page.extract_text() + "\n"
                    
            elif uploaded_file.name.endswith('.docx'):
                doc = Document(tmp_file_path)
                for paragraph in doc.paragraphs:
                    file_text += paragraph.text + "\n"
                    
            elif uploaded_file.name.endswith('.csv'):
                with open(tmp_file_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    for row in csv_reader:
                        file_text += ", ".join(row) + "\n"
                        
            elif uploaded_file.name.endswith('.txt'):
                with open(tmp_file_path, 'r', encoding='utf-8') as f:
                    file_text = f.read()
            
            # Store each document separately and combined
            st.session_state.all_documents[uploaded_file.name] = file_text
            st.session_state.documents_processed.append(uploaded_file.name)
            st.session_state.total_text += f"\n\n--- Document: {uploaded_file.name} ---\n{file_text}"
            
            st.sidebar.success(f"Processed {uploaded_file.name}")
            
        except Exception as e:
            st.sidebar.error(f"Error processing {uploaded_file.name}: {str(e)}")
        
        # Clean up temporary file
        os.unlink(tmp_file_path)

# Show processed files
if st.session_state.documents_processed:
    st.sidebar.header("Processed Documents")
    st.sidebar.write(f"**Total documents:** {len(st.session_state.documents_processed)}")
    
    for file_name in st.session_state.documents_processed:
        st.sidebar.write(f"{file_name}")

# Clear all documents
if st.session_state.documents_processed and st.sidebar.button("Clear All Documents"):
    st.session_state.documents_processed = []
    st.session_state.all_documents = {}
    st.session_state.total_text = ""
    st.sidebar.success("All documents cleared!")
    st.rerun()

# Question answering section
st.header("💬 Ask Questions Across All Documents")
question = st.text_input("Enter your question about the uploaded documents:")

if st.button("🔍 Get Answer") and question:
    if not st.session_state.documents_processed:
        st.warning("Please upload and process some documents first!")
    else:
        with st.spinner(f"🔍 Searching through {len(st.session_state.documents_processed)} documents..."):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": "Bearer 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",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b:free",
                        "messages": [
                            {
                                "role": "system",
                                "content": """You are a helpful assistant that answers questions based ONLY on the provided documents. 
                                IMPORTANT RULES:
                                1. Only use information from the provided documents
                                2. If the answer cannot be found in ANY of the documents, say 'I don't know based on the provided documents.'
                                3. If information comes from multiple documents, mention that
                                4. Do not use any external knowledge"""
                            },
                            {
                                "role": "user", 
                                "content": f"""I have {len(st.session_state.documents_processed)} documents. Here is the combined content:

{st.session_state.total_text}

Question: {question}

Please answer based ONLY on the documents above:"""
                            }
                        ],
                        "max_tokens": 400,
                        "temperature": 0.1
                    }
                )
                
                if response.status_code == 200:
                    answer = response.json()['choices'][0]['message']['content'].strip()
                    st.subheader("Chatbot Answer:")
                    st.write(answer)
                    
                    # Show which documents were available
                    st.subheader("Documents Searched:")
                    for doc_name in st.session_state.documents_processed:
                        st.write(f"{doc_name}")
                
                else:
                    st.error(f"Sorry, there was an API error. Status code: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Instructions
with st.expander("ℹHow to use this multi-document assistant"):
    st.markdown("""
    ## How to Use this ChatBot
    
    1. **Upload Multiple Documents**: 
       - Click 'Browse files' in the sidebar
       - Select multiple files at once (PDF, TXT, CSV, DOCX)
       - You can upload different types together
    
    2. **Process Files**: 
       - Click 'Process All Files' to analyze all documents
       - Each file is stored separately
    
    3. **Ask Questions**: 
       - Ask questions that might span across multiple documents
       - The assistant will search through ALL uploaded documents
       - Answers are based only on your documents
    
    4. **Clear Documents**: 
       - Use 'Clear All Documents' to start fresh
    
    ## Examples of Multi-Document Questions:
    - "What are the main topics covered across all documents?"
    - "Compare the information in different documents"
    - "What do all documents say about [specific topic]?"
    - "Find common themes in the documents"
    
    The system will search through all your documents and provide answers based on the combined information!

    """)

