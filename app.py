import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# ==============================================================================
# 1. KONFIGURASI HALAMAN
# ==============================================================================
st.set_page_config(
    page_title="Dashboard PBCK-3 | KPPBC TMC Malang",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling CSS (Modern Executive Theme)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E3989 0%, #0F2042 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #CBD5E1;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #F8FAFC;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3989 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. PENGAMBILAN & PEMBERSIHAN DATA DARI GOOGLE DRIVE
# ==============================================================================
FILE_ID = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
URL_DOWNLOAD = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_excel(URL_DOWNLOAD, sheet_name="DATABASE MERGE")
        
        # 1. Bersihkan spasi tak terlihat di semua nama kolom
        df.columns = df.columns.str.strip()
        
        # 2. Konversi kolom numerik penting secara aman (buang string/karakter non-angka)
        numeric_cols = ["CUKAI_MS", "TOTAL_CUKAI", "JUMLAH_BP", "TOTAL_BUNGKUS_MS", "TOTAL_BUNGKUS"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace("Rp", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(),
                    errors="coerce"
                ).fillna(0)
        
        # 3. Format Tanggal
        if "TGL_CK-2" in df.columns:
            df["TGL_CK-2_DT"] = pd.to_datetime(df["TGL_CK-2"], errors="coerce")
            df["BULAN_NUM"] = df["TGL_CK-2_DT"].dt.month
        else:
            df["BULAN_NUM"] = None
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari cloud: {e}")
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.warning("⚠️ Tidak ada data yang dapat ditampilkan. Pastikan link Google Drive sudah diatur ke 'Anyone with the link can view'.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR FILTER INTERAKTIF
# ==============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Logo_Bea_Cukai.png/300px-Logo_Bea_Cukai.png", width=110)
    st.title("Panel Kontrol")
    st.markdown("Filter pengawasan pengembalian cukai KPPBC TMC Malang.")
    st.markdown("---")
    
    # Filter Pabrik
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
    
    # Tombol Refresh Cache Data
    if st.button("🔄 Refresh Data Cloud"):
        st.cache_data.clear()
        st.rerun()

# ==============================================================================
# 4. LOGIKA FILTERING DATA
# ==============================================================================
df_filtered = df_raw.copy()

# Filter Nama Pabrik
if pabrik_terpilih != "SEMUA PABRIK (SEMUA PENGAJUAN)":
    df_filtered = df_filtered[df_filtered["PERUSAHAAN"] == pabrik_terpilih]

# Filter Bulan
if bulan_terpilih != "SEMUA BULAN (TOTAL TAHUNAN)":
    if bulan_terpilih.startswith("s.d. "):
        target_nama = bulan_terpilih.replace("s.d. ", "")
        target_num = nama_bulan_dict.get(target_nama, 12)
        df_filtered = df_filtered[df_filtered["BULAN_NUM"] <= target_num]
    else:
        target_num = nama_bulan_dict.get(bulan_terpilih, 0)
        df_filtered = df_filtered[df_filtered["BULAN_NUM"] == target_num]

# ==============================================================================
# 5. HEADER UTAMA & PROFIL
# ==============================================================================
st.markdown("## 📊 EXECUTIVE DASHBOARD PENGAWASAN PBCK-3")
st.markdown(f"**Wilayah Pengawasan:** KPPBC Tipe Madya Cukai Malang | **Tahun Anggaran:** 2026")

if pabrik_terpilih != "SEMUA PABRIK (SEMUA PENGAJUAN)":
    npp = df_filtered["NPPBKC 10 DIGIT"].iloc[0] if "NPPBKC 10 DIGIT" in df_filtered.columns else "-"
    alamat = df_filtered["ALAMAT"].iloc[0] if "ALAMAT" in df_filtered.columns else "-"
    st.info(f"🏢 **{pabrik_terpilih}** | **NPPBKC:** `{npp}` | **Alamat:** {alamat}")
else:
    st.caption(f"Menampilkan agregasi total seluruh pengajuan pabrik di wilayah pengawasan. Periode: **{bulan_terpilih}**")

# ==============================================================================
# 6. KARTU METRIK KPI UTAMA
# ==============================================================================
total_pengajuan = len(df_filtered)
total_cukai_ms = df_filtered["CUKAI_MS"].sum() if "CUKAI_MS" in df_filtered.columns else 0
total_bp = df_filtered["JUMLAH_BP"].sum() if "JUMLAH_BP" in df_filtered.columns else 0
total_bungkus_ms = df_filtered["TOTAL_BUNGKUS_MS"].sum() if "TOTAL_BUNGKUS_MS" in df_filtered.columns else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Pengajuan PBCK-3</div>
            <div class="metric-value">{total_pengajuan:,} Berkas</div>
        </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Nilai Cukai MS</div>
            <div class="metric-value">Rp {total_cukai_ms:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Biaya Pengganti (BP)</div>
            <div class="metric-value">Rp {total_bp:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Kemasan / Bungkus MS</div>
            <div class="metric-value">{total_bungkus_ms:,.0f} Bks</div>
        </div>
    """, unsafe_allow_html=True)

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
# TAB 1: VISUALISASI
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
                color_discrete_sequence=["#1E3989", "#D97706", "#2563EB", "#DC2626"]
            )
            fig_skema.update_traces(textposition='inside', textinfo='percent+label')
            fig_skema.update_layout(margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_skema, use_container_width=True)
        else:
            st.info("Data skema pelaksanaan belum tersedia.")

    with g2:
        st.subheader("📦 Kategori Asal BKC")
        if "ASAL" in df_filtered.columns and not df_filtered["ASAL"].dropna().empty:
            df_asal = df_filtered.groupby("ASAL")["CUKAI_MS"].sum().reset_index()
            fig_asal = px.bar(
                df_asal, x="ASAL", y="CUKAI_MS", text_auto=".2s",
                color="ASAL", color_discrete_sequence=["#0D9488", "#3B82F6", "#F59E0B"]
            )
            fig_asal.update_layout(
                yaxis_title="Nilai Cukai MS (Rp)", xaxis_title="",
                margin=dict(t=20, b=20, l=10, r=10), showlegend=False
            )
            st.plotly_chart(fig_asal, use_container_width=True)
        else:
            st.info("Data kategori asal belum tersedia.")

    # Top 5 Pabrik dengan Pengembalian Cukai Terbesar
    if pabrik_terpilih == "SEMUA PABRIK (SEMUA PENGAJUAN)":
        st.subheader("🏆 Top 7 Perusahaan Berdasarkan Nilai Cukai MS")
        top_pabrik = df_filtered.groupby("PERUSAHAAN")["CUKAI_MS"].sum().reset_index()
        top_pabrik = top_pabrik.sort_values(by="CUKAI_MS", ascending=True).tail(7)
        fig_top = px.bar(
            top_pabrik, x="CUKAI_MS", y="PERUSAHAAN", orientation="h",
            color="CUKAI_MS", color_continuous_scale="Blues", text_auto=".3s"
        )
        fig_top.update_layout(xaxis_title="Nilai Cukai (Rp)", yaxis_title="", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_top, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: TABEL RIWAYAT DOKUMEN & SEARCH
# ------------------------------------------------------------------------------
with tab_tabel:
    st.subheader("Daftar Riwayat Pemeriksaan & Pengembalian Cukai")
    
    # Kolom Pencarian Cepat
    search_keyword = st.text_input("🔍 Cari nomor agenda, nomor surat, atau kata kunci lain:", "")
    
    kolom_tampil = [
        "AGENDA", "PERUSAHAAN", "NO_PBCK-3", "TANGGAL_PBCK-3", 
        "SKEMA_PELAKSANAAN", "TOTAL_BUNGKUS_MS", "CUKAI_MS", "JUMLAH_BP", 
        "BACK-3", "NO_CK-2", "PETUGAS_1", "PETUGAS 2"
    ]
    kolom_ada = [c for c in kolom_tampil if c in df_filtered.columns]
    df_tabel = df_filtered[kolom_ada].copy()
    
    if search_keyword:
        mask = df_tabel.astype(str).apply(lambda row: row.str.contains(search_keyword, case=False).any(), axis=1)
        df_tabel = df_tabel[mask]

    # Format Tampilan Mata Uang & Angka pada Dataframe
    st.dataframe(
        df_tabel.style.format({
            "CUKAI_MS": "Rp {:,.0f}",
            "JUMLAH_BP": "Rp {:,.0f}",
            "TOTAL_BUNGKUS_MS": "{:,.0f}"
        }),
        use_container_width=True,
        height=450
    )
    
    # Tombol Download Data Filter
    csv_data = df_tabel.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data Ini ke File CSV",
        data=csv_data,
        file_name="rekap_pbck3_filtered.csv",
        mime="text/csv"
    )

# ------------------------------------------------------------------------------
# TAB 3: MONITORING JATUH TEMPO (10 HARI KERJA)
# ------------------------------------------------------------------------------
with tab_alert:
    st.subheader("🚨 Status Jatuh Tempo Penerbitan CK-2")
    st.caption("Batas maksimal penerbitan CK-2 adalah 10 hari kerja setelah tanggal Berita Acara (BACK-3) diterbitkan (Pasal 7 PER-2/BC/2026).")
    
    kolom_jt = ["AGENDA", "PERUSAHAAN", "TANGGAL_BACK-3", "BATAS MAKSIMAL CK-2", "JATUH TEMPO BERAPA HARI LAGI", "NO_CK-2"]
    kolom_jt_ada = [c for c in kolom_jt if c in df_filtered.columns]
    
    if kolom_jt_ada:
        df_jt = df_filtered[kolom_jt_ada].copy()
        
        # Pisahkan berkas yang belum terbit CK-2
        belum_ck2 = df_jt[df_jt["NO_CK-2"].isna() | (df_jt["NO_CK-2"] == "") | (df_jt["NO_CK-2"] == "-")]
        sudah_ck2 = df_jt[~(df_jt["NO_CK-2"].isna() | (df_jt["NO_CK-2"] == "") | (df_jt["NO_CK-2"] == "-"))]
        
        col_jt1, col_jt2 = st.columns([1, 1])
        with col_jt1:
            st.metric("Berkas Belum Terbit CK-2", f"{len(belum_ck2)} Berkas")
        with col_jt2:
            st.metric("Berkas Selesai CK-2", f"{len(sudah_ck2)} Berkas")
            
        st.markdown("#### ⏳ Berkas yang Sedang Berjalan / Menunggu CK-2:")
        if not belum_ck2.empty:
            st.dataframe(belum_ck2, use_container_width=True)
        else:
            st.success("✅ Semua dokumen pada filter ini telah selesai terbit CK-2!")
    else:
        st.info("Kolom jatuh tempo tidak ditemukan pada database.")
