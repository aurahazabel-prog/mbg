#!/usr/bin/env python3
"""Form anotasi lokal. Usage: python scripts/anotasi.py A|B
Serves one comment at a time (blind 151 first, then assisted 549),
auto-saves data/annotation_{A|B}.csv on every submission. Resume-aware.
ponytail: no auth/DB — single trusted annotator per port; upgrade if multi-user.
"""
import csv, http.server, json, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHO = sys.argv[1].upper() if len(sys.argv) > 1 else "A"
assert WHO in ("A", "B"), "gunakan: python scripts/anotasi.py A  (atau B)"
OUT = ROOT / "data" / f"annotation_{WHO}.csv"
COLS = ["id", "label", "sarkasme", "tak_jelas", "catatan"]


def load_units():
    units = []
    blind = ROOT / "data" / "gold_blind150.csv"
    with open(blind, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            units.append({"id": r["id"], "text": r["text"], "blind": True})
    with open(ROOT / "data" / "gold_assisted550.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            units.append({"id": r["id"], "text": r["text"], "blind": False,
                          "cek_cermat": r.get("cek_cermat", ""), "label_pre": r.get("label_pre", "")})
    return units


UNITS = load_units()
BY_ID = {u["id"]: u for u in UNITS}


def load_saved():
    if OUT.exists():
        with open(OUT, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        saved = {r["id"]: {k: r.get(k, "") for k in COLS} for r in rows}
    else:
        saved = {}
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=COLS).writeheader()
    return saved


SAVED = load_saved()
ORDER = [u["id"] for u in UNITS]
PENDING = [i for i in ORDER if i not in SAVED]


def next_idx(qs):
    idx = int(qs.get("i", 0))
    if qs.get("done") != "1" and idx < len(ORDER) and ORDER[idx] in SAVED:
        base = qs.get("_from")
        skip = int(base) if base is not None else idx
        for j in range(skip + 1, len(ORDER)):
            if ORDER[j] not in SAVED:
                return j
        for j in range(len(ORDER)):
            if ORDER[j] not in SAVED:
                return j
        return len(ORDER)
    if qs.get("done") == "1":
        for j in range(idx + 1, len(ORDER)):
            if ORDER[j] not in SAVED:
                return j
        return next((i for i, v in enumerate(ORDER) if v not in SAVED), len(ORDER))
    return idx


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, code=200, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(n).decode())
        uid = form.get("id", [""])[0]
        if uid not in BY_ID:
            return self._send(b"bad id", 400)
        row = {"id": uid, **{k: form.get(k, [""])[0] for k in COLS[1:]}}
        row["id"] = uid
        SAVED[uid] = row
        if uid in PENDING:
            PENDING.remove(uid)
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(SAVED[i] for i in ORDER if i in SAVED)
        self._redirect(i=ORDER.index(uid) + 1, done="1")

    def _redirect(self, **qs):
        self.send_response(303)
        self.send_header("Location", "/?" + urllib.parse.urlencode(qs))
        self.end_headers()

    def do_GET(self):
        path, _, q = self.path.partition("?")
        qs = urllib.parse.parse_qs(q)
        if path == "/export":
            body = open(OUT, "rb").read()
            return self._send(body, ctype="text/csv; charset=utf-8")
        i = next_idx(qs)
        done = len(PENDING) == 0
        n = len(ORDER)
        if done:
            body = f"""<meta charset=utf-8><h1>Selesai! {n}/{n} teranotasi (annotator {WHO})</h1>
<p>Tutup tab ini. File: {OUT.name}</p>""".encode()
            return self._send(body)
        u = BY_ID[ORDER[i]]
        prev = SAVED.get(u["id"], {})
        label = prev.get("label", "")
        sark = "checked" if prev.get("sarkasme") == "true" else ""
        tj = "checked" if prev.get("tak_jelas") == "true" else ""
        pre = ""
        if not u["blind"]:
            pre_show = (f'<div class="pre">pra-label ({u.get("label_pre","?")}): '
                        f'{"<b>cek cermat — nilai dulu sendiri YA</b>: label_pre dibuka" if u.get("cek_cermat")=="ya" else "label_pre dibuka"}</div>') \
                if (label or qs.get("reveal") == "1") else \
                (f'<div class="pre"><a href="/?i={i}&reveal=1">[lihat pra-label]</a></div>')
            pre = pre_show
        body = f"""<!doctype html><meta charset=utf-8>
<title>Anotasi {WHO}</title><style>
body{{font-family:sans-serif;max-width:44rem;margin:2rem auto;padding:0 1rem}}
.t{{font-size:1.25rem;line-height:1.6;margin:1rem 0;border:1px solid #ccc;padding:1rem;border-radius:.5rem}}
.pre{{color:#666;margin:.5rem 0}}
button{{font-size:1.3rem;padding:.6rem 1.4rem;margin:.2rem;border-radius:.4rem;border:1px solid #999;cursor:pointer}}
.sel{{outline:3px solid #222}}
.row{{margin-bottom:1rem}}label{{margin-right:1rem}}
code{{color:#777}}</style>
<h1>Annotator {WHO} — {i+1}/{n} <code>(sisa {len(PENDING)}, tersimpan {len(SAVED)})</code></h1>
<div class=t>{u["text"].replace("<","&lt;")}</div>
{"<div style=color:#999>BLIND — tanpa pra-label</div>" if u["blind"] else pre}
<form method=post>
<input type=hidden name=id value="{u["id"]}">
<div class=row id=lrow>
<button name=label value=+ class="{'sel' if label=='+' else ''}">👍 +</button>
<button name=label value=0 class="{'sel' if label=='0' else ''}">0 netral</button>
<button name=label value=- class="{'sel' if label=='-' else ''}">👎 −</button>
</div>
<div class=row>
<label><input type=checkbox name=sarkasme value=true {sark}> sarkasme</label>
<label><input type=checkbox name=tak_jelas value=true {tj}> tak jelas</label>
</div>
<input name=catatan placeholder="catatan (opsional)" value="{prev.get('catatan','').replace('"','&quot;')}" style=width:24rem>
<button style=margin-left:1rem>💾 Simpan</button>
</form>
<p><a href="/?i={i+1}">→ lewati</a></p>""".encode()
        self._send(body)


if __name__ == "__main__":
    port = 8787 if WHO == "A" else 8788
    print(f"Annotator {WHO}: buka http://localhost:{port}  | output: {OUT}")
    http.server.ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
