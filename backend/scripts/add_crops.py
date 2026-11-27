"""Add photo detection for rice, wheat and cotton (and a "Not a Plant Leaf" class) to the field-photo model.

Stage 2. Starts from the stage-1 field-photo model (38 classes, finetune_fieldphotos.py -> finetuned/), grows the classifier head to the labels
listed in NEW_LABELS (keeping the old 38 rows), and trains on old + new data so nothing is forgotten.

New data (Hugging Face):
  --rice-india   Project-AgML/rice_leaf_disease_classification_india  data/train-*.parquet
  --cotton       Project-AgML/cotton_leaf_disease_classification      raw/train-*.parquet
  --cld-dir      folders extracted from wambugu71/CropLeafDiseases (Wheat___*, Rice___Healthy/Hispa/
                 Leaf_Blast/Brown_Spot, Invalid) - see README "Training the model"
Old data (to keep accuracy): the same PlantDoc / PlantVillage parquet files as finetune_fieldphotos.py.

Run:  python scripts/add_crops.py --rice-india r.parquet --cotton c.parquet --cld-dir cld/ \
          --plantdoc-train a.parquet b.parquet --plantdoc-test t.parquet --plantvillage pv.parquet
Then: copy finetuned_crops/ to models/krishi-mobilenetv2-field/ and run python scripts/export_onnx.py --weights models/krishi-mobilenetv2-field
"""
import argparse
import collections
import io
import json
import os
import random
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finetune_fieldphotos import DS, TRAIN_TF, evaluate, load_plantdoc, load_plantvillage, shrink  # noqa: E402
from transformers import AutoModelForImageClassification  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = ROOT / "finetuned"  # output of finetune_fieldphotos.py (stage 1)
NEW_LABELS = [
    "Rice with Bacterial Leaf Blight", "Rice with Blast", "Rice with Brown Spot", "Rice Tungro Virus", "Rice with Hispa", "Healthy Rice Plant",
    "Wheat with Yellow Rust", "Wheat with Brown Rust", "Wheat with Septoria", "Healthy Wheat Plant",
    "Cotton with Bacterial Blight", "Cotton with Alternaria Leaf Spot", "Cotton with Fusarium Wilt", "Cotton with Verticillium Wilt",
    "Healthy Cotton Plant", "Not a Plant Leaf",
]
RICE_INDIA = {"Bacterialblight": "Rice with Bacterial Leaf Blight", "Blast": "Rice with Blast", "Brownspot": "Rice with Brown Spot", "Tungro": "Rice Tungro Virus"}
COTTON = {"Alternaria_Leaf": "Cotton with Alternaria Leaf Spot", "Bacterial_Blight": "Cotton with Bacterial Blight", "Fusarium_Wilt": "Cotton with Fusarium Wilt",
          "Healthy_Leaf": "Healthy Cotton Plant", "Verticillium_Wilt": "Cotton with Verticillium Wilt"}
CLD = {"Wheat___Yellow_Rust": "Wheat with Yellow Rust", "Wheat___Brown_Rust": "Wheat with Brown Rust", "Wheat___Septoria": "Wheat with Septoria",
       "Wheat___Healthy": "Healthy Wheat Plant", "Rice___Healthy": "Healthy Rice Plant", "Rice___Hispa": "Rice with Hispa",
       "Rice___Leaf_Blast": "Rice with Blast", "Rice___Brown_Spot": "Rice with Brown Spot", "Invalid": "Not a Plant Leaf"}


def split(items, test_frac=0.2, cap=None):
    random.shuffle(items)
    k = max(1, int(len(items) * test_frac))
    return items[k:][:cap], items[:k]


def load_parquet(path, mapping, lab2id, cap):
    t = pq.read_table(path)
    names = json.loads(t.schema.metadata[b"huggingface"])["info"]["features"]["label"]["names"]
    by = collections.defaultdict(list)
    for img, lab in zip(t.column("image").to_pylist(), t.column("label").to_pylist()):
        by[names[lab]].append(img["bytes"])
    train, test = [], []
    for name, blobs in by.items():
        tr, te = split(blobs, cap=cap)
        y = lab2id[mapping[name]]
        train += [(shrink(Image.open(io.BytesIO(b)).convert("RGB")), y) for b in tr]
        test += [(shrink(Image.open(io.BytesIO(b)).convert("RGB")), y) for b in te[:80]]
    return train, test


def load_folders(root, lab2id, cap):
    train, test = [], []
    for folder, label in CLD.items():
        files = sorted(Path(root, folder).glob("*"))
        tr, te = split(files, cap=cap)
        y = lab2id[label]
        train += [(shrink(Image.open(f).convert("RGB")), y) for f in tr]
        test += [(shrink(Image.open(f).convert("RGB")), y) for f in te[:80]]
    return train, test


