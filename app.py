import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==============================================================================
# KONFIGURASI HALAMAN UTAMA (ENTERPRISE ADMIN DASHBOARD)
# ==============================================================================
st.set_page_config(
    page_title="Dashboard PBCK-3 KPPBC TMC Malang",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# INJEKSI CSS GLOBAL: HYBRID ADMINTY x ADMINDEK ARCHITECTURE
# ==============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* 1. Tema Global Background (#F4F7FA) */
.stApp {
    background-color: #F4F7FA !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 98% !important;
}

/* 2. Dark Navigation Sidebar (#1E293B) ala Adminty/Admindek */
section[data-testid="stSidebar"] {
    background-color: #1E293B !important;
    border-right: 1px solid #0F172A !important;
}

section[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] label {
    color: #F8FAFC !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.12) !important;
    margin: 1.1rem 0 !important;
}

/* Kotak Selectbox & Input di dalam Sidebar agar Kontras & Nyaman Dibaca */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #0F172A !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color: #F8FAFC !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: rgba(15, 23, 42, 0.55);
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 6px;
    border: 1px solid rgba(255, 255, 255, 0.07);
    transition: all 0.2s ease;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(59, 130, 246, 0.18);
    border-color: #3B82F6;
}

/* Tombol Segarkan Data Cloud di Sidebar */
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #3B82F6 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1rem !important;
    width: 100% !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.38) !important;
}

/* Brand Header di Sidebar */
.sidebar-brand {
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.65) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 16px;
}

.sidebar-sla-box {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-left: 4px solid #06B6D4;
    border-radius: 10px;
    padding: 12px 14px;
    margin-top: 10px;
    margin-bottom: 14px;
    font-size: 12px;
}

/* 3. Top Header Bar Putih Bersih */
.top-header-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(15, 23, 42, 0.03);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 18px;
}

.header-title {
    margin: 0;
    color: #0F172A;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: -0.3px;
}

.header-subtitle {
    margin: 3px 0 0 0;
    color: #475569;
    font-size: 13px;
    font-weight: 500;
}

.header-law {
    display: inline-block;
    margin-top: 5px;
    font-size: 11.5px;
    font-weight: 700;
    color: #1E3A8A;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    padding: 3px 10px;
    border-radius: 6px;
}

.header-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #E2E8F0;
    background: #F8FAFC;
    color: #1E293B;
}

.pill-green {
    background: #ECFDF5;
    color: #047857;
    border-color: #A7F3D0;
}

.pill-red {
    background: #FEF2F2;
    color: #B91C1C;
    border-color: #FECACA;
}

.pill-blue {
    background: #EFF6FF;
    color: #1D4ED8;
    border-color: #BFDBFE;
}

/* 4. ZONA 1: 4 Top KPI Cards Berwarna (Gaya Adminty dengan Solid Footer Bar) */
.adminty-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 146px;
}

.adminty-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.09);
}

.adminty-body {
    padding: 18px 20px 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}

.adminty-title {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748B;
    margin-bottom: 6px;
}

.adminty-value {
    font-size: 26px;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.15;
}

.adminty-unit {
    font-size: 13px;
    font-weight: 600;
    color: #64748B;
}

.adminty-icon-circle {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
}

