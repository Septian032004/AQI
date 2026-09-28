# ============================================================
# AIR QUALITY DASHBOARD
# Streamlit Dashboard
# ============================================================

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. CUSTOM STYLE
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background: rgba(128,128,128,0.08);
        border: 1px solid rgba(128,128,128,0.18);
        padding: 15px 17px;
        border-radius: 14px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
    }

    .small-note {
        color: #888888;
        font-size: 0.88rem;
    }

    .dashboard-subtitle {
        color: #888888;
        font-size: 1rem;
        margin-top: -10px;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    # --------------------------------------------------------
    # Folder tempat app.py berada
    # --------------------------------------------------------

    BASE_DIR = Path(__file__).resolve().parent

    # Nama file harus sama persis dengan file di GitHub
    file_path = BASE_DIR / "Data AQI.json"

    # --------------------------------------------------------
    # Cek keberadaan file
    # --------------------------------------------------------

    if not file_path.exists():

        return None, BASE_DIR

    # --------------------------------------------------------
    # Baca JSON
    # --------------------------------------------------------

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            raw = json.load(file)

    except json.JSONDecodeError as error:

        st.error(
            f"Format JSON tidak valid: {error}"
        )

        return None, BASE_DIR

    except Exception as error:

        st.error(
            f"Gagal membaca file JSON: {error}"
        )

        return None, BASE_DIR


    # --------------------------------------------------------
    # Convert JSON menjadi DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(raw)


    # --------------------------------------------------------
    # Validasi kolom
    # --------------------------------------------------------

    required_columns = [
        "date",
        "aqi",
        "AQI-IN",
        "pm25",
        "pm10",
        "co",
        "so2",
        "no2",
        "o3",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        st.error(
            "Kolom berikut tidak ditemukan pada JSON: "
            + ", ".join(missing_columns)
        )

        return None, BASE_DIR


    # --------------------------------------------------------
    # Membersihkan kolom numerik
    #
    # Contoh:
    # "221,5" -> 221.5
    # --------------------------------------------------------

    numeric_columns = [
        "aqi",
        "AQI-IN",
        "pm25",
        "pm10",
        "co",
        "so2",
        "no2",
        "o3",
    ]

    for column in numeric_columns:

        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)
        )

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


    # --------------------------------------------------------
    # Convert tanggal
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
        utc=True
    )

    # Hapus timezone agar lebih mudah digunakan Streamlit
    df["date"] = df["date"].dt.tz_localize(None)


    # --------------------------------------------------------
    # Hapus data dengan tanggal/AQI kosong
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "date",
            "aqi"
        ]
    )


    # --------------------------------------------------------
    # Urutkan tanggal
    # --------------------------------------------------------

    df = (
        df
        .sort_values("date")
        .reset_index(drop=True)
    )


    return df, BASE_DIR


# ============================================================
# 4. LOAD DATA
# ============================================================

df, base_dir = load_data()


# ============================================================
# 5. HEADER
# ============================================================

st.title(
    "🌫️ Air Quality Dashboard"
)


# ============================================================
# 6. ERROR HANDLING FILE
# ============================================================

if df is None:

    st.error(
        "File `Data AQI.json` tidak ditemukan atau tidak dapat dibaca."
    )

    st.info(
        """
        Pastikan struktur repository GitHub seperti berikut:

        ```
        repository/
        ├── app.py
        ├── Data AQI.json
        ├── requirements.txt
        └── README.txt
        ```
        """
    )

    st.write(
        "**Folder yang sedang dibaca aplikasi:**"
    )

    st.code(
        str(base_dir)
    )


    # Menampilkan file yang ditemukan
    try:

        files_available = [
            file.name
            for file in base_dir.iterdir()
        ]

        st.write(
            "**File yang ditemukan:**"
        )

        st.write(
            files_available
        )

    except Exception:

        pass


    st.stop()


# ============================================================
# 7. DATA INFORMATION
# ============================================================

min_date = df["date"].min().date()

max_date = df["date"].max().date()


