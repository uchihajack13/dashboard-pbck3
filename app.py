# 4. RESOLVING GHOST COLUMNS (MENCEGAH KEYERROR & NAMEERROR)
# Membantu menyamakan kolom-kolom kritis seumpama ada pergantian nama di Drive Desktop
col_pabrik = "PERUSAHAAN" if "PERUSAHAAN" in df.columns else ("PERUSAHAAN_KEP" if "PERUSAHAAN_KEP" in df.columns else df.columns[1])
col_pbck3 = "NO_PBCK-3" if "NO_PBCK-3" in df.columns else ("NO_PBCK_3" if "NO_PBCK_3" in df.columns else df.columns[0])
col_tgl_pbck3 = "TANGGAL_PBCK-3" if "TANGGAL_PBCK-3" in df.columns else "TANGGAL_PBCK3"
col_back3 = "BACK-3" if "BACK-3" in df.columns else df.columns[0]
col_tgl_back3 = "TANGGAL BACK-3" if "TANGGAL BACK-3" in df.columns else "TANGGAL_BACK-3"
col_ck2 = "NO_CK-2" if "NO_CK-2" in df.columns else "NO_CK2"
col_tgl_ck2 = "TGL_CK-2" if "TGL_CK-2" in df.columns else "TGL_CK_2"

# 🚀 Koreksi Mapping Finansial (Sesuai Struktur PMK 113/2025)
col_potensi_cukai = "TOTAL_CUKAI" if "TOTAL_CUKAI" in df.columns else (" TOTAL_CUKAI " if " TOTAL_CUKAI " in df.columns else None)
col_cukai_ck2 = "CUKAI_MS" if "CUKAI_MS" in df.columns else (" CUKAI_MS " if " CUKAI_MS " in df.columns else None)
col_biaya_pengganti = "JUMLAH_BP" if "JUMLAH_BP" in df.columns else (" JUMLAH_BP " if " JUMLAH_BP " in df.columns else None)

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
