import streamlit as st
import pandas as pd
import os
from tqdm import tqdm
import yfinance as yf
from bs4 import BeautifulSoup
import requests
import warnings
from tkinter import Tk, filedialog
from tkinter import messagebox
import threading

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
st.set_page_config(layout="wide")

def show_combine_page():
    st.markdown("<h1 style='text-align: center;'>GABUNGKAN FILE LAPORAN KEUANGAN</h1>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'combine_process' not in st.session_state:
        st.session_state.combine_process = {
            'running': False,
            'completed': False,
            'output_file': None,
            'error': None
        }

    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Direktori Sumber File XBRL**")
            if st.button("Pilih Folder Sumber"):
                st.session_state.source_dir = select_directory()
            
            st.text_input("Direktori Sumber:", 
                         value=st.session_state.get('source_dir', ''), 
                         key="source_dir_display", 
                         disabled=True)

            st.markdown("**Direktori Output Hasil**")
            if st.button("Pilih Folder Output"):
                st.session_state.output_dir = select_directory()
            
            st.text_input("Direktori Output:", 
                         value=st.session_state.get('output_dir', ''), 
                         key="output_dir_display", 
                         disabled=True)

            tahun = st.text_input("Tahun Laporan:", value=st.session_state.get('tahun', ''))
            kuartal = st.selectbox("Kuartal:", ["Q1", "Q2", "Q3", "Q4"], 
                                 index=["Q1", "Q2", "Q3", "Q4"].index(st.session_state.get('kuartal', 'Q1')))

        with col2:
            st.markdown("**Panduan Penggunaan**")
            st.write("1. Pilih folder sumber dan output")
            st.write("2. Masukkan tahun dan pilih kuartal")
            st.write("3. Klik tombol proses")
            st.write("4. Tunggu hingga proses selesai")
            st.write("5. Download hasil yang sudah digabungkan")

    if st.button("Proses Gabungkan File", 
                disabled=st.session_state.combine_process['running']):
        if not all([st.session_state.get('source_dir'), 
                   st.session_state.get('output_dir'), 
                   st.session_state.get('tahun')]):
            st.error("Harap lengkapi semua field!")
        else:
            st.session_state.combine_process = {
                'running': True,
                'completed': False,
                'output_file': None,
                'error': None
            }
            
            try:
                # Jalankan proses secara synchronous (tanpa threading)
                output_file = os.path.join(
                    st.session_state.output_dir,
                    f"Data_Laporan_{st.session_state.tahun}_{st.session_state.kuartal}.xlsx"
                )
                
                with st.spinner("Sedang memproses..."):
                    # Simpan status di session state
                    st.session_state.combine_process['status'] = "Mengumpulkan informasi file..."
                    
                    data = file_info_scraper(st.session_state.source_dir)
                    
                    st.session_state.combine_process['status'] = "Memproses laporan keuangan..."
                    xbrl_scraper(data["NamaSheetPK"].unique(), "NamaSheetPK", 
                               st.session_state.source_dir, st.session_state.output_dir)
                    xbrl_scraper(data["NamaSheetLR"].unique(), "NamaSheetLR", 
                               st.session_state.source_dir, st.session_state.output_dir)
                    xbrl_scraper(data["NamaSheetAK"].unique(), "NamaSheetAK", 
                               st.session_state.source_dir, st.session_state.output_dir)
                    
                    st.session_state.combine_process['status'] = "Menggabungkan data..."
                    laporan_pk_all = gabungkan_data(data["NamaSheetPK"].unique(), st.session_state.output_dir)
                    laporan_lr_all = gabungkan_data(data["NamaSheetLR"].unique(), st.session_state.output_dir)
                    laporan_ak_all = gabungkan_data(data["NamaSheetAK"].unique(), st.session_state.output_dir)
                    
                    st.session_state.combine_process['status'] = "Mengambil data saham..."
                    general_info = general_information(st.session_state.source_dir, data)
                    latest_stock = stock_latest_googlefinance(data["kode entitas"].unique())
                    
                    st.session_state.combine_process['status'] = "Menyimpan hasil..."
                    PK_currentQ, PK_previousQ = pemisah_data(laporan_pk_all)
                    LR_currentQ, LR_previousQ = pemisah_data(laporan_lr_all)
                    AK_currentQ, AK_previousQ = pemisah_data(laporan_ak_all)
                    
                    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                        general_info.to_excel(writer, sheet_name="gen_info", index=False)
                        PK_currentQ.to_excel(writer, sheet_name="pk_now", index=False)
                        LR_currentQ.to_excel(writer, sheet_name="lr_now", index=False)
                        AK_currentQ.to_excel(writer, sheet_name="ak_now", index=False)
                        PK_previousQ.to_excel(writer, sheet_name="pk_prev", index=False)
                        LR_previousQ.to_excel(writer, sheet_name="lr_prev", index=False)
                        AK_previousQ.to_excel(writer, sheet_name="ak_prev", index=False)
                        latest_stock.to_excel(writer, sheet_name="stock_info", index=False)
                    
                    st.session_state.combine_process = {
                        'running': False,
                        'completed': True,
                        'output_file': output_file,
                        'error': None
                    }
                    
            except Exception as e:
                st.session_state.combine_process = {
                    'running': False,
                    'completed': False,
                    'output_file': None,
                    'error': str(e)
                }
    
    # Tampilkan status proses
    if st.session_state.combine_process['running']:
        st.info(f"Status: {st.session_state.combine_process.get('status', 'Memproses...')}")
    
    # Tampilkan hasil jika selesai
    if st.session_state.combine_process['completed']:
        output_file = st.session_state.combine_process['output_file']
        if output_file and os.path.exists(output_file):
            st.success("Proses selesai! File berhasil dibuat.")
            
            with open(output_file, "rb") as f:
                st.download_button(
                    label="Download Hasil",
                    data=f,
                    file_name=os.path.basename(output_file),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("File hasil tidak ditemukan.")
    
    # Tampilkan error jika ada
    if st.session_state.combine_process['error']:
        st.error(f"Terjadi kesalahan: {st.session_state.combine_process['error']}")

def select_directory():
    root = Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    folder = filedialog.askdirectory(master=root)
    root.destroy()
    return folder

def run_combine_process(status):
    try:
        status.update(label="Mengumpulkan informasi file...", state="running")
        data = file_info_scraper(st.session_state.source_dir, status)
        
        status.update(label="Mengumpulkan data laporan...", state="running")
        xbrl_scraper(data["NamaSheetPK"].unique(), "NamaSheetPK", st.session_state.source_dir, st.session_state.output_dir, status)
        xbrl_scraper(data["NamaSheetLR"].unique(), "NamaSheetLR", st.session_state.source_dir, st.session_state.output_dir, status)
        xbrl_scraper(data["NamaSheetAK"].unique(), "NamaSheetAK", st.session_state.source_dir, st.session_state.output_dir, status)
        
        status.update(label="Menggabungkan data...", state="running")
        laporan_pk_all = gabungkan_data(data["NamaSheetPK"].unique(), st.session_state.output_dir)
        laporan_lr_all = gabungkan_data(data["NamaSheetLR"].unique(), st.session_state.output_dir)
        laporan_ak_all = gabungkan_data(data["NamaSheetAK"].unique(), st.session_state.output_dir)
        
        status.update(label="Memproses data saham...", state="running")
        general_info = general_information(st.session_state.source_dir, data)
        latest_stock = stock_latest_googlefinance(data["kode entitas"].unique())
        
        status.update(label="Menyiapkan laporan akhir...", state="running")
        PK_currentQ, PK_previousQ = pemisah_data(laporan_pk_all)
        LR_currentQ, LR_previousQ = pemisah_data(laporan_lr_all)
        AK_currentQ, AK_previousQ = pemisah_data(laporan_ak_all)
        
        output_file = os.path.join(st.session_state.output_dir, f"Data_Laporan_{st.session_state.tahun}_{st.session_state.kuartal}.xlsx")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            general_info.to_excel(writer, sheet_name="gen_info", index=False)
            PK_currentQ.to_excel(writer, sheet_name="pk_now", index=False)
            LR_currentQ.to_excel(writer, sheet_name="lr_now", index=False)
            AK_currentQ.to_excel(writer, sheet_name="ak_now", index=False)
            PK_previousQ.to_excel(writer, sheet_name="pk_prev", index=False)
            LR_previousQ.to_excel(writer, sheet_name="lr_prev", index=False)
            AK_previousQ.to_excel(writer, sheet_name="ak_prev", index=False)
            latest_stock.to_excel(writer, sheet_name="stock_info", index=False)
        
        status.update(label="Proses selesai!", state="complete")
    except Exception as e:
        status.update(label=f"Error: {str(e)}", state="error")
        raise e

def file_info_scraper(folder_path, status=None):
    xlsx_files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx")]
    data = {"NamaFile":[], "kode entitas": [], "NamaSheetPK": [], "NamaSheetLR": [], "NamaSheetAK": []}
    
    progress_bar = st.progress(0, text="Mengumpulkan informasi file...") if status else None
    
    for i, namefile in enumerate(tqdm(xlsx_files, desc="Scanning files")):
        file_path = os.path.join(folder_path, namefile)
        try:
            xls = pd.ExcelFile(file_path)
        except Exception as e:
            if status:
                status.write(f"⚠️ File {namefile} error: {str(e)}")
            continue
            
        data["kode entitas"].append(namefile[-9:-5])
        sheet_pk, sheet_lr, sheet_ak = None, None, None
        
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, nrows=10, dtype=str)
            text = " ".join(df.astype(str).fillna("").values.flatten())
            
            if "Statement of financial position" in text:
                sheet_pk = sheet
            if "Statement of profit or loss and other comprehensive income" in text:
                sheet_lr = sheet
            if "Statement of cash flows" in text:
                sheet_ak = sheet
                
        data["NamaSheetPK"].append(sheet_pk)
        data["NamaSheetLR"].append(sheet_lr)
        data["NamaSheetAK"].append(sheet_ak)
        data["NamaFile"].append(namefile)
        
        if progress_bar:
            progress = (i + 1) / len(xlsx_files)
            progress_bar.progress(progress, text=f"Memproses file {i+1}/{len(xlsx_files)}")
    
    return pd.DataFrame(data)

def xbrl_scraper(jenis_laporan, kolom_sheet, folderpath, output_dir):
    data = file_info_scraper(folderpath)
    data_transit_path = os.path.join(output_dir, "temp/")
    os.makedirs(data_transit_path, exist_ok=True)
    
    for sheet_name in tqdm(jenis_laporan, desc=f"Processing {kolom_sheet}"):
        if pd.isna(sheet_name):
            continue
            
        data_filtered = data[data[kolom_sheet] == sheet_name].reset_index(drop=True)
        wadah_transit = pd.DataFrame()
        
        for _, row in data_filtered.iterrows():
            try:
                file_path = os.path.join(folderpath, row['NamaFile'])
                file_target = pd.read_excel(file_path, sheet_name=sheet_name, index_col=None)
                file_target = file_target.dropna(how="all").T
                file_target = file_target.drop(file_target.columns[0], axis=1).reset_index(drop=True).drop(3)
                file_target.loc[0, 2] = "Tanggal"
                file_target.columns = file_target.iloc[0].str.lower()
                file_target = file_target[1:].dropna(axis=1, how="all")
                file_target["kode entitas"] = [row["kode entitas"]] * 2
                wadah_transit = pd.concat([wadah_transit, file_target], ignore_index=True)
            except Exception as e:
                st.warning(f"Error pada {row['kode entitas']}: {str(e)}")
        
        if not wadah_transit.empty:
            wadah_transit.to_excel(f"{data_transit_path}{sheet_name}.xlsx", index=False)

def gabungkan_data(jenis_laporan, data_transit_path):
    data_transit_path = os.path.join(data_transit_path, "temp/")
    gabung_all = pd.concat([
        pd.read_excel(f"{data_transit_path}{sheet}.xlsx") for sheet in jenis_laporan if pd.notna(sheet)
    ], ignore_index=True)
    
    kolom_awal = ["kode entitas"]
    gabung_all = gabung_all[kolom_awal + [col for col in gabung_all.columns if col not in kolom_awal]].fillna(0)
    return gabung_all

def pemisah_data(df):
    current_q = df.iloc[::2].reset_index(drop=True)
    previous_q = df.iloc[1::2].reset_index(drop=True)
    return current_q, previous_q

def general_information(folderpath, data):
    info_entitas = pd.concat([
        pd.read_excel(os.path.join(folderpath, file), sheet_name="1000000").T.dropna(how="all").reset_index(drop=True).drop(2)
        for file in data["NamaFile"]
    ], ignore_index=True)
    
    info_entitas = info_entitas.drop_duplicates().reset_index(drop=True)
    info_entitas.columns = info_entitas.iloc[0].str.lower()
    info_entitas = info_entitas.drop(info_entitas.columns[:2], axis=1).drop(0)
    
    return info_entitas

def stock_latest_googlefinance(kode_entitas_list):
    harga_stock = {"kode entitas": [], "penutupan": []}
    
    for ticker in tqdm(kode_entitas_list, desc="Getting stock prices"):
        try:
            url = f'https://www.google.com/finance/quote/{ticker}:IDX?hl=en'
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            stock_price = soup.find('div', class_='AHmHk').text
            stock_price = "".join(filter(str.isdigit, stock_price))
            stock_price = int(stock_price) // 100
            
            harga_stock["kode entitas"].append(ticker)
            harga_stock["penutupan"].append(stock_price)
        except Exception as e:
            st.warning(f"Gagal mendapatkan harga saham {ticker}: {str(e)}")
            harga_stock["kode entitas"].append(ticker)
            harga_stock["penutupan"].append(None)
    
    return pd.DataFrame(harga_stock)

# Untuk menjalankan halaman ini secara terpisah
if __name__ == "__main__":
    show_combine_page()