st.markdown(
    f"""
    <div class="dashboard-subtitle">
    Monitoring AQI dan parameter kualitas udara •
    {min_date.strftime("%d %B %Y")} –
    {max_date.strftime("%d %B %Y")}
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 8. SIDEBAR
# ============================================================

st.sidebar.title(
    "🌫️ Air Quality"
)

st.sidebar.caption(
    "Dashboard Monitoring"
)

st.sidebar.divider()

st.sidebar.header(
    "Filter Dashboard"
)


# ============================================================
# 9. DATE FILTER
# ============================================================

date_range = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(
        min_date,
        max_date
    ),
    min_value=min_date,
    max_value=max_date,
)


# ------------------------------------------------------------
# Handle filter tanggal
# ------------------------------------------------------------

if (
    isinstance(date_range, (tuple, list))
    and len(date_range) == 2
):

    start_date = date_range[0]

    end_date = date_range[1]

else:

    start_date = min_date

    end_date = max_date


# ============================================================
# 10. POLLUTANT CONFIGURATION
# ============================================================

pollutants = [
    "pm25",
    "pm10",
    "co",
    "so2",
    "no2",
    "o3",
]


pollutant_labels = {

    "pm25": "PM2.5",

    "pm10": "PM10",

    "co": "CO",

    "so2": "SO₂",

    "no2": "NO₂",

    "o3": "O₃",

}


selected_pollutant = st.sidebar.selectbox(
    "Pilih Polutan",
    pollutants,
    format_func=lambda x: pollutant_labels[x],
)


# ============================================================
# 11. FILTER DATA
# ============================================================

filtered = df[
    (
        df["date"].dt.date
        >= start_date
    )
    &
    (
        df["date"].dt.date
        <= end_date
    )
].copy()


# ------------------------------------------------------------
# Reset index
# ------------------------------------------------------------

filtered = filtered.reset_index(
    drop=True
)


# ------------------------------------------------------------
# Perubahan AQI dihitung SETELAH filter
# ------------------------------------------------------------

filtered["AQI Change"] = (
    filtered["aqi"]
    .diff()
)


filtered["AQI Change %"] = (
    filtered["aqi"]
    .pct_change()
    * 100
)


# ------------------------------------------------------------
# Cek data kosong
# ------------------------------------------------------------

if filtered.empty:

    st.warning(
        "Tidak ada data pada rentang tanggal yang dipilih."
    )

    st.stop()


# ============================================================
# 12. KPI CALCULATION
# ============================================================

avg_aqi = filtered["aqi"].mean()

max_aqi = filtered["aqi"].max()

min_aqi = filtered["aqi"].min()

avg_pm25 = filtered["pm25"].mean()


# ------------------------------------------------------------
# Lokasi AQI tertinggi
# ------------------------------------------------------------

max_row = filtered.loc[
    filtered["aqi"].idxmax()
]


# ------------------------------------------------------------
# Lokasi AQI terendah
# ------------------------------------------------------------

min_row = filtered.loc[
    filtered["aqi"].idxmin()
]


max_date_aqi = max_row["date"]

min_date_aqi = min_row["date"]


# ------------------------------------------------------------
# AQI terbaru
# ------------------------------------------------------------

latest = filtered.iloc[-1]


if len(filtered) > 1:

    previous = filtered.iloc[-2]

    delta_latest = (
        latest["aqi"]
        - previous["aqi"]
    )

else:

    delta_latest = None


# ============================================================
# 13. KPI CARDS
# ============================================================

st.subheader(
    "Ringkasan Kualitas Udara"
)


c1, c2, c3, c4, c5 = st.columns(5)


with c1:

    st.metric(
        label="Rata-rata AQI",
        value=f"{avg_aqi:.2f}",
    )


with c2:

    st.metric(
        label="AQI Tertinggi",
        value=f"{max_aqi:.1f}",
        delta=max_date_aqi.strftime(
            "%d %b"
        ),
        delta_color="off",
    )


with c3:

    st.metric(
        label="AQI Terendah",
        value=f"{min_aqi:.1f}",
        delta=min_date_aqi.strftime(
            "%d %b"
        ),
        delta_color="off",
    )


with c4:

    st.metric(
        label="Rata-rata PM2.5",
        value=f"{avg_pm25:.2f}",
    )


with c5:

    if delta_latest is not None:

        st.metric(
            label="AQI Terbaru",
            value=f"{latest['aqi']:.1f}",
            delta=f"{delta_latest:+.1f} vs sebelumnya",
            delta_color="inverse",
        )

    else:

        st.metric(
            label="AQI Terbaru",
            value=f"{latest['aqi']:.1f}",
        )


st.divider()


# ============================================================
# 14. AQI TREND
# ============================================================

left, right = st.columns(
    [2.2, 1]
)


with left:

    st.subheader(
        "Tren AQI Harian"
    )


    fig_aqi = px.line(
        filtered,
        x="date",
        y="aqi",
        markers=True,
        labels={
            "date": "Tanggal",
            "aqi": "AQI",
        },
    )


    # Garis rata-rata
    fig_aqi.add_hline(

        y=avg_aqi,

        line_dash="dash",

        annotation_text=(
            f"Rata-rata = {avg_aqi:.1f}"
        ),

        annotation_position="top left",

    )


    # Titik maksimum
    fig_aqi.add_trace(

        go.Scatter(

            x=[
                max_date_aqi
            ],

            y=[
                max_aqi
            ],

            mode="markers",

            marker=dict(
                size=13
            ),

            name="AQI Tertinggi",

        )

    )


    # Titik minimum
    fig_aqi.add_trace(

        go.Scatter(

            x=[
                min_date_aqi
            ],

            y=[
                min_aqi
            ],

            mode="markers",

            marker=dict(
                size=13
            ),

            name="AQI Terendah",

        )

    )


    fig_aqi.update_layout(

        height=430,

        hovermode="x unified",

        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10
        ),

        legend=dict(
            orientation="h"
        ),

    )


    st.plotly_chart(
        fig_aqi,
        use_container_width=True
    )


# ============================================================
# 15. PERIOD SUMMARY
# ============================================================

with right:

    st.subheader(
        "Ringkasan Periode"
    )


    if len(filtered) > 1:

        valid_changes = (
            filtered
            .dropna(
                subset=["AQI Change"]
            )
        )


        if not valid_changes.empty:

            up = valid_changes.loc[
                valid_changes[
                    "AQI Change"
                ].idxmax()
            ]


            down = valid_changes.loc[
                valid_changes[
                    "AQI Change"
                ].idxmin()
            ]


            st.metric(

                "Kenaikan Terbesar",

                f"{up['AQI Change']:+.1f}",

                up["date"].strftime(
                    "%d %b %Y"
                ),

                delta_color="inverse",

            )


            st.metric(

                "Penurunan Terbesar",

                f"{down['AQI Change']:+.1f}",

                down["date"].strftime(
                    "%d %b %Y"
                ),

                delta_color="inverse",

            )


    st.metric(

        "Jumlah Observasi",

        f"{len(filtered)} hari"

    )


    st.metric(

        "Rata-rata AQI-IN",

        f"{filtered['AQI-IN'].mean():.2f}"

    )


    st.markdown(

        f"""
        <div class="small-note">
        Periode:<br>
        {start_date.strftime("%d %b %Y")}
        –
        {end_date.strftime("%d %b %Y")}
        </div>
        """,

        unsafe_allow_html=True,

    )


# ============================================================
# 16. POLLUTANT PROFILE
# ============================================================

st.divider()

st.subheader(
    "Profil Polutan"
)


avg_pollutants = (

    filtered[pollutants]

    .mean()

    .rename(
        index=pollutant_labels
    )

    .reset_index()

)


avg_pollutants.columns = [
    "Polutan",
    "Rata-rata",
]


col1, col2 = st.columns(2)


# ============================================================
# 17. AVERAGE POLLUTANT
# ============================================================

with col1:

    st.markdown(
        "#### Rata-rata Parameter Polutan"
    )


    fig_bar = px.bar(

        avg_pollutants,

        x="Polutan",

        y="Rata-rata",

        text_auto=".1f",

        labels={
            "Rata-rata":
            "Nilai Rata-rata"
        },

    )


    fig_bar.update_traces(

        textposition="outside"

    )


    fig_bar.update_layout(

        height=400,

        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10
        ),

    )


    st.plotly_chart(

        fig_bar,

        use_container_width=True

    )


# ============================================================
# 18. POLLUTANT TREND
# ============================================================

with col2:

    st.markdown(
        f"#### Tren {pollutant_labels[selected_pollutant]}"
    )


    fig_pollutant = px.line(

        filtered,

        x="date",

        y=selected_pollutant,

        markers=True,

        labels={

            "date":
            "Tanggal",

            selected_pollutant:
            pollutant_labels[
                selected_pollutant
            ],

        },

    )


    fig_pollutant.update_layout(

        height=400,

        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10
        ),

        hovermode="x unified",

    )


    st.plotly_chart(

        fig_pollutant,

        use_container_width=True

    )


# ============================================================
# 19. CORRELATION ANALYSIS
# ============================================================

st.divider()

st.subheader(
    "Hubungan Polutan dengan AQI"
)


# Korelasi membutuhkan minimal 2 observasi
if len(filtered) >= 2:

    corr = (

        filtered[
            ["aqi"]
            + pollutants
        ]

        .corr(
            numeric_only=True
        )["aqi"]

        .drop("aqi")

    )


    corr_df = (

        corr

        .rename(
            index=pollutant_labels
        )

        .reset_index()

    )


    corr_df.columns = [
        "Polutan",
        "Korelasi",
    ]


    corr_df = corr_df.sort_values(
        "Korelasi"
    )


    col3, col4 = st.columns(2)


    # --------------------------------------------------------
    # Correlation bar
    # --------------------------------------------------------

    with col3:

        fig_corr = px.bar(

            corr_df,

            x="Korelasi",

            y="Polutan",

            orientation="h",

            text_auto=".3f",

            range_x=[
                -1,
                1
            ],

            title=(
                "Korelasi Pearson terhadap AQI"
            ),

        )


        fig_corr.add_vline(
            x=0
        )


        fig_corr.update_layout(

            height=420,

            margin=dict(
                l=10,
                r=10,
                t=50,
                b=10
            ),

        )


        st.plotly_chart(

            fig_corr,

            use_container_width=True

        )


    # --------------------------------------------------------
    # Scatter plot
    # --------------------------------------------------------

    with col4:

        valid_scatter = filtered[
            [
                selected_pollutant,
                "aqi",
                "date",
            ]
        ].dropna()


        if len(valid_scatter) >= 2:

            corr_selected = (

                valid_scatter[
                    [
                        "aqi",
                        selected_pollutant
                    ]
                ]

                .corr()

                .iloc[0, 1]

            )


            fig_scatter = px.scatter(

                valid_scatter,

                x=selected_pollutant,

                y="aqi",

                hover_data=[
                    "date"
                ],

                labels={

                    selected_pollutant:
                    pollutant_labels[
                        selected_pollutant
                    ],

                    "aqi":
                    "AQI",

                },

                title=(

                    f"AQI vs "
                    f"{pollutant_labels[selected_pollutant]}"
                    f" • r = {corr_selected:.3f}"

                ),

            )


            # ------------------------------------------------
            # Regression line manual
            # Tidak membutuhkan statsmodels
            # ------------------------------------------------

            if (
                len(valid_scatter) >= 3
                and
                valid_scatter[
                    selected_pollutant
                ].nunique() > 1
            ):

                x = (
                    valid_scatter[
                        selected_pollutant
                    ].to_numpy()
                )

                y = (
                    valid_scatter[
                        "aqi"
                    ].to_numpy()
                )


                slope, intercept = np.polyfit(
                    x,
                    y,
                    1
                )


                x_line = np.linspace(
                    x.min(),
                    x.max(),
                    100
                )


                y_line = (
                    slope
                    * x_line
                    + intercept
                )


                fig_scatter.add_trace(

                    go.Scatter(

                        x=x_line,

                        y=y_line,

                        mode="lines",

                        name="Trend Linear",

                    )

                )


            fig_scatter.update_layout(

                height=420,

                margin=dict(
                    l=10,
                    r=10,
                    t=50,
                    b=10
                ),

            )


            st.plotly_chart(

                fig_scatter,

                use_container_width=True

            )


        else:

            st.info(
                "Data tidak cukup untuk membuat scatter plot."
            )


else:

    st.info(
        "Pilih minimal 2 hari untuk menghitung korelasi."
    )


# ============================================================
# 20. AQI VS AQI-IN
# ============================================================

st.divider()

st.subheader(
    "Perbandingan AQI dan AQI-IN"
)


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

    height=420,

    xaxis_title="Tanggal",

    yaxis_title="Indeks",

    hovermode="x unified",

    legend=dict(
        orientation="h"
    ),

    margin=dict(
        l=10,
        r=10,
        t=20,
        b=10
    ),

)


st.plotly_chart(

    fig_compare,

    use_container_width=True

)


# ============================================================
# 21. AUTOMATIC INSIGHTS
# ============================================================

st.divider()

st.subheader(
    "💡 Insight Otomatis"
)


if len(filtered) >= 2:

    valid_corr = corr.dropna()


    if not valid_corr.empty:

        strongest = (
            valid_corr
            .abs()
            .idxmax()
        )


        strongest_corr = (
            valid_corr[
                strongest
            ]
        )


        if strongest_corr >= 0:

            direction = "positif"

        else:

            direction = "negatif"


        ins1, ins2, ins3 = st.columns(3)


        # ----------------------------------------------------
        # Insight 1
        # ----------------------------------------------------

        with ins1:

            st.info(

                f"""
                **Puncak AQI**

                AQI tertinggi sebesar
                **{max_aqi:.1f}**
                terjadi pada
                **{max_date_aqi.strftime("%d %B %Y")}**.
                """

            )


        # ----------------------------------------------------
        # Insight 2
        # ----------------------------------------------------

        with ins2:

            st.info(

                f"""
                **Polutan Paling Terkait**

                **{pollutant_labels[strongest]}**
                memiliki korelasi {direction}
                terkuat dengan AQI:

                **r = {strongest_corr:.3f}**
                """

            )


        # ----------------------------------------------------
        # Insight 3
        # ----------------------------------------------------

        with ins3:

            if len(filtered) > 1:

                valid_changes = (
                    filtered
                    .dropna(
                        subset=["AQI Change"]
                    )
                )


                if not valid_changes.empty:

                    up = valid_changes.loc[
                        valid_changes[
                            "AQI Change"
                        ].idxmax()
                    ]


                    st.info(

                        f"""
                        **Perubahan Terbesar**

                        Kenaikan AQI terbesar:

                        **{up['AQI Change']:+.1f} poin**

                        pada
                        **{up['date'].strftime("%d %B %Y")}**.
                        """

                    )


else:

    st.info(
        "Pilih minimal dua hari untuk menghasilkan insight."
    )


# ============================================================
# 22. SUMMARY STATISTICS
# ============================================================

st.divider()

st.subheader(
    "Statistik Deskriptif"
)


summary = filtered[
    [
        "aqi",
        "AQI-IN",
        "pm25",
        "pm10",
        "co",
        "so2",
        "no2",
        "o3",
    ]
].agg(
    [
        "mean",
        "min",
        "max",
        "std",
    ]
)


summary.index = [
    "Rata-rata",
    "Minimum",
    "Maksimum",
    "Standar Deviasi",
]


summary = summary.rename(
    columns={
        "aqi": "AQI",
        "pm25": "PM2.5",
        "pm10": "PM10",
        "co": "CO",
        "so2": "SO₂",
        "no2": "NO₂",
        "o3": "O₃",
    }
)


st.dataframe(

    summary.style.format(
        "{:.2f}"
    ),

    use_container_width=True,

)


# ============================================================
# 23. DATA TABLE
# ============================================================

st.divider()


with st.expander(
    "📋 Lihat Data Lengkap"
):

    display = filtered.copy()


    display["date"] = (

        display["date"]

        .dt.strftime(
            "%d-%m-%Y"
        )

    )


    display = display.rename(

        columns={

            "date":
            "Tanggal",

            "aqi":
            "AQI",

            "pm25":
            "PM2.5",

            "pm10":
            "PM10",

            "co":
            "CO",

            "so2":
            "SO₂",

            "no2":
            "NO₂",

            "o3":
            "O₃",

        }

    )


    st.dataframe(

        display,

        use_container_width=True,

        hide_index=True,

    )


# ============================================================
# 24. DOWNLOAD DATA
# ============================================================

csv = (
    display
    .to_csv(
        index=False
    )
    .encode(
        "utf-8"
    )
)


st.download_button(

    label="⬇️ Download Data Hasil Filter",

    data=csv,

    file_name=(
        "air_quality_filtered.csv"
    ),

    mime="text/csv",

)


# ============================================================
# 25. FOOTER
# ============================================================

st.divider()


st.caption(
    "Air Quality Dashboard • "
    "Korelasi menunjukkan hubungan statistik pada periode "
    "yang dipilih dan tidak dengan sendirinya menunjukkan "
    "hubungan sebab-akibat."
)
