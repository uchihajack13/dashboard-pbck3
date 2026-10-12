import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA EKSEKUTIF
# ==============================================================================
st.set_page_config(
    page_title="Dashboard PBCK-3 KPPBC TMC Malang",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS warna instansi (Navy Blue, Gold, and Clean Card Style)
st.markdown("""
<style>
    .metric-card-custom {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HEADER & LOGO RESMI KPPBC
# ==============================================================================
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"
col_logo, col_header = st.columns([1, 8])
with col_logo:
    st.image(LOGO_URL, width=80)
with col_header:
    st.markdown("""
    <h2 style='margin-bottom: 0px; color: #1e3a8a;'>📊 DASHBOARD PBCK-3 & REALISASI CUKAI</h2>
    <p style='margin-top: 0px; color: #64748b; font-size: 15px;'>
    Monitoring Pengolahan Kembali & Pemusnahan BKC — KPPBC TMC Malang<br>
    <b>Terintegrasi dengan PMK 113/2025 & PER-2/BC/2026</b>
    </p>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. KONEKSI & LOAD DATA DARI CLOUD DRIVE
# ==============================================================================
@st.cache_data(ttl=300) # Cache 5 menit biar real-time dan hemat kuota
def load_data():
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url_merge, sheet_name="DATABASE MERGE")
    # ⚠️ Kunci Utama: Standardisasi Kolom (Huruf Besar & Tanpa Spasi)
    df.columns = df.columns.astype(str).str.strip().str.upper()
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()
except Exception as e:
    st.error(f"⚠️ Gagal memuat data dari G-Drive, bro. Error: {e}")
    st.stop()

# ==============================================================================
# 4. RESOLVING GHOST COLUMNS (MENCEGAH KEYERROR)
# ==============================================================================
col_pabrik = "PERUSAHAAN" if "PERUSAHAAN" in df.columns else ("PERUSAHAAN_KEP" if "PERUSAHAAN_KEP" in df.columns else df.columns[1])
col_pbck3 = "NO_PBCK-3" if "NO_PBCK-3" in df.columns else ("NO_PBCK_3" if "NO_PBCK_3" in df.columns else df.columns[0])
col_tgl_pbck3 = "TANGGAL_PBCK-3" if "TANGGAL_PBCK-3" in df.columns else "TANGGAL_PBCK3"
col_back3 = "BACK-3" if "BACK-3" in df.columns else df.columns[0]
col_tgl_back3 = "TANGGAL BACK-3" if "TANGGAL BACK-3" in df.columns else "TANGGAL_BACK-3"
col_ck2 = "NO_CK-2" if "NO_CK-2" in df.columns else "NO_CK2"
col_tgl_ck2 = "TGL_CK-2" if "TGL_CK-2" in df.columns else "TGL_CK_2"

# PEMISAHAN NILAI CUKAI: PENGAJUAN (PBCK-3) VS REALISASI (CK-2/MS)
col_cukai_pbck3 = "TOTAL_CUKAI" if "TOTAL_CUKAI" in df.columns else ("TOTAL CUKAI" if "TOTAL CUKAI" in df.columns else df.columns[47])
col_cukai_ck2 = "CUKAI_MS" if "CUKAI_MS" in df.columns else ("CUKAI MS" if "CUKAI MS" in df.columns else col_cukai_pbck3)
col_biaya_pengganti = "JUMLAH_BP" if "JUMLAH_BP" in df.columns else ("JUMLAH BP" if "JUMLAH BP" in df.columns else df.columns[49])

# Format Tanggal
if col_tgl_pbck3 in df.columns:
    df[col_tgl_pbck3] = pd.to_datetime(df[col_tgl_pbck3], errors='coerce')
if col_tgl_back3 in df.columns:
    df[col_tgl_back3] = pd.to_datetime(df[col_tgl_back3], errors='coerce')
if col_tgl_ck2 in df.columns:
    df[col_tgl_ck2] = pd.to_datetime(df[col_tgl_ck2], errors='coerce')

# Ekstrak Info Tahun & Bulan berdasarkan data TANGGAL_PBCK-3
df['TAHUN_PBCK'] = df[col_tgl_pbck3].dt.year.fillna(2026).astype(int) if col_tgl_pbck3 in df.columns else 2026
df['BULAN_ANGKA'] = df[col_tgl_pbck3].dt.month.fillna(1).astype(int) if col_tgl_pbck3 in df.columns else 1

INDO_BULAN = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}
df['BULAN_NAMA'] = df['BULAN_ANGKA'].map(INDO_BULAN)

