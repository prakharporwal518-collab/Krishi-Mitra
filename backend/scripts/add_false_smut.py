"""Stage 3: teach the photo model rice false smut (a grain / panicle disease), 54 -> 55 classes.

Data: 50 unique "False Smut" field photos from minhhungg/rice-disease-dataset (data/diseases-*.parquet;
fetch the rows labelled "False Smut" into a folder). 40 are used for training (oversampled with strong
augmentation), 10 are held out. Old data is replayed so the other 54 classes keep their accuracy.

Run:  python scripts/add_false_smut.py --false-smut-dir fs/ --rice-india r.parquet --cotton c.parquet --cld-dir cld/ \
          --plantdoc-train a.parquet b.parquet --plantdoc-test t.parquet --plantvillage pv.parquet
Then: copy finetuned_fs/ to models/krishi-mobilenetv2-field/ and run scripts/export_onnx.py --weights models/krishi-mobilenetv2-field
"""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms as T

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_crops import COTTON, RICE_INDIA, grow_head, load_folders, load_parquet  # noqa: E402
from finetune_fieldphotos import DS, EVAL_TF, NORM, TRAIN_TF, evaluate, load_plantdoc, load_plantvillage, shrink  # noqa: E402
from transformers import AutoModelForImageClassification  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LABEL = "Rice with False Smut"
# false smut balls range from yellow-orange (early) to green-black (late): stronger colour jitter for this class
FS_TF = T.Compose([T.RandomResizedCrop(224, scale=(0.25, 1.0)), T.RandomHorizontalFlip(), T.RandomVerticalFlip(0.3),
                   T.RandomRotation(30), T.ColorJitter(0.4, 0.4, 0.4, 0.08), T.ToTensor(), NORM])


class Mixed(torch.utils.data.Dataset):
    def __init__(self, items):  # (image, label, transform)
        self.items = items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        im, y, tf = self.items[i]
        return tf(im), y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--false-smut-dir", required=True)
    ap.add_argument("--rice-india", required=True)
    ap.add_argument("--cotton", required=True)
    ap.add_argument("--cld-dir", required=True)
    ap.add_argument("--plantdoc-train", nargs="+", required=True)
    ap.add_argument("--plantdoc-test", required=True)
    ap.add_argument("--plantvillage", required=True)
    ap.add_argument("--base", default=str(ROOT / "models" / "krishi-mobilenetv2-field"))
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--out", default=str(ROOT / "finetuned_fs"))
    a = ap.parse_args()
    random.seed(0)
    torch.manual_seed(0)
    torch.set_num_threads(os.cpu_count())

    model = grow_head(AutoModelForImageClassification.from_pretrained(a.base), [LABEL])
    lab2id = {v: k for k, v in model.config.id2label.items()}
    cmap = json.load(open(ROOT / "data" / "class_map.json"))
    crop_of = {i: cmap[l]["crop"] for l, i in lab2id.items()}

    t0 = time.time()
    fs = sorted(Path(a.false_smut_dir).glob("*.jpg"))
    random.shuffle(fs)
    fs_test = [(shrink(Image.open(f).convert("RGB")), lab2id[LABEL]) for f in fs[:10]]
    fs_train = [(shrink(Image.open(f).convert("RGB")), lab2id[LABEL]) for f in fs[10:]]
    rice_tr, rice_te = load_parquet(a.rice_india, RICE_INDIA, lab2id, cap=120)
    cot_tr, cot_te = load_parquet(a.cotton, COTTON, lab2id, cap=60)
    cld_tr, cld_te = load_folders(a.cld_dir, lab2id, cap=100)
    pd_train, _ = load_plantdoc(a.plantdoc_train, lab2id, crops_per_image=1)
    pd_train = random.sample(pd_train, 1500)
    pd_test, _ = load_plantdoc([a.plantdoc_test], lab2id, crops_per_image=0)
    pv_train, pv_held = load_plantvillage(a.plantvillage, 30)
    old_test = rice_te + cot_te + cld_te
    items = [(im, y, FS_TF) for im, y in fs_train] * 8 + [(im, y, TRAIN_TF) for im, y in rice_tr + cot_tr + cld_tr + pd_train + pv_train]
    print(f"data: false smut train {len(fs_train)} (x8) / test {len(fs_test)}; replay {len(items) - 8 * len(fs_train)} ({time.time() - t0:.0f}s)", flush=True)

    dl = torch.utils.data.DataLoader(Mixed(items), batch_size=32, shuffle=True, num_workers=3, persistent_workers=True)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.epochs * len(dl), pct_start=0.15)
    report = {"before": {"plantdoc_test": evaluate(model, pd_test, crop_of), "plantvillage_held": evaluate(model, pv_held, crop_of),
                         "rice_wheat_cotton_test": evaluate(model, old_test, crop_of)}, "epochs": []}
    print("before", report["before"], flush=True)
    for ep in range(a.epochs):
        model.train()
        for m in model.modules():  # BatchNorm statistics stay frozen (see finetune_fieldphotos.py)
            if isinstance(m, torch.nn.BatchNorm2d):
                m.eval()
        for x, y in dl:
            loss = torch.nn.functional.cross_entropy(model(x).logits, y, label_smoothing=0.1)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
        r = {"epoch": ep + 1, "false_smut_test": evaluate(model, fs_test, crop_of), "plantdoc_test": evaluate(model, pd_test, crop_of),
             "plantvillage_held": evaluate(model, pv_held, crop_of), "rice_wheat_cotton_test": evaluate(model, old_test, crop_of)}
        report["epochs"].append(r)
        print(r, f"({time.time() - t0:.0f}s)", flush=True)
    model.save_pretrained(a.out)
    report["final"] = report["epochs"][-1]
    Path(a.out, "training_report.json").write_text(json.dumps(report, indent=1))
    print("final", json.dumps(report["final"]))


if __name__ == "__main__":
    main()
