import os
import streamlit as st
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
import database  # Mengimpor file database.py

# --- 1. SETUP KONFIGURASI ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API Key tidak ditemukan! Pastikan file .env sudah benar.")
    st.stop()

genai.configure(api_key=api_key)

# Inisialisasi Model
model = genai.GenerativeModel('gemini-flash-latest')

# --- 2. UI STREAMLIT & SIDEBAR RIWAYAT ---
st.set_page_config(page_title="InsightVision GenAI", layout="wide")

with st.sidebar:
    st.title("📜 Riwayat Analisis")
    st.write("5 Analisis Terakhir:")
    riwayat = database.ambil_riwayat()
    if riwayat:
        for data in riwayat:
            with st.expander(f"📄 {data['nama_file']}"):
                st.caption(f"Waktu: {data['waktu_simpan']}")
                st.write(data['hasil_analisis'][:150] + "...")
    else:
        st.info("Belum ada riwayat analisis.")

# Tampilan Utama
st.title("📸 InsightVision")
st.subheader("GenAI Powered Image Analyzer")

# --- 3. LOGIKA RESET OTOMATIS SAAT GANTI GAMBAR ---
# Inisialisasi state untuk melacak file yang diunggah terakhir kali
if "file_sebelumnya" not in st.session_state:
    st.session_state["file_sebelumnya"] = None

# Komponen Upload Gambar
uploaded_file = st.file_uploader("Pilih file gambar (JPG, PNG, JPEG)...", type=["jpg", "png", "jpeg"])

# Cek jika file baru diunggah atau file dihapus
if uploaded_file is not None:
    if st.session_state["file_sebelumnya"] != uploaded_file.name:
        # Reset hasil analisis dan chat jika file berbeda dari sebelumnya
        if 'hasil_terakhir' in st.session_state:
            del st.session_state['hasil_terakhir']
        if 'chat_history' in st.session_state:
            st.session_state['chat_history'] = []
        
        # Update nama file yang sedang aktif
        st.session_state["file_sebelumnya"] = uploaded_file.name
        st.rerun() # Refresh UI agar bersih
else:
    # Jika file dihapus (klik tanda silang di uploader)
    if st.session_state["file_sebelumnya"] is not None:
        if 'hasil_terakhir' in st.session_state:
            del st.session_state['hasil_terakhir']
        st.session_state["file_sebelumnya"] = None
        st.rerun()

# Layout Kolom
col1, col2 = st.columns([1, 1])

with col1:
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar yang diunggah", use_container_width=True)

# --- 4. TAHAP PROMPT ENGINEERING ---
prompt_awal = """
Kamu adalah InsightVision, asisten AI pakar analisis gambar tingkat lanjut.
Berikan output dalam format Markdown yang rapi dengan struktur:
1. **📊 Ringkasan Eksekutif**: Jelaskan singkat isi gambar.
2. **🔍 Detail Visual**: Objek utama, warna, dan suasana.
3. **📝 Ekstraksi Teks (OCR)**: Tulis teks yang terbaca (atau beri tahu jika tidak ada).
4. **💡 Wawasan & Rekomendasi**: Interpretasi konteks dan 2 saran praktis.

Gunakan Bahasa Indonesia yang profesional.
"""

with col2:
    if uploaded_file is not None:
        if st.button("Analisis Gambar Sekarang"):
            with st.spinner("InsightVision sedang memproses gambar..."):
                try:
                    response = model.generate_content([prompt_awal, image])
                    st.session_state['hasil_terakhir'] = response.text
                    
                    database.simpan_ke_db(uploaded_file.name, response.text)
                    st.success("Analisis Selesai & Tersimpan!")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

        # Menampilkan Hasil Analisis
        if 'hasil_terakhir' in st.session_state:
            st.markdown(st.session_state['hasil_terakhir'])

# --- 5. TAHAP INTEGRASI MULTIMODAL (CHAT) ---
if uploaded_file is not None and 'hasil_terakhir' in st.session_state:
    st.markdown("---")
    st.subheader("💬 Tanya Lebih Lanjut")
    
    # Gunakan key unik agar text_input ter-reset jika gambar ganti
    user_question = st.text_input("Tanyakan sesuatu tentang gambar ini:", key=f"chat_{uploaded_file.name}")

    if user_question:
        with st.spinner("Berpikir..."):
            try:
                chat_response = model.generate_content([
                    f"Berdasarkan gambar ini dan analisis sebelumnya: {st.session_state['hasil_terakhir']}, jawablah pertanyaan user: {user_question}", 
                    image
                ])
                st.chat_message("assistant").write(chat_response.text)
            except Exception as e:
                st.error(f"Gagal merespon: {e}")

# Footer
st.markdown("---")
st.caption("InsightVision v1.1 - Powered by Gemini AI")
