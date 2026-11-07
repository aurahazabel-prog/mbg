# Tabel Bab IV — Draft (menunggu hasil IndoBERT dari Kaggle)

> Status data: baseline final + X5 + kappa selesai. Slot IndoBERT (e1/e2/e3 × seed) kosong —
> isi begitu `results/indobert_*.json` dari Kaggle ditaruh di repo. Angka final Bab IV
> = baris test-gold 245 unit (anotasi manusia, kappa 0,845).

## Tabel 4.1 — Kinerja model pada test-gold (245 unit, macro-F1)

| Model | Set latih | Macro-F1 | Accuracy | F1 negatif | F1 netral | F1 positif |
|---|---|---|---|---|---|---|
| Naive Bayes + TF-IDF | weak(c) 9998 | 0,312 | 0,554 | 0,69 | 0,25 | 0,00 |
| SVM Linear + TF-IDF | weak(c) 9998 | 0,568 | 0,676 | 0,76 | 0,62 | 0,33 |
| **LogisticRegression + TF-IDF (terbaik klasik)** | weak(c) 9998 | **0,634** | **0,713** | 0,79 | 0,68 | 0,43 |
| IndoBERT e1 (weak-only) | weak(c) | *TBD Kaggle* | *TBD* | | | |
| IndoBERT e2 (weak+train-gold) | weak + 357 | *TBD* | *TBD* | | | |
| IndoBERT e3 (gold-only) | 357 | *TBD* | *TBD* | | | |

## Tabel 4.2 — Reliabilitas anotasi & noise weak label

| Metrik | Nilai | Keterangan |
|---|---|---|
| Cohen's Kappa A-B (700 unit) | **0,845** | kesepakatan 91,1% (638/700) — substansial (target ≥0,61) ✓ |
| Kesepakatan subset blind (151) | 94,0% | 142/151 |
| Kesepakatan subset assisted (549) | 90,3% | 496/549 — selisih 3,7 poin = bukti bukan rubber-stamp |
| **X5: LLM(W2) vs gold** | **81,1%** | 568/700 |
| Adjudikasi disagreement | 62 kasus | terjadi terutama pada ambigu konteks |

## Tabel 4.3 — Pola error LLM weak-labeler (dari X5, n=700)

| Gold | Prediksi LLM | n | Interpretasi |
|---|---|---|---|
| negatif | negatif ✓ | 336 | LLM tepat pada kelas negatif |
| netral | netral ✓ | 177 | — |
| positif | positif ✓ | 55 | LLM tepat pada kelas positif |
| **netral** | **negatif** | **75** | LLM meng-opini-kan komentar netral (berita/sindiran tanpa instruksi ke program) |
| **netral** | **positif** | **43** | idem ke arah sebaliknya (harapan/semoga dianggap pujian) |
| negatif | netral | 6 | — |
| negatif | positif | 6 (2+…)| kecil |
| positif | negatif | 2 | — |

**Insight utama:** kesalahan LLM terkonsentrasi di kelas NETRAL (118/137 kesalahan) — bukan
sarkasme/teknis. Konsisten dengan agreement W1∧W2 rendah (44,2%) sebelumnya: konflik justru
di netral. Implikasi: strategi K5(c) (LLM menang konflik) perlu ablation dibanding K5(a).

## Tabel 4.4 — Error analysis LR (test-gold, 46/245 = 18,8% salah)

Arah salah (gold→pred): netral→pos 20 · netral→neg 17 · neg→netral 6 · neg→pos 3.

| Kategori awal (otomatis) | n | Contoh (disingkat) |
|---|---|---|
| slang/daerah | 16 | "ƁAT maju terus ...mencerdaskan rakyat" (netral→pos) |
| ambigu / objek-tak-eksplisit | 5 | "Program MBG itu bagus sekali yang menjadi masalah itu siapa orangnya…" (netral→neg) |
| sarkasme | 3 | — |
| selisih-politik (tokoh) | 4 | "…korupsi utusan Presiden…" |
| lainnya | 18 | komentar pendek/berbahasa daerah/konteks video |

File mentah untuk diskusi manual: `data/error_lr_p2_c.csv` (kolom kategori_otom diisi
otomatis — finalisasi kategori dilakukan Anda & tim saat membaca teks penuh; target 30–50 kasus tercapai = 46).

## Rencana pelengkapan

1. Isi Tabel 4.1 baris IndoBERT (3eksperimen × 3 seed → rata-rata ± standar deviasi)
2. McNemar: IndoBERT-e2 vs LR (kandidat model terbaik)
3. Kategori error final (manual) → naratif Bab 4.4.x
