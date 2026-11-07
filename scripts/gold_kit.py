#!/usr/bin/env python3
"""Buat file kerja anotasi protokol assisted+blind (panduan v2.1).
Pra-label SATU model: deepseek (label_m1) — qwen di-drop (sensor upstream).
Sinyal "cek cermat" = label deepseek ≠ label W2/GLM (sudah ada di data, nol API).
  data/gold_blind150.csv   → id,text (BUTA; strata S1/S2/S4/S5 + unit tanpa pra-label)
  data/gold_assisted550.csv → id,text,cek_cermat,label_pre (pra-label PALING KANAN)
  template_annotation.csv  → kolom kosong utk annotator A dan B

    .venv/bin/python scripts/gold_kit.py
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEED = 7


def main() -> None:
    strata = {r["id"]: r["stratum"] for r in
              csv.DictReader(open(BASE / "data/gold_strata.csv", newline="", encoding="utf-8"))}
    pre = [r for r in csv.DictReader(open(BASE / "data/gold_prelabel.csv", newline="", encoding="utf-8-sig"))
           if r["id"] in strata]  # buang baris sisa sampling gold lama
    # label W2/GLM utk sinyal cek_cermat (deepseek vs GLM beda → nilai teliti)
    glm = {r["id"]: r["label_llm"] for r in
           csv.DictReader(open(BASE / "data/pilot100_llm.csv", newline="", encoding="utf-8"))
           if r["id"] in strata and (r.get("status") or "").startswith("ok")}
    for p in pre:
        p["cek_cermat"] = "ya" if (p["label_m1"] and glm.get(p["id"])
                                   and p["label_m1"] != glm[p["id"]]) else "tidak"
    rnd = random.Random(SEED)
    pools = {k: [p for p in pre if strata[p["id"]] == k] for k in ("S1", "S2", "S4", "S5")}
    quota = {"S1": 40, "S2": 50, "S4": 30, "S5": 30}
    blind_ids: list[str] = []
    for k, q in quota.items():
        avail = pools[k]
        take = q if len(avail) >= q else len(avail)
        blind_ids += [p["id"] for p in rnd.sample(avail, take)]
    # baris tanpa pra-label (mis. kena sensor upstream) → ikut keranjang BUTA
    blind_ids += [p["id"] for p in pre if not p["label_m1"]]
    blind_ids = list(dict.fromkeys(blind_ids))
    assisted = [p for p in pre if p["id"] not in set(blind_ids)]
    rnd.shuffle(assisted)

    # teks PENUH dari sumber (gold_700/prelabel memotong di 200 char)
    text_of = {r["comment_id"].strip(): (r.get("text_original") or "").strip()
               for r in csv.DictReader(open(BASE / "data/MBG_Arya.csv",
                                            newline="", encoding="utf-8-sig"))}

    def dump(path, header, rows):
        with (BASE / path).open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(header)
            w.writerows(rows)
        print(f"→ {path} ({len(rows)})")

    dump("data/gold_blind150.csv", ["id", "text"],
         [[p["id"], text_of[p["id"]]] for p in pre if p["id"] in set(blind_ids)])
    dump("data/gold_assisted550.csv", ["id", "text", "cek_cermat", "label_pre"],
         [[p["id"], text_of[p["id"]], p["cek_cermat"], p["label_m1"]]
          for p in assisted])
    allids = [p["id"] for p in pre]
    dump("template_annotation.csv", ["id", "label", "sarkasme", "tak_jelas", "catatan"],
         [[i] + [""] * 4 for i in allids])
    n_cermat = sum(1 for p in assisted if p["cek_cermat"] == "ya")
    print(f"[catatan] assisted perlu cermat (deepseek≠GLM): {n_cermat}/{len(assisted)} "
          f"({n_cermat / max(len(assisted), 1):.0%}) — yang lain cek cepat")


if __name__ == "__main__":
    main()
