# Diagram Alur Penelitian — Analisis Sentimen Komentar YouTube tentang Program MBG

Baseline klasik (NB/SVM/LR + TF-IDF) vs fine-tuned IndoBERT, dengan gold set hasil anotasi manusia.

## 1. Ringkasan Alur (diagram ASCII)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 0 — DATA AWAL                                                      │
│ Scraping komentar YouTube "MBG" → data/MBG_Arya.csv (12.786 baris mentah)│
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 1 — PROFILING (profile_mbg.py)                                     │
│ hasil_profil.md: 10.000 komentar valid, 0 duplikat, kolom waktu ADA      │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
┌─────────────────────────┐               ┌─────────────────────────────┐
│ TAHAP 2a — WAK LEXIKON  │               │ TAHAP 2b — WEAK LABEL LLM   │
│ scripts/weak_label_lex  │               │ scripts/weak_label_llm      │
│ W1 (200+ kata seed)     │               │ W2 — GLM (9.998/10.000)     │
│ → data/weak_lex.csv     │               │ → data/pilot100_llm.csv     │
└────────────┬────────────┘               └──────────────┬──────────────┘
             └─────────────────────┬────────────────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 3 — KONSENSUS W1∧W2 (consensus.py)                                 │
│ agreement 44,2% → data/weak_final.csv (strategi (a) konsensus ketat;     │
│ strategi (c) W2-mengatasi-konflik → ablation K5 di Bab IV)               │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 4 — SAMPLING GOLD 700 (sample_gold.py)                             │
│ stratified: S1 pos 100, S2 neg 220, S3 net 160, S4 sarkasme 100, S5     │
│ konflik 120 → data/gold_700.csv + gold_blind150 + gold_assisted550       │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 5 — PRE-LABEL 2 LLM INDEPENDEN (prelabel_gold.py)                  │
│ deepseek-v4.1-flash → data/gold_prelabel.csv (bebas sirkularitas X5)     │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 6 — ANOTASI MANUSIA (scripts/anotasi.py, 2 annotator)              │
│ 700 unit → annotation_A.csv + annotation_B.csv                          │
│ Kappa (kappa.py) target ≥ 0,61 → adjudikasi disagreements               │
│ → data/gold_final.csv                                                    │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 7 — ANONIMISASI + PREPROCESSING                                    │
│ anonymize.py → *_anon.csv; preprocess.py P1 (ringan) & P2 (slang map,   │
│ stopword, stemming Sastrawi)                                             │
└──────────────────────────────┬───────────────────────────────────────────┘
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────────────────┐  ┌───────────────────────────────────────┐
│ TAHAP 8a — BASELINE KLASIK   │  │ TAHAP 8b — INDOBERT FINE-TUNE         │
│ baseline_sklearn.py          │  │ train_indobert.py (Kaggle T4)         │
│ NB/SVM/LR + TF-IDF           │  │ e1/e2/e3 × seed 42/123/2024           │
│ P1 vs P2, strat. balanced    │  │ strategi (a)/(c) — ablation K5        │
│ → results/*.json             │  │ → results/indobert_*.json             │
└──────────────┬───────────────┘  └───────────────┬───────────────────────┘
               └───────────────┬───────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 9 — EVALUASI & ANALISIS                                            │
│ McNemar antar model terbaik; error analysis 30–50 kasus (sarkasme,      │
│ slang, politik); X5 agreement weak-vs-gold; IndoBERTopic → topik ×      │
│ sentimen (X6); opsional: temporal (K2)                                   │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ TAHAP 10 — PENULISAN SKRIPSI                                             │
│ Bab I–V; lampiran: prompt W2 + parameter, panduan anotasi, kappa,      │
│ repo; tabel utama Bab IV = perbandingan baseline vs IndoBERT            │
└──────────────────────────────────────────────────────────────────────────┘
```

## 2. Penjelasan Detail Tiap Tahap

### Tahap 0 — Data Awal (`data/MBG_Arya.csv`)
- **Input:** komentar YouTube tentang program Makan Bergizi Gratis (MBG).
- **Bentuk hasil:** satu CSV, 12.786 baris mentah; kolom: `comment_id`, `text` (teks komentar), `published_at_comment` (waktu posting), `video`, `channel`, `url`.
- **Berfungsi untuk:** sumber tunggal seluruh analisis; dengan kolom waktu, analisis temporal (tren mingguan) jadi opsi tambahan yang memperkuat **novelty**.
- **Digunakan di tahap:** semua. Diseleksi jadi 10.000 komentar valid ber-teks.

### Tahap 1 — Profiling (`hasil_profil.md`)
- **Input:** `data/MBG_Arya.csv`.
- **Bentuk hasil:** laporan Markdown: statistik deskriptif (jumlah baris, duplikat = 0, median panjang 74 karakter, 2.068 emoji, 377 ALL-CAPS, 82 komentar <5 karakter), deteksi kolom waktu.
- **Berfungsi untuk:** bukti data bermutu (dipakai di Bab III metodologi) + dasar keputusan desain (mis. K2 temporal; batas minimal komentar).
- **Digunakan di tahap:** kriteria sampling Tahap 4 dan justifikasi protokol ke pembimbing.

### Tahap 2a — Label Leksikon W1 (`data/weak_lex.csv`)
- **Input:** 10.000 teks + leksikon seed 200+ kata (negasi 2-token).
- **Bentuk hasil:** CSV `id, label_w1 ∈ {negatif, netral, positif}` — label dari aturan kata yang cocok (heuristik cepat, tidak belajar apa pun).
- **Berfungsi untuk:** sinyal sentimen murah & transparan; jadi "juri pertama" konsensus.
- **Digunakan di tahap:** Tahap 3 (cross-check dengan W2).

### Tahap 2b — Weak Label LLM W2 (`data/pilot100_llm.csv`)
- **Input:** 10.000 teks → model GLM (`glm-5.3-flash`, endpoint opencode.ai, ± USD 2).
- **Bentuk hasil:** CSV `id, label_w2, sarkasme` — sebaran **neg 69% / net 25% / pos 6%**, sarkasme flag 8%; 2 parse_error.
- **Berfungsi untuk:** label "peniler sekamar" berbasis pemahaman konteks bahasa (lebih tajam dibanding leksikon, terutama sarkasme/slang).
- **Digunakan di tahap:** Tahap 3; dasar pra-label ulang Kalau Plan B aktif; sumber bagi strategi (c) di K5.

### Tahap 3 — Konsensus W1∧W2 (`data/weak_final.csv`)
- **Input:** `weak_lex.csv` + `pilot100_llm.csv`.
- **Bentuk hasil:** CSV `id, label_w1, label_w2, weak_final` — label final dari aturan konsensus. Agreement W1–W2 44,2% → 4.420 unit sepakat (neg 2.441, net 1.728, pos 251).
- **Berfungsi untuk:** keputusan K5 — data latih pool (a) konsensus ketat vs (c) konsensus+LLM-mengatasi-konflik. Ini jadi **ablation nyata di Bab IV**.
- **Digunakan di tahap:** Tahap 8 (e1 weak-only, e2 weak+gold).

### Tahap 4 — Sampling Gold 700 (`data/gold_700.csv` + `gold_blind150` + `gold_assisted550`)
- **Input:** pool 10.000 berprovenance (strata: w1/w2/conflict/sarkasme).
- **Bentuk hasil:** 3 CSV — `gold_700.csv` (id + strata internal), `gold_blind150.csv` (151 unit buta, `id,text` saja), `gold_assisted550.csv` (id, text, `cek_cermat`, `label_pre`).
- **Berfungsi untuk:** ground truth benar-benar manusia; stratifikasi menentukan sebaran label tidak salah rangka.
- **Digunakan di tahap:** Tahap 5 (prelabel), Tahap 6 (anotasi), Tahap 8 (gold test).

### Tahap 5 — Pre-label 2 LLM (independen) (`data/gold_prelabel.csv`)
- **Input:** 700 teks → `deepseek-v4.1-flash` (+ ±qwen di-drop karena censor politik) — model **BUKAN GLM** (w2) → bebas sirkularitas.
- **Bentuk hasil:** CSV `id, label_m1, label_m2, cek_cermat` — dua opini LLM yang tidak saling mengenal; flag `cek_cermat=ya` bila beda dengan GLM.
- **Berfungsi untuk:** mempercepat anotasi assisted; protokol human-in-the-loop yang terdokumentasi untuk Bab III.
- **Digunakan di tahap:** Tahap 6 (bentuk `gold_assisted550.csv`).

### Tahap 6 — Anotasi Manusia + Kappa + Adjudikasi (`data/gold_final.csv`)
- **Input:** blind150 + assisted550, `panduan_anotasi.md` v2.1.
- **Bentuk hasil:** `annotation_A.csv`, `annotation_B.csv` (id, label, sarkasme, tak_jelas, catatan) → kappa Cohen (target ≥ 0,61) → `gold_final.csv` (id, label_a, label_b, label_final, sarkasme_final, tak_jelas, adjudicated).
- **Berfungsi untuk:** **ground truth inti penelitian** — satu-satunya standar penilaian model; kappa = bukti keandalan antar-annotator wajib Bab III/IV.
- **Digunakan di tahap:** split (Tahap 7), evaluasi semua model (Tahap 8–9), skripsi.

### Tahap 7 — Preprocessing + Anonimisasi (`*_anon.csv` + hasil P1/P2)
- **Input:** semua CSV data.
- **Bentuk hasil:**
  - `MBG_Arya_anon.csv`, `weak_final_anon.csv`, `gold_700_anon.csv` — id di-hash SHA-256+salt; kolom identitas (video/channel/url) dibuang; `data/.hash_map.json` gitignored.
  - Hasil P2 = teks kebersihan: **slang map 40+ entri, stopword bahasa Indonesia, stemming Sastrawi** (P1: ringan: huruf kecil + hapus tautan).
- **Berfungsi untuk:** etika publikasi (tidak ada data pribadi yang beredar); tabel slang = **kontribusi kecil** di Bab III; perbandingan P1 vs P2 = ablation X4.
- **Digunakan di tahap:** semua model Tahap 8.

### Tahap 8a — Baseline Klasik (`results/*.json`)
- **Input:** teks preprocessed (P1 & P2) + label (weak strategi (c) / gold).
- **Bentuk hasil:** JSON per model: NB / SVM / LR dengan akurasi, macro-F1, per-class F1, confusion matrix.
- **Berfungsi untuk:** patokan (baseline) klasik yang mudah direplikasi; menunjukkan seberapa banyak IndoBERT menambah nilai.
- **Digunakan di tahap:** semua perbandingan di Bab IV; hasil smoke: LR macro-F1 0,58–0,60 (weak-vs-weak, bukan angka skripsi).

### Tahap 8b — IndoBERT Fine-tune (`results/indobert_*.json`)
- **Input:** teks + label (weak / gold), 3 eksperimen:
  - **e1** latih weak-only; **e2** latih weak + train-gold; **e3** latih gold-only.
- **Bentuk hasil:** JSON per (exp, model, seed): macro-F1, per-class F1, waktu, jumlah parameter.
- **Berfungsi untuk:** menjawab **RQ inti**: seberapa besar nilai tambah LLM-weak-label + human-verification vs baseline klasik.
- **Digunakan di tahap:** tabel utama Bab IV, McNemar Tahap 9, sebaran seed untuk menunjukkan stabilitas.

### Tahap 9 — Evaluasi & Analisis Tematik
- **Input:** semua JSON hasil Tahap 8 + model terbaik.
- **Bentuk hasil:**
  - Uji **McNemar** antar pasangan model terbaik (signifikansi beda kinerja).
  - **Error analysis** 30–50 kasus: sarkasme, slang, politik — dikategorikan, dikutip di Bab IV.
  - **X5**: agreement weak label vs gold → metrik utama noise label LLM.
  - **X6**: IndoBERTopic pada ±10 k → crosstab tema × sentimen; opsional X2-varian / temporal (K2 = tren mingguan × sentimen).
- **Berfungsi untuk:** penuhi RC (research contribution) + C4/C5 (pembahasan mendalam); justifikasi klaim kontribusi penelitian.
- **Digunakan di tahap:** Bab IV pembahasan, Bab V kesimpulan.

### Tahap 10 — Penulisan & Lampiran
- **Input:** semua di atas.
- **Bentuk hasil:** skripsi Bab I–V + lampiran: prompt W2 + versi model + parameter (replikabilitas), panduan anotasi, worksheet kappa, repo bersih (final).
- **Berfungsi untuk:** bukti transparansi & replikabilitas; artefak utk sidang di §3 `Rencana_Tindak_Lanjut.md`.
- **Digunakan di tahap:** sidang.

## 3. Artefak Kunci per Tahap (cepat referensi)

| Tahap | Artefak | Status |
|---|---|---|
| 0 | `data/MBG_Arya.csv` | ✅ |
| 1 | `hasil_profil.md` | ✅ |
| 2 | `data/weak_lex.csv`, `data/pilot100_llm.csv` | ✅ |
| 3 | `data/weak_final.csv` | ✅ |
| 4 | `data/gold_700.csv`, `gold_blind150.csv`, `gold_assisted550.csv` | ✅ |
| 5 | `data/gold_prelabel.csv` | ✅ |
| 6 | `annotation_A/B.csv` → `data/gold_final.csv` | ⬜ anotasi berjalan |
| 7 | `*_anon.csv`, `preprocess.py` | ✅ |
| 8 | `results/*.json` | ⬜ (baseline siap; IndoBERT menunggu gold + GPU) |
| 9–10 | tabel evaluasi, topik, skripsi | ⬜ |
