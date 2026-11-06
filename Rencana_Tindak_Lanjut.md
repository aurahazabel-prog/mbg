# Rencana Tindak Lanjut — Status 5 November 2026

Dokumen pendamping `Rencana_Riset_Skripsi_MBG.md`. Mencatat apa yang sudah selesai, simpangan protokol, dan urutan kerja berikutnya.

## 0. Status terkini ( Tahap 1–3 rencana asli)

| Item | Status | Artefak |
|---|---|---|
| Repo + dataset `MBG_Arya.csv` | ✅ | `data/MBG_Arya.csv`, 12.786 baris mentah; 10.000 komentar valid ber-teks; kolom waktu ADA (`published_at_comment`) → opsi analisis temporal terbuka |
| Profiling formal (Tahap 1) | ⚠️ belum dijalankan resmi | perlu `python scripts/profile_mbg.py data/MBG_Arya.csv` → simpan `hasil_profil.md` utk Lampiran |
| W2 weak label LLM | ✅ **SELESAI** | `data/pilot100_llm.csv` — 9.998/10.000 ok, 2 parse_error (masuk pool tanpa label) |
| W1 leksikon | ❌ belum | script belum ada |
| Konsensus W1∧W2 | ❌ belum | script belum ada |
| Gold set + anotasi | ❌ belum | — |
| Pemodelan | ❌ belum | — |

**Detail W2:** engine `--engine openai` di `scripts/weak_label_llm.py`, model `glm-5.3-flash` via endpoint OpenAI-compatible opencode.ai (bukan Claude Batches seperti rencana asli — biaya nyaris nol, ± USD 2 total; harga & model diverifikasi ulang sebelum run ulang).
Sebaran: **negatif 69% / netral 25% / positif 6%**, sarkasme ter-flag 811 (8%).

## 1. Simpangan protokol & penanganannya (WAJIB ditulis di BAB III)

Rencana asli: ID gold set di-exclude sebelum W2. Kenyataan: gold set belum ada saat W2 dijalankan → **W2 melabeli semua 10.000**, termasuk calon anggota gold set.

Mitigasi (valid, laporkan eksplisit):
1. **Anotasi gold tetap blind** — annotator TIDAK melihat `label_llm`; panduan anotasi + sheet kerja dibuat tanpa kolom LLM.
2. Evaluasi akhir hanya pada gold set **manusia** → tidak ada sirkularitas LLM-menilai-dirinya-sendiri; LLM tidak pernah jadi juri.
3. Saat training, jika satu baris punya weak label DAN gold label → **gold menang** (provenance dicatat).
4. Agreement LLM-vs-gold (X5) justru jadi metrik utama noise weak label — tetap terukur.
5. Bonus yang boleh dijual: label LLM-butaan + anotasi manusia = dua sumber independen untuk adjudikasi disagreements.

Konsekuensi biaya: kalau pembimbing menolak, Plan B tetap ada — sampling gold 700 dulu, lalu W2-ulang dengan `--exclude-ids` (murah, ±15 menit).

## 2. Urutan kerja berikutnya

### Minggu ini (pekan ~1–2) — ✅ SEMUA SELESAI 2026-11-05
1. ✅ **Profil resmi** → `hasil_profil.md` + bug-fix `profile_mbg.py` (deteksi kolom teks & BOM). Temuan: 10.000 baris, **0 duplikat**, waktu ADA (median 74 kar, 82 komentar <5 char, 2.068 emoji, 377 ALL-CAPS).
2. ✅ **W1 leksikon** → `scripts/weak_label_lex.py`, output `data/weak_lex.csv` (seed lexicon 200+ kata, negasi 2-token).
3. ✅ **Konsensus W1∧W2** → `scripts/consensus.py`, output `data/weak_final.csv`.
   **TEMUAN PENTING: agreement W1–W2 hanya 44,2%** → pool konsensus 4.420 (neg 2.441 / net 1.728 / **pos 251**). W1 seed-lexikon terlalu longgar (positif 18%) vs LLM (positif 6%) → positif jarang sepakat. Implikasi desain latih — **K5 (baru, diputuskan sebelum minggu 5)**:
   - (a) konsensus ketat (4.420) — noise rendah, data sedikit, positif cuma 251
   - (b) W2-saja (9.998) — data banyak, noise tidak terkontrol
   - (c) **konsensus + "lempar koin ke LLM" utk konflik** (semua 10k berlabel, LLM menangkan konflik) — rekomendasi; laporkan sensitivitasnya sebagai ablation X2-varian
   Keputusan (a/b/c) = ablation nyata di Bab IV, bukan jalan buntu.
