import re
import numpy as np
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
# LOGO BEA CUKAI RESMI + INLINE SVG FALLBACK ANTI-BROKEN IMAGE
# ==============================================================================
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/7/72/Logo_bea_cukai.png"
BC_SVG_FALLBACK = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120'>"
    "<defs><linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>"
    "<stop offset='0%' stop-color='%230F172A'/><stop offset='100%' stop-color='%231E3A8A'/>"
    "</linearGradient></defs>"
    "<polygon points='60,4 112,30 112,86 60,116 8,86 8,30' fill='url(%23bg)' stroke='%23F59E0B' stroke-width='5'/>"
    "<polygon points='60,14 102,36 102,80 60,106 18,80 18,36' fill='none' stroke='%23FDE68A' stroke-width='1.5' stroke-dasharray='4,3'/>"
    "<circle cx='60' cy='46' r='16' fill='%23F59E0B'/>"
    "<path d='M52,46 L58,52 L70,40' stroke='%230F172A' stroke-width='4' fill='none' stroke-linecap='round'/>"
    "<text x='60' y='80' font-family='Plus Jakarta Sans,Arial,sans-serif' font-size='14' font-weight='900' fill='%23FFFFFF' text-anchor='middle'>BEA CUKAI</text>"
    "<text x='60' y='94' font-family='Plus Jakarta Sans,Arial,sans-serif' font-size='9' font-weight='700' fill='%23FDE68A' text-anchor='middle'>KPPBC MALANG</text>"
    "</svg>"
)

