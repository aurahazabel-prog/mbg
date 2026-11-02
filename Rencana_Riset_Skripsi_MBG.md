# Rencana Riset Tugas Akhir (Skripsi)

**Topik:** Analisis Sentimen dan Klasifikasi Teks Bahasa Indonesia untuk Pengumpulan Opini Publik tentang Program Makan Bergizi Gratis (MBG)

**Dataset:** [Indonesian YouTube Comments on MBG Program](https://www.kaggle.com/datasets/aryachovapratama/makan-bergizi-gratis-platfrom-yt) — `MBG_Arya.csv`, 10.000 komentar YouTube bahasa Indonesia, 4,34 MB, *last updated* 21 Juni 2026.

> ⚠️ **Temuan verifikasi paling penting:** dataset ini berstatus **RAW & UNLABELED** (tidak memiliki kolom label sentimen). Ini bukan hambatan kecil — ini mengubah desain seluruh metodologi. Bagian [Analisis Mendalam](#bagian-a--analisis-mendalam-rencana-riset) menjelaskan konsekuensinya dan Bagian [Metodologi](#35-metodologi-pendekatan-umum) memberi strategi label yang layak untuk skripsi.

---

## BAGIAN A — ANALISIS MENDALAM RENCANA RISES

### A1. Kelayakan (Feasibility)

| Aspek | Penilaian | Catatan |
|---|---|---|
| **Ketersediaan data** | ✅ Kuat | 10.000 komentar cukup untuk skripsi NLP (sweet-spot: 5k–20k). Gratis, lisensi Kaggle. |
| **Kelengkapan label** | ❌ Tidak ada | Harus membuat label sendiri → biaya terbesar skripsi ini ada di **anotasi**, bukan di modeling. |
| **Komputasi** | ✅ Aman | Fine-tune IndoBERT `base` (±125–134M params, maxlen 128–256) berjalan di GPU 6–8 GB (bisa pakai Kaggle Colab T4 gratis / sewa GPU). Klasik (TF-IDF+SVM) cukup CPU. |
| **Keahlian** | ⚠️ Butuh belajar | Pra-pemrosesan Indonesia + HuggingFace + protokol anotasi. Semua berjenjang dan bisa dipelajari bertahap. |
| **Waktu (16 minggu)** | ⚠️ Rapat tapi realistis | Dengan skema semi-automated labeling (lihat A3). Dengan anotasi manual penuh 10.000 baris → **tidak realistis**. |
| **Isu etis/privasi** | ✅ Terkendali | Komentar publik; tetap perlu anonimisasi `username`/`comment_id` dan tidak menyebut kanal/korban secara spesifik di laporan. |

**Kesimpulan kelayakan:** Riset ini **LAYAK** dilanjutkan, dengan satu syarat wajib: rencana Anda harus secara eksplisit memuat **protokol pelabelan** (annotation protocol). Rencana riset yang menyatakan "analisis sentimen" tanpa menjelaskan asal label akan langsung dipertanyakan penguji.

### A2. Konsekuensi dataset tanpa label

Pilihan strategi pelabelan (dan trade-off-nya):

| Strategi | Cara | Biaya | Kualitas | Rekomendasi |
|---|---|---|---|---|
| **S1. Manual penuh** | Anotasi semua 10.000 | ~200+ jam, tidak realistis untuk S1 | Tinggi | ❌ Hindari |
| **S2. Manual sebagian + klasik** | Anotasi 1.000–1.500, latih SVM/NB/LR | ±2–3 minggu (2 annotator) | Sedang–tinggi | ✅ Valid, tapi novelty rendah |
| **S3. Semi-supervised / weak labeling** (REKOMENDASI) | (a) Label heuristik leksikon sentimen Indonesia (InSet/lexicon) + (b) zero-shot/few-shot IndoBERT atau LLM → *distant supervision*; latih model pada data ter-label otomatis; kemudian **validasi manual pada subset 500–800** sebagai gold set | ±1 minggu anotasi | Sedang, tapi terukur | ✅✅ Paling pas untuk skripsi: gabung S2+S3 |
| **S4. Tanpa label (unsupervised murni)** | BERTopic + analisis leksikal | Murah | Tidak ada akurasi model terawasi | ⚠️ Jadi komponen sekunder, bukan rencana utama |

**Skema terpilih untuk rencana ini (S3+gold set):**
1. Bangun **gold set** 600–800 komentar (sampling terstratifikasi acak) yang dianotasi **2 annotator** manusia → ukur **Cohen's Kappa** (target ≥ 0,61 *substantial agreement*).
2. Label sisanya secara otomatis (weak supervision: leksikon + model zero-shot; konsensus keduanya = label).
3. Fine-tune IndoBERT pada (weak labels + gold set), **evaluasi hanya pada gold set** — inilah angka yang dilaporkan di skripsi.
4. Validasi silang: bandingkan akurasi weak-label vs penilaian manual pada gold set (laporkan noise label sebagai keterbatasan).

Ini metodologis sah (praktik standar *distant supervision*, Feldman et al., dan umum di riset sentimen bahasa daerah/rendah-resource), dan justru jadi **nilai jual** di sidang: Anda menjawab keberatan "label dari mana" dengan protokol, bukan dengan asal-asalan.

### A3. Posisi novelty (gap penelitian)

Riset sentimen Indonesia sudah sangat banyak (pemilu, Pilkada, e-commerce, film, Twitter/X). Yang membuat skripsi Anda **tidak ulangan**:

1. **Objek kebijakan publik aktual**: MBG adalah program prioritas nasional yang diperdebatkan (dimulai Januari 2025; [fakta anggaran, jumlah penerima, dan kasus keracunan harus Anda verifikasi & sitasi dari sumber resmi: BGN, Kemenkeu/APBN, Kemendikdasmen, berita terverifikasi]). Dataset opini YouTube tentang MBG relatif baru; sedikit studi yang mempublikasikan **protokol anotasi + dataset ter-label** untuk domain ini.
2. **Dua-layer analisis** (bukan cuma akurasi): *model* (klasifikasi sentimen) **dan** *temuan sosial* (pola opini publik: tema & aspek yang dikritik/didukung). Skripsi Anda punya bab "pembahasan opini publik", bukan hanya tabel metrik.
3. **Aspek komparatif model**: baseline klasik (TF-IDF + SVM/NB) vs transformer (IndoBERT / IndoBERT-lite / mBERT) vs pendekatan weak-labeling — dengan analisis kesalahan (error analysis) kasus sarkasme & bahasa gaul.
4. **(Opsional, pembeda kuat)** Deteksi **aspek**: sentimen per aspek (gizi, kebersihan/keamanan pangan, anggaran, distribusi, manfaat) — aspek-based sentiment via keyword/label Propaganda-style mining atau co-occurrence topic–sentiment.

**Gap statement siap pakai (BAB I):**
> "Penelitian terdahulu analisis sentimen bahasa Indonesia banyak difokuskan pada ranah elektoral dan komersial dengan dataset yang sudah berlabel (mis. InSet, Emotic-Indo). Belum tersedia (dan belum lazim divalidasi) protokol analisis sentimen untuk opini publik terhadap program Makan Bergizi Gratis berbasis komentar YouTube yang berlabel andal, mengingat dataset mentah yang ada tidak dilengkapi label sentimen. Penelitian ini menutup kesenjangan tersebut dengan menyusun gold set berlabel hasil anotasi ganda (Cohen's Kappa ≥ 0,61) dan membandingkan pipeline klasik dan transformer di atas strategi weak supervision."

### A4. Risiko utama & mitigasi

| # | Risiko | Dampak | Mitigasi |
|---|---|---|---|
| 1 | Dataset tanpa label | Proyek jalan di tempat | Protokol S3 (weak labels + gold set 600–800) — sudah jadi desain inti |
| 2 | Kualitas/provenan CSV tidak diketahui (tanggal? video? duplikat?) | Kesimpulan temporal tidak bisa dibuat | Jalankan `scripts/profile_mbg.py` SEBELUM finalisasi Bab III; jika kolom waktu tidak ada, **buang** rencana analisis tren temporal → ganti jadi analisis per-tema |
| 3 | Sarkasme & bahasa gaul ("mantap sih bikin keracunan") | Akurasi turun, penguji menyerang | Masukkan kategori sarkasme di panduan anotasi; laporkan error analysis; augmentasi gold set dengan sampel sulit |
| 4 | Kelas tidak seimbang (netral mendominasi / positif-negatif ekstrem) | Accuracy menipu | Wajib pakai **macro-F1** + stratified split; bahas class weight/focal loss |
| 5 | Anotasi memakan waktu > jadwal | Skripsi telat | Batasi gold set ≤ 800; mulai anotasi minggu ke-2; siapkan Plan B (kurangi ke 400 + augmentasi) |
| 6 | Label otomatis bias (leksikon salah tangkap konteks) | Model latih jelek | Konsensus 2 sumber weak-label + laporan noise; gold set hanya dari anotasi manusia |
| 7 | GPU terbatas | Fine-tune gagal | Kaggle/Colab T4 gratis; fallback IndoBERT-lite / DistilBERT-id; maxlen 128; batch kecil + gradient accumulation |
| 8 | Isu etika (privasi komentar) | Revisi dosen | Anonimisasi (buang username/ID), kutip maksimum 1–2 komentar per temuan, sebutkan comply dengan kebijakan Kaggle |
| 9 | Overclaim "penggambar opini publik" padahal sampel YouTube bias (self-selection, bot, buzzer) | Digerogoti penguji | **Batasan penelitian eksplisit**: "opini pengguna YouTube, bukan opini publik secara statistik" (lihat Bab I batasan) |

### A5. Status Keputusan Metodologis — FINAL (2 November 2026)

1. ✅ **Skema pelabelan:** Weak supervision (leksikon + **LLM**) + gold set anotasi ganda.
2. ✅ **Pelabelan pakai LLM: BOLEH**, dan resmi menjadi sumber **W2** — Claude API `claude-haiku-5-5` via **Message Batches API** (asinkron, diskon 50%). Protokol lengkap + aturan anti-sirkularitas ada di Tahap 3; implementasi: `scripts/weak_label_llm.py`. Estimasi biaya seluruh pelabelan 10k komentar: **< USD 1** (≈ Rp15 ribu). Alternatif nol-biaya di Plan B (Kaggle LLM API / Ollama lokal).
3. ✅ **Kelas sentimen:** 3 kelas — Positif / Netral / Negatif (+ flag `sarkasme` & `alasan` untuk error analysis).
4. ✅ **Fokus skripsi: PEMODELAN (Informatika/Ilmu Komputer)** — Bab IV bertumpu pada desain eksperimen X1–X6, metrik, dan analisis kesalahan model. **Keputusan BERTopic: YA, dipakai** tetapi hanya sebagai komponen pendukung jawaban RM4 (crosstab topik × sentimen, ±1 minggu kerja di minggu 9–10), bukan full aspect-based sentiment analysis — supaya bobot tetap ke modeling dan jadwal aman.
5. ⚠️ Satu-satunya yang masih perlu **restu dosen**: butir 2 (LLM sebagai weak labeler). Sebagian pembimbing minta sumber label "tradisional" — bekalmu: sitasi praktik *distant supervision/LLM-as-annotator* (mis. Gilardi et al. 2023; Ding et al. 2024) + bukti agreement LLM-vs-gold (X5) yang akan kamu laporkan.

---

## BAGIAN B — RENCANA RISES DETAIL (BLUE-PRINT SKRIPSI)

### B0. Judul (3 opsi)

1. ✅ *(TERPILIH — fokus pemodelan)* **"Analisis Sentimen Komentar YouTube terhadap Program Makan Bergizi Gratis Menggunakan Fine-Tuning IndoBERT dengan Weak Supervision Berbasis LLM dan Gold Set Hasil Anotasi Ganda"**
2. "Klasifikasi Teks dan Analisis Sentimen Bahasa Indonesia untuk Menambang Opini Publik Program Makan Bergizi Gratis Berbasis Komentar YouTube"
3. "Perbandingan Model Klasik dan Transformer untuk Analisis Sentimen Program Kebijakan Publik Nasional: Studi Kasus Program Makan Bergizi Gratis"

### 3.1 Latar Belakang (kerangka paragraf BAB I)

- **P1 — Konteks kebijakan:** MBG sebagai program prioritas nasional (gizi siswa & ibu hamil; diluncurkan awal 2025). Sebutkan: sasaran, payung hukum (Perpres/Inpres), pelaksana (Badan Gizi Nasional), anggaran 2025–2026, dan dinamika publik (dukungan luas, kritik eksekusi, laporan kejadian keamanan pangan). **Setiap angka WAJIB dari sumber resmi/berita terverifikasi — verifikasi sendiri, jangan kutip ringkasan ini sebagai fakta.**
- **P2 — Urgensi menambang opini:** survei resmi terbatas & tertinggal; media sosial (YouTube) adalah ruang deliberasi massa program publik; komentar = opini organik, tidak terstruktur.
- **P3 — Peluang teknis:** NLP bahasa Indonesia matang (IndoBERT/IndoNLU, Sastrawi, InSet); analisis sentimen media sosial jadi instrumen policy monitoring.
- **P4 — Kesenjangan:** dataset opini MBG tersedia (Kaggle, 10.000 komentar) tetapi **tanpa label**; studi terdahulu jarang menjustifikasi asal label → butuh protokol anotasi + weak supervision yang direplikasi dan dilaporkan terbuka. (Gap statement A3.)
- **P5 — Kontribusi penelitian:** (i) gold set berlabel & protokol anotasi yang bisa direplikasi; (ii) model sentimen MBG tervalidasi (baseline vs transformer); (iii) temuan tematik opini publik (aspek yang didukung/dikritik).

### 3.2 Rumusan Masalah

1. Bagaimana membangun dataset berlabel andal dari 10.000 komentar YouTube tak-berlabel tentang program MBG, dan seberapa tinggi kesepakatan antar-annotator (Cohen's Kappa) pada gold set?
2. Seberapa baik model klasifikasi teks klasik (Naïve Bayes, SVM, Logistic Regression berbasis TF-IDF) dibandingkan model transformer (IndoBERT, mBERT) dalam mengklasifikasi sentimen komentar MBG berdasarkan macro-F1 pada gold set?
3. Strategi weak supervision (leksikon + LLM) mana yang menghasilkan label otomatis dengan noise terendah terhadap gold set?
4. Apa saja tema/aspek dominan dalam opini publik (positif & negatif) terhadap program MBG di kolom komentar YouTube?

### 3.3 Tujuan

1. Menghasilkan gold set ≥ 600 komentar berlabel 3 kelas dengan Kappa ≥ 0,61.
2. Mengukur dan membandingkan performa ≥ 3 model klasik + ≥ 2 transformer (target indikator: macro-F1 IndoBERT ≥ 0,80; baseline terbaik ≥ 0,70 — **sesuaikan setelah pilot**).
3. Mengevaluasi dampak kualitas weak label terhadap performa model akhir.
4. Memetakan distribusi sentimen × tema (gizi, keamanan pangan, anggaran, distribusi, manfaat ekonomi, dukungan politik).

### 3.4 Batasan / Lingkup

- Data: hanya dataset `MBG_Arya.csv` (komentar YouTube, bahasa Indonesia); **bukan** X/Twitter/TikTok; bukan sampling populasi Indonesia → **kesimpulan terbatas pada "opini pengguna YouTube"** (self-selected, bukan representatif secara statistik).
- Sentimen: 3 kelas (Positif/Netral/Negatif), level dokumen-per-komentar; tidak memodelkan intensi/stance terhadap entitas tertentu (kecuali aspek RC4).
- Model: IndoBERT-base/lite (indobenchmark), mBERT, baseline scikit-learn; tidak melatih LLM dari nol; **LLM hanya untuk weak labeling — tidak pernah terlibat pembentukan/evaluasi gold set**.
- Tidak ada analisis longitudinal kecuali kolom waktu tersedia (cek hasil profiling).

### 3.5 Metodologi (Pendekatan Umum)

**Paradigma:** kuantitatif-eksperimental (NLP) dengan tahap eksploratif-tematik, mengikuti alur CRISP-DM yang dimodifikasi + protokol anotasi.

```
[1 Akuisisi & Audit Data] → [2 Profiling & Pra-pemrosesan] → [3 Weak Labeling otomatis]
        → [4 Anotasi Gold Set (2 annotator, kappa)] → [5 Pemodelan & Eksperimen]
        → [6 Evaluasi & Analisis Kesalahan] → [7 Analisis Tema/Aspek] → [8 Penulisan]
```

**Tahap 1 — Akuisisi & audit provenan.** Unduh `MBG_Arya.csv`; jalankan `scripts/profile_mbg.py`; catat: kolom, kelengkapan, duplikat, rentang panjang, keberadaan timestamp/ID video. Dokumentasikan di Lampiran.

**Tahap 2 — Pra-pemrosesan** (dua varian, diperbandingkan):
- P1 "ringan" (untuk transformer): lowercasing, pembersihan URL/mention/emoji-unicode, normalisasi spasi, retokenisasi-friendly; simpan teks asli untuk anotasi.
- P2 "klasik" (untuk TF-IDF): + penghapusan stopwords (list Indonesia), slang mapping (contoh `gk/gak → tidak`, `bgt → banget`, `sy → saya`, `pjk → pajak` — pakai kamus gaul yang disitasi), stemming Sastrawi.
- Penanganan kode-campur (code-mixing) & singkatan: tabel normalisasi versi Anda (kontribusi kecil yang layak ditulis).

**Tahap 3 — Weak labeling otomatis (W):** *(revisi FINAL — LLM resmi menjadi W2)*
- **W1:** skor leksikon sentimen Indonesia (InSet / leksikon terbuka lain) → label threshold.
- **W2: LLM batch labeling via Claude API** — model `claude-haiku-5-5` ($0,10/$0,50 per MTok; cek harga terkini sebelum jalan), dijalankan dengan **Message Batches API** (asinkron, 50% lebih murah, maks 100.000 request/batch — 10k komentar cukup 2 batch @5.000) + **prompt caching** pada blok instruksi+few-shot (prefix sama di semua request). Satu komentar = satu request; output JSON `{label, sarkasme, alasan}`. Implementasi lengkap di `scripts/weak_label_llm.py` (tersedia, termasuk `--dry-run` & `--exclude-ids`). **Alur wajib: pilot `--limit 100` → review sebaran & 20 contoh → baru full run.**
- **Aturan metodologis (WAJIB ditulis di BAB III):**
  1. Label LLM adalah *weak label* untuk **training saja**; gold set **selalu** hasil anotasi manusia, dan **ID gold set dikecualikan dari pool pelabelan LLM** (`--exclude-ids`) agar tidak terjadi *circular evaluation*.
  2. LLM tidak pernah menjadi juri/verifikator gold set dan tidak pernah dipakai menghitung metrik akhir.
  3. Prompt (sistem + few-shot), nama & versi model, parameter (effort/max_tokens), dan contoh output dilampirkan penuh → replikabilitas.
  4. Agreement LLM-vs-gold (Cohen's Kappa, eksperimen X5) dilaporkan sebagai estimasi noise label.
- Label lemah = W1 ∧ W2 sepakat; konflik → *unlabeled pool* (tidak dipakai latih). Laporkan tingkat kesepakatan W1–W2 sebagai estimasi awal noise.

**Tahap 4 — Anotasi gold set (protokol; inti justifikasi ilmiah Anda):**
- Sampling: 700 unit (stratified proporsional panjang komentar + coverage weak label Pos/Net/Neg & pool konflik).
- Annotator: Anda + 1 rekan (bukan pembimbing sebagai annotator agar bisa jadi "external check" saat sidang).
- Unit analisis: satu komentar penuh; kategori: **Positif / Netral / Negatif** + flag tambahan: `sarkasme?`, `tak_jelas?`.
- Aturan utama (panduan lengkap di `panduan_anotasi.md` yang akan Anda tulis dari template dokumen ini): menilai *sentimen terhadap program/pelaksanaan MBG*, bukan polaritas kata; spam/idiom netral; komentar yang menyerang orang ≠ otomatis negatif program → berkode.
- Proses: anotasi independen → hitung **Cohen's Kappa** → diskusi disagreements (adjudikasi) → kappa final dilaporkan. Jika kappa < 0,61 → revisi panduan + tambah contoh → anotasi ulang.
- Pembagian: gold set dipecah **hanya untuk evaluasi akhir**; sebagian kecil (±100) boleh dipakai untuk kalibrasi panduan anotasi awal (di luar test).

**Tahap 5 — Pemodelan & eksperimen:**
- Dataset latih: weak labels (N≈6.000–8.000) + gold latih (±500–600, label manual lebih diutamakan bila konflik dengan weak).
- Split: **train/val/test = 80/10/10 stratified 3-kelas**; gold set **tidak pernah** ikut latih kecuali bagian train-gold yang dinyatakan eksplisit (design decision — tulis alasannya).
- Model & setting (ringkas, detail di tabel eksperimen B1):
  - NB, Linear SVM, Logistic Regression + TF-IDF (unigram+bigram, n-gram ±(1,2), sublinear_tf).
  - IndoBERT-base-p1 & IndoBERT-lite (`indobenchmark`), mBERT, maxlen 128, AdamW lr 2e-5, epoch ≤ 10 + early stopping, seed 3 (42,43,44) → laporkan mean±std.
  - Eksperimen ablation: (E1) latih full weak vs (E2) weak + gold vs (E3) gold-only 500 → ukur *nilai tambah anotasi manusia*.

**Tahap 6 — Evaluasi:** Accuracy, **macro & weighted F1**, precision/recall per kelas, confusion matrix, kappa model-vs-gold; uji McNemar antar dua model terbaik (α=0,05); **error analysis** 30–50 salah prediks (sarkasme, slang, konteks politik).

**Tahap 7 — Analisis tema/aspek (RC4):** topic modeling bahasa Indonesia (IndoBERTopic / LDA-Sastrawi) pada ±7.000 komentar; tabel co-occurrence topik × sentimen (gold + weak teruji); kutip komentar exemplar anonim; visualisasi (distribusi, heatmap topik-sentimen, bar per aspek). *Cek dataviz guidance saat membuat gambar.*

**Tahap 8 — Penulisan:** struktur Bab I–V (lihat B2), replikasi repositori (codebook, data teranonimisasi, requirements.txt).

### B1. Desain Eksperimen (ringkas)

| ID | Pertanyaan | Perlakuan | Metrik utama | Hipotesis awal |
|---|---|---|---|---|
| X1 | Transformer > klasik? | IndoBERT vs SVM/NB/LR (pra-proses P2 untuk klasik) | macro-F1 test-gold | H_a: ΔmacroF1 > +5pp |
| X2 | Weak labeling berguna? | E1 vs E3 (weak+gold vs gold-only) | macro-F1 | H_a: weak menambah data → F1 naik |
| X3 | Gold-only cukup? | E3 baseline | macro-F1 ≥ 0,70? | — (kalibrasi target) |
| X4 | Pra-pemrosesan penting utk klasik? | P1 vs P2 pada SVM | macro-F1 | normalisasi slang & stemming menaikkan |
| X5 | Noise weak label? | cek silang weak vs gold | agreement rate | ≥ 0,70 agar layak |
| X6 | Model mana + tema? | IndoBERT terbaik infer ke 10k → crosstab topik | distribusi sentimen | — (deskriptif) |

### 3.6 Tools & Dataset

Python 3.10+ · pandas/numpy · scikit-learn · Sastrawi · nltk (stopword id) · kamus slang Indonesia (mis. sumber daya NusaCrowds) · HuggingFace transformers + datasets + accelerate · IndoBERT (`indobenchmark/indobert-base-p1`, `indobert-lite-base`) · **`anthropic` SDK (Message Batches + prompt caching; `claude-haiku-5-5`; alternatif nol-biaya: Kaggle LLM API / Ollama lokal)** · IndoBERTopic/BERTopic+keybert · matplotlib/seaborn · Label Studio/Google Sheets untuk anotasi · Git+GitHub · [Kaggle/Colab T4] atau [sewa GPU]. **Anggaran API LLM: < USD 1** (simulasi kasar ±7 jt token input + 0,3 jt output untuk 10k request; harga per cache skill 2026-10-06 — verifikasi di `shared/live-sources`/pricing page sebelum run).

### 3.7 Jadwal (16 minggu efektif)

| Minggu | Aktivitas | Deliverable (cek-able) |
|---|---|---|
| 1 | Download CSV, profiling, audit provenan, seminar proposal Bab I–III draft | Laporan profiling + proposal v1 |
| 2 | Finalisasi panduan anotasi; pilot LLM `--limit 100` → review prompt → full run W1+W2 (batch, ID gold di-exclude); sampling gold set | Log pilot + weak labels 10k; csv 700 siap anotasi |
| 3–4 | Anotasi ganda (±150/300/hari untuk 2 orang) + kappa + adjudikasi | Gold set 700 + kappa ≥ 0,61 |
| 5 | Pra-pemrosesan P1/P2, split data, setup pipeline HF | Dataset train/val/test + script |
| 6 | Eksperimen klasik (NB/SVM/LR) X4 | Tabel hasil baseline |
| 7–8 | Fine-tune IndoBERT/mBERT (X1, X2, X3) | Run + log + checkpoint |
| 9 | Evaluasi menyeluruh, McNemar, error analysis | Bab IV draf 1 |
| 10 | Topik/aspek (X6) + visualisasi | Bab IV draf 2 |
| 11 | Penulisan lengkap (Bab I–V) + revisi dosen | Draf utuh |
| 12 | Uji plagiarsime/quality gate, siapkan lampiran & repositori | Repro closed |
| 13–14 | Sidang/ perbaikan (buffer) | — |
| 15 | Finalisasi & unggah dataset ter-label (opsional, bonus sitasi) | Public artifact |
| 16 | Serah-terima | Skripsi final |

### B2. Kerangka BAB Skripsi

- **BAB I:** Latar belakang (P1–P5), rumusan (3.2), tujuan (3.3), batasan (3.4), manfaat, sistematika.
- **BAB II:** Landasan teori — analisis sentimen & klasifikasi teks; bahasa Indonesia berdaya-rendah vs menengah (kasus gaul/sarkasme); IndoBERT (arsitektur, pretrain); weak/distant supervision; metrik (F1, Kappa); penelitian terkait (≥ 8–12 paper; minimal 5 dari 2023–2026; sisakan tabel perbandingan + kolom gap).
- **BAB III:** Metodologi = Tahap 1–5 B.1 + protokol anotasi (BAB III wajib memuat: panduan kode, jumlah annotator, sampling, kappa) + desain eksperimen + lingkungan.
- **BAB IV:** Hasil eksperimen (tabel X1–X5) → analisis kesalahan → **pembahasan opini publik** (X6: tema×sentimen, 4–6 temuan naratif, contoh anonim) → jawaban rumusan masalah satu-satu.
- **BAB V:** Kesimpulan, keterbatasan (bias platform YouTube, noise label, tidak representatif nasional), saran (stance detection, lintas platform, update temporal).
- **Lampiran:** panduan anotasi, confusion matrix penuh, script, kappa worksheet, link repositori.

### 3.8 Indikator keberhasilan (target, bukan janji)

1. Gold set ≥ 600, **Cohen's Kappa ≥ 0,61**.
2. **IndoBERT fine-tuned: macro-F1 ≥ 0,80** pada test gold (fallback realistis: ≥ 0,75).
3. Selisih model terbaik vs terbaik klasik dilaporkan + diuji (McNemar).
4. ≥ 4 tema opini teridentifikasi dengan contoh kutipan.
5. Repo replikabel + (bonus) dataset berlabel di-upload ke Kaggle/HF → sitasi sendiri.

### 3.9 Etika

Data publik → tetap: (1) buang/ hashing `username` & `comment_id`; (2) kutipan komentar di laporan: tanpa nama penulis, singkat; (3) hindari menampilkan identitas anak/minoritas di kutipan; (4) nyatakan kepatuhan pada kebijakan penggunaan Kaggle & YouTube ToS; (5) laporkan potensi bias (buzzer/bot) sebagai keterbatasan, klaim opini dibatasi frasa "pengguna YouTube yang terekam".

### 3.10 Plan B (kalau macet)

- **Budget API LLM nol / akses terbatas** → pakai Kaggle LLM API (credit gratis bulanan, Gemma/Gemini) atau Ollama lokal (gemma/qwen kecil) dengan pipeline prompt yang sama; atau mundurkan W2 ke zero-shot/few-shot IndoBERT klasik.
- Anotasi meleset dari target → perkecil gold set 400 + tambah *data augmentation* (back-translation id→en→id).
- GPU tak cukup → IndoBERT-lite / DistilBERT / mBERT base batch 8 maxlen 96, atau sewa T4 12 jam.
- Weak labels < 0,55 agreement → lanjut **supervised murni gold-set 600** (masih layak skripsi; X2 dihapus, X3 jadi utama).
- Kolom waktu ada → tambahkan analisis tren (mingguan, per fase kebijakan) sebagai RC tambahan.

---

## C. LANGKAH PERTAMA ANDA (checklist minggu ini)

- [ ] Unduh dataset & taruh `MBG_Arya.csv` di folder ini → jalankan `python -I scripts/profile_mbg.py MBG_Arya.csv` (hasilnya tentukan: kolom waktu? kolom apa? duplikat? panjang komentar?).
- [ ] Konfirmasi ke dosen: skema FINAL sudah tercatat di A5 — yang perlu restu hanya **butir 2 (LLM sebagai weak labeler)**; bekalmu: aturan anti-sirkularitas Tahap 3 + sitasi distant supervision/LLM-as-annotator (Gilardi et al. 2023, Ding et al. 2024) + hasil X5 nanti.
- [ ] Siapkan kredensial salah satu jalur: `ANTHROPIC_API_KEY` (atau `ant auth login`) / Kaggle LLM API / Ollama. Uji alur tanpa biaya: `python -I scripts/weak_label_llm.py MBG_Arya.csv --dry-run`, lalu pilot `--limit 100`.
- [ ] Cari 1 rekan annotator untuk minggu 3–4.
- [ ] Verifikasi fakta program MBG dari BGN/APBN 2025–2026 (untuk Bab I P1) — jangan pakai angka dari dokumen ini.
- [ ] Kumpulkan 10 paper pembanding (kata kunci: *sentimen + IndoBERT + YouTube*, *distant supervision Indonesian*, *BERTopic Indonesia*).
- [ ] Setujui/tolak opsi Plan B bila pilot LLM hasilnya < 0,55 agreement → kabari saya; saya lanjutkan menulis draf **BAB I** penuh + **panduan anotasi** + skrip **W1 leksikon & consensus W1∧W2** + notebook fine-tune IndoBERT.

---
*Disusun otomatis pada 2026-11-02 berdasarkan metadata resmi dataset Kaggle (diakses via API Kaggle). Semua klaim fakta publik tentang program MBG wajib direverifikasi oleh penulis dari sumber resmi sebelum masuk Bab I.*
