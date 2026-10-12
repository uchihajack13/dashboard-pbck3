import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. KONFIGURASI HALAMAN & TEMA EKSEKUTIF
st.set_page_config(
    page_title="Dashboard PBCK-3 KPPBC TMC Malang",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS warna instansi (Navy Blue, Gold, and Clean Card Style)
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
        font-weight: bold;
        font-size: 13px !important;
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .custom-title { font-family: 'Montserrat', sans-serif; font-weight: 800; margin: 0; font-size: 28px; }
    .custom-subtitle { font-size: 13px; opacity: 0.8; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# 2. HEADER & LOGO RESMI KPPBC
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"

col_logo, col_header = st.columns([1, 8])
with col_logo:
    st.image(LOGO_URL, width=80)
with col_header:
    st.markdown("""
        <div class="main-header">
            <h2 class="custom-title">📊 DASHBOARD PBCK-3 & REALISASI CUKAI</h2>
            <p class="custom-subtitle">Monitoring Pengolahan Kembali & Pemusnahan BKC — KPPBC TMC Malang</p>
            <p style="font-size: 11px; opacity: 0.6; margin-top: 5px;">Terintegrasi dengan PMK 113/2025 & PER-2/BC/2026</p>
        </div>
    """, unsafe_allow_html=True)

# 3. KONEKSI & LOAD DATA DARI CLOUD DRIVE
@st.cache_data(ttl=300)  # Cache 5 menit biar real-time dan hemat kuota
def load_data():
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url_merge, sheet_name="DATABASE MERGE")
    
    # ⚠️ Kunci Utama: Standardisasi Kolom (Huruf Besar & Tanpa Spasi)
    df.columns = df.columns.str.strip().str.upper()
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()
except Exception as e:
    st.error(f"⚠️ Gagal memuat data dari G-Drive, bro. Error: {e}")
    st.stop()

# 4. RESOLVING GHOST COLUMNS (MENCEGAH KEYERROR)
# Membantu menyamakan kolom-kolom kritis seumpama ada pergantian nama di Drive Desktop
col_pabrik = "PERUSAHAAN" if "PERUSAHAAN" in df.columns else ("PERUSAHAAN_KEP" if "PERUSAHAAN_KEP" in df.columns else df.columns[1])
col_pbck3 = "NO_PBCK-3" if "NO_PBCK-3" in df.columns else ("NO_PBCK_3" if "NO_PBCK_3" in df.columns else df.columns[0])
col_tgl_pbck3 = "TANGGAL_PBCK-3" if "TANGGAL_PBCK-3" in df.columns else "TANGGAL_PBCK3"
col_back3 = "BACK-3" if "BACK-3" in df.columns else df.columns[0]
col_tgl_back3 = "TANGGAL BACK-3" if "TANGGAL BACK-3" in df.columns else "TANGGAL_BACK-3"
col_ck2 = "NO_CK-2" if "NO_CK-2" in df.columns else "NO_CK2"
col_tgl_ck2 = "TGL_CK-2" if "TGL_CK-2" in df.columns else "TGL_CK_2"
col_potensi_cukai = "TOTAL_CUKAI" if "TOTAL_CUKAI" in df.columns else "TOTAL CUKAI"
col_biaya_pengganti = "JUMLAH_BP" if "JUMLAH_BP" in df.columns else "JUMLAH BP"

# Format Tanggal PBCK-3
if col_tgl_pbck3 in df.columns:
    df[col_tgl_pbck3] = pd.to_datetime(df[col_tgl_pbck3], errors='coerce')
if col_tgl_back3 in df.columns:
    df[col_tgl_back3] = pd.to_datetime(df[col_tgl_back3], errors='coerce')
if col_tgl_ck2 in df.columns:
    df[col_tgl_ck2] = pd.to_datetime(df[col_tgl_ck2], errors='coerce')

# Ekstrak Info Tahun & Bulan berdasarkan data TANGGAL_PBCK-3
df['TAHUN_PBCK'] = df[col_tgl_pbck3].dt.year.fillna(2026).astype(int)
df['BULAN_ANGKA'] = df[col_tgl_pbck3].dt.month.fillna(1).astype(int)

INDO_BULAN = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}
df['BULAN_NAMA'] = df['BULAN_ANGKA'].map(INDO_BULAN)

