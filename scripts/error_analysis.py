#!/usr/bin/env python3
"""Error analysis: prediksi LR pada test-gold, ekspor kasus salah + kategorisasi otomatis awal.
Output: data/error_lr_p2_c.csv + ringkasan kategori konsol.
"""
import csv, json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

import sys
sys.path.insert(0, str(Path(__file__).parent))
from baseline_sklearn import LABELS, load_texts, load_weak, gold_labels, p2

ROOT = Path(__file__).parent.parent
SPLIT = {r["id"]: r["split"] for r in csv.DictReader(open(ROOT / "data/gold_split.csv", encoding="utf-8-sig"))}
texts, weak, gold = load_texts(), load_weak(strategy="c"), gold_labels("data/gold_final.csv")
test_ids = [i for i in gold if SPLIT.get(i) == "test_gold" and texts.get(i)]

X = [p2(texts[i]) for i in weak if texts.get(i)]
y = [weak[i] for i in weak if texts.get(i)]
pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=3)),
                 ("clf", LogisticRegression(max_iter=2000, class_weight="balanced"))])
pipe.fit(X, y)
Xt = [p2(texts[i]) for i in test_ids]

preds = pipe.predict(Xt)
rows = [{"id": i, "text": texts[i], "gold": gold[i], "pred_lr": p,
         "error": "" if gold[i] == p else "ya"}
        for i, p in zip(test_ids, preds)]

errs = [r for r in rows if r["error"]]
# kategorisasi otomatis kasar → bantu diskusi manusia
RULES = {"sarkasme": ["hebat", "mantap", "bagus banget", "keren", "semoga"],
         "slang/daerah": ["kang", "bos", "gemoy", "kyk", "gak", "ga ", "aja", "nih", "banget"],
         "ambigu/objek-tak-eksplisit": ["mereka", "wong", "orang", "dia", "itu"],
         "selisih-politik": ["prabowo", "jhoko", "jokowi", "pemerintah", "pejabat", "presiden"],
         "emoji-only/hampir": []}
for r in errs:
    t = r["text"].lower()
    r["kategori_otom"] = next((k for k, w in RULES.items() if any(x in t for x in w)) or "lainnya", "lainnya")

with open(ROOT / "data/error_lr_p2_c.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "text", "gold", "pred_lr", "error", "kategori_otom"])
    w.writeheader()
    w.writerows(rows)

print(f"test-gold: {len(test_ids)} | salah: {len(errs)} ({len(errs)/len(test_ids):.1%})")
print("arah salah (gold→pred):", dict(Counter(f'{r["gold"]}→{r["pred_lr"]}' for r in errs)))
print("kategori otomatis:", dict(Counter(r["kategori_otom"] for r in errs)))
# contoh 10 utk diskusi
for r in sorted(errs, key=lambda r: r["kategori_otom"])[:10]:
    print(f'  [{r["kategori_otom"]}] {r["gold"]}→{r["pred_lr"]} | {r["text"][:70]}')
