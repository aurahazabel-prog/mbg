#!/usr/bin/env python3
"""Fine-tune IndoBERT (X1/X2/X3) — jalankan di GPU (Kaggle/Colab T4, pip install
transformers datasets accelerate scikit-learn).

    python scripts/train_indobert.py --exp e2 --model indobenchmark/indobert-base-p1 \
        --gold gold_final.csv --seed 42

exp: e1 = weak-only latih; e2 = weak + gold-train; e3 = gold-only.
Evaluasi akhir HANYA pada gold-test. Aturan anti-bocor: id gold TIDAK PERNAH
ikut latih di e1; di e2/e3 hanya train-gold yang ikut (keputusan BAB III).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import train_test_split
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          Trainer, TrainingArguments)

LABELS = ["negatif", "netral", "positif"]
L2I = {l: i for i, l in enumerate(LABELS)}
I2L = {i: l for l, i in L2I.items()}


def load_weak(strategy="c"):
    out = {}
    for r in csv.DictReader(open("data/weak_final.csv", newline="", encoding="utf-8")):
        if r["weak_final"] in LABELS:
            out[r["id"]] = r["weak_final"]
        elif strategy == "c" and r["label_w2"] in LABELS:
            out[r["id"]] = r["label_w2"]
    return out


def load_gold(path):
    out = {}
    for r in csv.DictReader(open(path, newline="", encoding="utf-8-sig")):
        lab = (r.get("label_final") or r.get("label") or "").strip().lower()
        if lab in LABELS:
            out[r["id"].strip()] = lab
    return out


def load_texts():
    return {r["comment_id"].strip(): (r.get("text_original") or "").strip()
            for r in csv.DictReader(open("data/MBG_Arya.csv", newline="", encoding="utf-8-sig"))}


class DS(torch.utils.data.Dataset):
    def __init__(self, ids, labels, texts, tok, maxlen):
        enc = tok([texts[i] for i in ids], truncation=True, max_length=maxlen)
        self.enc = [{k: v[i] for k, v in enc.items()} for i in range(len(ids))]
        self.y = [labels[i] for i in ids]

    def __len__(self):
        return len(self.enc)

    def __getitem__(self, i):
        item = {k: torch.tensor(v) for k, v in self.enc[i].items()}
        item["labels"] = torch.tensor(self.y[i])
        return item


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", choices=["e1", "e2", "e3"], default="e2")
    ap.add_argument("--model", default="indobenchmark/indobert-base-p1")
    ap.add_argument("--gold", default="gold_final.csv")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--maxlen", type=int, default=128)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--min-gold", type=int, default=400)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    texts = load_texts()
    gold_map = load_gold(args.gold)
    if len(gold_map) < args.min_gold:
        raise SystemExit(f"Gold di {args.gold} cuma {len(gold_map)} — selesaikan anotasi dulu.")
    weak = load_weak()

    gids = [i for i in gold_map if texts.get(i)]
    # split gold: 1/3 train-gold (dipakai e2/e3), 2/3 test-gold (evaluasi final)
    g_train, g_test = train_test_split(
        gids, test_size=0.67, random_state=args.seed,
        stratify=[gold_map[i] for i in gids])
    weak_train = [i for i in weak if texts.get(i) and i not in gold_map]

    if args.exp == "e1":
        tr_ids = weak_train
    elif args.exp == "e2":
        tr_ids = weak_train + g_train
    else:
        tr_ids = g_train
    tr_lab = {i: (gold_map.get(i) or weak.get(i)) for i in tr_ids}
    tr_lab = {i: L2I[l] for i, l in tr_lab.items() if l}
    tr_ids = [i for i in tr_ids if i in tr_lab]

    # val dari train-gold supaya early stopping memakai label manusia;
    # e1 (tanpa gold latih) pakai split acak weak utk val — laporkan sebagai limitasi.
    if args.exp == "e1":
        tr_ids, va_ids = train_test_split(tr_ids, test_size=0.1, random_state=args.seed,
                                          stratify=[tr_lab[i] for i in tr_ids])
    else:
        tr_ids, va_ids = train_test_split(tr_ids, test_size=0.12, random_state=args.seed,
                                          stratify=[tr_lab[i] for i in tr_ids])
    te_ids = g_test
    print(f"[{args.exp}] train={len(tr_ids)} val={len(va_ids)} test-gold={len(te_ids)} "
          f"dist-train={np.bincount([tr_lab[i] for i in tr_ids], minlength=3)}")

    tok = AutoTokenizer.from_pretrained(args.model)
    ds_tr = DS(tr_ids, tr_lab, texts, tok, args.maxlen)
    ds_va = DS(va_ids, tr_lab, texts, tok, args.maxlen)
    ds_te = DS(te_ids, {i: L2I[gold_map[i]] for i in te_ids}, texts, tok, args.maxlen)

    from sklearn.metrics import f1_score

    def metrics(eval_pred):
        logits, y = eval_pred
        pred = np.argmax(logits, axis=-1)
        return {"macro_f1": f1_score(y, pred, average="macro", labels=[0, 1, 2]),
                "acc": (pred == y).mean()}

    model = AutoModelForSequenceClassification.from_pretrained(args.model, num_labels=3)
    # class weight utk 6%-positif
    cnt = np.bincount([tr_lab[i] for i in tr_ids], minlength=3).astype(float)
    weights = torch.tensor((cnt.sum() / (3 * np.maximum(cnt, 1))), dtype=torch.float32)
    steps = max(1, args.epochs * -(-len(tr_ids) // args.batch))  # ceil steps/epoch
    targs = TrainingArguments(
        output_dir=f"runs/{args.exp}_{args.model.split('/')[-1]}_{args.seed}",
        num_train_epochs=args.epochs, learning_rate=args.lr,
        per_device_train_batch_size=args.batch, per_device_eval_batch_size=64,
        eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model="macro_f1",
        seed=args.seed, report_to="none",
        warmup_steps=max(1, int(0.1 * steps)), weight_decay=0.01)

    class WTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kw):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            loss = torch.nn.functional.cross_entropy(
                outputs.logits, labels, weight=weights.to(outputs.logits.device))
            return (loss, outputs) if return_outputs else loss

    trainer = WTrainer(model=model, args=targs, train_dataset=ds_tr,
                      eval_dataset=ds_va, processing_class=tok, compute_metrics=metrics)
    trainer.train()

    pred = trainer.predict(ds_te)
    y_true = np.array([L2I[gold_map[i]] for i in te_ids])
    y_hat = np.argmax(pred.predictions, axis=-1)
    out = {"exp": args.exp, "model": args.model, "seed": args.seed,
           "macro_f1": float(f1_score(y_true, y_hat, average="macro", labels=[0, 1, 2])),
           "per_class_f1": {LABELS[k]: float(f1_score(y_true == k, y_hat == k, average="binary"))
                            for k in range(3)},
           "confusion": np.array([[int(((y_true == a) & (y_hat == b)).sum())
                                   for b in range(3)] for a in range(3)]).tolist()}
    p = Path("results") / f"indobert_{args.exp}_{args.model.split('/')[-1]}_{args.seed}.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
