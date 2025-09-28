import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import time

# Set page configuration
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2ca02c;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .upload-section {
        background-color: #e9ecef;
        padding: 2rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def get_stock_data(stock_code):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5*365)
        
        stock = yf.Ticker(stock_code)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            st.warning(f"Tidak ditemukan data untuk {stock_code}")
            return None
        
        # Mengambil hanya kolom Close
        close_prices = hist['Close']
        
        # Handle missing values - drop NaN values
        close_prices = close_prices.dropna()
        
        if close_prices.empty:
            st.warning(f"Data untuk {stock_code} hanya berisi NaN values")
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
        st.error(f"Error mendapatkan data {stock_code}: {e}")
        return None

def get_multiple_stocks(stock_list):
    all_data = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stock_code in enumerate(stock_list):
        status_text.text(f"Mengambil data {stock_code}... ({i+1}/{len(stock_list)})")
        full_stock_code = stock_code + ".JK"
        data = get_stock_data(full_stock_code)
        
        if data is not None:
            all_data[stock_code] = data
        else:
            st.warning(f"Data {stock_code} tidak valid atau kosong")
        
        progress_bar.progress((i + 1) / len(stock_list))
        time.sleep(0.1)  # Small delay to show progress
    
    progress_bar.empty()
    status_text.empty()
    
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
        st.error("Tidak ada data yang berhasil diambil")
        return None

def get_data_period_info(stock_series):
    """
    Mendapatkan informasi periode data yang tersedia untuk suatu saham
    """
    if stock_series.empty:
        return "Tidak ada data", 0
    
    start_date = stock_series.index.min()
    end_date = stock_series.index.max()
    days_available = len(stock_series)
    
    # Hitung durasi dalam tahun
    duration_days = (end_date - start_date).days
    duration_years = duration_days / 365.25
    
    if duration_years >= 4.5:
        return "5 tahun", 5
    elif duration_years >= 2.5:
        return "3 tahun", 3
    elif duration_years >= 0.5:
        return "1 tahun", 1
    else:
        return f"{int(duration_days/30)} bulan", 0

def get_status_dataframe(stock_df):
    """
    Membuat dataframe dengan status harga saham terendah
    dengan menyesuaikan periode berdasarkan ketersediaan data
    """
    status_data = []
    
    for column in stock_df.columns:
        try:
            current_price = stock_df[column].iloc[-1]  # Harga terakhir
            all_time_data = stock_df[column]  # Semua data yang tersedia
            
            # Dapatkan info periode data
            period_info, available_years = get_data_period_info(all_time_data)
            
            # Hitung tanggal untuk periode berdasarkan data yang tersedia
            end_date = datetime.now().date()
            
            # Sesuaikan periode dengan data yang tersedia
            if available_years >= 5:
                # Data 5 tahun tersedia
                five_years_ago = (datetime.now() - timedelta(days=5*365)).date()
                period_data = all_time_data[all_time_data.index >= five_years_ago]
                status_type = "5 tahun terakhir"
                
            elif available_years >= 3:
                # Data 3 tahun tersedia
                three_years_ago = (datetime.now() - timedelta(days=3*365)).date()
                period_data = all_time_data[all_time_data.index >= three_years_ago]
                status_type = "3 tahun terakhir"
                
            elif available_years >= 1:
                # Data 1 tahun tersedia
                one_year_ago = (datetime.now() - timedelta(days=365)).date()
                period_data = all_time_data[all_time_data.index >= one_year_ago]
                status_type = "1 tahun terakhir"
                
            else:
                # Data kurang dari 1 tahun, gunakan semua data yang ada
                period_data = all_time_data
                status_type = f"seluruh periode ({period_info})"
            
            # Pastikan data tidak kosong
            if period_data.empty:
                continue
            
            # Cek apakah harga terkini adalah terendah dalam periode
            if current_price == period_data.min():
                status_data.append({
                    'Kode Perusahaan': column,
                    'Harga Terkini': current_price,
                    'Status': f"terendah {status_type}",
                    'Periode Data': period_info,
                    'Harga Terendah Periode': period_data.min(),
                    'Jumlah Data': len(all_time_data)
                })
                
        except Exception as e:
            st.warning(f"Error memproses {column}: {e}")
            continue
    
    # Buat dataframe dari data status
    if status_data:
        status_df = pd.DataFrame(status_data)
        status_df = status_df.set_index('Kode Perusahaan')
        return status_df
    else:
        st.info("Tidak ada saham yang memenuhi kriteria status")
        return None

