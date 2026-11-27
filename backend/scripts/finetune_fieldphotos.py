"""Fine-tune the PlantVillage MobileNetV2 on real field photos (PlantDoc) so it works on farmers' photos.

Why: the base model is trained only on lab photos (single leaf, plain background). On PlantDoc's
real-world test set it is right only ~31% of the time. We keep the same 38 output classes, so the
rest of the app (class_map.json, knowledge base) is unchanged.

Data (Hugging Face parquet files, passed as arguments):
  --plantdoc-train   agyaatcoder/PlantDoc  data/train-*.parquet   (field photos + leaf bounding boxes)
  --plantdoc-test    agyaatcoder/PlantDoc  data/test-*.parquet    (held out, used only for evaluation)
  --plantvillage     BrandonFors/Plant-Diseases-PlantVillage-Dataset data/test-*.parquet (replay, to keep lab accuracy)

Run (CPU, ~30 min):  python scripts/finetune_fieldphotos.py --plantdoc-train a.parquet b.parquet --plantdoc-test t.parquet --plantvillage pv.parquet
Then export:          python scripts/export_onnx.py --weights finetuned/
"""
import argparse
import collections
import io
import json
import os
import random
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
import numpy as np  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402
from torchvision import transforms as T  # noqa: E402
from transformers import AutoModelForImageClassification  # noqa: E402

MODEL_ID = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
# PlantDoc category -> PlantVillage model label
PD2PV = {
    "Apple Scab Leaf": "Apple Scab", "Apple leaf": "Healthy Apple", "Apple rust leaf": "Cedar Apple Rust",
    "Bell_pepper leaf": "Healthy Bell Pepper Plant", "Bell_pepper leaf spot": "Bell Pepper with Bacterial Spot",
    "Blueberry leaf": "Healthy Blueberry Plant", "Cherry leaf": "Healthy Cherry Plant",
    "Corn Gray leaf spot": "Corn (Maize) with Cercospora and Gray Leaf Spot", "Corn leaf blight": "Corn (Maize) with Northern Leaf Blight",
    "Corn rust leaf": "Corn (Maize) with Common Rust", "Peach leaf": "Healthy Peach Plant",
    "Potato leaf early blight": "Potato with Early Blight", "Potato leaf late blight": "Potato with Late Blight",
    "Raspberry leaf": "Healthy Raspberry Plant", "Soyabean leaf": "Healthy Soybean Plant", "Soybean leaf": "Healthy Soybean Plant",
    "Squash Powdery mildew leaf": "Squash with Powdery Mildew", "Strawberry leaf": "Healthy Strawberry Plant",
    "Tomato Early blight leaf": "Tomato with Early Blight", "Tomato Septoria leaf spot": "Tomato with Septoria Leaf Spot",
    "Tomato leaf": "Healthy Tomato Plant", "Tomato leaf bacterial spot": "Tomato with Bacterial Spot",
    "Tomato leaf late blight": "Tomato with Late Blight", "Tomato leaf mosaic virus": "Tomato Mosaic Virus",
    "Tomato leaf yellow virus": "Tomato Yellow Leaf Curl Virus", "Tomato mold leaf": "Tomato with Leaf Mold",
    "Tomato two spotted spider mites leaf": "Tomato with Spider Mites or Two-spotted Spider Mite",
    "grape leaf": "Healthy Grape Plant", "grape leaf black rot": "Grape with Black Rot",
}


def shrink(im, short=320):
    w, h = im.size
    k = short / min(w, h)
    return im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.BILINEAR) if k < 1 else im


def load_plantdoc(paths, lab2id, crops_per_image=2, min_box=64, val_frac=0.0):
    """Whole field photos (majority label) + leaf crops from bounding boxes. Optionally holds out whole photos for validation."""
    out, val = [], []
    for p in paths:
        t = pq.read_table(p, columns=["image", "objects"])
        for img, obj in zip(t.column("image").to_pylist(), t.column("objects").to_pylist()):
            cats = [c for c in obj["category"] if c in PD2PV]
            if not cats:
                continue
            im = Image.open(io.BytesIO(img["bytes"])).convert("RGB")
            whole = (shrink(im), lab2id[PD2PV[collections.Counter(cats).most_common(1)[0][0]]])
            if random.random() < val_frac:
                val.append(whole)
                continue
            out.append(whole)
            boxes = [(b, c) for b, c in zip(obj["bbox"], obj["category"]) if c in PD2PV and min(b[2], b[3]) >= min_box]
            random.shuffle(boxes)
            for (x, y, w, h), c in boxes[:crops_per_image]:  # COCO bbox: x, y, w, h
                m = 0.1 * max(w, h)
                out.append((shrink(im.crop((max(0, x - m), max(0, y - m), x + w + m, y + h + m))), lab2id[PD2PV[c]]))
    return out, val


