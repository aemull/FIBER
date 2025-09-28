import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# ===============================
# CONFIG
# ===============================
API_KEY = "2b6c8ad4-5b20-4d72-997d-ccfd935cad32"  # ganti dengan API key dari CommodityPriceAPI
BASE_URL = "https://api.commoditypriceapi.com/v2"

HEADERS = {
    "x-api-key": API_KEY
}

# ===============================
# Fungsi API
# ===============================
def get_symbols():
    """
    Ambil daftar simbol dari CommodityPriceAPI v2
    """
    url = f"{BASE_URL}/symbols"
    resp = requests.get(url, headers=HEADERS)

    try:
        data = resp.json()
    except Exception:
        st.error(f"Response bukan JSON: {resp.text}")
        return {}

    if resp.status_code != 200:
        st.error(f"Gagal ambil simbol: {data}")
        return {}

    symbols = data.get("data", [])
    # Filter hanya metals
    metals = {
        s["name"]: s["symbol"]
        for s in symbols
        if "metal" in s.get("category", "").lower()
    }
    return metals


def fetch_timeseries(symbol: str, start_date: str, end_date: str):
    """
    Ambil data historis logam dari CommodityPriceAPI v2
    """
    url = f"{BASE_URL}/timeseries"
    params = {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "currency": "USD"
    }
    resp = requests.get(url, headers=HEADERS, params=params)

    try:
        data = resp.json()
    except Exception:
        st.error(f"Response bukan JSON: {resp.text}")
        return None

    if resp.status_code != 200:
        st.error(f"Error API: {data}")
        return None

    prices = data.get("data", [])
    if not prices:
        return None

    df = pd.DataFrame(prices)
    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={"price": "Price"})
    df = df.sort_values("date")
    return df

# ===============================
# Streamlit App
# ===============================
def main():
    st.title("📈 Harga Komoditas - 10 Tahun Terakhir")
    st.markdown("Data diambil dari [CommodityPriceAPI v2](https://www.commoditypriceapi.com)")

    # Ambil simbol metals
    metals = get_symbols()
    if not metals:
        st.stop()

    # Pilih logam
    metal_choice = st.selectbox("Pilih Logam", list(metals.keys()))

    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*10)  # 10 tahun

    df = fetch_timeseries(
        metals[metal_choice],
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    if df is None or df.empty:
        st.warning("Data tidak tersedia untuk pilihan ini.")
    else:
        st.subheader(f"Harga {metal_choice} (USD)")

        # Chart
        fig = px.line(df, x="date", y="Price", title=f"{metal_choice} Price (10 Tahun)")
        st.plotly_chart(fig, use_container_width=True)

        # Dataframe preview
        st.dataframe(df.tail(10))

        # Statistik
        st.subheader("Statistik Dasar")
        st.write({
            "Harga maksimum": df["Price"].max(),
            "Harga minimum": df["Price"].min(),
            "Harga rata-rata": round(df["Price"].mean(), 2)
        })

if __name__ == "__main__":
    main()
