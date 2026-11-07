#!/usr/bin/env python3
"""Anonimisasi artefak publik (etika §3.9): hash comment_id, buang kolom
video_id/url/channel — pertahankan hanya teks + tanggal (utuh utk analisis
temporal) + label yang sudah digabung.

    python -I scripts/anonymize.py
Output: data/MBG_Arya_anon.csv, data/weak_final_anon.csv, data/gold_700_anon.csv
(catatan mapping id→hash disimpan lokal di data/.hash_map.json — JANGAN
di-commit ke repo publik; dipakai utk join balik saat eksperimen.)
"""
from __future__ import annotations

import csv
import hashlib
import json
import secrets
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MAP_PATH = BASE / "data/.hash_map.json"
MAP_PATH.parent.mkdir(exist_ok=True)

# Salt = rahasia acak, HANYA dari .hash_map.json (file PIBUN, jangan di-commit).
# Dilarang menurunkan salt dari atribut yang terlihat publik (jumlah baris/isi
# file) — hash deterministik dgn salt known ⇒ comment_id asli bisa di-hash balik.
FRESH = not MAP_PATH.exists()
if not FRESH:
    salt = json.loads(MAP_PATH.read_text())["salt"]
else:
    salt = secrets.token_hex(16)


def _public_derivable_salts(n_lines: int, src_bytes: bytes) -> set:
    """Ruang salt lawas: turunan sha256 dari atribut publik (jumlah baris/isi file)."""
    cand = set()
    for k in range(n_lines - 2, n_lines + 9):
        for cut in (8, 16, 64):
            cand.add(hashlib.sha256(str(k)[:cut].encode()).hexdigest()[:16])
            cand.add(hashlib.sha256(str(k).encode()).hexdigest()[:cut])
    for cut in (8, 16, 64):
        cand.add(hashlib.sha256(src_bytes).hexdigest()[:cut])
        cand.add(hashlib.sha256(src_bytes[:cut]).hexdigest()[:16])
        cand.add(hashlib.sha256(str(len(src_bytes)).encode()).hexdigest()[:16])
    return cand


def _assert_salt_not_public(n_lines: int, src_bytes: bytes) -> None:
    """Self-check: salt tidak boleh dapat dihitung ulang dari artefak publik."""
    bad = salt in _public_derivable_salts(n_lines, src_bytes)
    if FRESH:
        assert not bad, "salt bocor: fresh-run salt ternyata derivable dari publik"
        assert len(salt) >= 32, "salt terlalu pendek"
    elif bad:  # salt lawas = bug lama; hentikan tanpa tulis artefak baru
        raise SystemExit(f"[ETIKA §3.9] salt lama ({salt}) derivable dari jumlah "
                         "baris publik ⇒ deanonymizable. Hapus data/.hash_map.json "
                        "lalu jalankan ulang utk rotasi salt acak.")


def h(cid: str) -> str:
    return hashlib.sha256(f"{salt}{cid}".encode()).hexdigest()[:12]


def main() -> None:
    src = BASE / "data/MBG_Arya.csv"
    raw = src.read_bytes()
    _assert_salt_not_public(sum(1 for _ in raw.splitlines()) - 1, raw)
    rows = list(csv.DictReader(open(src, newline="", encoding="utf-8-sig")))
    keep = ["comment_id", "published_at_comment", "like_count", "text_original"]
    with (BASE / "data/MBG_Arya_anon.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(keep)
        for r in rows:
            w.writerow([h(r["comment_id"]), r.get("published_at_comment", ""),
                        r.get("like_count", ""), r.get("text_original", "")])
    print("→ data/MBG_Arya_anon.csv (id hashed, kolom video/channel dibuang)")

    # label files pakai kolom 'id'
    for src, dst in [("data/weak_final.csv", "data/weak_final_anon.csv"),
                     ("data/gold_700.csv", "data/gold_700_anon.csv")]:
        p = BASE / src
        if not p.exists():
            print(f"[skip] {src} belum ada")
            continue
        rs = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
        cols = list(rs[0].keys())
        with (BASE / dst).open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for r in rs:
                w.writerow([h(r["id"]) if c == "id" else r[c] for c in cols])
        print(f"→ {dst}")

    mapping = {r["comment_id"]: h(r["comment_id"]) for r in rows}
    MAP_PATH.write_text(json.dumps({"salt": salt, "map": mapping}))
    print(f"[mapping id→hash] {MAP_PATH} — file PIBUN, jangan di-commit")


if __name__ == "__main__":
    main()
