import streamlit as st
import google.generativeai as genai
import os
import io
from docx import Document
from fpdf import FPDF

# --- Google Gemini API Configuration ---
# Securely fetching the API Key from Streamlit Secrets
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

def extract_title(pdf_path):
    """Identifies the research paper title using Gemini 1.5 Flash"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        # Using the stable 1.5 Flash model for higher quota
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        prompt = "Provide ONLY the exact title of this research paper. No extra text or formatting."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text.strip()
    except Exception:
        return "Research_Summary"

def generate_summary(pdf_path, language):
    """Generates a deep, structured summary of the research paper"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        
        # Language instructions
        if language == "සිංහල (Sinhala)":
            lang_instr = "Write a comprehensive academic summary in Sinhala. Explain formulas in LaTeX."
        elif language == "한국어 (Korean)":
            lang_instr = "Write a professional academic summary in Korean (formal style). Explain formulas in LaTeX."
        else:
            lang_instr = "Write a comprehensive academic summary in English."

        prompt = f"""
        You are an expert research professor. Analyze this PDF and provide a deep summary:
        1. Research Objectives: The core problem and why it matters.
        2. Methodology: Detailed explanation of the approach/algorithms.
        3. Mathematical Foundations: List and explain key equations using LaTeX ($...$ or $$...$$).
        4. Findings: Major results and data outcomes.
        5. Conclusion: Takeaways and future research directions.
        
        Language: {lang_instr}
        """

        model = genai.GenerativeModel('gemini-flash-lite-latest')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def explain_math_deeply(pdf_path, language):
    """Provides a detailed breakdown of all math found in the paper"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        prompt = f"Break down every mathematical equation in this paper step-by-step. Explain variables and logic in {language} using LaTeX."
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def generate_citation(pdf_path, citation_style):
    """Generates citation based on IEEE or BibTeX format"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        style = "IEEE format" if citation_style == "IEEE Format" else "BibTeX entry"
        prompt = f"Extract metadata and generate a {style} citation for this paper."
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- Export Utilities ---
def create_docx(title, summary, math, citation):
    """Creates a Word document including summary, math analysis, and citation"""
    doc = Document()
    doc.add_heading(title, level=1)
    
    doc.add_heading('Research Summary', level=2)
    doc.add_paragraph(summary)
    
    if math:
        doc.add_heading('Mathematical Breakdown', level=2)
        doc.add_paragraph(math)
        
    if citation:
        doc.add_heading('Citation', level=2)
        doc.add_paragraph(citation)
        
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_pdf(title, summary, math, citation):
    """Creates a PDF document including all generated content"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", 'B', size=16)
    safe_title = title.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 10, txt=safe_title)
    pdf.ln(5)
    
    # Content sections
    sections = [("Research Summary", summary), ("Mathematical Breakdown", math), ("Citation", citation)]
    
    for sec_title, content in sections:
        if content:
            pdf.set_font("Helvetica", 'B', size=12)
            pdf.cell(0, 10, txt=sec_title, ln=True)
            pdf.set_font("Helvetica", size=10)
            safe_content = content.encode('ascii', 'ignore').decode('ascii')
            pdf.multi_cell(0, 7, txt=safe_content)
            pdf.ln(3)
            
    return io.BytesIO(pdf.output())

# --- Streamlit UI Layout ---
st.set_page_config(page_title="Research Summarizer", page_icon="🔬", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(250, 250, 250, 0.9); color: #555555; text-align: center; padding: 10px; border-top: 1px solid #e0e0e0; z-index: 100; font-size: 14px; }
    @media (prefers-color-scheme: dark) { .footer { background-color: rgba(17, 17, 17, 0.9); color: #bbbbbb; border-top: 1px solid #333333; } }
    </style>
""", unsafe_allow_html=True)

st.title("🔬 Smart Research Paper Summarizer")
st.write("Professional academic analysis powered by Gemini 1.5 Flash.")
st.write("---")

# User Inputs
st.subheader("Configuration & Upload")
language_opt = st.selectbox("Select Output Language:", ["English", "සිංහල (Sinhala)", "한국어 (Korean)"])
uploaded_file = st.file_uploader("Upload Research Paper (PDF):", type="pdf")

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if "paper_title" not in st.session_state: st.session_state.paper_title = None
    if "summary_text" not in st.session_state: st.session_state.summary_text = None
    if "math_text" not in st.session_state: st.session_state.math_text = None
    if "citation_text" not in st.session_state: st.session_state.citation_text = None
        
    temp_filename = "temp_stable_paper.pdf"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    if st.button("Generate Summary"):
        with st.spinner("Summarizing paper... This may take a few seconds."):
            st.session_state.paper_title = extract_title(temp_filename)
            st.session_state.summary_text = generate_summary(temp_filename, language_opt)
            st.session_state.math_text = None 
            st.session_state.citation_text = None

    if st.session_state.summary_text:
        st.write("---")
        st.markdown(f"### 📄 {st.session_state.paper_title}")
        st.markdown(st.session_state.summary_text)
        st.write("---")
        
        # Tools in Columns
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🧮 Mathematical Breakdown")
            if st.button("Explain Mathematics"):
                with st.spinner("Analyzing math..."):
                    st.session_state.math_text = explain_math_deeply(temp_filename, language_opt)
        with col2:
            st.subheader("📚 Reference & Citation")
            citation_style = st.radio("Style:", ["IEEE Format", "BibTeX (LaTeX)"])
            if st.button("Generate Citation"):
                with st.spinner("Formatting reference..."):
                    st.session_state.citation_text = generate_citation(temp_filename, citation_style)
                    
        if st.session_state.math_text:
            st.write("---")
            st.info("Mathematical Breakdown Output:")
            st.markdown(st.session_state.math_text)
            
        if st.session_state.citation_text:
            st.write("---")
            st.success("Generated Citation:")
            if "BibTeX" in citation_style: st.code(st.session_state.citation_text, language="latex")
            else: st.markdown(st.session_state.citation_text)

        # --- Export Section (NOW AT THE END) ---
        st.write("---")
        st.subheader("💾 Export Document")
        st.write("This will include the summary and any additional math/citation analysis generated above.")
        export_format = st.radio("Select Format:", ["Word (.docx)", "PDF (.pdf)"], horizontal=True)
        
        safe_name = "".join([c for c in st.session_state.paper_title if c.isalnum() or c in (' ', '_')]).strip()
        
        if export_format == "Word (.docx)":
            docx_io = create_docx(st.session_state.paper_title, st.session_state.summary_text, st.session_state.math_text, st.session_state.citation_text)
            st.download_button(label="📥 Download Complete DOCX", data=docx_io, file_name=f"{safe_name}.docx")
        else:
            pdf_io = create_pdf(st.session_state.paper_title, st.session_state.summary_text, st.session_state.math_text, st.session_state.citation_text)
            st.download_button(label="📥 Download Complete PDF", data=pdf_io, file_name=f"{safe_name}.pdf")

    if os.path.exists(temp_filename): os.remove(temp_filename)
else:
    st.info("Please upload a PDF file to begin.")

# Professional Footer
st.markdown(
    f"""<div class="footer"><p>Developed by <b>Sankalpa Lokuliyanage</b> | Kyungpook National University</p></div>""",
    unsafe_allow_html=True
)