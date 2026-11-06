#!/usr/bin/env python3
"""Form adjudikasi — diskusikan disagreements A vs B, pilih label_final.
Usage: python scripts/adjudikasi.py ; buka http://localhost:8790
Output: data/gold_final.csv (700 baris; sepakat otomatis, kumpulan dari form).
Resume-aware; reset satu baris = kosongkan via catatan khusus tak tersedia (edit CSV).
"""
import csv, html, http.server, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "gold_final.csv"
COLS = ["id", "text", "label_a", "label_b", "label_pre", "label_final", "metode", "koreksi_llm", "adjudicated"]
NORM = {"-1": "negatif", "1": "positif", "0": "netral", "-": "negatif", "+": "positif"}


def texts():
    t = {}
    for p, idc, txtc in [("data/gold_blind150.csv", "id", "text"),
                         ("data/gold_assisted550.csv", "id", "text")]:
        for r in csv.DictReader(open(ROOT / p, encoding="utf-8-sig")):
            t[r[idc]] = r[txtc]
    return t


def pre():
    p = {}
    for r in csv.DictReader(open(ROOT / "data/gold_assisted550.csv", encoding="utf-8-sig")):
        p[r["id"]] = (r.get("label_pre") or "").strip().lower()
    return p


def ann(which):
    path = ROOT / "data" / f"annotation_{which}.csv"
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        lab = NORM.get((r["label"] or "").strip(), (r["label"] or "").strip()).lower()
        out[r["id"]] = {"label": lab, "sarkasme": (r.get("sarkasme") or "").strip(),
                        "catatan": r.get("catatan") or ""}
    return out


TXT = texts()
PRE = pre()
A = ann("A")
B = ann("B")
ORDER = [rid for rid in TXT if rid in A and rid in B]
DIS = [rid for rid in ORDER if A[rid]["label"] != B[rid]["label"]]

if OUT.exists():
    FINAL = {r["id"]: r for r in csv.DictReader(open(OUT, encoding="utf-8-sig"))}
else:
    FINAL = {}


def rows_for(rid):
    va, vb = A[rid], B[rid]
    return {"id": rid, "text": TXT[rid], "label_a": va["label"], "label_b": vb["label"],
            "label_pre": PRE.get(rid, ""), "label_final": "", "metode": "", "koreksi_llm": "", "adjudicated": ""}


def save():
    rows = []
    for rid in ORDER:
        if rid in FINAL:
            rows.append(FINAL[rid])
        elif A[rid]["label"] == B[rid]["label"]:
            r = rows_for(rid)
            r.update(label_final=A[rid]["label"], metode="sepakat",
                     sarkasme_final=A[rid]["sarkasme"] or B[rid]["sarkasme"], adjudicated="")
            rows.append(r)
        else:
            rows.append(rows_for(rid))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return rows


PENDING = [rid for rid in DIS if rid not in FINAL or not FINAL[rid].get("label_final")]


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(n).decode())
        uid = form.get("id", [""])[0]
        if uid not in DIS:
            return self._send(b"bukan unit disagreement", 400)
        fin = (form.get("label_final", [""])[0] or "").strip().lower()
        fin = NORM.get(fin, fin)
        if fin not in ("negatif", "netral", "positif"):
            return self._send(b"label_final wajib salah satu: positif/netral/positif", 400)
        r = rows_for(uid)
        r.update(label_final=fin, metode="adjudicated",
                 koreksi_llm=form.get("koreksi_llm", [""])[0],
                 sarkasme_final=form.get("sarkasme_final", [""])[0] or A[uid]["sarkasme"],
                 adjudicated="true")
        if uid in FINAL:
            r.update({k: v for k, v in FINAL[uid].items() if k not in r})
        FINAL[uid] = r
        save()
        if uid in PENDING:
            PENDING.remove(uid)
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        path, _, q = self.path.partition("?")
        qs = urllib.parse.parse_qs(q)
        if path == "/export":
            save()
            return self._send(open(OUT, "rb").read(), "text/csv; charset=utf-8")
        n_dis = len(DIS)
        if not PENDING:
            body = (f"<h1>Adjudikasi selesai</h1><p>Semua {n_dis} disagreement terputuskan. "
                    f"File final: data/gold_final.csv ({len(ORDER)} baris).</p>").encode()
            return self._send(body)
        i = int(qs.get("i", [DIS.index(PENDING[0])])[0])
        rid = DIS[i]
        va, vb = A[rid], B[rid]
        body = f"""<!doctype html><meta charset=utf-8><title>Adjudikasi</title><style>
body{{font-family:sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem}}
.t{{font-size:1.25rem;line-height:1.6;border:1px solid #ccc;border-radius:.5rem;padding:1rem;margin:1rem 0}}
button{{font-size:1.25rem;padding:.55rem 1.3rem;margin:.15rem;border-radius:.4rem;border:1px solid #999;cursor:pointer}}
.badge{{display:inline-block;padding:.15rem .7rem;border-radius:1rem;font-weight:bold;margin-right:.6rem}}
.A{{background:#dfe}}  .B{{background:#fed}}  .pre{{color:#777;margin:.2rem 0}}
.row{{margin:.6rem 0}} label{{margin-right:1rem}}
</style><h1>Adjudikasi — sisa {len(PENDING)}/{n_dis}</h1>
<div class=t>{html.escape(TXT[rid])}</div>
<div><span class="badge A">A: {va['label']}</span><span class="badge B">B: {vb['label']}</span>
<span class="pre">pre(deepseek): {PRE.get(rid,'-')} | sark: A={va['sarkasme'] or '-'} B={vb['sarkasme'] or '-'}</span></div>
<div class="pre">cat A: {html.escape(va['catatan'] or '-')}</div>
<div class="pre">cat B: {html.escape(vb['catatan'] or '-')}</div>
<form method=post><input type=hidden name=id value="{rid}">
<div class=row>
<button name=label_final value=negatif>👎 negatif</button>
<button name=label_final value=netral>0 netral</button>
<button name=label_final value=positif>👍 positif</button>
<label><input type=checkbox name=sarkasme_final value=true> sarkasme final</label>
</div>
<input name=koreksi_llm placeholder="catatan koreksi LLM (opsional)" style=width:26rem>
<button style=margin-left:.5rem>💾 Simpan</button></form>
<p><a href="/?i={i+1}">→ skip</a></p>""".encode()
        self._send(body)


if __name__ == "__main__":
    port = 8790
    print(f"adjudikasi: http://localhost:{port} | sisa {len(PENDING)}/{len(DIS)} disagreement | output {OUT}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
