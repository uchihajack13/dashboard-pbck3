import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Dashboard PBCK-3 KPPBC TMC Malang",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk warna instansi (Navy Blue, Gold, and Clean Card Style)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
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
    }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .custom-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        margin: 0;
    }
    .custom-subtitle {
        font-size: 14px;
        opacity: 0.8;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# 2. LOGO DAN HEADER (Visual Instansi)
# Menggunakan logo resmi Bea Cukai dari link wiki yang stabil
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"

col_logo, col_header = st.columns([1, 6])
with col_logo:
    st.image(LOGO_URL, width=105)
with col_header:
    st.markdown("""
        <div class="main-header">
            <h1 class="custom-title">📊 DASHBOARD PBCK-3 & REALISASI CUKAI</h1>
            <p class="custom-subtitle">Sistem Pengawasan Pengolahan Kembali & Pemusnahan BKC — KPPBC TMC Malang</p>
            <p style="font-size: 11px; opacity: 0.6; margin-top: 5px;">Berdasarkan PMK 113/2025 & PER-2/BC/2026</p>
        </div>
    """, unsafe_allow_html=True)

# 3. KONEKSI & LOAD DATA (G-DRIVE EXCEL CLOUD ID)
@st.cache_data(ttl=600)  # Cache 10 menit agar tidak spam request
def load_data():
    # ID Drive file database utama
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    # Load sheet 'DATABASE MERGE'
    df = pd.read_excel(url_merge, sheet_name="DATABASE MERGE")
    
    # Standardisasi Nama Kolom (Mencegah Typo / Case-sensitive)
    df.columns = df.columns.str.strip()
    
    # Konversi tanggal
    date_cols = ['Tanggal PBCK-3', 'Tanggal BACK-3', 'Tanggal CK-2']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    return df

try:
    df_raw = load_data()
    # Masking/Penyesuaian kolom yang krusial jika ada
    df = df_raw.copy()
except Exception as e:
    st.error(f"⚠️ Gagal memuat data dari Cloud Drive, bro. Pastikan link file tidak di-Trash atau sinkronisasi lancar. Error: {e}")
    st.stop()

# 4. FILTER SIDEBAR (Untuk fleksibilitas Pimpinan)
st.sidebar.markdown("### 🎛️ Filter Eksekutif")
pabrik_list = ["Semua Pabrik"] + sorted(df['Nama Perusahaan'].dropna().unique().tolist())
selected_pabrik = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", pabrik_list)

# Filter Berdasarkan Tahun PBCK-3 (Biasanya pimpinan pengen lihat per-tahun anggaran)
if 'Tanggal PBCK-3' in df.columns:
    df['Tahun'] = df['Tanggal PBCK-3'].dt.year.fillna("Tanpa Tahun").astype(str)
    tahun_list = ["Semua Tahun"] + sorted(df['Tahun'].unique().tolist(), reverse=True)
    selected_tahun = st.sidebar.selectbox("Tahun Anggaran:", tahun_list)
else:
    selected_tahun = "Semua Tahun"

# Filter Data Berdasarkan Dropdown
df_filtered = df.copy()
if selected_pabrik != "Semua Pabrik":
    df_filtered = df_filtered[df_filtered['Nama Perusahaan'] == selected_pabrik]
if selected_tahun != "Semua Tahun":
    df_filtered = df_filtered[df_filtered['Tahun'] == selected_tahun]

# 5. PEMROSESAN METRIK UTAMA (DOUBLE COUNTER & FINANSIAL)
# Jumlah PBCK-3 (Dokumen permohonan masuk)
total_pbck3 = df_filtered['Nomor PBCK-3'].nunique() if 'Nomor PBCK-3' in df_filtered.columns else len(df_filtered)

# Jumlah CK-2 yang telah terbit (Memiliki Nomor CK-2 dan tidak kosong)
if 'Nomor CK-2' in df_filtered.columns:
    df_filtered['Status_CK2'] = df_filtered['Nomor CK-2'].apply(lambda x: "Terbit" if pd.notnull(x) and str(x).strip() != "" and str(x).strip().lower() != "nan" else "Proses")
    total_ck2 = df_filtered[df_filtered['Status_CK2'] == "Terbit"]['Nomor CK-2'].nunique()
else:
    df_filtered['Status_CK2'] = "Proses"
    total_ck2 = 0

# Jumlah yang Masih Proses / Outstanding
total_proses = total_pbck3 - total_ck2

# Perhitungan Cukai & BP (Biaya Pengganti)
# Menggunakan kolom finansial dari dataset
nilai_cukai = df_filtered['Nilai Cukai'].sum() if 'Nilai Cukai' in df_filtered.columns else 0
biaya_pengganti = df_filtered['Biaya Pengganti'].sum() if 'Biaya Pengganti' in df_filtered.columns else 0

# 6. TAMPILAN ROW METRIK UTAMA (3 COUNTERS ATAS + 2 FINANSIAL)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="📥 Total PBCK-3 (Masuk)", 
        value=f"{total_pbck3} Dokumen",
        help="Jumlah total dokumen PBCK-3 permohonan pemusnahan/pengolahan kembali yang diajukan ke kantor."
    )
