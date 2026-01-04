import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
import database  # Mengimpor file database.py
from docx import Document
from fpdf import FPDF
from io import BytesIO

# --- 1. SETUP KONFIGURASI ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API Key tidak ditemukan!")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

# Konfigurasi Halaman
st.set_page_config(page_title="InsightVision", layout="wide", page_icon="📸")

# --- 2. FUNGSI LOAD CSS EKSTERNAL ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("File style.css tidak ditemukan. Menggunakan tampilan standar.")

local_css("style.css")

# --- 3. FUNGSI EKSPOR (DOCX & PDF) ---
def buat_docx(teks):
    doc = Document()
    doc.add_heading('Laporan Analisis InsightVision', 0)
    doc.add_paragraph(teks)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def buat_pdf(teks):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Membersihkan karakter non-latin agar tidak error di FPDF
    clean_text = teks.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SIDEBAR RIWAYAT ---
with st.sidebar:
    st.title("InsightVision")
    st.markdown("---")
    st.subheader("📜 Riwayat Terakhir")
    riwayat = database.ambil_riwayat()
    if riwayat:
        for data in riwayat:
            with st.expander(f"📄 {data['nama_file']}"):
                st.caption(f"📅 {data['waktu_simpan']}")
                st.write(data['hasil_analisis'][:100] + "...")
    else:
        st.info("Belum ada riwayat.")

# --- 5. LOGIKA RESET ---
if "file_sebelumnya" not in st.session_state:
    st.session_state["file_sebelumnya"] = None

st.title("📸 InsightVision")
st.markdown("<p style='color: gray; font-size: 18px;'>Transformasi Gambar Menjadi Wawasan Cerdas</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Seret dan lepaskan gambar di sini", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    if st.session_state["file_sebelumnya"] != uploaded_file.name:
        if 'hasil_terakhir' in st.session_state:
            del st.session_state['hasil_terakhir']
        st.session_state["file_sebelumnya"] = uploaded_file.name
        st.rerun()
else:
    if st.session_state["file_sebelumnya"] is not None:
        if 'hasil_terakhir' in st.session_state:
            del st.session_state['hasil_terakhir']
        st.session_state["file_sebelumnya"] = None
        st.rerun()

# --- 6. TAMPILAN UTAMA (KOLOM) ---
col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview Gambar", use_container_width=True)
        
        btn_analisis = st.button("🚀 Mulai Analisis Cerdas")
        
        if btn_analisis:
            with st.spinner("Menganalisis konten gambar..."):
                try:
                    prompt = """
                    Kamu adalah InsightVision. Berikan laporan analisis gambar yang sangat mendalam:
                    1. **📊 Ringkasan**: Deskripsi tingkat tinggi.
                    2. **🔍 Detail Visual**: Objek, warna, komposisi.
                    3. **📝 Teks/OCR**: Ekstraksi semua tulisan yang terlihat.
                    4. **💡 Interpretasi**: Konteks dan saran pakar praktis.
                    Gunakan Bahasa Indonesia profesional.
                    """
                    response = model.generate_content([prompt, image])
                    st.session_state['hasil_terakhir'] = response.text
                    database.simpan_ke_db(uploaded_file.name, response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

with col2:
    if 'hasil_terakhir' in st.session_state:
        st.success("Analisis Berhasil!")
        st.markdown(st.session_state['hasil_terakhir'])
        
        # --- FITUR EKSPOR ---
        st.markdown("---")
        st.subheader("📥 Ekspor Laporan")
        
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            docx_data = buat_docx(st.session_state['hasil_terakhir'])
            st.download_button(
                label="📄 Download DOCX",
                data=docx_data,
                file_name=f"Insight_{uploaded_file.name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        with btn_col2:
            try:
                pdf_data = buat_pdf(st.session_state['hasil_terakhir'])
                st.download_button(
                    label="📕 Download PDF",
                    data=pdf_data,
                    file_name=f"Insight_{uploaded_file.name}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error("Karakter teks tidak didukung untuk PDF standar.")

# --- 7. CHAT MULTIMODAL ---
if uploaded_file is not None and 'hasil_terakhir' in st.session_state:
    st.markdown("---")
    st.subheader("💬 Diskusi Lanjutan")
    user_question = st.text_input("Tanyakan detail spesifik tentang gambar ini:", key=f"chat_{uploaded_file.name}", placeholder="Contoh: Apa arti teks di pojok kanan?")

    if user_question:
        with st.chat_message("assistant"):
            with st.spinner("Mengkaji ulang..."):
                try:
                    chat_res = model.generate_content([
                        f"Konteks: {st.session_state['hasil_terakhir']}\n\nPertanyaan: {user_question}", 
                        image
                    ])
                    st.write(chat_res.text)
                except Exception as e:
                    st.error(f"Gagal merespon: {e}")

# Footer
st.markdown("<br><br><div class='footer'>InsightVision v1.1 | 2026</div>", unsafe_allow_html=True)