# ==============================================================================
# 5. INTEGRASI FILTER PERIODE & PABRIK (DI SIDEBAR)
# ==============================================================================
st.sidebar.markdown("### 🎛️ Filter Dasbor")

# Filter A: Perusahaan Pabrik
pabrik_list = ["Semua Pabrik"] + sorted(df[col_pabrik].dropna().unique().tolist())
selected_pabrik = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", pabrik_list)

# Filter B: Tahun
tahun_list = sorted(df['TAHUN_PBCK'].unique().tolist(), reverse=True)
selected_tahun = st.sidebar.selectbox("Pilih Tahun:", tahun_list)

# Filter Periode Bulan
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗓️ Filter Periode Bulanan")
mode_periode = st.sidebar.radio(
    "Mode Periode:",
    ["Semua Periode", "Bulanan Tunggal (Single Month)", "Kumulatif (s.d. Bulan)"],
    help="Sangat penting untuk laporan audit, bisa melihat realisasi satu bulan tertentu atau perkembangan s.d. bulan berjalan!"
)

selected_bulan_nama = "Januari"
selected_bulan_angka = 1
if mode_periode != "Semua Periode":
    nama_bulan_list = [INDO_BULAN[i] for i in sorted(df[df['TAHUN_PBCK'] == selected_tahun]['BULAN_ANGKA'].unique())]
    if not nama_bulan_list:
        nama_bulan_list = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    selected_bulan_nama = st.sidebar.selectbox("Pilih Bulan Acuan:", nama_bulan_list)
    selected_bulan_angka = next(k for k, v in INDO_BULAN.items() if v == selected_bulan_nama)

# ==============================================================================
# 6. PENGEKSEKUSIAN LOGIKA FILTER DATA
# ==============================================================================
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

# ==============================================================================
# 7. PEMROSESAN ANGGOTA & METRIK EKSEKUTIF
# ==============================================================================
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