def plot_stock_prices(stock_df, selected_stocks):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for stock in selected_stocks:
        if stock in stock_df.columns:
            ax.plot(stock_df.index, stock_df[stock], label=stock, linewidth=2)
    
    ax.set_title('Perubahan Harga Saham')
    ax.set_xlabel('Tanggal')
    ax.set_ylabel('Harga (IDR)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format tanggal pada x-axis
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">📈 Stock Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('### 📤 Upload File Daftar Saham')
    uploaded_file = st.file_uploader("Upload File Excel dengan kolom 'Kode' yang berisi daftar saham", 
                                    type=['xlsx'], 
                                    label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            daftar_emitem = pd.read_excel(uploaded_file)
            if 'Kode' in daftar_emitem.columns:
                stock_list = daftar_emitem['Kode'].tolist()
                
                # Informasi file yang diupload
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Jumlah Saham", len(stock_list))
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Nama File", uploaded_file.name)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.metric("Ukuran File", f"{uploaded_file.size / 1024:.1f} KB")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Tampilkan preview data
                st.markdown("### 📋 Preview Daftar Saham")
                st.dataframe(daftar_emitem.head(), use_container_width=True)
                
                # Informasi periode analisis
                st.markdown("### 📅 Informasi Periode Analisis")
                info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                with info_col1:
                    st.info(f"**Data Terakhir:**\n{datetime.now().date().strftime('%Y-%m-%d')}")
                with info_col2:
                    st.info(f"**Target 5 Tahun:**\n{(datetime.now() - timedelta(days=5*365)).date().strftime('%Y-%m-%d')}")
                with info_col3:
                    st.info(f"**Target 3 Tahun:**\n{(datetime.now() - timedelta(days=3*365)).date().strftime('%Y-%m-%d')}")
                with info_col4:
                    st.info(f"**Target 1 Tahun:**\n{(datetime.now() - timedelta(days=365)).date().strftime('%Y-%m-%d')}")
                
                # Load data button
                if st.button("🚀 Muat Data Saham", type="primary", use_container_width=True):
                    with st.spinner("Sedang memuat data saham..."):
                        saham_df = get_multiple_stocks(stock_list)
                        
                        if saham_df is not None:
                            st.session_state.saham_df = saham_df
                            st.session_state.stock_list = stock_list
                            st.success(f"✅ Berhasil memuat data {len(saham_df.columns)} saham")
                
                # Display data if available
                if 'saham_df' in st.session_state:
                    saham_df = st.session_state.saham_df
                    
                    st.divider()
                    st.markdown("### 📊 Metrics Data Saham")
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Jumlah Saham", len(saham_df.columns))
                    with col2:
                        st.metric("Periode Data", f"{len(saham_df)} hari")
                    with col3:
                        latest_date = saham_df.index[-1]
                        st.metric("Data Terakhir", str(latest_date))
                    with col4:
                        oldest_date = saham_df.index[0]
                        st.metric("Data Terlama", str(oldest_date))
                    
                    # Info periode masing-masing saham
                    st.markdown("### 📅 Info Periode Data per Saham")
                    period_info_data = []
                    for column in saham_df.columns:
                        period_info, available_years = get_data_period_info(saham_df[column])
                        period_info_data.append({
                            'Kode': column,
                            'Periode': period_info,
                            'Data Points': len(saham_df[column]),
                            'Tahun': available_years
                        })
                    
                    period_df = pd.DataFrame(period_info_data)
                    st.dataframe(period_df.set_index('Kode'), use_container_width=True)
                    
                    st.divider()
                    
                    # Stock selection for chart
                    st.markdown("### 📈 Grafik Harga Saham")
                    selected_stocks = st.multiselect(
                        "Pilih saham untuk ditampilkan pada grafik:",
                        options=saham_df.columns.tolist(),
                        default=saham_df.columns.tolist()[:3]  # Default first 3 stocks
                    )
                    
                    if selected_stocks:
                        fig = plot_stock_prices(saham_df, selected_stocks)
                        st.pyplot(fig)
                    
                    st.divider()
                    
                    # Status analysis
                    st.markdown("### 🔍 Analisis Status Harga")
                    
                    if st.button("🔄 Analisis Status Harga", use_container_width=True):
                        with st.spinner("Sedang menganalisis status harga..."):
                            status_df = get_status_dataframe(saham_df)
                            
                            if status_df is not None:
                                st.session_state.status_df = status_df
                    
                    if 'status_df' in st.session_state:
                        status_df = st.session_state.status_df
                        
                        # Display status table
                        st.dataframe(
                            status_df.style.format({
                                'Harga Terkini': '{:,}',
                                'Harga Terendah Periode': '{:,}',
                                'Jumlah Data': '{:,}'
                            }).highlight_max(color='lightgreen').highlight_min(color='lightcoral'),
                            use_container_width=True
                        )
                        
                        # Summary metrics
                        st.markdown("### 📋 Ringkasan Status")
                        status_counts = status_df['Status'].value_counts()
                        
                        for status_type, count in status_counts.items():
                            st.markdown(f'<div class="success-box">'
                                      f'🏆 {count} saham dengan status: <b>{status_type}</b>'
                                      f'</div>', unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Raw data
                    st.markdown("### 📄 Data Mentah")
                    if st.checkbox("Tampilkan data mentah"):
                        st.dataframe(saham_df.tail(20), use_container_width=True)
                        
                        # Download button
                        csv = saham_df.to_csv().encode('utf-8')
                        st.download_button(
                            label="📥 Download Data CSV",
                            data=csv,
                            file_name="stock_data.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        
            else:
                st.error("❌ File harus memiliki kolom 'Kode' yang berisi daftar kode saham")
                
        except Exception as e:
            st.error(f"❌ Error membaca file: {e}")
    
    else:
        st.markdown("""
        <div class="info-box">
        <h3>📝 Instruksi:</h3>
        <ol>
            <li>Upload file Excel yang memiliki kolom 'Kode' berisi daftar saham</li>
            <li>Contoh format: AALI, BBCA, BBRI, TLKM, UNVR</li>
            <li>File akan diproses dan data saham akan diambil otomatis</li>
            <li>Analisis status harga akan ditampilkan setelah data dimuat</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()