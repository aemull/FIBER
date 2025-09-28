import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

def get_stock_data(stock_code):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5*365)
        
        stock = yf.Ticker(stock_code)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            print(f"Tidak ditemukan data untuk {stock_code}")
            return None
        
        # Mengambil hanya kolom Close
        close_prices = hist['Close']
        
        # Handle missing values - drop NaN values
        close_prices = close_prices.dropna()
        
        if close_prices.empty:
            print(f"Data untuk {stock_code} hanya berisi NaN values")
            return None
        
        # Konversi harga ke integer (setelah handle NaN)
        close_prices = close_prices.astype(int)
        
        # Format index menjadi hanya tanggal (tanpa waktu)
        close_prices.index = close_prices.index.date
        
        # Hapus .JK dari nama series, hanya ambil kode perusahaan saja
        company_code = stock_code.replace('.JK', '')
        close_prices.name = company_code
        
        return close_prices
    
    except Exception as e:
        print(f"Error mendapatkan data {stock_code}: {e}")
        return None

def get_multiple_stocks(stock_list):
    all_data = {}
    
    for stock_code in stock_list:
        print(f"Mengambil data {stock_code}...")
        full_stock_code = stock_code + ".JK"
        data = get_stock_data(full_stock_code)
        
        if data is not None:
            all_data[stock_code] = data
        else:
            print(f"Data {stock_code} tidak valid atau kosong")
    
    if all_data:
        # Gabungkan semua data menjadi DataFrame
        df = pd.concat(all_data.values(), axis=1, keys=all_data.keys())
        df.index.name = 'Date'
        
        # Handle missing values dalam DataFrame gabungan
        df = df.dropna()  # Hapus baris yang memiliki NaN di salah satu kolom
        
        # Konversi ke integer hanya jika tidak ada NaN
        df = df.astype(int)
        
        return df
    else:
        print("Tidak ada data yang berhasil diambil")
        return None

def get_status_dataframe(stock_df):
    """
    Membuat dataframe dengan status harga saham terendah
    """
    status_data = []
    
    for column in stock_df.columns:
        try:
            current_price = stock_df[column].iloc[-1]  # Harga terakhir
            all_time_data = stock_df[column]  # Data 5 tahun
            
            # Hitung tanggal untuk periode waktu tertentu
            end_date = datetime.now().date()
            one_year_ago = (datetime.now() - timedelta(days=365)).date()
            three_years_ago = (datetime.now() - timedelta(days=3*365)).date()
            five_years_ago = (datetime.now() - timedelta(days=5*365)).date()
            
            # Filter data berdasarkan periode
            five_year_data = all_time_data[all_time_data.index >= five_years_ago]
            three_year_data = all_time_data[all_time_data.index >= three_years_ago]
            one_year_data = all_time_data[all_time_data.index >= one_year_ago]
            
            # Pastikan data tidak kosong setelah filtering
            if five_year_data.empty or three_year_data.empty or one_year_data.empty:
                continue
            
            # Cek status
            status = None
            
            # 1. Cek apakah harga terendah 5 tahun
            if current_price == five_year_data.min():
                status = "terendah 5 tahun terakhir"
            
            # 2. Cek apakah harga terendah 3 tahun (jika bukan terendah 5 tahun)
            elif status is None and current_price == three_year_data.min():
                status = "terendah 3 tahun terakhir"
            
            # 3. Cek apakah harga terendah 1 tahun (jika bukan terendah 5 atau 3 tahun)
            elif status is None and current_price == one_year_data.min():
                status = "terendah 1 tahun terakhir"
            
            # Hanya tambahkan jika memiliki status
            if status is not None:
                status_data.append({
                    'Kode Perusahaan': column,
                    'Harga Terkini': current_price,
                    'Status': status,
                    'Harga Terendah 1 Tahun': one_year_data.min(),
                    'Harga Terendah 3 Tahun': three_year_data.min(),
                    'Harga Terendah 5 Tahun': five_year_data.min()
                })
                
        except Exception as e:
            print(f"Error memproses {column}: {e}")
            continue
    
    # Buat dataframe dari data status
    if status_data:
        status_df = pd.DataFrame(status_data)
        status_df = status_df.set_index('Kode Perusahaan')
        return status_df
    else:
        print("Tidak ada saham yang memenuhi kriteria status")
        return None

# List kode saham yang ingin diambil
daftar_emitem = pd.read_excel("database/Daftar Saham.xlsx")
stock_list = daftar_emitem["Kode"]

# Ambil data multiple saham
saham_df = get_multiple_stocks(stock_list)

if saham_df is not None:
    print(f"\nData Harga Saham (Shape: {saham_df.shape}):")
    print(saham_df.tail())
    print(f"\nJumlah saham yang berhasil diambil: {len(saham_df.columns)}")
    
    # Buat dataframe status
    status_df = get_status_dataframe(saham_df)
    
    if status_df is not None:
        print("\nDataFrame Status:")
        print(status_df)
    else:
        print("\nTidak ada saham yang memenuhi kriteria status")
        
    # Tampilkan informasi tambahan
    print(f"\nTanggal data terakhir: {saham_df.index[-1]}")
    print(f"Tanggal 1 tahun lalu: {(datetime.now() - timedelta(days=365)).date()}")
    print(f"Tanggal 3 tahun lalu: {(datetime.now() - timedelta(days=3*365)).date()}")
    print(f"Tanggal 5 tahun lalu: {(datetime.now() - timedelta(days=5*365)).date()}")
else:
    print("Tidak ada data saham yang berhasil diambil")