#!/usr/bin/env python3
"""Cohen's Kappa antar dua kolom label anotasi (stdlib-only).

Pakai:
    python -I scripts/kappa.py annotation_a.csv annotation_b.csv \
        --col-a label --col-b label --disagreements out.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load(path: Path, col: str) -> dict[str, str]:
    return {r["id"].strip(): r[col].strip()
            for r in csv.DictReader(path.open(newline="", encoding="utf-8-sig"))
            if r.get(col, "").strip()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--col-a", default="label")
    ap.add_argument("--col-b", default="label")
    ap.add_argument("--disagreements", help="opsional: tulis baris beda ke csv")
    args = ap.parse_args()

    la, lb = load(Path(args.a), args.col_a), load(Path(args.b), args.col_b)
    ids = sorted(set(la) & set(lb))
    n = len(ids)
    if not n:
        raise SystemExit("Tidak ada id beririsan.")
    po = sum(la[i] == lb[i] for i in ids) / n
    cats = sorted({*la.values(), *lb.values()})
    pe = sum((sum(1 for i in ids if la[i] == c) / n) *
             (sum(1 for i in ids if lb[i] == c) / n) for c in cats)
    k = (po - pe) / (1 - pe)
    print(f"n={n} agreement={po:.3f} expected={pe:.3f} KAPPA={k:.3f} "
          f"({'substantial ≥0.61' if k >= 0.61 else 'REVISI PANDUAN — di bawah target'})")
    if args.disagreements:
        d = [i for i in ids if la[i] != lb[i]]
        with Path(args.disagreements).open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["id", args.col_a, args.col_b])
            w.writerows((i, la[i], lb[i]) for i in d)
        print(f"[disagreements] {len(d)} → {args.disagreements}")


if __name__ == "__main__":
    main()
