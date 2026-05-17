import streamlit as st
import google.generativeai as genai
import os
import io
from docx import Document
from fpdf import FPDF

# --- Google Gemini API Configuration ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

def extract_title(pdf_path):
    """PDF එකෙන් පත්‍රිකාවේ මාතෘකාව (Title) පමණක් හඳුනා ගැනීමට"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = "Analyze the attached research paper and provide ONLY the title of the paper. No other text."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text.strip()
    except:
        return "Research_Summary"

def generate_summary(pdf_path, language):
    """PDF එක කියවා මූලික සාරාංශය ලබාගැනීම"""
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        
        if language == "සිංහල (Sinhala)":
            lang_instruction = "Write the summary clearly in academic Sinhala. Keep mathematical formulas in standard LaTeX notation."
        elif language == "한국어 (Korean)":
            lang_instruction = "Write the summary professionally in academic Korean. Keep mathematical formulas in standard LaTeX notation."
        else:
            lang_instruction = "Write the summary clearly in academic English."

        prompt = f"""
        You are an expert academic research assistant. Analyze the attached research paper PDF.
        Provide a concise yet informative summary under the following clear sections:
        
        # 📄 Research Paper Summary
        
        ### 🎯 1. Main Objectives & Contributions
        - What is the core problem and proposed solution?
        
        ### ⚙️ 2. Methodology Overview
        - Briefly explain the core system, algorithm, or experimental approach.
        
        ### 🧮 3. Key Mathematical Equations Found
        - List all the critical mathematical formulas using standard LaTeX notation ($...$ or $$...$$).
        
        ### 📊 4. Key Findings & Conclusion
        - What are the major results and takeaways?
        
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
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        if language == "සිංහල (Sinhala)":
            lang_instruction = "Explain the mathematics step-by-step deeply in clear Sinhala."
        elif language == "한국어 (Korean)":
            lang_instruction = "Explain the mathematics step-by-step deeply in clear Korean."
        else:
            lang_instruction = "Explain the mathematics step-by-step deeply in English."

        prompt = f"Analyze the PDF and provide a thorough step-by-step deep dive of all math equations using LaTeX.\nLanguage: {lang_instruction}"
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def generate_citation(pdf_path, citation_style):
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        style_instruction = "IEEE style" if citation_style == "IEEE Format" else "BibTeX entry"
        prompt = f"Analyze the PDF and generate a {style_instruction} citation for this paper."
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- Export Utilities ---
def create_docx(title, text):
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def create_pdf(title, text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.multi_cell(0, 10, txt=title.encode('latin-1', 'ignore').decode('latin-1'))
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 10, txt=text.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output()

# --- Streamlit UI ---
st.set_page_config(page_title="Research Summarizer", page_icon="🔬", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(250, 250, 250, 0.9); color: #555555; text-align: center; padding: 10px; font-size: 14px; border-top: 1px solid #e0e0e0; z-index: 100; }
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
        with st.spinner("Processing title and summary..."):
            st.session_state.paper_title = extract_title(temp_filename)
            st.session_state.summary_text = generate_summary(temp_filename, language_opt)
            st.session_state.math_text = None 
            st.session_state.citation_text = None

    if st.session_state.summary_text:
        st.write("---")
        # පත්‍රිකාවේ Title එක UI එකේ පෙන්වීම (ඔයාගේ Image එකේ තියෙන තැනට සමානව)
        st.markdown(f"### 📄 {st.session_state.paper_title}")
        st.markdown(st.session_state.summary_text)
        st.write("---")
        
        st.subheader("💾 Export Document")
        export_format = st.radio("Select File Format:", ["Word (.docx)", "PDF (.pdf)"], horizontal=True)
        
        safe_filename = "".join([c for c in st.session_state.paper_title if c.isalnum() or c in (' ', '_')]).rstrip()
        
        if export_format == "Word (.docx)":
            docx_data = create_docx(st.session_state.paper_title, st.session_state.summary_text)
            st.download_button(label="📥 Download as DOCX", data=docx_data, file_name=f"{safe_filename}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            pdf_data = create_pdf(st.session_state.paper_title, st.session_state.summary_text)
            st.download_button(label="📥 Download as PDF", data=pdf_data, file_name=f"{safe_filename}.pdf", mime="application/pdf")
            
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🧮 Mathematical Breakdown")
            if st.button("Explain Mathematics"):
                with st.spinner("Analyzing math..."):
                    st.session_state.math_text = explain_math_deeply(temp_filename, language_opt)
        with col2:
            st.subheader("📚 Reference & Citation")
            citation_style = st.radio("Choose Format:", ["IEEE Format", "BibTeX (LaTeX)"])
            if st.button("Generate Citation"):
                with st.spinner("Generating citation..."):
                    st.session_state.citation_text = generate_citation(temp_filename, citation_style)
                    
        if st.session_state.math_text:
            st.write("---"); st.info("Mathematical Breakdown Output:"); st.markdown(st.session_state.math_text)
        if st.session_state.citation_text:
            st.write("---"); st.success("Generated Citation:")
            if "BibTeX" in citation_style: st.code(st.session_state.citation_text, language="latex")
            else: st.markdown(st.session_state.citation_text)

    if os.path.exists(temp_filename): os.remove(temp_filename)
else:
    st.info("Please upload a PDF file to begin the analysis.")

st.markdown("""<div class="footer"><p>Developed by <b>Sankalpa Lokuliyanage</b> | Kyungpook National University</p></div>""", unsafe_allow_html=True)