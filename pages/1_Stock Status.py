import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from io import BytesIO

# =========================================================
# 1. Fungsi utilitas
# =========================================================
def load_stock_list(filepath: str) -> pd.DataFrame:
    return pd.read_excel(filepath)

def fetch_stock_data(kode_saham: pd.DataFrame, period: str = "6y", progress_callback=None) -> pd.DataFrame:
    kode_list = (kode_saham['Kode'] + ".JK").to_list()
    total = len(kode_list)
    data_combined = pd.DataFrame()

    for i, kode in enumerate(kode_list, 1):
        try:
            ticker = yf.Ticker(kode)
            data = ticker.history(period=period)['Close'].round()
            data = data.to_frame(name=kode.replace(".JK", ""))
            if data_combined.empty:
                data_combined = data
            else:
                data_combined = data_combined.join(data, how='outer')
        except Exception:
            pass  # Lewati saham yang gagal diambil
        if progress_callback:
            progress_callback(i / total)

    # Format tanggal agar lebih rapi (dd-mm-yyyy)
    data_combined.index = data_combined.index.strftime("%d-%m-%Y")
    return data_combined

def filter_data_by_years(data: pd.DataFrame, years: int) -> pd.DataFrame:
    # Konversi index kembali ke datetime untuk perhitungan
    data.index = pd.to_datetime(data.index, format="%d-%m-%Y")
    latest_date = data.index.max()
    cutoff_date = latest_date - pd.DateOffset(years=years)
    subset = data[data.index >= cutoff_date]
    valid_cols = (
        subset[subset.index.year == cutoff_date.year]
        .dropna(axis=1, how="all")
        .columns.to_list()
    )
    subset.index = subset.index.strftime("%d-%m-%Y")
    return subset[valid_cols]

def compute_statistics(data: pd.DataFrame, label: str) -> dict:
    return {
        f"Max {label}": data.max(),
        f"Min {label}": data.min(),
        f"Mean {label}": data.mean().round()
    }

def combine_with_current(data_stats: dict, harga_sekarang: pd.DataFrame) -> pd.DataFrame:
    frames = [df.to_frame(name=col_name) for col_name, df in data_stats.items()]
    combined = pd.concat(frames + [harga_sekarang], axis=1)
    return combined

def check_status(row, period_label: str):
    now = row["Now"]
    value_5 = row.get(f"{period_label} 5 Years")
    value_3 = row.get(f"{period_label} 3 Years")
    value_1 = row.get(f"{period_label} 1 Years")
    if pd.notna(value_5) and now < value_5:
        return f"Lower than 5 years {period_label.lower()}"
    elif pd.notna(value_3) and now < value_3:
        return f"Lower than 3 years {period_label.lower()}"
    elif pd.notna(value_1) and now < value_1:
        return f"Lower than 1 year {period_label.lower()}"
    else:
        return None


# =========================================================
# 2. Fungsi utama analisis
# =========================================================
def analyze_data(data: pd.DataFrame):
    data_ff = data.ffill()
    latest_date = pd.to_datetime(data_ff.index, format="%d-%m-%Y").max()
    harga_sekarang = data_ff.loc[data_ff.index == latest_date.strftime("%d-%m-%Y")].T
    harga_sekarang.columns = ["Now"]

    data_1y = filter_data_by_years(data_ff.copy(), 1)
    data_3y = filter_data_by_years(data_ff.copy(), 3)
    data_5y = filter_data_by_years(data_ff.copy(), 5)

    stats_1y = compute_statistics(data_1y, "1 Years")
    stats_3y = compute_statistics(data_3y, "3 Years")
    stats_5y = compute_statistics(data_5y, "5 Years")

    result = {}
    for label in ["Max", "Min", "Mean"]:
        combined = combine_with_current(
            {
                f"{label} 1 Years": stats_1y[f"{label} 1 Years"],
                f"{label} 3 Years": stats_3y[f"{label} 3 Years"],
                f"{label} 5 Years": stats_5y[f"{label} 5 Years"],
            },
            harga_sekarang,
        )
        combined["Status"] = combined.apply(check_status, axis=1, period_label=label)
        combined = combined.dropna(subset=["Status"])
        result[label] = combined

    return result


# =========================================================
# 3. Streamlit Dashboard
# =========================================================
st.set_page_config(page_title="📊 Stock Analyzer Dashboard", layout="wide")
st.title("📈 Stock Analyzer Dashboard")

stock_file = "database/Daftar Saham.xlsx"

if "data_saham" not in st.session_state:
    st.session_state.data_saham = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None

# Tombol ambil data
st.subheader("1️⃣ Ambil Data Saham dari Yahoo Finance")
get_data_btn = st.button("📥 Get Stock Price")

if get_data_btn and stock_file is not None:
    kode_df = load_stock_list(stock_file)
    progress_bar = st.progress(0)
    with st.spinner("Mengambil data harga saham dari Yahoo Finance..."):
        data_saham = fetch_stock_data(kode_df, progress_callback=progress_bar.progress)
        st.session_state.data_saham = data_saham
    progress_bar.progress(1.0)
    st.success("✅ Data saham berhasil diambil!")

# Menampilkan tabel
st.subheader("2️⃣ Data Saham yang Diambil")
if st.session_state.data_saham is not None:
    st.dataframe(st.session_state.data_saham.tail(10))
else:
    st.info("Belum ada data saham yang diambil. Tekan tombol Get Stock Price untuk mulai.")

# =========================================================
# Grafik Per Saham
# =========================================================
if st.session_state.data_saham is not None:
    st.subheader("📊 Grafik Harga Saham")
    saham_terpilih = st.selectbox("Pilih saham untuk ditampilkan:", st.session_state.data_saham.columns)
    df_chart = st.session_state.data_saham[[saham_terpilih]].dropna()
    df_chart.index = pd.to_datetime(df_chart.index, format="%d-%m-%Y")
    st.line_chart(df_chart, height=400)
else:
    st.subheader("📊 Grafik Harga Saham")
    st.info("Grafik akan muncul setelah data berhasil diambil.")

# =========================================================
# Analisis dan Status
# =========================================================
if st.session_state.data_saham is not None:
    st.subheader("3️⃣ Analisis Status Saham")
    option = st.radio("Pilih tipe analisis:", ["Max", "Min", "Mean"], horizontal=True)

    if st.session_state.analysis is None:
        with st.spinner("Menganalisis data saham..."):
            st.session_state.analysis = analyze_data(st.session_state.data_saham)

    df_status = st.session_state.analysis[option]
    st.dataframe(df_status)

    # Generate file Excel
    st.subheader("4️⃣ Generate File Excel")
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for label, df in st.session_state.analysis.items():
            df.to_excel(writer, sheet_name=label)
    buffer.seek(0)

    st.download_button(
        label="💾 Download Excel File",
        data=buffer,
        file_name="Stock_Status.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.subheader("3️⃣ Analisis Status Saham")
    st.radio("Pilih tipe analisis:", ["Max", "Min", "Mean"], horizontal=True)
    st.info("Analisis belum dapat dilakukan sebelum data diambil.")
    st.subheader("4️⃣ Generate File Excel")
    st.warning("Silakan ambil data saham terlebih dahulu sebelum membuat file Excel.")
