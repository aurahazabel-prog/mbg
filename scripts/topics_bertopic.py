#!/usr/bin/env python3
"""X6b: BERTopic multilingual + crosstab sentimen (run dari root repo)."""
import csv, collections
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import baseline_sklearn as bs
from bertopic import BERTopic

texts, weak = bs.load_texts(), bs.load_weak(strategy="c")
ids = [i for i in weak if texts.get(i)]
docs = [bs.p1(texts[i]) for i in ids]
model = BERTopic(language="multilingual", min_topic_size=80, verbose=False)
topics, _ = model.fit_transform(docs)
rows = [(t, s, i, texts[i]) for t, s, i in zip(topics, [weak[i] for i in ids], ids)]
with open(Path(__file__).parent.parent / "results/topics_bertopic.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["topic", "sentimen", "id", "text"])
    w.writerows(rows)
ct = collections.Counter((t, s) for t, s, _, _ in rows)
print(f"{'clu':>3} {'neg':>5} {'net':>5} {'pos':>5} {'n':>6}")
for t in sorted(set(r[0] for r in rows)):
    c = {s: ct[(t, s)] for s in ("negatif", "netral", "positif")}
    n = sum(c.values())
    if n >= 60:
        print(f"{t:>3} {c['negatif']:>5} {c['netral']:>5} {c['positif']:>5} {n:>6}")
print("--- topik nama:")
for _, r in model.get_topic_info().iterrows():
    if r.Name == "-1_uncategorized" or r.Count < 70:
        continue
    kw = ", ".join(k for k, _ in model.get_topic(r.Topic)[:6])
    print(f"{r.Topic:>3} n={r.Count:>5} | {kw}")
