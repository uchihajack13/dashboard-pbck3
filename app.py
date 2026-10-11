import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Monitoring PBCK-3",
    page_icon="📊",
    layout="wide"
)

# Kustomisasi Warna Header Bea Cukai (Deep Navy)
st.markdown("""
    <style>
    .main-title {
        font-size: 26px;
        font-weight: bold;
        color: #1E3989;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 14px;
        color: #555;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">MONITORING PENGAWASAN PBCK-3 & PENGEMBALIAN CUKAI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">KPPBC TMC MALANG — TAHUN ANGGARAN 2026</div>', unsafe_allow_html=True)

# 2. Fungsi Mengambil Data Excel dari Google Drive
FILE_ID = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok" 
URL_DOWNLOAD = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

@st.cache_data(ttl=60) # Refresh data otomatis tiap 60 detik jika ada perubahan di Excel
def load_data():
    try:
        df = pd.read_excel(URL_DOWNLOAD, sheet_name="DATABASE MERGE")
        if "TGL_CK-2" in df.columns:
            df["TGL_CK-2"] = pd.to_datetime(df["TGL_CK-2"], errors="coerce")
            df["BULAN_NUM"] = df["TGL_CK-2"].dt.month
        return df
    except Exception as e:
        st.error(f"Gagal membaca file Excel dari Google Drive: {e}")
        return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.warning("Menunggu data dimuat atau periksa izin akses file Google Drive.")
    st.stop()

# 3. Sidebar Filter (Pabrik & Periode Bulan)
st.sidebar.header("🔍 Filter Dashboard")

# Filter Perusahaan
daftar_pabrik = ["SEMUA PABRIK (SEMUA PENGAJUAN)"] + sorted(df_raw["PERUSAHAAN"].dropna().unique().tolist())
pabrik_terpilih = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", daftar_pabrik)

# Filter Periode Bulan
opsi_bulan = [
    "SEMUA BULAN (TOTAL TAHUNAN)",
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    "s.d. Januari", "s.d. Februari", "s.d. Maret", "s.d. April", "s.d. Mei", "s.d. Juni",
    "s.d. Juli", "s.d. Agustus", "s.d. September", "s.d. Oktober", "s.d. November", "s.d. Desember"
]
bulan_terpilih = st.sidebar.selectbox("Pilih Periode CK-2:", opsi_bulan)

nama_bulan_dict = {
    "Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6,
    "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12
}

# 4. Logika Pemfilteran Data
df_filtered = df_raw.copy()

if pabrik_terpilih != "SEMUA PABRIK (SEMUA PENGAJUAN)":
    df_filtered = df_filtered[df_filtered["PERUSAHAAN"] == pabrik_terpilih]

if bulan_terpilih != "SEMUA BULAN (TOTAL TAHUNAN)":
    if bulan_terpilih.startswith("s.d. "):
        target_nama = bulan_terpilih.replace("s.d. ", "")
        target_num = nama_bulan_dict.get(target_nama, 12)
        df_filtered = df_filtered[df_filtered["BULAN_NUM"] <= target_num]
    else:
        target_num = nama_bulan_dict.get(bulan_terpilih, 0)
        df_filtered = df_filtered[df_filtered["BULAN_NUM"] == target_num]

# 5. Menampilkan Kartu KPI Utama
total_pengajuan = len(df_filtered)
total_cukai_ms = df_filtered["CUKAI_MS "].sum() if "CUKAI_MS " in df_filtered.columns else 0
total_bp = df_filtered[" JUMLAH_BP "].sum() if " JUMLAH_BP " in df_filtered.columns else 0
total_bungkus = df_filtered[" TOTAL_BUNGKUS_MS "].sum() if " TOTAL_BUNGKUS_MS " in df_filtered.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pengajuan", f"{total_pengajuan:,} Berkas")
col2.metric("Total Cukai MS", f"Rp {total_cukai_ms:,.0f}")
col3.metric("Total Biaya Pengganti", f"Rp {total_bp:,.0f}")
col4.metric("Total Bungkus MS", f"{total_bungkus:,.0f} Bks")

st.markdown("---")

# 6. Menampilkan Grafik & Rincian Matriks
col_grafik1, col_grafik2 = st.columns(2)

with col_grafik1:
    st.subheader("📌 Rincian Cara Penyelesaian")
    if "SKEMA_PELAKSANAAN" in df_filtered.columns:
        df_skema = df_filtered["SKEMA_PELAKSANAAN"].value_counts().reset_index()
        df_skema.columns = ["Skema", "Jumlah"]
        fig1 = px.pie(df_skema, names="Skema", values="Jumlah", hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig1, use_container_width=True)

with col_grafik2:
    st.subheader("🏭 Rincian Asal BKC")
    if "ASAL" in df_filtered.columns:
        df_asal = df_filtered["ASAL"].value_counts().reset_index()
        df_asal.columns = ["Asal BKC", "Jumlah"]
        fig2 = px.bar(df_asal, x="Asal BKC", y="Jumlah", color="Asal BKC", text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

# 7. Menampilkan Tabel Riwayat Pengawasan
st.subheader("📋 Riwayat Pengajuan & Dokumen")
kolom_tampil = ["AGENDA", "PERUSAHAAN", "NO_PBCK-3", "TANGGAL_PBCK-3", "SKEMA_PELAKSANAAN", "CUKAI_MS ", "BACK-3", "NO_CK-2", "PETUGAS_1", "PETUGAS 2"]
kolom_ada = [c for c in kolom_tampil if c in df_filtered.columns]

st.dataframe(
    df_filtered[kolom_ada].reset_index(drop=True),
    use_container_width=True
)
