import streamlit as st
import pandas as pd
import openpyxl
import os
import requests
from tkinter import Tk, filedialog

st.set_page_config(layout="wide")

##################################
##           FUNCTION           ##
##################################

# Mencari Directory
def get_directory():
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    folder = filedialog.askdirectory(master=root)
    return folder

# Membuat directory untuk menyimpan hasil download XBRL 
def generate_directory(directory_download, tahun, kuartal):
    directory_download = directory_download + f"/XBRL_{tahun}_{kuartal}/"
    os.makedirs(directory_download, exist_ok=True)
    return directory_download

# Download function dengan error handling yang lebih baik
def download_xbrl_idx(kode_perusahaan, tahun, kuartal, directory_download):
    
    if kuartal == "Q1":
        kuartal_url = "TW1"
        kuartal_romawi = "I"
    elif kuartal == "Q2":
        kuartal_url = "TW2"
        kuartal_romawi = "II"
    elif kuartal == "Q3":
        kuartal_url = "TW3"
        kuartal_romawi = "III"
    elif kuartal == "Q4":
        kuartal_url = "Audit"
        kuartal_romawi = "Tahunan"

    url = f"https://www.idx.co.id/Portals/0/StaticData/ListedCompanies/Corporate_Actions/New_Info_JSX/Jenis_Informasi/01_Laporan_Keuangan/02_Soft_Copy_Laporan_Keuangan//Laporan%20Keuangan%20Tahun%20{tahun}/{kuartal_url}/{kode_perusahaan}/FinancialStatement-{tahun}-{kuartal_romawi}-{kode_perusahaan}.xlsx"
    output_file = generate_directory(directory_download, tahun, kuartal) + f"FinancialStatement-{tahun}-{kuartal_romawi}-{kode_perusahaan}.xlsx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.idx.co.id/',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'DNT': '1'
    }
    
    try:
        with st.spinner(f'Downloading {kode_perusahaan}...'):
            with requests.Session() as session:
                session.get("https://www.idx.co.id/", headers=headers)
                response = session.get(url, headers=headers, stream=True)
                response.raise_for_status()
                
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
                
                return True, f"✅ {kode_perusahaan} berhasil didownload"

    except Exception as e:
        return False, f"❌ Error downloading {kode_perusahaan}: {str(e)}"


daftar_saham = pd.read_excel("database\Daftar Saham.xlsx")

##################################
##             VIEW             ##
##################################

st.markdown("<h1 style='text-align: center;'> DOWNLOAD LAPORAN KEUANGAN </h1> <br> ", unsafe_allow_html=True)

# Buat empty container untuk error messages
error_container = st.empty()
success_container = st.empty()
progress_container = st.empty()