def grow_head(model, new_labels):
    old = model.classifier
    n_old = old.out_features
    head = torch.nn.Linear(old.in_features, n_old + len(new_labels))
    with torch.no_grad():
        head.weight[:n_old] = old.weight
        head.bias[:n_old] = old.bias
        head.weight[n_old:].normal_(0, 0.01)
        head.bias[n_old:] = old.bias.mean()
    model.classifier = head
    id2label = {**{int(k): v for k, v in model.config.id2label.items()}, **{n_old + i: l for i, l in enumerate(new_labels)}}
    model.config.id2label = id2label
    model.config.label2id = {v: k for k, v in id2label.items()}
    model.config.num_labels = len(id2label)
    model.num_labels = len(id2label)
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rice-india", required=True)
    ap.add_argument("--cotton", required=True)
    ap.add_argument("--cld-dir", required=True)
    ap.add_argument("--plantdoc-train", nargs="+", required=True)
    ap.add_argument("--plantdoc-test", required=True)
    ap.add_argument("--plantvillage", required=True)
    ap.add_argument("--base", default=str(DEFAULT_BASE), help="stage-1 field-photo model folder")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--out", default=str(ROOT / "finetuned_crops"))
    a = ap.parse_args()
    random.seed(0)
    torch.manual_seed(0)
    torch.set_num_threads(os.cpu_count())

    model = grow_head(AutoModelForImageClassification.from_pretrained(a.base), NEW_LABELS)
    lab2id = {v: k for k, v in model.config.id2label.items()}
    cmap = json.load(open(ROOT / "data" / "class_map.json"))
    crop_of = {i: cmap[l]["crop"] for l, i in lab2id.items()}

    t0 = time.time()
    rice_tr, rice_te = load_parquet(a.rice_india, RICE_INDIA, lab2id, cap=400)
    cot_tr, cot_te = load_parquet(a.cotton, COTTON, lab2id, cap=None)
    cld_tr, cld_te = load_folders(a.cld_dir, lab2id, cap=560)
    pd_train, _ = load_plantdoc(a.plantdoc_train, lab2id, crops_per_image=1)
    pd_test, _ = load_plantdoc([a.plantdoc_test], lab2id, crops_per_image=0)
    pv_train, pv_held = load_plantvillage(a.plantvillage, 80)
    new_test = rice_te + cot_te + cld_te
    print(f"data: new train {len(rice_tr)+len(cot_tr)+len(cld_tr)} / test {len(new_test)}; plantdoc {len(pd_train)}; plantvillage {len(pv_train)} ({time.time()-t0:.0f}s)", flush=True)

    def per_class(items):
        model.eval()
        hit, tot = collections.Counter(), collections.Counter()
        with torch.no_grad():
            from finetune_fieldphotos import EVAL_TF
            for i in range(0, len(items), 64):
                b = items[i:i + 64]
                pred = model(torch.stack([EVAL_TF(im) for im, _ in b])).logits.argmax(-1).tolist()
                for (_, y), p in zip(b, pred):
                    tot[y] += 1
                    hit[y] += p == y
        return {model.config.id2label[y]: round(hit[y] / tot[y], 2) for y in sorted(tot)}

    train = rice_tr + cot_tr + cld_tr + pd_train + pv_train
    dl = torch.utils.data.DataLoader(DS(train, TRAIN_TF), batch_size=32, shuffle=True, num_workers=3, persistent_workers=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.epochs * len(dl), pct_start=0.15)
    report = {"epochs": []}
    for ep in range(a.epochs):
        model.train()
        for m in model.modules():  # keep BatchNorm statistics frozen (see finetune_fieldphotos.py)
            if isinstance(m, torch.nn.BatchNorm2d):
                m.eval()
        tot = n = 0
        for x, y in dl:
            loss = torch.nn.functional.cross_entropy(model(x).logits, y, label_smoothing=0.1)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            tot, n = tot + loss.item() * len(y), n + len(y)
        r = {"epoch": ep + 1, "loss": round(tot / n, 3), "new_crops_test": evaluate(model, new_test, crop_of),
             "plantdoc_test": evaluate(model, pd_test, crop_of), "plantvillage_held": evaluate(model, pv_held, crop_of)}
        report["epochs"].append(r)
        print(r, f"({time.time()-t0:.0f}s)", flush=True)
    # Keep the final epoch (the learning rate has annealed by then). We don't pick an epoch by test score,
    # so the reported test numbers are honest.
    model.save_pretrained(a.out)
    report["final"] = {**report["epochs"][-1], "new_crops_per_class": per_class(new_test)}
    Path(a.out, "training_report.json").write_text(json.dumps(report, indent=1))
    print("final", json.dumps(report["final"]))


if __name__ == "__main__":
    main()
