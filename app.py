import os
import streamlit as st
from pypdf import PdfReader

# Pengaturan Judul Halaman Website
st.set_page_config(page_title="Mesin Pencari Undang-Undang", page_icon="📚", layout="centered")

st.title("📚 Mesin Pencari Undang-Undang Online")
st.markdown("Cari topik atau kata kunci tertentu di dalam dokumen undang-undang secara instan tanpa harus baca satu per satu.")

# Fungsi untuk membaca dan mencari teks di dalam file PDF
def cari_dalam_pdf(file_path, kata_kunci):
    hasil = []
    try:
        reader = PdfReader(file_path)
        for i, halaman in enumerate(reader.pages):
            teks_halaman = halaman.extract_text()
            if kata_kunci.lower() in teks_halaman.lower():
                # Ambil baris-baris yang mengandung kata kunci
                baris_list = teks_halaman.split('\n')
                cuplikan = [baris.strip() for baris in baris_list if kata_kunci.lower() in baris.lower()]
                hasil.append({
                    "halaman": i + 1,
                    "cuplikan": cuplikan
                })
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
    return hasil

# Direktori tempat file PDF undang-undang disimpan (misalnya di folder yang sama di GitHub)
# Kamu bisa membuat folder khusus bernama 'data_uu' atau langsung di root repository.
FOLDER_PENYIMPANAN = "." 

# Mencari semua file PDF di folder
if os.path.exists(FOLDER_PENYIMPANAN):
    file_pdf_list = [f for f in os.listdir(FOLDER_PENYIMPANAN) if f.lower().endswith('.pdf')]
else:
    file_pdf_list = []

if not file_pdf_list:
    st.warning("⚠️ Belum ada file PDF undang-undang yang ditemukan di repository GitHub. Silakan unggah file PDF melalui menu 'Add file' di GitHub.")
else:
    # Pilihan file PDF dari dropdown
    pilihan_file = st.selectbox("Pilih Dokumen Undang-Undang:", file_pdf_list)
    
    # Kolom untuk mengetik kata kunci pencarian
    kata_kunci = st.text_input("Masukkan topik atau kata kunci yang dicari (contoh: 'sanksi', 'pasal 5', 'pidana'):")
    
    if st.button("Cari Sekarang", type="primary"):
        if not kata_kunci.strip():
            st.warning("Tolong masukkan kata kunci terlebih dahulu ya!")
        else:
            path_file_terpilih = os.path.join(FOLDER_PENYIMPANAN, pilihan_file)
            
            with st.spinner(f"Sedang memindai '{pilihan_file}'..."):
                hasil_pencarian = cari_dalam_pdf(path_file_terpilih, kata_kunci)
            
            st.markdown("---")
            st.subheader(f"Hasil Pencarian untuk: *'{kata_kunci}'*")
            
            if not hasil_pencarian:
                st.info("Maaf, kata kunci tersebut tidak ditemukan di dalam dokumen ini.")
            else:
                st.success(f"Ditemukan di **{len(hasil_pencarian)} halaman**!")
                
                for item in hasil_pencarian:
                    with st.expander(f"📄 Halaman {item['halaman']}", expanded=True):
                        for c in item['cuplikan'][:5]: # Batasi tampilkan maksimal 5 cuplikan per halaman
                            st.write(f"> {c}")
