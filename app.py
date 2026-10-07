import os
import re
import streamlit as st
from pypdf import PdfReader

# 1. Konfigurasi Halaman Website
st.set_page_config(
    page_title="Pencari UU Online",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #ffffff;
    }
    .result-card {
        background-color: #1a1c23;
        border: 1px solid #2e323e;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .file-tag {
        background-color: #2a5298;
        color: #ffffff;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .page-tag {
        background-color: #ff9800;
        color: #ffffff;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 0.5rem;
    }
    .context-box {
        background-color: #0f1117;
        border-left: 4px solid #ff9800;
        padding: 0.8rem;
        border-radius: 4px;
        margin-top: 0.6rem;
        font-size: 0.95rem;
        line-height: 1.5;
        color: #d1d5db;
    }
    /* Style untuk Highlight Kata Kunci */
    .highlight-word {
        background-color: #ffd700;
        color: #000000;
        font-weight: bold;
        padding: 2px 5px;
        border-radius: 4px;
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

# Sidebar
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

# Fungsi Bersihkan Teks
def bersihkan_teks_uu(teks):
    teks_bersih = re.sub(r'(-?\s*\d+\s*-?)*\s*[a-zA-Z0-9_]+\s*(\.|\s){2,}', '', teks)
    teks_bersih = re.sub(r'(\.|\s){3,}', ' ', teks_bersih)
    return teks_bersih.strip()

# Fungsi Highlight Teks Kata Kunci
def berikan_highlight(teks, kata_kunci):
    if not kata_kunci:
        return teks
    pattern = re.compile(re.escape(kata_kunci), re.IGNORECASE)
    return pattern.sub(lambda m: f'<span class="highlight-word">{m.group(0)}</span>', teks)

# Fungsi Pencarian Kontekstual Pintar
def cari_dalam_pdf_kontekstual(file_path, kata_kunci, window=2):
    hasil = []
    try:
        reader = PdfReader(file_path)
        for i, halaman in enumerate(reader.pages):
            teks_halaman = halaman.extract_text()
            if not teks_halaman:
                continue
                
            baris_list = [b.strip() for b in teks_halaman.split('\n') if b.strip()]
            
            for idx, baris in enumerate(baris_list):
                baris_dibersihkan = bersihkan_teks_uu(baris)
                
                if kata_kunci.lower() in baris_dibersihkan.lower():
                    awal = max(0, idx - window)
                    akhir = min(len(baris_list), idx + window + 1)
                    
                    blok_konteks = [bersihkan_teks_uu(b) for b in baris_list[awal:akhir] if bersihkan_teks_uu(b)]
                    
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
    with st.form(key="search_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            kata_kunci = st.text_input("Kata Kunci", placeholder="Masukkan kata kunci atau nomor pasal (contoh: 'sanksi pidana', 'Pasal 5')...", label_visibility="collapsed")
        with col2:
            tombol_cari = st.form_submit_button("🔍 Cari", type="primary", use_container_width=True)

    if tombol_cari:
        if not kata_kunci.strip():
            st.warning("Ketikkan kata kunci atau nomor pasal yang ingin kamu cari dulu ya.")
        else:
            st.markdown("---")
            total_ditemukan = 0
            semua_hasil = []
            
            with st.spinner("Sedang memindai seluruh dokumen undang-undang..."):
                for nama_file in file_pdf_list:
                    path_file = os.path.join(FOLDER_PENYIMPANAN, nama_file)
                    hasil_file = cari_dalam_pdf_kontekstual(path_file, kata_kunci)
                    if hasil_file:
                        total_ditemukan += len(hasil_file)
                        semua_hasil.append({
                            "file": nama_file,
                            "data": hasil_file
                        })
            
            if total_ditemukan > 0:
                st.success(f"Ditemukan **{total_ditemukan} konteks kecocokan** dari **{len(semua_hasil)} dokumen**.")
                
                # Tampilkan hasil dalam Expander/Dropdown per dokumen
                for item in semua_hasil:
                    # Menggunakan st.expander supaya hasil per UU bisa ditutup/dibuka
                    with st.expander(f"📄 **{item['file']}** — (Ditemukan di {len(item['data'])} tempat)", expanded=True):
                        for detail in item['data']:
                            # Berikan highlight warna kuning pada kata kunci
                            konteks_highlight = berikan_highlight(detail['konteks'], kata_kunci)
                            
                            st.markdown(f"""
                                <div class="result-card">
                                    <span class="file-tag">{item['file']}</span>
                                    <span class="page-tag">Halaman {detail['halaman']}</span>
                                    <div class="context-box">
                                        "{konteks_highlight}"
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
            else:
                st.info(f"Tidak ditemukan kata kunci **'{kata_kunci}'** di seluruh dokumen.")
