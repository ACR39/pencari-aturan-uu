import os
import streamlit as st
from pypdf import PdfReader

# Pengaturan Judul Halaman Website
st.set_page_config(page_title="Pencari Undang-Undang Global", page_icon="📚", layout="centered")

st.title("📚 Mesin Pencari Semua Undang-Undang")
st.markdown("Ketik topik atau kata kunci apa saja, sistem akan otomatis mencari di seluruh dokumen PDF yang tersimpan!")

# Fungsi untuk membaca dan mencari teks di dalam file PDF
def cari_dalam_pdf(file_path, kata_kunci):
    hasil = []
    try:
        reader = PdfReader(file_path)
        for i, halaman in enumerate(reader.pages):
            teks_halaman = halaman.extract_text()
            if kata_kunci.lower() in teks_halaman.lower():
                baris_list = teks_halaman.split('\n')
                cuplikan = [baris.strip() for baris in baris_list if kata_kunci.lower() in baris.lower()]
                hasil.append({
                    "halaman": i + 1,
                    "cuplikan": cuplikan
                })
    except Exception as e:
        pass # Lewati jika ada error pada file tertentu
    return hasil

# Direktori penyimpanan file PDF di GitHub
FOLDER_PENYIMPANAN = "." 

# Ambil semua file PDF yang ada secara otomatis
if os.path.exists(FOLDER_PENYIMPANAN):
    file_pdf_list = [f for f in os.listdir(FOLDER_PENYIMPANAN) if f.lower().endswith('.pdf')]
else:
    file_pdf_list = []

if not file_pdf_list:
    st.warning("⚠️ Belum ada file PDF undang-undang di repository GitHub. Silakan unggah file PDF terlebih dahulu.")
else:
    # Langsung sediakan kolom pencarian tanpa perlu memilih dropdown dokumen
    kata_kunci = st.text_input("Masukkan topik atau kata kunci yang dicari (contoh: 'sanksi', 'pasal 5', 'pidana'):")
    
    if st.button("Cari di Semua Undang-Undang", type="primary"):
        if not kata_kunci.strip():
            st.warning("Tolong masukkan kata kunci terlebih dahulu ya!")
        else:
            st.markdown("---")
            st.subheader(iklan := f"Hasil Pencarian untuk: *'{kata_kunci}'*")
            
            total_ditemukan_global = 0
            
            # Melakukan perulangan (looping) ke semua file PDF secara otomatis!
            for nama_file in file_pdf_list:
                path_file = os.path.join(FOLDER_PENYIMPANAN, nama_file)
                
                with st.spinner(f"Memindai dokumen: {nama_file}..."):
                    hasil_pencarian = cari_dalam_pdf(path_file, kata_kunci)
                
                if hasil_pencarian:
                    total_ditemukan_global += len(hasil_pencarian)
                    with st.expander(f"📁 Dokumen: {nama_file} (Ditemukan di {len(hasil_pencarian)} halaman)", expanded=True):
                        for item in hasil_pencarian:
                            st.markdown(f"**Halaman {item['halaman']}**")
                            for c in item['cuplikan'][:3]: # Batasi cuplikan per halaman
                                st.write(f"> {c}")
                            st.markdown("---")
            
            if total_ditemukan_global == 0:
                st.info("Maaf, kata kunci tersebut tidak ditemukan di seluruh dokumen undang-undang yang ada.")
            else:
                st.success(f"Pencarian selesai! Ditemukan total di {total_ditemukan_global} tempat dari berbagai dokumen.")
