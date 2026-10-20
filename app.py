import re
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
        margin-bottom: 12px; transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.25s ease;
        &:hover { transform: translateY(-3px); box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.1); border-color: transparent; }
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.1);
        border-color: transparent;
    }
    .border-blue, .border-blue:hover { border-left: 5px solid #1E3A8A; }
    .border-green, .border-green:hover { border-left: 5px solid #059669; }
    .border-amber, .border-amber:hover { border-left: 5px solid #D97706; }
    .border-slate, .border-slate:hover { border-left: 5px solid #475569; }
    .border-red, .border-red:hover { border-left: 5px solid #DC2626; }
    .kpi-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .kpi-label { font-size: 11px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: #64748B; }
    .kpi-icon { font-size: 16px; }
    .kpi-value { font-size: 21px; font-weight: 800; color: #0F172A; line-height: 1.2; margin-bottom: 4px; }
    .kpi-subtext { font-size: 11px; font-weight: 500; color: #64748B; }
    .badge-success { background-color: #ECFDF5; color: #047857; padding: 2px 7px; border-radius: 9999px; font-size: 10px; font-weight: 700; }
    .badge-warning { background-color: #FFFBEB; color: #B45309; padding: 2px 7px; border-radius: 9999px; font-size: 10px; font-weight: 700; }
    .badge-danger { background-color: #FEF2F2; color: #B91C1C; padding: 2px 7px; border-radius: 9999px; font-size: 10px; font-weight: 700; }
    .badge-info { background-color: #EFF6FF; color: #1D4ED8; padding: 2px 7px; border-radius: 9999px; font-size: 10px; font-weight: 700; }
    .info-banner { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 16px; margin-bottom: 18px; font-size: 13px; color: #334155; }
</style>
""", unsafe_allow_html=True)

# ---- PEMBERSIH ID DOKUMEN (Anti .000000 & Sinkronisasi Key) ----
def clean_doc_id(series):
    def _clean(x):
        if pd.isna(x): return "-"
        s = re.sub(r'\.0+$', '', str(x).strip())
        if s.lower() in ["", "nan", "none", "nat", "-"]: return "-"
        return s
    return series.map(_clean)

# ---- FORMATTER BANNER & TABEL (Kompatibel untuk .map Vektorisasi) ----
def fmt_exact_rp(val):
    if pd.isna(val) or val == 0: return "Rp 0"
    return f"-Rp {abs(val):,.0f}".replace(",", ".") if val < 0 else f"Rp {abs(val):,.0f}".replace(",", ".")

def fmt_exact_bks(val):
    if pd.isna(val) or val == 0: return "0"
    return f"-{abs(val):,.0f}".replace(",", ".") if val < 0 else f"{abs(val):,.0f}".replace(",", ".")

# ---- FORMATTER KPI CARDS (Stacking Vertikal) ----
def fmt_kpi_rupiah(val):
    if pd.isna(val) or val == 0: return "Rp 0"
    is_negative = val < 0
    val = abs(val)
    real_str = f"Rp {val:,.0f}".replace(",", ".")
    
    if val >= 1_000_000_000_000: alias = f"{val/1_000_000_000_000:.2f} Triliun".replace(".", ",")
    elif val >= 1_000_000_000: alias = f"{val/1_000_000_000:.2f} Miliar".replace(".", ",")
    elif val >= 1_000_000: alias = f"{val/1_000_000:.2f} Juta".replace(".", ",")
    else: return f"-{real_str}" if is_negative else real_str
        
    final_str = f"{real_str}<div style='font-size: 13px; color: #64748B; font-weight: 700; margin-top: 2px;'>≈ {alias}</div>"
    return f"-{final_str}" if is_negative else final_str

def fmt_kpi_bungkus(val):
    if pd.isna(val) or val == 0: return "0 <span style='font-size: 13px; font-weight: 500;'>Bks</span>"
    is_negative = val < 0
    val = abs(val)
    real_str = f"{val:,.0f}".replace(",", ".")
    
    if val >= 1_000_000_000: alias = f"{val/1_000_000_000:.2f} M".replace(".", ",")
    elif val >= 1_000_000: alias = f"{val/1_000_000:.2f} Jt".replace(".", ",")
    else: 
        base = f"{real_str} <span style='font-size: 13px; font-weight: 500;'>Bks</span>"
        return f"-{base}" if is_negative else base
        
    final_str = f"{real_str} <span style='font-size: 13px; font-weight: 500;'>Bks</span><div style='font-size: 13px; color: #64748B; font-weight: 700; margin-top: 2px;'>≈ {alias} Bks</div>"
    return f"-{final_str}" if is_negative else final_str

LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"
col_logo, col_header = st.columns([1, 8])
with col_logo:
    st.markdown(
        f'<img src="{LOGO_URL}" width="78" referrerpolicy="no-referrer" style="margin-top: 4px;" onerror="this.style.display=\'none\'">',
        unsafe_allow_html=True
    )
with col_header:
    st.markdown("""
    <h2 style='margin-bottom: 2px; color: #1e3a8a; font-weight: 800;'>📊 EXECUTIVE DASHBOARD PBCK-3 & REALISASI CUKAI</h2>
    <p style='margin-top: 0px; color: #64748b; font-size: 14px;'>
    Monitoring Pelayanan Pengolahan Kembali & Pemusnahan BKC — KPPBC Tipe Madya Cukai Malang<br>
    <b>Landasan Hukum: Peraturan Menteri Keuangan No. 113/2025 & PER-2/BC/2026</b>
    </p>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner="Memuat Database Realisasi...")
def load_data():
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    with pd.ExcelFile(url_merge) as xls:
        df_main = pd.read_excel(xls, sheet_name="DATABASE MERGE")
        df_main.columns = df_main.columns.astype(str).str.strip().str.upper()
        
        sheet_map = {s.strip().upper(): s for s in xls.sheet_names}
        if "DETAIL" in sheet_map:
            df_detail = pd.read_excel(xls, sheet_name=sheet_map["DETAIL"])
            df_detail.columns = df_detail.columns.astype(str).str.strip().str.upper()
            valid_cols = [c for c in df_detail.columns if not c.startswith("UNNAMED")]
            df_detail = df_detail[valid_cols]
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
col_back3 = "BACK-3" if "BACK-3" in df.columns else ("NO_BACK-3" if "NO_BACK-3" in df.columns else df.columns[0])
col_tgl_back3 = "TANGGAL_BACK-3" if "TANGGAL_BACK-3" in df.columns else ("TGL_BACK-3" if "TGL_BACK-3" in df.columns else "TANGGAL BACK-3")
col_ck2 = "NO_CK-2" if "NO_CK-2" in df.columns else "NO_CK2"
col_tgl_ck2 = "TGL_CK-2" if "TGL_CK-2" in df.columns else "TGL_CK_2"

col_cukai_pbck3 = "TOTAL_CUKAI" if "TOTAL_CUKAI" in df.columns else ("TOTAL CUKAI" if "TOTAL CUKAI" in df.columns else df.columns[47])
col_cukai_ck2 = "CUKAI_MS" if "CUKAI_MS" in df.columns else ("CUKAI MS" if "CUKAI MS" in df.columns else col_cukai_pbck3)
col_biaya_pengganti = "JUMLAH_BP" if "JUMLAH_BP" in df.columns else ("JUMLAH BP" if "JUMLAH BP" in df.columns else df.columns[49])
col_bks_pbck3 = "TOTAL_BUNGKUS" if "TOTAL_BUNGKUS" in df.columns else "TOTAL BUNGKUS"
col_bks_ck2 = "TOTAL_BUNGKUS_MS" if "TOTAL_BUNGKUS_MS" in df.columns else "TOTAL BUNGKUS MS"

# ---- TERAPKAN PEMBERSIH ID DOKUMEN PADA DF & DF_DETAIL ----
for c_id in [col_agenda, col_pbck3, col_back3, col_ck2]:
    if c_id in df.columns:
        df[c_id] = clean_doc_id(df[c_id])

if not df_detail.empty:
    for c_dtl_id in ["AGENDA", "NO_PBCK-3", "NO_PBCK_3", "BACK-3", "NO_BACK-3", "NO_CK-2", "NO_CK2"]:
        if c_dtl_id in df_detail.columns:
            df_detail[c_dtl_id] = clean_doc_id(df_detail[c_dtl_id])

for c_date in [col_tgl_pbck3, col_tgl_back3, col_tgl_ck2]:
    if c_date in df.columns: df[c_date] = pd.to_datetime(df[c_date], errors='coerce')

if col_ck2 in df.columns:
    df['STATUS_CK2_BOOL'] = "PROSES"
    df.loc[df[col_ck2] != "-", 'STATUS_CK2_BOOL'] = "TERBIT"
else:
    df['STATUS_CK2_BOOL'] = "PROSES"

if col_tgl_ck2 in df.columns:
    df['TAHUN_CK2'] = df[col_tgl_ck2].dt.year
    df['BULAN_CK2_ANGKA'] = df[col_tgl_ck2].dt.month
else:
    df['TAHUN_CK2'] = pd.Series(dtype='float64')
    df['BULAN_CK2_ANGKA'] = pd.Series(dtype='float64')

if col_tgl_pbck3 in df.columns:
    df['TAHUN_PBCK3'] = df[col_tgl_pbck3].dt.year
    df['BULAN_PBCK3_ANGKA'] = df[col_tgl_pbck3].dt.month
else:
    df['TAHUN_PBCK3'] = pd.Series(dtype='float64')
    df['BULAN_PBCK3_ANGKA'] = pd.Series(dtype='float64')

# ---- KOLOM BANTU TAHUN & BULAN EFEKTIF (Anti-Hilang Berkas Outstanding) ----
df['TAHUN_EFEKTIF'] = df['TAHUN_CK2'].fillna(df['TAHUN_PBCK3'])
df['BULAN_EFEKTIF'] = df['BULAN_CK2_ANGKA'].fillna(df['BULAN_PBCK3_ANGKA'])

INDO_BULAN = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus', 9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
df['BULAN_CK2_NAMA'] = df['BULAN_CK2_ANGKA'].map(INDO_BULAN)

def clean_num(series):
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0)
    def parse_value(x):
        if pd.isna(x): return 0
        if isinstance(x, (int, float)): return x
        x_str = str(x).replace("Rp", "").strip().replace(".", "").replace(",", ".")
        try:
            return float(x_str)
        except ValueError:
            return 0
    return series.map(parse_value)

if col_cukai_pbck3 in df.columns: df[col_cukai_pbck3] = clean_num(df[col_cukai_pbck3])
if col_cukai_ck2 in df.columns: df[col_cukai_ck2] = clean_num(df[col_cukai_ck2])
if col_biaya_pengganti in df.columns: df[col_biaya_pengganti] = clean_num(df[col_biaya_pengganti])
if col_bks_pbck3 in df.columns: df[col_bks_pbck3] = clean_num(df[col_bks_pbck3])
if col_bks_ck2 in df.columns: df[col_bks_ck2] = clean_num(df[col_bks_ck2])

df['BUNGKUS_TMS'] = (df[col_bks_pbck3] - df[col_bks_ck2]).clip(lower=0)

st.sidebar.markdown("### 🎛️ Filter Dasbor")
pabrik_list = ["Semua Pabrik"] + sorted([p for p in df[col_pabrik].dropna().unique().tolist() if str(p).strip() not in ["", "-"]])
selected_pabrik = st.sidebar.selectbox("Pilih Pabrik / Perusahaan:", pabrik_list)

tahun_tersedia = [2026]
if df['TAHUN_EFEKTIF'].dropna().nunique() > 0:
    tahun_tersedia = sorted(df['TAHUN_EFEKTIF'].dropna().unique().astype(int).tolist(), reverse=True)
selected_tahun = st.sidebar.selectbox("Pilih Tahun Anggaran:", tahun_tersedia)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗓️ Filter Periode Terbit CK-2")
mode_periode = st.sidebar.radio("Mode Periode:", ["Semua Periode (Total Tahunan)", "Bulanan Tunggal (Single Month)", "Kumulatif (s.d. Bulan)"])

# ---- DINAMISASI FILTER WAKTU DEFAULT BERDASARKAN DATETIME.NOW() ----
current_month_num = datetime.now().month
selected_bulan_angka = current_month_num
selected_bulan_nama = INDO_BULAN.get(current_month_num, "Januari")
list_12_bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

if mode_periode != "Semua Periode (Total Tahunan)":
    selected_bulan_nama = st.sidebar.selectbox("Pilih Bulan CK-2:", list_12_bulan, index=current_month_num - 1)
    selected_bulan_angka = next(k for k, v in INDO_BULAN.items() if v == selected_bulan_nama)

# ---- LOGIKA FILTER PERIODE AKUNTABEL (Menjaga Berkas Outstanding Tetap Terpantau) ----
df_filtered = df.copy()
if selected_pabrik != "Semua Pabrik":
    df_filtered = df_filtered[df_filtered[col_pabrik] == selected_pabrik]

is_terbit = df_filtered['STATUS_CK2_BOOL'] == "TERBIT"
is_proses = df_filtered['STATUS_CK2_BOOL'] == "PROSES"

if mode_periode == "Semua Periode (Total Tahunan)":
    cond_terbit = is_terbit & (df_filtered['TAHUN_CK2'] == selected_tahun)
    cond_proses = is_proses & ((df_filtered['TAHUN_EFEKTIF'] == selected_tahun) | df_filtered['TAHUN_EFEKTIF'].isna())
    df_filtered = df_filtered[cond_terbit | cond_proses]
elif mode_periode == "Bulanan Tunggal (Single Month)":
    cond_terbit = is_terbit & (df_filtered['TAHUN_CK2'] == selected_tahun) & (df_filtered['BULAN_CK2_ANGKA'] == selected_bulan_angka)
    cond_proses = is_proses & (
        ((df_filtered['TAHUN_EFEKTIF'] == selected_tahun) & (df_filtered['BULAN_EFEKTIF'] == selected_bulan_angka)) |
        df_filtered['TAHUN_EFEKTIF'].isna()
    )
    df_filtered = df_filtered[cond_terbit | cond_proses]
elif mode_periode == "Kumulatif (s.d. Bulan)":
    cond_terbit = is_terbit & (df_filtered['TAHUN_CK2'] == selected_tahun) & (df_filtered['BULAN_CK2_ANGKA'] <= selected_bulan_angka)
    cond_proses = is_proses & (
        ((df_filtered['TAHUN_EFEKTIF'] == selected_tahun) & (df_filtered['BULAN_EFEKTIF'] <= selected_bulan_angka)) |
        df_filtered['TAHUN_EFEKTIF'].isna()
    )
    df_filtered = df_filtered[cond_terbit | cond_proses]

# ---- PERHITUNGAN METRIK UTAMA & RATA-RATA KECEPATAN LAYANAN (SLA) ----
valid_pbck3 = df_filtered[df_filtered[col_pbck3] != "-"][col_pbck3] if col_pbck3 in df_filtered.columns else pd.Series(dtype='str')
total_pbck3 = valid_pbck3.nunique() if not valid_pbck3.empty else len(df_filtered)

df_terbit_filtered = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"]
total_ck2 = df_terbit_filtered[df_terbit_filtered[col_ck2] != "-"][col_ck2].nunique() if col_ck2 in df_filtered.columns else 0
total_outstanding = max(total_pbck3 - total_ck2, int((df_filtered['STATUS_CK2_BOOL'] == "PROSES").sum()))
persen_selesai = (total_ck2 / total_pbck3 * 100) if total_pbck3 > 0 else 0

# Rata-rata Hari Penyelesaian BACK-3 ke CK-2
avg_sla_str = "- Hari"
badge_sla_card = '<span class="badge-info">⚡ SLA: - Hari</span>'
if not df_terbit_filtered.empty and col_tgl_ck2 in df_terbit_filtered.columns and col_tgl_back3 in df_terbit_filtered.columns:
    sla_days = (df_terbit_filtered[col_tgl_ck2] - df_terbit_filtered[col_tgl_back3]).dt.days.dropna()
    sla_days = sla_days[sla_days >= 0]
    if not sla_days.empty:
        avg_sla_val = sla_days.mean()
        avg_sla_fmt = f"{avg_sla_val:.1f}".replace(".", ",")
        avg_sla_str = f"{avg_sla_fmt} Hari"
        sla_cls = "badge-success" if avg_sla_val <= 10 else "badge-danger"
        badge_sla_card = f'<span class="{sla_cls}">⚡ Rata-rata SLA: {avg_sla_str}</span>'

cukai_pbck3_val = df_filtered[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_filtered.columns else 0
cukai_ck2_val = df_filtered[col_cukai_ck2].sum() if col_cukai_ck2 in df_filtered.columns else 0
selisih_fisik = cukai_pbck3_val - cukai_ck2_val
biaya_pengganti = df_filtered[col_biaya_pengganti].sum() if col_biaya_pengganti in df_filtered.columns else 0
total_bks_pbck3 = df_filtered[col_bks_pbck3].sum() if col_bks_pbck3 in df_filtered.columns else 0
total_bks_ck2 = df_filtered[col_bks_ck2].sum() if col_bks_ck2 in df_filtered.columns else 0
total_bks_tms = max(total_bks_pbck3 - total_bks_ck2, 0)

visual_periode_lbl = f"Tahun Anggaran {selected_tahun}"
if mode_periode == "Bulanan Tunggal (Single Month)": visual_periode_lbl = f"Bulan Realisasi {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)": visual_periode_lbl = f"Realisasi s.d. Bulan {selected_bulan_nama} {selected_tahun}"

st.markdown(f"""
<div class="info-banner">
    📌 <b>Periode Terpantau:</b> <code>{visual_periode_lbl}</code> &nbsp;|&nbsp; 
    🏢 <b>Entitas:</b> <code>{selected_pabrik}</code> &nbsp;|&nbsp; 
    ⚡ <b>Rata-rata SLA:</b> <span class="badge-info">{avg_sla_str} dari batas 10 Hari Kerja</span> &nbsp;|&nbsp; 
    📄 <b>Status Rekonsiliasi:</b> {'<span class="badge-success">Fisik 100% Sesuai</span>' if selisih_fisik == 0 else f'<span class="badge-danger">Selisih Fisik: {fmt_exact_rp(-selisih_fisik)} ({fmt_exact_bks(total_bks_tms)} Bks TMS)</span>'}
</div>
""", unsafe_allow_html=True)

r1_c1, r1_c2, r1_c3 = st.columns(3)
with r1_c1:
    st.markdown(f"""<div class="kpi-card border-blue"><div class="kpi-header"><span class="kpi-label">Permohonan PBCK-3 Terlayani</span><span class="kpi-icon">📥</span></div><div class="kpi-value">{total_pbck3:,.0f} <span style="font-size: 14px; color: #64748B;">Berkas</span></div><div class="kpi-subtext">Pengajuan permohonan periode terpilih</div></div>""".replace(",", "."), unsafe_allow_html=True)
with r1_c2:
    st.markdown(f"""<div class="kpi-card border-green"><div class="kpi-header"><span class="kpi-label">Realisasi CK-2 Terbit</span><span class="kpi-icon">📜</span></div><div class="kpi-value">{total_ck2:,.0f} <span style="font-size: 14px; color: #64748B;">Dokumen</span></div><div class="kpi-subtext"><span class="badge-success">{persen_selesai:.1f}% Selesai</span> &nbsp;{badge_sla_card}</div></div>""".replace(",", "."), unsafe_allow_html=True)
with r1_c3:
    badge_ot = "badge-success" if total_outstanding == 0 else "badge-warning"
    st.markdown(f"""<div class="kpi-card border-amber"><div class="kpi-header"><span class="kpi-label">Outstanding (Dalam Proses)</span><span class="kpi-icon">⏳</span></div><div class="kpi-value">{total_outstanding:,.0f} <span style="font-size: 14px; color: #64748B;">Dokumen</span></div><div class="kpi-subtext"><span class="{badge_ot}">{(total_outstanding/total_pbck3*100) if total_pbck3 > 0 else 0:.1f}% Beban Kerja</span> menunggu CK-2</div></div>""".replace(",", "."), unsafe_allow_html=True)

r2_c1, r2_c2, r2_c3 = st.columns(3)
with r2_c1:
    st.markdown(f"""<div class="kpi-card border-slate"><div class="kpi-header"><span class="kpi-label">Nilai Pengajuan (PBCK-3)</span><span class="kpi-icon">📋</span></div><div class="kpi-value" style="font-size: 19px;">{fmt_kpi_rupiah(cukai_pbck3_val)}</div><div class="kpi-subtext" style="margin-top: 4px;">Potensi nilai cukai pemberitahuan</div></div>""", unsafe_allow_html=True)
with r2_c2:
    badge_cukai = f'<span class="badge-danger">Selisih TMS: {fmt_exact_rp(-selisih_fisik)}</span>' if selisih_fisik > 0 else '<span class="badge-success">100% Memenuhi Syarat</span>'
    st.markdown(f"""<div class="kpi-card border-green" style="background: #F0FDF4;"><div class="kpi-header"><span class="kpi-label" style="color: #047857;">Realisasi Cukai CK-2 (MS)</span><span class="kpi-icon">💸</span></div><div class="kpi-value" style="color: #065F46; font-size: 19px;">{fmt_kpi_rupiah(cukai_ck2_val)}</div><div class="kpi-subtext" style="margin-top: 4px;">{badge_cukai}</div></div>""", unsafe_allow_html=True)
with r2_c3:
    st.markdown(f"""<div class="kpi-card border-amber"><div class="kpi-header"><span class="kpi-label">Biaya Pengganti (BP) Pita Cukai</span><span class="kpi-icon">🏦</span></div><div class="kpi-value" style="color: #92400E; font-size: 19px;">{fmt_kpi_rupiah(biaya_pengganti)}</div><div class="kpi-subtext" style="margin-top: 4px;">Penerimaan Negara (PMK 113/2025)</div></div>""", unsafe_allow_html=True)

r3_c1, r3_c2, r3_c3 = st.columns(3)
with r3_c1:
    st.markdown(f"""<div class="kpi-card border-slate"><div class="kpi-header"><span class="kpi-label">Kemasan Diajukan (PBCK-3)</span><span class="kpi-icon">📦</span></div><div class="kpi-value" style="font-size: 19px;">{fmt_kpi_bungkus(total_bks_pbck3)}</div><div class="kpi-subtext" style="margin-top: 4px;">Jumlah fisik awal yang diberitahukan</div></div>""", unsafe_allow_html=True)
with r3_c2:
    st.markdown(f"""<div class="kpi-card border-green"><div class="kpi-header"><span class="kpi-label" style="color: #047857;">Kemasan Disetujui (MS)</span><span class="kpi-icon">✅</span></div><div class="kpi-value" style="color: #065F46; font-size: 19px;">{fmt_kpi_bungkus(total_bks_ck2)}</div><div class="kpi-subtext" style="margin-top: 4px;"><span class="badge-success">Memenuhi Syarat Pengembalian</span></div></div>""", unsafe_allow_html=True)
with r3_c3:
    badge_tms = "badge-danger" if total_bks_tms > 0 else "badge-success"
    st.markdown(f"""<div class="kpi-card border-red"><div class="kpi-header"><span class="kpi-label" style="color: #B91C1C;">Kemasan Ditolak / TMS</span><span class="kpi-icon">❌</span></div><div class="kpi-value" style="color: #991B1B; font-size: 19px;">{fmt_kpi_bungkus(total_bks_tms)}</div><div class="kpi-subtext" style="margin-top: 4px;"><span class="{badge_tms}">{'Tidak Mendapat Pengembalian' if total_bks_tms > 0 else 'Nihil Selisih (0 Bks)'}</span></div></div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

col_chart1, col_chart2 = st.columns([6, 5])
with col_chart1:
    st.subheader("📈 Tren Realisasi CK-2 per Bulan")
    st.caption(f"Visualisasi volume dokumen & nilai cukai CK-2 terbit sepanjang Tahun {selected_tahun} ({selected_pabrik}).")
    df_terbit_trend = df[df['STATUS_CK2_BOOL'] == "TERBIT"].copy()
    if selected_pabrik != "Semua Pabrik":
        df_terbit_trend = df_terbit_trend[df_terbit_trend[col_pabrik] == selected_pabrik]
    if 'TAHUN_CK2' in df_terbit_trend.columns:
        df_terbit_trend = df_terbit_trend[df_terbit_trend['TAHUN_CK2'] == selected_tahun]

    if not df_terbit_trend.empty and 'BULAN_CK2_ANGKA' in df_terbit_trend.columns:
        df_trend = (
            df_terbit_trend.dropna(subset=['BULAN_CK2_ANGKA'])
            .groupby('BULAN_CK2_ANGKA')
            .agg(CK2=(col_ck2, 'nunique'), TOTAL_CUKAI=(col_cukai_ck2, 'sum'))
            .reset_index()
        )
        df_trend['BULAN_CK2_ANGKA'] = df_trend['BULAN_CK2_ANGKA'].astype(int)
        df_trend['BULAN'] = df_trend['BULAN_CK2_ANGKA'].map(INDO_BULAN)
        df_trend = df_trend.sort_values(by='BULAN_CK2_ANGKA')
        df_trend['CUKAI_STR'] = df_trend['TOTAL_CUKAI'].map(fmt_exact_rp)

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=df_trend['BULAN'],
            y=df_trend['CK2'],
            name='Dokumen CK-2 Terbit',
            marker_color='#1E3A8A',
            text=df_trend['CK2'],
            textposition='auto',
            customdata=df_trend['CUKAI_STR'],
            hovertemplate="<b>Bulan %{x}</b><br>Dokumen CK-2: %{y} Dokumen<br>Total Nilai Cukai: %{customdata}<extra></extra>"
        ))
        fig_trend.add_trace(go.Scatter(
            x=df_trend['BULAN'],
            y=df_trend['TOTAL_CUKAI'],
            name='Nilai Cukai (Rp)',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='#059669', width=2.5),
            marker=dict(size=7, color='#059669'),
            customdata=df_trend['CUKAI_STR'],
            hovertemplate="<b>Bulan %{x}</b><br>Realisasi Cukai: %{customdata}<extra></extra>"
        ))
        fig_trend.update_layout(
            xaxis_title="Bulan Terbit CK-2",
            yaxis=dict(title="Jumlah Dokumen"),
            yaxis2=dict(title="Nilai Cukai (Rp)", overlaying='y', side='right', showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=340,
            margin=dict(t=30, b=15, l=10, r=10)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Belum ada data dokumen CK-2 yang berstatus TERBIT pada filter pabrik/tahun ini.")

with col_chart2:
    st.subheader("📊 Kontribusi Realisasi Nilai Cukai (CK-2)")
    st.caption("Distribusi nilai pengembalian cukai yang memenuhi syarat (MS) per pabrik.")
    if col_pabrik in df_filtered.columns and col_cukai_ck2 in df_filtered.columns and not df_filtered.empty:
        df_pabrik_grp = df_filtered.groupby(col_pabrik)[col_cukai_ck2].sum().reset_index()
        df_pabrik_grp = df_pabrik_grp[df_pabrik_grp[col_cukai_ck2] > 0].sort_values(by=col_cukai_ck2, ascending=False).head(5)
        if not df_pabrik_grp.empty:
            df_pabrik_grp['CUKAI_STR'] = df_pabrik_grp[col_cukai_ck2].map(fmt_exact_rp)
            fig_pie = px.pie(df_pabrik_grp, names=col_pabrik, values=col_cukai_ck2, color_discrete_sequence=px.colors.sequential.Blues_r, hole=0.45, custom_data=['CUKAI_STR'])
            fig_pie.update_traces(hovertemplate="<b>%{label}</b><br>Nilai Cukai: %{customdata[0]}<br>Porsi: %{percent}<extra></extra>")
            fig_pie.update_layout(
                height=340,
                margin=dict(t=15, b=40, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5)
            )
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
        df_proses["TGL_PBCK-3_WARN"] = df_proses[col_tgl_pbck3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_pbck3 in df_proses.columns else "-"
        df_proses["TGL_BACK-3_WARN"] = df_proses[col_tgl_back3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_back3 in df_proses.columns else "-"
        df_proses["SISA_HARI_STR"] = df_proses['SISA_HARI_INT'].map(lambda x: f"{x:.0f} Hari" if pd.notnull(x) else "-")

        warn_rename = {
            col_pabrik: "Perusahaan",
            col_pbck3: "No. PBCK-3",
            "TGL_PBCK-3_WARN": "Tgl PBCK-3",
            col_back3: "No. BACK-3",
            "TGL_BACK-3_WARN": "Tgl BACK-3",
            "SISA_HARI_STR": "Sisa Waktu SLA"
        }
        warn_cols = [col_pabrik, col_pbck3, "TGL_PBCK-3_WARN", col_back3, "TGL_BACK-3_WARN", "SISA_HARI_STR"]

        overdue_items = df_proses[df_proses['SISA_HARI_INT'] < 0].sort_values(by='SISA_HARI_INT')
        critical_items = df_proses[(df_proses['SISA_HARI_INT'] >= 0) & (df_proses['SISA_HARI_INT'] <= 3)].sort_values(by='SISA_HARI_INT')
        
        with col_warn1:
            if not overdue_items.empty:
                st.error(f"🔴 **{len(overdue_items)} Berkas OVERDUE (Lewat Batas)!**")
                st.dataframe(overdue_items[warn_cols].rename(columns=warn_rename), hide_index=True, use_container_width=True)
            else: st.success("🟢 Bebas Overdue! Semua berkas dalam batas waktu yang sah.")
        with col_warn2:
            if not critical_items.empty:
                st.warning(f"🟡 **{len(critical_items)} Berkas Jatuh Tempo H-3 atau Kurang!**")
                st.dataframe(critical_items[warn_cols].rename(columns=warn_rename), hide_index=True, use_container_width=True)
            else: st.info("🔵 Bagus! Belum ada berkas dalam proses yang mendekati masa kritis (≤ 3 Hari).")
    else: st.success("🎉 Seluruh dokumen periode ini sudah selesai diproses (terbit CK-2).")
else: st.info("Data jatuh tempo (SLA) belum termuat dalam database.")

st.markdown("---")
st.subheader("📑 Detail Data Transaksi (Ter-filter)")
df_display = df_filtered.copy()

if not df_display.empty:
    # ---- SORTING BERDASARKAN KOLOM DATETIME ASLI SEBELUM FORMATTING STRING ----
    sort_cols = [c for c in [col_tgl_pbck3, col_tgl_ck2] if c in df_display.columns]
    if sort_cols:
        df_display = df_display.sort_values(by=sort_cols, ascending=False, na_position='last')

    df_display["TGL_PBCK-3_STR"] = df_display[col_tgl_pbck3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_pbck3 in df_display.columns else "-"
    df_display["TGL_BACK-3_STR"] = df_display[col_tgl_back3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_back3 in df_display.columns else "-"
    df_display["TGL_CK-2_STR"] = df_display[col_tgl_ck2].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_ck2 in df_display.columns else "-"
    
    df_display["CUKAI_PENGAJUAN"] = df_display[col_cukai_pbck3].map(fmt_exact_rp)
    df_display["CUKAI_REALISASI_CK2"] = df_display[col_cukai_ck2].map(fmt_exact_rp)
    df_display["BIAYA_PENGGANTI_STR"] = df_display[col_biaya_pengganti].map(fmt_exact_rp)
    df_display["BKS_DIAJUKAN"] = df_display[col_bks_pbck3].map(fmt_exact_bks)
    df_display["BKS_DISETUJUI_MS"] = df_display[col_bks_ck2].map(fmt_exact_bks)
    df_display["BKS_DITOLAK_TMS"] = df_display['BUNGKUS_TMS'].map(fmt_exact_bks)

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
    df_tabel_rapi = df_display[kolom_final].rename(columns=rename_map).reset_index(drop=True)

    # ---- FITUR PENCARIAN CEPAT & EKSPOR LAPORAN AKUNTABEL (.CSV) ----
    col_search, col_export = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "🔍 Cari Nomor PBCK-3 / BACK-3 / CK-2 / Nama Pabrik",
            placeholder="🔍 Cari Nomor PBCK-3 / BACK-3 / CK-2 / Agenda / Nama Pabrik...",
            label_visibility="collapsed"
        )
    if search_query:
        q_str = search_query.strip()
        mask_search = (
            df_tabel_rapi["Perusahaan"].astype(str).str.contains(q_str, case=False, na=False) |
            df_tabel_rapi["Agenda"].astype(str).str.contains(q_str, case=False, na=False) |
            df_tabel_rapi["No. PBCK-3"].astype(str).str.contains(q_str, case=False, na=False) |
            df_tabel_rapi["No. BACK-3"].astype(str).str.contains(q_str, case=False, na=False) |
            df_tabel_rapi["No. CK-2"].astype(str).str.contains(q_str, case=False, na=False)
        )
        df_tabel_rapi = df_tabel_rapi[mask_search].reset_index(drop=True)

    with col_export:
        csv_bytes = df_tabel_rapi.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Unduh Rekapitulasi Ter-filter (.csv)",
            data=csv_bytes,
            file_name=f"Rekap_PBCK3_KPPBC_Malang_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # ---- STYLING & KONFIGURASI KOLOM PROPORSIONAL ----
    kolom_rata_kanan = [
        "Bks Diajukan", "Bks Disetujui (MS)", "Bks Ditolak (TMS)",
        "Cukai Diajukan (PBCK-3)", "Realisasi Cukai (CK-2)", "Biaya Pengganti"
    ]
    kolom_rata_kiri = [c for c in df_tabel_rapi.columns if c not in kolom_rata_kanan]
    
    styled_tabel_utama = (
        df_tabel_rapi.style
        .set_properties(subset=kolom_rata_kanan, **{"text-align": "right"})
        .set_properties(subset=kolom_rata_kiri, **{"text-align": "left"})
    )

    konfigurasi_kolom = {
        "Agenda": st.column_config.TextColumn("Agenda", width="small"),
        "Perusahaan": st.column_config.TextColumn("Perusahaan", width="medium"),
        "No. PBCK-3": st.column_config.TextColumn("No. PBCK-3", width="medium"),
        "Tgl PBCK-3": st.column_config.TextColumn("Tgl PBCK-3", width="small"),
        "Bks Diajukan": st.column_config.TextColumn("Bks Diajukan", width="small"),
        "Bks Disetujui (MS)": st.column_config.TextColumn("Bks Disetujui (MS)", width="small"),
        "Bks Ditolak (TMS)": st.column_config.TextColumn("Bks Ditolak (TMS)", width="small"),
        "Cukai Diajukan (PBCK-3)": st.column_config.TextColumn("Cukai Diajukan (PBCK-3)", width="medium"),
        "Realisasi Cukai (CK-2)": st.column_config.TextColumn("Realisasi Cukai (CK-2)", width="medium"),
        "Biaya Pengganti": st.column_config.TextColumn("Biaya Pengganti", width="small"),
        "No. BACK-3": st.column_config.TextColumn("No. BACK-3", width="small"),
        "Tgl BACK-3": st.column_config.TextColumn("Tgl BACK-3", width="small"),
        "No. CK-2": st.column_config.TextColumn("No. CK-2", width="small"),
        "Tgl CK-2": st.column_config.TextColumn("Tgl CK-2", width="small"),
    }
    
    tabel_event = st.dataframe(
        styled_tabel_utama, 
        column_config=konfigurasi_kolom,
        use_container_width=True, 
        hide_index=True,
        on_select="rerun",           
        selection_mode="single-row"  
    )

    selected_rows = tabel_event.selection.rows
    if selected_rows and not df_tabel_rapi.empty:
        idx = selected_rows[0]
        if idx < len(df_tabel_rapi):
            selected_agenda = df_tabel_rapi.iloc[idx]["Agenda"]
            selected_pbck3 = df_tabel_rapi.iloc[idx]["No. PBCK-3"]
            
            st.markdown(f"### 🔍 Rincian Item untuk Dokumen: `{selected_pbck3}` (Agenda: {selected_agenda})")
            
            if not df_detail.empty:
                col_dtl_agenda = "AGENDA" if "AGENDA" in df_detail.columns else df_detail.columns[0]
                detail_filtered = df_detail.loc[df_detail[col_dtl_agenda].astype(str) == str(selected_agenda)].copy()
                
                if not detail_filtered.empty:
                    KOLOM_DIBUANG_SET = {
                        "TOTAL CUKAI PEMBERITAHUAN", "TOTAL CUKAI MS", 
                        "NO", "MOR", "↑ MOR", 
                        "BUNGKUS", "BP SERI I", "BUNGKUS.1", "BP SERI II", 
                        "BUNGKUS.2", "BP SERI III-TP", "BUNGKUS.3", "BP SERI III-DP", 
                        "BUNGKUS.4", "BP SERI MMEA", "TOTAL BP",
                        "JUMLAH MS (BUNGKUS)", "NILAI CUKAI PEMBERITAHUAN", "NILAI CUKAI MS"
                    }
                    
                    cols_to_keep = [
                        c for c in detail_filtered.columns 
                        if not c.startswith("UNNAMED") and c not in KOLOM_DIBUANG_SET
                    ]
                    detail_filtered = detail_filtered[cols_to_keep]

                    cols = list(detail_filtered.columns)
                    ck2_col = next((c for c in cols if c == "NILAI CK-2"), None)
                    
                    if ck2_col:
                        cols.remove(ck2_col)
                        insert_idx = next(
                            (i + 1 for i, c in enumerate(cols) if "CUKAI" in c and "BACK-3" in c),
                            len(cols)
                        )
                        cols.insert(insert_idx, ck2_col)
                        detail_filtered = detail_filtered[cols].rename(columns={ck2_col: "NILAI CK-2"})
                    
                    # ---- PEMFORMATAN VEKTORISASI CEPAT (.map) ----
                    num_cols = list(detail_filtered.select_dtypes(include='number').columns)
                    CURRENCY_KEYWORDS = ("CUKAI", "NILAI", "HJE", "TARIF", "BP")
                    
                    for col in num_cols:
                        col_up = str(col).upper()
                        if any(k in col_up for k in CURRENCY_KEYWORDS):
                            detail_filtered[col] = detail_filtered[col].map(fmt_exact_rp)
                        elif "TAHUN" in col_up:
                            detail_filtered[col] = detail_filtered[col].map(lambda x: f"{x:.0f}" if pd.notnull(x) else "-")
                        else:
                            detail_filtered[col] = detail_filtered[col].map(fmt_exact_bks)
                    
                    if "NILAI CK-2" in detail_filtered.columns and len(detail_filtered) > 1:
                        detail_filtered.iloc[1:, detail_filtered.columns.get_loc("NILAI CK-2")] = ""
                    
                    st.dataframe(detail_filtered, use_container_width=True, hide_index=True)
                else:
                    st.info(f"Tidak ada rincian tambahan di sheet 'Detail' untuk Agenda {selected_agenda}.")
            else:
                st.warning("Sheet bernama 'Detail' tidak ditemukan di database.")
    else:
        st.caption("💡 *Klik pada salah satu baris di tabel atas untuk memunculkan rincian item (Sheet Detail).*")

else:
    st.info("Tidak ada berkas transaksi pada periode / filter yang dipilih.")
