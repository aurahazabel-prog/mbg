#!/usr/bin/env python3
"""Weak labeling W2 — pelabelan sentimen LLM untuk komentar MBG (skripsi).

Mengirim SATU request per komentar melalui Anthropic **Message Batches API**
(asinkron, diskon 50%), dengan instruksi+few-shot di-`system` dan **prompt
caching** pada blok few-shot. Output: CSV `label_llm` siap dipakai sebagai
weak label (W2) untuk eksperimen X5 dan dataset training.

Aturan metodologis (lihat BAB III / dokumen rencana):
  - Hasil skrip ini HANYA untuk training (weak label). Gold set = anotasi
    manusia; ID gold set wajib dilewatkan lewat --exclude-ids.
  - Selalu pilot dulu: `--limit 100`, review, baru full run.

Contoh pemakaian
----------------
  # 1) Uji alur tanpa API key / tanpa biaya (heuristik kata kunci):
  python -I scripts/weak_label_llm.py MBG_Arya.csv --dry-run --out weak_labels.csv

  # 2) Simulasi biaya saja:
  python -I scripts/weak_label_llm.py MBG_Arya.csv --estimate-only

  # 3) Pilot 100 komentar (butuh ANTHROPIC_API_KEY atau profil `ant auth login`):
  python -I scripts/weak_label_llm.py MBG_Arya.csv --limit 100 --out weak_labels.csv

  # 4) Full run 10k, ID gold set dikecualikan (satu kolom id per baris):
  python -I scripts/weak_label_llm.py MBG_Arya.csv --exclude-ids gold_ids.csv --out weak_labels.csv

Resume: jalankan ulang dengan --out yang sama; baris yang sudah berstatus ok
tidak dikirim ulang.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

TEXT_HINTS = ("comment", "text", "isi", "komentar", "body", "content")

# ---------------------------------------------------------------- prompts --
INSTRUKSI = """Kamu adalah annotator sentimen untuk riset akademik berbahasa Indonesia.
Tugas: memberi label SATU komentar YouTube tentang program Makan Bergizi Gratis (MBG) — program pemerintah Indonesia yang menyediakan makanan bergizi gratis bagi siswa dan ibu hamil.

Kelas label (pilih TEPAT SATU):
- "positif": mendukung/memuji program atau pelaksanaannya (manfaat, harapan, apresiasi, terima kasih).
- "negatif": mengkritik/menolak program atau pelaksanaannya (kecewa, kasus keracunan/kegagalan distribusi, boros/salah sasaran anggaran, sinis/cemooh).
- "netral": informasi/berita/tanya-jawab tanpa condong dukung/tolak; spam atau tidak jelas kaitannya dengan MBG juga "netral".

Aturan:
1. Nilailah sentimen TERHADAP program/pelaksanaan MBG, bukan emosi umum penulis komentar.
2. Sarkasme: maknai maksud sebenarnya (biasanya menjadi "negatif") dan tandai "sarkasme": true.
3. Kritik keras kepada pemerintah yang jelas terkait program = negatif; hujatan tanpa kaitan program = netral.
4. Pertanyaan faktual ("MBG mulai kapan?") = netral.

Format jawaban: HANYA satu objek JSON, tanpa teks lain:
{"label": "positif|netral|negatif", "sarkasme": true|false, "alasan": "penjelasan maksimal 8 kata"}"""

FEWSHOT = """Contoh:
Komentar: "Program MBG sangat membantu orang tua, anak makan terjamin gizinya."
Jawaban: {"label": "positif", "sarkasme": false, "alasan": "apresiasi manfaat program"}

Komentar: "Anak saya sampai keracunan, mana bilang bergizi?!"
Jawaban: {"label": "negatif", "sarkasme": false, "alasan": "kegagalan keamanan pangan"}

Komentar: "Anggarannya triliunan, mending buat gaji guru."
Jawaban: {"label": "negatif", "sarkasme": false, "alasan": "kritik prioritas anggaran"}

Komentar: "MBG mulai kapan sih di daerah saya?"
Jawaban: {"label": "netral", "sarkasme": false, "alasan": "pertanyaan faktual"}

Komentar: "Wow hebat, menunya keracunan, pasti bergizi tuh dari dapur bersih."
Jawaban: {"label": "negatif", "sarkasme": true, "alasan": "sarkasme atas kasus keracunan"}

Komentar: "Ya pro dan kontra itu wajar program baru, yang penting evaluasi."
Jawaban: {"label": "netral", "sarkasme": false, "alasan": "posisi berimbang"}

Komentar: "JUALAN TAS MURAH, WA 0812xxxx, lupakan urusan sekolah"
Jawaban: {"label": "netral", "sarkasme": false, "alasan": "spam tidak relevan"}

