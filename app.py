import os
import re
import streamlit as st
from pypdf import PdfReader
from google import genai

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

# Inisialisasi API Key Gemini (Bisa diset di Streamlit Secrets atau Environment Variable)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

# Sidebar & Indeks File
with st.sidebar:
    st.title("📂 Status Repositori")
    st.markdown("---")
    FOLDER_PENYIMPANAN = "."
    file_pdf_list = [f for f in os.listdir(FOLDER_PENYIMPANAN) if f.lower().endswith('.pdf')] if os.path.exists(FOLDER_PENYIMPANAN) else []
    st.metric(label="Total Dokumen Terdaftar", value=f"{len(file_pdf_list)} PDF")
    
    # Input API Key jika belum diset di server/secrets
    if not GEMINI_API_KEY:
        st.markdown("---")
        st.markdown("### 🤖 Pengaturan AI")
        GEMINI_API_KEY = st.text_input("Gemini API Key", type="password", help="Masukkan API Key dari Google AI Studio untuk mengaktifkan ringkasan AI.")
        
    st.markdown("---")
    st.markdown("### 📜 Daftar File Aktif & Unduh:")
    if file_pdf_list:
        for f in file_pdf_list:
            path_f = os.path.join(FOLDER_PENYIMPANAN, f)
            with open(path_f, "rb") as file_data:
                st.download_button(label=f"📥 {f}", data=file_data, file_name=f, mime="application/pdf", key=f"sidebar_{f}")
    else:
        st.caption("Belum ada file PDF di repositori.")

def ekstrak_kata_kunci_fleksibel(query):
    """Menghapus kata-kata pertanyaan umum agar pencarian fokus pada inti kata/istilah."""
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
    if not kata_kunci: return teks
    pattern = re.compile(re.escape(kata_kunci), re.IGNORECASE)
    return pattern.sub(lambda m: f'<span class="highlight-word">{m.group(0)}</span>', teks)

def cari_dalam_pdf_kontekstual(file_path, kata_kunci, window=2):
    hasil = []
    try:
        reader = PdfReader(file_path)
        for i, halaman in enumerate(reader.pages):
            teks_halaman = halaman.extract_text()
            if not teks_halaman: continue
            baris_list = [b.strip() for b in teks_halaman.split('\n') if b.strip()]
            for idx, baris in enumerate(baris_list):
                baris_dibersihkan = bersihkan_teks_uu(baris)
                if kata_kunci.lower() in baris_dibersihkan.lower():
                    awal = max(0, idx - window)
                    akhir = min(len(baris_list), idx + window + 1)
                    blok_konteks = [bersihkan_teks_uu(b) for b in baris_list[awal:akhir] if bersihkan_teks_uu(b)]
                    hasil.append({"halaman": i + 1, "konteks": " ".join(blok_konteks)})
    except Exception:
        pass
    return hasil

# --- FUNGSI RINGKASAN GEMINI AI ---
def buat_ringkasan_gemini(api_key, kata_kunci, semua_hasil):
    """Mengirimkan potongan teks dari hasil pencarian ke Gemini untuk dirangkum."""
    try:
        client = genai.Client(api_key=api_key)
        
        # Mengumpulkan konteks terbaik (maksimal 8 konteks agar prompt tidak terlalu panjang)
        konteks_gabungan = ""
        count = 0
        for item in semua_hasil:
            for detail in item['data']:
                konteks_gabungan += f"- Dokumen {item['file']} (Hal. {detail['halaman']}): {detail['konteks']}\n"
                count += 1
                if count >= 8: break
            if count >= 8: break

        prompt = f"""
Kamu adalah asisten hukum AI. Berdasarkan potongan ayat/pasal Undang-Undang berikut, buatlah ringkasan penjelasan yang sangat singkat, jelas, dan mudah dipahami mengenai istilah/kata kunci: "{kata_kunci}".

Potongan Teks Hukum:
{konteks_gabungan}

Aturan Ringkasan:
1. Tulis dalam 2-3 kalimat saja.
2. Gunakan bahasa Indonesia baku yang mudah dipahami orang awam.
3. Sebutkan nomor pasal atau undang-undangnya jika ada di teks.
"""
        # Menggunakan model gemini-2.0-flash yang aktif
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
