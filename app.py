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

# Custom Styling CSS Modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Container Kartu KPI */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        margin-bottom: 14px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    }

    /* Varian Garis Aksen Samping */
    .border-blue { border-left: 5px solid #1E3A8A; }
    .border-green { border-left: 5px solid #059669; }
    .border-amber { border-left: 5px solid #D97706; }
    .border-slate { border-left: 5px solid #475569; }
    .border-red { border-left: 5px solid #DC2626; }

    /* Label & Nilai Metrik */
    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: #64748B;
    }
    .kpi-icon {
        font-size: 18px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
        margin-bottom: 4px;
    }
    .kpi-subtext {
        font-size: 12px;
        font-weight: 500;
        color: #64748B;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Badge Tag */
    .badge-success {
        background-color: #ECFDF5;
        color: #047857;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-warning {
        background-color: #FFFBEB;
        color: #B45309;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-danger {
        background-color: #FEF2F2;
        color: #B91C1C;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
    }

    /* Banner Info Header */
    .info-banner {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 20px;
        font-size: 13px;
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HEADER & LOGO RESMI KPPBC
# ==============================================================================
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"
col_logo, col_header = st.columns([1, 8])
with col_logo:
    st.image(LOGO_URL, width=78)
with col_header:
    st.markdown("""
    <h2 style='margin-bottom: 2px; color: #1e3a8a; font-weight: 800;'>📊 EXECUTIVE DASHBOARD PBCK-3 & REALISASI CUKAI</h2>
    <p style='margin-top: 0px; color: #64748b; font-size: 14px;'>
    Monitoring Pelayanan Pengolahan Kembali & Pemusnahan BKC — KPPBC Tipe Madya Cukai Malang<br>
    <b>Landasan Hukum: Peraturan Menteri Keuangan No. 113/2025 & PER-2/BC/2026</b>
    </p>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. KONEKSI & LOAD DATA CLOUD
# ==============================================================================
@st.cache_data(ttl=300)
def load_data():
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    df = pd.read_excel(url_merge, sheet_name="DATABASE MERGE")
    df.columns = df.columns.astype(str).str.strip().str.upper()
    return df

try:
    df_raw = load_data()
    df = df_raw.copy()
except Exception as e:
    st.error(f"⚠️ Gagal memuat data dari cloud. Error: {e}")
    st.stop()

# ==============================================================================
# 4. RESOLVING GHOST COLUMNS & FORMAT DATA
# ==============================================================================
col_pabrik = "PERUSAHAAN" if "PERUSAHAAN" in df.columns else ("PERUSAHAAN_KEP" if "PERUSAHAAN_KEP" in df.columns else df.columns[1])
col_pbck3 = "NO_PBCK-3" if "NO_PBCK-3" in df.columns else ("NO_PBCK_3" if "NO_PBCK_3" in df.columns else df.columns[0])
col_tgl_pbck3 = "TANGGAL_PBCK-3" if "TANGGAL_PBCK-3" in df.columns else "TANGGAL_PBCK3"
col_back3 = "BACK-3" if "BACK-3" in df.columns else df.columns[0]
col_tgl_back3 = "TANGGAL BACK-3" if "TANGGAL BACK-3" in df.columns else "TANGGAL_BACK-3"
col_ck2 = "NO_CK-2" if "NO_CK-2" in df.columns else "NO_CK2"
col_tgl_ck2 = "TGL_CK-2" if "TGL_CK-2" in df.columns else "TGL_CK_2"

# Pemisahan Nilai Cukai: Pengajuan (PBCK-3) vs Realisasi (CK-2/MS)
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

df['TAHUN_PBCK'] = df[col_tgl_pbck3].dt.year.fillna(2026).astype(int) if col_tgl_pbck3 in df.columns else 2026
df['BULAN_ANGKA'] = df[col_tgl_pbck3].dt.month.fillna(1).astype(int) if col_tgl_pbck3 in df.columns else 1

INDO_BULAN = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni',
    7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}
df['BULAN_NAMA'] = df['BULAN_ANGKA'].map(INDO_BULAN)

# ==============================================================================
# 5. SIDEBAR FILTER
# ==============================================================================
st.sidebar.markdown("### 🎛️ Filter Dasbor")

pabrik_list = ["Semua Pabrik"] + sorted(df[col_pabrik].dropna().unique().tolist())
selected_pabrik = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", pabrik_list)

tahun_list = sorted(df['TAHUN_PBCK'].unique().tolist(), reverse=True)
selected_tahun = st.sidebar.selectbox("Pilih Tahun:", tahun_list)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗓️ Filter Periode Bulanan")
mode_periode = st.sidebar.radio(
    "Mode Periode:",
    ["Semua Periode", "Bulanan Tunggal (Single Month)", "Kumulatif (s.d. Bulan)"],
    help="Gunakan untuk laporan evaluasi berkala bulanan atau capaian kumulatif YTD."
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
# 6. LOGIKA FILTERING
# ==============================================================================
df_filtered = df.copy()

if selected_pabrik != "Semua Pabrik":
    df_filtered = df_filtered[df_filtered[col_pabrik] == selected_pabrik]

df_filtered = df_filtered[df_filtered['TAHUN_PBCK'] == selected_tahun]

if mode_periode == "Bulanan Tunggal (Single Month)":
    df_filtered = df_filtered[df_filtered['BULAN_ANGKA'] == selected_bulan_angka]
elif mode_periode == "Kumulatif (s.d. Bulan)":
    df_filtered = df_filtered[df_filtered['BULAN_ANGKA'] <= selected_bulan_angka]

# ==============================================================================
# 7. PERHITUNGAN METRIK EKSEKUTIF
# ==============================================================================
total_pbck3 = df_filtered[col_pbck3].nunique() if col_pbck3 in df_filtered.columns else len(df_filtered)

if col_ck2 in df_filtered.columns:
    df_filtered['STATUS_CK2_BOOL'] = df_filtered[col_ck2].apply(
        lambda x: "TERBIT" if pd.notnull(x) and str(x).strip() != "" and str(x).strip().lower() != "nan" and str(x).strip() != "-" else "PROSES"
    )
    total_ck2 = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"][col_ck2].nunique()
else:
    df_filtered['STATUS_CK2_BOOL'] = "PROSES"
    total_ck2 = 0

total_outstanding = total_pbck3 - total_ck2
persen_selesai = (total_ck2 / total_pbck3 * 100) if total_pbck3 > 0 else 0

# Nilai Keuangan Bersih
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

# Label Info Periode
visual_periode_lbl = f"Tahun Anggaran {selected_tahun}"
if mode_periode == "Bulanan Tunggal (Single Month)":
    visual_periode_lbl = f"Bulan {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)":
    visual_periode_lbl = f"Januari s.d. {selected_bulan_nama} {selected_tahun}"

st.markdown(f"""
<div class="info-banner">
    📌 <b>Periode Aktif:</b> <code>{visual_periode_lbl}</code> &nbsp;|&nbsp; 
    🏢 <b>Entitas:</b> <code>{selected_pabrik}</code> &nbsp;|&nbsp; 
    📄 <b>Status Rekonsiliasi:</b> {'<span class="badge-success">Fisik 100% Sesuai</span>' if selisih_fisik == 0 else f'<span class="badge-danger">Selisih Fisik Rp {selisih_fisik:,.0f}</span>'}
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 8. PANEL METRIK MODERN UI (SANGAT ENYAK DIBACA)
# ==============================================================================

# BARIS 1: VOLUME PENGAWASAN & PROGRESS PELAYANAN
row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    st.markdown(f"""
    <div class="kpi-card border-blue">
        <div class="kpi-header">
            <span class="kpi-label">Total Permohonan PBCK-3</span>
            <span class="kpi-icon">📥</span>
        </div>
        <div class="kpi-value">{total_pbck3:,} <span style="font-size: 15px; font-weight: 600; color: #64748B;">Berkas</span></div>
        <div class="kpi-subtext">Diajukan pengusaha pabrik</div>
    </div>
    """, unsafe_allow_html=True)

with row1_col2:
    st.markdown(f"""
    <div class="kpi-card border-green">
        <div class="kpi-header">
            <span class="kpi-label">Realisasi Selesai (CK-2 Terbit)</span>
            <span class="kpi-icon">📜</span>
        </div>
        <div class="kpi-value">{total_ck2:,} <span style="font-size: 15px; font-weight: 600; color: #64748B;">Dokumen</span></div>
        <div class="kpi-subtext">
            <span class="badge-success">{persen_selesai:.1f}% Tuntas</span> dari total berkas
        </div>
    </div>
    """, unsafe_allow_html=True)

with row1_col3:
    badge_outstanding = "badge-success" if total_outstanding == 0 else "badge-warning"
    st.markdown(f"""
    <div class="kpi-card border-amber">
        <div class="kpi-header">
            <span class="kpi-label">Outstanding (Dalam Proses)</span>
            <span class="kpi-icon">⏳</span>
        </div>
        <div class="kpi-value">{total_outstanding:,} <span style="font-size: 15px; font-weight: 600; color: #64748B;">Dokumen</span></div>
        <div class="kpi-subtext">
            <span class="{badge_outstanding}">{(total_outstanding/total_pbck3*100) if total_pbck3 > 0 else 0:.1f}% Beban Kerja</span> menunggu CK-2
        </div>
    </div>
    """, unsafe_allow_html=True)

# BARIS 2: NILAI FINANSIAL CUKAI (HIERARKI & READABILITY FOKUS)
row2_col1, row2_col2, row2_col3 = st.columns(3)

with row2_col1:
    st.markdown(f"""
    <div class="kpi-card border-slate">
        <div class="kpi-header">
            <span class="kpi-label">Nilai Pengajuan (PBCK-3)</span>
            <span class="kpi-icon">📋</span>
        </div>
        <div class="kpi-value">Rp {cukai_pbck3_val:,.0f}</div>
        <div class="kpi-subtext">Total potensi cukai pemberitahuan</div>
    </div>
    """, unsafe_allow_html=True)

with row2_col2:
    selisih_badge = f'<span class="badge-danger">Selisih TMS: -Rp {selisih_fisik:,.0f}</span>' if selisih_fisik > 0 else '<span class="badge-success">100% Memenuhi Syarat</span>'
    st.markdown(f"""
    <div class="kpi-card border-green" style="background: #F0FDF4;">
        <div class="kpi-header">
            <span class="kpi-label" style="color: #047857;">Realisasi Cukai CK-2 (MS)</span>
            <span class="kpi-icon">💸</span>
        </div>
        <div class="kpi-value" style="color: #065F46;">Rp {cukai_ck2_val:,.0f}</div>
        <div class="kpi-subtext">{selisih_badge}</div>
    </div>
    """, unsafe_allow_html=True)

with row2_col3:
    st.markdown(f"""
    <div class="kpi-card border-amber">
        <div class="kpi-header">
            <span class="kpi-label">Biaya Pengganti (BP) Pita Cukai</span>
            <span class="kpi-icon">🏦</span>
        </div>
        <div class="kpi-value" style="color: #92400E;">Rp {biaya_pengganti:,.0f}</div>
        <div class="kpi-subtext">Penerimaan Negara (PMK 113/2025)</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 9. INTEGRASI DIAGRAM & ANALISIS TREN BULANAN
# ==============================================================================
col_chart1, col_chart2 = st.columns([6, 5])

with col_chart1:
    st.subheader("📈 Tren Kinerja Pelayanan Bulanan")
    st.caption("Visualisasi permohonan masuk (Inflow PBCK-3) vs CK-2 terbit (Outflow).")
    
    df_trend_monthly = df_filtered.groupby('BULAN_ANGKA').agg(
        PBCK3=(col_pbck3, 'count') if col_pbck3 in df_filtered.columns else ('BULAN_ANGKA', 'count'),
        CK2=('STATUS_CK2_BOOL', lambda x: (x == "TERBIT").sum())
    ).reset_index()
    
    df_trend_monthly['BULAN'] = df_trend_monthly['BULAN_ANGKA'].map(INDO_BULAN)
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=df_trend_monthly['BULAN'],
        y=df_trend_monthly['PBCK3'],
        name='PBCK-3 Masuk',
        marker_color='#1E3A8A',
        opacity=0.88
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_trend_monthly['BULAN'],
        y=df_trend_monthly['CK2'],
        name='CK-2 Terbit',
        marker_color='#F59E0B',
        mode='lines+markers',
        line=dict(width=3.5)
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
            hole=0.45
        )
        fig_pie.update_layout(height=320, margin=dict(t=15, b=15, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Visualisasi kontribusi pabrik belum memadai.")

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
