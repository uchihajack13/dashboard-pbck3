import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. KONFIGURASI HALAMAN & TEMA
st.set_page_config(
    page_title="Dashboard Eksekutif PBCK-3 KPPBC TMC Malang",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk warna instansi (Navy Blue, Gold, Clean Card)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    div[data-testid="metric-container"] label {
        color: #1e3a8a !important; /* Navy */
        font-weight: 800;
        font-size: 1.1rem;
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .custom-title { font-family: 'Montserrat', sans-serif; font-weight: 800; margin: 0; font-size: 32px;}
    .custom-subtitle { font-size: 16px; opacity: 0.85; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# 2. LOGO DAN HEADER
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"
st.markdown(f"""
    <div class="main-header">
        <img src="{LOGO_URL}" width="100">
        <div>
            <h1 class="custom-title">DASHBOARD EKSEKUTIF PBCK-3</h1>
            <p class="custom-subtitle">Pengawasan Pengembalian Cukai (Olah Kembali & Pemusnahan) — KPPBC TMC Malang</p>
            <p style="font-size: 12px; opacity: 0.6; margin-top: 5px;">Terintegrasi dengan PMK 113/2025 & PER-2/BC/2026</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# 3. KONEKSI & LOAD DATA
@st.cache_data(ttl=600)
def load_data():
    # ID Drive file database utama lu
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url_merge, sheet_name="DATABASE MERGE")
    
    # Standardisasi Nama Kolom untuk menghindari error spasi gaib
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ Gagal memuat data dari Cloud. Pastikan sinkronisasi Desktop ke Web berjalan lancar. Error: {e}")
    st.stop()

# Bersihkan data: Hapus baris yang kosong semua di kolom krusial
df = df.dropna(subset=['PERUSAHAAN', 'NO_PBCK-3'], how='all')

# 4. FILTER SIDEBAR EKSEKUTIF
st.sidebar.markdown("### 🎛️ Filter Dasbor")
pabrik_list = ["Semua Pabrik"] + sorted(df['PERUSAHAAN'].dropna().unique().tolist())
selected_pabrik = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", pabrik_list)

df_filtered = df.copy()
if selected_pabrik != "Semua Pabrik":
    df_filtered = df_filtered[df_filtered['PERUSAHAAN'] == selected_pabrik]

# 5. METRIK UTAMA (DOUBLE COUNTER)
# A. Jumlah PBCK-3 (Dokumen Masuk)
total_pbck3 = df_filtered['NO_PBCK-3'].nunique()

# B. Jumlah CK-2 yang telah terbit (Memiliki Nomor CK-2 yang valid)
if 'NO_CK-2' in df_filtered.columns:
    # Filter yang bukan NaN dan bukan string kosong/strip
    ck2_terbit_df = df_filtered[df_filtered['NO_CK-2'].notna() & (df_filtered['NO_CK-2'] != "") & (df_filtered['NO_CK-2'] != "-")]
    total_ck2 = ck2_terbit_df['NO_CK-2'].nunique()
else:
    total_ck2 = 0

# C. Sisa Pekerjaan (Outstanding)
total_proses = total_pbck3 - total_ck2

# D. Finansial (Cukai & BP)
nilai_cukai = pd.to_numeric(df_filtered['TOTAL_CUKAI'], errors='coerce').sum()
biaya_pengganti = pd.to_numeric(df_filtered['JUMLAH_BP'], errors='coerce').sum()

# TAMPILKAN METRIK KINERJA
st.subheader("📊 Kinerja Penyelesaian Kertas Kerja")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📥 Total Masuk (PBCK-3)", value=f"{total_pbck3} Dokumen")
with col2:
    st.metric(label="✅ Selesai Terbit (CK-2)", value=f"{total_ck2} Dokumen", delta=f"{total_ck2/total_pbck3*100:.1f}% Tuntas" if total_pbck3 > 0 else "0%")
with col3:
    st.metric(label="⏳ Outstanding (Dalam Proses)", value=f"{total_proses} Dokumen", delta=f"Tanggungan Seksi", delta_color="inverse")

# TAMPILKAN METRIK FINANSIAL
st.subheader("💰 Rekapitulasi Finansial")
col_fin1, col_fin2 = st.columns(2)
with col_fin1:
    st.metric(label="💸 Total Pengembalian Cukai (Hak Pabrik)", value=f"Rp {nilai_cukai:,.0f}")
with col_fin2:
    st.metric(label="🏦 Total Biaya Pengganti (Penerimaan Negara)", value=f"Rp {biaya_pengganti:,.0f}")

st.markdown("---")

# 6. WARNING SLA (CRITICAL BUAT PIMPINAN)
st.subheader("🚨 Warning Kepatuhan SLA (Maks 10 Hari Kerja CK-2)")
if 'JATUH TEMPO BERAPA HARI LAGI' in df_filtered.columns:
    # Mengambil dokumen yang belum terbit CK-2
    df_outstanding = df_filtered[df_filtered['NO_CK-2'].isna() | (df_filtered['NO_CK-2'] == "") | (df_filtered['NO_CK-2'] == "-")].copy()
    
    if not df_outstanding.empty:
        # Konversi sisa hari ke numerik
        df_outstanding['SISA_HARI'] = pd.to_numeric(df_outstanding['JATUH TEMPO BERAPA HARI LAGI'], errors='coerce')
        
        # Kategorisasi SLA
        df_overdue = df_outstanding[df_outstanding['SISA_HARI'] < 0]
        df_warning = df_outstanding[(df_outstanding['SISA_HARI'] >= 0) & (df_outstanding['SISA_HARI'] <= 3)]
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            if not df_overdue.empty:
                st.error(f"🔴 **OVERDUE! Ada {len(df_overdue)} Dokumen Melebihi Batas Waktu.** Berpotensi temuan BPK/Itjen.")
                st.dataframe(df_overdue[['PERUSAHAAN', 'NO_PBCK-3', 'BACK-3', 'BATAS MAKSIMAL CK-2']], hide_index=True)
            else:
                st.success("🟢 Aman! Tidak ada dokumen Overdue.")
                
        with col_w2:
            if not df_warning.empty:
                st.warning(f"🟡 **ATENSI SEGERA! Ada {len(df_warning)} Dokumen jatuh tempo dalam ≤ 3 hari.**")
                st.dataframe(df_warning[['PERUSAHAAN', 'NO_PBCK-3', 'SISA_HARI']], hide_index=True)
            else:
                st.info("🔵 Belum ada dokumen yang mendekati masa kritis (≤ 3 Hari).")
    else:
        st.success("🎉 Luar biasa! Semua dokumen CK-2 untuk filter ini sudah selesai diterbitkan.")

# 7. TABEL DATABASE UTAMA
st.markdown("---")
st.subheader("📑 Rincian Dokumen & Transaksi")
cols_to_show = ['PERUSAHAAN', 'NO_PBCK-3', 'TANGGAL_PBCK-3', 'BACK-3', 'TANGGAL_BACK-3', 'NO_CK-2', 'TGL_CK-2', 'TOTAL_CUKAI']
available_cols = [c for c in cols_to_show if c in df_filtered.columns]
st.dataframe(df_filtered[available_cols], use_container_width=True, hide_index=True)
