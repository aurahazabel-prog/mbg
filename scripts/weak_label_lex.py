#!/usr/bin/env python3
"""Weak labeling W1 — skor leksikon sentimen Indonesia (stdlib-only).

Leksikon tertanam (seed list, disitasi & bisa diperluas ke InSet/lexicon
publik — lihat catatan di akhir file). Aturan: hitung skor = pos - neg per
komentar; negasi ("tidak/bukan/gak/...") dalam 2 token sebelum kata membalik
polaritasnya. Frasa multi-kata (mis. "luar biasa", "tak berguna") dicocokkan
sebagai bigram/trigram lewat scan token; entri frasa tidak dipecah ke unigram.
Bare negator tidak diberi skor. Threshold: >=1 positif, <=-1 negatif,
selainnya netral.

Pakai:
    python -I scripts/weak_label_lex.py data/MBG_Arya.csv --out data/weak_lex.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

POS = """senang bagus baik hebat mantap top setuju dukung dukungan
syukur alhamdulillah apresiasi bermanfaat manfaat
bergizi sehat layak puas lancar sempurna ideal cerdas jujur peduli
santun ramah gratis murah membantu terbantu salut bangga optimis aman nyaman
enak lezat nikmat maju sejahtera sukses keren oke ok sip asik serasi adil
profesional transparan responsif sigap perhatian sayang semangat positif"""

NEG = """jelek buruk busuk sampah kacau gagal kecewa marah bodoh tolol bego
hancur mubazir boros maling koruptor korupsi pencuri pencitraan janji
dusta bohong omong omdo palsu munafik zalim aniaya tumpul lamban lemot
lama percuma fatal bahaya beracun keracunan
racun kotor jijik menjijikkan ngeri menyeramkan takut cemas gelisah
sedih pilu nangis parah rusak curang culas suap sogok preman
premanisme arogan sewenangwenang otoriter diktator rejim rezim bobrok
rusuh onar anarkis bubar bubarkan hentikan stop muntah
muak eneg sebal
kesal dongkol benci membenci menolak kritik cela cemooh sinis
sarkas nista najis hina penghinaan fitnah hoaks"""

# Frasa multi-kata: cocok sebagai bigram/trigram token, bukan unigram.
PHRASES = {
    "luar biasa": 1,
    "terima kasih": 1,
    "alhamdulillah": 1,
    "tak berguna": -1,
    "tidak berguna": -1,
    "sia sia": -1,
    "tidak layak": -1,
}

NEGATORS = {"tidak", "bukan", "gak", "gk", "nggak", "engga", "tak",
            "tdk", "bkn", "belum", "jangan", "tanpa", "anti", "no"}

TOKEN = re.compile(r"[a-z0-9]+")
POSSET, NEGSET = set(POS.split()), set(NEG.split())


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    tc = next((c for c in fieldnames if c.lower() in ("text_original", "text")), None)
    if not tc:
        sys.exit("Kolom text_original tidak ditemukan")
    return rows, tc


def score(text: str) -> int:
    toks = TOKEN.findall(text.lower())
    s = 0
    i, n = 0, len(toks)
    while i < n:
        matched = 0
        for k in (3, 2):  # frasa terpanjang dulu
            if i + k <= n and (pol := PHRASES.get(" ".join(toks[i:i + k]))) is not None:
                s += pol
                matched = k
                break
        if matched:
            i += matched
            continue
        t = toks[i]
        i += 1
        if t in NEGATORS:
            continue  # bare negator tidak menyumbang skor
        w = sum(t in NEGATORS for t in toks[max(0, i - 3):i - 1])
        if t in POSSET:
            s += -1 if w else 1
        elif t in NEGSET:
            s += 1 if w else -1
    return s


def label(text: str) -> str:
    sc = score(text)
    return "positif" if sc >= 1 else "negatif" if sc <= -1 else "netral"


def _selfcheck() -> None:
    assert label("jangan") == "netral"
    assert label("saya tidak") == "netral"
    assert label("tidak ada") == "netral"
    assert label("anti") == "netral"
    assert label("tak") == "netral"
    assert label("makanannya enak sekali") == "positif"
    assert label("makanannya tidak enak") == "negatif"
    assert label("pelayanannya luar biasa") == "positif"
    assert label("terima kasih atas layanannya") == "positif"
    assert label("alhamdulillah") == "positif"
    assert label("biasa saja") == "netral"
    assert label("makanannya sia-sia dibuang") == "negatif"  # via frasa 'sia sia', bukan 'sia' umum
    assert label("tak berguna") == "negatif"  # frasa bigram
    assert label("sangat tidak berguna") == "negatif"  # frasa bigram
    assert label("produk ini tidak layak") == "negatif"  # frasa bigram, negator di dalamnya tidak menegasi diri sendiri
    assert label("busuk") == "negatif"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--out", default="data/weak_lex.csv")
    args = ap.parse_args()

    rows, tcol = load_rows(Path(args.csv_path))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_lab = {"positif": 0, "netral": 0, "negatif": 0}
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "text", "label_lex", "score_lex", "status", "provenance"])
        for i, r in enumerate(rows):
            t = (r.get(tcol) or "").strip()
            rid = (r.get("comment_id") or str(i)).strip()
            lab = label(t)
            n_lab[lab] += 1
            w.writerow([rid, t[:200], lab, score(t), "ok", "lexicon-seed-v1"])
    print(f"[W1] {len(rows)} baris → {out_path}")
    print(f"[sebaran] {n_lab}  (lexicon-only; netral = tidak ada kata leksikon)")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selfcheck":
        _selfcheck()
        print("selfcheck ok")
    else:
        _selfcheck()
        main()

# Upgrade path: ganti POS/NEG dengan leksikon InSet/IndoClass atau
# SenticNet-id bila tersedia; format output tetap sama.