with st.container(border=True):
    column_kiri1, column_kanan1 = st.columns([1,2])
    
    with column_kiri1:
        with st.container(border=False):
            
            # ini buat ngambil tahun. variabelnya " tahun "
            with st.container(border=True):
                tahun = st.text_input(
                    label="Masukan Tahun :",
                    max_chars=4,
                    help="Masukkan 4 digit tahun (contoh: 2024)"
                )
                if tahun:
                    if not tahun.isdigit() or len(tahun) != 4:
                        error_container.error("Format tahun salah ❌. Harus 4 digit angka.")
                    else:
                        error_container.empty()
            
            # ini buat ngambil kuartal. hasilnya masih bentuk Q. variabelnya " kuartal "
            with st.container(border=True):        
                kuartal = st.radio(label="Pilih Kuartal :",
                                options=["Q1","Q2","Q3","Q4"],
                                horizontal=True)

            # ini ngambil alamat directory, variabelnya  " directory "
            with st.container(border=True):
                if st.button(label="Pilih Folder untuk Simpan", key="Pilih Folder"):
                    directory = get_directory()
                    if directory:
                        st.session_state.selected_dir = directory
                        st.write("Hasil download disimpan di :")
                        st.write(f"--->    {directory}")
                        
            if st.button("Download XBRL"):
                # Clear previous messages
                error_container.empty()
                success_container.empty()
                
                if 'selected_dir' not in st.session_state:
                    error_container.error("Silakan pilih directory terlebih dahulu")
                elif not tahun:
                    error_container.error("Silakan isi tahun")
                elif 'edited_df' not in st.session_state:
                    error_container.error("Silakan pilih perusahaan terlebih dahulu")
                else:
                    # Get selected companies
                    edited_df = st.session_state.edited_df
                    selected_companies = edited_df[edited_df['Pilih']]['Kode'].tolist()
                    
                    if not selected_companies:
                        error_container.error("Silakan pilih minimal satu perusahaan")
                    else:
                        success_count = 0
                        total_companies = len(selected_companies)
                        
                        # Progress bar
                        progress_bar = progress_container.progress(0)
                        status_text = progress_container.empty()
                        
                        results = []
                        for i, kode in enumerate(selected_companies):
                            status_text.text(f"Memproses {kode} ({i+1}/{total_companies})")
                            success, message = download_xbrl_idx(kode, tahun, kuartal, st.session_state.selected_dir)
                            results.append((kode, success, message))
                            
                            if success:
                                success_count += 1
                            
                            # Update progress bar
                            progress_bar.progress((i + 1) / total_companies)
                        
                        # Clear progress elements
                        progress_bar.empty()
                        status_text.empty()
                        progress_container.empty()
                        
                        # Tampilkan hasil summary
                        if success_count == total_companies:
                            success_container.success(f"✅ Download selesai! Semua {success_count} perusahaan berhasil didownload")
                        elif success_count > 0:
                            success_container.warning(f"⚠️ Download selesai! {success_count} dari {total_companies} perusahaan berhasil didownload")
                        else:
                            error_container.error("❌ Download gagal! Tidak ada perusahaan yang berhasil didownload")
                        
                        # Tampilkan detail hasil per perusahaan (opsional)
                        with st.expander("Lihat Detail Hasil Download"):
                            for kode, success, message in results:
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)

    with column_kanan1:
        with st.container(border=True):
            # Tombol Pilih Semua dan Batal Semua
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Pilih Semua", key="select_all", use_container_width=True):
                    kode_perusahaan = daftar_saham[["Kode","Nama Perusahaan"]].copy()
                    kode_perusahaan.insert(0, 'Pilih', True)
                    st.session_state.edited_df = kode_perusahaan
                    st.rerun()
            
            with col2:
                if st.button("❌ Batal Semua", key="deselect_all", use_container_width=True):
                    kode_perusahaan = daftar_saham[["Kode","Nama Perusahaan"]].copy()
                    kode_perusahaan.insert(0, 'Pilih', False)
                    st.session_state.edited_df = kode_perusahaan
                    st.rerun()
            
            # Inisialisasi dataframe jika belum ada di session state
            if 'edited_df' not in st.session_state:
                kode_perusahaan = daftar_saham[["Kode","Nama Perusahaan"]].copy()
                kode_perusahaan.insert(0, 'Pilih', False)
                st.session_state.edited_df = kode_perusahaan
            
            # Tampilkan data editor
            edited_df = st.data_editor(
                st.session_state.edited_df,
                column_config={
                    "Pilih": st.column_config.CheckboxColumn("Pilih"),
                    "Kode": st.column_config.TextColumn("Kode", disabled=True),
                    "Nama Perusahaan": st.column_config.TextColumn("Nama Perusahaan", disabled=True)
                },
                hide_index=True,
                use_container_width=True,
                key="company_table"
            )
            
            # Update session state dengan perubahan dari user
            st.session_state.edited_df = edited_df
            
            # Tampilkan jumlah yang dipilih
            selected_count = edited_df['Pilih'].sum()
            total_count = len(edited_df)
            st.caption(f"📊 {selected_count} dari {total_count} perusahaan dipilih")