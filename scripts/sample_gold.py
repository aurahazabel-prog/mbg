#!/usr/bin/env python3
"""Sampling gold set 700 unit utk anotasi ganda (BLIND: tanpa label LLM).

Strata (kode opaque agar annotator tidak membocorkan weak label):
  S1 positif-ish (W2=positif & sepakat W1)        → 100
  S2 negatif sepakat                               → 220
  S3 netral sepakat                                → 160
  S4 sarkasme ter-flag LLM (subset dari S1/S2/S3)  → 100
  S5 konflik W1≠W2 (pool konflik)                  → 120
Total 700. Sampel acak deterministik (seed 42), tanpa pengulangan antar strata
(S1-S3 saling lepas; S4/S5 menyisihkan yang sudah terpilih dulu).

Output:
  data/gold_700.csv  → id,stratum,text  (untuk Label Studio / Sheets)
  test_data/gold_ids.txt → id per baris (untuk --exclude-ids run W2 ulang Plan B)
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
QUOTA = {"S1": 100, "S2": 220, "S3": 160, "S4": 100, "S5": 120}
SEED = 42


def load(path, label_col):
    out = {}
    with (BASE / path).open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if (r.get("status") or "").startswith("ok"):
                out[r["id"].strip()] = r
    return out


def load_full_texts():
    """Teks penuh dari MBG_Arya.csv — kolom text di weak_labels terpotong 200 char."""
    texts = {}
    with (BASE / "data/MBG_Arya.csv").open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            cid = (r.get("comment_id") or "").strip()
            if cid:
                texts[cid] = (r.get("text_original") or "").strip()
    return texts


def main() -> None:
    w2 = load("data/pilot100_llm.csv", "label_llm")
    w1 = load("data/weak_lex.csv", "label_lex")

    agree = {i: w2[i]["label_llm"] for i in w2 if i in w1 and w1[i]["label_lex"] == w2[i]["label_llm"]}
    conflict = [i for i in w2 if i in w1 and w1[i]["label_lex"] != w2[i]["label_llm"]]
    sark = [i for i in agree if w2[i]["sarkasme_llm"] == "true"]

    rnd = random.Random(SEED)
    pools = {
        "S1": [i for i, l in agree.items() if l == "positif"],
        "S2": [i for i, l in agree.items() if l == "negatif"],
        "S3": [i for i, l in agree.items() if l == "netral"],
        "S4": list(sark),
        "S5": list(conflict),
    }
    chosen: dict[str, str] = {}
    # ambil strata kelas sepakat dulu, lalu sarkasme & konflik (hindari duplikat)
    for key in ("S1", "S2", "S3", "S4", "S5"):
        avail = [i for i in pools[key] if i not in chosen]
        rnd.shuffle(avail)
        take = avail[: QUOTA[key]]
        if len(take) < QUOTA[key]:
            print(f"[warn] {key}: pool hanya {len(take)} < kuota {QUOTA[key]}")
        for i in take:
            chosen[i] = key

    order = sorted(chosen)
    rnd.shuffle(order)  # acak urutan agar strata tidak bocor lewat pengelompokan
    # gold_700.csv = blind utk annotator; mapping strata → file internal terpisah
    # text dari MBG_Arya.csv (penuh) — kolom text weak_labels terpotong 200 char
    full = load_full_texts()
    with (BASE / "data/gold_700.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "text"])
        for i in order:
            w.writerow([i, full.get(i) or w2[i]["text"]])
    with (BASE / "data/gold_strata.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "stratum"])
        for i in order:
            w.writerow([i, chosen[i]])
    (BASE / "test_data/gold_ids.txt").write_text("\n".join(sorted(chosen)) + "\n", encoding="utf-8")
    print(f"[gold] {len(chosen)} unit → data/gold_700.csv | strata: "
          + ", ".join(f"{k}={sum(1 for v in chosen.values() if v==k)}" for k in QUOTA))


if __name__ == "__main__":
    main()