# 5. INTEGRASI FILTER PERIODE & PABRIK (DI SIDEBAR)
st.sidebar.markdown("### 🎛️ Filter Dasbor")

# Filter A: Perusahaan Pabrik
pabrik_list = ["Semua Pabrik"] + sorted(df[col_pabrik].dropna().unique().tolist())
selected_pabrik = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", pabrik_list)

# Filter B: Tahun
tahun_list = sorted(df['TAHUN_PBCK'].unique().tolist(), reverse=True)
selected_tahun = st.sidebar.selectbox("Pilih Tahun:", tahun_list)

# 🚀 FITUR MEWAH: FILTER PERIODE BULAN (Sesuai Kebutuhan Pimpinan)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗓️ Filter Periode Bulanan")
mode_periode = st.sidebar.radio(
    "Mode Periode:",
    ["Semua Periode", "Bulanan Tunggal (Single Month)", "Kumulatif (s.d. Bulan)"],
    help="Sangat penting untuk laporan audit, bisa melihat realisasi satu bulan tertentu atau perkembangan s.d. bulan berjalan!"
)

# Render Dropdown Bulan kalau user memilih metode bulan spesifik
selected_bulan_nama = "Januari"
selected_bulan_angka = 1
if mode_periode != "Semua Periode":
    # Pastikan list bulan berdasarkan kronologis, bukan abjad
    nama_bulan_list = [INDO_BULAN[i] for i in sorted(df[df['TAHUN_PBCK'] == selected_tahun]['BULAN_ANGKA'].unique())]
    if not nama_bulan_list:
        nama_bulan_list = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    
    selected_bulan_nama = st.sidebar.selectbox("Pilih Bulan Acuan:", nama_bulan_list)
    # Convert nama bulan terpilih ke angka (1-12)
    selected_bulan_angka = next(k for k, v in INDO_BULAN.items() if v == selected_bulan_nama)

# 6. PENGEKSEKUSIAN LOGIKA FILTER DATA
df_filtered = df.copy()

# Filter Perusahaan
if selected_pabrik != "Semua Pabrik":
    df_filtered = df_filtered[df_filtered[col_pabrik] == selected_pabrik]

# Filter Tahun
df_filtered = df_filtered[df_filtered['TAHUN_PBCK'] == selected_tahun]

# Filter Periode Bulan (Logika Tunggal vs Kumulatif)
if mode_periode == "Bulanan Tunggal (Single Month)":
    df_filtered = df_filtered[df_filtered['BULAN_ANGKA'] == selected_bulan_angka]
elif mode_periode == "Kumulatif (s.d. Bulan)":
    df_filtered = df_filtered[df_filtered['BULAN_ANGKA'] <= selected_bulan_angka]

# 7. PEMROSESAN ANGGOTA & METRIK EKSEKUTIF
total_pbck3 = df_filtered[col_pbck3].nunique() if col_pbck3 in df_filtered.columns else len(df_filtered)

# Jumlah CK-2 yang Telah Terbit (No CK-2 valid/tidak kosong)
if col_ck2 in df_filtered.columns:
    df_filtered['STATUS_CK2_BOOL'] = df_filtered[col_ck2].apply(
        lambda x: "TERBIT" if pd.notnull(x) and str(x).strip() != "" and str(x).strip().lower() != "nan" and str(x).strip() != "-" else "PROSES"
    )
    total_ck2 = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"][col_ck2].nunique()
else:
    df_filtered['STATUS_CK2_BOOL'] = "PROSES"
    total_ck2 = 0

# Outstanding Pekerjaan (Masuk tapi belum terbit CK-2)
total_outstanding = total_pbck3 - total_ck2

# Potensi Finansial (Sesuai PMK 113/2025)
nilai_cukai = pd.to_numeric(df_filtered[col_potensi_cukai], errors='coerce').sum() if col_potensi_cukai in df_filtered.columns else 0
biaya_pengganti = pd.to_numeric(df_filtered[col_biaya_pengganti], errors='coerce').sum() if col_biaya_pengganti in df_filtered.columns else 0

