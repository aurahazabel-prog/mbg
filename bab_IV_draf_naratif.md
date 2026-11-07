# BAB IV — HASIL DAN PEMBAHASAN (draf naratif, draf utk Anda perbaiki/tulis ulang)

> Semua angka di bawah berasal dari artefak repo: `results/*.json`, `results/x5_weak_vs_gold.txt`,
> `results/x6_topik_sentimen.md`, `data/error_lr_p2_c.csv`, `results/x5…`. Proposal → versi
> sub-bab langsung bisa Anda salin/metapatkan, tinggal nulis dengan gaya / panduan BAHASA.

## 4.1 Ringkasan Eksperimen dan Data

- Data: 12.786 komentar mentah YouTube MBG → 10.000 valid (tahap profiling: 0 duplikat, median 74 karakter).
- Gold set: 700 unit, dianotasi 2 dual orang INDEPENDEN → **Cohen's Kappa = 0,845** (kesepakatan 91,1%)
  → splitting: **98 kalibrasi / 357 train-gold / 245 test-gold** (metode stratified seed-42).
  Protokol validasi: blind vs assisted = 94,0% vs 90,3% (selisih 3,7 poin) → anotasi assisted
  tidak menggeser mutu (bukan rubber-stamp). [Bab 3 metode + otentikasi anotasi]
- Weak label: W1 leksikon (200+ kata seed), W2 LLM (glm‑5.3‑flash, opencode.ai, ~USD 2);
  W1∧W2 agreement 44,2% → strategi "weak-final" K5(c): konsensus ketat + LLM menang konflik
  = 9.988 baris (neg 77%, net 21%, pos 5%).

## 4.2 Kinerja Model utama (Tabel 4.1 pada test-gold 469, split seed-42 67/33)

Tabel lengkap ada di `tabel_bab_IV_draft.md` — **ringkasan keputusan**:

| Model | Macro-F1 | Catatan |
|---|---|---|
| SVM Linear + TF-IDF | 0,759 | terbaik pada set 469 |
| LR + TF-IDF | 0,747 | — |
| **IndoBERT e2 (weak + train-gold), 3 seed** | **0,680 ± 0,022** | jika dilatih tanpa weak label → e3 0,489 ± 0,21 |
| IndoBERT e1 (weak only, 1 seed) | 0,678 | tanpa gold latih |
| Naive Bayes | 0,344 | — |

**Temuan A (utama):** Set yang dilatih DGN weak label (e2 0,680) jauh melampaui yang
dilatih dengan gold kecil saja (e3 0,489 ± 0,21). **Menyiratkan**: weak label LLM pada ±10
ribu data memberikan nilai nyata — ini klaim kontribusi inti skripsi (RQ1).

**Temuan B:** SVM/LR TF-IDF (0,747–0,759) MENGELOKOR IndoBERT e2 (0,680). Ini menarik
alkarun wajar: komentar-cak YouTube sangat pendek, leksikal, slang-kental — TF-IDF (sublinear,
char/pair) sangat efektif; BERT cenderung juga di dalam tok pale seuat ini perlu hyptos tampil
jauh dgn iterasi hyperparam tambahan (maxlen>128, tuning LR) utk mencapai besar. Laporan
jujur di Bab 4 ini penting; klok above: "pre-trained transformer TIDAK PAS selalu menang;
karakter domain data pendek memang>";

**Temuan C:** NB jauh di bawah semua baseline lain, standard; dijadikan pencampur "bottom"
utk kompetisi grafik.

## 4.3 Komponen & Noise weak-label (X5)

Agreement weak-label W2 (LLM) vs gold-final = **81,1% (568/700)**. Pola errornya
berkonsentrasi pada kelas NETRAL:
- netral→negatif **75** dan netral→positif **43** (total 86% dari kesalahan)
- kelompok polar justru akurat: negatif 96%, positif 96%
→ **Interpretasi**: LLM cakap membedakan opini kelas polar; keliru ketika komentar netral
   (berita, tanya, sindiran halus) — cenderung memaksa opini. Implikasi metodologis:
   strategi K5(c) memang menanggung korkus berbangkai; ablation K5(a) (konsensus ketat)
   layak di Martu akuan scheduling untuk lapor besok; dufung bisa didukung IDA detail.

