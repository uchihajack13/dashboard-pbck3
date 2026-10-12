import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Dashboard PBCK-3 KPPBC TMC Malang",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .kpi-card {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 16px 18px; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px; transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .border-blue { border-left: 5px solid #1E3A8A; }
    .border-green { border-left: 5px solid #059669; }
    .border-amber { border-left: 5px solid #D97706; }
    .border-slate { border-left: 5px solid #475569; }
    .border-red { border-left: 5px solid #DC2626; }
    .kpi-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .kpi-label { font-size: 11px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: #64748B; }
    .kpi-icon { font-size: 16px; }
    .kpi-value { font-size: 21px; font-weight: 800; color: #0F172A; line-height: 1.2; margin-bottom: 4px; }
    .kpi-subtext { font-size: 11px; font-weight: 500; color: #64748B; }
    .badge-success { background-color: #ECFDF5; color: #047857; padding: 2px 7px; border-radius: 9999px; font-size: 10px; font-weight: 700; }
    .badge-warning { background-color: #FFFBEB; color: #B45309; padding: 2px 7px; border-radius: 9999px; font-size: 10px; font-weight: 700; }
    .badge-danger { background-color: #FEF2F2; color: #B91C1C; padding: 2px 7px; border-radius: 9999px; font-size: 10px; font-weight: 700; }
    .info-banner { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; margin-bottom: 18px; font-size: 13px; color: #334155; }
</style>
""", unsafe_allow_html=True)

# ---- FORMATTER BARU (Angka Asli + Singkatan) ----
def fmt_rupiah(val):
    if pd.isna(val) or val == 0: return "Rp 0"
    is_negative = val < 0
    val = abs(val)
    
    real_str = f"Rp {val:,.0f}".replace(",", ".")
    
    if val >= 1_000_000_000_000:
        alias = f"({val/1_000_000_000_000:.2f} Triliun)".replace(".", ",")
        formatted = f"{real_str} <span style='font-size: 13px; color: #64748B;'>{alias}</span>"
    elif val >= 1_000_000_000:
        alias = f"({val/1_000_000_000:.2f} Miliar)".replace(".", ",")
        formatted = f"{real_str} <span style='font-size: 13px; color: #64748B;'>{alias}</span>"
    elif val >= 1_000_000:
        alias = f"({val/1_000_000:.2f} Juta)".replace(".", ",")
        formatted = f"{real_str} <span style='font-size: 13px; color: #64748B;'>{alias}</span>"
    else:
        formatted = real_str
        
    return f"-{formatted}" if is_negative else formatted

def fmt_bungkus(val):
    if pd.isna(val) or val == 0: return "0"
    is_negative = val < 0
    val = abs(val)
    
    real_str = f"{val:,.0f}".replace(",", ".")
    
    if val >= 1_000_000_000:
        alias = f"({val/1_000_000_000:.2f} M)".replace(".", ",")
        formatted = f"{real_str} <span style='font-size: 13px; color: #64748B;'>{alias}</span>"
    elif val >= 1_000_000:
        alias = f"({val/1_000_000:.2f} Jt)".replace(".", ",")
        formatted = f"{real_str} <span style='font-size: 13px; color: #64748B;'>{alias}</span>"
    else:
        formatted = real_str
        
    return f"-{formatted}" if is_negative else formatted
# -------------------------------------------------

LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"
col_logo, col_header = st.columns([1, 8])
with col_logo: st.image(LOGO_URL, width=78)
with col_header:
    st.markdown("""
    <h2 style='margin-bottom: 2px; color: #1e3a8a; font-weight: 800;'>📊 EXECUTIVE DASHBOARD PBCK-3 & REALISASI CUKAI</h2>
    <p style='margin-top: 0px; color: #64748b; font-size: 14px;'>
    Monitoring Pelayanan Pengolahan Kembali & Pemusnahan BKC — KPPBC Tipe Madya Cukai Malang<br>
    <b>Landasan Hukum: Peraturan Menteri Keuangan No. 113/2025 & PER-2/BC/2026</b>
    </p>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_data():
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    xls = pd.ExcelFile(url_merge)
    
    df_main = pd.read_excel(xls, sheet_name="DATABASE MERGE")
    df_main.columns = df_main.columns.astype(str).str.strip().str.upper()
    
    if "DETAIL" in [s.upper() for s in xls.sheet_names]:
        sheet_detail_name = next(s for s in xls.sheet_names if s.upper() == "DETAIL")
        df_detail = pd.read_excel(xls, sheet_name=sheet_detail_name)
        df_detail.columns = df_detail.columns.astype(str).str.strip().str.upper()
    else:
        df_detail = pd.DataFrame()
        
    return df_main, df_detail

try:
    df_raw, df_detail_raw = load_data()
    df = df_raw.copy()
    df_detail = df_detail_raw.copy()
except Exception as e:
    st.error(f"⚠️ Gagal memuat data dari cloud. Error: {e}")
    st.stop()

col_agenda = "AGENDA" if "AGENDA" in df.columns else df.columns[0]
col_pabrik = "PERUSAHAAN" if "PERUSAHAAN" in df.columns else ("PERUSAHAAN_KEP" if "PERUSAHAAN_KEP" in df.columns else df.columns[1])
col_pbck3 = "NO_PBCK-3" if "NO_PBCK-3" in df.columns else ("NO_PBCK_3" if "NO_PBCK_3" in df.columns else df.columns[0])
col_tgl_pbck3 = "TANGGAL_PBCK-3" if "TANGGAL_PBCK-3" in df.columns else "TANGGAL_PBCK3"
col_back3 = "BACK-3" if "BACK-3" in df.columns else df.columns[0]
col_tgl_back3 = "TANGGAL_BACK-3" if "TANGGAL_BACK-3" in df.columns else ("TGL_BACK-3" if "TGL_BACK-3" in df.columns else "TANGGAL BACK-3")
col_ck2 = "NO_CK-2" if "NO_CK-2" in df.columns else "NO_CK2"
col_tgl_ck2 = "TGL_CK-2" if "TGL_CK-2" in df.columns else "TGL_CK_2"

col_cukai_pbck3 = "TOTAL_CUKAI" if "TOTAL_CUKAI" in df.columns else ("TOTAL CUKAI" if "TOTAL CUKAI" in df.columns else df.columns[47])
col_cukai_ck2 = "CUKAI_MS" if "CUKAI_MS" in df.columns else ("CUKAI MS" if "CUKAI MS" in df.columns else col_cukai_pbck3)
col_biaya_pengganti = "JUMLAH_BP" if "JUMLAH_BP" in df.columns else ("JUMLAH BP" if "JUMLAH BP" in df.columns else df.columns[49])
col_bks_pbck3 = "TOTAL_BUNGKUS" if "TOTAL_BUNGKUS" in df.columns else "TOTAL BUNGKUS"
col_bks_ck2 = "TOTAL_BUNGKUS_MS" if "TOTAL_BUNGKUS_MS" in df.columns else "TOTAL BUNGKUS MS"

for c_date in [col_tgl_pbck3, col_tgl_back3, col_tgl_ck2]:
    if c_date in df.columns: df[c_date] = pd.to_datetime(df[c_date], errors='coerce')

if col_ck2 in df.columns:
    df['STATUS_CK2_BOOL'] = df[col_ck2].apply(lambda x: "TERBIT" if pd.notnull(x) and str(x).strip() != "" and str(x).strip().lower() != "nan" and str(x).strip() != "-" else "PROSES")
else:
    df['STATUS_CK2_BOOL'] = "PROSES"

if col_tgl_ck2 in df.columns:
    df['TAHUN_CK2'] = df[col_tgl_ck2].dt.year
    df['BULAN_CK2_ANGKA'] = df[col_tgl_ck2].dt.month
else:
    df['TAHUN_CK2'] = None
    df['BULAN_CK2_ANGKA'] = None

INDO_BULAN = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
df['BULAN_CK2_NAMA'] = df['BULAN_CK2_ANGKA'].map(INDO_BULAN)

def clean_num(series):
    def parse_value(x):
        if pd.isna(x): return 0
        if isinstance(x, (int, float)): return x
        x_str = str(x).replace("Rp", "").strip()
        x_str = x_str.replace(".", "").replace(",", ".")
        try:
            return float(x_str)
        except ValueError:
            return 0
    return series.apply(parse_value)

if col_cukai_pbck3 in df.columns: df[col_cukai_pbck3] = clean_num(df[col_cukai_pbck3])
if col_cukai_ck2 in df.columns: df[col_cukai_ck2] = clean_num(df[col_cukai_ck2])
if col_biaya_pengganti in df.columns: df[col_biaya_pengganti] = clean_num(df[col_biaya_pengganti])
if col_bks_pbck3 in df.columns: df[col_bks_pbck3] = clean_num(df[col_bks_pbck3])
if col_bks_ck2 in df.columns: df[col_bks_ck2] = clean_num(df[col_bks_ck2])

df['BUNGKUS_TMS'] = df[col_bks_pbck3] - df[col_bks_ck2]
df['BUNGKUS_TMS'] = df['BUNGKUS_TMS'].apply(lambda x: x if x > 0 else 0)

st.sidebar.markdown("### 🎛️ Filter Dasbor")
pabrik_list = ["Semua Pabrik"] + sorted(df[col_pabrik].dropna().unique().tolist())
selected_pabrik = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", pabrik_list)

tahun_tersedia = [2026]
if df['TAHUN_CK2'].dropna().nunique() > 0:
    tahun_tersedia = sorted(df['TAHUN_CK2'].dropna().unique().astype(int).tolist(), reverse=True)
selected_tahun = st.sidebar.selectbox("Pilih Tahun Anggaran:", tahun_tersedia)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗓️ Filter Periode Terbit CK-2")
mode_periode = st.sidebar.radio("Mode Periode:", ["Semua Periode (Total Tahunan)", "Bulanan Tunggal (Single Month)", "Kumulatif (s.d. Bulan)"])
selected_bulan_nama = "Agustus"
selected_bulan_angka = 8
list_12_bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

if mode_periode != "Semua Periode (Total Tahunan)":
    selected_bulan_nama = st.sidebar.selectbox("Pilih Bulan CK-2:", list_12_bulan, index=7)
    selected_bulan_angka = next(k for k, v in INDO_BULAN.items() if v == selected_bulan_nama)

df_filtered = df.copy()
if selected_pabrik != "Semua Pabrik": df_filtered = df_filtered[df_filtered[col_pabrik] == selected_pabrik]
if mode_periode == "Bulanan Tunggal (Single Month)":
    df_filtered = df_filtered[(df_filtered['TAHUN_CK2'] == selected_tahun) & (df_filtered['BULAN_CK2_ANGKA'] == selected_bulan_angka)]
elif mode_periode == "Kumulatif (s.d. Bulan)":
    df_filtered = df_filtered[(df_filtered['TAHUN_CK2'] == selected_tahun) & (df_filtered['BULAN_CK2_ANGKA'] <= selected_bulan_angka)]

total_pbck3 = df_filtered[col_pbck3].nunique() if col_pbck3 in df_filtered.columns else len(df_filtered)
total_ck2 = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"][col_ck2].nunique() if col_ck2 in df_filtered.columns else 0
total_outstanding = total_pbck3 - total_ck2
persen_selesai = (total_ck2 / total_pbck3 * 100) if total_pbck3 > 0 else 0

cukai_pbck3_val = df_filtered[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_filtered.columns else 0
cukai_ck2_val = df_filtered[col_cukai_ck2].sum() if col_cukai_ck2 in df_filtered.columns else 0
selisih_fisik = cukai_pbck3_val - cukai_ck2_val
biaya_pengganti = df_filtered[col_biaya_pengganti].sum() if col_biaya_pengganti in df_filtered.columns else 0
total_bks_pbck3 = df_filtered[col_bks_pbck3].sum() if col_bks_pbck3 in df_filtered.columns else 0
total_bks_ck2 = df_filtered[col_bks_ck2].sum() if col_bks_ck2 in df_filtered.columns else 0
total_bks_tms = total_bks_pbck3 - total_bks_ck2
total_bks_tms = total_bks_tms if total_bks_tms > 0 else 0

visual_periode_lbl = f"Tahun Anggaran {selected_tahun}"
if mode_periode == "Bulanan Tunggal (Single Month)": visual_periode_lbl = f"Bulan Realisasi {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)": visual_periode_lbl = f"Realisasi s.d. Bulan {selected_bulan_nama} {selected_tahun}"

# Regex banner info juga menyesuaikan
st.markdown(f"""
<div class="info-banner">
    📌 <b>Periode Terpantau:</b> <code>{visual_periode_lbl}</code> &nbsp;|&nbsp; 
    🏢 <b>Entitas:</b> <code>{selected_pabrik}</code> &nbsp;|&nbsp; 
    📄 <b>Status Rekonsiliasi:</b> {'<span class="badge-success">Fisik 100% Sesuai</span>' if selisih_fisik == 0 else f'<span class="badge-danger">Selisih Fisik: {fmt_rupiah(-selisih_fisik)} ({fmt_bungkus(total_bks_tms)} Bks TMS)</span>'}
</div>
""", unsafe_allow_html=True)

r1_c1, r1_c2, r1_c3 = st.columns(3)
with r1_c1:
    st.markdown(f"""<div class="kpi-card border-blue"><div class="kpi-header"><span class="kpi-label">Permohonan PBCK-3 Terlayani</span><span class="kpi-icon">📥</span></div><div class="kpi-value">{total_pbck3:,} <span style="font-size: 14px; color: #64748B;">Berkas</span></div><div class="kpi-subtext">Pengajuan permohonan periode terpilih</div></div>""", unsafe_allow_html=True)
with r1_c2:
    st.markdown(f"""<div class="kpi-card border-green"><div class="kpi-header"><span class="kpi-label">Realisasi CK-2 Terbit</span><span class="kpi-icon">📜</span></div><div class="kpi-value">{total_ck2:,} <span style="font-size: 14px; color: #64748B;">Dokumen</span></div><div class="kpi-subtext"><span class="badge-success">{persen_selesai:.1f}% Selesai</span> dokumen resmi diterbitkan</div></div>""", unsafe_allow_html=True)
with r1_c3:
    badge_ot = "badge-success" if total_outstanding == 0 else "badge-warning"
    st.markdown(f"""<div class="kpi-card border-amber"><div class="kpi-header"><span class="kpi-label">Outstanding (Dalam Proses)</span><span class="kpi-icon">⏳</span></div><div class="kpi-value">{total_outstanding:,} <span style="font-size: 14px; color: #64748B;">Dokumen</span></div><div class="kpi-subtext"><span class="{badge_ot}">{(total_outstanding/total_pbck3*100) if total_pbck3 > 0 else 0:.1f}% Beban Kerja</span> menunggu CK-2</div></div>""", unsafe_allow_html=True)

r2_c1, r2_c2, r2_c3 = st.columns(3)
with r2_c1:
    # Font dikecilkan dari 20px ke 18px supaya pas dengan teks tambahannya
    st.markdown(f"""<div class="kpi-card border-slate"><div class="kpi-header"><span class="kpi-label">Nilai Pengajuan (PBCK-3)</span><span class="kpi-icon">📋</span></div><div class="kpi-value" style="font-size: 18px;">{fmt_rupiah(cukai_pbck3_val)}</div><div class="kpi-subtext" style="margin-top: 4px;">Potensi nilai cukai pemberitahuan</div></div>""", unsafe_allow_html=True)
with r2_c2:
    badge_cukai = f'<span class="badge-danger">Selisih TMS: {fmt_rupiah(-selisih_fisik)}</span>' if selisih_fisik > 0 else '<span class="badge-success">100% Memenuhi Syarat</span>'
    st.markdown(f"""<div class="kpi-card border-green" style="background: #F0FDF4;"><div class="kpi-header"><span class="kpi-label" style="color: #047857;">Realisasi Cukai CK-2 (MS)</span><span class="kpi-icon">💸</span></div><div class="kpi-value" style="color: #065F46; font-size: 18px;">{fmt_rupiah(cukai_ck2_val)}</div><div class="kpi-subtext" style="margin-top: 4px;">{badge_cukai}</div></div>""", unsafe_allow_html=True)
with r2_c3:
    st.markdown(f"""<div class="kpi-card border-amber"><div class="kpi-header"><span class="kpi-label">Biaya Pengganti (BP) Pita Cukai</span><span class="kpi-icon">🏦</span></div><div class="kpi-value" style="color: #92400E; font-size: 18px;">{fmt_rupiah(biaya_pengganti)}</div><div class="kpi-subtext" style="margin-top: 4px;">Penerimaan Negara (PMK 113/2025)</div></div>""", unsafe_allow_html=True)

r3_c1, r3_c2, r3_c3 = st.columns(3)
with r3_c1:
    st.markdown(f"""<div class="kpi-card border-slate"><div class="kpi-header"><span class="kpi-label">Kemasan Diajukan (PBCK-3)</span><span class="kpi-icon">📦</span></div><div class="kpi-value" style="font-size: 18px;">{fmt_bungkus(total_bks_pbck3)} <span style="font-size: 13px; color: #64748B;">Bks</span></div><div class="kpi-subtext" style="margin-top: 4px;">Jumlah fisik awal yang diberitahukan</div></div>""", unsafe_allow_html=True)
with r3_c2:
    st.markdown(f"""<div class="kpi-card border-green"><div class="kpi-header"><span class="kpi-label" style="color: #047857;">Kemasan Disetujui (MS)</span><span class="kpi-icon">✅</span></div><div class="kpi-value" style="color: #065F46; font-size: 18px;">{fmt_bungkus(total_bks_ck2)} <span style="font-size: 13px; color: #047857;">Bks</span></div><div class="kpi-subtext" style="margin-top: 4px;"><span class="badge-success">Memenuhi Syarat Pengembalian</span></div></div>""", unsafe_allow_html=True)
with r3_c3:
    badge_tms = "badge-danger" if total_bks_tms > 0 else "badge-success"
    st.markdown(f"""<div class="kpi-card border-red"><div class="kpi-header"><span class="kpi-label" style="color: #B91C1C;">Kemasan Ditolak / TMS</span><span class="kpi-icon">❌</span></div><div class="kpi-value" style="color: #991B1B; font-size: 18px;">{fmt_bungkus(total_bks_tms)} <span style="font-size: 13px; color: #991B1B;">Bks</span></div><div class="kpi-subtext" style="margin-top: 4px;"><span class="{badge_tms}">{'Tidak Mendapat Pengembalian' if total_bks_tms > 0 else 'Nihil Selisih (0 Bks)'}</span></div></div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

col_chart1, col_chart2 = st.columns([6, 5])
with col_chart1:
    st.subheader("📈 Tren Realisasi CK-2 per Bulan")
    st.caption("Visualisasi volume dokumen yang resmi rampung terbit CK-2 sepanjang tahun.")
    df_terbit = df[df['STATUS_CK2_BOOL'] == "TERBIT"].copy()
    if not df_terbit.empty and 'BULAN_CK2_ANGKA' in df_terbit.columns:
        df_trend = df_terbit.dropna(subset=['BULAN_CK2_ANGKA']).groupby('BULAN_CK2_ANGKA').agg(CK2=(col_ck2, 'nunique')).reset_index()
        df_trend['BULAN'] = df_trend['BULAN_CK2_ANGKA'].map(INDO_BULAN)
        df_trend = df_trend.sort_values(by='BULAN_CK2_ANGKA')
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=df_trend['BULAN'], y=df_trend['CK2'], name='Dokumen CK-2 Terbit', marker_color='#1E3A8A', text=df_trend['CK2'], textposition='auto'))
        fig_trend.update_layout(xaxis_title="Bulan Terbit CK-2", yaxis_title="Jumlah Dokumen", height=320, margin=dict(t=15, b=15, l=10, r=10))
        st.plotly_chart(fig_trend, use_container_width=True)
    else: st.info("Belum ada data dokumen CK-2 yang berstatus TERBIT.")

with col_chart2:
    st.subheader("📊 Kontribusi Realisasi Nilai Cukai (CK-2)")
    st.caption("Distribusi nilai pengembalian cukai yang memenuhi syarat (MS) per pabrik.")
    if col_pabrik in df_filtered.columns and col_cukai_ck2 in df_filtered.columns and not df_filtered.empty:
        df_pabrik_grp = df_filtered.groupby(col_pabrik)[col_cukai_ck2].sum().reset_index()
        df_pabrik_grp = df_pabrik_grp[df_pabrik_grp[col_cukai_ck2] > 0].sort_values(by=col_cukai_ck2, ascending=False).head(5)
        if not df_pabrik_grp.empty:
            fig_pie = px.pie(df_pabrik_grp, names=col_pabrik, values=col_cukai_ck2, color_discrete_sequence=px.colors.sequential.Blues_r, hole=0.45)
            fig_pie.update_traces(hovertemplate="<b>%{label}</b><br>Nilai Cukai: Rp %{value:,.0f}<br>Porsi: %{percent}<extra></extra>")
            fig_pie.update_layout(height=320, margin=dict(t=15, b=15, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        else: st.info("Belum ada realisasi nilai CK-2 pada filter ini.")
    else: st.info("Data belum tersedia untuk grafik kontribusi.")

st.markdown("---")
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
            else: st.success("🟢 Bebas Overdue! Semua berkas dalam batas waktu yang sah.")
        with col_warn2:
            if not critical_items.empty:
                st.warning(f"🟡 **{len(critical_items)} Berkas Jatuh Tempo H-3 atau Kurang!**")
                st.dataframe(critical_items[[col_pabrik, col_pbck3, col_tempo]], hide_index=True, use_container_width=True)
            else: st.info("🔵 Bagus! Belum ada berkas dalam proses yang mendekati masa kritis (≤ 3 Hari).")
    else: st.success("🎉 Seluruh dokumen periode ini sudah selesai diproses (terbit CK-2).")
else: st.info("Data jatuh tempo (SLA) belum termuat dalam database.")

st.markdown("---")
st.subheader("📑 Detail Data Transaksi (Ter-filter)")
df_display = df_filtered.copy()

if not df_display.empty:
    df_display["TGL_PBCK-3_STR"] = df_display[col_tgl_pbck3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_pbck3 in df_display.columns else "-"
    df_display["TGL_BACK-3_STR"] = df_display[col_tgl_back3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_back3 in df_display.columns else "-"
    df_display["TGL_CK-2_STR"] = df_display[col_tgl_ck2].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_ck2 in df_display.columns else "-"
    
    df_display["CUKAI_PENGAJUAN"] = df_display[col_cukai_pbck3].apply(lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notnull(x) and x != 0 else "Rp 0")
    df_display["CUKAI_REALISASI_CK2"] = df_display[col_cukai_ck2].apply(lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notnull(x) and x != 0 else "Rp 0")
    df_display["BIAYA_PENGGANTI_STR"] = df_display[col_biaya_pengganti].apply(lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notnull(x) and x != 0 else "Rp 0")
    df_display["BKS_DIAJUKAN"] = df_display[col_bks_pbck3].apply(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notnull(x) and x != 0 else "0")
    df_display["BKS_DISETUJUI_MS"] = df_display[col_bks_ck2].apply(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notnull(x) and x != 0 else "0")
    df_display["BKS_DITOLAK_TMS"] = df_display['BUNGKUS_TMS'].apply(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notnull(x) and x != 0 else "0")

    col_agenda_main = "AGENDA" if "AGENDA" in df_display.columns else df_display.columns[0]

    rename_map = {
        col_agenda_main: "Agenda", col_pabrik: "Perusahaan", col_pbck3: "No. PBCK-3", "TGL_PBCK-3_STR": "Tgl PBCK-3",
        "BKS_DIAJUKAN": "Bks Diajukan", "BKS_DISETUJUI_MS": "Bks Disetujui (MS)", "BKS_DITOLAK_TMS": "Bks Ditolak (TMS)",
        "CUKAI_PENGAJUAN": "Cukai Diajukan (PBCK-3)", "CUKAI_REALISASI_CK2": "Realisasi Cukai (CK-2)", "BIAYA_PENGGANTI_STR": "Biaya Pengganti",
        col_back3: "No. BACK-3", "TGL_BACK-3_STR": "Tgl BACK-3", col_ck2: "No. CK-2", "TGL_CK-2_STR": "Tgl CK-2"
    }
    
    kolom_final = [
        col_agenda_main, col_pabrik, col_pbck3, "TGL_PBCK-3_STR", 
        "BKS_DIAJUKAN", "BKS_DISETUJUI_MS", "BKS_DITOLAK_TMS",
        "CUKAI_PENGAJUAN", "CUKAI_REALISASI_CK2", "BIAYA_PENGGANTI_STR",
        col_back3, "TGL_BACK-3_STR", col_ck2, "TGL_CK-2_STR"
    ]
    df_tabel_rapi = df_display[kolom_final].rename(columns=rename_map)
    df_tabel_rapi = df_tabel_rapi.sort_values(by="Tgl PBCK-3", ascending=False).reset_index(drop=True)
    
    tabel_event = st.dataframe(
        df_tabel_rapi, 
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",           
        selection_mode="single-row"  
    )

    selected_rows = tabel_event.selection.rows
    if selected_rows:
        idx = selected_rows[0]
        selected_agenda = df_tabel_rapi.iloc[idx]["Agenda"]
        selected_pbck3 = df_tabel_rapi.iloc[idx]["No. PBCK-3"]
        
        st.markdown(f"### 🔍 Rincian Item untuk Dokumen: `{selected_pbck3}` (Agenda: {selected_agenda})")
        
        if not df_detail.empty:
            col_dtl_agenda = "AGENDA" if "AGENDA" in df_detail.columns else df_detail.columns[0]
            detail_filtered = df_detail[df_detail[col_dtl_agenda].astype(str) == str(selected_agenda)].copy()
            
            if not detail_filtered.empty:
                kolom_dibuang = [
                    "TOTAL CUKAI PEMBERITAHUAN", "TOTAL CUKAI MS", 
                    "NO", "MOR", "↑ MOR", 
                    "BUNGKUS", "BP SERI I", "BUNGKUS.1", "BP SERI II", 
                    "BUNGKUS.2", "BP SERI III-TP", "BUNGKUS.3", "BP SERI III-DP", 
                    "BUNGKUS.4", "BP SERI MMEA", "TOTAL BP",
                    "JUMLAH MS (BUNGKUS)", "NILAI CUKAI PEMBERITAHUAN", "NILAI CUKAI MS"
                ]
                
                cols_to_keep = [
                    c for c in detail_filtered.columns 
                    if not str(c).strip().upper().startswith("UNNAMED") 
                    and str(c).strip().upper() not in kolom_dibuang
                ]
                detail_filtered = detail_filtered[cols_to_keep]

                cols = list(detail_filtered.columns)
                ck2_col = next((c for c in cols if str(c).strip().upper() == "NILAI CK-2"), None)
                
                if ck2_col:
                    cols.remove(ck2_col)
                    insert_idx = len(cols)
                    for i, c in enumerate(cols):
                        c_up = str(c).upper()
                        if "CUKAI" in c_up and "BACK-3" in c_up:
                            insert_idx = i + 1
                            break
                    cols.insert(insert_idx, ck2_col)
                    detail_filtered = detail_filtered[cols]
                    detail_filtered = detail_filtered.rename(columns={ck2_col: "NILAI CK-2"})
                
                for col in detail_filtered.columns:
                    if pd.api.types.is_numeric_dtype(detail_filtered[col]):
                        detail_filtered[col] = detail_filtered[col].apply(
                            lambda x: f"{x:,.0f}".replace(",", ".") if pd.notnull(x) else "0"
                        )
                
                if "NILAI CK-2" in detail_filtered.columns and len(detail_filtered) > 1:
                    vals = detail_filtered["NILAI CK-2"].tolist()
                    new_vals = [vals[0]] + [""] * (len(vals) - 1)
                    detail_filtered["NILAI CK-2"] = new_vals
                
                st.dataframe(detail_filtered, use_container_width=True, hide_index=True)
            else:
                st.info(f"Tidak ada rincian tambahan di sheet 'Detail' untuk Agenda {selected_agenda}.")
        else:
            st.warning("Sheet bernama 'Detail' tidak ditemukan di database.")
    else:
        st.caption("💡 *Klik pada salah satu baris di tabel atas untuk memunculkan rincian item (Sheet Detail).*")

else:
    st.info("Tidak ada berkas yang terbit CK-2 pada periode / filter yang dipilih.")
