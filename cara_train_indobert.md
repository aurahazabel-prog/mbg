# Cara Menjalankan `train_indobert.py` + Kapan Dilaksanakan

## Kapan Dilaksanakan

| Syarat | Status |
|---|---|
| `data/gold_final.csv` sudah ada (hasil anotasi 700 + adjudikasi) | ⬜ blocking |
| GPU tersedia (Kaggle / Colab T4 — laptop macOS TIDAK cukup) | ⬜ blocking |
| Jika laptop tidak punya GPU, jalankan di Kaggle — lihat §"Jalankan di Kaggle". | |

Sesuai rencana: **minggu 5–8**, langsung begitu `gold_final.csv` jadi. Baseline sklearn (langkah sebelumnya) bisa jalan lebih dulu tanpa menunggu GPU.

## Perintah

```bash
pip install torch transformers datasets accelerate scikit-learn

# e2 = eksperimen utama: weak label + gold-train (default)
python scripts/train_indobert.py --exp e2 \
    --model indobenchmark/indobert-base-p1 \
    --gold gold_final.csv --seed 42

# e1 = weak-only (ablation); e3 = gold-only
python scripts/train_indobert.py --exp e1 --gold gold_final.csv --seed 42
python scripts/train_indobert.py --exp e3 --gold gold_final.csv --seed 42
```

Kombinasi lengkap skripsi = 3 eksperimen × 3 seed (42/123/2024) → 9 run, ±15 menit/run di T4.

### Opsi CLI

| Arg | Default | Arti |
|---|---|---|
| `--exp` | `e2` | e1=weak-only, e2=weak+gold, e3=gold-only |
| `--model` | `indobenchmark/indobert-base-p1` | ganti varian bila ingin (mis. rubert-tiny2 — lebih cepat) |
| `--gold` | `gold_final.csv` | path gold set (Wajib benar setelah adjudikasi) |
| `--seed` | `42` | seed untuk reproducibility; lakukan 42/123/2024 |
| `--epochs` | `8` | maksimum; early stopping dari val-gold |
| `--lr` | `2e-5` | learning rate |
| `--maxlen` | `128` | max token |
| `--batch` | `32` | batch size |
| `--min-gold` | `400` | berhenti dengan pesan bila gold < ini |

## Output

- `results/indobert_{exp}_{model}_{seed}.json` — metrik (macro-F1, per-class F1, dll)
- `runs/{exp}_{model}_{seed}/` — checkpoint (ditambahkan ke `.gitignore`; bisa regenerasi dari script + data)

## Aturan Anti-Bocor (penting untuk validitas Bab IV)

- e1: semua id gold TIDAK PERNAH ikut latih (hanya weak label dari non-gold pool).
- e2/e3: hanya train-gold yang ikut latih; test-gold selalu terpisah.
- Evaluasi akhir **hanya** pada test-gold hasil anotasi manusia.

## Jalankan di Kaggle (jika laptop tanpa GPU)

1. Masuk [kaggle.com](https://www.kaggle.com) → Create → New Notebook → Settings → Accelerator: **GPU T4 ×2** (atau P100).
2. Upload `data/` (weak_final.csv, MBG_Arya.csv, gold_final.csv) + `scripts/train_indobert.py` sebagai File / Dataset.
3. Di cell pertama:
   ```python
   !pip install -q transformers datasets accelerate scikit-learn
   !cp -r <path-dataset>/data . && cp <path-dataset>/scripts/train_indobert.py .
   ```
4. Di cell kedua:
   ```python
   !python train_indobert.py --exp e2 --gold gold_final.csv --seed 42
   !python train_indobert.py --exp e2 --gold gold_final.csv --seed 123
   !python train_indobert.py --exp e2 --gold gold_final.csv --seed 2024
   !python train_indobert.py --exp e1 --gold gold_final.csv --seed 42
   !python train_indobert.py --exp e3 --gold gold_final.csv --seed 42
   ```
5. Unduh `results/*.json` → taruh di folder `results/` repo → commit.

## Bandingkan dengan Baseline

Setelah semua run selesai, jalankan baseline klasik dengan gold yang sama:

```bash
python scripts/baseline_sklearn.py --gold gold_final.csv
```

Gabungkan semua JSON (`results/*.json`) menjadi tabel perbandingan Bab IV (baseline vs IndoBERT e1/e2/e3).
