#!/usr/bin/env python3
"""Pra-pemrosesan varian P1 (ringan, utk transformer) & P2 (klasik, utk TF-IDF).

P1: lowercasing, buang URL/mention, normalisasi spasi — teks asli utk anotasi
    tidak disentuh (dipisah di sini hanya saat modeling).
P2: P1 + slang mapping + stopword id + stemming Sastrawi (opsional; fallback
    suffix-strip ringan bila Sastrawi belum terpasang).

Kamus slang: seed manual (versi Anda, layak ditulis sbg kontribusi kecil) —
perluas/disitasi dari NusaCrowds/slank.id sebelum final.
Import dari script lain: `from preprocess import p1, p2, ID_STOPWORDS`.
"""
from __future__ import annotations

import re

SLANG = {
    "gk": "tidak", "gak": "tidak", "nggak": "tidak", "ndak": "tidak", "tdk": "tidak",
    "bgt": "banget", "bngt": "banget", "bjt": "banget",
    "sy": "saya", "aq": "aku", "ak": "aku", "q": "aku", "sya": "saya",
    "dgn": "dengan", "sm": "sama", "sma": "sama", "dr": "dari", "dri": "dari",
    "utk": "untuk", "untu": "untuk", "blh": "boleh", "hrus": "harus",
    "bntr": "sebentar", "ntar": "nanti", "skrg": "sekarang", "sdh": "sudah",
    "sdh": "sudah", "blm": "belum", "bkn": "bukan", "kalo": "kalau",
    "klw": "kalau", "kl": "kalau", "cma": "cuma", "cm": "cuma", "aja": "saja",
    "sih": "sih", "dong": "dong", "deh": "deh", "nih": "ini", "tu": "itu",
    "pjk": "pajak", "krn": "karena", "karna": "karena", "krna": "karena",
    "emng": "memang", "mn": "mana", "dimn": "dimana", "dw": "dunia usaha",
    "py": "punya", "pnya": "punya", "ny": "nya", "anak2": "anak-anak",
    "brp": "berapa", "gmn": "bagaimana", "gmna": "bagaimana", "og": "saya",
    "lu": "kamu", "elo": "kamu", "gw": "saya", "gue": "saya", "sykt": "sehat",
    "rusak": "rusak", "mrah": "marah", "mrh": "marah", "sng": "senang",
}

# Stopword id (versi ringkas dari list nltk id + adaptasi; final pakai nltk)
ID_STOPWORDS = set("""dan di ke dari yang untuk pada adalah itu ini saya aku kamu anda mereka kami
kalian nya dia ia dengan tanpa dalam luar atas bawah sebagai sebagai juga masih sudah akan mau bisa dapat
harus tidak bukan agar agar supaya supaya tapi namun karena sebab saat ketika telah lagi telah sangat
ya i ih eh oh aduh wah duh si si teh deh dong lah kah pun per para antara setiap semua seluruh beberapa
banyak sedikit satu dua tiga jika kalau bagai seperti yakni ialah adalah merupakan""".split())

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
MENTION_RE = re.compile(r"@\w+")
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF☀-➿]+")
SPACES_RE = re.compile(r"\s+")


def _try_sastrawi():
    try:
        from Sastrawi.Stemmer.StemmerFactory import StemmerFactory  # noqa
        return StemmerFactory().create_stemmer()
    except Exception:
        return None


def p1(text: str) -> str:
    t = URL_RE.sub(" ", text.lower())
    t = MENTION_RE.sub(" ", t)
    t = EMOJI_RE.sub(" ", t)
    return SPACES_RE.sub(" ", t).strip()


def p2(text: str) -> str:
    t = p1(text)
    toks = [w for w in (SLANG.get(x, x) for x in t.split()) if w not in ID_STOPWORDS]
    joined = " ".join(toks)
    stemmer = _try_sastrawi()
    if stemmer:
        return stemmer.stem(joined)
    # fallback suffix-strip ringan (-nya, -kan, -an, -i) — ponytail: pengganti
    # Sastrawi sampai dependensi terpasang; hasil tidak identik, tandai di laporan.
    return " ".join(re.sub(r"(nya|kan|an|i)$", "", w) if len(w) > 4 else w for w in toks)


if __name__ == "__main__":
    demo = "Sy dukung bgt program MBG 🙏 https://youtu.be/x @bgn, anak2 jadi sehat"
    print("P1:", p1(demo))
    print("P2:", p2(demo))