# Tampilkan Label Filter Aktif di Atas Dashboard
visual_periode_lbl = "Semua Periode Tahun " + str(selected_tahun)
if mode_periode == "Bulanan Tunggal (Single Month)":
    visual_periode_lbl = f"Bulan {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)":
    visual_periode_lbl = f"Januari s.d. {selected_bulan_nama} {selected_tahun}"

st.markdown(f"🚩 **Periode Terpantau saat ini:** `{visual_periode_lbl}`  |  🏢 **Perusahaan Pabrik:** `{selected_pabrik}`")

# 8. PANEL UTAMA TAMPILAN COUNTER / METRIKS
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="📥 TOTAL PBCK-3 (PERMOHONAN)",
        value=f"{total_pbck3} Berkas",
        help="Semua pengajuan permohonan pemusnahan / olah kembali."
    )
with col2:
    st.metric(
        label="📜 CK-2 SELESAI TERBIT",
        value=f"{total_ck2} Dokumen",
        delta=f"{total_ck2/total_pbck3*100:.1f}% dari permohonan" if total_pbck3 > 0 else "0%",
        delta_color="normal",
        help="Dokumen tanda perusakan pita cukai yang resmi rampung."
    )
with col3:
    st.metric(
        label="⏳ OUTSTANDING (BELUM SELESAI)",
        value=f"{total_outstanding} Dokumen",
        delta=f"{(total_outstanding/total_pbck3)*100:.1f}% Sisa Pekerjaan" if total_pbck3 > 0 else "0%",
        delta_color="inverse",
        help="Dokumen yang belum diterbitkan CK-2 nya."
    )

col_fin1, col_fin2 = st.columns(2)
with col_fin1:
    st.metric(label="💸 TOTAL PENGEMBALIAN CUKAI (PMK 113/2025)", value=f"Rp {nilai_cukai:,.0f}")
with col_fin2:
    st.metric(label="🏦 TOTAL BIAYA PENGGANTI (PENERIMAAN NEGARA)", value=f"Rp {biaya_pengganti:,.0f}")

st.markdown("---")

# 9. INTEGRASI DIAGRAM & ANALISIS TREN BULANAN (Visual Favorit Pimpinan)
col_chart1, col_chart2 = st.columns([6, 5])