# ==============================================================================
# BAGIAN 1: FUNGSI PEMBERSIHAN DATA & PERBAIKAN BUG TEKNIS (CROSSCHECKED)
# ==============================================================================
def deduplicate_columns(df_in):
    """Menjamin tidak ada nama kolom duplikat setelah normalisasi huruf besar (.upper())."""
    seen = {}
    new_cols = []
    for c in df_in.columns:
        c_clean = str(c).strip().upper()
        if c_clean not in seen:
            seen[c_clean] = 0
            new_cols.append(c_clean)
        else:
            seen[c_clean] += 1
            new_cols.append(f"{c_clean}_DUP{seen[c_clean]}")
    df_in.columns = new_cols
    return df_in

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
    """
    BUG FIX KRITIS TANGGAL, GRAFIK BULANAN & SLA (TIDAK DIUBAH — 100% AKURAT):
    Memeriksa setiap sel secara presisi:
    1. Jika sudah berupa objek datetime/Timestamp asli, langsung dikembalikan tanpa diubah ke string.
    2. Jika berupa string berformat ISO YYYY-MM-DD, wajib di-parse dengan dayfirst=False.
    3. Jika berupa teks Bahasa Indonesia ('19 Oktober 2026'), diterjemahkan dan di-parse dengan dayfirst=True.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series

    def _parse_single(val):
        if pd.isna(val):
            return pd.NaT
        if isinstance(val, pd.Timestamp):
            return val
        if hasattr(val, 'year') and hasattr(val, 'month') and hasattr(val, 'day'):
            return pd.Timestamp(val.year, val.month, val.day)
        if isinstance(val, (int, float)):
            if 30000 < val < 60000:
                return pd.to_datetime(val, unit='D', origin='1899-12-30', errors='coerce')
            return pd.NaT
        s = str(val).strip()
        if not s or s.lower() in ["nan", "none", "nat", "-", "0", "belum", "proses"]:
            return pd.NaT
        m_iso = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', s)
        if m_iso:
            return pd.Timestamp(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
        for indo, eng in INDO_MONTH_REPLACE.items():
            s = re.sub(rf'\b{indo}\b', eng, s, flags=re.IGNORECASE)
        return pd.to_datetime(s, errors='coerce', dayfirst=True)

    return pd.to_datetime(series.map(_parse_single), errors='coerce')

def extract_agenda_num(series):
    def _extract(x):
        nums = re.findall(r'\d+', str(x))
        return int(nums[-1]) if nums else -1
    return series.map(_extract)

def parse_sisa_hari(series):
    """Mengekstrak angka sisa hari dari nilai numerik maupun teks seperti '13 hari kerja lagi'."""
    def _extract_days(val):
        if pd.isna(val):
            return float('nan')
        if isinstance(val, (int, float)):
            return float(val)
        m = re.search(r'(-?\d+)', str(val))
        return float(m.group(1)) if m else float('nan')
    return series.map(_extract_days)

def normalize_tahun_pc(val):
    """Normalisasi nilai Tahun Pita Cukai (misal 2025.0 -> '2025', '2025 & 2026' -> '2025 & 2026')."""
    if pd.isna(val):
        return "-"
    s = re.sub(r'\.0+$', '', str(val).strip())
    yrs = sorted(set(re.findall(r'20\d{2}', s)))
    if len(yrs) == 1:
        return yrs[0]
    elif len(yrs) > 1:
        return " & ".join(yrs)
    return "-" if s.lower() in ["", "nan", "none", "nat", "-", "0"] else s

def classify_asal_bkc(raw_text):
    """
    Normalisasi Asal BKC:
    - 'Dalam & Luar Pabrik' jika dokumen memuat gabungan keduanya (yang di rincian item dipecah via CK-1 vs CK-5).
    - 'Peredaran Bebas (Luar Pabrik)' jika berasal dari peredaran bebas / market return / luar pabrik / CK-5.
    - 'Dalam Pabrik' jika berasal dari dalam pabrik / produksi / CK-1 (atau default).
    """
    if pd.isna(raw_text):
        return "Dalam Pabrik"
    s = str(raw_text).strip().upper()
    has_dalam = any(k in s for k in ["DALAM PABRIK", "DALAM DAN LUAR", "DALAM & LUAR", "CK-1", "CK1"])
    has_luar = any(k in s for k in ["PEREDARAN BEBAS", "LUAR PABRIK", "MARKET RETURN", "RETURN", "PASAR", "BEBAS", "CK-5", "CK5"])
    if has_dalam and has_luar:
        return "Dalam & Luar Pabrik"
    if has_luar:
        return "Peredaran Bebas (Luar Pabrik)"
    return "Dalam Pabrik"

def classify_kegiatan_lokasi(raw_text):
    """
    Normalisasi Jenis Kegiatan & Lokasi Pemusnahan ke dalam 3 kategori standar:
    1. 'Pemusnahan - Luar Pabrik'
    2. 'Pemusnahan - Dalam Pabrik'
    3. 'Pengolahan Kembali'
    """
    if pd.isna(raw_text):
        return "Pengolahan Kembali"
    s = str(raw_text).strip().upper()
    is_musnah = any(k in s for k in ["MUSNAH", "PEMUSNAHAN", "DIMUSNAHKAN"])
    is_luar = any(k in s for k in ["LUAR PABRIK", "DI LUAR", "EKSTERNAL"])
    if is_musnah and is_luar:
        return "Pemusnahan - Luar Pabrik"
    if is_musnah:
        return "Pemusnahan - Dalam Pabrik"
    return "Pengolahan Kembali"

def fmt_exact_rp(val):
    if pd.isna(val) or val == 0:
        return "Rp 0"
    return f"-Rp {abs(val):,.0f}".replace(",", ".") if val < 0 else f"Rp {abs(val):,.0f}".replace(",", ".")

def fmt_exact_bks(val):
    if pd.isna(val) or val == 0:
        return "0"
    return f"-{abs(val):,.0f}".replace(",", ".") if val < 0 else f"{abs(val):,.0f}".replace(",", ".")

def fmt_miliar_short(val):
    if pd.isna(val) or val == 0:
        return "Rp 0"
    sign = "-" if val < 0 else ""
    v = abs(val)
    if v >= 1_000_000_000_000:
        return f"{sign}Rp {v/1_000_000_000_000:.2f} T".replace(".", ",")
    elif v >= 1_000_000_000:
        return f"{sign}Rp {v/1_000_000_000:.2f} M".replace(".", ",")
    elif v >= 1_000_000:
        return f"{sign}Rp {v/1_000_000:.2f} Jt".replace(".", ",")
    return fmt_exact_rp(val)

def fmt_axis_rp_indo(val):
    """Format label sumbu Y grafik dalam Bahasa Indonesia (Rp X,X M / Rp X,X Jt) tanpa singkatan 'B'."""
    if pd.isna(val) or val <= 0:
        return "Rp 0"
    if val >= 1_000_000_000_000:
        return f"Rp {val/1_000_000_000_000:.1f} T".replace(".", ",")
    elif val >= 1_000_000_000:
        return f"Rp {val/1_000_000_000:.1f} M".replace(".", ",")
    elif val >= 1_000_000:
        return f"Rp {val/1_000_000:.0f} Jt".replace(".", ",")
    return f"Rp {val:,.0f}".replace(",", ".")

def fmt_bks_short(val):
    if pd.isna(val) or val == 0:
        return "0 Bks"
    val = abs(val)
    if val >= 1_000_000_000:
        return f"{val/1_000_000_000:.2f} M Bks".replace(".", ",")
    elif val >= 1_000_000:
        return f"{val/1_000_000:.2f} Jt Bks".replace(".", ",")
    return f"{val:,.0f} Bks".replace(",", ".")

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
    final_str = f"{real_str}<div class='kpi-alias-sub'>≈ {alias}</div>"
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
    final_str = f"{real_str} <span style='font-size: 13px; font-weight: 500;'>Bks</span><div class='kpi-alias-sub'>≈ {alias} Bks</div>"
    return f"-{final_str}" if is_negative else final_str

def clean_num(series):
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0.0).astype(float)
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
    return series.map(parse_value).astype(float)

# ==============================================================================
# PEMBACAAN DATA CLOUD GOOGLE DRIVE (GUARDRAIL: FILE ID & LOGIKA TETAP UTUH)
# ==============================================================================
@st.cache_data(ttl=300, show_spinner="Memuat Database Realisasi...")
def load_data():
    sheet_id = "15vLiGh3HzvYPF5Ru_b9ndD2PQKBUrXok"
    url_merge = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    with pd.ExcelFile(url_merge) as xls:
        df_main = pd.read_excel(xls, sheet_name="DATABASE MERGE")
        df_main = deduplicate_columns(df_main)
        sheet_map = {s.strip().upper(): s for s in xls.sheet_names}
        if "DETAIL" in sheet_map:
            df_detail = pd.read_excel(xls, sheet_name=sheet_map["DETAIL"])
            df_detail = deduplicate_columns(df_detail)
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
    col_dtl_agenda = "AGENDA" if "AGENDA" in df_detail.columns else ("NO. AGENDA" if "NO. AGENDA" in df_detail.columns else df_detail.columns[0])
    df_detail[col_dtl_agenda] = clean_doc_str(df_detail[col_dtl_agenda])
    for c_dtl_id in ["AGENDA", "NO. AGENDA", "NO_PBCK-3", "NO_PBCK_3", "BACK-3", "NO_BACK-3", "NO_CK-2", "NO_CK2"]:
        if c_dtl_id in df_detail.columns:
            df_detail[c_dtl_id] = clean_doc_str(df_detail[c_dtl_id])
    if "TANGGAL" in df_detail.columns:
        df_detail["TANGGAL"] = parse_indo_date(df_detail["TANGGAL"]).dt.strftime('%d/%m/%Y').fillna("-")

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

# Normalisasi spasi nama perusahaan agar pengelompokan & ranking konsisten
if col_pabrik in df.columns:
    df[col_pabrik] = df[col_pabrik].astype(str).str.strip()

# Konversi Kolom Tanggal (Bebas Bug Swap Bulan/Hari ISO)
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

# PERBAIKAN LOGIKA AKUNTANSI #1: Hanya hitung BUNGKUS_TMS pada baris yang sudah berstatus TERBIT
df['BUNGKUS_TMS'] = np.where(
    df['STATUS_CK2_BOOL'] == "TERBIT",
    (df[col_bks_pbck3] - df[col_bks_ck2]).clip(lower=0),
    0.0
)

# ==============================================================================
# DETEKSI & INTEGRASI OTOMATIS PARAMETER SEKUNDER:
# 1. TAHUN PITA CUKAI (PC 2025 vs PC 2026)
# 2. ASAL BKC (DALAM PABRIK vs PEREDARAN BEBAS / LUAR PABRIK)
# 3. JENIS KEGIATAN & LOKASI PEMUSNAHAN (PENGOLAHAN KEMBALI vs PEMUSNAHAN DALAM/LUAR)
# ==============================================================================
pc_candidates_main = [
    c for c in df.columns
    if any(k in c for k in ["TAHUN_PC", "TAHUN PC", "THN_PC", "THN PC", "TAHUN PITA", "TAHUN_PITA"])
]
col_tahun_pc_main = pc_candidates_main[0] if pc_candidates_main else None

if col_tahun_pc_main:
    df['TAHUN_PC_STR'] = df[col_tahun_pc_main].map(normalize_tahun_pc)
else:
    df['TAHUN_PC_STR'] = "-"

# Deteksi Kolom Asal BKC di df (DATABASE MERGE)
asal_candidates_main = [
    c for c in df.columns
    if any(k in c for k in ["ASAL", "POSISI_BKC", "SUMBER", "PEREDARAN", "STATUS_BKC", "KATEGORI_BKC", "DALAM_LUAR", "LOKASI_ASAL"])
]
if asal_candidates_main:
    combined_asal_series = df[asal_candidates_main].fillna("").astype(str).agg(" | ".join, axis=1)
    df['ASAL_BKC_STR'] = combined_asal_series.map(classify_asal_bkc)
else:
    df['ASAL_BKC_STR'] = "Dalam Pabrik"

# Deteksi Kolom Kegiatan & Lokasi Pemusnahan di df (DATABASE MERGE)
giat_candidates_main = [
    c for c in df.columns
    if any(k in c for k in [
        "SKEMA_PELAKSANAAN", "TENTANG_KEP", "DIAPAKAN", "HAL_SURAT",
        "KEGIATAN", "JENIS_KEGIATAN", "TUJUAN", "PENYELESAIAN", "PEMUSNAHAN"
    ])
]
if giat_candidates_main:
    combined_giat_series = df[giat_candidates_main].fillna("").astype(str).agg(" | ".join, axis=1)
    df['KEGIATAN_LOKASI_STR'] = combined_giat_series.map(classify_kegiatan_lokasi)
else:
    df['KEGIATAN_LOKASI_STR'] = "Pengolahan Kembali"

# Pemetaan & Agregasi Rincian Item per Tahun PC & Asal BKC (CK-1 vs CK-5) dari df_detail (Sheet DETAIL)
if not df_detail.empty:
    col_dtl_agenda_key = "AGENDA" if "AGENDA" in df_detail.columns else ("NO. AGENDA" if "NO. AGENDA" in df_detail.columns else df_detail.columns[0])
    col_dtl_pc = next((c for c in df_detail.columns if "TAHUN" in c and ("PC" in c or "PITA" in c)), None)
    if col_dtl_pc is None:
        col_dtl_pc = next((c for c in df_detail.columns if c == "TAHUN"), None)

    col_dtl_asal_item = next((c for c in df_detail.columns if c == "ASAL"), None)
    col_dtl_dok_asal = next((c for c in df_detail.columns if "DOKUMEN ASAL" in c), None)

    col_dtl_bks_pbck3 = next((c for c in df_detail.columns if "KEMASAN" in c and "PBCK" in c), None)
    col_dtl_bks_ms = next((c for c in df_detail.columns if "KEMASAN" in c and "BACK" in c), None)
    col_dtl_cukai_pbck3 = next((c for c in df_detail.columns if "CUKAI" in c and "PBCK" in c and "TOTAL" not in c and "NILAI" not in c), None)
    col_dtl_cukai_ms = next((c for c in df_detail.columns if "CUKAI" in c and "BACK" in c), None)

    if col_dtl_pc and all([col_dtl_bks_pbck3, col_dtl_bks_ms, col_dtl_cukai_pbck3, col_dtl_cukai_ms]):
        dtl_work = df_detail[df_detail[col_dtl_agenda_key] != "-"].copy()
        dtl_work['_YR_NUM'] = pd.to_numeric(dtl_work[col_dtl_pc], errors='coerce')
        dtl_work = dtl_work[dtl_work['_YR_NUM'].isin([2025, 2026])].copy()
        dtl_work['_YR_INT'] = dtl_work['_YR_NUM'].astype(int)

        if col_dtl_asal_item:
            s_asal_dtl = dtl_work[col_dtl_asal_item].astype(str).str.upper().str.strip()
            dtl_work['_ASAL_GRP'] = np.where(
                s_asal_dtl.str.contains("CK-5|CK5|LUAR|BEBAS", regex=True),
                "LUAR",
                "DALAM"
            )
        elif col_dtl_dok_asal:
            s_dok_dtl = dtl_work[col_dtl_dok_asal].astype(str).str.upper().str.strip()
            dtl_work['_ASAL_GRP'] = np.where(s_dok_dtl.str.contains("LUAR|BEBAS", regex=True), "LUAR", "DALAM")
        else:
            dtl_work['_ASAL_GRP'] = "DALAM"

        for c_dnum in [col_dtl_bks_pbck3, col_dtl_bks_ms, col_dtl_cukai_pbck3, col_dtl_cukai_ms]:
            dtl_work[c_dnum] = clean_num(dtl_work[c_dnum])

        dtl_active = dtl_work[(dtl_work[col_dtl_bks_pbck3] > 0) | (dtl_work[col_dtl_cukai_pbck3] > 0) | (dtl_work[col_dtl_cukai_ms] > 0)].copy()

        # Pemetaan label tahun PC dari detail jika di df utama belum terisi
        dtl_yr_map = (
            dtl_active.groupby(col_dtl_agenda_key)['_YR_INT']
            .apply(lambda s: " & ".join(str(y) for y in sorted(set(s))))
            .to_dict()
        )
        mask_missing_pc = df['TAHUN_PC_STR'].isin(["-", "", "nan"])
        if mask_missing_pc.any():
            df.loc[mask_missing_pc, 'TAHUN_PC_STR'] = df.loc[mask_missing_pc, col_agenda].map(lambda a: dtl_yr_map.get(a, "-"))

        # 1) Agregasi Detail per Tahun PC (2025 vs 2026)
        grp_dtl_pc = dtl_active.groupby([col_dtl_agenda_key, '_YR_INT']).agg(
            BKS_PBCK3=(col_dtl_bks_pbck3, 'sum'),
            BKS_MS=(col_dtl_bks_ms, 'sum'),
            CUKAI_PBCK3=(col_dtl_cukai_pbck3, 'sum'),
            CUKAI_MS=(col_dtl_cukai_ms, 'sum')
        ).unstack(fill_value=0.0)
        grp_dtl_pc.columns = [f"_DTL_{m}_{y}" for m, y in grp_dtl_pc.columns]
        grp_dtl_pc = grp_dtl_pc.reset_index().rename(columns={col_dtl_agenda_key: "_AGENDA_JOIN_KEY_PC"})
        df = pd.merge(df, grp_dtl_pc, left_on=col_agenda, right_on="_AGENDA_JOIN_KEY_PC", how="left")

        # 2) Agregasi Detail per Asal BKC (DALAM [CK-1] vs LUAR [CK-5])
        grp_dtl_asal = dtl_active.groupby([col_dtl_agenda_key, '_ASAL_GRP']).agg(
            BKS_PBCK3=(col_dtl_bks_pbck3, 'sum'),
            BKS_MS=(col_dtl_bks_ms, 'sum'),
            CUKAI_PBCK3=(col_dtl_cukai_pbck3, 'sum'),
            CUKAI_MS=(col_dtl_cukai_ms, 'sum')
        ).unstack(fill_value=0.0)
        grp_dtl_asal.columns = [f"_DTL_ASAL_{m}_{a}" for m, a in grp_dtl_asal.columns]
        grp_dtl_asal = grp_dtl_asal.reset_index().rename(columns={col_dtl_agenda_key: "_AGENDA_JOIN_KEY_ASAL"})
        df = pd.merge(df, grp_dtl_asal, left_on=col_agenda, right_on="_AGENDA_JOIN_KEY_ASAL", how="left")

for c_init in [
    "_DTL_BKS_PBCK3_2025", "_DTL_BKS_PBCK3_2026",
    "_DTL_BKS_MS_2025", "_DTL_BKS_MS_2026",
    "_DTL_CUKAI_PBCK3_2025", "_DTL_CUKAI_PBCK3_2026",
    "_DTL_CUKAI_MS_2025", "_DTL_CUKAI_MS_2026",
    "_DTL_ASAL_BKS_PBCK3_DALAM", "_DTL_ASAL_BKS_PBCK3_LUAR",
    "_DTL_ASAL_BKS_MS_DALAM", "_DTL_ASAL_BKS_MS_LUAR",
    "_DTL_ASAL_CUKAI_PBCK3_DALAM", "_DTL_ASAL_CUKAI_PBCK3_LUAR",
    "_DTL_ASAL_CUKAI_MS_DALAM", "_DTL_ASAL_CUKAI_MS_LUAR"
]:
    if c_init not in df.columns:
        df[c_init] = 0.0
    df[c_init] = df[c_init].fillna(0.0)

# Rekonsiliasi Presisi Nilai & Bungkus PC 2025 vs PC 2026 per Dokumen agar 100% Akuntabel = Total Dokumen Utama
for main_col, d25_col, d26_col, out25_col, out26_col in [
    (col_bks_pbck3, "_DTL_BKS_PBCK3_2025", "_DTL_BKS_PBCK3_2026", "PC2025_BKS_PBCK3", "PC2026_BKS_PBCK3"),
    (col_bks_ck2, "_DTL_BKS_MS_2025", "_DTL_BKS_MS_2026", "PC2025_BKS_MS", "PC2026_BKS_MS"),
    (col_cukai_pbck3, "_DTL_CUKAI_PBCK3_2025", "_DTL_CUKAI_PBCK3_2026", "PC2025_CUKAI_PBCK3", "PC2026_CUKAI_PBCK3"),
    (col_cukai_ck2, "_DTL_CUKAI_MS_2025", "_DTL_CUKAI_MS_2026", "PC2025_CUKAI_MS", "PC2026_CUKAI_MS"),
]:
    is_pure_2025 = df['TAHUN_PC_STR'] == "2025"
    is_pure_2026 = df['TAHUN_PC_STR'] == "2026"
    has_dtl_split = (df[d25_col] + df[d26_col]) > 0
    only_dtl_25 = has_dtl_split & (df[d25_col] > 0) & (df[d26_col] == 0)
    only_dtl_26 = has_dtl_split & (df[d26_col] > 0) & (df[d25_col] == 0)
    both_dtl = has_dtl_split & (df[d25_col] > 0) & (df[d26_col] > 0)

    df[out25_col] = np.where(
        is_pure_2025, df[main_col],
        np.where(is_pure_2026, 0.0, np.where(only_dtl_25, df[main_col], np.where(both_dtl, df[d25_col], 0.0)))
    )
    df[out26_col] = np.where(
        is_pure_2026, df[main_col],
        np.where(is_pure_2025, 0.0, np.where(only_dtl_26, df[main_col], np.where(both_dtl, df[d26_col], 0.0)))
    )

tot_bks_row = (df['PC2025_BKS_PBCK3'] + df['PC2026_BKS_PBCK3']).replace(0, np.nan)
df['PC2025_BP'] = (df[col_biaya_pengganti] * (df['PC2025_BKS_PBCK3'] / tot_bks_row)).fillna(0.0)
df['PC2026_BP'] = (df[col_biaya_pengganti] * (df['PC2026_BKS_PBCK3'] / tot_bks_row)).fillna(0.0)

df['HAS_PC_2025'] = df['TAHUN_PC_STR'].astype(str).str.contains("2025", na=False) | (df['PC2025_BKS_PBCK3'] > 0)
df['HAS_PC_2026'] = df['TAHUN_PC_STR'].astype(str).str.contains("2026", na=False) | (df['PC2026_BKS_PBCK3'] > 0)

# Rekonsiliasi Presisi Nilai & Bungkus Asal BKC (Dalam Pabrik vs Peredaran Bebas / Luar Pabrik)
for main_col, d_dlm_col, d_luar_col, out_dlm_col, out_luar_col in [
    (col_bks_pbck3, "_DTL_ASAL_BKS_PBCK3_DALAM", "_DTL_ASAL_BKS_PBCK3_LUAR", "ASAL_DALAM_BKS_PBCK3", "ASAL_LUAR_BKS_PBCK3"),
    (col_bks_ck2, "_DTL_ASAL_BKS_MS_DALAM", "_DTL_ASAL_BKS_MS_LUAR", "ASAL_DALAM_BKS_MS", "ASAL_LUAR_BKS_MS"),
    (col_cukai_pbck3, "_DTL_ASAL_CUKAI_PBCK3_DALAM", "_DTL_ASAL_CUKAI_PBCK3_LUAR", "ASAL_DALAM_CUKAI_PBCK3", "ASAL_LUAR_CUKAI_PBCK3"),
    (col_cukai_ck2, "_DTL_ASAL_CUKAI_MS_DALAM", "_DTL_ASAL_CUKAI_MS_LUAR", "ASAL_DALAM_CUKAI_MS", "ASAL_LUAR_CUKAI_MS"),
]:
    is_pure_dalam = df['ASAL_BKC_STR'] == "Dalam Pabrik"
    is_pure_luar = df['ASAL_BKC_STR'] == "Peredaran Bebas (Luar Pabrik)"
    has_asal_split = (df[d_dlm_col] + df[d_luar_col]) > 0
    only_dlm = has_asal_split & (df[d_dlm_col] > 0) & (df[d_luar_col] == 0)
    only_luar = has_asal_split & (df[d_luar_col] > 0) & (df[d_dlm_col] == 0)
    both_asal = has_asal_split & (df[d_dlm_col] > 0) & (df[d_luar_col] > 0)

    df[out_dlm_col] = np.where(
        is_pure_dalam, df[main_col],
        np.where(is_pure_luar, 0.0, np.where(only_dlm, df[main_col], np.where(both_asal, df[d_dlm_col], df[main_col] * 0.5)))
    )
    df[out_luar_col] = np.where(
        is_pure_luar, df[main_col],
        np.where(is_pure_dalam, 0.0, np.where(only_luar, df[main_col], np.where(both_asal, df[d_luar_col], df[main_col] * 0.5)))
    )

tot_asal_bks_row = (df['ASAL_DALAM_BKS_PBCK3'] + df['ASAL_LUAR_BKS_PBCK3']).replace(0, np.nan)
df['ASAL_DALAM_BP'] = (df[col_biaya_pengganti] * (df['ASAL_DALAM_BKS_PBCK3'] / tot_asal_bks_row)).fillna(0.0)
df['ASAL_LUAR_BP'] = (df[col_biaya_pengganti] * (df['ASAL_LUAR_BKS_PBCK3'] / tot_asal_bks_row)).fillna(0.0)

df['HAS_ASAL_DALAM'] = (df['ASAL_BKC_STR'].isin(["Dalam Pabrik", "Dalam & Luar Pabrik"])) | (df['ASAL_DALAM_BKS_PBCK3'] > 0)
df['HAS_ASAL_LUAR'] = (df['ASAL_BKC_STR'].isin(["Peredaran Bebas (Luar Pabrik)", "Dalam & Luar Pabrik"])) | (df['ASAL_LUAR_BKS_PBCK3'] > 0)

# ==============================================================================
# ZONA SIDEBAR KIRI GELAP (#1E293B) — PANEL NAVIGASI, TEMA & FILTER EKSEKUTIF
# ==============================================================================
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <div style="display:flex; align-items:center; gap:12px;">
            <img src="{LOGO_URL}" width="46" referrerpolicy="no-referrer"
                 style="object-fit:contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));"
                 onerror="this.onerror=null; this.src='{BC_SVG_FALLBACK}';">
            <div>
                <div style="font-size:13.5px; font-weight:800; letter-spacing:0.6px; color:#F8FAFC;">KPPBC TMC MALANG</div>
                <div style="font-size:11px; color:#94A3B8; font-weight:600;">Executive Analytics Suite</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🌓 Mode Tampilan Layar")
    theme_choice = st.radio(
        "Pilih Tema:",
        ["☀️ Morning Mode (Terang)", "🌙 Night Mode (Gelap)"],
        index=0,
        label_visibility="collapsed"
    )
    is_night_mode = "Night Mode" in theme_choice

    st.markdown("---")
    st.markdown("### 🎛️ Filter Entitas & Parameter")
    pabrik_list = ["Semua Pabrik"] + sorted([
        str(p).strip() for p in df[col_pabrik].dropna().unique().tolist()
        if str(p).strip().lower() not in ["", "-", "nan", "none"]
    ])
    selected_pabrik = st.selectbox("🏢 Pilih Pabrik / Perusahaan:", pabrik_list)

    tahun_tersedia = [2026]
    if df['TAHUN_ACUAN'].dropna().nunique() > 0:
        tahun_tersedia = sorted(df['TAHUN_ACUAN'].dropna().unique().astype(int).tolist(), reverse=True)
    selected_tahun = st.selectbox("📅 Pilih Tahun Anggaran:", tahun_tersedia)

    # FILTER SEKUNDER: Tahun Pita Cukai (PC 2025 vs PC 2026)
    opsi_tahun_pc = ["Semua Tahun PC (Gabungan)", "Pita Cukai 2025", "Pita Cukai 2026"]
    extra_pc_years = sorted({
        y for val in df['TAHUN_PC_STR'].dropna().unique()
        for y in re.findall(r'20\d{2}', str(val))
        if y not in ("2025", "2026")
    })
    for ey in extra_pc_years:
        opsi_tahun_pc.append(f"Pita Cukai {ey}")
    selected_tahun_pc = st.selectbox("🏷️ Tahun Pita Cukai (PC):", opsi_tahun_pc, index=0)

    # FILTER BARU #1: Asal BKC (Dalam Pabrik vs Peredaran Bebas / Luar Pabrik)
    opsi_asal_bkc = [
        "Semua Asal BKC (Gabungan)",
        "Dalam Pabrik",
        "Peredaran Bebas (Luar Pabrik)"
    ]
    selected_asal_bkc = st.selectbox("🏭 Asal BKC (PBCK-3):", opsi_asal_bkc, index=0)

    # FILTER BARU #2: Kegiatan & Lokasi Pemusnahan
    opsi_kegiatan = [
        "Semua Kegiatan (Gabungan)",
        "Pengolahan Kembali",
        "Semua Pemusnahan (Gabungan)",
        "Pemusnahan - Dalam Pabrik",
        "Pemusnahan - Luar Pabrik"
    ]
    selected_kegiatan = st.selectbox("🔥 Kegiatan & Lokasi:", opsi_kegiatan, index=0)

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
# INJEKSI CSS DINAMIS: MORNING MODE vs NIGHT MODE + PERBAIKAN TOMBOL UNDUH CSV
# ==============================================================================
if is_night_mode:
    app_bg = "#0B1120"
    card_bg = "#1E293B"
    card_border = "#334155"
    text_primary = "#F8FAFC"
    text_secondary = "#94A3B8"
    pill_default_bg = "#0F172A"
    pill_default_text = "#E2E8F0"
    fin_green_bg = "rgba(6, 95, 70, 0.28)"
    fin_green_border = "#059669"
    fin_green_text = "#34D399"
    fin_amber_text = "#FBBF24"
    track_bg = "#334155"
    divider_col = "#334155"
    chart_grid = "#334155"
    chart_font = "#E2E8F0"
    input_main_bg = "#0F172A"
    input_main_text = "#F8FAFC"
    input_placeholder = "#94A3B8"
    donut_other_slice = "#334155"
    insight_banner_bg = "rgba(15, 23, 42, 0.72)"
    insight_banner_border = "#334155"
    pc_mini_bg = "rgba(15, 23, 42, 0.65)"
    pc_mini_border = "#334155"
    pc_mini_text = "#E2E8F0"
    tax_box_bg = "rgba(15, 23, 42, 0.55)"
    tax_rose_bg = "rgba(244, 63, 94, 0.14)"
    tax_rose_border = "rgba(244, 63, 94, 0.45)"
else:
    app_bg = "#F4F7FA"
    card_bg = "#FFFFFF"
    card_border = "#E2E8F0"
    text_primary = "#0F172A"
    text_secondary = "#64748B"
    pill_default_bg = "#F8FAFC"
    pill_default_text = "#1E293B"
    fin_green_bg = "#F0FDF4"
    fin_green_border = "#BBF7D0"
    fin_green_text = "#065F46"
    fin_amber_text = "#92400E"
    track_bg = "#E2E8F0"
    divider_col = "#F1F5F9"
    chart_grid = "#F1F5F9"
    chart_font = "#334155"
    input_main_bg = "#FFFFFF"
    input_main_text = "#0F172A"
    input_placeholder = "#64748B"
    donut_other_slice = "#CBD5E1"
    insight_banner_bg = "#F8FAFC"
    insight_banner_border = "#E2E8F0"
    pc_mini_bg = "#F8FAFC"
    pc_mini_border = "#E2E8F0"
    pc_mini_text = "#334155"
    tax_box_bg = "#F8FAFC"
    tax_rose_bg = "#FFF1F2"
    tax_rose_border = "#FECDD3"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}

/* 1. Tema Global Background (Morning / Night Mode) */
.stApp {{
    background-color: {app_bg} !important;
    color: {text_primary} !important;
}}

.block-container {{
    padding-top: 1.4rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 98% !important;
}}

/* 2. Dark Navigation Sidebar (#1E293B) & Perbaikan Mutlak Kontras Dropdown */
section[data-testid="stSidebar"] {{
    background-color: #1E293B !important;
    border-right: 1px solid #0F172A !important;
}}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {{
    color: #F8FAFC !important;
}}

section[data-testid="stSidebar"] hr {{
    border-color: rgba(255, 255, 255, 0.14) !important;
    margin: 1rem 0 !important;
}}

/* PERBAIKAN DROPDOWN SELECTBOX SIDEBAR: Latar Gelap (#0F172A) & Teks Putih Terang (#F8FAFC) */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    background-color: #0F172A !important;
    border: 1.5px solid #475569 !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {{
    border-color: #38BDF8 !important;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] * {{
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 600 !important;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] svg {{
    fill: #38BDF8 !important;
}}

/* Menu Popover / Daftar Pilihan Saat Dropdown Diklik (Di Luar Sidebar) */
div[data-baseweb="popover"] ul,
div[data-baseweb="menu"],
ul[role="listbox"] {{
    background-color: #1E293B !important;
    border: 1px solid #475569 !important;
    border-radius: 8px !important;
}}

div[data-baseweb="popover"] li,
ul[role="listbox"] li,
li[role="option"] {{
    color: #F8FAFC !important;
    background-color: #1E293B !important;
    font-weight: 500 !important;
}}

div[data-baseweb="popover"] li:hover,
ul[role="listbox"] li:hover,
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {{
    background-color: #2563EB !important;
    color: #FFFFFF !important;
}}

/* Radio Button di Sidebar */
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    background: rgba(15, 23, 42, 0.65) !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    transition: all 0.2s ease !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
    color: #F8FAFC !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background: rgba(59, 130, 246, 0.22) !important;
    border-color: #38BDF8 !important;
}}

/* Tombol Segarkan Data Cloud di Sidebar */
section[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #3B82F6 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1rem !important;
    width: 100% !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.2s ease !important;
}}

section[data-testid="stSidebar"] .stButton > button:hover {{
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.38) !important;
}}

/* PERBAIKAN BUG VISUAL TOMBOL UNDUH CSV & KOTAK PENCARIAN DI NIGHT/MORNING MODE */
div[data-testid="stDownloadButton"] > button {{
    background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #34D399 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    padding: 0.52rem 1rem !important;
    width: 100% !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
    transition: all 0.2s ease !important;
}}

div[data-testid="stDownloadButton"] > button *,
div[data-testid="stDownloadButton"] > button p,
div[data-testid="stDownloadButton"] > button span {{
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
}}

div[data-testid="stDownloadButton"] > button:hover {{
    background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
    border-color: #6EE7B7 !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.38) !important;
}}

div[data-testid="stDownloadButton"] > button:active,
div[data-testid="stDownloadButton"] > button:focus {{
    background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
    color: #FFFFFF !important;
}}

/* Perbaikan Kotak Pencarian di Zona 5 agar Kontras di Night Mode & Morning Mode */
div[data-testid="stTextInput"] div[data-baseweb="input"] {{
    background-color: {input_main_bg} !important;
    border: 1.5px solid {card_border} !important;
    border-radius: 8px !important;
}}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {{
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
}}

div[data-testid="stTextInput"] input {{
    background-color: transparent !important;
    color: {input_main_text} !important;
    -webkit-text-fill-color: {input_main_text} !important;
    font-weight: 600 !important;
}}

div[data-testid="stTextInput"] input::placeholder {{
    color: {input_placeholder} !important;
    -webkit-text-fill-color: {input_placeholder} !important;
    opacity: 1 !important;
}}

/* Brand Header & SLA Box di Sidebar */
.sidebar-brand {{
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.75) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 16px;
}}

.sidebar-sla-box {{
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-left: 4px solid #06B6D4;
    border-radius: 10px;
    padding: 12px 14px;
    margin-top: 10px;
    margin-bottom: 14px;
    font-size: 12px;
}}

/* 3. Top Header Card */
.top-header-card {{
    background: {card_bg};
    border: 1px solid {card_border};
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
}}

.header-left {{
    display: flex;
    align-items: center;
    gap: 18px;
}}

.header-title {{
    margin: 0;
    color: {text_primary};
    font-size: 21px;
    font-weight: 800;
    letter-spacing: -0.3px;
}}

.header-subtitle {{
    margin: 3px 0 0 0;
    color: {text_secondary};
    font-size: 13px;
    font-weight: 500;
}}

.header-law {{
    display: inline-block;
    margin-top: 6px;
    font-size: 11.5px;
    font-weight: 700;
    color: #1E3A8A;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    padding: 3px 10px;
    border-radius: 6px;
}}

.header-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}}

.status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid {card_border};
    background: {pill_default_bg};
    color: {pill_default_text};
}}

.pill-green {{
    background: #ECFDF5;
    color: #047857;
    border-color: #A7F3D0;
}}

.pill-red {{
    background: #FEF2F2;
    color: #B91C1C;
    border-color: #FECACA;
}}

.pill-blue {{
    background: #EFF6FF;
    color: #1D4ED8;
    border-color: #BFDBFE;
}}

.pill-amber {{
    background: #FFFBEB;
    color: #B45309;
    border-color: #FDE68A;
}}

.pill-purple {{
    background: #F5F3FF;
    color: #6D28D9;
    border-color: #DDD6FE;
}}

/* 4. ZONA 1: 4 Top KPI Cards Berwarna (Gaya Adminty dengan Solid Footer Bar) */
.adminty-card {{
    background: {card_bg};
    border: 1px solid {card_border};
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 156px;
}}

.adminty-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
}}

.adminty-body {{
    padding: 18px 20px 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}}

.adminty-title {{
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: {text_secondary};
    margin-bottom: 6px;
}}

.adminty-value {{
    font-size: 26px;
    font-weight: 800;
    color: {text_primary};
    line-height: 1.15;
}}

.adminty-unit {{
    font-size: 13px;
    font-weight: 600;
    color: {text_secondary};
}}

.adminty-subnote {{
    font-size: 11px;
    font-weight: 600;
    color: {text_secondary};
    margin-top: 5px;
}}

.pc-mini-badge {{
    display: inline-block;
    background: {pc_mini_bg};
    border: 1px solid {pc_mini_border};
    color: {pc_mini_text};
    padding: 2px 7px;
    border-radius: 6px;
    font-size: 10.5px;
    font-weight: 700;
    margin-top: 2px;
}}

.adminty-icon-circle {{
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
}}

.adminty-footer {{
    padding: 8px 20px;
    color: #FFFFFF;
    font-size: 11.5px;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.footer-orange {{ background: linear-gradient(90deg, #F97316, #FB923C); }}
.footer-emerald {{ background: linear-gradient(90deg, #10B981, #34D399); }}
.footer-rose {{ background: linear-gradient(90deg, #F43F5E, #FB7185); }}
.footer-cyan {{ background: linear-gradient(90deg, #06B6D4, #22D3EE); }}

.icon-orange {{ background: #FFF7ED; color: #EA580C; }}
.icon-emerald {{ background: #ECFDF5; color: #059669; }}
.icon-rose {{ background: #FFF1F2; color: #E11D48; }}
.icon-cyan {{ background: #ECFEFF; color: #0891B2; }}

/* 5. ZONA 2: Right Stacked Financial Cards ala Admindek */
.admindek-fin-card {{
    background: {card_bg};
    border: 1px solid {card_border};
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.admindek-fin-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.1);
}}

.fin-label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: {text_secondary};
    margin-bottom: 4px;
}}

.fin-val {{
    font-size: 18px;
    font-weight: 800;
    color: {text_primary};
    line-height: 1.2;
}}

.kpi-alias-sub {{
    font-size: 12px;
    color: {text_secondary};
    font-weight: 700;
    margin-top: 2px;
}}

.fin-sub {{
    font-size: 11px;
    font-weight: 600;
    color: {text_secondary};
    margin-top: 4px;
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    align-items: center;
}}

.fin-pc-strip {{
    font-size: 10.5px;
    font-weight: 700;
    color: {pc_mini_text};
    background: {pc_mini_bg};
    border: 1px solid {pc_mini_border};
    border-radius: 6px;
    padding: 2px 7px;
    margin-top: 4px;
    display: inline-block;
}}

.fin-icon-box {{
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
}}

.box-blue {{ background: linear-gradient(135deg, #1E3A8A, #3B82F6); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.28); }}
.box-emerald {{ background: linear-gradient(135deg, #047857, #10B981); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.28); }}
.box-amber {{ background: linear-gradient(135deg, #B45309, #F59E0B); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.28); }}

/* 6. ZONA 3: Horizontal Progress Bar Strip ala Admindek */
.progress-strip-item {{
    padding: 8px 12px;
    border-right: 1px solid {divider_col};
}}

.progress-strip-label {{
    font-size: 11.5px;
    font-weight: 700;
    color: {text_secondary};
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 4px;
}}

.progress-strip-val {{
    font-size: 19px;
    font-weight: 800;
    color: {text_primary};
    margin-bottom: 6px;
}}

.progress-track {{
    width: 100%;
    height: 8px;
    background-color: {track_bg};
    border-radius: 999px;
    overflow: hidden;
    margin-top: 6px;
}}

.progress-fill {{
    height: 100%;
    border-radius: 999px;
    transition: width 0.5s ease;
}}

.progress-meta {{
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 600;
    color: {text_secondary};
    margin-top: 5px;
}}

.progress-pc-sub {{
    font-size: 10.5px;
    font-weight: 700;
    color: {text_secondary};
    margin-top: 3px;
}}

/* 7. ZONA 3B: Executive Taxonomy & Location Strip (Asal BKC & Kegiatan/Lokasi Pemusnahan) */
.taxonomy-card-wrap {{
    padding: 6px 10px 8px 10px;
}}

.taxonomy-bar-multi {{
    width: 100%;
    height: 9px;
    background-color: {track_bg};
    border-radius: 999px;
    overflow: hidden;
    display: flex;
    margin: 8px 0 12px 0;
}}

.taxonomy-grid-2 {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}}

.taxonomy-grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}}

.taxonomy-mini-box {{
    background: {tax_box_bg};
    border: 1px solid {card_border};
    border-radius: 10px;
    padding: 10px 12px;
    transition: transform 0.2s ease;
}}

.taxonomy-mini-box:hover {{
    transform: translateY(-2px);
}}

.taxonomy-mini-box-rose {{
    background: {tax_rose_bg};
    border: 1.5px solid {tax_rose_border};
    border-radius: 10px;
    padding: 10px 12px;
    transition: transform 0.2s ease;
}}

.taxonomy-mini-box-rose:hover {{
    transform: translateY(-2px);
}}

.tax-box-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 800;
    color: {text_secondary};
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 4px;
}}

.tax-box-main {{
    font-size: 15.5px;
    font-weight: 800;
    color: {text_primary};
    line-height: 1.25;
}}

.tax-box-sub {{
    font-size: 10.5px;
    font-weight: 600;
    color: {text_secondary};
    margin-top: 3px;
}}

/* Executive Insight Banner di Bawah Donut Chart (Zona 4) */
.donut-insight-strip {{
    background: {insight_banner_bg};
    border: 1px solid {insight_banner_border};
    border-left: 4px solid #10B981;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 4px 8px 6px 8px;
    font-size: 11.5px;
    color: {text_primary};
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}}

/* Styling Kontainer Kartu Streamlit (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: {card_bg} !important;
    border: 1px solid {card_border} !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04) !important;
    padding: 6px !important;
}}

/* Badges Universal */
.badge-success {{ background-color: #ECFDF5; color: #047857; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }}
.badge-warning {{ background-color: #FFFBEB; color: #B45309; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }}
.badge-danger {{ background-color: #FEF2F2; color: #B91C1C; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }}
.badge-info {{ background-color: #EFF6FF; color: #1D4ED8; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700; }}

.section-title {{
    font-size: 16px;
    font-weight: 800;
    color: {text_primary};
    margin: 0 0 2px 0;
}}

.section-caption {{
    font-size: 12px;
    color: {text_secondary};
    margin-bottom: 12px;
}}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# FUNGSI HELPER FILTER TAHUN PITA CUKAI & PARAMETER TAKSONOMI (ASAL BKC & KEGIATAN)
# ==============================================================================
def apply_tahun_pc_filter(df_in, pc_choice):
    """
    Jika pengguna memilih 'Pita Cukai 2025' atau 'Pita Cukai 2026', saring dokumen yang
    memiliki pita cukai tahun tersebut dan sesuaikan kolom nilai/bungkus pada dokumen
    gabungan ('2025 & 2026') agar metrik mencerminkan 100% porsi tahun PC yang dipilih!
    BUNGKUS_TMS hanya dihitung pada berkas yang sudah berstatus TERBIT.
    """
    out = df_in.copy()
    if pc_choice == "Pita Cukai 2025":
        out = out[out['HAS_PC_2025']].copy()
        out[col_bks_pbck3] = out['PC2025_BKS_PBCK3']
        out[col_bks_ck2] = out['PC2025_BKS_MS']
        out[col_cukai_pbck3] = out['PC2025_CUKAI_PBCK3']
        out[col_cukai_ck2] = out['PC2025_CUKAI_MS']
        out[col_biaya_pengganti] = out['PC2025_BP']
        out['BUNGKUS_TMS'] = np.where(
            out['STATUS_CK2_BOOL'] == "TERBIT",
            (out[col_bks_pbck3] - out[col_bks_ck2]).clip(lower=0),
            0.0
        )
    elif pc_choice == "Pita Cukai 2026":
        out = out[out['HAS_PC_2026']].copy()
        out[col_bks_pbck3] = out['PC2026_BKS_PBCK3']
        out[col_bks_ck2] = out['PC2026_BKS_MS']
        out[col_cukai_pbck3] = out['PC2026_CUKAI_PBCK3']
        out[col_cukai_ck2] = out['PC2026_CUKAI_MS']
        out[col_biaya_pengganti] = out['PC2026_BP']
        out['BUNGKUS_TMS'] = np.where(
            out['STATUS_CK2_BOOL'] == "TERBIT",
            (out[col_bks_pbck3] - out[col_bks_ck2]).clip(lower=0),
            0.0
        )
    elif pc_choice != "Semua Tahun PC (Gabungan)":
        yr_target = pc_choice.replace("Pita Cukai", "").strip()
        out = out[out['TAHUN_PC_STR'].astype(str).str.contains(yr_target, na=False)].copy()
    return out

def apply_taxonomy_filters(df_in, asal_choice, giat_choice):
    """
    Menyaring dataframe berdasarkan Asal BKC (Dalam Pabrik vs Peredaran Bebas / Luar Pabrik)
    dan Jenis Kegiatan & Lokasi Pemusnahan. Untuk dokumen gabungan ('Dalam & Luar Pabrik'),
    kolom nilai cukai & kemasan disesuaikan secara presisi menggunakan porsi CK-1 vs CK-5 dari Sheet DETAIL.
    """
    out = df_in.copy()
    if asal_choice == "Dalam Pabrik":
        out = out[out['HAS_ASAL_DALAM']].copy()
        is_mix_asal = out['ASAL_BKC_STR'] == "Dalam & Luar Pabrik"
        if is_mix_asal.any():
            out.loc[is_mix_asal, col_bks_pbck3] = out.loc[is_mix_asal, 'ASAL_DALAM_BKS_PBCK3']
            out.loc[is_mix_asal, col_bks_ck2] = out.loc[is_mix_asal, 'ASAL_DALAM_BKS_MS']
            out.loc[is_mix_asal, col_cukai_pbck3] = out.loc[is_mix_asal, 'ASAL_DALAM_CUKAI_PBCK3']
            out.loc[is_mix_asal, col_cukai_ck2] = out.loc[is_mix_asal, 'ASAL_DALAM_CUKAI_MS']
            out.loc[is_mix_asal, col_biaya_pengganti] = out.loc[is_mix_asal, 'ASAL_DALAM_BP']
            # Sinkronkan juga kolom PC2025 pada berkas campuran Asal BKC
            is_mix_25 = is_mix_asal & (out['TAHUN_PC_STR'] == "2025")
            out.loc[is_mix_25, 'PC2025_BKS_PBCK3'] = out.loc[is_mix_25, 'ASAL_DALAM_BKS_PBCK3']
            out.loc[is_mix_25, 'PC2025_BKS_MS'] = out.loc[is_mix_25, 'ASAL_DALAM_BKS_MS']
            out.loc[is_mix_25, 'PC2025_CUKAI_PBCK3'] = out.loc[is_mix_25, 'ASAL_DALAM_CUKAI_PBCK3']
            out.loc[is_mix_25, 'PC2025_CUKAI_MS'] = out.loc[is_mix_25, 'ASAL_DALAM_CUKAI_MS']
            out.loc[is_mix_25, 'PC2025_BP'] = out.loc[is_mix_25, 'ASAL_DALAM_BP']
        out['BUNGKUS_TMS'] = np.where(
            out['STATUS_CK2_BOOL'] == "TERBIT",
            (out[col_bks_pbck3] - out[col_bks_ck2]).clip(lower=0),
            0.0
        )
    elif asal_choice == "Peredaran Bebas (Luar Pabrik)":
        out = out[out['HAS_ASAL_LUAR']].copy()
        is_mix_asal = out['ASAL_BKC_STR'] == "Dalam & Luar Pabrik"
        if is_mix_asal.any():
            out.loc[is_mix_asal, col_bks_pbck3] = out.loc[is_mix_asal, 'ASAL_LUAR_BKS_PBCK3']
            out.loc[is_mix_asal, col_bks_ck2] = out.loc[is_mix_asal, 'ASAL_LUAR_BKS_MS']
            out.loc[is_mix_asal, col_cukai_pbck3] = out.loc[is_mix_asal, 'ASAL_LUAR_CUKAI_PBCK3']
            out.loc[is_mix_asal, col_cukai_ck2] = out.loc[is_mix_asal, 'ASAL_LUAR_CUKAI_MS']
            out.loc[is_mix_asal, col_biaya_pengganti] = out.loc[is_mix_asal, 'ASAL_LUAR_BP']
            is_mix_25 = is_mix_asal & (out['TAHUN_PC_STR'] == "2025")
            out.loc[is_mix_25, 'PC2025_BKS_PBCK3'] = out.loc[is_mix_25, 'ASAL_LUAR_BKS_PBCK3']
            out.loc[is_mix_25, 'PC2025_BKS_MS'] = out.loc[is_mix_25, 'ASAL_LUAR_BKS_MS']
            out.loc[is_mix_25, 'PC2025_CUKAI_PBCK3'] = out.loc[is_mix_25, 'ASAL_LUAR_CUKAI_PBCK3']
            out.loc[is_mix_25, 'PC2025_CUKAI_MS'] = out.loc[is_mix_25, 'ASAL_LUAR_CUKAI_MS']
            out.loc[is_mix_25, 'PC2025_BP'] = out.loc[is_mix_25, 'ASAL_LUAR_BP']
        out['BUNGKUS_TMS'] = np.where(
            out['STATUS_CK2_BOOL'] == "TERBIT",
            (out[col_bks_pbck3] - out[col_bks_ck2]).clip(lower=0),
            0.0
        )

    if giat_choice == "Pengolahan Kembali":
        out = out[out['KEGIATAN_LOKASI_STR'] == "Pengolahan Kembali"].copy()
    elif giat_choice == "Semua Pemusnahan (Gabungan)":
        out = out[out['KEGIATAN_LOKASI_STR'].isin(["Pemusnahan - Dalam Pabrik", "Pemusnahan - Luar Pabrik"])].copy()
    elif giat_choice == "Pemusnahan - Dalam Pabrik":
        out = out[out['KEGIATAN_LOKASI_STR'] == "Pemusnahan - Dalam Pabrik"].copy()
    elif giat_choice == "Pemusnahan - Luar Pabrik":
        out = out[out['KEGIATAN_LOKASI_STR'] == "Pemusnahan - Luar Pabrik"].copy()

    return out

# ==============================================================================
# BAGIAN 1 & 2: PEMISAHAN FILTER PERIODE GLOBAL (df_period_all) VS ENTITAS PABRIK (df_filtered)
# ==============================================================================
df_period_all = df.copy()
is_terbit_all = df_period_all['STATUS_CK2_BOOL'] == "TERBIT"
is_proses_all = df_period_all['STATUS_CK2_BOOL'] == "PROSES"

if mode_periode == "Semua Periode (Total Tahunan)":
    df_period_all = df_period_all[(df_period_all['TAHUN_ACUAN'] == selected_tahun) | df_period_all['TAHUN_ACUAN'].isna()]
elif mode_periode == "Bulanan Tunggal (Single Month)":
    cond_terbit_all = is_terbit_all & (df_period_all['TAHUN_ACUAN'] == selected_tahun) & (df_period_all['BULAN_ACUAN'] == selected_bulan_angka)
    cond_proses_all = is_proses_all & (
        ((df_period_all['TAHUN_ACUAN'] == selected_tahun) & (df_period_all['BULAN_ACUAN'] == selected_bulan_angka))
        | df_period_all['TAHUN_ACUAN'].isna()
        | df_period_all['BULAN_ACUAN'].isna()
    )
    df_period_all = df_period_all[cond_terbit_all | cond_proses_all]
elif mode_periode == "Kumulatif (s.d. Bulan)":
    cond_terbit_all = is_terbit_all & (df_period_all['TAHUN_ACUAN'] == selected_tahun) & (df_period_all['BULAN_ACUAN'] <= selected_bulan_angka)
    cond_proses_all = is_proses_all & (
        ((df_period_all['TAHUN_ACUAN'] == selected_tahun) & (df_period_all['BULAN_ACUAN'] <= selected_bulan_angka))
        | df_period_all['TAHUN_ACUAN'].isna()
        | df_period_all['BULAN_ACUAN'].isna()
    )
    df_period_all = df_period_all[cond_terbit_all | cond_proses_all]

# Terapkan filter sekunder Tahun Pita Cukai serta Filter Asal BKC & Kegiatan/Lokasi pada df_period_all
df_period_all = apply_tahun_pc_filter(df_period_all, selected_tahun_pc)
df_period_all = apply_taxonomy_filters(df_period_all, selected_asal_bkc, selected_kegiatan)

# Hitung Grand Total KPPBC & Tabel Peringkat Pabrik dari df_period_all (murni dari dokumen TERBIT untuk Realisasi CK-2)
df_period_terbit_all = df_period_all[df_period_all['STATUS_CK2_BOOL'] == "TERBIT"]
grand_total_cukai_ck2 = df_period_terbit_all[col_cukai_ck2].sum() if col_cukai_ck2 in df_period_terbit_all.columns else 0.0
grand_total_dok_ck2 = df_period_terbit_all[df_period_terbit_all[col_ck2] != "-"][col_ck2].nunique() if col_ck2 in df_period_all.columns else 0

if col_pabrik in df_period_terbit_all.columns and col_cukai_ck2 in df_period_terbit_all.columns and not df_period_terbit_all.empty:
    df_all_pabrik_rank = (
        df_period_terbit_all.groupby(col_pabrik)[col_cukai_ck2]
        .sum()
        .reset_index()
    )
    df_all_pabrik_rank = (
        df_all_pabrik_rank[df_all_pabrik_rank[col_cukai_ck2] > 0]
        .sort_values(by=col_cukai_ck2, ascending=False)
        .reset_index(drop=True)
    )
    df_all_pabrik_rank['RANK'] = df_all_pabrik_rank.index + 1
else:
    df_all_pabrik_rank = pd.DataFrame(columns=[col_pabrik, col_cukai_ck2, 'RANK'])

total_pabrik_aktif_periode = len(df_all_pabrik_rank)

# Buat df_filtered untuk Entitas Pabrik Terpilih
if selected_pabrik != "Semua Pabrik":
    df_filtered = df_period_all[df_period_all[col_pabrik].astype(str).str.strip() == selected_pabrik].copy()
else:
    df_filtered = df_period_all.copy()

# ==============================================================================
# PERHITUNGAN METRIK EKSEKUTIF, PEMISAHAN POPULASI TERBIT vs PROSES & KECEPATAN SLA
# ==============================================================================
valid_agenda = df_filtered[df_filtered[col_agenda] != "-"][col_agenda] if col_agenda in df_filtered.columns else pd.Series(dtype='str')
valid_pbck3 = df_filtered[df_filtered[col_pbck3] != "-"][col_pbck3] if col_pbck3 in df_filtered.columns else pd.Series(dtype='str')
total_pbck3 = max(valid_agenda.nunique(), valid_pbck3.nunique(), len(df_filtered))

# PEMISAHAN POPULASI EKSPLISIT: df_terbit_filtered (Selesai CK-2) vs df_proses_filtered (Outstanding / Proses)
df_terbit_filtered = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"].copy()
df_proses_filtered = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "PROSES"].copy()

total_ck2 = df_terbit_filtered[df_terbit_filtered[col_ck2] != "-"][col_ck2].nunique() if col_ck2 in df_filtered.columns else 0
total_outstanding = int(len(df_proses_filtered))
persen_selesai = (total_ck2 / total_pbck3 * 100) if total_pbck3 > 0 else 0.0
persen_outstanding = (total_outstanding / total_pbck3 * 100) if total_pbck3 > 0 else 0.0

# Breakdown Dokumen per Tahun PC (2025 vs 2026 vs Gabungan 2025 & 2026)
if selected_tahun_pc == "Pita Cukai 2025":
    pbck3_pc2025 = total_pbck3
    pbck3_pc2026 = 0
    pbck3_pc_mix = 0
    ck2_pc2025 = total_ck2
    ck2_pc2026 = 0
    ck2_pc_mix = 0
elif selected_tahun_pc == "Pita Cukai 2026":
    pbck3_pc2025 = 0
    pbck3_pc2026 = total_pbck3
    pbck3_pc_mix = 0
    ck2_pc2025 = 0
    ck2_pc2026 = total_ck2
    ck2_pc_mix = 0
else:
    pbck3_pc2025 = int((df_filtered['TAHUN_PC_STR'] == "2025").sum())
    pbck3_pc2026 = int((df_filtered['TAHUN_PC_STR'] == "2026").sum())
    pbck3_pc_mix = int((df_filtered['TAHUN_PC_STR'] == "2025 & 2026").sum())
    ck2_pc2025 = int((df_terbit_filtered['TAHUN_PC_STR'] == "2025").sum())
    ck2_pc2026 = int((df_terbit_filtered['TAHUN_PC_STR'] == "2026").sum())
    ck2_pc_mix = int((df_terbit_filtered['TAHUN_PC_STR'] == "2025 & 2026").sum())

mix_pbck3_lbl = f" (+{pbck3_pc_mix} Mix)" if pbck3_pc_mix > 0 else ""
mix_ck2_lbl = f" (+{ck2_pc_mix} Mix)" if ck2_pc_mix > 0 else ""

# PERBAIKAN #2: Perhitungan Kecepatan Layanan (SLA Speed): HARI KERJA (HK) sebagai Angka Utama!
avg_sla_val = None
avg_sla_hk_val = None
avg_sla_num_str = "-"
avg_sla_hk_num_str = "-"
avg_sla_str = "- Hari"
avg_sla_hk_str = "- Hari Kerja"

if not df_terbit_filtered.empty and col_tgl_ck2 in df_terbit_filtered.columns and col_tgl_back3 in df_terbit_filtered.columns:
    valid_sla_df = df_terbit_filtered.dropna(subset=[col_tgl_ck2, col_tgl_back3]).copy()
    if not valid_sla_df.empty:
        sla_cal_series = (valid_sla_df[col_tgl_ck2] - valid_sla_df[col_tgl_back3]).dt.days
        mask_non_neg = sla_cal_series >= 0
        valid_sla_df = valid_sla_df[mask_non_neg]
        sla_cal_series = sla_cal_series[mask_non_neg]
        if not sla_cal_series.empty:
            avg_sla_val = sla_cal_series.mean()
            avg_sla_num_str = f"{avg_sla_val:.1f}".replace(".", ",")
            avg_sla_str = f"{avg_sla_num_str} Hari"
            d_start = valid_sla_df[col_tgl_back3].values.astype('datetime64[D]')
            d_end = valid_sla_df[col_tgl_ck2].values.astype('datetime64[D]')
            hk_arr = np.busday_count(d_start, d_end)
            avg_sla_hk_val = float(np.mean(hk_arr))
            avg_sla_hk_num_str = f"{avg_sla_hk_val:.1f}".replace(".", ",")
            avg_sla_hk_str = f"{avg_sla_hk_num_str} HK"

# PERBAIKAN AKUNTANSI #1: Pemisahan Nilai Pengajuan (100% PBCK-3) vs Realisasi (TERBIT) vs On-Process (PROSES) vs Selisih TMS Murni (TERBIT)
cukai_pbck3_val = df_filtered[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_filtered.columns else 0.0
total_bks_pbck3 = df_filtered[col_bks_pbck3].sum() if col_bks_pbck3 in df_filtered.columns else 0.0

cukai_ck2_val = df_terbit_filtered[col_cukai_ck2].sum() if col_cukai_ck2 in df_terbit_filtered.columns else 0.0
total_bks_ck2 = df_terbit_filtered[col_bks_ck2].sum() if col_bks_ck2 in df_terbit_filtered.columns else 0.0

cukai_on_process = df_proses_filtered[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_proses_filtered.columns else 0.0
bks_on_process = df_proses_filtered[col_bks_pbck3].sum() if col_bks_pbck3 in df_proses_filtered.columns else 0.0

selisih_fisik = max((df_terbit_filtered[col_cukai_pbck3].sum() - cukai_ck2_val), 0.0) if not df_terbit_filtered.empty else 0.0
total_bks_tms = max((df_terbit_filtered[col_bks_pbck3].sum() - total_bks_ck2), 0.0) if not df_terbit_filtered.empty else 0.0

biaya_pengganti = df_filtered[col_biaya_pengganti].sum() if col_biaya_pengganti in df_filtered.columns else 0.0

rasio_bks_ms = (total_bks_ck2 / total_bks_pbck3 * 100) if total_bks_pbck3 > 0 else 0.0
rasio_bks_tms = (total_bks_tms / total_bks_pbck3 * 100) if total_bks_pbck3 > 0 else 0.0
rasio_bks_proses = (bks_on_process / total_bks_pbck3 * 100) if total_bks_pbck3 > 0 else 0.0

# Breakdown Nilai Rupiah & Kemasan Bungkus untuk PC 2025 vs PC 2026 (PBCK-3 dari df_filtered, CK-2 MS dari df_terbit_filtered)
if selected_tahun_pc == "Pita Cukai 2025":
    val_pbck3_2025, val_pbck3_2026 = cukai_pbck3_val, 0.0
    val_ck2_2025, val_ck2_2026 = cukai_ck2_val, 0.0
    bks_pbck3_2025, bks_pbck3_2026 = total_bks_pbck3, 0.0
    bks_ms_2025, bks_ms_2026 = total_bks_ck2, 0.0
elif selected_tahun_pc == "Pita Cukai 2026":
    val_pbck3_2025, val_pbck3_2026 = 0.0, cukai_pbck3_val
    val_ck2_2025, val_ck2_2026 = 0.0, cukai_ck2_val
    bks_pbck3_2025, bks_pbck3_2026 = 0.0, total_bks_pbck3
    bks_ms_2025, bks_ms_2026 = 0.0, total_bks_ck2
else:
    val_pbck3_2025 = df_filtered['PC2025_CUKAI_PBCK3'].sum()
    val_pbck3_2026 = df_filtered['PC2026_CUKAI_PBCK3'].sum()
    val_ck2_2025 = df_terbit_filtered['PC2025_CUKAI_MS'].sum()
    val_ck2_2026 = df_terbit_filtered['PC2026_CUKAI_MS'].sum()
    bks_pbck3_2025 = df_filtered['PC2025_BKS_PBCK3'].sum()
    bks_pbck3_2026 = df_filtered['PC2026_BKS_PBCK3'].sum()
    bks_ms_2025 = df_terbit_filtered['PC2025_BKS_MS'].sum()
    bks_ms_2026 = df_terbit_filtered['PC2026_BKS_MS'].sum()

persen_pbck3_2025 = (val_pbck3_2025 / cukai_pbck3_val * 100) if cukai_pbck3_val > 0 else 0.0
persen_pbck3_2026 = (val_pbck3_2026 / cukai_pbck3_val * 100) if cukai_pbck3_val > 0 else 0.0
persen_ck2_2025 = (val_ck2_2025 / cukai_ck2_val * 100) if cukai_ck2_val > 0 else 0.0
persen_ck2_2026 = (val_ck2_2026 / cukai_ck2_val * 100) if cukai_ck2_val > 0 else 0.0

# Perhitungan Porsi Kontribusi & Ranking Pabrik Terpilih terhadap Grand Total KPPBC
val_selected = cukai_ck2_val
val_others = max(grand_total_cukai_ck2 - val_selected, 0.0)
porsi_persen = (val_selected / grand_total_cukai_ck2 * 100) if grand_total_cukai_ck2 > 0 else 0.0
porsi_persen_str = f"{porsi_persen:.2f}".replace(".", ",")
dok_persen = (total_ck2 / grand_total_dok_ck2 * 100) if grand_total_dok_ck2 > 0 else 0.0
dok_persen_str = f"{dok_persen:.1f}".replace(".", ",")

selected_rank_int = None
if selected_pabrik != "Semua Pabrik" and not df_all_pabrik_rank.empty:
    match_rank = df_all_pabrik_rank[df_all_pabrik_rank[col_pabrik] == selected_pabrik]
    if not match_rank.empty:
        selected_rank_int = int(match_rank['RANK'].iloc[0])

# ==============================================================================
# PERHITUNGAN METRIK ZONA 3B: ASAL BKC & KEGIATAN/LOKASI PEMUSNAHAN
# ==============================================================================
if selected_asal_bkc == "Dalam Pabrik":
    dok_asal_dalam = total_pbck3
    dok_asal_luar = 0
    dok_asal_mix = 0
    val_asal_dalam = cukai_pbck3_val
    val_asal_luar = 0.0
    bks_asal_dalam = total_bks_pbck3
    bks_asal_luar = 0.0
elif selected_asal_bkc == "Peredaran Bebas (Luar Pabrik)":
    dok_asal_dalam = 0
    dok_asal_luar = total_pbck3
    dok_asal_mix = 0
    val_asal_dalam = 0.0
    val_asal_luar = cukai_pbck3_val
    bks_asal_dalam = 0.0
    bks_asal_luar = total_bks_pbck3
else:
    dok_asal_dalam = int((df_filtered['ASAL_BKC_STR'] == "Dalam Pabrik").sum())
    dok_asal_luar = int((df_filtered['ASAL_BKC_STR'] == "Peredaran Bebas (Luar Pabrik)").sum())
    dok_asal_mix = int((df_filtered['ASAL_BKC_STR'] == "Dalam & Luar Pabrik").sum())
    if selected_tahun_pc == "Semua Tahun PC (Gabungan)":
        val_asal_dalam = df_filtered['ASAL_DALAM_CUKAI_PBCK3'].sum()
        val_asal_luar = df_filtered['ASAL_LUAR_CUKAI_PBCK3'].sum()
        bks_asal_dalam = df_filtered['ASAL_DALAM_BKS_PBCK3'].sum()
        bks_asal_luar = df_filtered['ASAL_LUAR_BKS_PBCK3'].sum()
    else:
        # Proporsional terhadap filter Tahun PC aktif
        tot_orig_cukai = (df_filtered['ASAL_DALAM_CUKAI_PBCK3'] + df_filtered['ASAL_LUAR_CUKAI_PBCK3']).replace(0, np.nan)
        tot_orig_bks = (df_filtered['ASAL_DALAM_BKS_PBCK3'] + df_filtered['ASAL_LUAR_BKS_PBCK3']).replace(0, np.nan)
        val_asal_dalam = (df_filtered[col_cukai_pbck3] * (df_filtered['ASAL_DALAM_CUKAI_PBCK3'] / tot_orig_cukai)).fillna(0.0).sum()
        val_asal_luar = (df_filtered[col_cukai_pbck3] * (df_filtered['ASAL_LUAR_CUKAI_PBCK3'] / tot_orig_cukai)).fillna(0.0).sum()
        bks_asal_dalam = (df_filtered[col_bks_pbck3] * (df_filtered['ASAL_DALAM_BKS_PBCK3'] / tot_orig_bks)).fillna(0.0).sum()
        bks_asal_luar = (df_filtered[col_bks_pbck3] * (df_filtered['ASAL_LUAR_BKS_PBCK3'] / tot_orig_bks)).fillna(0.0).sum()

persen_asal_dalam = (val_asal_dalam / cukai_pbck3_val * 100) if cukai_pbck3_val > 0 else 0.0
persen_asal_luar = (val_asal_luar / cukai_pbck3_val * 100) if cukai_pbck3_val > 0 else 0.0
mix_asal_note = f" (+{dok_asal_mix} Mix CK-1/CK-5)" if dok_asal_mix > 0 else ""

# Metrik Kegiatan & Lokasi Pemusnahan (Pengolahan Kembali vs Pemusnahan Dalam Pabrik vs Pemusnahan Luar Pabrik)
df_giat_olah = df_filtered[df_filtered['KEGIATAN_LOKASI_STR'] == "Pengolahan Kembali"]
df_giat_musnah_dlm = df_filtered[df_filtered['KEGIATAN_LOKASI_STR'] == "Pemusnahan - Dalam Pabrik"]
df_giat_musnah_luar = df_filtered[df_filtered['KEGIATAN_LOKASI_STR'] == "Pemusnahan - Luar Pabrik"]

dok_giat_olah = len(df_giat_olah)
val_giat_olah = df_giat_olah[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_giat_olah.columns else 0.0
bks_giat_olah = df_giat_olah[col_bks_pbck3].sum() if col_bks_pbck3 in df_giat_olah.columns else 0.0
persen_giat_olah = (val_giat_olah / cukai_pbck3_val * 100) if cukai_pbck3_val > 0 else 0.0

dok_giat_musnah_dlm = len(df_giat_musnah_dlm)
val_giat_musnah_dlm = df_giat_musnah_dlm[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_giat_musnah_dlm.columns else 0.0
bks_giat_musnah_dlm = df_giat_musnah_dlm[col_bks_pbck3].sum() if col_bks_pbck3 in df_giat_musnah_dlm.columns else 0.0
persen_giat_musnah_dlm = (val_giat_musnah_dlm / cukai_pbck3_val * 100) if cukai_pbck3_val > 0 else 0.0

dok_giat_musnah_luar = len(df_giat_musnah_luar)
val_giat_musnah_luar = df_giat_musnah_luar[col_cukai_pbck3].sum() if col_cukai_pbck3 in df_giat_musnah_luar.columns else 0.0
bks_giat_musnah_luar = df_giat_musnah_luar[col_bks_pbck3].sum() if col_bks_pbck3 in df_giat_musnah_luar.columns else 0.0
persen_giat_musnah_luar = (val_giat_musnah_luar / cukai_pbck3_val * 100) if cukai_pbck3_val > 0 else 0.0

visual_periode_lbl = f"Tahun Anggaran {selected_tahun}"
if mode_periode == "Bulanan Tunggal (Single Month)":
    visual_periode_lbl = f"Bulan {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)":
    visual_periode_lbl = f"s.d. Bulan {selected_bulan_nama} {selected_tahun}"

visual_pc_pill_lbl = (
    "PC: Semua Tahun (2025 & 2026)"
    if selected_tahun_pc == "Semua Tahun PC (Gabungan)"
    else f"PC: {selected_tahun_pc.replace('Pita Cukai ', 'Tahun ')}"
)

# Ringkasan Cepat SLA & Tombol Refresh di Bawah Sidebar (Rata-rata Hari Kerja sebagai Utama)
with st.sidebar:
    st.markdown("---")
    st.markdown(f"""
    <div class="sidebar-sla-box">
        <div style="font-weight:800; color:#38BDF8; margin-bottom:4px;">📌 RINGKASAN KEPATUHAN SLA</div>
        <div style="color:#E2E8F0; line-height:1.55;">
            • Formula: <b>Tgl CK-2 − Tgl BACK-3</b><br>
            • Rata-rata Hari Kerja: <b>{avg_sla_hk_str}</b> (Maks 10 HK)<br>
            • Setara Kalender: <b>≈ {avg_sla_str} Kalender</b><br>
            • Standar PER-2/BC/2026: <b>Maks 10 HK (Pasal 7)</b><br>
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
    else f'<span class="status-pill pill-red">⚠️ Selisih TMS Murni: {fmt_exact_rp(-selisih_fisik)} ({fmt_exact_bks(total_bks_tms)} Bks)</span>'
)

