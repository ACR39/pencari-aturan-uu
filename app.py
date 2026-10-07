import os
import streamlit as st
from pypdf import PdfReader

# Pengaturan Judul Halaman Website
st.set_page_config(page_title="Pencari Undang-Undang Konteks Pasal", page_icon="📚", layout="centered")

st.title("📚 Mesin Pencari Undang-Undang Berbasis Konteks")
st.markdown("Mencari kata kunci sekaligus menampilkan konteks kalimat atau pasal di sekitarnya secara utuh.")

# Fungsi untuk membaca dan mencari teks beserta konteks di dalam file PDF
def cari_dalam_pdf_kontekstual(file_path, kata_kunci, window=2):
    hasil = []
    try:
        reader = PdfReader(file_path)
        for i, halaman in enumerate(reader.pages):
            teks_halaman = halaman.extract_text()
            if not teks_halaman:
                continue
                
            # Pecah teks halaman menjadi baris-baris
            baris_list = teks_halaman.split('\n')
            
            for idx, baris in enumerate(baris_list):
                if kata_kunci.lower() in baris.lower():
                    # Ambil beberapa baris sebelum dan sesudah kata kunci (konteks)
                    awal = max(0, idx - window)
                    akhir = min(len(baris_list), idx + window + 1)
                    
                    # Gabungkan baris-baris tersebut menjadi satu blok konteks
                    blok_konteks = [b.strip() for b in baris_list[awal:akhir] if b.strip()]
                    
                    hasil.append({
                        "halaman": i + 1,
                        "konteks": blok_konteks
                    })
    except Exception as e:
        pass
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
    kata_kunci = st.text_input("Masukkan topik atau kata kunci yang dicari (contoh: 'Pasal 5', 'pidana', 'hak'):")
    
    if st.button("Cari dengan Konteks", type="primary"):
        if not kata_kunci.strip():
            st.warning("Tolong masukkan kata kunci terlebih dahulu ya!")
        else:
            st.markdown("---")
            st.subheader(f"Hasil Pencarian untuk: *'{kata_kunci}'*")
            
            total_ditemukan = 0
            
            for nama_file in file_pdf_list:
                path_file = os.path.join(FOLDER_PENYIMPANAN, nama_file)
                
                with st.spinner(f"Memindai dokumen: {nama_file}..."):
                    hasil_pencarian = cari_dalam_pdf_kontekstual(path_file, kata_kunci)
                
                if hasil_pencarian:
                    total_ditemukan += len(hasil_pencarian)
                    with st.expander(f"📁 Dokumen: {nama_file} (Ditemukan {len(hasil_pencarian)} titik)", expanded=True):
                        for item in hasil_pencarian:
                            st.markdown(f"**Halaman {item['halaman']}**")
                            # Tampilkan blok konteks kalimat di sekitar kata kunci
                            teks_gabungan = " ".join(item['konteks'])
                            st.info(f"{teks_gabungan}")
                            st.markdown("---")
            
            if total_ditemukan == 0:
                st.info("Maaf, kata kunci tersebut tidak ditemukan di seluruh dokumen undang-undang.")
            else:
                st.success(f"Pencarian selesai! Ditemukan total {total_ditemukan} titik kecocokan konteks.")
