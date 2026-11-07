#!/usr/bin/env python3
"""Konsensus W1 (leksikon) ∧ W2 (LLM) → weak_final untuk training.

Kolom weak_final mengikuti aturan Tahap 3: sepakat = label itu; konflik =
'unlabeled'. Keputusan K5 (Rencana_Tindak_Lanjut #14/#42) untuk SET LATIH:
  - strategi 'a': hanya baris sepakat (konflik benar-benar tidak ikut latih)
  - strategi 'c' (default): konflik diisi label_w2 → BUKAN tanpa label.
    Loader baseline_sklearn.load_weak / train_indobert.load_weak yang
    menerapkan ini; skrip ini HANYA pencatat, tidak mengubah kolom.
Proporsi kelas label_w2 di pool konflik dicetak di bawah dan WAJIB dilaporkan
di Bab IV (bias ke negatif; ablasi 'a' vs 'c'). Gold S5 (konflik) = subset
audit kecil, BUKAN held-out khusus konflik; gold di-exclude dari latih di
kedua strategi, sehingga akurasi kelas konflik tertimbang rendah ikut
terlihat di metrik gold overall.
Agreement rate W1–W2 = estimasi awal noise (X5 resmi pakai gold set).

Pakai:
    python -I scripts/consensus.py data/weak_lex.csv data/pilot100_llm.csv \
        --out data/weak_final.csv
"""
from __future__ import annotations

import argparse
import csv
import collections
from pathlib import Path


def load(path: Path, label_col: str) -> dict[str, str]:
    out: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            if (r.get("status") or "").startswith("ok"):
                out[r["id"].strip()] = r[label_col].strip()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("w1")
    ap.add_argument("w2")
    ap.add_argument("--out", default="data/weak_final.csv")
    args = ap.parse_args()

    w1 = load(Path(args.w1), "label_lex")
    w2 = load(Path(args.w2), "label_llm")
    ids = sorted(set(w1) | set(w2))
    agree = sum(1 for i in ids if i in w1 and i in w2 and w1[i] == w2[i])
    both = sum(1 for i in ids if i in w1 and i in w2)

    dist = collections.Counter()
    conf_w2 = collections.Counter()  # label_w2 pada baris konflik (dipakai strategi 'c')
    with Path(args.out).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "label_w1", "label_w2", "weak_final"])
        for i in ids:
            a, b = w1.get(i, ""), w2.get(i, "")
            final = a if (a and a == b) else "unlabeled"
            dist[final] += 1
            if final == "unlabeled" and b:
                conf_w2[b] += 1
            w.writerow([i, a, b, final])

    print(f"[konsensus] W1={len(w1)} W2={len(w2)} berpasangan={both}")
    print(f"[agreement W1-W2] {agree}/{both} = {agree / both:.1%}  (estimasi awal noise; X5 resmi pakai gold set)")
    print(f"[weak_final] {dict(dist)}")
    n_conf = sum(conf_w2.values())
    if n_conf:
        share = {k: f"{v / n_conf:.1%}" for k, v in sorted(conf_w2.items())}
        print(f"[strategi-c] konflik ikut latih via W2: n={n_conf} dist={dict(sorted(conf_w2.items()))} proporsi={share}")
        print("[strategi-c] laporkan angka ini di Bab IV; bandingkan ablasi --strategy a (hanya sepakat).")


if __name__ == "__main__":
    main()