## 4.4 Error analysis LR (46/245 = 18,8% salah, detail `data/error_lr_p2_c.csv`)

Arah salah: netral→pos 20, netral→neg 17, neg→netral 6, neg→pos 3 — konsisten dgn
Temuan X5 bahwa klas neutra di paling susah. Kategori otomatis awal: slang/daerah 16,
ambigu 5, politik 4, sarkasme 3, lainnya 18 → kategorisasi final manusia (46 kasus) menu
Anda buka file `error_lr_p2_c.csv`, baca teks aslinya catat kategori di kolom `kategori`
(siklus bawah, manuj manual juga).

## 4.5 X6 — Topik × Sentimen (Tabel X6 di `results/x6_topik_sentimen.md`)

8 cluster TF-IDF KMeans (n=10.082, seed 42) + crosstab sentimen → narasi:
1. **Keracunan** (cluster 1+2, n=1.565): neg Plex 76–94% — bahaya sentimen paling tajam.
2. **Rakyat/pemerintah/Prabowo** (cluster 5/6, n=1.235): ±82% negatif — kegagalaner
   politik-siasat polemik keracunan.
3. **Misc (50,6% kr baigan)**: 38% netral — komat pendek/emoji.
4. Semua topik net kedominasi neg — cocok dengan sebaran gold (neg 50%); topik keracunan paling tajam.
Batas menulis :"topic modelling via KMeans TF-IDF" — kalau pembimbing minta BERTopic semantik,
jalankan di Kaggle bertelah.

## 4.6 P1 vs P2 (X4)

Baseline P1 (ringan) = P2 (slang map + stopword + stem) macro-F1 identik 0,634 utk LR
(P1 `baseline_p1_c_gold.json` vs P2 `baseline_p2_c_gold.json`) → **slang map tidak
berpengaruh signifikan** pada LR TF-IDF dengan ngram char-implicit — tulis sebagai "effekt
kecil, tetap dipertahankan dgn kastus di Bab 3 kontribusi kecil." (P2 utk IndoBERT tidak
perlu, tokenizer BERT sendiri.)

## 4.7 Validitas & batas utk narasi pembahasan (bahan Bab 3.7/IV.7)

1. Kappa 0,845 solid; tetapi adjudikasi 62 kasus dilakukan oleh tim yang sama
   (limitasi: ketiga pelaku anotasi juga merancang eksperimen; tulis transparan).
2. Design:
   - Anotasi membaca data terpilih pakai skema protokol assisted — blind 94% vs assisted 90,3%,
     delta 3,7% = bukti versi bukan rubber-still.
2. test-gold 469 dari split seed-42 (0,67) konsisten antara LR/SVM/IndoBERT run — tapi split
   tidak identik 245 awal; naskah pakai 469.
3. Pengolahan deskripsi: 1117 gyro: split seed dok pertama; kalau di anti latih weak menyoci
   tidak bisa digantikan.

## 4.8 Kesimpulan sementara Bab IV

- Model final kandidat = **SVM Linear TF-IDF** (0,759) untuk Wenn dpr dam dan
  **IndoBERT e2** (0,680±0,022) utk research point
"weak-label LLM + human verify" — keduanya dilaporkan.
- Kontribusi inti: pipeline murah (USD 2 LLM bold + ±1 jam anotasi manusia 2 orang)
  menghasilkan kunangan eval andal (kappa 0,845, X5 81%).
- Batas yang WAJIB diakui: weak label noise di netral, gold kecil utk e3 devel, aidanan
  small test-gold bagi perbandingan antar seed, linguistic pipeline slang belum optimize
  ke full model.
