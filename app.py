import os
import re
import streamlit as st
from pypdf import PdfReader
from openai import OpenAI

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

RELINK_API_KEY = ambil_secret("RELINK_API_KEY")

# Sidebar & Indeks File
with st.sidebar:
    st.title("📂 Status Repositori")
    st.markdown("---")
    FOLDER_PENYIMPANAN = "."
    file_pdf_list = [f for f in os.listdir(FOLDER_PENYIMPANAN) if f.lower().endswith('.pdf')] if os.path.exists(FOLDER_PENYIMPANAN) else []
    st.metric(label="Total Dokumen Terdaftar", value=f"{len(file_pdf_list)} PDF")
    
    st.markdown("---")
    st.markdown("### 🤖 Pengaturan AI")
    if not RELINK_API_KEY:
        RELINK_API_KEY = st.text_input("Relink API Key", type="password")
        
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

def ekstraksi_kata_kunci_ai(relink_key, query_pengguna):
    """Menggunakan AI Relink untuk mengambil kata kunci inti dari kalimat pertanyaan panjang."""
    if not relink_key or len(query_pengguna.split()) <= 2:
        return query_pengguna.strip()
        
    try:
        client = OpenAI(
            base_url="https://api.relink-gateway.biz.id/v1",
            api_key=relink_key
        )
        prompt = f'Ekstrak 1 sampai 3 kata kunci paling inti dari kalimat pertanyaan hukum berikut untuk digunakan dalam pencarian teks dokumen hukum. Hanya jawab dengan kata kunci intinya saja tanpa penjelasan tambahan.\n\nPertanyaan: "{query_pengguna}"'
        response = client.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20
        )
        hasil = response.choices[0].message.content.strip()
        return hasil.replace('"', '').replace("'", "")
    except Exception:
        # Fallback manual jika API error
        stop_words = [r"apa itu", r"apa yang dimaksud dengan", r"apakah yang dimaksud dengan", r"bagaimana aturan", r"jelaskan", r"pengertian"]
        q = query_pengguna.strip()
        for w in stop_words:
            q = re.sub(rf"^{w}\s+", "", q, flags=re.IGNORECASE)
        return q

def bersihkan_teks_uu(teks):
    teks_bersih = re.sub(r'(-?\s*\d+\s*-?)*\s*[a-zA-Z0-9_]+\s*(\.|\s){2,}', '', teks)
    teks_bersih = re.sub(r'(\.|\s){3,}', ' ', teks_bersih)
    return teks_bersih.strip()

def berikan_highlight(teks, kata_kunci_list):
    teks_hasil = teks
    for kw in kata_kunci_list:
        if len(kw) > 2: # Hanya highlight kata dengan panjang > 2 huruf
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            teks_hasil = pattern.sub(lambda m: f'<span class="highlight-word">{m.group(0)}</span>', teks_hasil)
    return teks_hasil

def cari_dari_cache_fleksibel(data_dokumen, kata_kunci_string, window=2):
    """Pencarian kontekstual fleksibel (mencari kecocokan kata kunci)."""
    semua_hasil = []
    total_ditemukan = 0
    # Pecah kata kunci menjadi beberapa kata terpisah untuk pencarian parsial
    daftar_kata = [k.strip().lower() for k in re.split(r'\s+|,', kata_kunci_string) if len(k.strip()) > 2]
    
    if not daftar_kata:
        daftar_kata = [kata_kunci_string.lower()]

    for nama_file, daftar_halaman in data_dokumen.items():
        hasil_file = []
        for item in daftar_halaman:
            teks_halaman = item['teks']
            if not teks_halaman: 
                continue
            baris_list = [b.strip() for b in teks_halaman.split('\n') if b.strip()]
            for idx, baris in enumerate(baris_list):
                baris_dibersihkan = bersihkan_teks_uu(baris).lower()
                
                # Hitung berapa banyak kata kunci yang cocok di baris ini
                jumlah_cocok = sum(1 for kw in daftar_kata if kw in baris_dibersihkan)
                
                if jumlah_cocok > 0:
                    awal = max(0, idx - window)
                    akhir = min(len(baris_list), idx + window + 1)
                    blok_konteks = [bersihkan_teks_uu(b) for b in baris_list[awal:akhir] if bersihkan_teks_uu(b)]
                    hasil_file.append({
                        "halaman": item['halaman'], 
                        "konteks": " ".join(blok_konteks),
                        "skor": jumlah_cocok
                    })
        
        if hasil_file:
            # Urutkan konteks berdasarkan skor kecocokan tertinggi
            hasil_file = sorted(hasil_file, key=lambda x: x['skor'], reverse=True)
            total_ditemukan += len(hasil_file)
            semua_hasil.append({
                "file": nama_file, 
                "path": os.path.join(FOLDER_PENYIMPANAN, nama_file), 
                "data": hasil_file
            })
            
    return semua_hasil, total_ditemukan, daftar_kata

