import streamlit as st
import google.generativeai as genai
import os
import io
from docx import Document
from fpdf import FPDF

# --- Google Gemini API Configuration ---
# Fetching the API Key from Streamlit Secrets for security
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

def extract_title(pdf_path):
    """Extracts the research paper title using Gemini Vision/Text capabilities"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = "Analyze the attached research paper and provide ONLY the title of the paper. No other text."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text.strip()
    except Exception:
        return "Research_Summary"

def generate_summary(pdf_path, language):
    """Generates a highly detailed and structured academic summary"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        
        # Language instructions for the AI
        if language == "සිංහල (Sinhala)":
            lang_instruction = "Write a comprehensive and professional academic summary in Sinhala. Ensure technical terms are well-explained."
        elif language == "한국어 (Korean)":
            lang_instruction = "Write a comprehensive and professional academic summary in Korean (using academic/formal style)."
        else:
            lang_instruction = "Write a comprehensive and professional academic summary in English."

        # Enhanced Prompt for Better Explanation
        prompt = f"""
        You are an elite academic research professor. Analyze the attached research paper PDF thoroughly and provide a deep, well-structured summary.
        
        Please cover the following in great detail:
        
        # 📄 Comprehensive Research Analysis
        
        ### 🎯 1. Research Motivation & Core Objectives
        - What is the specific problem the authors are trying to solve?
        - Why is this research significant in the current field?
        
        ### ⚙️ 2. Detailed Methodology & Proposed Approach
        - Explain the framework, algorithms, or experimental setup used.
        - How does the proposed solution differ from existing work?
        
        ### 🧮 3. Critical Mathematical Foundations
        - Identify and explain the most important mathematical formulations or logic found in the paper.
        - (Use LaTeX $...$ for inline or $$...$$ for block equations).
        
        ### 📊 4. Key Results, Findings & Evaluation
        - What were the major outcomes? 
        - Summarize the performance metrics or data results presented.
        
        ### 💡 5. Conclusion & Future Implications
        - What are the final takeaways? 
        - What future research directions do the authors suggest?

        ---
        Language Constraint: {lang_instruction}
        """

        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def explain_math_deeply(pdf_path, language):
    """Provides a detailed step-by-step breakdown of mathematical formulas"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        prompt = f"Identify all math equations in this paper and provide a step-by-step breakdown of variables, derivations, and logic in {language} using LaTeX."
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def generate_citation(pdf_path, citation_style):
    """Generates an academic citation in IEEE or BibTeX format"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        style_instr = "IEEE format" if citation_style == "IEEE Format" else "BibTeX entry"
        prompt = f"Analyze the PDF and generate a {style_instr} citation for this research paper."
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- Export Document Utilities ---
def create_docx(title, text):
    """Creates a downloadable Word document stream"""
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_pdf(title, text):
    """Creates a downloadable PDF document stream"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', size=14)
    safe_title = title.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 10, txt=safe_title)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    safe_text = text.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 10, txt=safe_text)
    return io.BytesIO(pdf.output())

# --- Streamlit UI Configuration ---
st.set_page_config(page_title="Research Summarizer", page_icon="🔬", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(250, 250, 250, 0.9); color: #555555; text-align: center; padding: 10px; border-top: 1px solid #e0e0e0; z-index: 100; font-size: 14px; }
    @media (prefers-color-scheme: dark) { .footer { background-color: rgba(17, 17, 17, 0.9); color: #bbbbbb; border-top: 1px solid #333333; } }
    </style>
""", unsafe_allow_html=True)

st.title("🔬 Smart Research Paper Summarizer")
st.write("Upload a research paper to get a clean summary, extract mathematical formulations, and generate citations instantly.")
st.write("---")

st.subheader("Configuration & File Upload")
language_opt = st.selectbox("Select Output Language:", ["English", "සිංහල (Sinhala)", "한국어 (Korean)"])
uploaded_file = st.file_uploader("Upload Research Paper (PDF):", type="pdf")

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if "paper_title" not in st.session_state: st.session_state.paper_title = None
    if "summary_text" not in st.session_state: st.session_state.summary_text = None
    if "math_text" not in st.session_state: st.session_state.math_text = None
    if "citation_text" not in st.session_state: st.session_state.citation_text = None
        
    temp_filename = "temp_summarizer_paper.pdf"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    if st.button("Generate Summary"):
        with st.spinner("Extracting title and generating a deep summary..."):
            st.session_state.paper_title = extract_title(temp_filename)
            st.session_state.summary_text = generate_summary(temp_filename, language_opt)
            st.session_state.math_text = None 
            st.session_state.citation_text = None

    if st.session_state.summary_text:
        st.write("---")
        st.markdown(f"### 📄 {st.session_state.paper_title}")
        st.markdown(st.session_state.summary_text)
        st.write("---")
        
        st.subheader("💾 Export Document")
        export_format = st.radio("Select File Format:", ["Word (.docx)", "PDF (.pdf)"], horizontal=True)
        
        safe_filename = "".join([c for c in st.session_state.paper_title if c.isalnum() or c in (' ', '_')]).rstrip()
        
        if export_format == "Word (.docx)":
            docx_io = create_docx(st.session_state.paper_title, st.session_state.summary_text)
            st.download_button(label="📥 Download as DOCX", data=docx_io, file_name=f"{safe_filename}.docx")
        else:
            pdf_io = create_pdf(st.session_state.paper_title, st.session_state.summary_text)
            st.download_button(label="📥 Download as PDF", data=pdf_io, file_name=f"{safe_filename}.pdf")
            
        st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🧮 Mathematical Breakdown")
            if st.button("Explain Mathematics"):
                with st.spinner("Analyzing equations in depth..."):
                    st.session_state.math_text = explain_math_deeply(temp_filename, language_opt)
                    
        with col2:
            st.subheader("📚 Reference & Citation")
            citation_style = st.radio("Choose Format:", ["IEEE Format", "BibTeX (LaTeX)"])
            if st.button("Generate Citation"):
                with st.spinner("Generating citation..."):
                    st.session_state.citation_text = generate_citation(temp_filename, citation_style)
                    
        if st.session_state.math_text:
            st.info("Mathematical Breakdown Output:")
            st.markdown(st.session_state.math_text)
            
        if st.session_state.citation_text:
            st.success("Generated Citation:")
            if "BibTeX" in citation_style: st.code(st.session_state.citation_text, language="latex")
            else: st.markdown(st.session_state.citation_text)

    if os.path.exists(temp_filename): os.remove(temp_filename)
else:
    st.info("Please upload a PDF file to begin the analysis.")

st.markdown(
    f"""<div class="footer"><p>Developed by <b>Sankalpa Lokuliyanage</b> | Kyungpook National University</p></div>""",
    unsafe_allow_html=True
)