with col2:
    st.metric(
        label="📜 CK-2 Telah Terbit", 
        value=f"{total_ck2} Dokumen",
        delta=f"{total_ck2/total_pbck3*100:.1f}% dari total" if total_pbck3 > 0 else "0%",
        delta_color="normal",
        help="Jumlah dokumen CK-2 (Tanda Bukti Perusakan Pita Cukai) yang sudah resmi terbit dan tuntas."
    )
with col3:
    st.metric(
        label="⏳ Dalam Proses / Outstanding", 
        value=f"{total_proses} Dokumen",
        delta=f"{(total_proses/total_pbck3)*100:.1f}% sisa" if total_pbck3 > 0 else "0%",
        delta_color="inverse",
        help="Sisa berkas PBCK-3 yang sudah diajukan namun belum sampai ke tahap penerbitan CK-2."
    )
with col4:
    st.metric(
        label="💸 Potensi Pengembalian Cukai", 
        value=f"Rp {nilai_cukai:,.0f}",
        help="Nilai cukai bruto yang berhak dikembalikan ke Pengusaha Pabrik (PMK 113/2025)."
    )
with col5:
    st.metric(
        label="🏦 Biaya Pengganti (BP) Masuk", 
        value=f"Rp {biaya_pengganti:,.0f}",
        help="Penerimaan negara dari biaya penyediaan pita cukai yang dirusak (Seri I: Rp25, Seri II: Rp40, dst)."
    )

st.markdown("---")

# 7. MITIGASI SLA & PENGAWASAN (Fitur Mewah Buat Pimpinan)
st.subheader("🚨 Monitoring Kepatuhan & SLA Kertas Kerja")

# Hitung Kepatuhan SLA: CK-2 harus terbit maksimal 10 hari kerja dari BACK-3 (PER-2/BC/2026 Pasal 7)
if 'Tanggal BACK-3' in df_filtered.columns and 'Tanggal CK-2' in df_filtered.columns:
    # Buat simulasi penghitungan hari kerja (SLA 10 Hari)
    df_sla = df_filtered[df_filtered['Tanggal BACK-3'].notnull()].copy()
    
    # Hari ini (utk hitung outstanding SLA)
    today = datetime.today()
    
    def hitung_sla_status(row):
        tgl_back = row['Tanggal BACK-3']
        tgl_ck = row['Tanggal CK-2']
        
        if pd.isnull(tgl_ck):
            # Jika belum terbit, hitung dari BACK-3 ke Hari ini
            hari_lewat = (today - tgl_back).days
            if hari_lewat > 14: # Kasarannya 10 hari kerja setara ~14 hari kalender
                return "🚨 Overdue (Belum CK-2)"
            elif hari_lewat >= 10:
                return "⚠️ Peringatan SLA (>7 Hari)"
            else:
                return "⏳ Dalam Batas Aman"
        else:
            # Jika sudah terbit, hitung selisih
            hari_kerja_est = (tgl_ck - tgl_back).days
            if hari_kerja_est <= 14:
                return "✅ SLA Terpenuhi (<10 Hari Kerja)"
            else:
                return "❌ Lewat SLA (Terlambat Terbit)"

    df_sla['SLA_Status'] = df_sla.apply(hitung_sla_status, axis=1)
    
    # Hitung Rekap SLA
    rekap_sla = df_sla['SLA_Status'].value_counts()
    
    # Kolom Peringatan & Grafik SLA
    col_sla_info, col_sla_graph = st.columns([1, 1])
    
    with col_sla_info:
        st.markdown("##### 📌 Rekap SLA Penerbitan CK-2 (Max 10 Hari Kerja)")
        st.caption("Memantau kepatuhan KPPBC terhadap Pasal 7 ayat (1) PER-2/BC/2026.")
        
        # Penampilan badge status alert
        overdue_cnt = rekap_sla.get("🚨 Overdue (Belum CK-2)", 0)
        warn_cnt = rekap_sla.get("⚠️ Peringatan SLA (>7 Hari)", 0)
        late_cnt = rekap_sla.get("❌ Lewat SLA (Terlambat Terbit)", 0)
        ok_cnt = rekap_sla.get("✅ SLA Terpenuhi (<10 Hari Kerja)", 0)
        
        if overdue_cnt > 0:
            st.error(f"🔴 **{overdue_cnt} Dokumen OVERDUE!** Melebihi batas 10 hari kerja sejak BACK-3 tapi CK-2 belum terbit.")
        if warn_cnt > 0:
            st.warning(f"🟡 **{warn_cnt} Dokumen mendekati batas SLA.** Membutuhkan prioritas pemeriksaan.")
        if late_cnt > 0:
            st.info(f"⚪ {late_cnt} Dokumen tercatat diterbitkan terlambat (melewati batas waktu).")
        if overdue_cnt == 0 and warn_cnt == 0:
            st.success("🟢 Semua proses penerbitan CK-2 saat ini berada dalam koridor SLA yang aman!")
            
        # Tabel Data yang Perlu Diatensi (Filter yang "Overdue" dan "Peringatan")
        df_atensi = df_sla[df_sla['SLA_Status'].isin(["🚨 Overdue (Belum CK-2)", "⚠️ Peringatan SLA (>7 Hari)"])][['Nama Perusahaan', 'Nomor PBCK-3', 'Tanggal BACK-3', 'SLA_Status']]
        if not df_atensi.empty:
            st.markdown("**📋 Daftar Perlu Atensi Segera:**")
            st.dataframe(df_atensi, use_container_width=True, hide_index=True)
            
    with col_sla_graph:
        # Pie Chart SLA Status
        fig_sla = px.pie(
            names=rekap_sla.index, 
            values=rekap_sla.values,
            title="Persentase Kepatuhan SLA Kantor (PER-2/BC/2026)",
            color_discrete_sequence=["#10b981", "#ef4444", "#f59e0b", "#3b82f6", "#6b7280"]
        )
        fig_sla.update_layout(margin=dict(t=35, b=10, l=10, r=10), height=230)
        st.plotly_chart(fig_sla, use_container_width=True)

