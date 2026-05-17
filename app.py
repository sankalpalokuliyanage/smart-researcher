import streamlit as st
import google.generativeai as genai
import os
import io
import re
import matplotlib.pyplot as plt
import textwrap
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF

# --- Google Gemini API Configuration ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# සමීකරණ පින්තූරයක් බවට පත් කරන ශ්‍රිතය (High Quality)
def latex_to_image(latex_str):
    try:
        # සමීකරණය පිරිසිදු කිරීම
        latex_str = latex_str.replace('$', '').strip()
        fig = plt.figure(figsize=(6, 0.8)) # ටිකක් ලොකු size එකක් ගත්තා පැහැදිලි වෙන්න
        plt.text(0.5, 0.5, f"${latex_str}$", size=18, ha='center', va='center')
        plt.axis('off')
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0.1, transparent=True, dpi=300)
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
        # විග්‍රහය ලස්සනට එන්න prompt එක දියුණු කළා
        prompt = f"""
        You are a world-class research professor. Analyze this PDF and provide a highly structured, deep academic summary in {language}.
        Structure your response with:
        1. 🌟 OVERVIEW: A professional introduction to the research.
        2. 🎯 CORE OBJECTIVES: What the researchers aimed to achieve.
        3. ⚙️ METHODOLOGY: A step-by-step breakdown of the approach.
        4. 📊 KEY FINDINGS: The most important results discovered.
        5. 💡 CONCLUSION: Final takeaways and significance.
        
        IMPORTANT: Use LaTeX ($...$) for every single mathematical symbol and formula.
        """
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def explain_math_deeply(pdf_path, language):
    try:
        uploaded_gemini_file = genai.upload_file(path=pdf_path)
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        # ගණිතමය විග්‍රහය සුපිරියටම එන්න මෙන්න prompt එක
        prompt = f"""
        As a Mathematics Expert, find every equation in this paper and provide a MASTERCLASS explanation in {language}.
        For each equation:
        1. State the formula clearly using LaTeX.
        2. Explain each variable and constant.
        3. Describe the logic and derivation behind the formula.
        4. Explain why this specific equation is critical for the research.
        
        Use LaTeX ($...$ or $$...$$) for ALL mathematical notations.
        """
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
        prompt = f"Generate a professional {style} citation for this research paper."
        response = model.generate_content([uploaded_gemini_file, prompt])
        genai.delete_file(uploaded_gemini_file.name)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- Export Utilities ---

def create_docx(title, summary, math, citation):
    doc = Document()
    
    # Title - Center Aligned
    t = doc.add_heading(title, level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    sections = [("📄 RESEARCH SUMMARY", summary), ("🧮 MATHEMATICAL ANALYSIS", math), ("📚 CITATION", citation)]
    
    for sec_title, content in sections:
        if content:
            doc.add_heading(sec_title, level=1)
            # LaTeX කොටස් වෙන් කර ගැනීම
            parts = re.split(r'(\$\$.*?\$\$|\$.*?\$)', content, flags=re.DOTALL)
            p = doc.add_paragraph()
            
            for part in parts:
                if part.startswith('$'):
                    img = latex_to_image(part)
                    if img:
                        p.add_run().add_picture(img, width=Inches(2.5)) # සමීකරණය පින්තූරයක් ලෙස
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
    pdf.multi_cell(0, 10, txt=title.encode('ascii', 'ignore').decode('ascii'), align='C')
    pdf.ln(10)
    
    def write_section(pdf, header, text):
        if not text: return
        pdf.set_font("Helvetica", 'B', size=12)
        pdf.set_text_color(0, 51, 102) # Dark blue for headers
        pdf.cell(0, 10, txt=header, ln=True)
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(0, 0, 0)
        clean_text = text.replace('$', '').encode('ascii', 'ignore').decode('ascii')
        wrapped = textwrap.fill(clean_text, width=85)
        pdf.multi_cell(0, 7, txt=wrapped)
        pdf.ln(5)

    write_section(pdf, "RESEARCH SUMMARY", summary)
    write_section(pdf, "MATHEMATICAL ANALYSIS", math)
    write_section(pdf, "CITATION", citation)
    
    return io.BytesIO(pdf.output())

# --- Streamlit UI ---
st.set_page_config(page_title="Smart Researcher", page_icon="🔬", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; padding: 10px; font-size: 14px; background: rgba(255,255,255,0.8); }
    </style>
""", unsafe_allow_html=True)

st.title("🔬 Smart Research Paper Summarizer")
st.write("Professional analysis with high-quality mathematical rendering.")
st.write("---")

language_opt = st.selectbox("Select Language:", ["English", "සිංහල (Sinhala)", "한국어 (Korean)"])
uploaded_file = st.file_uploader("Upload PDF:", type="pdf")

if uploaded_file is not None:
    if "paper_title" not in st.session_state: st.session_state.paper_title = None
    if "summary_text" not in st.session_state: st.session_state.summary_text = None
    if "math_text" not in st.session_state: st.session_state.math_text = None
    if "citation_text" not in st.session_state: st.session_state.citation_text = None
        
    temp_filename = "temp_file.pdf"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    if st.button("🚀 Start Deep Analysis"):
        with st.spinner("Analyzing paper structure and content..."):
            st.session_state.paper_title = extract_title(temp_filename)
            st.session_state.summary_text = generate_summary(temp_filename, language_opt)
            st.session_state.math_text = None 
            st.session_state.citation_text = None

    if st.session_state.summary_text:
        st.markdown(f"## 📄 {st.session_state.paper_title}")
        st.markdown(st.session_state.summary_text)
        
        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧮 Explain All Mathematics"):
                with st.spinner("Deep diving into equations..."):
                    st.session_state.math_text = explain_math_deeply(temp_filename, language_opt)
        with col2:
            style = st.radio("Citation Style:", ["IEEE Format", "BibTeX"])
            if st.button("📚 Generate Citation"):
                st.session_state.citation_text = generate_citation(temp_filename, style)
                    
        if st.session_state.math_text: 
            st.info("### 📐 Mathematical Breakdown")
            st.markdown(st.session_state.math_text)
        if st.session_state.citation_text: 
            st.success("### 📖 Citation")
            st.code(st.session_state.citation_text)

        st.write("---")
        st.subheader("💾 Export Professional Report")
        fmt = st.radio("Format:", ["Word (.docx) - Best for Math", "PDF (.pdf)"], horizontal=True)
        
        safe_name = "".join([c for c in st.session_state.paper_title if c.isalnum() or c in (' ', '_')]).strip()
        
        if st.download_button(label=f"📥 Download {fmt}", 
                              data=create_docx(st.session_state.paper_title, st.session_state.summary_text, st.session_state.math_text, st.session_state.citation_text) if "Word" in fmt else create_pdf(st.session_state.paper_title, st.session_state.summary_text, st.session_state.math_text, st.session_state.citation_text), 
                              file_name=f"{safe_name}.docx" if "Word" in fmt else f"{safe_name}.pdf"):
            st.balloons()

    if os.path.exists(temp_filename): os.remove(temp_filename)

st.markdown("""<div class="footer">Developed by <b>Sankalpa Lokuliyanage</b> | KNU</div>""", unsafe_allow_html=True)