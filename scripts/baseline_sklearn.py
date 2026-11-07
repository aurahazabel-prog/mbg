#!/usr/bin/env python3
"""Baseline klasik (X4/X1-baseline): NB, Linear SVM, Logistic Regression + TF-IDF.

Latih pada weak labels; evaluasi pada gold set manusia bila tersedia
(--gold gold_final.csv; kolom id,label_final). Tanpa --gold → smoke test
internal (split acak weak) utk validasi pipeline SAJA — angka ini TIDAK
boleh dilaporkan di skripsi.

    .venv/bin/python scripts/baseline_sklearn.py --preproc p2 --gold none
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from preprocess import p1, p2

LABELS = ["negatif", "netral", "positif"]


def load_texts():
    rows = list(csv.DictReader(open("data/MBG_Arya.csv", newline="", encoding="utf-8-sig")))
    return {r["comment_id"].strip(): (r.get("text_original") or "").strip() for r in rows}


def load_weak(path="data/weak_final.csv", strategy="c"):
    """strategy c: sepakat → label; konflik → pakai W2 (LLM)."""
    out = {}
    for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
        f = r["weak_final"]
        if f in LABELS:
            out[r["id"]] = f
        elif strategy == "c" and r["label_w2"] in LABELS:
            out[r["id"]] = r["label_w2"]
    return out


def gold_labels(path):
    out = {}
    for r in csv.DictReader(open(path, newline="", encoding="utf-8-sig")):
        lab = (r.get("label_final") or r.get("label") or "").strip().lower()
        if lab in LABELS:
            out[r["id"].strip()] = lab
    return out


def make_pipe(name):
    clf = {"nb": MultinomialNB(), "svm": LinearSVC(class_weight="balanced"),
           "lr": LogisticRegression(max_iter=2000, class_weight="balanced")}[name]
    return Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True,
                                               min_df=3)),
                     ("clf", clf)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preproc", choices=["p1", "p2"], default="p2")
    ap.add_argument("--gold", default="none", help="gold_final.csv atau 'none'")
    ap.add_argument("--strategy", choices=["a", "c"], default="c")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    texts = load_texts()
    pre = p1 if args.preproc == "p1" else p2
    weak = load_weak(strategy=args.strategy)
    gold = gold_labels(args.gold) if args.gold != "none" else {}
    # gold TIDAK ikut latih (evaluasi murni manusia); gold menang atas weak
    have = [i for i in weak if texts.get(i) and i not in gold]
    X = [pre(texts[i]) for i in have]
    y = [weak[i] for i in have]
    print(f"[latih] {len(have)} weak ({args.strategy}, {args.preproc}) | {dict(Counter(y))}")

    if gold:
        gids = [i for i in gold if texts.get(i)]
        Xt = [pre(texts[i]) for i in gids]
        yt = [gold[i] for i in gids]
        print(f"[test] {len(gids)} gold-set")
    else:
        X, Xt, y, yt = train_test_split(X, y, test_size=0.25, stratify=y, random_state=args.seed)
        print("!! TIDAK ADA GOLD — smoke test weak-vs-weak, JANGAN dilaporkan")

    results = {}
    for name in ("nb", "svm", "lr"):
        pipe = make_pipe(name)
        pipe.fit(X, y)
        pred = pipe.predict(Xt)
        mf1 = f1_score(yt, pred, average="macro", labels=LABELS)
        acc = accuracy_score(yt, pred)
        results[name] = {"macro_f1": round(mf1, 4), "accuracy": round(acc, 4),
                         "per_class_f1": {l: round(f1_score(yt, pred, labels=[l], average=None, zero_division=0)[0], 4) for l in LABELS},
                         "confusion": confusion_matrix(yt, pred, labels=LABELS).tolist()}
        print(f"[{name}] macro-F1={mf1:.3f} acc={acc:.3f} " +
              " ".join(f"{l}:{results[name]['per_class_f1'][l]:.2f}" for l in LABELS))

    out = Path(f"results/baseline_{args.preproc}_{args.strategy}{'_gold' if gold else '_smoke'}.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print("→", out)


if __name__ == "__main__":
    main()