with col_chart1:
    st.subheader("📈 Tren Kinerja Bulanan")
    st.caption("Visualisasi permohonan yang masuk (Inflow) dibanding CK-2 yang terbit (Outflow).")
    
    # Tren Kumulatif / Bulanan dari Tanggal Permohonan
    df_trend_monthly = df_filtered.groupby('BULAN_ANGKA').agg(
        PBCK3=(col_pbck3, 'count') if col_pbck3 in df_filtered.columns else ('BULAN_ANGKA', 'count'),
        CK2=('STATUS_CK2_BOOL', lambda x: (x == "TERBIT").sum())
    ).reset_index()
    
    # Map angka bulan ke nama bulan singkat
    df_trend_monthly['BULAN'] = df_trend_monthly['BULAN_ANGKA'].map(INDO_BULAN)
    
    fig_trend = go.Figure()
    # Bar Chart: PBCK-3 (Masuk)
    fig_trend.add_trace(go.Bar(
        x=df_trend_monthly['BULAN'], y=df_trend_monthly['PBCK3'],
        name='Dokumen PBCK-3 Masuk', marker_color='#1e3a8a', opacity=0.85
    ))
    # Line Chart: CK-2 (Terbit)
    fig_trend.add_trace(go.Scatter(
        x=df_trend_monthly['BULAN'], y=df_trend_monthly['CK2'],
        name='Dokumen CK-2 Terbit', marker_color='#fbbf24', mode='lines+markers',
        line=dict(width=4)
    ))
    
    fig_trend.update_layout(
        barmode='group',
        xaxis_title="Periode Bulan",
        yaxis_title="Volume Dokumen",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320,
        margin=dict(t=15, b=15, l=10, r=10)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_chart2:
    st.subheader("📊 Pembagian Kontribusi Nilai Cukai")
    st.caption("Visualisasi permohonan ter-filter per-perusahaan pabrik.")
    
    if col_pabrik in df_filtered.columns:
        df_pabrik_grp = df_filtered.groupby(col_pabrik)[col_potensi_cukai].sum().reset_index()
        df_pabrik_grp = df_pabrik_grp.sort_values(by=col_potensi_cukai, ascending=False).head(5)
        
        fig_pie = px.pie(
            df_pabrik_grp,
            names=col_pabrik,
            values=col_potensi_cukai,
            color_discrete_sequence=px.colors.sequential.Blues_r,
            hole=0.4
        )
        fig_pie.update_layout(height=320, margin=dict(t=15, b=15, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Visualisasi data Perusahaan Pabrik tidak memadai.")

st.markdown("---")

# 10. NOTIFIKASI SLA (MEGATRON / COMPLIANCE WARNING)
st.subheader("🚨 Warning Kepatuhan SLA (Maks 10 Hari Kerja s.d. CK-2)")
st.caption("Berdasarkan PER-2/BC/2026 Pasal 7, penerbitan CK-2 tidak boleh melebihi 10 hari kerja sejak Tanggal BACK-3 diterbitkan.")

col_warn1, col_warn2 = st.columns(2)

# Menggunakan kolom "JATUH TEMPO BERAPA HARI LAGI" dari database
col_tempo = "JATUH TEMPO BERAPA HARI LAGI" if "JATUH TEMPO BERAPA HARI LAGI" in df.columns else None

if col_tempo:
    # Memproses sisa waktu untuk permohonan yang masih dalam proses
    df_proses = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "PROSES"].copy()
    
    if not df_proses.empty:
        df_proses['SISA_HARI_INT'] = pd.to_numeric(df_proses[col_tempo], errors='coerce')
        
        # Saring Berkas yang Melebihi / Menjelang Jatuh Tempo
        overdue_items = df_proses[df_proses['SISA_HARI_INT'] < 0]
        critical_items = df_proses[(df_proses['SISA_HARI_INT'] >= 0) & (df_proses['SISA_HARI_INT'] <= 3)]
        
        with col_warn1:
            if not overdue_items.empty:
                st.error(f"🔴 **{len(overdue_items)} Berkas OVERDUE (Lewat Batas)!**")
                st.dataframe(overdue_items[[col_pabrik, col_pbck3, col_tgl_pbck3, col_tempo]], hide_index=True, use_container_width=True)
            else:
                st.success("🟢 Bebas Overdue! Semua berkas dalam seksi masih berada dalam batas waktu yang sah.")
                
        with col_warn2:
            if not critical_items.empty:
                st.warning(f"🟡 **{len(critical_items)} Berkas Jatuh Tempo H-3 atau Kurang!**")
                st.dataframe(critical_items[[col_pabrik, col_pbck3, col_tempo]], hide_index=True, use_container_width=True)
            else:
                st.info("🔵 Bagus! Belum ada berkas dalam proses yang mendekati masa kritis (≤ 3 Hari).")
    else:
        st.success("🎉 Hebat! Seluruh dokumen pemusnahan/pengolahan periode ini sudah selesai diproses (terbit CK-2).")
else:
    st.info("Data jatuh tempo (SLA) saat ini belum termuat secara dinamis dalam database.")

# 11. DETIL DATA TRANSAKSI
st.markdown("---")
st.subheader("📑 Detail Data Transaksi (Ter-filter)")

view_cols = [col_pabrik, col_pbck3, col_tgl_pbck3, col_back3, col_tgl_back3, col_ck2, col_tgl_ck2, col_potensi_cukai]
available_cols_to_show = [c for c in view_cols if c in df_filtered.columns]

st.dataframe(
    df_filtered[available_cols_to_show].sort_values(by=col_tgl_pbck3, ascending=False) if col_tgl_pbck3 in df_filtered.columns else df_filtered[available_cols_to_show],
    use_container_width=True,
    hide_index=True
)
