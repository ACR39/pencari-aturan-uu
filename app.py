import os
import re
import streamlit as st
from pypdf import PdfReader
from huggingface_hub import InferenceClient

st.set_page_config(
    page_title="Pencari UU Online",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS & Styling
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
    .main-header h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem; color: #ffffff; }
    .result-card { background-color: #1a1c23; border: 1px solid #2e323e; border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem; }
    .file-tag { background-color: #2a5298; color: #ffffff; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.8rem; font-weight: 600; }
    .page-tag { background-color: #ff9800; color: #ffffff; padding: 0.2rem 0.5rem; border-radius: 5px; font-size: 0.8rem; font-weight: bold; margin-left: 0.5rem; }
    .context-box { background-color: #0f1117; border-left: 4px solid #ff9800; padding: 0.8rem; border-radius: 4px; margin-top: 0.6rem; font-size: 0.95rem; line-height: 1.5; color: #d1d5db; }
    .highlight-word { background-color: #ffd700; color: #000000; font-weight: bold; padding: 2px 5px; border-radius: 4px; }
    .ai-box { background-color: #1e1b4b; border: 1px solid #6366f1; border-radius: 10px; padding: 1.2rem; margin-bottom: 1.5rem; color: #e0e7ff; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>⚖️ Portal Pencari Undang-Undang</h1>
        <p>Akses Cepat & Pencarian Konteks Pasal Terpadu di Seluruh Dokumen Hukum</p>
    </div>
""", unsafe_allow_html=True)

# Function Pembaca Secrets Aman
def ambil_secret(nama_key):
    try:
        return st.secrets.get(nama_key, "") or os.environ.get(nama_key, "")
    except Exception:
        return os.environ.get(nama_key, "")

HF_API_KEY = ambil_secret("HUGGINGFACE_API_KEY")

# Sidebar & Indeks File
with st.sidebar:
    st.title("📂 Status Repositori")
    st.markdown("---")
    FOLDER_PENYIMPANAN = "."
    file_pdf_list = [f for f in os.listdir(FOLDER_PENYIMPANAN) if f.lower().endswith('.pdf')] if os.path.exists(FOLDER_PENYIMPANAN) else []
    st.metric(label="Total Dokumen Terdaftar", value=f"{len(file_pdf_list)} PDF")
    
    st.markdown("---")
    st.markdown("### 🤖 Pengaturan AI")
    if not HF_API_KEY:
        HF_API_KEY = st.text_input("Hugging Face API Token", type="password")
        
    st.markdown("---")
    st.markdown("### 📜 Daftar File Aktif & Unduh:")
    if file_pdf_list:
        for f in file_pdf_list:
            path_f = os.path.join(FOLDER_PENYIMPANAN, f)
            with open(path_f, "rb") as file_data:
                st.download_button(label=f"📥 {f}", data=file_data, file_name=f, mime="application/pdf", key=f"sidebar_{f}")
    else:
        st.caption("Belum ada file PDF di repositori.")

@st.cache_data(show_spinner="⚡ Menyiapkan & memuat memori dokumen PDF...")
def muat_semua_dokumen_pdf(folder_path):
    data_dokumen = {}
    if os.path.exists(folder_path):
        for nama_file in os.listdir(folder_path):
            if nama_file.lower().endswith('.pdf'):
                path_file = os.path.join(folder_path, nama_file)
                try:
                    reader = PdfReader(path_file)
                    halaman_list = []
                    for i, page in enumerate(reader.pages):
                        teks = page.extract_text() or ""
                        halaman_list.append({"halaman": i + 1, "teks": teks})
                    data_dokumen[nama_file] = halaman_list
                except Exception:
                    pass
    return data_dokumen

def ekstrak_kata_kunci_fleksibel(query):
    stop_words = [
        r"apa itu", r"apa yang dimaksud dengan", r"apakah yang dimaksud dengan",
        r"apa yang dimaksud", r"jelaskan tentang", r"jelaskan", r"sebutkan", 
        r"penjelasan tentang", r"pengertian dari", r"pengertian", r"definisi"
    ]
    query_bersih = query.strip()
    for word in stop_words:
        query_bersih = re.sub(rf"^{word}\s+", "", query_bersih, flags=re.IGNORECASE)
    query_bersih = re.sub(r"\?+$", "", query_bersih).strip()
    return query_bersih

def bersihkan_teks_uu(teks):
    teks_bersih = re.sub(r'(-?\s*\d+\s*-?)*\s*[a-zA-Z0-9_]+\s*(\.|\s){2,}', '', teks)
    teks_bersih = re.sub(r'(\.|\s){3,}', ' ', teks_bersih)
    return teks_bersih.strip()

def berikan_highlight(teks, kata_kunci):
    if not kata_kunci: 
        return teks
    pattern = re.compile(re.escape(kata_kunci), re.IGNORECASE)
    return pattern.sub(lambda m: f'<span class="highlight-word">{m.group(0)}</span>', teks)

def cari_dari_cache_kontekstual(data_dokumen, kata_kunci, window=2):
    semua_hasil = []
    total_ditemukan = 0
    
    for nama_file, daftar_halaman in data_dokumen.items():
        hasil_file = []
        for item in daftar_halaman:
            teks_halaman = item['teks']
            if not teks_halaman: 
                continue
            baris_list = [b.strip() for b in teks_halaman.split('\n') if b.strip()]
            for idx, baris in enumerate(baris_list):
                baris_dibersihkan = bersihkan_teks_uu(baris)
                if kata_kunci.lower() in baris_dibersihkan.lower():
                    awal = max(0, idx - window)
                    akhir = min(len(baris_list), idx + window + 1)
                    blok_konteks = [bersihkan_teks_uu(b) for b in baris_list[awal:akhir] if bersihkan_teks_uu(b)]
                    hasil_file.append({
                        "halaman": item['halaman'], 
                        "konteks": " ".join(blok_konteks)
                    })
        
        if hasil_file:
            total_ditemukan += len(hasil_file)
            semua_hasil.append({
                "file": nama_file, 
                "path": os.path.join(FOLDER_PENYIMPANAN, nama_file), 
                "data": hasil_file
            })
            
    return semua_hasil, total_ditemukan

def buat_ringkasan_hf(hf_key, kata_kunci, semua_hasil):
    """Ringkasan AI 100% Gratis menggunakan Hugging Face Inference Client."""
    konteks_gabungan = ""
    count = 0
    for item in semua_hasil:
        for detail in item['data']:
            konteks_gabungan += f"- Dokumen {item['file']} (Hal. {detail['halaman']}): {detail['konteks']}\n"
            count += 1
            if count >= 6: 
                break
        if count >= 6: 
            break

    prompt = f"""
Kamu adalah asisten hukum AI. Berdasarkan potongan ayat/pasal Undang-Undang berikut, buatlah ringkasan penjelasan yang sangat singkat, jelas, dan mudah dipahami mengenai istilah/kata kunci: "{kata_kunci}".

Potongan Teks Hukum:
{konteks_gabungan}

Aturan Ringkasan:
1. Tulis dalam 2-3 kalimat saja.
2. Gunakan bahasa Indonesia baku yang mudah dipahami orang awam.
3. Sebutkan nomor pasal atau undang-undangnya jika ada di teks.
"""
    daftar_model_hf = [
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-Coder-7B-Instruct",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    ]
    
    client = InferenceClient(api_key=hf_key)
    catatan_err = []

    for model_name in daftar_model_hf:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            catatan_err.append(f"{model_name}: {str(e)}")

    return f"⚠️ Gagal memanggil Hugging Face API: {'; '.join(catatan_err)}"

# Memuat dokumen ke cache RAM
data_pdf_cached = muat_semua_dokumen_pdf(FOLDER_PENYIMPANAN)

if not file_pdf_list:
    st.warning("⚠️ Belum ada dokumen PDF undang-undang yang diunggah ke repositori GitHub.")
else:
    with st.form(key="search_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            query_input = st.text_input("Kata Kunci", placeholder="Ketik kalimat atau istilah (contoh: Apa itu Hak Cipta?)...", label_visibility="collapsed")
        with col2:
            tombol_cari = st.form_submit_button("🔍 Cari", type="primary", use_container_width=True)
            
    gunakan_ai = st.checkbox("✨ Aktifkan Ringkasan AI Hugging Face", value=True, help="Hapus centang untuk pencarian super cepat tanpa ringkasan AI.")

    if tombol_cari:
        if not query_input.strip():
            st.warning("Ketikkan kata kunci terlebih dahulu.")
        else:
            kata_kunci = ekstrak_kata_kunci_fleksibel(query_input)
            st.markdown("---")
            
            semua_hasil, total_ditemukan = cari_dari_cache_kontekstual(data_pdf_cached, kata_kunci)
            
            if total_ditemukan > 0:
                if kata_kunci.lower() != query_input.lower():
                    st.caption(f"💡 *Menampilkan hasil pencarian untuk istilah inti:* **'{kata_kunci}'**")
                
                if gunakan_ai:
                    if HF_API_KEY:
                        with st.spinner("🤖 AI Hugging Face sedang menyusun ringkasan..."):
                            ringkasan_ai = buat_ringkasan_hf(HF_API_KEY, kata_kunci, semua_hasil)
                            st.markdown(f"""
                                <div class="ai-box">
                                    <h3>✨ Ringkasan AI Hugging Face untuk "{kata_kunci}"</h3>
                                    <p>{ringkasan_ai}</p>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("💡 *Tips: Masukkan Hugging Face API Token di sidebar untuk mendapatkan ringkasan kilat dari AI!*")

                st.success(f"⚡ Ditemukan **{total_ditemukan} konteks kecocokan** dari **{len(semua_hasil)} dokumen**.")
                for item in semua_hasil:
                    with st.expander(f"📄 **{item['file']}** — (Ditemukan di {len(item['data'])} tempat)", expanded=True):
                        if os.path.exists(item['path']):
                            with open(item['path'], "rb") as pdf_file:
                                st.download_button(label=f"📥 Unduh Dokumen Lengkap ({item['file']})", data=pdf_file, file_name=item['file'], mime="application/pdf", key=f"main_dl_{item['file']}")
                        st.markdown("<br>", unsafe_allow_html=True)
                        for detail in item['data']:
                            konteks_highlight = berikan_highlight(detail['konteks'], kata_kunci)
                            st.markdown(f"""
                                <div class="result-card">
                                    <span class="file-tag">{item['file']}</span>
                                    <span class="page-tag">Halaman {detail['halaman']}</span>
                                    <div class="context-box">"{konteks_highlight}"</div>
                                </div>
                            """, unsafe_allow_html=True)
            else:
                st.info(f"Tidak ditemukan kata kunci **'{kata_kunci}'** di seluruh dokumen.")
