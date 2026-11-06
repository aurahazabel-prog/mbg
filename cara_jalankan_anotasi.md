# Cara Menjalankan Server Anotasi

Panduan menjalankan form anotasi lokal untuk gold set 700 unit.

## Prasyarat

- Python 3 (tersedia default di macOS)
- Tidak butuh instalasi tambahan (stdlib murni, tanpa `pip install`)

## Langkah

### 1. Buka Terminal

Gunakan jendela terminal terpisah per annotator.

### 2. Masuk ke folder proyek

```bash
cd /Users/lufias/Project/intan/mbg
```

### 3. Jalankan server annotator A

```bash
python3 scripts/anotasi.py A
```

Terminal akan menampilkan:

```
Annotator A: buka http://localhost:8787  | output: /Users/lufias/Project/intan/mbg/data/annotation_A.csv
```

### 4. Jalankan server annotator B (terminal jendela kedua)

```bash
cd /Users/lufias/Project/intan/mbg
python3 scripts/anotasi.py B
```

Terminal akan menampilkan:

```
Annotator B: buka http://localhost:8788  | output: /Users/lufias/Project/intan/mbg/data/annotation_B.csv
```

### 5. Anotasi di browser

| Annotator | URL |
|---|---|
| A | <http://localhost:8787> |
| B | <http://localhost:8788> |

Per komentar: baca teks → klik label (`👍 +`, `0 netral`, atau `👎 −`), centang `sarkasme`/`tak_jelas` bila perlu, isi catatan (opsional) → klik 💾 **Simpan** → langsung pindah ke komentar berikutnya yang belum dinilai.

- 151 unit pertama adalah **blind** (tanpa pra-label); sisanya assisted — klik `[lihat pra-label]` hanya setelah memilih label sendiri (untuk unit `cek_cermat=ya`).
- Gambaran waktu: ±150–300 komentar/jam/orang.

## Hasil Penyimpanan

Tersimpan otomatis setiap kali klik Simpan:

- Annotator A → `data/annotation_A.csv`
- Annotator B → `data/annotation_B.csv`

Format kolom: `id,label,sarkasme,tak_jelas,catatan` (sesuai Panduan Anotasi v2.1 §4.1, siap untuk `scripts/kappa.py`).

## Catatan Penting

- **Biarkan terminal tetap terbuka** selama menganotasi; menutup = server berhenti (hasil yang tersimpan tetap aman).
- **Lanjut kapan saja:** jalankan ulang perintah langkah 3/4 — server lanjut dari komentar yang belum dinilai.
- **Error `Address already in use`** = server sudah jalan; langsung buka browser saja. Untuk mematikan server: `Ctrl+C` di terminal.
- **Dua orang, dua port berbeda** (A = 8787, B = 8788) agar bisa anotasi bersamaan dari komputer yang sama. Untuk teman di komputer sendiri, cukup jalankan `python3 scripts/anotasi.py B` di komputernya.

## Setelah Selesai 700/700

```bash
python3 scripts/kappa.py
```

Lalu adjudikasi disagreements → `data/gold_final.csv`.