4. ✅ **Sampling gold set** → `scripts/sample_gold.py`: 700 unit (S1 pos- agree 100, S2 neg-agree 220, S3 net-agree 160, S4 sarkasme 100, S5 konflik 120; seed 42, urutan diacak). Output blind: `data/gold_700.csv` (id,text saja) + internal `data/gold_strata.csv` + `test_data/gold_ids.txt`.
5. ✅ **`panduan_anotasi.md`** v1.0 — 8 aturan disambiguasi + alur 2 annotator + adjudikasi. Plus `scripts/kappa.py` (Cohen's Kappa + ekspor disagreements; sudah self-check vs known-answer).
6. ⚠️ **Keamanan (masih terbuka)**: rotate API key opencode (terekspos di chat); jangan commit key.

### Minggu 3–4 — Anotasi (protokol v2 assisted + blind control) — ⬅️ SEKARANG
7. ✅ Pre-label 700 oleh 2 LLM independen BUKAN-W2: `deepseek-v4.1-flash` + `qwen3.8-flash` (`scripts/prelabel_gold.py` → `data/gold_prelabel.csv`) — bebas sirkularitas X5.
7a. ✅ `scripts/gold_kit.py` → `gold_blind150.csv` (buta; strata S1/S2/S4/S5), `gold_assisted550.csv` (m1/m2 di kolom kanan), `template_annotation.csv`.
7b. Anotasi (±1–2 hari, 2 orang INDEPENDEN): 150 buta penuh; 550 assisted — cek cepat yang sepakat, nilai sendiri dulu yang beda. Kappa manusia-sesama di semua 700 (≥0,61) + metrik validasi protokol (kesepakatan blind-vs-assisted; anti rubber-stamp; Bab III).
8. Adjudikasi disagreements → `gold_final.csv` (+ kolom `metode`, `koreksi_llm`). Split: ±100 kalibrasi, sisanya train/test-gold.
⚠️ Protokol ini mengubah batasan Bab 3.4 rencana asli ("LLM tidak pernah terlibat pembentukan gold set") → **perlu restu eksplisit pembimbing**; justifikasi: human-in-the-loop verification + subset buta 150.

### Minggu 5–8 — Pemodelan (kode sudah disiapkan 2026-11-05; jalan begitu gold ada)
9. ✅ **Preprocessing** → `scripts/preprocess.py`: P1 (ringan) & P2 (slang map 40+ entri, stopword id, stemming Sastrawi — teruji aktif). Tabel slang = kontribusi kecil utk Bab III.
10. ✅ **Anonimisasi** → `scripts/anonymize.py`: `data/MBG_Arya_anon.csv` + `weak_final_anon.csv` + `gold_700_anon.csv` (id di-hash SHA-256+salt, kolom video/channel/url dibuang). Mapping id→hash di `data/.hash_map.json` — **gitignored, jangan pernah di-commit** (untuk join balik saat eksperimen internal). `.gitignore` baru ditambahkan.
11. ✅ **Baseline klasik** → `scripts/baseline_sklearn.py` (NB/SVM/LR + TF-IDF, class_weight balanced, X4 P1 vs P2, hasil ke `results/*.json`). Smoke test (weak-vs-weak, BUKAN angka skripsi): lr macro-F1 0,58–0,60. **Tinggal tambahkan `--gold gold_final.csv`.**
12. ✅ **IndoBERT** → `scripts/train_indobert.py`: exp e1/e2/e3, class weighting manual (positif 6%), val dari gold utk early stopping, eval test-gold, output JSON per seed. Jalan di GPU Kaggle — belum tervalidasi runtime (butuh GPU).
13. ✅ Class imbalance ditangani di kode (class_weight + macro-F1 + stratified). S1=100 positif di gold → metrik kelas minoritas meaningful.
14. ⬜ **Strategi latih K5** diimplementasikan di kode sebagai `--strategy c` (default) vs `a`; ablation (a) vs (c) di Bab IV.

### Minggu 9–10 — Evaluasi & tema
14. McNemar antar model terbaik; error analysis 30–50 kasus (sarkasme, slang, politik); X5 agreement weak-vs-gold.
15. IndoBERTopic pada ±10k → crosstab topik × sentimen (X6); analisis temporal opsional (kolom waktu ADA — tentukan setelah hasil profiling; jika diambil, jadi RC tambahan + perkuat novelty).

### Minggu 11–16 — Penulisan
16. Bab I–V sesuai B2; lampiran: prompt + versi model + parameter W2 (replikabilitas), panduan anotasi, kappa worksheet, repo closed.

## 3. Artefak yang harus ada di repo saat sidang

```
scripts/  profile_mbg.py  weak_label_llm.py  weak_label_lex.py  consensus.py  sample_gold.py
data/     MBG_Arya.csv  pilot100_llm.csv(weak W2)  weak_lex.csv(W1)  weak_final.csv  gold_700.csv  gold_final.csv
docs/     hasil_profil.md  panduan_anotasi.md  (requirements.txt)
notebooks/ baseline_sklearn.ipynb  indobert_finetune.ipynb  topics.ipynb
```

## 4. Keputusan yang masih terbuka (butuh kamu/dosen)

| # | Keputusan | Opsi | Rekomendasi |
|---|---|---|---|
| K1 | Restu LLM weak labeler (A5.2) | setuju / Plan B exclude-then-relabel | tetap lanjut; bawa §1 di atas + sitasi Gilardi 2023, Ding 2024 |
| K2 | Analisis temporal (kolom waktu ternyata ADA) | ambil / buang | ambil versi ringan (tren mingguan × sentimen model terbaik) hanya jika jadwal minggu 9–10 longgar |
| K3 | Annotator kedua | — | kunci orangnya sebelum akhir minggu ini (blocking) |
| K4 | Positif cuma 6% — definisi ulang? | tetap 3 kelas / gabung jadi 2 kelas | tetap 3 kelas (komparabilitas InSet) + laporkan rebalancing; 2-kelas jadi fallback kalau macro-F1 kelas positif < 0,3 |
| K5 | Strategi set latih weak (agreement W1–W2 44,2%) | konsensus ketat / W2-saja / konsensus+LLM-untuk-konflik | opsi (c) + laporkan ablation (a) vs (c) di Bab IV |