def load_plantvillage(path, per_class):
    t = pq.read_table(path)
    by = collections.defaultdict(list)
    for i, lab in enumerate(t.column("label").to_pylist()):
        by[lab].append(i)
    col, train, held = t.column("image"), [], []
    for lab, idx in by.items():
        random.shuffle(idx)
        for k, i in enumerate(idx[: per_class + 10]):  # first 10 per class are always held out
            item = (shrink(Image.open(io.BytesIO(col[i].as_py()["bytes"])).convert("RGB")), lab)
            (held if k < 10 else train).append(item)
    return train, held


class DS(torch.utils.data.Dataset):
    def __init__(self, items, tf):
        self.items, self.tf = items, tf

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        im, y = self.items[i]
        return self.tf(im), y


NORM = T.Normalize([0.5] * 3, [0.5] * 3)
TRAIN_TF = T.Compose([T.RandomResizedCrop(224, scale=(0.35, 1.0)), T.RandomHorizontalFlip(), T.RandomVerticalFlip(0.2),
                      T.RandomRotation(20), T.ColorJitter(0.3, 0.3, 0.3, 0.03), T.ToTensor(), NORM])
EVAL_TF = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(), NORM])  # same as the app


@torch.no_grad()
def evaluate(model, items, crop_of):
    model.eval()
    ok = crop_ok = conf = conf_ok = 0
    for i in range(0, len(items), 64):
        batch = items[i:i + 64]
        p = model(torch.stack([EVAL_TF(im) for im, _ in batch])).logits.softmax(-1)
        s, pred = p.max(-1)
        for (_, y), pr, sc in zip(batch, pred.tolist(), s.tolist()):
            ok += pr == y
            crop_ok += crop_of[pr] == crop_of[y]
            if sc >= 0.6:
                conf += 1
                conf_ok += pr == y
    n = len(items)
    return {"top1": round(ok / n, 3), "crop": round(crop_ok / n, 3), "confident_share": round(conf / n, 3), "confident_precision": round(conf_ok / max(conf, 1), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plantdoc-train", nargs="+", required=True)
    ap.add_argument("--plantdoc-test", required=True)
    ap.add_argument("--plantvillage", required=True)
    ap.add_argument("--pv-per-class", type=int, default=150)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "finetuned"))
    a = ap.parse_args()
    random.seed(0)
    torch.manual_seed(0)
    torch.set_num_threads(os.cpu_count())

    model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
    lab2id = {v: int(k) for k, v in model.config.id2label.items()}
    crop_of = {i: json.load(open(Path(__file__).resolve().parent.parent / "data" / "class_map.json"))[l]["crop"] for l, i in lab2id.items()}

    t0 = time.time()
    pd_train, pd_val = load_plantdoc(a.plantdoc_train, lab2id, val_frac=0.12)
    pd_test, _ = load_plantdoc([a.plantdoc_test], lab2id, crops_per_image=0)  # whole photos only, like a farmer's upload
    pv_train, pv_held = load_plantvillage(a.plantvillage, a.pv_per_class)
    print(f"data: plantdoc train {len(pd_train)} / val {len(pd_val)} / test {len(pd_test)}, plantvillage train {len(pv_train)} / held {len(pv_held)} ({time.time()-t0:.0f}s)", flush=True)

    report = {"before": {"plantdoc_test": evaluate(model, pd_test, crop_of), "plantvillage_held": evaluate(model, pv_held, crop_of)}}
    print("before", report["before"], flush=True)

    dl = torch.utils.data.DataLoader(DS(pd_train + pv_train, TRAIN_TF), batch_size=32, shuffle=True, num_workers=3, persistent_workers=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.epochs * len(dl), pct_start=0.15)
    best, report["epochs"] = -1, []
    def train_mode():
        # Keep BatchNorm running stats frozen: mixing field + lab photos otherwise shifts them and
        # destroys accuracy on clean photos (catastrophic drift we saw in an earlier run).
        model.train()
        for m in model.modules():
            if isinstance(m, torch.nn.BatchNorm2d):
                m.eval()

    for ep in range(a.epochs):
        train_mode()
        tot = n = 0
        for x, y in dl:
            loss = torch.nn.functional.cross_entropy(model(x).logits, y, label_smoothing=0.1)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            tot, n = tot + loss.item() * len(y), n + len(y)
        r = {"epoch": ep + 1, "loss": round(tot / n, 3), "plantdoc_val": evaluate(model, pd_val, crop_of), "plantdoc_test": evaluate(model, pd_test, crop_of), "plantvillage_held": evaluate(model, pv_held, crop_of)}
        report["epochs"].append(r)
        print(r, f"({time.time()-t0:.0f}s)", flush=True)
        score = r["plantdoc_val"]["top1"] + r["plantvillage_held"]["top1"]
        if score > best:  # select on validation; the test split is only reported
            best = score
            model.save_pretrained(a.out)
            report["best"] = r
    Path(a.out, "training_report.json").write_text(json.dumps(report, indent=1))
    print("best", report["best"])


if __name__ == "__main__":
    main()
