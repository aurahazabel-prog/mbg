#!/usr/bin/env python3
"""Pre-label gold_700.csv dengan DUA LLM independen utk protokol assisted
(2026-11-06): manusia mengoreksi, hasil akhir = keputusan manusia.

Model sengaja BUKAN glm-5.3-flash (W2 training) → hindari sirkularitas X5.
Pakai:
    OPENCODE_API_KEY=... .venv/bin/python scripts/prelabel_gold.py \
        --m1 deepseek-v4.1-flash --m2 qwen3.8-flash
Output: data/gold_prelabel.csv → id,text,label_m1,sarkasme_m1,label_m2,sarkasme_m2,sepakat
Resume: jalankan ulang dengan --out sama; baris status ok tidak diulang.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from weak_label_llm import openai_chat  # reuse prompt + parser

BASE = Path(__file__).resolve().parent.parent


def chat_robust(base_url, key, model, text, max_tokens, attempts=2):
    """Satu model, satu panggilan per kali. Kembalikan (label, sarkasme) atau
    (None, 'censored') bila upstream menolak konten (HTTP 400 sensor /
    respons tak valid) — ini BUKAN kegagalan transien, jangan retry buta."""
    last = ""
    for i in range(attempts):
        try:
            lab, sark, _ = openai_chat(base_url, key, model, text, max_tokens)
            if lab:
                return lab, sark
            last = "unparsed"
        except Exception as e:  # noqa
            msg = str(e)
            if "400" in msg or "data_inspection" in msg or "not valid JSON" in msg:
                return None, "censored"
            last = msg[:100]
    return None, f"failed:{last}"


def load_out(out_path):
    if not out_path.exists():
        return {}
    return {r["id"]: dict(r) for r in
            csv.DictReader(open(out_path, newline="", encoding="utf-8-sig"))}


FIELDS = ["id", "text", "label_m1", "sarkasme_m1", "label_m2", "sarkasme_m2",
          "sepakat", "status", "provenance"]


def save_out(out_path, rows_by_id):
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows_by_id.values())


def phase(out_path, rows_by_id, todo_rows, model, key, args, cell):
    """Isi satu sel label utk semua baris yang belum punya — satu model per fase."""
    lab_col, sark_col = ("label_m1", "sarkasme_m1") if cell == 1 else ("label_m2", "sarkasme_m2")
    lock = threading.Lock()
    done = {"ok": 0, "censored": 0, "failed": 0}

    def work(r):
        if rows_by_id[r["id"]][lab_col]:
            return
        lab, sark = chat_robust(args.base_url, key, model, r["text"], args.max_tokens)
        with lock:
            rows_by_id[r["id"]][lab_col] = lab or ""
            rows_by_id[r["id"]][sark_col] = sark if lab else str(sark)
            done["censored" if sark == "censored" else ("ok" if lab else "failed")] += 1
            n = done["ok"] + done["censored"] + done["failed"]
            if n % 50 == 0:
                print(f"[{model}] {n}/{len(todo_rows)} {done}", flush=True)

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        list(ex.map(work, todo_rows))
    for rid in rows_by_id:
        r = rows_by_id[rid]
        if r["label_m1"] and r["label_m2"]:
            r["sepakat"] = "ya" if r["label_m1"] == r["label_m2"] else "tidak"
            r["status"] = "ok"
        else:
            r["sepakat"] = ""
            r["status"] = ("censored" if "censored" in (r["sarkasme_m1"], r["sarkasme_m2"])
                           else r.get("status") or "pending")
        r["provenance"] = f"{args.m1}+{args.m2}"
    save_out(out_path, rows_by_id)
    print(f"[{model}] fase selesai {done}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--m1", default="deepseek-v4.1-flash")
    ap.add_argument("--m2", default="qwen3.8-flash")
    ap.add_argument("--base-url", default="https://opencode.ai/inference/openai/v1")
    ap.add_argument("--out", default=str(BASE / "data/gold_prelabel.csv"))
    ap.add_argument("--in", dest="inp", default=str(BASE / "data/gold_700.csv"))
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=400)
    ap.add_argument("--redo-censored", action="store_true",
                    help="reset sel yang terblokir sensor lalu ulangi (default: biarkan)")
    args = ap.parse_args()

    key = os.environ.get("OPENCODE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("Set OPENCODE_API_KEY dulu")

    rows = list(csv.DictReader(open(args.inp, newline="", encoding="utf-8-sig")))
    out_path = Path(args.out)
    rows_by_id = load_out(out_path)
    for r in rows:  # tambah baru / sinkron teks
        rows_by_id.setdefault(r["id"], {**{c: "" for c in FIELDS}, "id": r["id"], "text": r["text"]})
    if args.redo_censored:
        for r in rows_by_id.values():
            if r["sarkasme_m1"] == "censored":
                r["sarkasme_m1"] = ""
            if r["sarkasme_m2"] == "censored":
                r["sarkasme_m2"] = ""
    todo = [r for r in rows if r["id"] in rows_by_id]
    print(f"[pre-label] {len(todo)} unit | fase berurutan: {args.m1} → {args.m2}")
    phase(out_path, rows_by_id, todo, args.m1, key, args, cell=1)
    phase(out_path, rows_by_id, todo, args.m2, key, args, cell=2)
    ok = sum(1 for r in rows_by_id.values() if r["status"] == "ok")
    cen = sum(1 for r in rows_by_id.values() if r["status"] == "censored")
    agree = sum(1 for r in rows_by_id.values() if r["sepakat"] == "ya")
    print(f"SELESAI. lengkap={ok} sensor={cen} agreement={agree}/{max(ok,1)} "
          f"({agree/max(ok,1):.0%}) → {out_path}")
    print("Sel sensor otomatis masuk keranjang BUTA saat gold_kit.py dijalankan.")


if __name__ == "__main__":
    main()
