import streamlit as st
import os
import pandas as pd

st.set_page_config(layout="wide")

# Judul aplikasi
st.markdown("<h1 style='text-align: center;'> UPDATE EMITEM LIST 📂 </h1> <br> ", unsafe_allow_html=True)

# Pastikan folder tujuan ada
upload_folder = "./database/"
viewer_excel = "./database/Daftar Saham.xlsx"
os.makedirs(upload_folder, exist_ok=True)

# Komponen upload
uploaded_file = st.file_uploader("Pilih file Excel untuk diunggah", type=["xlsx", "xls"])

# Jika ada file yang diunggah
if uploaded_file is not None:
    # Nama file baru selalu "Daftar Saham.xlsx"
    save_path = os.path.join(upload_folder, "Daftar Saham.xlsx")

    # Simpan file ke folder database
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ File berhasil diunggah dan dan diperbaharui")

    # Tampilkan info file
    st.write("**Nama file yang disimpan:** Daftar Saham.xlsx")
    st.write("**Ukuran:**", f"{uploaded_file.size / 1024:.2f} KB")

    # Membaca dan menampilkan isi Excel
try:
    df = pd.read_excel(viewer_excel)
    st.subheader("📊 Preview Data Emitem List")
    st.dataframe(df)
except Exception as e:
    st.error(f"Gagal membaca file Excel: {e}")
