# Panduan Anotasi Gold Set — Sentimen Komentar YouTube terhadap Program MBG

**Versi 2.1 — 2026-11-06 (assisted + blind control; pra-label 1 model).** File kerja: `data/gold_blind150.csv` (buta), `data/gold_assisted550.csv` (kolom `label_pre` = **deepseek-v4.1-flash** + `cek_cermat`), `template_annotation.csv` (700 baris — isi di sini). Pra-label sengaja model BEDA dari W2 (GLM) → bebas sirkularitas X5; qwen di-drop karena sensor upstream pada konten politik. `cek_cermat=ya` (79/549, 14%) = deepseek≠GLM → nilai teliti; sisanya cek cepat. **Keputusan akhir label selalu manusia.** Perubahan protokol dari v1 dikonfirmasi ke pembimbing (butir A5.2-style).

## 0. Alur protokol assisted

1. **Subset BUTA 151 unit** (`data/gold_blind150.csv`; sampling acak strata S1/S2/S4/S5 + unit tanpa pra-label) → Anda & teman anotasi penuh TANPA melihat pra-label, INDEPENDEN.
2. **Sisa 549 unit (`gold_assisted550.csv`):** kolom keputusan selalu di kiri, `label_pre` di kanan.
   - `cek_cermat=tidak` → WAJIB tetap membaca komentar & memastikan; setuju atau koreksi.
   - `cek_cermat=ya` → nilai sendiri DULU, baru lihat `label_pre`.
3. Kedua annotator (A & B) menempuh langkah 1–2 INDEPENDEN satu sama lain.
4. Kappa pada SEMUA 700 (label_a vs label_b manusia) — target ≥ 0,61.
5. **Validasi protokol:** bandingkan bagian buta vs assisted (kasus serupa) — laporkan % kesepakatan sbg bukti bukan rubber-stamp.
6. Adjudikasi disagreements → `gold_final.csv` (+ kolom `metode ∈ {blind, assisted}`, `koreksi_llm`, `adjudicated`).

> Kenapa dibalik dari rencana asli? Kecepatan (±2×). Anchoring bias dikendalikan lewat subset buta, bukan lewat larangan total. Ini metodologis sah (human-in-the-loop verification), tapi WAJIB ditulis transparan di BAB III.

## 1. Unit analisis & prinsip utama

Satu baris = satu komentar penuh. Nilai **satu label sentimen TERHADAP program Makan Bergizi Gratis (MBG)** — bukan emosi umum penulis, bukan sentimen terhadap tokoh/parpol secara umum.

MBG = program pemerintah Indonesia: makanan bergizi gratis untuk siswa & ibu hamil, dijalankan Badan Gizi Nasional (BGN), diluncurkan awal 2025.

## 2. Kategori (pilih TEPAT SATU)

| Kode | Label | Definisi operasional |
|---|---|---|
| `+` | **positif** | Mendukung/memuji program ATAU pelaksanaannya: manfaat, apresiasi, harapan program berlanjut, syukur, pujian eksplisit ke MBG/BGN/dapur/SPPG. |
| `0` | **netral** | (a) Informasi/berita/tanya-jawab tanpa condong; (b) opini umum yang tidak menyebut/menyiratkan program; (c) spam/iklan/tak-terhubung MBG; (d) hanya emoji/hinaan tanpa objek program; (e) posisi berimbang ("pro kontra wajar, yang penting evaluasi"). |
| `-` | **negatif** | Mengkritik/menolak program ATAU pelaksanaannya: kasus keracunan/kegagalan distribusi, anggaran boros/salah sasaran, korupsi dana program, janji kampanye palsu, sinis/cemooh terhadap program, tuntutan bubarkan. |

Flag tambahan (selain label):

| Flag | Isi | Kapan |
|---|---|---|
| `sarkasme` | true/false | Makna terbalik: pujian palsu ("Wow hebat, menunya keracunan"). **Sarkasme terhadap program → label negatif** (kecuali sarkasme netral/tokoh lain → ikuti objeknya). |
| `tak_jelas` | true/false | Komentar tak bisa dipahami / terpotong / bahasa asing total → tetap beri label `0`. |

## 3. Aturan disambiguasi (kasus tersering)

1. **Kritik ke tokoh/parpol tanpa kaitan program → netral.** "Bahlil harus ditahan" ≠ soal MBG → `0`. Tapi "dana MBG dikorupsi Bahlil cs" → `-`.
2. **Hujatan tanpa objek program → netral.** "Pemerintah semua maling" (tanpa menyebut program/konteks MBG) → `0`; jika konteks kanal/video jelas soal MBG dan tuduhan korupsi diarahkan ke pelaksanaan program → `-`. Ragu → diskusikan di adjudikasi.
3. **Pertanyaan faktual → netral.** "MBG mulai kapan di daerah saya?" → `0` — meski nadanya skeptis ("katanya gratis, kok bayar?") → `0`.
4. **Keraguan bersyarat → netral.** "Setuju MBG kalau memang bergizi" → `0` (belum condong). "Setuju, bagus programnya" → `+`.
5. **Berita negatif yang dibagikan tanpa opini → netral** (posting ulang judul berita keracunan) — penilainya adalah *opini penulis*, bukan isi berita. KECUALI penulis menambahkan komentar (emoji 😂 terhadap berita = condong mengejek → boleh `-`, tandai untuk adjudikasi).
6. **Emoji-only:** 😢😢 sendirian di kanal MBG → `0` (tak_jelas=true, kemungkinan sedih — tapi tanpa objek jelas). 👍/❤️ eksplisit → `+`; 😂/🤡/🤮 → `-`.
7. **Komentar di luar topik MBG (spam jualan, bahas artis) → `0`** tanpa kecuali.
8. **Panjang bukan masalah:** satu kata "BUBARKAN AJA" (konteks program) → `-`; 500 kata tapi curhat pribadi → `0`.

## 4. Proses anotasi (2 annotator)

1. **Independen.** Masing-masing mengisi `annotation_a.csv` / `annotation_b.csv` (kolom: `id,label,sarkasme,tak_jelas,catatan`) TANPA melihat file lain dan tanpa kolom label LLM apa pun. Anotasi ~150–300/hari/orang.
2. Kalibrasi: 50 unit pertama bersama → diskusikan perbedaan sebelum lanjut.
3. Setelah penuh: hitung **Cohen's Kappa** (skrip `scripts/kappa.py`). Target **≥ 0,61** (substantial agreement).
4. Kappa < 0,61 → revisi panduan (tambah contoh nyata dari disagreements) → anotasi ulang bagian yang berbeda.
5. **Adjudikasi:** setiap disagreement didiskusikan → `gold_final.csv` kolom `label_final` + `adjudicated=true`. Jika buntu → `0,tak_jelas=true`.
6. Hasil akhir disimpan: `gold_final.csv` (`id,label_a,label_b,label_final,sarkasme_final,tak_jelas,adjudicated`).

## 5. Pembagian penggunaan gold set (keputusan desain BAB III)

- ±100 unit (termasuk 50 kalibrasi) → pengembangan/kalibrasi panduan. **Tidak dipakai test.**
- Sisanya → test-gold (evaluasi akhir model) + sebagian train-gold (E2/E3), pemisahan dicatat di file split, stratified 3-kelas.
- Weak label LLM **tidak pernah** menjadi dasar gold; jika weak-vs-gold konflik, saat training **gold menang**.

## 6. Rambu etika

Jangan kutip komentar + username bersama-sama di laporan. Labeli tanpa membuka profil penulis. Dugaan SARA/hujatan berat tetap dinilai per aturan §3.1, bukan langsung `-`.
