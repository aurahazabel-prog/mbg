# Hasil Profil Dataset — MBG_Arya.csv

- Jumlah baris: **10000**
- Jumlah kolom: **14**  → `['comment_id', 'video_id', 'video_title', 'channel_title', 'published_at_video', 'published_at_comment', 'updated_at_comment', 'like_count', 'text_original', 'keyword', 'source', 'video_url', 'crawled_at', 'is_indonesian']`

## 1. Kelengkapan per kolom
- `comment_id`: kosong/NaN **0** (0.0%), unik **10000**
- `video_id`: kosong/NaN **0** (0.0%), unik **13**
- `video_title`: kosong/NaN **0** (0.0%), unik **13**
- `channel_title`: kosong/NaN **0** (0.0%), unik **13**
- `published_at_video`: kosong/NaN **0** (0.0%), unik **13**
- `published_at_comment`: kosong/NaN **0** (0.0%), unik **9982**
- `updated_at_comment`: kosong/NaN **0** (0.0%), unik **9983**
- `like_count`: kosong/NaN **0** (0.0%), unik **193**
- `text_original`: kosong/NaN **0** (0.0%), unik **10000**
- `keyword`: kosong/NaN **0** (0.0%), unik **1**
- `source`: kosong/NaN **0** (0.0%), unik **1**
- `video_url`: kosong/NaN **0** (0.0%), unik **13**
- `crawled_at`: kosong/NaN **0** (0.0%), unik **54**
- `is_indonesian`: kosong/NaN **0** (0.0%), unik **1**

## 2. Peran kolom (tebak otomatis — verifikasi manual!)
- Kandidat kolom teks : `['text_original']`
- Kandidat kolom waktu: `['published_at_video', 'published_at_comment', 'updated_at_comment']`
- Kandidat kolom ID   : `['comment_id', 'video_id', 'video_title', 'channel_title', 'published_at_video', 'video_url']`
- Kandidat kolom label: `— (konfirmasi: dataset TIDAK berlabel)`

## 3. Duplikat teks komentar: **0** baris (0.0%)

## 4. Statistik panjang komentar
- Karakter: min 1, median 74, mean 112.7, p95 339, max 2798
- Kata: median 12, mean 17.5, max 362
- Komentar < 5 karakter (noise/spam): **82** (0.8%)

## 5. Sinyal pra-pemrosesan
- Mengandung URL: 11 | Emoji: 2068 | ALL-CAPS(>15): 377

## 6. 40 kata terbanyak (sanity check: harusnya didominasi bahasa Indonesia)
  mbg(4414), dan(2567), ini(1905), yang(1877), ada(1650), itu(1601), anak(1546), nya(1400), makan(1357), program(1284), tidak(1195), rakyat(1103), orang(1035), dari(1013), aja(1006), untuk(988), sekolah(927), makanan(922), gratis(912), bisa(885), lebih(804), banyak(800), jadi(799), korupsi(777), gak(755), keracunan(690), saja(686), saya(683), tapi(671), uang(667), mau(600), buat(599), kalau(593), negara(585), sudah(574), juga(567), harus(548), baik(544), bukan(535), apa(524)

## 7. Contoh komentar (potong 160 karakter)
- [0] 'Bang  kumis memiliki karakter salesman yg kuat. Ciri khasnya selalu mengulang2  keunggulan produk yg dijual meski  terbukti gagal dng terus menanamkan ke dlm pi'
- [833] 'Manfaat apa istri gua aja dapet utk ibu menyusui malah ga pernah di makan karna ga enak'
- [1666] 'Bahlil juga harus di tahan..'
- [2499] 'Dari sampai kini si ngabalin ,makin nyebelin ,dasar penjilat'
- [3332] '😢😢😢🥺😔😞'
- [4165] 'TEMPO TOP MARKOTOP GAS TERUS SAYA SUKA HASIL INVESTIGASINYA'
- [4998] 'Bukanprogam mbgproyekmbg buatkakitangan praboworayat dipakealat yangmakanduit mbgmanusiaprabowobejabatnya'
- [5831] 'Upah kerja di sesuaikan dengan UMR ini yg jadi polemik tolong upah nya di sesuaikan'
- [6664] 'Saya setuju MBG, klo memang SANGAT bergizi dan utk anak kurang mampu'
- [7497] 'Harus begini kepala daerah'
- [8330] 'BUBARKAN AJA'
- [9163] 'Program yg terlalu dipaksakan...demi janji kampaye asal jd presiden'