Komentar: "Mantap sarapan gratis, konsentrasi belajar anak naik katanya."
Jawaban: {"label": "positif", "sarkasme": false, "alasan": "dukungan manfaat pendidikan"}"""

VALID_LABELS = {"positif", "netral", "negatif"}

# Harga per juta token (cache skill 2026-10-06 — verifikasi sebelum run), batch = x0.5
PRICE_MTOK = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-fable-5-1": (10.00, 50.00),
}

# ---------------------------------------------------------------- helpers --

def sniff_dialect(path: Path):
    sample = path.read_text(encoding="utf-8", errors="replace")[:64_000]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel


def is_id_like(col: str) -> bool:
    lc = col.lower()
    return lc == "id" or lc.endswith("_id") or any(h in lc for h in ("url", "user", "nama", "link"))


def pick_text_col(fieldnames: list[str], explicit: str | None) -> str:
    if explicit:
        if explicit not in fieldnames:
            sys.exit(f"Kolom {explicit!r} tidak ada. Pilihan: {fieldnames}")
        return explicit
    # kolom id/url/user tidak pernah boleh jadi kolom teks (mis. `comment_id`)
    cands = [c for c in fieldnames if any(h in c.lower() for h in TEXT_HINTS) and not is_id_like(c)]
    if not cands:
        sys.exit(f"Tidak menemukan kolom teks otomatis — pakai --text-col. Pilihan: {fieldnames}")
    prio = ("text", "komentar", "isi", "content", "body", "comment")
    cands.sort(key=lambda c: next((k for k, h in enumerate(prio) if h in c.lower()), 99))
    return cands[0]


def pick_id_col(fieldnames: list[str], rows: list[dict]) -> str | None:
    """Kolom id eksplisit jika ada dan unik (mis. comment_id); selain itu indeks baris."""
    for c in fieldnames:
        lc = c.lower()
        if lc == "id" or lc.endswith("_id"):
            vals = [str(r.get(c) or "").strip() for r in rows]
            if len(set(vals)) == len(vals) and all(vals):
                return c
    return None


def parse_answer(raw: str) -> tuple[str | None, str, str]:
    """Kembalikan (label|None, sarkasme, alasan) dari teks respons LLM."""
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    m = re.search(r"\{.*\}", cleaned, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            label = str(obj.get("label", "")).strip().lower()
            if label in VALID_LABELS:
                sark = "true" if obj.get("sarkasme") in (True, "true", "True") else "false"
                return label, sark, str(obj.get("alasan", ""))[:80]
        except json.JSONDecodeError:
            pass
    low = cleaned.lower()  # fallback scan kata
    hits = {l: low.count(l) for l in VALID_LABELS}
    best = max(hits, key=hits.get)
    if hits[best]:
        return best, ("true" if "sarkasme\": true" in low or "sarkasme: true" in low else "false"), "fallback-parse"
    return None, "", "unparsed"


def mock_label(text: str) -> tuple[str, str, str]:
    """Heuristik kata-kunci untuk --dry-run (BUKAN pengganti W2 sungguhan)."""
    low = text.lower()
    pos = re.search(r"bantu|bergizi|mantap|hebat|terima kasih|dukung|syukur|senang|bagus|manfaat", low)
    neg = re.search(r"keracunan|boros|mubazir|gagal|jelek|bosan|korupsi|lama|kurang|asalan|racun|kecewa", low)
    if neg and not pos:
        return "negatif", "false", "dryrun-neg"
    if pos and not neg:
        return "positif", "false", "dryrun-pos"
    return "netral", "false", "dryrun-net"


# ------------------------------------------------------------------ main --

def main() -> None:
    ap = argparse.ArgumentParser(description="Weak labeling W2 — LLM batch sentimen MBG")
    ap.add_argument("csv_path", help="mis. MBG_Arya.csv")
    ap.add_argument("--text-col", help="kolom teks komentar (otok-deteksi jika kosong)")
    ap.add_argument("--id-col", help="kolom id baris; default = indeks baris")
    ap.add_argument("--out", default="weak_labels_llm.csv")
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--limit", type=int, default=0, help="hanya N komentar pertama (pilot)")
    ap.add_argument("--exclude-ids", help="file txt/csv berisi id gold set yang tidak boleh dilabel LLM")
    ap.add_argument("--chunk", type=int, default=5000, help="request per batch (maks 100.000)")
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--poll", type=int, default=30, help="detik jeda polling status batch")
    ap.add_argument("--dry-run", action="store_true", help="tanpa API — heuristik kata kunci")
    ap.add_argument("--estimate-only", action="store_true", help="cetak estimasi biaya lalu berhenti")
    args = ap.parse_args()

    path = Path(args.csv_path)
    if not path.exists():
        sys.exit(f"File tidak ditemukan: {path} (unduh MBG_Arya.csv dari Kaggle dulu)")

    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh, dialect=sniff_dialect(path))
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    if not rows:
        sys.exit("CSV kosong?")

    tcol = pick_text_col(fieldnames, args.text_col)
    idcol = args.id_col or pick_id_col(fieldnames, rows)
    print(f"[kolom] teks={tcol!r} | id={'indeks baris' if not idcol else repr(idcol)}")
    excluded: set[str] = set()
    if args.exclude_ids:
        p = Path(args.exclude_ids)
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            v = line.strip().split(",")[0].strip()
            if v and v.lower() != "id":
                excluded.add(v)

    # bangun daftar kerja: (id, teks)
    items: list[tuple[str, str]] = []
    for i, r in enumerate(rows):
        rid = str(r.get(idcol)).strip() if idcol else str(i)
        if rid in excluded:
            continue
        t = str(r.get(tcol) or "").strip()
        if not t:
            continue
        items.append((rid, t))
    if args.limit:
        items = items[: args.limit]

    # resume: skip id yang sudah ok di file out
    out_path = Path(args.out)
    done_ids: set[str] = set()
    if out_path.exists():
        with out_path.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (r.get("status") or "").startswith("ok"):
                    done_ids.add(r.get("id", ""))
    todo = [(i, t) for i, t in items if i not in done_ids]

    # estimasi biaya
    sys_chars = len(INSTRUKSI) + len(FEWSHOT)
    tin_per_req = sys_chars / 3.0 + 30
    tin = sum(tin_per_req + len(t) / 3.0 for _, t in todo)
    tout = len(todo) * 40
    pin, pout = PRICE_MTOK.get(args.model, (0.10, 0.50))
    cost = (tin / 1e6 * pin + tout / 1e6 * pout) * (0.5 if not args.dry_run else 0)
    print(f"[rencana] model={args.model} | item={len(todo)} (skip selesai={len(done_ids)}, "
          f"exclude={len(excluded)}) | perkiraan token in/out ≈ {tin:,.0f}/{tout:,.0f} | "
          f"perkiraan biaya batch ≈ USD {cost:.2f}*")
    print("  (*harga tabel cache 2026-10-06; dengan prompt caching bisa lebih murah lagi)")
    if args.estimate_only:
        return
    if not todo:
        print("Tidak ada item baru — selesai.")
        return

    write_new = not out_path.exists()
    fh = out_path.open("a", newline="", encoding="utf-8")
    w = csv.writer(fh)
    if write_new:
        w.writerow(["id", "text", "label_llm", "sarkasme_llm", "alasan_llm", "status", "provenance"])

    def save(rid: str, text: str, label, sark, alasan, status, prov: str):
        w.writerow([rid, text[:200], label or "", sark, alasan, status, prov])

    try:
        if args.dry_run:
            for rid, t in todo:
                lab, sark, alasan = mock_label(t)
                save(rid, t, lab, sark, alasan, "ok-dryrun", "dryrun-heuristic")
            print(f"[dry-run] {len(todo)} baris ditulis ke {out_path} — HEURISTIK, bukan LLM.")
            return

        import anthropic  # noqa: lazy import — tidak dibutuhkan utk --dry-run
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request
    except ImportError:
        sys.exit("SDK `anthropic` belum terpasang: pip install anthropic (atau pakai --dry-run untuk uji alur)")

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY / profil `ant auth login`
    system_blocks = [
        {"type": "text", "text": INSTRUKSI},
        {"type": "text", "text": FEWSHOT, "cache_control": {"type": "ephemeral"}},
    ]

    try:
        for start in range(0, len(todo), args.chunk):
            chunk = todo[start : start + args.chunk]
            requests = [
                Request(
                    custom_id=f"c:{rid}",
                    params=MessageCreateParamsNonStreaming(
                        model=args.model,
                        max_tokens=args.max_tokens,
                        output_config={"effort": "low"},
                        system=system_blocks,
                        messages=[{"role": "user", "content": t}],
                    ),
                )
                for rid, t in chunk
            ]
            batch = client.messages.batches.create(requests=requests)
            print(f"[batch {start//args.chunk + 1}] id={batch.id} ({len(requests)} request) — menunggu…")
            while True:
                batch = client.messages.batches.retrieve(batch.id)
                if batch.processing_status == "ended":
                    break
                time.sleep(args.poll)

            texts = dict(chunk)
            n_ok = 0
            for result in client.messages.batches.results(batch.id):
                rid = result.custom_id.removeprefix("c:")
                text = texts.get(rid, "")
                if result.result.type == "succeeded":
                    msg = result.result.message
                    raw = next((b.text for b in msg.content if b.type == "text"), "")
                    lab, sark, alasan = parse_answer(raw)
                    if lab:
                        save(rid, text, lab, sark, alasan, "ok", args.model)
                        n_ok += 1
                    else:
                        save(rid, text, "", "", raw[:120], "parse_error", args.model)
                elif result.result.type == "errored":
                    save(rid, text, "", "", "", "errored", args.model)
                else:
                    save(rid, text, "", "", "", result.result.type, args.model)
            print(f"[batch selesai] ok={n_ok}/{len(chunk)} — tersimpan di {out_path}")
        print("SELESAI. Jalankan pilot review sebelum dipakai training.")
    finally:
        fh.close()


if __name__ == "__main__":
    main()