# Perhitungan Nilai Finansial (PBCK-3, Realisasi CK-2, dan Biaya Pengganti)
cukai_pbck3_val = pd.to_numeric(
    df_filtered[col_cukai_pbck3].astype(str).str.replace("Rp", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(),
    errors='coerce'
).sum() if col_cukai_pbck3 in df_filtered.columns else 0

cukai_ck2_val = pd.to_numeric(
    df_filtered[col_cukai_ck2].astype(str).str.replace("Rp", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(),
    errors='coerce'
).sum() if col_cukai_ck2 in df_filtered.columns else 0

selisih_fisik = cukai_pbck3_val - cukai_ck2_val

biaya_pengganti = pd.to_numeric(
    df_filtered[col_biaya_pengganti].astype(str).str.replace("Rp", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(),
    errors='coerce'
).sum() if col_biaya_pengganti in df_filtered.columns else 0

# Label Filter Aktif
visual_periode_lbl = "Semua Periode Tahun " + str(selected_tahun)
if mode_periode == "Bulanan Tunggal (Single Month)":
    visual_periode_lbl = f"Bulan {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)":
    visual_periode_lbl = f"Januari s.d. {selected_bulan_nama} {selected_tahun}"

st.markdown(f"🚩 **Periode Terpantau:** `{visual_periode_lbl}` &nbsp;|&nbsp; 🏢 **Perusahaan Pabrik:** `{selected_pabrik}`")

# ==============================================================================
# 8. PANEL UTAMA TAMPILAN COUNTER / METRIKS
# ==============================================================================
# Baris 1: Volume Berkas
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

# Baris 2: Nilai Finansial (Komparasi PBCK-3 vs Realisasi CK-2)
col_fin1, col_fin2, col_fin3 = st.columns(3)
with col_fin1:
    st.metric(
        label="📋 TOTAL CUKAI DIAJUKAN (PBCK-3)",
        value=f"Rp {cukai_pbck3_val:,.0f}",
        help="Nilai cukai yang diberitahukan pengusaha pada dokumen PBCK-3."
    )
with col_fin2:
    st.metric(
        label="💸 REALISASI CUKAI CK-2 (MS)",
        value=f"Rp {cukai_ck2_val:,.0f}",
        delta=f"-Rp {selisih_fisik:,.0f} TMS" if selisih_fisik > 0 else "100% Sesuai Fisik",
        delta_color="normal" if selisih_fisik == 0 else "inverse",
        help="Nilai cukai yang memenuhi syarat (MS) dan resmi terbit dokumen CK-2 (PMK 113/2025)."
    )
with col_fin3:
    st.metric(
        label="🏦 TOTAL BIAYA PENGGANTI (PENERIMAAN NEGARA)",
        value=f"Rp {biaya_pengganti:,.0f}",
        help="Biaya pengganti penyediaan pita cukai yang harus disetor sebelum CK-2 digunakan."
    )

st.markdown("---")

# ==============================================================================
# 9. INTEGRASI DIAGRAM & ANALISIS TREN BULANAN
# ==============================================================================
col_chart1, col_chart2 = st.columns([6, 5])

with col_chart1:
    st.subheader("📈 Tren Kinerja Bulanan")
    st.caption("Visualisasi permohonan yang masuk (Inflow) dibanding CK-2 yang terbit (Outflow).")
    
    df_trend_monthly = df_filtered.groupby('BULAN_ANGKA').agg(
        PBCK3=(col_pbck3, 'count') if col_pbck3 in df_filtered.columns else ('BULAN_ANGKA', 'count'),
        CK2=('STATUS_CK2_BOOL', lambda x: (x == "TERBIT").sum())
    ).reset_index()
    
    df_trend_monthly['BULAN'] = df_trend_monthly['BULAN_ANGKA'].map(INDO_BULAN)
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=df_trend_monthly['BULAN'],
        y=df_trend_monthly['PBCK3'],
        name='Dokumen PBCK-3 Masuk',
        marker_color='#1e3a8a',
        opacity=0.85
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_trend_monthly['BULAN'],
        y=df_trend_monthly['CK2'],
        name='Dokumen CK-2 Terbit',
        marker_color='#fbbf24',
        mode='lines+markers',
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
    st.subheader("📊 Kontribusi Realisasi Nilai Cukai (CK-2)")
    st.caption("Distribusi nilai pengembalian cukai yang memenuhi syarat (MS) per pabrik.")
    if col_pabrik in df_filtered.columns and col_cukai_ck2 in df_filtered.columns:
        df_pabrik_grp = df_filtered.groupby(col_pabrik)[col_cukai_ck2].apply(
            lambda s: pd.to_numeric(s.astype(str).str.replace("Rp", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip(), errors='coerce').sum()
        ).reset_index()
        df_pabrik_grp = df_pabrik_grp.sort_values(by=col_cukai_ck2, ascending=False).head(5)
        fig_pie = px.pie(
            df_pabrik_grp,
            names=col_pabrik,
            values=col_cukai_ck2,
            color_discrete_sequence=px.colors.sequential.Blues_r,
            hole=0.4
        )
        fig_pie.update_layout(height=320, margin=dict(t=15, b=15, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Visualisasi data Perusahaan Pabrik tidak memadai.")

st.markdown("---")

# ==============================================================================
# 10. NOTIFIKASI SLA (MEGATRON / COMPLIANCE WARNING)
# ==============================================================================
st.subheader("🚨 Warning Kepatuhan SLA (Maks 10 Hari Kerja s.d. CK-2)")
st.caption("Berdasarkan PER-2/BC/2026 Pasal 7, penerbitan CK-2 tidak boleh melebihi 10 hari kerja sejak Tanggal BACK-3 diterbitkan.")

col_warn1, col_warn2 = st.columns(2)
col_tempo = "JATUH TEMPO BERAPA HARI LAGI" if "JATUH TEMPO BERAPA HARI LAGI" in df.columns else None

if col_tempo:
    df_proses = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "PROSES"].copy()
    if not df_proses.empty:
        df_proses['SISA_HARI_INT'] = pd.to_numeric(df_proses[col_tempo], errors='coerce')
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

# ==============================================================================
# 11. DETIL DATA TRANSAKSI
# ==============================================================================
st.markdown("---")
st.subheader("📑 Detail Data Transaksi (Ter-filter)")

# Menampilkan nilai pengajuan PBCK-3 dan realisasi CK-2 secara berdampingan di tabel
view_cols = [
    col_pabrik, col_pbck3, col_tgl_pbck3, 
    col_cukai_pbck3, col_cukai_ck2, 
    col_biaya_pengganti, col_back3, col_tgl_back3, 
    col_ck2, col_tgl_ck2
]
available_cols_to_show = [c for c in view_cols if c and c in df_filtered.columns]

st.dataframe(
    df_filtered[available_cols_to_show].sort_values(by=col_tgl_pbck3, ascending=False) if col_tgl_pbck3 in df_filtered.columns else df_filtered[available_cols_to_show],
    use_container_width=True,
    hide_index=True
)