def buat_ringkasan_relink(relink_key, pertanyaan_asli, semua_hasil):
    """Ringkasan AI menggunakan Relink Gateway."""
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
Kamu adalah asisten hukum AI. Berdasarkan potongan ayat/pasal Undang-Undang berikut, jawab dan buatlah ringkasan penjelasan yang sangat singkat, jelas, dan mudah dipahami untuk pertanyaan pengguna: "{pertanyaan_asli}".

Potongan Teks Hukum:
{konteks_gabungan}

Aturan Ringkasan:
1. Tulis jawaban dalam 2-3 kalimat saja.
2. Gunakan bahasa Indonesia baku yang mudah dipahami orang awam.
3. Sebutkan nomor pasal atau undang-undangnya jika ada di teks.
"""
    try:
        client = OpenAI(
            base_url="https://api.relink-gateway.biz.id/v1",
            api_key=relink_key
        )
        response = client.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Gagal memanggil Relink Gateway: {str(e)}"

# Memuat dokumen ke cache RAM
data_pdf_cached = muat_semua_dokumen_pdf(FOLDER_PENYIMPANAN)

if not file_pdf_list:
    st.warning("⚠️ Belum ada dokumen PDF undang-undang yang diunggah ke repositori GitHub.")
else:
    with st.form(key="search_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            query_input = st.text_input("Pertanyaan / Kata Kunci", placeholder="Ketik pertanyaan atau kata kunci bebas (contoh: Bagaimana sanksi jika melanggar jam operasional?)...", label_visibility="collapsed")
        with col2:
            tombol_cari = st.form_submit_button("🔍 Cari", type="primary", use_container_width=True)
            
    gunakan_ai = st.checkbox("✨ Aktifkan Ringkasan AI Relink Gateway", value=True, help="Hapus centang untuk pencarian super cepat tanpa ringkasan AI.")

    if tombol_cari:
        if not query_input.strip():
            st.warning("Ketikkan pertanyaan atau kata kunci terlebih dahulu.")
        else:
            st.markdown("---")
            
            # Ekstraksi Kata Kunci dengan AI
            with st.spinner("🔍 Menganalisis kata kunci pertanyaan..."):
                kata_kunci_inti = ekstraksi_kata_kunci_ai(RELINK_API_KEY, query_input)
            
            semua_hasil, total_ditemukan, daftar_kata_list = cari_dari_cache_fleksibel(data_pdf_cached, kata_kunci_inti)
            
            if total_ditemukan > 0:
                st.caption(f"💡 *Pertanyaan:* **'{query_input}'** | *Kata kunci terdeteksi:* **'{kata_kunci_inti}'**")
                
                if gunakan_ai:
                    if RELINK_API_KEY:
                        with st.spinner("🤖 AI Relink Gateway sedang menyusun ringkasan..."):
                            ringkasan_ai = buat_ringkasan_relink(RELINK_API_KEY, query_input, semua_hasil)
                            st.markdown(f"""
                                <div class="ai-box">
                                    <h3>✨ Ringkasan AI Relink untuk: "{query_input}"</h3>
                                    <p>{ringkasan_ai}</p>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("💡 *Tips: Masukkan Relink API Key di sidebar untuk mendapatkan ringkasan kilat dari AI!*")

                st.success(f"⚡ Ditemukan **{total_ditemukan} konteks kecocokan** dari **{len(semua_hasil)} dokumen**.")
                for item in semua_hasil:
                    with st.expander(f"📄 **{item['file']}** — (Ditemukan di {len(item['data'])} tempat)", expanded=True):
                        if os.path.exists(item['path']):
                            with open(item['path'], "rb") as pdf_file:
                                st.download_button(label=f"📥 Unduh Dokumen Lengkap ({item['file']})", data=pdf_file, file_name=item['file'], mime="application/pdf", key=f"main_dl_{item['file']}")
                        st.markdown("<br>", unsafe_allow_html=True)
                        for detail in item['data']:
                            konteks_highlight = berikan_highlight(detail['konteks'], daftar_kata_list)
                            st.markdown(f"""
                                <div class="result-card">
                                    <span class="file-tag">{item['file']}</span>
                                    <span class="page-tag">Halaman {detail['halaman']}</span>
                                    <div class="context-box">"{konteks_highlight}"</div>
                                </div>
                            """, unsafe_allow_html=True)
            else:
                st.info(f"Tidak ditemukan konteks yang cocok untuk pertanyaan **'{query_input}'** di seluruh dokumen.")
