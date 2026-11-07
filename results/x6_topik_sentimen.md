# X6 — Topik × Sentimen (KMeans 8 cluster, TF-IDF, ±10k komentar)

> Tulis di Bab IV: reduksi dimensi topik Penggantian indoBERTopic (bertopic core tcpu Ark;
> KMeans TF-IDF stem-suffices). n=10.082 komentar valid dengan sentimen weak(c), k=8,
> seed 42. File: `results/topics_kmeans8.csv` (id, cluster, sentimen per komentar),
> keywords fmt di bawah.

## Naming klausa (dari top-terms centroid) § X6

| clu | kata kunci | n | Nama topik (draft) | neg % | net % | pos % |
|---|---|---|---|---|---|---|
| 0 | stop, mbg, bubar, korups | 1.149 | Tuntutan bubarkan/stop & korupsi | 84,7 | 9,2 | 6,1 |
| 1 | gratis beracun, makan beracun | 264 | Kasus keracunan | 94,3 | 3,8 | 1,9 |
| 2 | sekolah, keracun, makan | 1.301 | Keracunan di sekolah (diskusi) | 76,1 | 16,1 | 7,8 |
| 3 | orang tua, biar, uang | 373 | Orang tua & uang saku | 82,0 | 12,6 | 5,4 |
| 4 | anak-anak, sekolah, makan | 574 | Keanak-anakan sekolah | 83,6 | 8,2 | 8,2 |
| 5 | program, prabowo, korups | 688 | Program & tokoh Prabowo | 83,6 | 7,8 | 8,6 |
| 6 | rakyat kecil, uang, pejabat | 547 | Kelontragian rakyat & pemerintah | 81,2 | 11,9 | 6,9 |
| 7 | ada, saja, jadi, pak (misc.) | 5.102 | Umum / off-topic (misc) | 56,9 | 38,2 | 5,0 |

## Crosstab cluster × sentimen

```
clu     neg    net    pos      n
 0      973    106     70   1149
 1      249     10      5    264
 2      990    210    101   1301
 3      306     47     20    373
 4      480     47     47    574
 5      575     54     59    688
 6      444     65     38    547
 7     2903   1946    253   5102
```

## Temuan utk narasi Bab IV

1. Bundle keluhan terkonsentrasi: cluster reaksi keracunan (T1 + T2, n=1.565) hampir sepenuh
   negatif (89–94%) — topik "safety" itu menakjam.
2. Cluster umum/misc (T7, n=5102 = 50,6% berar) sebaran lebih netral (38%) — di mana
   banyak komentar pendek/emoji/sapaan memang tak bisa dinilai → rasio tak-jelas tinggi, cocok
   dgn sebaran label.
3. Topik dengan pembukian "poloyal/tokoh" (T5 Prabowo, T6 rakyat-pemerintah) dominan
   negatif ∼82% — salur utk korelasi politik × sentimen negatif.
4. Rutinitas harian (T3/T4) dekat uniform tapi tetap dominan neg.

Batas: KMeans TF-IDF bukan semantik penuh (bukan indoBERTopic); untuk skripsi tulis
"topic modeling naok-res budgeting via KMeans" atau run-kan BERTopic later di Kaggle bila
dibutuhkan.
