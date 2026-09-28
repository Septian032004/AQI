import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="🌫️",
    layout="wide",
)

# -----------------------------
# STYLE
# -----------------------------
st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {
    background: rgba(128,128,128,0.08);
    border: 1px solid rgba(128,128,128,0.18);
    padding: 14px 16px;
    border-radius: 14px;
}
.small-note {color:#777; font-size:0.88rem;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD & CLEAN DATA
# -----------------------------
@st.cache_data
def load_data():
    candidates = [
        Path("Data AQI.json"),
        Path("/mnt/data/Data AQI.json"),
    ]
    file_path = next((p for p in candidates if p.exists()), None)
    if file_path is None:
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    df = pd.DataFrame(raw)

    # Convert decimal comma strings, e.g. "221,5" -> 221.5
    numeric_cols = ["aqi", "AQI-IN", "pm25", "pm10", "co", "so2", "no2", "o3"]
    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .replace("nan", np.nan)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_localize(None)
    df = df.sort_values("date").reset_index(drop=True)

    df["AQI Change"] = df["aqi"].diff()
    df["AQI Change %"] = df["aqi"].pct_change() * 100
    return df

df = load_data()

st.title("Air Quality Dashboard")
st.caption("Monitoring AQI dan parameter kualitas udara • 29 Agustus – 26 September 2026")

if df is None:
    st.error("File `Data AQI.json` tidak ditemukan. Letakkan file JSON di folder yang sama dengan `app.py`.")
    st.stop()

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Filter Dashboard")

min_date = df["date"].min().date()
max_date = df["date"].max().date()

date_range = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

filtered = df[
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
].copy()

pollutants = ["pm25", "pm10", "co", "so2", "no2", "o3"]
pollutant_labels = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "co": "CO",
    "so2": "SO₂",
    "no2": "NO₂",
    "o3": "O₃",
}

selected_pollutant = st.sidebar.selectbox(
    "Polutan untuk analisis",
    pollutants,
    format_func=lambda x: pollutant_labels[x],
)

if filtered.empty:
    st.warning("Tidak ada data pada rentang tanggal yang dipilih.")
    st.stop()

# -----------------------------
# KPI
# -----------------------------
avg_aqi = filtered["aqi"].mean()
max_idx = filtered["aqi"].idxmax()
min_idx = filtered["aqi"].idxmin()
max_aqi = filtered.loc[max_idx, "aqi"]
min_aqi = filtered.loc[min_idx, "aqi"]
max_date_aqi = filtered.loc[max_idx, "date"]
min_date_aqi = filtered.loc[min_idx, "date"]
avg_pm25 = filtered["pm25"].mean()

latest = filtered.iloc[-1]
previous = filtered.iloc[-2] if len(filtered) > 1 else None
delta_latest = latest["aqi"] - previous["aqi"] if previous is not None else None

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rata-rata AQI", f"{avg_aqi:.2f}")
c2.metric("AQI Tertinggi", f"{max_aqi:.1f}", max_date_aqi.strftime("%d %b"))
c3.metric("AQI Terendah", f"{min_aqi:.1f}", min_date_aqi.strftime("%d %b"))
c4.metric("Rata-rata PM2.5", f"{avg_pm25:.2f}")
c5.metric(
    "AQI Terbaru",
    f"{latest['aqi']:.1f}",
    None if delta_latest is None else f"{delta_latest:+.1f} vs hari sebelumnya",
    delta_color="inverse",
)

st.divider()

# -----------------------------
# MAIN TREND
# -----------------------------
left, right = st.columns([2.1, 1])

