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

# Inisialisasi Model (Menggunakan gemini-flash-latest yang sudah terbukti lancar di sistem Anda)
model = genai.GenerativeModel('gemini-flash-latest')

# --- 2. UI STREAMLIT & SIDEBAR RIWAYAT ---
st.set_page_config(page_title="InsightVision GenAI", layout="wide") # Mengubah ke 'wide' untuk tampilan lebih luas

# Sidebar untuk menampilkan riwayat dari database
with st.sidebar:
    st.title("📜 Riwayat Analisis")
    st.write("5 Analisis Terakhir:")
    riwayat = database.ambil_riwayat() # Pastikan fungsi ini sudah ada di database.py
    if riwayat:
        for data in riwayat:
            with st.expander(f"📄 {data['nama_file']}"):
                st.caption(f"Waktu: {data['waktu_simpan']}")
                st.write(data['hasil_analisis'][:150] + "...") # Tampilkan cuplikan teks
    else:
        st.info("Belum ada riwayat analisis.")

# Tampilan Utama
st.title("📸 InsightVision")
st.subheader("GenAI Powered Image Analyzer")
st.write("Unggah gambar untuk mendapatkan deskripsi, ekstraksi teks, dan wawasan cerdas.")

# Layout Kolom untuk Unggah dan Hasil
col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Pilih file gambar (JPG, PNG, JPEG)...", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar yang diunggah", use_container_width=True)

# --- 3. TAHAP PROMPT ENGINEERING ---
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
                    # Memanggil API Gemini
                    response = model.generate_content([prompt_awal, image])
                    st.session_state['hasil_terakhir'] = response.text # Simpan hasil ke session state
                    
                    # Simpan ke Database
                    database.simpan_ke_db(uploaded_file.name, response.text)
                    st.success("Analisis Selesai & Tersimpan!")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

        # Menampilkan Hasil Analisis jika ada di session state
        if 'hasil_terakhir' in st.session_state:
            st.markdown(st.session_state['hasil_terakhir'])

# --- 4. TAHAP INTEGRASI MULTIMODAL (INTERAKSI LANJUTAN) ---
if uploaded_file is not None and 'hasil_terakhir' in st.session_state:
    st.markdown("---")
    st.subheader("💬 Tanya Lebih Lanjut tentang Gambar Ini")
    user_question = st.text_input("Contoh: 'Berapa total harganya?' atau 'Apa merk benda itu?'")

    if user_question:
        with st.spinner("Berpikir..."):
            try:
                # Mengirim konteks gambar + pertanyaan tambahan
                chat_response = model.generate_content([
                    f"Berdasarkan gambar ini dan analisis sebelumnya: {st.session_state['hasil_terakhir']}, jawablah: {user_question}", 
                    image
                ])
                st.chat_message("assistant").write(chat_response.text)
            except Exception as e:
                st.error(f"Gagal merespon: {e}")

# Footer
st.markdown("---")
st.caption("InsightVision v1.0 - Powered by Gemini 1.5 Flash")