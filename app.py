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

# 🚀 UPDATE FINANSIAL: POTENSI (PBCK-3) VS REALISASI (CK-2)
# Menyesuaikan nama kolom dengan struktur DATABASE MERGE yang sebenarnya
col_cukai_pbck3 = ' TOTAL_CUKAI ' if ' TOTAL_CUKAI ' in df_filtered.columns else ('TOTAL_CUKAI' if 'TOTAL_CUKAI' in df_filtered.columns else None)
col_cukai_ck2 = ' CUKAI_MS ' if ' CUKAI_MS ' in df_filtered.columns else ('CUKAI_MS' if 'CUKAI_MS' in df_filtered.columns else None)

# 1. Total Nilai Cukai dari PBCK-3 (Potensi)
nilai_cukai_pbck3 = pd.to_numeric(df_filtered[col_cukai_pbck3], errors='coerce').sum() if col_cukai_pbck3 else 0

# 2. Total Nilai Cukai dari CK-2 (Realisasi Memenuhi Syarat)
# Hanya menjumlahkan baris yang CK-2 nya berstatus "TERBIT"
if col_cukai_ck2 and 'STATUS_CK2_BOOL' in df_filtered.columns:
    df_ck2_terbit = df_filtered[df_filtered['STATUS_CK2_BOOL'] == 'TERBIT']
    nilai_cukai_ck2 = pd.to_numeric(df_ck2_terbit[col_cukai_ck2], errors='coerce').sum()
else:
    nilai_cukai_ck2 = 0

biaya_pengganti = pd.to_numeric(df_filtered[col_biaya_pengganti], errors='coerce').sum() if col_biaya_pengganti in df_filtered.columns else 0

# Tampilkan Label Filter Aktif di Atas Dashboard
visual_periode_lbl = "Semua Periode Tahun " + str(selected_tahun)
if mode_periode == "Bulanan Tunggal (Single Month)":
    visual_periode_lbl = f"Bulan {selected_bulan_nama} {selected_tahun}"
elif mode_periode == "Kumulatif (s.d. Bulan)":
    visual_periode_lbl = f"Januari s.d. {selected_bulan_nama} {selected_tahun}"

st.markdown(f"🚩 **Periode Terpantau saat ini:** `{visual_periode_lbl}`  |  🏢 **Perusahaan Pabrik:** `{selected_pabrik}`")

# 8. PANEL UTAMA TAMPILAN COUNTER / METRIKS
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

st.markdown("---")

# 🚀 PANEL BARU: REKAPITULASI FINANSIAL GANDA
st.markdown("### 💰 Rekapitulasi Finansial Pengembalian Cukai (PMK 113/2025)")
col_fin1, col_fin2, col_fin3 = st.columns(3)

with col_fin1:
    st.metric(
        label="💸 POTENSI CUKAI MASUK (PBCK-3)", 
        value=f"Rp {nilai_cukai_pbck3:,.0f}",
        help="Total nilai cukai awal yang diajukan dalam dokumen PBCK-3 yang masuk."
    )
with col_fin2:
    st.metric(
        label="✅ REALISASI CUKAI SAH (CK-2 TERBIT)", 
        value=f"Rp {nilai_cukai_ck2:,.0f}",
        delta=f"Telah di-ACC (Memenuhi Syarat)",
        delta_color="normal",
        help="Total Nilai Cukai MS (Memenuhi Syarat) yang sudah terbit CK-2 nya dan sah dikembalikan."
    )
with col_fin3:
    st.metric(
        label="🏦 BIAYA PENGGANTI (PENERIMAAN NEGARA)", 
        value=f"Rp {biaya_pengganti:,.0f}",
        help="Penerimaan dari biaya penyediaan pita cukai yang dirusak."
    )

st.markdown("---")