with left:
    st.subheader("Tren AQI Harian")
    fig = px.line(
        filtered,
        x="date",
        y="aqi",
        markers=True,
        labels={"date": "Tanggal", "aqi": "AQI"},
    )
    fig.add_hline(
        y=avg_aqi,
        line_dash="dash",
        annotation_text=f"Rata-rata {avg_aqi:.1f}",
        annotation_position="top left",
    )
    fig.update_layout(
        height=390,
        margin=dict(l=10, r=10, t=20, b=10),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Ringkasan Periode")
    largest_up_idx = filtered["AQI Change"].idxmax()
    largest_down_idx = filtered["AQI Change"].idxmin()

    if len(filtered) > 1:
        up = filtered.loc[largest_up_idx]
        down = filtered.loc[largest_down_idx]
        st.metric(
            "Kenaikan Harian Terbesar",
            f"+{up['AQI Change']:.1f}",
            up["date"].strftime("%d %b %Y"),
            delta_color="inverse",
        )
        st.metric(
            "Penurunan Harian Terbesar",
            f"{down['AQI Change']:.1f}",
            down["date"].strftime("%d %b %Y"),
            delta_color="inverse",
        )

    st.metric("Jumlah Observasi", f"{len(filtered)} hari")
    st.markdown(
        f'<div class="small-note">Periode: {start_date.strftime("%d %b %Y")} – '
        f'{end_date.strftime("%d %b %Y")}</div>',
        unsafe_allow_html=True,
    )

# -----------------------------
# POLLUTANTS
# -----------------------------
st.subheader("Profil Polutan")

avg_pollutants = (
    filtered[pollutants]
    .mean()
    .rename(index=pollutant_labels)
    .reset_index()
)
avg_pollutants.columns = ["Polutan", "Rata-rata"]

col1, col2 = st.columns(2)

with col1:
    fig_bar = px.bar(
        avg_pollutants,
        x="Polutan",
        y="Rata-rata",
        text_auto=".1f",
        labels={"Rata-rata": "Nilai rata-rata"},
    )
    fig_bar.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    fig_pol = px.line(
        filtered,
        x="date",
        y=selected_pollutant,
        markers=True,
        labels={
            "date": "Tanggal",
            selected_pollutant: pollutant_labels[selected_pollutant],
        },
        title=f"Tren {pollutant_labels[selected_pollutant]}",
    )
    fig_pol.update_layout(height=360, margin=dict(l=10, r=10, t=45, b=10))
    st.plotly_chart(fig_pol, use_container_width=True)

# -----------------------------
# RELATIONSHIP & CORRELATION
# -----------------------------
st.subheader("Hubungan Polutan dengan AQI")

corr = (
    filtered[["aqi"] + pollutants]
    .corr(numeric_only=True)["aqi"]
    .drop("aqi")
    .sort_values()
)
corr_df = corr.rename(index=pollutant_labels).reset_index()
corr_df.columns = ["Polutan", "Korelasi"]

col3, col4 = st.columns(2)

with col3:
    fig_corr = px.bar(
        corr_df,
        x="Korelasi",
        y="Polutan",
        orientation="h",
        text_auto=".3f",
        range_x=[-1, 1],
        title="Korelasi Pearson terhadap AQI",
    )
    fig_corr.add_vline(x=0, line_width=1)
    fig_corr.update_layout(height=380, margin=dict(l=10, r=10, t=45, b=10))
    st.plotly_chart(fig_corr, use_container_width=True)

with col4:
    corr_selected = filtered[["aqi", selected_pollutant]].corr().iloc[0, 1]
    fig_scatter = px.scatter(
        filtered,
        x=selected_pollutant,
        y="aqi",
        trendline="ols" if len(filtered) >= 3 else None,
        hover_data={"date": "|%d %b %Y"},
        labels={
            selected_pollutant: pollutant_labels[selected_pollutant],
            "aqi": "AQI",
        },
        title=f"AQI vs {pollutant_labels[selected_pollutant]} • r = {corr_selected:.3f}",
    )
    fig_scatter.update_layout(height=380, margin=dict(l=10, r=10, t=45, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# -----------------------------
# AQI VS AQI-IN
# -----------------------------
st.subheader("Perbandingan AQI dan AQI-IN")
fig_compare = go.Figure()
fig_compare.add_trace(
    go.Scatter(
        x=filtered["date"],
        y=filtered["aqi"],
        mode="lines+markers",
        name="AQI",
    )
)
fig_compare.add_trace(
    go.Scatter(
        x=filtered["date"],
        y=filtered["AQI-IN"],
        mode="lines+markers",
        name="AQI-IN",
    )
)
fig_compare.update_layout(
    height=390,
    xaxis_title="Tanggal",
    yaxis_title="Indeks",
    hovermode="x unified",
    margin=dict(l=10, r=10, t=20, b=10),
)
st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------
# INSIGHTS
# -----------------------------
st.subheader("Insight Otomatis")

strongest = corr.abs().idxmax()
strongest_corr = corr.loc[strongest]
direction = "positif" if strongest_corr >= 0 else "negatif"

ins1, ins2, ins3 = st.columns(3)

with ins1:
    st.info(
        f"**Puncak AQI**\n\nAQI tertinggi **{max_aqi:.1f}** terjadi pada "
        f"**{max_date_aqi.strftime('%d %B %Y')}**."
    )

with ins2:
    st.info(
        f"**Polutan paling terkait**\n\n**{pollutant_labels[strongest]}** memiliki "
        f"korelasi {direction} terkuat dengan AQI, yaitu **r = {strongest_corr:.3f}**."
    )

with ins3:
    if len(filtered) > 1:
        st.info(
            f"**Perubahan terbesar**\n\nKenaikan AQI harian terbesar adalah "
            f"**{up['AQI Change']:+.1f} poin** pada **{up['date'].strftime('%d %B %Y')}**."
        )
    else:
        st.info("Pilih minimal dua hari untuk menghitung perubahan AQI.")

# -----------------------------
# DATA TABLE
# -----------------------------
with st.expander("Lihat data lengkap"):
    display = filtered.copy()
    display["date"] = display["date"].dt.strftime("%d-%m-%Y")
    display = display.rename(columns={
        "date": "Tanggal",
        "aqi": "AQI",
        "pm25": "PM2.5",
        "pm10": "PM10",
        "co": "CO",
        "so2": "SO₂",
        "no2": "NO₂",
        "o3": "O₃",
    })
    st.dataframe(display, use_container_width=True, hide_index=True)

st.caption(
    "Catatan: korelasi menunjukkan hubungan statistik pada periode data yang dipilih "
    "dan tidak dengan sendirinya menunjukkan hubungan sebab-akibat."
)
