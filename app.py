def buat_ringkasan_hf(hf_key, kata_kunci, semua_hasil):
    """Ringkasan AI 100% Percuma menggunakan Hugging Face Inference Client."""
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
    # Senarai model percuma Hugging Face Serverless yang aktif
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