proses_pill_html = (
    f'<span class="status-pill pill-amber">⏳ On-Process ({total_outstanding} Dok): {fmt_miliar_short(cukai_on_process)}</span>'
    if total_outstanding > 0
    else ""
)

asal_pill_html = (
    f'<span class="status-pill pill-purple">🏭 Asal: {selected_asal_bkc}</span>'
    if selected_asal_bkc != "Semua Asal BKC (Gabungan)"
    else ""
)

giat_pill_html = (
    f'<span class="status-pill pill-purple">🔥 Kegiatan: {selected_kegiatan}</span>'
    if selected_kegiatan != "Semua Kegiatan (Gabungan)"
    else ""
)

st.markdown(f"""
<div class="top-header-card">
    <div class="header-left">
        <img src="{LOGO_URL}" width="68" referrerpolicy="no-referrer"
             style="object-fit:contain; filter: drop-shadow(0 2px 6px rgba(15,23,42,0.18));"
             onerror="this.onerror=null; this.src='{BC_SVG_FALLBACK}';">
        <div>
            <h1 class="header-title">📊 EXECUTIVE DASHBOARD PBCK-3 & REALISASI CUKAI</h1>
            <p class="header-subtitle">Monitoring Pelayanan Pengolahan Kembali & Pemusnahan BKC — KPPBC Tipe Madya Cukai Malang</p>
            <span class="header-law">⚖️ Landasan Hukum: PMK Nomor 113 Tahun 2025 & PER-2/BC/2026 (SLA Maks. 10 Hari Kerja sejak BACK-3)</span>
        </div>
    </div>
    <div class="header-pills">
        <span class="status-pill pill-blue">🗓️ {visual_periode_lbl}</span>
        <span class="status-pill pill-amber">🏷️ {visual_pc_pill_lbl}</span>
        {asal_pill_html}
        {giat_pill_html}
        <span class="status-pill">🏢 {selected_pabrik}</span>
        {rekon_pill_html}
        {proses_pill_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ZONA 1: st.columns(4) untuk 4 Kartu KPI Utama bergaya Adminty + Mini-Breakdown Tahun PC & On-Process
z1_c1, z1_c2, z1_c3, z1_c4 = st.columns(4)

with z1_c1:
    st.markdown(f"""
    <div class="adminty-card">
        <div class="adminty-body">
            <div>
                <div class="adminty-title">Permohonan PBCK-3 Terlayani</div>
                <div class="adminty-value">{total_pbck3:,.0f} <span class="adminty-unit">Berkas</span></div>
                <div class="adminty-subnote"><span class="pc-mini-badge">🏷️ PC 2025: {pbck3_pc2025} | PC 2026: {pbck3_pc2026}{mix_pbck3_lbl}</span></div>
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
                <div class="adminty-subnote"><span class="pc-mini-badge">🏷️ PC 2025: {ck2_pc2025} | PC 2026: {ck2_pc2026}{mix_ck2_lbl}</span></div>
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
    subnote_outstanding_html = (
        f'<span class="pc-mini-badge">⏳ Nilai Proses: {fmt_miliar_short(cukai_on_process)} ({fmt_exact_bks(bks_on_process)} Bks)</span>'
        if total_outstanding > 0
        else "Seluruh berkas telah terbit CK-2"
    )
    st.markdown(f"""
    <div class="adminty-card">
        <div class="adminty-body">
            <div>
                <div class="adminty-title">Outstanding / Dalam Proses</div>
                <div class="adminty-value">{total_outstanding:,.0f} <span class="adminty-unit">Dokumen</span></div>
                <div class="adminty-subnote">{subnote_outstanding_html}</div>
            </div>
            <div class="adminty-icon-circle icon-rose">⏳</div>
        </div>
        <div class="adminty-footer footer-rose">
            <span>Menunggu Terbit CK-2</span>
            <span>{persen_outstanding:.1f}% Beban Kerja</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with z1_c4:
    sla_check_val = avg_sla_hk_val if avg_sla_hk_val is not None else avg_sla_val
    sla_status_txt = (
        "✅ Memenuhi SLA (≤ 10 HK)"
        if (sla_check_val is not None and sla_check_val <= 10)
        else ("⚠️ Melebihi SLA (> 10 HK)" if sla_check_val is not None else "Menunggu Data CK-2")
    )
    st.markdown(f"""
    <div class="adminty-card">
        <div class="adminty-body">
            <div>
                <div class="adminty-title">Kecepatan Layanan (BACK-3 ➔ CK-2)</div>
                <div class="adminty-value">{avg_sla_hk_num_str} <span class="adminty-unit">Hari Kerja</span></div>
                <div class="adminty-subnote">Standar Maks. 10 HK (Pasal 7) &bull; ≈ {avg_sla_num_str} Hari Kalender</div>
            </div>
            <div class="adminty-icon-circle icon-cyan">⚡</div>
        </div>
        <div class="adminty-footer footer-cyan">
            <span>Rentang BACK-3 s.d. CK-2</span>
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
            <div class="section-caption">Visualisasi volume dokumen CK-2 terbit, info berkas proses & nilai realisasi cukai (MS) — Entitas: <b>{selected_pabrik}</b> | <b>{visual_pc_pill_lbl}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # Saring data Grafik Tren Bulanan agar sinkron dengan Pabrik, Tahun, Tahun PC, Asal BKC & Kegiatan
        df_base_trend = apply_tahun_pc_filter(df.copy(), selected_tahun_pc)
        df_base_trend = apply_taxonomy_filters(df_base_trend, selected_asal_bkc, selected_kegiatan)
        if selected_pabrik != "Semua Pabrik":
            df_base_trend = df_base_trend[df_base_trend[col_pabrik].astype(str).str.strip() == selected_pabrik]

        df_terbit_trend = df_base_trend[df_base_trend['STATUS_CK2_BOOL'] == "TERBIT"].copy()
        if 'TAHUN_CK2' in df_terbit_trend.columns:
            df_terbit_trend = df_terbit_trend[df_terbit_trend['TAHUN_CK2'] == selected_tahun]

        df_proses_trend = df_base_trend[df_base_trend['STATUS_CK2_BOOL'] == "PROSES"].copy()
        if 'TAHUN_ACUAN' in df_proses_trend.columns:
            df_proses_trend = df_proses_trend[df_proses_trend['TAHUN_ACUAN'] == selected_tahun]

        if (not df_terbit_trend.empty and 'BULAN_CK2_ANGKA' in df_terbit_trend.columns) or (not df_proses_trend.empty and 'BULAN_ACUAN' in df_proses_trend.columns):
            if not df_terbit_trend.empty:
                df_trend_terbit = (
                    df_terbit_trend.dropna(subset=['BULAN_CK2_ANGKA'])
                    .groupby('BULAN_CK2_ANGKA')
                    .agg(CK2=(col_ck2, 'nunique'), TOTAL_CUKAI=(col_cukai_ck2, 'sum'))
                    .reset_index()
                    .rename(columns={'BULAN_CK2_ANGKA': 'BULAN_NUM'})
                )
            else:
                df_trend_terbit = pd.DataFrame(columns=['BULAN_NUM', 'CK2', 'TOTAL_CUKAI'])

            if not df_proses_trend.empty:
                df_trend_proses = (
                    df_proses_trend.dropna(subset=['BULAN_ACUAN'])
                    .groupby('BULAN_ACUAN')
                    .agg(PROSES_CNT=(col_agenda, 'count'), PROSES_CUKAI=(col_cukai_pbck3, 'sum'))
                    .reset_index()
                    .rename(columns={'BULAN_ACUAN': 'BULAN_NUM'})
                )
            else:
                df_trend_proses = pd.DataFrame(columns=['BULAN_NUM', 'PROSES_CNT', 'PROSES_CUKAI'])

            df_trend = pd.merge(df_trend_terbit, df_trend_proses, on='BULAN_NUM', how='outer').fillna(0)
            df_trend['BULAN_NUM'] = df_trend['BULAN_NUM'].astype(int)
            df_trend['CK2'] = df_trend['CK2'].astype(int)
            df_trend['PROSES_CNT'] = df_trend['PROSES_CNT'].astype(int)
            df_trend = df_trend.sort_values(by='BULAN_NUM')
            df_trend['BULAN'] = df_trend['BULAN_NUM'].map(INDO_BULAN)
            df_trend['CUKAI_STR'] = df_trend['TOTAL_CUKAI'].map(fmt_exact_rp)
            df_trend['PROSES_INFO_HOVER'] = df_trend.apply(
                lambda r: f"<br>⏳ Dalam Proses: <b>{int(r['PROSES_CNT'])} Berkas ({fmt_exact_rp(r['PROSES_CUKAI'])})</b>" if r['PROSES_CNT'] > 0 else "",
                axis=1
            )
            df_trend['BAR_LABEL'] = df_trend.apply(
                lambda r: f"{int(r['CK2'])} Dok (+{int(r['PROSES_CNT'])} Proses)" if r['PROSES_CNT'] > 0 else f"{int(r['CK2'])} Dok",
                axis=1
            )

            # Hitung tick dinamis sumbu Y kanan (Format Bahasa Indonesia Rp X,X M / Jt tanpa 'B')
            max_cukai_val = float(df_trend['TOTAL_CUKAI'].max()) if not df_trend.empty else 0.0
            y2_max = max_cukai_val * 1.18 if max_cukai_val > 0 else 1_000_000_000.0
            y2_tickvals = np.linspace(0, y2_max, 5).tolist()
            y2_ticktext = [fmt_axis_rp_indo(v) for v in y2_tickvals]

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=df_trend['BULAN'],
                y=df_trend['CK2'],
                name='Dokumen CK-2 Terbit',
                marker=dict(color='#3B82F6' if is_night_mode else '#2563EB', cornerradius=6),
                text=df_trend['BAR_LABEL'],
                textposition='outside',
                customdata=np.stack([df_trend['CUKAI_STR'], df_trend['PROSES_INFO_HOVER']], axis=-1),
                hovertemplate="<b>Bulan %{x}</b><br>Dokumen CK-2 Terbit: <b>%{y} Dokumen</b><br>Total Realisasi Cukai (MS): <b>%{customdata[0]}</b>%{customdata[1]}<extra></extra>"
            ))
            fig_trend.add_trace(go.Scatter(
                x=df_trend['BULAN'],
                y=df_trend['TOTAL_CUKAI'],
                name='Nilai Cukai MS (Rp)',
                yaxis='y2',
                mode='lines+markers',
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.14)',
                line=dict(color='#10B981' if is_night_mode else '#059669', width=2.8),
                marker=dict(size=8, color='#10B981' if is_night_mode else '#059669', line=dict(width=2, color=card_bg)),
                customdata=np.stack([df_trend['CUKAI_STR'], df_trend['PROSES_INFO_HOVER']], axis=-1),
                hovertemplate="<b>Bulan %{x}</b><br>Realisasi Cukai (MS): <b>%{customdata[0]}</b>%{customdata[1]}<extra></extra>"
            ))
            max_ck2_bar = max(int(df_trend['CK2'].max()), 1)
            fig_trend.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color=chart_font),
                xaxis=dict(
                    title="Bulan Terbit CK-2",
                    showgrid=False,
                    type='category',
                    categoryorder='array',
                    categoryarray=df_trend['BULAN'].tolist(),
                    tickfont=dict(color=chart_font, weight=600)
                ),
                yaxis=dict(
                    title="Jumlah Dokumen",
                    gridcolor=chart_grid,
                    zeroline=False,
                    range=[0, max_ck2_bar * 1.25],
                    tickfont=dict(color=chart_font)
                ),
                yaxis2=dict(
                    title="Nilai Cukai (Rp)",
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    zeroline=False,
                    range=[0, y2_max],
                    tickmode='array',
                    tickvals=y2_tickvals,
                    ticktext=y2_ticktext,
                    tickfont=dict(color=chart_font)
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=chart_font)),
                height=355,
                margin=dict(t=28, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Belum ada data dokumen CK-2 pada filter pabrik/tahun ini.")

# ZONA 2 KANAN: 3 KARTU FINANSIAL DENGAN REKONSILIASI AKUNTANSI PRESISI & BREAKDOWN PC 2025 vs 2026
with col_side_kpis:
    badge_pbck3_total = f'<span class="badge-info">Total {total_pbck3} Berkas PBCK-3</span>'
    badge_pbck3_proses = (
        f'<span class="badge-warning">⏳ {total_outstanding} Proses: {fmt_miliar_short(cukai_on_process)}</span>'
        if total_outstanding > 0
        else ""
    )

    badge_cukai_side = (
        f'<span class="badge-danger">Selisih TMS Murni: {fmt_exact_rp(-selisih_fisik)} ({total_ck2} Dok Terbit)</span>'
        if selisih_fisik > 0
        else f'<span class="badge-success">100% Memenuhi Syarat ({total_ck2} Dok Terbit)</span>'
    )
    badge_share_side = (
        f'<span class="badge-info">📊 Kontribusi: {porsi_persen_str}% Total KPPBC</span>'
        if (selected_pabrik != "Semua Pabrik" and grand_total_cukai_ck2 > 0)
        else ""
    )

    pc_pbck3_strip_html = (
        f"<div class='fin-pc-strip'>🏷️ PC 2025: {fmt_miliar_short(val_pbck3_2025)} ({persen_pbck3_2025:.1f}%) &bull; PC 2026: {fmt_miliar_short(val_pbck3_2026)} ({persen_pbck3_2026:.1f}%)</div>"
    )
    pc_ck2_strip_html = (
        f"<div class='fin-pc-strip'>🏷️ PC 2025: {fmt_miliar_short(val_ck2_2025)} ({persen_ck2_2025:.1f}%) &bull; PC 2026: {fmt_miliar_short(val_ck2_2026)} ({persen_ck2_2026:.1f}%)</div>"
    )

    st.markdown(f"""
    <div class="admindek-fin-card">
        <div>
            <div class="fin-label">Nilai Pengajuan (PBCK-3)</div>
            <div class="fin-val">{fmt_kpi_rupiah(cukai_pbck3_val)}</div>
            <div class="fin-sub">{badge_pbck3_total}{badge_pbck3_proses}</div>
            {pc_pbck3_strip_html}
        </div>
        <div class="fin-icon-box box-blue">📋</div>
    </div>

    <div class="admindek-fin-card" style="background: {fin_green_bg}; border-color: {fin_green_border};">
        <div>
            <div class="fin-label" style="color: {fin_green_text};">Realisasi Cukai CK-2 (MS)</div>
            <div class="fin-val" style="color: {fin_green_text};">{fmt_kpi_rupiah(cukai_ck2_val)}</div>
            <div class="fin-sub">{badge_cukai_side}{badge_share_side}</div>
            {pc_ck2_strip_html}
        </div>
        <div class="fin-icon-box box-emerald">💸</div>
    </div>

    <div class="admindek-fin-card">
        <div>
            <div class="fin-label" style="color: {fin_amber_text};">Biaya Pengganti (BP) Pita Cukai</div>
            <div class="fin-val" style="color: {fin_amber_text};">{fmt_kpi_rupiah(biaya_pengganti)}</div>
            <div class="fin-sub">Penerimaan Negara (PMK 113/2025)</div>
        </div>
        <div class="fin-icon-box box-amber">🏦</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# ZONA 3: HORIZONTAL PROGRESS BAR STRIP (GAYA ADMINDEK — 4 KOLOM + RINCIAN PC & ON-PROCESS)
# ==============================================================================
with st.container(border=True):
    z3_c1, z3_c2, z3_c3, z3_c4 = st.columns(4)

    with z3_c1:
        st.markdown(f"""
        <div class="progress-strip-item">
            <div class="progress-strip-label">📦 Kemasan Diajukan (PBCK-3)</div>
            <div class="progress-strip-val">{fmt_kpi_bungkus(total_bks_pbck3)}</div>
            <div class="progress-track">
                <div class="progress-fill" style="width: 100%; background: #3B82F6;"></div>
            </div>
            <div class="progress-meta">
                <span>Basis Pemberitahuan Fisik ({total_pbck3} Berkas)</span>
                <span>100%</span>
            </div>
            <div class="progress-pc-sub">🏷️ PC 2025: {fmt_bks_short(bks_pbck3_2025)} &bull; PC 2026: {fmt_bks_short(bks_pbck3_2026)}</div>
        </div>
        """, unsafe_allow_html=True)

    with z3_c2:
        w_ms = min(max(rasio_bks_ms, 0.0), 100.0)
        st.markdown(f"""
        <div class="progress-strip-item">
            <div class="progress-strip-label" style="color:#10B981;">✅ Kemasan Disetujui (MS)</div>
            <div class="progress-strip-val" style="color:{fin_green_text};">{fmt_kpi_bungkus(total_bks_ck2)}</div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {w_ms:.1f}%; background: #10B981;"></div>
            </div>
            <div class="progress-meta">
                <span>Memenuhi Syarat ({total_ck2} Dok Terbit)</span>
                <span style="color:#10B981; font-weight:700;">{rasio_bks_ms:.1f}%</span>
            </div>
            <div class="progress-pc-sub">🏷️ PC 2025: {fmt_bks_short(bks_ms_2025)} &bull; PC 2026: {fmt_bks_short(bks_ms_2026)}</div>
        </div>
        """, unsafe_allow_html=True)

    with z3_c3:
        w_tms = min(max(rasio_bks_tms, 0.0), 100.0)
        sub_tms_proses_lbl = (
            f"⏳ Belum Dilaksanakan / Proses: {fmt_exact_bks(bks_on_process)} Bks ({total_outstanding} Dok)"
            if bks_on_process > 0
            else "Selisih Pemeriksaan Fisik BACK-3 (Berkas Selesai)"
        )
        st.markdown(f"""
        <div class="progress-strip-item">
            <div class="progress-strip-label" style="color:#F43F5E;">❌ Kemasan Ditolak (TMS Murni)</div>
            <div class="progress-strip-val" style="color:#F43F5E;">{fmt_kpi_bungkus(total_bks_tms)}</div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {w_tms:.1f}%; background: #EF4444;"></div>
            </div>
            <div class="progress-meta">
                <span>{'Tidak Mendapat Pengembalian' if total_bks_tms > 0 else 'Nihil Selisih (0 Bks)'}</span>
                <span style="color:#F43F5E; font-weight:700;">{rasio_bks_tms:.2f}%</span>
            </div>
            <div class="progress-pc-sub">{sub_tms_proses_lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    with z3_c4:
        w_done = min(max(persen_selesai, 0.0), 100.0)
        st.markdown(f"""
        <div class="progress-strip-item" style="border-right:none;">
            <div class="progress-strip-label" style="color:#06B6D4;">🎯 Tingkat Penyelesaian Dokumen</div>
            <div class="progress-strip-val" style="color:#06B6D4;">{persen_selesai:.1f}% <span style="font-size:13px; font-weight:600; color:{text_secondary};">({total_ck2}/{total_pbck3} Berkas)</span></div>
            <div class="progress-track">
                <div class="progress-fill" style="width: {w_done:.1f}%; background: #06B6D4;"></div>
            </div>
            <div class="progress-meta">
                <span>Rasio Terbit CK-2 vs PBCK-3</span>
                <span style="color:#06B6D4; font-weight:700;">{persen_selesai:.1f}%</span>
            </div>
            <div class="progress-pc-sub">🏷️ Terbit PC 2025: {ck2_pc2025} Dok &bull; PC 2026: {ck2_pc2026} Dok{mix_ck2_lbl}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# ZONA 3B: EXECUTIVE TAXONOMY & LOCATION STRIP (ASAL BKC & KEGIATAN/LOKASI PEMUSNAHAN)
# ==============================================================================
col_tax_asal, col_tax_giat = st.columns(2)

with col_tax_asal:
    with st.container(border=True):
        w_asal_dlm = min(max(persen_asal_dalam, 0.0), 100.0)
        w_asal_luar = min(max(persen_asal_luar, 0.0), 100.0)
        st.markdown(f"""
        <div class="taxonomy-card-wrap">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                <div class="section-title" style="font-size:14.5px;">🏭 Klasifikasi Asal BKC (PBCK-3): Dalam Pabrik vs Peredaran Bebas</div>
                <span class="badge-info">Total: {total_pbck3} Berkas{mix_asal_note}</span>
            </div>
            <div class="taxonomy-bar-multi">
                <div style="width:{w_asal_dlm:.1f}%; background:#2563EB;" title="Dalam Pabrik: {w_asal_dlm:.1f}%"></div>
                <div style="width:{w_asal_luar:.1f}%; background:#F59E0B;" title="Peredaran Bebas (Luar Pabrik): {w_asal_luar:.1f}%"></div>
            </div>
            <div class="taxonomy-grid-2">
                <div class="taxonomy-mini-box" style="border-left: 3.5px solid #2563EB;">
                    <div class="tax-box-head">
                        <span style="color:#2563EB;">🏢 Dalam Pabrik (CK-1)</span>
                        <span class="badge-info">{dok_asal_dalam} Murni{f' +{dok_asal_mix} Mix' if dok_asal_mix > 0 else ''}</span>
                    </div>
                    <div class="tax-box-main">{fmt_miliar_short(val_asal_dalam)} <span style="font-size:11.5px; font-weight:700; color:#2563EB;">({persen_asal_dalam:.1f}%)</span></div>
                    <div class="tax-box-sub">{fmt_exact_rp(val_asal_dalam)} &bull; <b>{fmt_exact_bks(bks_asal_dalam)} Bks</b></div>
                </div>
                <div class="taxonomy-mini-box" style="border-left: 3.5px solid #F59E0B;">
                    <div class="tax-box-head">
                        <span style="color:#D97706;">🚚 Peredaran Bebas / Luar (CK-5)</span>
                        <span class="badge-warning">{dok_asal_luar} Murni{f' +{dok_asal_mix} Mix' if dok_asal_mix > 0 else ''}</span>
                    </div>
                    <div class="tax-box-main">{fmt_miliar_short(val_asal_luar)} <span style="font-size:11.5px; font-weight:700; color:#D97706;">({persen_asal_luar:.1f}%)</span></div>
                    <div class="tax-box-sub">{fmt_exact_rp(val_asal_luar)} &bull; <b>{fmt_exact_bks(bks_asal_luar)} Bks</b></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_tax_giat:
    with st.container(border=True):
        w_g_olah = min(max(persen_giat_olah, 0.0), 100.0)
        w_g_mdlm = min(max(persen_giat_musnah_dlm, 0.0), 100.0)
        w_g_mluar = min(max(persen_giat_musnah_luar, 0.0), 100.0)
        tot_musnah_dok = dok_giat_musnah_dlm + dok_giat_musnah_luar
        st.markdown(f"""
        <div class="taxonomy-card-wrap">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                <div class="section-title" style="font-size:14.5px;">🔥 Rincian Kegiatan & Lokasi Pemusnahan BKC</div>
                <span class="badge-danger">Total Pemusnahan: {tot_musnah_dok} Berkas ({dok_giat_musnah_luar} Luar Pabrik)</span>
            </div>
            <div class="taxonomy-bar-multi">
                <div style="width:{w_g_olah:.1f}%; background:#10B981;" title="Pengolahan Kembali: {w_g_olah:.1f}%"></div>
                <div style="width:{w_g_mdlm:.1f}%; background:#F59E0B;" title="Pemusnahan Dalam Pabrik: {w_g_mdlm:.1f}%"></div>
                <div style="width:{w_g_mluar:.1f}%; background:#F43F5E;" title="Pemusnahan Luar Pabrik: {w_g_mluar:.1f}%"></div>
            </div>
            <div class="taxonomy-grid-3">
                <div class="taxonomy-mini-box" style="border-left: 3.5px solid #10B981;">
                    <div class="tax-box-head">
                        <span style="color:#059669;">♻️ Olah Kembali</span>
                        <span class="badge-success">{dok_giat_olah} Dok</span>
                    </div>
                    <div class="tax-box-main">{fmt_miliar_short(val_giat_olah)} <span style="font-size:11px; color:#059669;">({persen_giat_olah:.1f}%)</span></div>
                    <div class="tax-box-sub"><b>{fmt_bks_short(bks_giat_olah)}</b></div>
                </div>
                <div class="taxonomy-mini-box" style="border-left: 3.5px solid #F59E0B;">
                    <div class="tax-box-head">
                        <span style="color:#D97706;">🏭 Musnah (Dalam)</span>
                        <span class="badge-warning">{dok_giat_musnah_dlm} Dok</span>
                    </div>
                    <div class="tax-box-main">{fmt_miliar_short(val_giat_musnah_dlm)} <span style="font-size:11px; color:#D97706;">({persen_giat_musnah_dlm:.1f}%)</span></div>
                    <div class="tax-box-sub"><b>{fmt_bks_short(bks_giat_musnah_dlm)}</b></div>
                </div>
                <div class="taxonomy-mini-box-rose" style="border-left: 3.5px solid #F43F5E;">
                    <div class="tax-box-head">
                        <span style="color:#E11D48;">🚨 Musnah (Luar)</span>
                        <span class="badge-danger">{dok_giat_musnah_luar} Dok</span>
                    </div>
                    <div class="tax-box-main" style="color:#E11D48;">{fmt_miliar_short(val_giat_musnah_luar)} <span style="font-size:11px;">({persen_giat_musnah_luar:.1f}%)</span></div>
                    <div class="tax-box-sub"><b>{fmt_bks_short(bks_giat_musnah_luar)}</b></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# ZONA 4: SPLIT VIEW — DYNAMIC CONTEXT-AWARE DONUT CHART (45%) & RADAR KEPATUHAN SLA (55%)
# ==============================================================================
col_donut, col_sla_radar = st.columns([4.5, 5.5])

with col_donut:
    with st.container(border=True):
        if selected_pabrik == "Semua Pabrik":
            # MODE A — Semua Pabrik: Top 5 Pabrik + Pabrik Lainnya (Gabungan) = 100% Grand Total KPPBC
            st.markdown("""
            <div style="padding: 6px 10px 0 10px;">
                <div class="section-title">🍩 Kontribusi Realisasi Nilai Cukai (Top 5 Pabrik vs Total KPPBC)</div>
                <div class="section-caption">Proporsi nilai pengembalian cukai (MS) 5 pabrik terbesar beserta gabungan pabrik lainnya terhadap 100% total KPPBC.</div>
            </div>
            """, unsafe_allow_html=True)

            if not df_all_pabrik_rank.empty and grand_total_cukai_ck2 > 0:
                df_top5 = df_all_pabrik_rank.head(5).copy()
                df_rest = df_all_pabrik_rank.iloc[5:]
                if not df_rest.empty and df_rest[col_cukai_ck2].sum() > 0:
                    others_sum = df_rest[col_cukai_ck2].sum()
                    others_row = pd.DataFrame({
                        col_pabrik: [f"Pabrik Lainnya ({len(df_rest)} Pabrik)"],
                        col_cukai_ck2: [others_sum],
                        'RANK': [6]
                    })
                    df_pie_mode_a = pd.concat([df_top5, others_row], ignore_index=True)
                else:
                    df_pie_mode_a = df_top5.copy()

                df_pie_mode_a['CUKAI_STR'] = df_pie_mode_a[col_cukai_ck2].map(fmt_exact_rp)
                palette_mode_a = ['#1E3A8A', '#2563EB', '#3B82F6', '#06B6D4', '#10B981', donut_other_slice]

                fig_pie = go.Figure(data=[go.Pie(
                    labels=df_pie_mode_a[col_pabrik],
                    values=df_pie_mode_a[col_cukai_ck2],
                    hole=0.56,
                    sort=False,
                    direction='clockwise',
                    marker=dict(colors=palette_mode_a[:len(df_pie_mode_a)], line=dict(color=card_bg, width=2)),
                    customdata=df_pie_mode_a['CUKAI_STR'],
                    textinfo='percent',
                    textposition='inside',
                    insidetextorientation='horizontal',
                    hovertemplate="<b>%{label}</b><br>Nilai Cukai (MS): <b>%{customdata}</b><br>Porsi Se-KPPBC: <b>%{percent}</b><extra></extra>"
                )])

                fig_pie.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=chart_font),
                    height=350,
                    margin=dict(t=10, b=55, l=10, r=10),
                    annotations=[dict(
                        text=f"<span style='font-size:11px; color:{text_secondary};'>Total KPPBC</span><br><b style='font-size:14px; color:{text_primary};'>{fmt_miliar_short(grand_total_cukai_ck2)}</b>",
                        x=0.5, y=0.5, font_size=13, showarrow=False
                    )],
                    legend=dict(orientation="h", yanchor="bottom", y=-0.30, xanchor="center", x=0.5, font=dict(color=chart_font, size=11))
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Belum ada realisasi nilai CK-2 pada periode ini.")

        else:
            # MODE B — Saat 1 Pabrik Spesifik Dipilih: Porsi Pabrik Terpilih vs Pabrik Lainnya (Se-KPPBC)
            st.markdown(f"""
            <div style="padding: 6px 10px 0 10px;">
                <div class="section-title">🍩 Porsi Kontribusi {selected_pabrik} terhadap Total KPPBC</div>
                <div class="section-caption">Perbandingan realisasi cukai (MS) pabrik terpilih terhadap seluruh pabrik pada periode <b>{visual_periode_lbl}</b>.</div>
            </div>
            """, unsafe_allow_html=True)

            if grand_total_cukai_ck2 > 0:
                slice_labels = [selected_pabrik, "Pabrik Lainnya (Se-KPPBC)"]
                slice_values = [val_selected, val_others]
                slice_custom = [fmt_exact_rp(val_selected), fmt_exact_rp(val_others)]
                slice_colors = ['#10B981', donut_other_slice]

                fig_pie_single = go.Figure(data=[go.Pie(
                    labels=slice_labels,
                    values=slice_values,
                    hole=0.58,
                    sort=False,
                    direction='clockwise',
                    pull=[0.06, 0],
                    marker=dict(colors=slice_colors, line=dict(color=card_bg, width=2.5)),
                    customdata=slice_custom,
                    textinfo='percent',
                    textposition='inside',
                    hovertemplate="<b>%{label}</b><br>Nilai Cukai (MS): <b>%{customdata}</b><br>Porsi Terhadap Total KPPBC: <b>%{percent}</b><extra></extra>"
                )])

                fig_pie_single.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=chart_font),
                    height=305,
                    margin=dict(t=10, b=35, l=10, r=10),
                    annotations=[dict(
                        text=f"<b style='font-size:20px; color:#10B981;'>{porsi_persen_str}%</b><br><span style='font-size:11px; color:{text_secondary};'>Porsi Cukai</span>",
                        x=0.5, y=0.5, font_size=14, showarrow=False
                    )],
                    legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5, font=dict(color=chart_font, size=11.5))
                )
                st.plotly_chart(fig_pie_single, use_container_width=True)

                rank_label_str = (
                    f"#{selected_rank_int} dari {total_pabrik_aktif_periode} Pabrik"
                    if selected_rank_int is not None
                    else f"Belum Ada Realisasi ({total_pabrik_aktif_periode} Pabrik Aktif)"
                )

                st.markdown(f"""
                <div class="donut-insight-strip">
                    <span>🏆 <b>Peringkat:</b> {rank_label_str}</span>
                    <span>💸 <b>Porsi Cukai:</b> {porsi_persen_str}% dari Total KPPBC ({fmt_miliar_short(grand_total_cukai_ck2)})</span>
                    <span>📜 <b>Porsi Dokumen:</b> {total_ck2} dari {grand_total_dok_ck2} Dok ({dok_persen_str}%)</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Belum ada realisasi nilai CK-2 di KPPBC pada periode ini.")

with col_sla_radar:
    with st.container(border=True):
        st.markdown("""
        <div style="padding: 6px 10px 0 10px;">
            <div class="section-title">🚨 Warning Kepatuhan SLA (Maks 10 Hari Kerja sejak BACK-3)</div>
            <div class="section-caption">Berdasarkan PER-2/BC/2026 Pasal 7, penerbitan CK-2 tidak boleh melebihi 10 hari kerja sejak Tanggal BACK-3 diterbitkan.</div>
        </div>
        """, unsafe_allow_html=True)

        col_tempo = "JATUH TEMPO BERAPA HARI LAGI" if "JATUH TEMPO BERAPA HARI LAGI" in df.columns else None
        if col_tempo:
            df_proses = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "PROSES"].copy()
            if not df_proses.empty:
                df_proses['SISA_HARI_INT'] = parse_sisa_hari(df_proses[col_tempo])
                df_proses["TGL_PBCK-3_WARN"] = df_proses[col_tgl_pbck3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_pbck3 in df_proses.columns else "-"
                df_proses["TGL_BACK-3_WARN"] = df_proses[col_tgl_back3].dt.strftime('%d/%m/%Y').fillna("-") if col_tgl_back3 in df_proses.columns else "-"
                df_proses["SISA_HARI_STR"] = df_proses['SISA_HARI_INT'].map(lambda x: f"{x:.0f} Hari Kerja" if pd.notnull(x) else "Menunggu Pelaksanaan / BACK-3")

                warn_rename = {
                    col_agenda: "Agenda",
                    col_pabrik: "Perusahaan",
                    col_pbck3: "No. PBCK-3",
                    "TGL_PBCK-3_WARN": "Tgl PBCK-3",
                    col_back3: "No. BACK-3",
                    "TGL_BACK-3_WARN": "Tgl BACK-3",
                    "SISA_HARI_STR": "Status / Sisa SLA"
                }
                warn_cols = [col_agenda, col_pabrik, col_pbck3, "TGL_PBCK-3_WARN", col_back3, "TGL_BACK-3_WARN", "SISA_HARI_STR"]

                overdue_items = df_proses[df_proses['SISA_HARI_INT'] < 0].sort_values(by='SISA_HARI_INT')
                critical_items = df_proses[(df_proses['SISA_HARI_INT'] >= 0) & (df_proses['SISA_HARI_INT'] <= 3)].sort_values(by='SISA_HARI_INT')
                safe_or_pending_items = df_proses[(df_proses['SISA_HARI_INT'] > 3) | (df_proses['SISA_HARI_INT'].isna())].sort_values(by='SISA_HARI_INT', na_position='last')

                if not overdue_items.empty:
                    st.error(f"🔴 **{len(overdue_items)} Berkas OVERDUE (Lewat Batas SLA)!**")
                    st.dataframe(overdue_items[warn_cols].rename(columns=warn_rename), hide_index=True, use_container_width=True)
                else:
                    st.success("🟢 Bebas Overdue! Semua berkas dalam batas waktu yang sah.")

                if not critical_items.empty:
                    st.warning(f"🟡 **{len(critical_items)} Berkas Jatuh Tempo Kritis (H-3 atau Kurang)!**")
                    st.dataframe(critical_items[warn_cols].rename(columns=warn_rename), hide_index=True, use_container_width=True)
                elif not safe_or_pending_items.empty:
                    st.info(f"🔵 **{len(safe_or_pending_items)} Berkas Outstanding Dalam Proses (Nilai Pengajuan: {fmt_exact_rp(cukai_on_process)} | {fmt_exact_bks(bks_on_process)} Bks):**")
                    st.dataframe(safe_or_pending_items[warn_cols].rename(columns=warn_rename), hide_index=True, use_container_width=True)
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
        df_display["CUKAI_REALISASI_CK2"] = np.where(
            df_display['STATUS_CK2_BOOL'] == "PROSES",
            "Rp 0 (Proses)",
            df_display[col_cukai_ck2].map(fmt_exact_rp)
        )
        df_display["BIAYA_PENGGANTI_STR"] = df_display[col_biaya_pengganti].map(fmt_exact_rp)
        df_display["BKS_DIAJUKAN"] = df_display[col_bks_pbck3].map(fmt_exact_bks)
        df_display["BKS_DISETUJUI_MS"] = np.where(
            df_display['STATUS_CK2_BOOL'] == "PROSES",
            "0 (Proses)",
            df_display[col_bks_ck2].map(fmt_exact_bks)
        )
        df_display["BKS_DITOLAK_TMS"] = np.where(
            df_display['STATUS_CK2_BOOL'] == "PROSES",
            "0 (Proses)",
            df_display['BUNGKUS_TMS'].map(fmt_exact_bks)
        )

        col_agenda_main = "AGENDA" if "AGENDA" in df_display.columns else df_display.columns[0]
        rename_map = {
            col_agenda_main: "Agenda",
            col_pabrik: "Perusahaan",
            col_pbck3: "No. PBCK-3",
            "TGL_PBCK-3_STR": "Tgl PBCK-3",
            "TAHUN_PC_STR": "Tahun PC",
            "ASAL_BKC_STR": "Asal BKC",
            "KEGIATAN_LOKASI_STR": "Kegiatan / Lokasi",
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
            col_agenda_main, col_pabrik, col_pbck3, "TGL_PBCK-3_STR", "TAHUN_PC_STR",
            "ASAL_BKC_STR", "KEGIATAN_LOKASI_STR",
            "BKS_DIAJUKAN", "BKS_DISETUJUI_MS", "BKS_DITOLAK_TMS",
            "CUKAI_PENGAJUAN", "CUKAI_REALISASI_CK2", "BIAYA_PENGGANTI_STR",
            col_back3, "TGL_BACK-3_STR", col_ck2, "TGL_CK-2_STR"
        ]
        df_tabel_rapi = df_display[kolom_final].rename(columns=rename_map).reset_index(drop=True)

        col_search, col_export = st.columns([3, 1])
        with col_search:
            search_query = st.text_input(
                "🔍 Cari",
                placeholder="🔍 Cari Pabrik / No. PBCK-3 / BACK-3 / CK-2 / Agenda / Tahun PC / Asal BKC / Kegiatan...",
                label_visibility="collapsed"
            )

        if search_query:
            q_str = search_query.strip()
            mask_search = (
                df_tabel_rapi["Perusahaan"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["Agenda"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["No. PBCK-3"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["Tahun PC"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["Asal BKC"].astype(str).str.contains(q_str, case=False, na=False)
                | df_tabel_rapi["Kegiatan / Lokasi"].astype(str).str.contains(q_str, case=False, na=False)
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
            "Tahun PC": st.column_config.TextColumn("Tahun PC", width="small"),
            "Asal BKC": st.column_config.TextColumn("Asal BKC", width="medium"),
            "Kegiatan / Lokasi": st.column_config.TextColumn("Kegiatan / Lokasi", width="medium"),
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
                selected_pc_row = df_tabel_rapi.iloc[idx]["Tahun PC"]
                selected_asal_row = df_tabel_rapi.iloc[idx]["Asal BKC"]
                selected_giat_row = df_tabel_rapi.iloc[idx]["Kegiatan / Lokasi"]
                st.markdown(
                    f"#### 🔍 Rincian Item untuk Dokumen: `{selected_pbck3}` "
                    f"(Agenda: `{selected_agenda}` | Tahun PC: `{selected_pc_row}` | Asal: `{selected_asal_row}` | Kegiatan: `{selected_giat_row}`)"
                )

                if not df_detail.empty:
                    col_dtl_agenda = "AGENDA" if "AGENDA" in df_detail.columns else ("NO. AGENDA" if "NO. AGENDA" in df_detail.columns else df_detail.columns[0])
                    detail_filtered = df_detail.loc[df_detail[col_dtl_agenda].astype(str) == str(selected_agenda)].copy()
                    if not detail_filtered.empty:
                        KOLOM_DIBUANG_SET = {
                            "TOTAL CUKAI PEMBERITAHUAN", "TOTAL CUKAI MS", "NO", "MOR", "↑ MOR",
                            "BUNGKUS", "BP SERI I", "BUNGKUS.1", "BP SERI II", "BUNGKUS.2",
                            "BP SERI III-TP", "BUNGKUS.3", "BP SERI III-DP", "BUNGKUS.4",
                            "BP SERI MMEA", "TOTAL BP", "JUMLAH MS (BUNGKUS)",
                            "NILAI CUKAI PEMBERITAHUAN", "NILAI CUKAI MS", "CEK", "FILTER_MATCH"
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