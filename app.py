import streamlit as st
import google.generativeai as genai
import os
import io
import re
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches
from fpdf import FPDF

# --- Google Gemini API Configuration ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# Function to convert LaTeX to Image (Advanced Method)
def latex_to_image(latex_str):
    """Converts a LaTeX string to a BytesIO image object"""
    try:
        fig = plt.figure(figsize=(4, 0.5))
        plt.text(0.5, 0.5, f"${latex_str}$", size=15, ha='center', va='center')
        plt.axis('off')
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0.05, transparent=True)
        img_buf.seek(0)
        plt.close(fig)
        return img_buf
    except:
        return None

def extract_title(pdf_path):
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        prompt = "Provide ONLY the exact title of this research paper. No extra text or formatting."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text.strip()
    except:
        return "Research_Summary"

def generate_summary(pdf_path, language):
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        prompt = f"Analyze this PDF and provide a deep academic summary in {language}. Use LaTeX for all equations."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def explain_math_deeply(pdf_path, language):
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        prompt = f"Break down every mathematical equation in this paper step-by-step in {language} using LaTeX."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def generate_citation(pdf_path, citation_style):
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        style = "IEEE format" if citation_style == "IEEE Format" else "BibTeX entry"
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        prompt = f"Generate a {style} citation for this paper."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- Export Utilities (Updated with Image Support) ---
def create_docx(title, summary, math, citation):
    doc = Document()
    doc.add_heading(title, level=1)
    
    sections = [("Research Summary", summary), ("Mathematical Breakdown", math), ("Citation", citation)]
    
    for sec_title, content in sections:
        if content:
            doc.add_heading(sec_title, level=2)
            # Find LaTeX formulas $...$ or $$...$$
            parts = re.split(r'(\$\$.*?\$\$|\$.*?\$)', content, flags=re.DOTALL)
            p = doc.add_paragraph()
            for part in parts:
                if part.startswith('$'):
                    latex = part.replace('$', '')
                    img = latex_to_image(latex)
                    if img:
                        p.add_run().add_picture(img, width=Inches(1.5))
                else:
                    p.add_run(part)
    
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def create_pdf(title, summary, math, citation):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', size=16)
    pdf.multi_cell(0, 10, txt=title.encode('ascii', 'ignore').decode('ascii'))
    
    content_combined = f"Summary:\n{summary}\n\nMath:\n{math}\n\nCitation:\n{citation}"
    pdf.set_font("Helvetica", size=10)
    # Simple clean text for PDF as FPDF doesn't support inline images easily
    clean_text = content_combined.replace('$', '').encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 7, txt=clean_text)
    
    return io.BytesIO(pdf.output())

# --- Streamlit UI Layout ---
st.set_page_config(page_title="Research Summarizer", page_icon="🔬", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(250, 250, 250, 0.9); color: #555555; text-align: center; padding: 10px; border-top: 1px solid #e0e0e0; z-index: 100; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

st.title("🔬 Smart Research Paper Summarizer")
st.write("Professional academic analysis powered by Gemini 1.5 Flash Lite.")
st.write("---")

language_opt = st.selectbox("Select Output Language:", ["English", "සිංහල (Sinhala)", "한국어 (Korean)"])
uploaded_file = st.file_uploader("Upload Research Paper (PDF):", type="pdf")

if uploaded_file is not None:
    if "paper_title" not in st.session_state: st.session_state.paper_title = None
    if "summary_text" not in st.session_state: st.session_state.summary_text = None
    if "math_text" not in st.session_state: st.session_state.math_text = None
    if "citation_text" not in st.session_state: st.session_state.citation_text = None
        
    temp_filename = "temp_stable_paper.pdf"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    if st.button("Generate Summary"):
        with st.spinner("Summarizing..."):
            st.session_state.paper_title = extract_title(temp_filename)
            st.session_state.summary_text = generate_summary(temp_filename, language_opt)
    
    if st.session_state.summary_text:
        st.write("---")
        st.markdown(f"### 📄 {st.session_state.paper_title}")
        st.markdown(st.session_state.summary_text)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Explain Mathematics"):
                with st.spinner("Analyzing math..."):
                    st.session_state.math_text = explain_math_deeply(temp_filename, language_opt)
        with col2:
            citation_style = st.radio("Style:", ["IEEE Format", "BibTeX (LaTeX)"])
            if st.button("Generate Citation"):
                with st.spinner("Generating citation..."):
                    st.session_state.citation_text = generate_citation(temp_filename, citation_style)
                    
        if st.session_state.math_text: st.info(st.session_state.math_text)
        if st.session_state.citation_text: st.success(st.session_state.citation_text)

        st.write("---")
        st.subheader("💾 Export Document")
        export_format = st.radio("Select Format:", ["Word (.docx)", "PDF (.pdf)"], horizontal=True)
        
        safe_name = "".join([c for c in st.session_state.paper_title if c.isalnum() or c in (' ', '_')]).strip()
        
        if export_format == "Word (.docx)":
            docx_io = create_docx(st.session_state.paper_title, st.session_state.summary_text, st.session_state.math_text, st.session_state.citation_text)
            st.download_button(label="📥 Download DOCX (with Real Equations)", data=docx_io, file_name=f"{safe_name}.docx")
        else:
            pdf_io = create_pdf(st.session_state.paper_title, st.session_state.summary_text, st.session_state.math_text, st.session_state.citation_text)
            st.download_button(label="📥 Download PDF", data=pdf_io, file_name=f"{safe_name}.pdf")

    if os.path.exists(temp_filename): os.remove(temp_filename)

st.markdown(f"""<div class="footer"><p>Developed by <b>Sankalpa Lokuliyanage</b> | Kyungpook National University</p></div>""", unsafe_allow_html=True)