#!/usr/bin/env python3
"""Split gold_final: ±100 kalibrasi / train-gold / test-gold stratified 3 kelas.
Output: data/gold_split.csv (id, split) + ringkasan konsol.
Seed 42. Kalibrasi TIDAK dipakai test (panduan §5).
"""
import csv, random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
random.seed(42)
rows = {r["id"]: r for r in csv.DictReader(open(ROOT / "data/gold_final.csv", encoding="utf-8-sig"))}
by_lab = defaultdict(list)
for rid, r in rows.items():
    by_lab[r["label_final"]].append(rid)

# sasaran: 100 kalibrasi (~14%), test 35%, train sisanya — stratified per kelas
for lab, ids in by_lab.items():
    random.shuffle(ids)
n_cal = round(0.14 * len(rows))
per_lab = {lab: [round(n_cal * c / len(rows)) for lab, c in [(l, len(i)) for l, i in by_lab.items()]] for l, i in by_lab.items()}

split = {}
CAL, TRAIN, TEST = "kalibrasi", "train_gold", "test_gold"
for lab, ids in by_lab.items():
    n = len(ids)
    ncal = max(1, round(n_cal * n / len(rows)))
    ntest = round(0.35 * n)
    split.update({i: CAL for i in ids[:ncal]})
    split.update({i: TEST for i in ids[ncal:ncal + ntest]})
    split.update({i: TRAIN for i in ids[ncal + ntest:]})

with open(ROOT / "data/gold_split.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "split"])
    for rid in rows:
        w.writerow([rid, split[rid]])

for s in (CAL, TRAIN, TEST):
    cnt = Counter(rows[rid]["label_final"] for rid in rows if split[rid] == s)
    print(s, sum(cnt.values()), dict(cnt))
