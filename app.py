# =====================================================================
# 7. PEMROSESAN METRIK EKSEKUTIF (PBCK-3 vs CK-2)
# =====================================================================

# 1. Menghitung Jumlah Dokumen
total_pbck3 = df_filtered[col_pbck3].nunique() if col_pbck3 in df_filtered.columns else len(df_filtered)

# Identifikasi Dokumen CK-2 Terbit
if col_ck2 in df_filtered.columns:
    df_filtered['STATUS_CK2_BOOL'] = df_filtered[col_ck2].apply(
        lambda x: "TERBIT" if pd.notnull(x) and str(x).strip() not in ["", "-", "nan", "NaN"] else "PROSES"
    )
    total_ck2 = df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"][col_ck2].nunique()
else:
    df_filtered['STATUS_CK2_BOOL'] = "PROSES"
    total_ck2 = 0

total_outstanding = total_pbck3 - total_ck2

# 2. Menghitung Nilai Finansial (Sesuai PMK 113/2025)
# Standarisasi nama kolom dari file Excel lu (' TOTAL_CUKAI ' dan ' CUKAI_MS ')
col_cukai_pbck3 = ' TOTAL_CUKAI ' if ' TOTAL_CUKAI ' in df_filtered.columns else 'TOTAL_CUKAI'
col_cukai_ck2 = ' CUKAI_MS ' if ' CUKAI_MS ' in df_filtered.columns else 'CUKAI_MS'
col_biaya_pengganti = ' JUMLAH_BP ' if ' JUMLAH_BP ' in df_filtered.columns else 'JUMLAH_BP'

# A. Nilai Cukai dari PBCK-3 Masuk (Potensi Awal)
nilai_cukai_pbck3 = pd.to_numeric(df_filtered[col_cukai_pbck3], errors='coerce').sum() if col_cukai_pbck3 in df_filtered.columns else 0

# B. Nilai Cukai dari CK-2 Terbit (Cukai MS / Realisasi Final)
# Syarat: Hanya hitung baris yang Status CK-2 nya "TERBIT"
if col_cukai_ck2 in df_filtered.columns:
    nilai_cukai_ck2 = pd.to_numeric(df_filtered[df_filtered['STATUS_CK2_BOOL'] == "TERBIT"][col_cukai_ck2], errors='coerce').sum()
else:
    nilai_cukai_ck2 = 0

# C. Biaya Pengganti (BP)
biaya_pengganti = pd.to_numeric(df_filtered[col_biaya_pengganti], errors='coerce').sum() if col_biaya_pengganti in df_filtered.columns else 0


# =====================================================================
# 8. PANEL UTAMA TAMPILAN COUNTER / METRIKS
# =====================================================================

st.markdown("### 📊 Kinerja Dokumen Kertas Kerja")
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
        help="Dokumen tanda perusakan pita cukai yang resmi rampung (Maks 10 Hari Kerja dari BACK-3)."
    )
with col3:
    st.metric(
        label="⏳ OUTSTANDING (DALAM PROSES)",
        value=f"{total_outstanding} Dokumen",
        delta=f"{(total_outstanding/total_pbck3)*100:.1f}% Sisa Pekerjaan" if total_pbck3 > 0 else "0%",
        delta_color="inverse",
        help="Dokumen yang belum diterbitkan CK-2 nya."
    )

st.markdown("---")

st.markdown("### 💰 Rekapitulasi Finansial Pengembalian Cukai (PMK 113/2025)")
col_fin1, col_fin2, col_fin3 = st.columns(3)
with col_fin1:
    st.metric(
        label="💸 POTENSI CUKAI MASUK (PBCK-3)", 
        value=f"Rp {nilai_cukai_pbck3:,.0f}",
        help="Total nilai cukai awal yang diajukan dalam dokumen PBCK-3."
    )
with col_fin2:
    st.metric(
        label="✅ REALISASI CUKAI SAH (CK-2 TERBIT)", 
        value=f"Rp {nilai_cukai_ck2:,.0f}",
        delta=f"Telah di-ACC (Memenuhi Syarat)",
        delta_color="normal",
        help="Total Nilai Cukai MS (Memenuhi Syarat) yang sudah terbit CK-2 nya dan sah untuk kompensasi/tunai."
    )
with col_fin3:
    st.metric(
        label="🏦 BIAYA PENGGANTI (PENERIMAAN BP)", 
        value=f"Rp {biaya_pengganti:,.0f}",
        delta="Penerimaan Negara",
        delta_color="off",
        help="Penerimaan dari biaya penyediaan pita cukai yang dirusak (Seri I, II, III, MMEA)."
    )

st.markdown("---")