st.markdown("---")

# 8. ANALISIS OPERASIONAL & TREN (PLOT/VISUALISASI)
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📈 Tren Bulanan Pengajuan & Penyelesaian")
    if 'Tanggal PBCK-3' in df_filtered.columns:
        # Grouping Bulan
        df_filtered['Bulan-Tahun'] = df_filtered['Tanggal PBCK-3'].dt.to_period('M').astype(str)
        
        # Hitung PBCK3 vs CK2 bulanan
        df_trend = df_filtered.groupby('Bulan-Tahun').agg(
            PBCK3=('Nomor PBCK-3', 'count'),
            CK2=('Nomor CK-2', lambda x: x.notnull().sum())
        ).reset_index()
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=df_trend['Bulan-Tahun'], y=df_trend['PBCK3'],
            name='Permohonan (PBCK-3)', marker_color='#1e3a8a'
        ))
        fig_trend.add_trace(go.Line(
            x=df_trend['Bulan-Tahun'], y=df_trend['CK2'],
            name='Tuntas (CK-2)', marker_color='#fbbf24', line=dict(width=3)
        ))
        fig_trend.update_layout(
            barmode='group', 
            xaxis_title="Bulan Anggaran",
            yaxis_title="Jumlah Dokumen",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=300,
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Data tanggal tidak tersedia untuk merender Tren Bulanan.")

with col_chart2:
    st.subheader("🏭 Kontribusi Nilai Cukai per Pabrik / Golongan")
    if 'Nama Perusahaan' in df_filtered.columns and 'Nilai Cukai' in df_filtered.columns:
        # Group by pabrik
        df_pabrik_grp = df_filtered.groupby('Nama Perusahaan')['Nilai Cukai'].sum().reset_index().sort_values(by='Nilai Cukai', ascending=False).head(8)
        
        fig_pabrik = px.bar(
            df_pabrik_grp, 
            x='Nilai Cukai', 
            y='Nama Perusahaan', 
            orientation='h',
            title="8 Pabrik Terbesar Berdasarkan Nilai Refund Cukai (Rp)",
            color_discrete_sequence=["#fbbf24"]
        )
        fig_pabrik.update_layout(
            xaxis_title="Rupiah (Rp)",
            yaxis_title=None,
            height=300,
            margin=dict(t=35, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_pabrik, use_container_width=True)
    else:
        st.info("Data tidak memiliki kolom 'Nama Perusahaan' atau 'Nilai Cukai' yang cukup.")

# 9. DETAIL DATA TRANSAKSI
st.subheader("📑 Detail Data Transaksi Ter-filter")
view_cols = ['Nama Perusahaan', 'Nomor PBCK-3', 'Tanggal PBCK-3', 'Tanggal BACK-3', 'Nomor CK-2', 'Tanggal CK-2', 'Nilai Cukai', 'Biaya Pengganti']
cols_present = [col for col in view_cols if col in df_filtered.columns]

st.dataframe(
    df_filtered[cols_present].sort_values(by='Tanggal PBCK-3', ascending=False) if 'Tanggal PBCK-3' in df_filtered.columns else df_filtered[cols_present], 
    use_container_width=True,
    hide_index=True
)