.adminty-footer {
    padding: 8px 20px;
    color: #FFFFFF;
    font-size: 11.5px;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.footer-orange { background: linear-gradient(90deg, #F97316, #FB923C); }
.footer-emerald { background: linear-gradient(90deg, #10B981, #34D399); }
.footer-rose { background: linear-gradient(90deg, #F43F5E, #FB7185); }
.footer-cyan { background: linear-gradient(90deg, #06B6D4, #22D3EE); }

.icon-orange { background: #FFF7ED; color: #EA580C; }
.icon-emerald { background: #ECFDF5; color: #059669; }
.icon-rose { background: #FFF1F2; color: #E11D48; }
.icon-cyan { background: #ECFEFF; color: #0891B2; }

/* 5. ZONA 2: Right Stacked Financial Cards ala Admindek */
.admindek-fin-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 15px 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.admindek-fin-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.fin-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748B;
    margin-bottom: 4px;
}

.fin-val {
    font-size: 18px;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.2;
}

.fin-sub {
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    margin-top: 4px;
}

.fin-icon-box {
    width: 46px;
    height: 46px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    color: #FFFFFF;
    flex-shrink: 0;
    margin-left: 12px;
}

.box-blue { background: linear-gradient(135deg, #1E3A8A, #3B82F6); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.28); }
.box-emerald { background: linear-gradient(135deg, #047857, #10B981); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.28); }
.box-amber { background: linear-gradient(135deg, #B45309, #F59E0B); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.28); }

/* 6. ZONA 3: Horizontal Progress Bar Strip ala Admindek */
.progress-strip-item {
    padding: 8px 12px;
    border-right: 1px solid #F1F5F9;
}

.progress-strip-label {
    font-size: 11.5px;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 4px;
}

.progress-strip-val {
    font-size: 19px;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 6px;
}

.progress-track {
    width: 100%;
    height: 8px;
    background-color: #E2E8F0;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 6px;
}

.progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.5s ease;
}

.progress-meta {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    margin-top: 5px;
}

/* Styling Kontainer Kartu Putih Streamlit (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03) !important;
    padding: 6px !important;
}

/* Badges Universal */
.badge-success { background-color: #ECFDF5; color: #047857; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }
.badge-warning { background-color: #FFFBEB; color: #B45309; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }
.badge-danger { background-color: #FEF2F2; color: #B91C1C; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }
.badge-info { background-color: #EFF6FF; color: #1D4ED8; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }

.section-title {
    font-size: 16px;
    font-weight: 800;
    color: #0F172A;
    margin: 0 0 2px 0;
}

.section-caption {
    font-size: 12px;
    color: #64748B;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# BAGIAN 1: FUNGSI PEMBERSIHAN DATA & PERBAIKAN BUG TEKNIS
# ==============================================================================
def clean_doc_str(series):
    """
    BUG FIX #1: Menghilangkan desimal .0 / .000000 pada Nomor Dokumen (No. BACK-3,
    Agenda, No. PBCK-3, No. CK-2) akibat pembacaan float64 oleh Pandas,
    serta membersihkan nilai kosong/error menjadi '-'.
    """
    def _clean(val):
        if pd.isna(val):
            return "-"
        s = re.sub(r'\.0+$', '', str(val).strip())
        if s.lower() in ["", "nan", "none", "nat", "-", "0", "#n/a", "#value!", "#ref!", "belum", "proses"]:
            return "-"
        return s
    return series.map(_clean)

# Alias kompatibilitas dengan baseline
clean_doc_id = clean_doc_str

INDO_MONTH_REPLACE = {
    'januari': 'January', 'februari': 'February', 'pebruari': 'February',
    'maret': 'March', 'april': 'April', 'mei': 'May', 'juni': 'June',
    'juli': 'July', 'agustus': 'August', 'september': 'September',
    'oktober': 'October', 'november': 'November', 'nopember': 'November',
    'desember': 'December',
    'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
    'jun': 'Jun', 'jul': 'Jul', 'agu': 'Aug', 'ags': 'Aug', 'agt': 'Aug',
    'sep': 'Sep', 'sept': 'Sep', 'okt': 'Oct', 'nov': 'Nov', 'nop': 'Nov', 'des': 'Dec'
}

def parse_indo_date(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    s_clean = series.astype(str).str.strip()
    for indo, eng in INDO_MONTH_REPLACE.items():
        s_clean = s_clean.str.replace(rf'\b{indo}\b', eng, case=False, regex=True)
    dt = pd.to_datetime(s_clean, errors='coerce', dayfirst=True)
    mask_na = dt.isna() & series.notna()
    if mask_na.any():
        num_dates = pd.to_numeric(series[mask_na], errors='coerce')
        valid_num = num_dates[(num_dates > 30000) & (num_dates < 60000)]
        if not valid_num.empty:
            dt.loc[valid_num.index] = pd.to_datetime(valid_num, unit='D', origin='1899-12-30', errors='coerce')
    return dt

def extract_agenda_num(series):
    def _extract(x):
        nums = re.findall(r'\d+', str(x))
        return int(nums[-1]) if nums else -1
    return series.map(_extract)

def fmt_exact_rp(val):
    if pd.isna(val) or val == 0:
        return "Rp 0"
    return f"-Rp {abs(val):,.0f}".replace(",", ".") if val < 0 else f"Rp {abs(val):,.0f}".replace(",", ".")

def fmt_exact_bks(val):
    if pd.isna(val) or val == 0:
        return "0"
    return f"-{abs(val):,.0f}".replace(",", ".") if val < 0 else f"{abs(val):,.0f}".replace(",", ".")

def fmt_kpi_rupiah(val):
    if pd.isna(val) or val == 0:
        return "Rp 0"
    is_negative = val < 0
    val = abs(val)
    real_str = f"Rp {val:,.0f}".replace(",", ".")
    if val >= 1_000_000_000_000:
        alias = f"{val/1_000_000_000_000:.2f} Triliun".replace(".", ",")
    elif val >= 1_000_000_000:
        alias = f"{val/1_000_000_000:.2f} Miliar".replace(".", ",")
    elif val >= 1_000_000:
        alias = f"{val/1_000_000:.2f} Juta".replace(".", ",")
    else:
        return f"-{real_str}" if is_negative else real_str
    final_str = f"{real_str}<div style='font-size: 12px; color: #64748B; font-weight: 700; margin-top: 2px;'>≈ {alias}</div>"
    return f"-{final_str}" if is_negative else final_str

def fmt_kpi_bungkus(val):
    if pd.isna(val) or val == 0:
        return "0 <span style='font-size: 13px; font-weight: 500;'>Bks</span>"
    is_negative = val < 0
    val = abs(val)
    real_str = f"{val:,.0f}".replace(",", ".")
    if val >= 1_000_000_000:
        alias = f"{val/1_000_000_000:.2f} M".replace(".", ",")
    elif val >= 1_000_000:
        alias = f"{val/1_000_000:.2f} Jt".replace(".", ",")
    else:
        base = f"{real_str} <span style='font-size: 13px; font-weight: 500;'>Bks</span>"
        return f"-{base}" if is_negative else base
    final_str = f"{real_str} <span style='font-size: 13px; font-weight: 500;'>Bks</span><div style='font-size: 12px; color: #64748B; font-weight: 700; margin-top: 2px;'>≈ {alias} Bks</div>"
    return f"-{final_str}" if is_negative else final_str

def clean_num(series):
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0)
    def parse_value(x):
        if pd.isna(x):
            return 0
        if isinstance(x, (int, float)):
            return x
        x_str = str(x).replace("Rp", "").strip().replace(".", "").replace(",", ".")
        try:
            return float(x_str)
        except ValueError:
            return 0
    return series.map(parse_value)

# ==============================================================================
# PEMBACAAN DATA CLOUD GOOGLE DRIVE (GUARDRAIL: FILE ID & LOGIKA TETAP UTUH)
# ==============================================================================
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

# Pemetaan Kolom Utama
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

# BUG FIX #1: Terapkan clean_doc_str pada seluruh kolom nomor dokumen di df dan df_detail
for c_id in [col_agenda, col_pbck3, col_back3, col_ck2]:
    if c_id in df.columns:
        df[c_id] = clean_doc_str(df[c_id])

if not df_detail.empty:
    col_dtl_agenda = "AGENDA" if "AGENDA" in df_detail.columns else df_detail.columns[0]
    df_detail[col_dtl_agenda] = clean_doc_str(df_detail[col_dtl_agenda])
    for c_dtl_id in ["AGENDA", "NO_PBCK-3", "NO_PBCK_3", "BACK-3", "NO_BACK-3", "NO_CK-2", "NO_CK2"]:
        if c_dtl_id in df_detail.columns:
            df_detail[c_dtl_id] = clean_doc_str(df_detail[c_dtl_id])

# Penyaringan Baris Valid
mask_valid_row = pd.Series(False, index=df.index)
if col_agenda in df.columns:
    mask_valid_row |= (df[col_agenda] != "-")
if col_pbck3 in df.columns:
    mask_valid_row |= (df[col_pbck3] != "-")
if col_pabrik in df.columns:
    s_pab = df[col_pabrik].astype(str).str.strip()
    mask_valid_row |= (~df[col_pabrik].isna() & ~s_pab.str.lower().isin(["", "nan", "none", "-"]))
df = df[mask_valid_row].copy()

# Konversi Kolom Tanggal
for c_date in [col_tgl_pbck3, col_tgl_back3, col_tgl_ck2]:
    if c_date in df.columns:
        df[c_date] = parse_indo_date(df[c_date])

df['TAHUN_CK2'] = df[col_tgl_ck2].dt.year if col_tgl_ck2 in df.columns else pd.Series(dtype='float64')
df['BULAN_CK2_ANGKA'] = df[col_tgl_ck2].dt.month if col_tgl_ck2 in df.columns else pd.Series(dtype='float64')
df['TAHUN_PBCK3'] = df[col_tgl_pbck3].dt.year if col_tgl_pbck3 in df.columns else pd.Series(dtype='float64')
df['BULAN_PBCK3_ANGKA'] = df[col_tgl_pbck3].dt.month if col_tgl_pbck3 in df.columns else pd.Series(dtype='float64')
df['TAHUN_BACK3'] = df[col_tgl_back3].dt.year if col_tgl_back3 in df.columns else pd.Series(dtype='float64')
df['BULAN_BACK3_ANGKA'] = df[col_tgl_back3].dt.month if col_tgl_back3 in df.columns else pd.Series(dtype='float64')

def extract_year_agenda(val):
    m = re.search(r'PPK(\d{2})-', str(val).upper())
    return float(2000 + int(m.group(1))) if m else float('nan')

df['TAHUN_AGENDA'] = df[col_agenda].map(extract_year_agenda) if col_agenda in df.columns else pd.Series(dtype='float64')

# BUG FIX #2: Kolom bantu TAHUN_ACUAN & BULAN_ACUAN (+ fallback) agar berkas Outstanding (PROSES) tidak pernah hilang
df['TAHUN_ACUAN'] = (
    df['TAHUN_CK2']
    .fillna(df[col_tgl_pbck3].dt.year if col_tgl_pbck3 in df.columns else pd.Series(dtype='float64'))
    .fillna(df['TAHUN_BACK3'])
    .fillna(df['TAHUN_AGENDA'])
)
df['BULAN_ACUAN'] = (
    df['BULAN_CK2_ANGKA']
    .fillna(df[col_tgl_pbck3].dt.month if col_tgl_pbck3 in df.columns else pd.Series(dtype='float64'))
    .fillna(df['BULAN_BACK3_ANGKA'])
)

# Alias kompatibilitas
df['TAHUN_EFEKTIF'] = df['TAHUN_ACUAN']
df['BULAN_EFEKTIF'] = df['BULAN_ACUAN']

if col_ck2 in df.columns:
    df['STATUS_CK2_BOOL'] = "PROSES"
    df.loc[df[col_ck2] != "-", 'STATUS_CK2_BOOL'] = "TERBIT"
else:
    df['STATUS_CK2_BOOL'] = "PROSES"

INDO_BULAN = {
    1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
    5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
    9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
}
df['BULAN_CK2_NAMA'] = df['BULAN_CK2_ANGKA'].map(INDO_BULAN)

for c_num in [col_cukai_pbck3, col_cukai_ck2, col_biaya_pengganti, col_bks_pbck3, col_bks_ck2]:
    if c_num in df.columns:
        df[c_num] = clean_num(df[c_num])

df['BUNGKUS_TMS'] = (df[col_bks_pbck3] - df[col_bks_ck2]).clip(lower=0)

# ==============================================================================
# ZONA SIDEBAR KIRI GELAP (#1E293B) — PANEL NAVIGASI & FILTER EKSEKUTIF
# ==============================================================================
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/1/1a/Logo_Bea_Cukai.png"

with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <div style="display:flex; align-items:center; gap:12px;">
            <img src="{LOGO_URL}" width="42" referrerpolicy="no-referrer" onerror="this.style.display='none'">
            <div>
                <div style="font-size:13px; font-weight:800; letter-spacing:0.6px; color:#F8FAFC;">KPPBC TMC MALANG</div>
                <div style="font-size:11px; color:#94A3B8; font-weight:600;">Executive Analytics Suite</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎛️ Filter Entitas & Tahun")
    pabrik_list = ["Semua Pabrik"] + sorted([
        str(p).strip() for p in df[col_pabrik].dropna().unique().tolist()
        if str(p).strip().lower() not in ["", "-", "nan", "none"]
    ])
    selected_pabrik = st.selectbox("🏢 Pilih Pabrik / Perusahaan:", pabrik_list)

    tahun_tersedia = [2026]
    if df['TAHUN_ACUAN'].dropna().nunique() > 0:
        tahun_tersedia = sorted(df['TAHUN_ACUAN'].dropna().unique().astype(int).tolist(), reverse=True)
    selected_tahun = st.selectbox("📅 Pilih Tahun Anggaran:", tahun_tersedia)

    st.markdown("---")
    st.markdown("### 🗓️ Filter Periode CK-2")
    mode_periode = st.radio(
        "Mode Periode:",
        ["Semua Periode (Total Tahunan)", "Bulanan Tunggal (Single Month)", "Kumulatif (s.d. Bulan)"]
    )

    current_month_num = datetime.now().month
    selected_bulan_angka = current_month_num
    selected_bulan_nama = INDO_BULAN.get(current_month_num, "Januari")
    list_12_bulan = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    if mode_periode != "Semua Periode (Total Tahunan)":
        selected_bulan_nama = st.selectbox("Pilih Bulan Acuan:", list_12_bulan, index=current_month_num - 1)
        selected_bulan_angka = next(k for k, v in INDO_BULAN.items() if v == selected_bulan_nama)

# ==============================================================================
# LOGIKA FILTER DATA (MENGGUNAKAN TAHUN_ACUAN & BULAN_ACUAN AGAR OUTSTANDING AMAN)
# ==============================================================================
df_filtered = df.copy()
if selected_pabrik != "Semua Pabrik":
    df_filtered = df_filtered[df_filtered[col_pabrik].astype(str).str.strip() == selected_pabrik]

is_terbit = df_filtered['STATUS_CK2_BOOL'] == "TERBIT"
is_proses = df_filtered['STATUS_CK2_BOOL'] == "PROSES"

if mode_periode == "Semua Periode (Total Tahunan)":
    df_filtered = df_filtered[(df_filtered['TAHUN_ACUAN'] == selected_tahun) | df_filtered['TAHUN_ACUAN'].isna()]
elif mode_periode == "Bulanan Tunggal (Single Month)":
    cond_terbit = is_terbit & (df_filtered['TAHUN_ACUAN'] == selected_tahun) & (df_filtered['BULAN_ACUAN'] == selected_bulan_angka)
    cond_proses = is_proses & (
        ((df_filtered['TAHUN_ACUAN'] == selected_tahun) & (df_filtered['BULAN_ACUAN'] == selected_bulan_angka))
        | df_filtered['TAHUN_ACUAN'].isna()
        | df_filtered['BULAN_ACUAN'].isna()
    )
    df_filtered = df_filtered[cond_terbit | cond_proses]
elif mode_periode == "Kumulatif (s.d. Bulan)":
    cond_terbit = is_terbit & (df_filtered['TAHUN_ACUAN'] == selected_tahun) & (df_filtered['BULAN_ACUAN'] <= selected_bulan_angka)
    cond_proses = is_proses & (
        ((df_filtered['TAHUN_ACUAN'] == selected_tahun) & (df_filtered['BULAN_ACUAN'] <= selected_bulan_angka))
        | df_filtered['TAHUN_ACUAN'].isna()
        | df_filtered['BULAN_ACUAN'].isna()
    )
    df_filtered = df_filtered[cond_terbit | cond_proses]

# ==============================================================================
# PERHITUNGAN METRIK EKSEKUTIF
# ==============================================================================
valid_agenda = df_filtered[df_filtered[col_agenda] != "-"][col_agenda] if col_agenda in df_filtered.columns else pd.Series(dtype='str')
valid_pbck3 = df_filtered[df_filtered[col_pbck3] != "-"][col_pbck3] if col_pbck3 in df_filtered.columns else pd.Series(dtype='str')
total_pbck3 = max(valid_agenda.nunique(), valid_pbck3.nunique(), len(df_filtered))

df_terbit_filtered = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"]
total_ck2 = df_terbit_filtered[df_terbit_filtered[col_ck2] != "-"][col_ck2].nunique() if col_ck2 in df_filtered.columns else 0
total_outstanding = int((df_filtered['STATUS_CK2_BOOL'] == "PROSES").sum())
persen_selesai = (total_ck2 / total_pbck3 * 100) if total_pbck3 > 0 else 0.0
persen_outstanding = (total_outstanding / total_pbck3 * 100) if total_pbck3 > 0 else 0.0

avg_sla_val = None
avg_sla_num_str = "-"
avg_sla_str = "- Hari"
if not df_terbit_filtered.empty and col_tgl_ck2 in df_terbit_filtered.columns and col_tgl_back3 in df_terbit_filtered.columns:
    sla_days = (df_terbit_filtered[col_tgl_ck2] - df_terbit_filtered[col_tgl_back3]).dt.days.dropna()
    sla_days = sla_days[sla_days >= 0]
    if not sla_days.empty:
        avg_sla_val = sla_days.mean()
        avg_sla_num_str = f"{avg_sla_val:.1f}".replace(".", ",")
        avg_sla_str = f"{avg_sla_num_str} Hari"

cukai_pbck3_val = df_filtered[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_filtered.columns else 0
cukai_ck2_val = df_filtered[col_cukai_ck2].sum() if col_cukai_ck2 in df_filtered.columns else 0
selisih_fisik = cukai_pbck3_val - cukai_ck2_val
biaya_pengganti = df_filtered[col_biaya_pengganti].sum() if col_biaya_pengganti in df_filtered.columns else 0

total_bks_pbck3 = df_filtered[col_bks_pbck3].sum() if col_bks_pbck3 in df_filtered.columns else 0
total_bks_ck2 = df_filtered[col_bks_ck2].sum() if col_bks_ck2 in df_filtered.columns else 0
total_bks_tms = max(total_bks_pbck3 - total_bks_ck2, 0)

rasio_bks_ms = (total_bks_ck2 / total_bks_pbck3 * 100) if total_bks_pbck3 > 0 else 0.0
rasio_bks_tms = (total_bks_tms / total_bks_pbck3 * 100) if total_bks_pbck3 > 0 else 0.0

visual_periode_lbl = f"Tahun Anggaran {selected_tahun}"
if mode_periode == "Bulanan Tunggal (Single Month)":
    visual_periode_lbl = f"Bulan {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)":
    visual_periode_lbl = f"s.d. Bulan {selected_bulan_nama} {selected_tahun}"

# Ringkasan Cepat SLA & Tombol Refresh di Bawah Sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown(f"""
    <div class="sidebar-sla-box">
        <div style="font-weight:800; color:#38BDF8; margin-bottom:4px;">📌 RINGKASAN KEPATUHAN SLA</div>
        <div style="color:#E2E8F0; line-height:1.5;">
            • Rata-rata Penyelesaian: <b>{avg_sla_str}</b><br>
            • Standar PER-2/BC/2026: <b>Maks 10 HK</b><br>
            • Berkas Outstanding: <b>{total_outstanding} Dokumen</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Segarkan Data Cloud", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==============================================================================
# TOP HEADER BAR & ZONA 1: 4 TOP KPI CARDS BERWARNA (GAYA ADMINTY)
# ==============================================================================
rekon_pill_html = (
    '<span class="status-pill pill-green">✅ Rekonsiliasi: Fisik 100% Sesuai</span>'
    if selisih_fisik == 0
    else f'<span class="status-pill pill-red">⚠️ Selisih TMS: {fmt_exact_rp(-selisih_fisik)} ({fmt_exact_bks(total_bks_tms)} Bks)</span>'
)

st.markdown(f"""
<div class="top-header-card">
    <div class="header-left">
        <img src="{LOGO_URL}" width="66" referrerpolicy="no-referrer" onerror="this.style.display='none'">
        <div>
            <h1 class="header-title">📊 EXECUTIVE DASHBOARD PBCK-3 & REALISASI CUKAI</h1>
            <p class="header-subtitle">Monitoring Pelayanan Pengolahan Kembali & Pemusnahan BKC — KPPBC Tipe Madya Cukai Malang</p>
            <span class="header-law">⚖️ Landasan Hukum: PMK Nomor 113 Tahun 2025 & PER-2/BC/2026 (SLA Maks. 10 Hari Kerja)</span>
        </div>
    </div>
    <div class="header-pills">
        <span class="status-pill pill-blue">🗓️ {visual_periode_lbl}</span>
        <span class="status-pill">🏢 {selected_pabrik}</span>
        {rekon_pill_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ZONA 1: st.columns(4) untuk 4 Kartu KPI Utama bergaya Adminty
z1_c1, z1_c2, z1_c3, z1_c4 = st.columns(4)

with z1_c1:
    st.markdown(f"""
    <div class="adminty-card">
        <div class="adminty-body">
            <div>
                <div class="adminty-title">Permohonan PBCK-3 Terlayani</div>
                <div class="adminty-value">{total_pbck3:,.0f} <span class="adminty-unit">Berkas</span></div>
            </div>
            <div class="adminty-icon-circle icon-orange">📥</div>
        </div>
        <div class="adminty-footer footer-orange">
            <span>Total Pengajuan Masuk</span>
            <span>100% Terdata</span>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with z1_c2:
    st.markdown(f"""
    <div class="adminty-card">
        <div class="adminty-body">
            <div>
                <div class="adminty-title">Realisasi CK-2 Terbit</div>
                <div class="adminty-value">{total_ck2:,.0f} <span class="adminty-unit">Dokumen</span></div>
            </div>
            <div class="adminty-icon-circle icon-emerald">📜</div>
        </div>
        <div class="adminty-footer footer-emerald">
            <span>Tingkat Penyelesaian</span>
            <span>{persen_selesai:.1f}% Selesai</span>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with z1_c3:
    st.markdown(f"""
    <div class="adminty-card">
        <div class="adminty-body">
            <div>
                <div class="adminty-title">Outstanding / Dalam Proses</div>
                <div class="adminty-value">{total_outstanding:,.0f} <span class="adminty-unit">Dokumen</span></div>
            </div>
            <div class="adminty-icon-circle icon-rose">⏳</div>
        </div>
        <div class="adminty-footer footer-rose">
            <span>Menunggu Terbit CK-2</span>
            <span>{persen_outstanding:.1f}% Beban Kerja</span>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with z1_c4:
    sla_status_txt = "Memenuhi SLA (≤ 10 HK)" if (avg_sla_val is not None and avg_sla_val <= 10) else ("Melebihi SLA (> 10 HK)" if avg_sla_val is not None else "Menunggu Data CK-2")
    st.markdown(f"""
    <div class="adminty-card">
        <div class="adminty-body">
            <div>
                <div class="adminty-title">Kecepatan Layanan (SLA Speed)</div>
                <div class="adminty-value">{avg_sla_num_str} <span class="adminty-unit">Hari</span></div>
            </div>
            <div class="adminty-icon-circle icon-cyan">⚡</div>
        </div>
        <div class="adminty-footer footer-cyan">
            <span>Batas Maks 10 Hari Kerja</span>
            <span>{sla_status_txt}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# ZONA 2: ASYMMETRIC ANALYTICS GRID 7 : 3 (GAYA ADMINDEK)
# ==============================================================================
col_main_chart, col_side_kpis = st.columns([6.8, 3.2])

with col_main_chart:
    with st.container(border=True):
        st.markdown(f"""
        <div style="padding: 6px 10px 0 10px;">
            <div class="section-title">📈 Tren Realisasi CK-2 per Bulan ({selected_tahun})</div>
            <div class="section-caption">Visualisasi volume dokumen CK-2 terbit & nilai realisasi cukai (MS) — Entitas: <b>{selected_pabrik}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # BUG FIX #4: Sinkronkan Grafik Tren Bulanan dengan Filter Pabrik & Tahun + Tooltip Nilai Rupiah Cukai
        df_terbit_trend = df[df['STATUS_CK2_BOOL'] == "TERBIT"].copy()
        if selected_pabrik != "Semua Pabrik":
            df_terbit_trend = df_terbit_trend[df_terbit_trend[col_pabrik].astype(str).str.strip() == selected_pabrik]
        if 'TAHUN_ACUAN' in df_terbit_trend.columns:
            df_terbit_trend = df_terbit_trend[df_terbit_trend['TAHUN_ACUAN'] == selected_tahun]

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
                marker=dict(color='#2563EB', cornerradius=6),
                text=df_trend['CK2'],
                textposition='auto',
                customdata=df_trend['CUKAI_STR'],
                hovertemplate="<b>Bulan %{x}</b><br>Dokumen CK-2: %{y} Dokumen<br>Total Nilai Cukai (MS): %{customdata}<extra></extra>"
            ))
            fig_trend.add_trace(go.Scatter(
                x=df_trend['BULAN'],
                y=df_trend['TOTAL_CUKAI'],
                name='Nilai Cukai MS (Rp)',
                yaxis='y2',
                mode='lines+markers',
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.10)',
                line=dict(color='#059669', width=2.8),
                marker=dict(size=8, color='#059669', line=dict(width=2, color='#FFFFFF')),
                customdata=df_trend['CUKAI_STR'],
                hovertemplate="<b>Bulan %{x}</b><br>Realisasi Cukai (MS): %{customdata}<extra></extra>"
            ))
            fig_trend.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title="Bulan Terbit CK-2", showgrid=False),
                yaxis=dict(title="Jumlah Dokumen", gridcolor='#F1F5F9', zeroline=False),
                yaxis2=dict(title="Nilai Cukai (Rp)", overlaying='y', side='right', showgrid=False, zeroline=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=335,
                margin=dict(t=25, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Belum ada data dokumen CK-2 yang berstatus TERBIT pada filter pabrik/tahun ini.")

with col_side_kpis:
    badge_cukai_side = (
        f'<span class="badge-danger">Selisih TMS: {fmt_exact_rp(-selisih_fisik)}</span>'
        if selisih_fisik > 0
        else '<span class="badge-success">100% Memenuhi Syarat</span>'
    )

    st.markdown(f"""
    <div class="admindek-fin-card">
        <div>
            <div class="fin-label">Nilai Pengajuan (PBCK-3)</div>
            <div class="fin-val">{fmt_kpi_rupiah(cukai_pbck3_val)}</div>
            <div class="fin-sub">Potensi nilai cukai pemberitahuan</div>
        </div>
        <div class="fin-icon-box box-blue">📋</div>
    </div>

    <div class="admindek-fin-card" style="background: #F0FDF4; border-color: #BBF7D0;">
        <div>
            <div class="fin-label" style="color: #047857;">Realisasi Cukai CK-2 (MS)</div>
            <div class="fin-val" style="color: #065F46;">{fmt_kpi_rupiah(cukai_ck2_val)}</div>
            <div class="fin-sub">{badge_cukai_side}</div>
        </div>
        <div class="fin-icon-box box-emerald">💸</div>
    </div>

    <div class="admindek-fin-card">
        <div>
            <div class="fin-label" style="color: #B45309;">Biaya Pengganti (BP) Pita Cukai</div>
            <div class="fin-val" style="color: #92400E;">{fmt_kpi_rupiah(biaya_pengganti)}</div>
            <div class="fin-sub">Penerimaan Negara (PMK 113/2025)</div>
        </div>
        <div class="fin-icon-box box-amber">🏦</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# ZONA 3: HORIZONTAL PROGRESS BAR STRIP (GAYA ADMINDEK — 4 KOLOM)
# ==============================================================================
with st.container(border=True):
    z3_c1, z3_c2, z3_c3, z3_c4 = st.columns(4)

    with z3_c1:
        st.markdown(f"""
        <div class="progress-strip-item">
            <div class="progress-strip-label">📦 Kemasan Diajukan (PBCK-3)</div>
            <div class="progress-strip-val">{fmt_kpi_bungkus(total_bks_pbck3)}</div>
            <div class="progress-track">
                <div class="progress-fill" style="width: 100%; background: #2563EB;"></div>
            </div>
            <div class="progress-meta">
                <span>Basis Pemberitahuan Fisik</span>
                <span>100%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with z3_c2:
        w_ms = min(max(rasio_bks_ms, 0.0), 100.0)
        st.markdown(f"""
        <div class="progress-strip-item">
            <div class="progress-strip-label" style="color:#047857;">✅ Kemasan Disetujui (MS)</div>
            <div class="progress-strip-val" style="color:#065F46;">{fmt_kpi_bungkus(total_bks_ck2)}</div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {w_ms:.1f}%; background: #10B981;"></div>
            </div>
            <div class="progress-meta">
                <span>Memenuhi Syarat Pengembalian</span>
                <span style="color:#047857; font-weight:700;">{rasio_bks_ms:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with z3_c3:
        w_tms = min(max(rasio_bks_tms, 0.0), 100.0)
        st.markdown(f"""
        <div class="progress-strip-item">
            <div class="progress-strip-label" style="color:#B91C1C;">❌ Kemasan Ditolak (TMS)</div>
            <div class="progress-strip-val" style="color:#991B1B;">{fmt_kpi_bungkus(total_bks_tms)}</div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {w_tms:.1f}%; background: #EF4444;"></div>
            </div>
            <div class="progress-meta">
                <span>{'Tidak Mendapat Pengembalian' if total_bks_tms > 0 else 'Nihil Selisih (0 Bks)'}</span>
                <span style="color:#B91C1C; font-weight:700;">{rasio_bks_tms:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with z3_c4:
        w_done = min(max(persen_selesai, 0.0), 100.0)
        st.markdown(f"""
        <div class="progress-strip-item" style="border-right:none;">
            <div class="progress-strip-label" style="color:#0891B2;">🎯 Tingkat Penyelesaian Dokumen</div>
            <div class="progress-strip-val" style="color:#0E7490;">{persen_selesai:.1f}% <span style="font-size:13px; font-weight:600; color:#64748B;">({total_ck2}/{total_pbck3} Berkas)</span></div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {w_done:.1f}%; background: #06B6D4;"></div>
            </div>
            <div class="progress-meta">
                <span>Rasio Terbit CK-2 vs PBCK-3</span>
                <span style="color:#0891B2; font-weight:700;">{persen_selesai:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# ZONA 4: SPLIT VIEW — DONUT CHART (45%) & RADAR KEPATUHAN SLA (55%)
# ==============================================================================
col_donut, col_sla_radar = st.columns([4.5, 5.5])

with col_donut:
    with st.container(border=True):
        st.markdown("""
        <div style="padding: 6px 10px 0 10px;">
            <div class="section-title">🍩 Kontribusi Realisasi Nilai Cukai (Top 5 Pabrik)</div>
            <div class="section-caption">Distribusi nilai pengembalian cukai yang memenuhi syarat (MS) per perusahaan.</div>
        </div>
        """, unsafe_allow_html=True)

        if col_pabrik in df_filtered.columns and col_cukai_ck2 in df_filtered.columns and not df_filtered.empty:
            df_pabrik_grp = df_filtered.groupby(col_pabrik)[col_cukai_ck2].sum().reset_index()
            df_pabrik_grp = df_pabrik_grp[df_pabrik_grp[col_cukai_ck2] > 0].sort_values(by=col_cukai_ck2, ascending=False).head(5)
            if not df_pabrik_grp.empty:
                df_pabrik_grp['CUKAI_STR'] = df_pabrik_grp[col_cukai_ck2].map(fmt_exact_rp)
                fig_pie = px.pie(
                    df_pabrik_grp,
                    names=col_pabrik,
                    values=col_cukai_ck2,
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                    hole=0.48,
                    custom_data=['CUKAI_STR']
                )
                fig_pie.update_traces(
                    hovertemplate="<b>%{label}</b><br>Nilai Cukai: %{customdata[0]}<br>Porsi: %{percent}<extra></extra>"
                )
                fig_pie.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=340,
                    margin=dict(t=15, b=45, l=10, r=10),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Belum ada realisasi nilai CK-2 pada filter ini.")
        else:
            st.info("Data belum tersedia untuk grafik kontribusi.")

with col_sla_radar:
    with st.container(border=True):
        st.markdown("""
        <div style="padding: 6px 10px 0 10px;">
            <div class="section-title">🚨 Warning Kepatuhan SLA (Maks 10 Hari Kerja s.d. CK-2)</div>
            <div class="section-caption">Berdasarkan PER-2/BC/2026 Pasal 7, penerbitan CK-2 tidak boleh melebihi 10 hari kerja sejak Tanggal BACK-3 diterbitkan.</div>
        </div>
        """, unsafe_allow_html=True)

        col_tempo = "JATUH TEMPO BERAPA HARI LAGI" if "JATUH TEMPO BERAPA HARI LAGI" in df.columns else None
        if col_tempo:
            df_proses = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "PROSES"].copy()
            if not df_proses.empty:
                df_proses['SISA_HARI_INT'] = pd.to_numeric(df_proses[col_tempo], errors='coerce')
                df_proses["TGL_PBCK-3_WARN"] = df_proses[col_tgl_pbck3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_pbck3 in df_proses.columns else "-"
                df_proses["TGL_BACK-3_WARN"] = df_proses[col_tgl_back3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_back3 in df_proses.columns else "-"
                df_proses["SISA_HARI_STR"] = df_proses['SISA_HARI_INT'].map(lambda x: f"{x:.0f} Hari" if pd.notnull(x) else "Menunggu BACK-3")

                warn_rename = {
                    col_agenda: "Agenda",
                    col_pabrik: "Perusahaan",
                    col_pbck3: "No. PBCK-3",
                    "TGL_PBCK-3_WARN": "Tgl PBCK-3",
                    col_back3: "No. BACK-3",
                    "TGL_BACK-3_WARN": "Tgl BACK-3",
                    "SISA_HARI_STR": "Sisa Waktu SLA"
                }
                warn_cols = [col_agenda, col_pabrik, col_pbck3, "TGL_PBCK-3_WARN", col_back3, "TGL_BACK-3_WARN", "SISA_HARI_STR"]

                overdue_items = df_proses[df_proses['SISA_HARI_INT'] < 0].sort_values(by='SISA_HARI_INT')
                critical_items = df_proses[(df_proses['SISA_HARI_INT'] >= 0) & (df_proses['SISA_HARI_INT'] <= 3)].sort_values(by='SISA_HARI_INT')

                if not overdue_items.empty:
                    st.error(f"🔴 **{len(overdue_items)} Berkas OVERDUE (Lewat Batas SLA)!**")
                    st.dataframe(overdue_items[warn_cols].rename(columns=warn_rename), hide_index=True, use_container_width=True)
                else:
                    st.success("🟢 Bebas Overdue! Semua berkas dalam batas waktu yang sah.")

                if not critical_items.empty:
                    st.warning(f"🟡 **{len(critical_items)} Berkas Jatuh Tempo Kritis (H-3 atau Kurang)!**")
                    st.dataframe(critical_items[warn_cols].rename(columns=warn_rename), hide_index=True, use_container_width=True)
                else:
                    st.info("🔵 Bagus! Belum ada berkas dalam proses yang mendekati masa kritis (≤ 3 Hari).")
            else:
                st.success("🎉 Seluruh dokumen periode ini sudah selesai diproses (terbit CK-2).")
        else:
            st.info("Data jatuh tempo (SLA) belum termuat dalam database.")

st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# ZONA 5: TABEL DETAIL DATA TRANSAKSI INTERAKTIF & EKSPOR CSV (MASTER-DETAIL)
# ==============================================================================
with st.container(border=True):
    st.markdown("""
    <div style="padding: 6px 10px 0 10px;">
        <div class="section-title">📑 Detail Data Transaksi Interaktif & Rekapitulasi</div>
        <div class="section-caption">Klik pada salah satu baris di tabel untuk memunculkan rincian item pita cukai dari Sheet <b>Detail</b> di bawahnya.</div>
    </div>
    """, unsafe_allow_html=True)

    df_display = df_filtered.copy()
    if not df_display.empty:
        # BUG FIX #3: Urutkan df_display berdasarkan kolom datetime asli (col_tgl_pbck3) SEBELUM diformat menjadi teks dd/mm/yyyy
        df_display["_AGENDA_SORT_NUM"] = extract_agenda_num(df_display[col_agenda]) if col_agenda in df_display.columns else 0
        sort_cols = [c for c in [col_tgl_pbck3, "_AGENDA_SORT_NUM", col_tgl_ck2] if c in df_display.columns]
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
            col_agenda_main: "Agenda",
            col_pabrik: "Perusahaan",
            col_pbck3: "No. PBCK-3",
            "TGL_PBCK-3_STR": "Tgl PBCK-3",
            "BKS_DIAJUKAN": "Bks Diajukan",
            "BKS_DISETUJUI_MS": "Bks Disetujui (MS)",
            "BKS_DITOLAK_TMS": "Bks Ditolak (TMS)",
            "CUKAI_PENGAJUAN": "Cukai Diajukan (PBCK-3)",
            "CUKAI_REALISASI_CK2": "Realisasi Cukai (CK-2)",
            "BIAYA_PENGGANTI_STR": "Biaya Pengganti",
            col_back3: "No. BACK-3",
            "TGL_BACK-3_STR": "Tgl BACK-3",
            col_ck2: "No. CK-2",
            "TGL_CK-2_STR": "Tgl CK-2"
        }
        kolom_final = [
            col_agenda_main, col_pabrik, col_pbck3, "TGL_PBCK-3_STR",
            "BKS_DIAJUKAN", "BKS_DISETUJUI_MS", "BKS_DITOLAK_TMS",
            "CUKAI_PENGAJUAN", "CUKAI_REALISASI_CK2", "BIAYA_PENGGANTI_STR",
            col_back3, "TGL_BACK-3_STR", col_ck2, "TGL_CK-2_STR"
        ]
        df_tabel_rapi = df_display[kolom_final].rename(columns=rename_map).reset_index(drop=True)

        col_search, col_export = st.columns([3, 1])
        with col_search:
            search_query = st.text_input(
                "🔍 Cari",
                placeholder="🔍 Cari Pabrik / No. PBCK-3 / BACK-3 / CK-2 / Agenda...",
                label_visibility="collapsed"
            )

        if search_query:
            q_str = search_query.strip()
            mask_search = (
                df_tabel_rapi["Perusahaan"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["Agenda"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["No. PBCK-3"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["No. BACK-3"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["No. CK-2"].astype(str).str.contains(q_str, case=False, na=False)
            )
            df_tabel_rapi = df_tabel_rapi[mask_search].reset_index(drop=True)

        with col_export:
            csv_bytes = df_tabel_rapi.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Unduh Data Ter-filter (.csv)",
                data=csv_bytes,
                file_name=f"Rekap_PBCK3_KPPBC_Malang_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

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
                st.markdown(f"#### 🔍 Rincian Item untuk Dokumen: `{selected_pbck3}` (Agenda: `{selected_agenda}`)")

                if not df_detail.empty:
                    col_dtl_agenda = "AGENDA" if "AGENDA" in df_detail.columns else df_detail.columns[0]
                    detail_filtered = df_detail.loc[df_detail[col_dtl_agenda].astype(str) == str(selected_agenda)].copy()
                    if not detail_filtered.empty:
                        KOLOM_DIBUANG_SET = {
                            "TOTAL CUKAI PEMBERITAHUAN", "TOTAL CUKAI MS", "NO", "MOR", "↑ MOR",
                            "BUNGKUS", "BP SERI I", "BUNGKUS.1", "BP SERI II", "BUNGKUS.2",
                            "BP SERI III-TP", "BUNGKUS.3", "BP SERI III-DP", "BUNGKUS.4",
                            "BP SERI MMEA", "TOTAL BP", "JUMLAH MS (BUNGKUS)",
                            "NILAI CUKAI PEMBERITAHUAN", "NILAI CUKAI MS"
                        }
                        cols_to_keep = [c for c in detail_filtered.columns if not c.startswith("UNNAMED") and c not in KOLOM_DIBUANG_SET]
                        detail_filtered = detail_filtered[cols_to_keep]

                        cols = list(detail_filtered.columns)
                        ck2_col = next((c for c in cols if c == "NILAI CK-2"), None)
                        if ck2_col:
                            cols.remove(ck2_col)
                            insert_idx = next((i + 1 for i, c in enumerate(cols) if "CUKAI" in c and "BACK-3" in c), len(cols))
                            cols.insert(insert_idx, ck2_col)
                            detail_filtered = detail_filtered[cols].rename(columns={ck2_col: "NILAI CK-2"})

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
