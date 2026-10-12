import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. KONFIGURASI HALAMAN
# ==============================================================================
st.set_page_config(
    page_title="Dashboard PBCK-3 | KPPBC TMC Malang",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling CSS (Tema Eksekutif Modern Bea Cukai)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        text-align: center;
        margin-bottom: 12px;
        color: white;
    }
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #E2E8F0;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 21px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3989 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. PENGAMBILAN & PEMBERSIHAN DATA CLOUD
# ==============================================================================
FILE_ID = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
URL_DOWNLOAD = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_excel(URL_DOWNLOAD, sheet_name="DATABASE MERGE")
        
        # 1. Bersihkan spasi tersembunyi di seluruh nama kolom
        df.columns = df.columns.astype(str).str.strip()
        
        # 2. Pembersihan & standardisasi kolom numerik penting
        numeric_cols = ["TOTAL_CUKAI", "CUKAI_MS", "JUMLAH_BP", "TOTAL_BUNGKUS", "TOTAL_BUNGKUS_MS"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str)
                    .str.replace("Rp", "", regex=False)
                    .str.replace(".", "", regex=False)
                    .str.replace(",", ".", regex=False)
                    .str.strip(),
                    errors="coerce"
                ).fillna(0)
            else:
                df[col] = 0
                
        # 3. Format Tanggal CK-2 untuk filter bulan
        if "TGL_CK-2" in df.columns:
            df["TGL_CK-2_DT"] = pd.to_datetime(df["TGL_CK-2"], errors="coerce")
            df["BULAN_NUM"] = df["TGL_CK-2_DT"].dt.month
        else:
            df["BULAN_NUM"] = None
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Drive: {e}")
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.warning("⚠️ Data belum dapat dimuat. Pastikan file Google Drive berstatus Viewer publik.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR FILTER INTERAKTIF
# ==============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Logo_Bea_Cukai.png/300px-Logo_Bea_Cukai.png", width=105)
    st.title("Panel Filter")
    st.markdown("Monitoring PBCK-3 KPPBC TMC Malang")
    st.markdown("---")
    
    # Filter Perusahaan
    daftar_pabrik = ["SEMUA PABRIK (SEMUA PENGAJUAN)"] + sorted(df_raw["PERUSAHAAN"].dropna().unique().tolist())
    pabrik_terpilih = st.selectbox("🏭 Pilih Perusahaan / Pabrik:", daftar_pabrik)
    
    # Filter Periode CK-2
    opsi_bulan = [
        "SEMUA BULAN (TOTAL TAHUNAN)",
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
        "s.d. Januari", "s.d. Februari", "s.d. Maret", "s.d. April", "s.d. Mei", "s.d. Juni",
        "s.d. Juli", "s.d. Agustus", "s.d. September", "s.d. Oktober", "s.d. November", "s.d. Desember"
    ]
    bulan_terpilih = st.selectbox("📅 Pilih Periode Terbit CK-2:", opsi_bulan)
    
    nama_bulan_dict = {
        "Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6,
        "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    
    # Tombol Refresh Cache Manual
    if st.button("🔄 Refresh Data Real-Time"):
        st.cache_data.clear()
        st.rerun()

# ==============================================================================
# 4. LOGIKA PEMFILTERAN DATA
# ==============================================================================
df_filtered = df_raw.copy()

# Filter Pabrik
if pabrik_terpilih != "SEMUA PABRIK (SEMUA PENGAJUAN)":
    df_filtered = df_filtered[df_filtered["PERUSAHAAN"] == pabrik_terpilih]

# Filter Periode Bulan
if bulan_terpilih != "SEMUA BULAN (TOTAL TAHUNAN)":
    if bulan_terpilih.startswith("s.d. "):
        target_nama = bulan_terpilih.replace("s.d. ", "")
        target_num = nama_bulan_dict.get(target_nama, 12)
        df_filtered = df_filtered[df_filtered["BULAN_NUM"] <= target_num]
    else:
        target_num = nama_bulan_dict.get(bulan_terpilih, 0)
        df_filtered = df_filtered[df_filtered["BULAN_NUM"] == target_num]

# ==============================================================================
# 5. HEADER UTAMA
# ==============================================================================
st.markdown("## 🏛️ EXECUTIVE DASHBOARD PENGAWASAN PBCK-3")
st.markdown("**Wilayah Pengawasan:** KPPBC Tipe Madya Cukai Malang &nbsp;|&nbsp; **Tahun Anggaran:** 2026")

if pabrik_terpilih != "SEMUA PABRIK (SEMUA PENGAJUAN)":
    npp = df_filtered["NPPBKC 10 DIGIT"].iloc[0] if "NPPBKC 10 DIGIT" in df_filtered.columns else "-"
    alamat = df_filtered["ALAMAT"].iloc[0] if "ALAMAT" in df_filtered.columns else "-"
    st.info(f"🏢 **{pabrik_terpilih}** &nbsp;|&nbsp; **NPPBKC:** `{npp}` &nbsp;|&nbsp; **Alamat:** {alamat}")
else:
    st.caption(f"Menampilkan seluruh pengajuan pabrik di wilayah pengawasan. Periode: **{bulan_terpilih}**")

# ==============================================================================
# 6. KARTU METRIK KPI UTAMA (PBCK-3 vs REALISASI CK-2)
# ==============================================================================
total_pengajuan = len(df_filtered)
total_cukai_pbck3 = df_filtered["TOTAL_CUKAI"].sum()
total_cukai_ck2 = df_filtered["CUKAI_MS"].sum()
selisih_tms = total_cukai_pbck3 - total_cukai_ck2
total_bp = df_filtered["JUMLAH_BP"].sum()
total_bungkus_ms = df_filtered["TOTAL_BUNGKUS_MS"].sum()

# Baris Metrik Utama
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #334155 0%, #1E293B 100%);">
            <div class="metric-label">Total Berkas</div>
            <div class="metric-value">{total_pengajuan:,} Berkas</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #1E3989 0%, #172554 100%);">
            <div class="metric-label">Nilai Pengajuan (PBCK-3)</div>
            <div class="metric-value">Rp {total_cukai_pbck3:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #059669 0%, #064E3B 100%);">
            <div class="metric-label">Nilai Realisasi (CK-2 / MS)</div>
            <div class="metric-value">Rp {total_cukai_ck2:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #D97706 0%, #78350F 100%);">
            <div class="metric-label">Biaya Pengganti (BP)</div>
            <div class="metric-value">Rp {total_bp:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4F46E5 0%, #312E81 100%);">
            <div class="metric-label">Total Bungkus MS</div>
            <div class="metric-value">{total_bungkus_ms:,.0f} Bks</div>
        </div>
    """, unsafe_allow_html=True)

# Notifikasi Khusus Jika Ada Selisih Fisik / Tidak Memenuhi Syarat
if selisih_tms > 0:
    st.warning(f"⚠️ **Terdapat Selisih Fisik / Tidak Memenuhi Syarat (TMS):** Sebesar **Rp {selisih_tms:,.0f}** (Pengajuan PBCK-3: Rp {total_cukai_pbck3:,.0f} | Realisasi CK-2: Rp {total_cukai_ck2:,.0f})")

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 7. TAB KONTEN INTERAKTIF
# ==============================================================================
tab_visual, tab_tabel, tab_alert = st.tabs([
    "📈 Analisis Visual & Grafik", 
    "📑 Daftar Riwayat Dokumen", 
    "🚨 Monitoring Jatuh Tempo CK-2"
])

# ------------------------------------------------------------------------------
# TAB 1: VISUALISASI GRAFIK
# ------------------------------------------------------------------------------
with tab_visual:
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🍩 Skema Pelaksanaan (PER-2/BC/2026)")
        if "SKEMA_PELAKSANAAN" in df_filtered.columns and not df_filtered["SKEMA_PELAKSANAAN"].dropna().empty:
            df_skema = df_filtered["SKEMA_PELAKSANAAN"].value_counts().reset_index()
            df_skema.columns = ["Skema", "Jumlah"]
            fig_skema = px.pie(
                df_skema, names="Skema", values="Jumlah", hole=0.45,
                color_discrete_sequence=["#1E3989", "#D97706", "#059669", "#DC2626"]
            )
            fig_skema.update_traces(textposition='inside', textinfo='percent+label')
            fig_skema.update_layout(margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_skema, use_container_width=True)
        else:
            st.info("Data skema pelaksanaan belum tersedia.")

    with g2:
        st.subheader("📦 Realisasi Nilai Cukai Berdasarkan Asal BKC")
        if "ASAL" in df_filtered.columns and not df_filtered["ASAL"].dropna().empty:
            df_asal = df_filtered.groupby("ASAL")["CUKAI_MS"].sum().reset_index()
            fig_asal = px.bar(
                df_asal, x="ASAL", y="CUKAI_MS", text_auto=".2s",
                color="ASAL", color_discrete_sequence=["#0D9488", "#3B82F6", "#F59E0B"]
            )
            fig_asal.update_layout(
                yaxis_title="Nilai Cukai CK-2 (Rp)", xaxis_title="",
                margin=dict(t=20, b=20, l=10, r=10), showlegend=False
            )
            st.plotly_chart(fig_asal, use_container_width=True)
        else:
            st.info("Data asal BKC belum tersedia.")

    # Top Perusahaan Berdasarkan Nilai Cukai Realisasi CK-2
    if pabrik_terpilih == "SEMUA PABRIK (SEMUA PENGAJUAN)":
        st.subheader("🏆 Top 7 Perusahaan Berdasarkan Nilai Realisasi CK-2")
        top_pabrik = df_filtered.groupby("PERUSAHAAN")["CUKAI_MS"].sum().reset_index()
        top_pabrik = top_pabrik.sort_values(by="CUKAI_MS", ascending=True).tail(7)
        fig_top = px.bar(
            top_pabrik, x="CUKAI_MS", y="PERUSAHAAN", orientation="h",
            color="CUKAI_MS", color_continuous_scale="Blues", text_auto=".3s"
        )
        fig_top.update_layout(xaxis_title="Nilai Cukai Realisasi (Rp)", yaxis_title="", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_top, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: TABEL RIWAYAT DOKUMEN & PENCARIAN
# ------------------------------------------------------------------------------
with tab_tabel:
    st.subheader("📋 Daftar Riwayat Pemeriksaan & Nilai Cukai")
    search_keyword = st.text_input("🔍 Cari nomor agenda, nomor surat, atau nama pabrik:", "")
    
    # Kolom lengkap: Menampilkan Nilai Pengajuan dan Nilai Realisasi CK-2 berdampingan
    kolom_tampil = [
        "AGENDA", "PERUSAHAAN", "NO_PBCK-3", "TANGGAL_PBCK-3", 
        "SKEMA_PELAKSANAAN", "TOTAL_BUNGKUS_MS", 
        "TOTAL_CUKAI",  # Nilai Pengajuan PBCK-3
        "CUKAI_MS",     # Nilai Realisasi CK-2
        "JUMLAH_BP", "BACK-3", "NO_CK-2", "PETUGAS_1", "PETUGAS 2"
    ]
    kolom_ada = [c for c in kolom_tampil if c in df_filtered.columns]
    df_tabel = df_filtered[kolom_ada].copy()
    
    if search_keyword:
        mask = df_tabel.astype(str).apply(lambda row: row.str.contains(search_keyword, case=False).any(), axis=1)
        df_tabel = df_tabel[mask]

    st.dataframe(
        df_tabel.style.format({
            "TOTAL_CUKAI": "Rp {:,.0f}",
            "CUKAI_MS": "Rp {:,.0f}",
            "JUMLAH_BP": "Rp {:,.0f}",
            "TOTAL_BUNGKUS_MS": "{:,.0f}"
        }),
        use_container_width=True,
        height=450
    )
    
    csv_data = df_tabel.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data Riwayat (CSV)",
        data=csv_data,
        file_name="riwayat_pbck3_ck2.csv",
        mime="text/csv"
    )

# ------------------------------------------------------------------------------
# TAB 3: MONITORING JATUH TEMPO CK-2 (10 HARI KERJA)
# ------------------------------------------------------------------------------
with tab_alert:
    st.subheader("🚨 Status Jatuh Tempo Penerbitan CK-2")
    st.caption("Batas maksimal penerbitan CK-2 adalah 10 hari kerja setelah tanggal Berita Acara (BACK-3) diterbitkan (Pasal 7 PER-2/BC/2026).")
    
    kolom_jt = ["AGENDA", "PERUSAHAAN", "TANGGAL_BACK-3", "BATAS MAKSIMAL CK-2", "JATUH TEMPO BERAPA HARI LAGI", "NO_CK-2"]
    kolom_jt_ada = [c for c in kolom_jt if c in df_filtered.columns]
    
    if kolom_jt_ada:
        df_jt = df_filtered[kolom_jt_ada].copy()
        belum_ck2 = df_jt[df_jt["NO_CK-2"].isna() | (df_jt["NO_CK-2"] == "") | (df_jt["NO_CK-2"] == "-")]
        sudah_ck2 = df_jt[~(df_jt["NO_CK-2"].isna() | (df_jt["NO_CK-2"] == "") | (df_jt["NO_CK-2"] == "-"))]
        
        col_jt1, col_jt2 = st.columns(2)
        with col_jt1:
            st.metric("Berkas Menunggu CK-2", f"{len(belum_ck2)} Berkas")
        with col_jt2:
            st.metric("Berkas Selesai CK-2", f"{len(sudah_ck2)} Berkas")
            
        st.markdown("#### ⏳ Berkas yang Sedang Berjalan:")
        if not belum_ck2.empty:
            st.dataframe(belum_ck2, use_container_width=True)
        else:
            st.success("✅ Seluruh berkas pada filter ini telah selesai terbit CK-2!")
    else:
        st.info("Kolom jatuh tempo tidak ditemukan pada database.")
