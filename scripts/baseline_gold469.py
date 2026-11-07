#!/usr/bin/env python3
"""Baseline LR pada test-gold 469 (split sama dgn Kaggle run: seed 42, 67% test) — align dgn IndoBERT."""
from collections import Counter
import csv, json
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import sys
sys.path.insert(0, str(Path(__file__).parent))
from baseline_sklearn import LABELS, load_texts, load_weak, p2

texts, weak = load_texts(), load_weak(strategy="c")
gold = {r["id"]: r["label_final"] for r in csv.DictReader(open("data/gold_final.csv", encoding="utf-8-sig")) if r["label_final"] in LABELS}
test_ids = open("test_data/test_gold_ids_469.txt").read().split()

X = [p2(texts[i]) for i in weak if texts.get(i)]
y = [weak[i] for i in weak if texts.get(i)]
Xt = [p2(texts[i]) for i in test_ids]
yt = [gold[i] for i in test_ids]

out = {}
for name, clf in {"nb": None, "svm": None, "lr": None}.items():
    import importlib, baseline_sklearn as bs
    pipe = bs.make_pipe(name)
    pipe.fit(X, y)
    pred = pipe.predict(Xt)
    out[name] = {"macro_f1": round(f1_score(yt, pred, average="macro", labels=sorted(LABELS)), 4),
                 "accuracy": round(accuracy_score(yt, pred), 4),
                 "per_class_f1": {l: round(f1_score(yt, pred, labels=[l], average=None, zero_division=0)[0], 4) for l in sorted(LABELS)},
                 "confusion": confusion_matrix(yt, pred, labels=sorted(LABELS)).tolist()}
    print(name, out[name]["macro_f1"])

Path("results/baseline_p2_c_gold469.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
