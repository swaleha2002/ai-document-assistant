import streamlit as st
import os
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import tempfile

# Page setup
st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🤖 AI Document Research Assistant</div>', unsafe_allow_html=True)
st.write("Upload documents and ask questions about their content!")

# Sidebar for configuration
with st.sidebar:
    st.header("🔧 Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Get your key from platform.openai.com")
    
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
        st.markdown('<div class="success-box">✅ API Key configured</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.header("ℹ️ How to Use")
    st.write("""
    1. Enter your OpenAI API key
    2. Upload a PDF or text file
    3. Click 'Process Document'
    4. Ask questions about the content
    """)
    
    st.markdown("---")
    st.header("📊 Sample Questions")
    st.write("""
    - What are the main points?
    - Summarize this document
    - What are the key findings?
    - Explain the methodology
    - What conclusions are reached?
    """)

# Main content area
if not api_key:
    st.warning("🔑 Please enter your OpenAI API key in the sidebar to continue")
    st.stop()

# Initialize session state
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'processed' not in st.session_state:
    st.session_state.processed = False

# File upload section
st.header("📄 Step 1: Upload Document")
uploaded_file = st.file_uploader(
    "Choose a PDF or text file",
    type=['pdf', 'txt'],
    help="Supported formats: PDF, Text"
)

if uploaded_file and not st.session_state.processed:
    if st.button("🚀 Process Document", type="primary"):
        with st.spinner("Processing document... This may take a minute."):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                # Load document based on type
                if uploaded_file.type == "application/pdf":
                    loader = PyPDFLoader(tmp_path)
                else:
                    loader = TextLoader(tmp_path)
                
                documents = loader.load()
                
                # Split text into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                texts = text_splitter.split_documents(documents)
                
                # Create embeddings and vector store
                embeddings = OpenAIEmbeddings()
                st.session_state.vectorstore = Chroma.from_documents(
                    texts, 
                    embeddings,
                    persist_directory="./chroma_db"
                )
                
                st.session_state.processed = True
                st.success(f"✅ Document processed successfully! Loaded {len(texts)} text chunks.")
                
                # Show document info
                with st.expander("📋 Document Information"):
                    st.write(f"**File name:** {uploaded_file.name}")
                    st.write(f"**File size:** {uploaded_file.size} bytes")
                    st.write(f"**Text chunks created:** {len(texts)}")
                    st.write(f"**Approximate pages:** {len(documents)}")
                
            except Exception as e:
                st.error(f"Error processing document: {str(e)}")

# Q&A section
if st.session_state.processed:
    st.header("💬 Step 2: Ask Questions")
    
    # Question input
    question = st.text_area(
        "Enter your question about the document:",
        placeholder="e.g., What are the main findings of this research?",
        height=100
    )
    
    # Example questions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Summarize"):
            question = "Provide a comprehensive summary of the main points and key findings."
    with col2:
        if st.button("🔍 Key Points"):
            question = "What are the most important key points or takeaways?"
    with col3:
        if st.button("🎯 Conclusions"):
            question = "What conclusions or recommendations are presented?"
    
    if question:
        with st.spinner("🔍 Searching document and generating answer..."):
            try:
                # Create QA chain
                qa_chain = RetrievalQA.from_chain_type(
                    llm=OpenAI(temperature=0.3),  # Lower temperature for more factual answers
                    chain_type="stuff",
                    retriever=st.session_state.vectorstore.as_retriever(search_kwargs={"k": 3}),
                    return_source_documents=True
                )
                
                # Get answer
                result = qa_chain({"query": question})
                
                # Display answer
                st.subheader("💡 Answer:")
                st.write(result["result"])
                
                # Show source documents
                with st.expander("📚 Source References"):
                    for i, doc in enumerate(result["source_documents"]):
                        st.write(f"**Source {i+1}:**")
                        st.write(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                        st.write("---")
                        
            except Exception as e:
                st.error(f"Error generating answer: {str(e)}")

else:
    # Welcome message when no document is processed
    st.info("👆 Please upload a document to get started!")
    
    # Sample document section for testing
    with st.expander("🧪 Don't have a document? Try with sample text"):
        sample_text = """
        Artificial Intelligence in Healthcare: Research Report
        
        Executive Summary:
        This report examines the current state of AI applications in healthcare. Key findings indicate that AI can improve diagnostic accuracy by 30-40% compared to traditional methods. Machine learning algorithms are particularly effective in medical imaging analysis.
        
        Main Findings:
        1. AI-powered diagnostic tools show 95% accuracy in detecting early-stage diseases
        2. Natural language processing can reduce administrative workload by 50%
        3. Predictive analytics help identify at-risk patients 6 months earlier than conventional methods
        
        Challenges:
        - Data privacy concerns remain significant
        - Integration with existing healthcare systems is complex
        - Regulatory approval processes are lengthy
        
        Recommendations:
        Healthcare providers should invest in AI training for staff and develop clear implementation strategies. Further research is needed on long-term outcomes of AI-assisted diagnoses.
        
        Conclusion:
        AI has transformative potential in healthcare but requires careful implementation and ongoing evaluation.
        """
        
        if st.button("Use Sample Text for Testing"):
            # Create a temporary text file with sample content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
                tmp_file.write(sample_text.encode())
                tmp_path = tmp_file.name
            
            with st.spinner("Processing sample document..."):
                try:
                    loader = TextLoader(tmp_path)
                    documents = loader.load()
                    
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200
                    )
                    texts = text_splitter.split_documents(documents)
                    
                    embeddings = OpenAIEmbeddings()
                    st.session_state.vectorstore = Chroma.from_documents(
                        texts, 
                        embeddings,
                        persist_directory="./chroma_db"
                    )
                    
                    st.session_state.processed = True
                    st.success("✅ Sample document loaded! You can now ask questions.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using LangChain, ChromaDB, and Streamlit</p>
    <p><small>AI Document Research Assistant v1.0</small></p>
</div>
""", unsafe_allow_html=True)