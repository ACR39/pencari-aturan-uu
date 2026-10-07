import os
import streamlit as st
from pypdf import PdfReader

# 1. Konfigurasi Halaman Website
st.set_page_config(
    page_title="Pencari UU Online",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS untuk Mempercantik Tampilan (Tema Dark & Glassmorphism)
st.markdown("""
    <style>
    /* Styling Header & Judul */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        color: #e0e0e0;
    }
    
    /* Card Hasil Pencarian */
    .result-card {
        background-color: #1a1c23;
        border: 1px solid #2e323e;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .file-tag {
        background-color: #2a5298;
        color: #ffffff;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.8rem;
    }
    .page-tag {
        background-color: #ff9800;
        color: #ffffff;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 0.5rem;
    }
    .context-box {
        background-color: #0f1117;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 4px;
        margin-top: 0.8rem;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #d1d5db;
    }
    </style>
""", unsafe_allow_html=True)

# Header Utama
st.markdown("""
    <div class="main-header">
        <h1>⚖️ Portal Pencari Undang-Undang</h1>
        <p>Akses Cepat & Pencarian Konteks Pasal Terpadu di Seluruh Dokumen Hukum</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar untuk Informasi & Statistik Dokumen
with st.sidebar:
    st.title("📂 Status Repositori")
    st.markdown("---")
    
    FOLDER_PENYIMPANAN = "."
    if os.path.exists(FOLDER_PENYIMPANAN):
        file_pdf_list = [f for f in os.listdir(FOLDER_PENYIMPANAN) if f.lower().endswith('.pdf')]
    else:
        file_pdf_list = []
        
    st.metric(label="Total Dokumen Terdaftar", value=f"{len(file_pdf_list)} PDF")
    
    st.markdown("---")
    st.markdown("### 📜 Daftar File Aktif:")
    if file_pdf_list:
        for f in file_pdf_list:
            st.caption(f"• {f}")
    else:
        st.caption("Belum ada file PDF di repositori.")

# Fungsi Pencarian Kontekstual
def cari_dalam_pdf_kontekstual(file_path, kata_kunci, window=2):
    hasil = []
    try:
        reader = PdfReader(file_path)
        for i, halaman in enumerate(reader.pages):
            teks_halaman = halaman.extract_text()
            if not teks_halaman:
                continue
                
            baris_list = teks_halaman.split('\n')
            
            for idx, baris in enumerate(baris_list):
                if kata_kunci.lower() in baris.lower():
                    awal = max(0, idx - window)
                    akhir = min(len(baris_list), idx + window + 1)
                    blok_konteks = [b.strip() for b in baris_list[awal:akhir] if b.strip()]
                    
                    hasil.append({
                        "halaman": i + 1,
                        "konteks": " ".join(blok_konteks)
                    })
    except Exception as e:
        pass
    return hasil

# Area Utama Pencarian
if not file_pdf_list:
    st.warning("⚠️ Belum ada dokumen PDF undang-undang yang diunggah ke repositori GitHub.")
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        kata_kunci = st.text_input("", placeholder="Masukkan topik, istilah, atau nomor pasal (contoh: 'sanksi pidana', 'Pasal 5')...")
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        tombol_cari = st.button("🔍 Cari", type="primary", use_container_width=True)
        
    if tombol_cari and kata_kunci.strip():
        st.markdown("---")
        
        total_ditemukan = 0
        semua_hasil = []
        
        # Proses pencarian
        with st.spinner("Sedang memindai seluruh dokumen undang-undang..."):
            for nama_file in file_pdf_list:
                path_file = os
