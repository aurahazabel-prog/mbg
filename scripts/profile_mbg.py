#!/usr/bin/env python3
"""Profil cepat MBG_Arya.csv sebelum skripsi menetapkan desain.

Pakai (dari folder proyek):
    python -I scripts/profile_mbg.py MBG_Arya.csv

Tanpa dependensi eksternal (hanya stdlib) — aman untuk data unduhan.
Menghasilkan ringkasan ke stdout + file `hasil_profil.md`.
"""
from __future__ import annotations

import csv
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

TEXT_HINTS = ("comment", "text", "isi", "komentar", "body", "content")
TIME_HINTS = ("date", "time", "waktu", "tanggal", "published", "created", "timestamp")
ID_HINTS = ("id", "url", "link", "video", "channel", "user", "author", "nama")
LABEL_HINTS = ("label", "sentiment", "sentimen", "klass", "kelas", "polarity", "sent")
MAX_REPORT_ROWS = 12


def sniff_dialect(path: Path):
    sample = path.read_text(encoding="utf-8", errors="replace")[:64_000]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel  # default koma


def main(csv_path: str) -> None:
    path = Path(csv_path)
    if not path.exists():
        sys.exit(f"File tidak ditemukan: {path}")

    dialect = sniff_dialect(path)
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh, dialect=dialect)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    n = len(rows)
    lines: list[str] = []
    w = lines.append
    w(f"# Hasil Profil Dataset — {path.name}\n")
    w(f"- Jumlah baris: **{n}**")
    w(f"- Jumlah kolom: **{len(fieldnames)}**  → `{fieldnames}`\n")

    # 1. Kelengkapan & tipe-ish per kolom
    w("## 1. Kelengkapan per kolom")
    for col in fieldnames:
        vals = [r.get(col) for r in rows]
        empty = sum(1 for v in vals if v is None or str(v).strip() == "")
        uniq = len({str(v).strip() for v in vals})
        w(f"- `{col}`: kosong/NaN **{empty}** ({empty / n:.1%}), unik **{uniq}**")

    # 2. Tebak peran kolom
    def cols_with(hints):
        return [c for c in fieldnames if any(h in c.lower() for h in hints)]

    text_cols = cols_with(TEXT_HINTS) or ([fieldnames[0]] if fieldnames else [])
    time_cols = cols_with(TIME_HINTS)
    id_cols = cols_with(ID_HINTS)
    label_cols = cols_with(LABEL_HINTS)
    w("\n## 2. Peran kolom (tebak otomatis — verifikasi manual!)")
    w(f"- Kandidat kolom teks : `{text_cols}`")
    w(f"- Kandidat kolom waktu: `{time_cols or '— (TIDAK ADA → riset temporal dibatalkan)'}`")
    w(f"- Kandidat kolom ID   : `{id_cols}`")
    w(f"- Kandidat kolom label: `{label_cols or '— (konfirmasi: dataset TIDAK berlabel)'}`")

    # 3. Duplikat
    tc = text_cols[0] if text_cols else None
    if tc:
        texts = [str(r.get(tc) or "").strip() for r in rows]
        dup = len(texts) - len(set(texts))
        w(f"\n## 3. Duplikat teks komentar: **{dup}** baris ({dup / n:.1%})")

        # 4. Statistik panjang
        lengths = [len(t) for t in texts if t]
        words = [len(t.split()) for t in texts if t]
        if lengths:
            w("\n## 4. Statistik panjang komentar")
            w(f"- Karakter: min {min(lengths)}, median {statistics.median(lengths):.0f}, "
              f"mean {statistics.fmean(lengths):.1f}, p95 {sorted(lengths)[int(0.95*len(lengths))]}, max {max(lengths)}")
            w(f"- Kata: median {statistics.median(words):.0f}, mean {statistics.fmean(words):.1f}, max {max(words)}")
            very_short = sum(1 for t in texts if len(t) < 5)
            w(f"- Komentar < 5 karakter (noise/spam): **{very_short}** ({very_short / n:.1%})")

        # 5. Sinyal kebisingan
        url_ct = sum(1 for t in texts if re.search(r"https?://|www\.", t, re.I))
        emoji_ct = sum(1 for t in texts if re.search("[\U0001F300-\U0001FAFF☀-➿]", t))
        caps_ct = sum(1 for t in texts if len(t) > 15 and t == t.upper())
        w("\n## 5. Sinyal pra-pemrosesan")
        w(f"- Mengandung URL: {url_ct} | Emoji: {emoji_ct} | ALL-CAPS(>15): {caps_ct}")

        # 6. Kata paling sering (sanity-check bahasa & topik)
        toks = re.findall(r"[a-z]{3,}", " ".join(texts).lower())
        top = Counter(toks).most_common(40)
        w("\n## 6. 40 kata terbanyak (sanity check: harusnya didominasi bahasa Indonesia)")
        w("  " + ", ".join(f"{t}({c})" for t, c in top))

        # 7. Contoh acak untuk dibaca manual
        w("\n## 7. Contoh komentar (potong 160 karakter)")
        step = max(1, n // MAX_REPORT_ROWS)
        for i in range(0, min(n, step * MAX_REPORT_ROWS), step):
            w(f"- [{i}] {texts[i][:160]!r}")

    out = Path("hasil_profil.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n[disimpan ke {out.resolve()}]")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "MBG_Arya.csv"
    main(target)
