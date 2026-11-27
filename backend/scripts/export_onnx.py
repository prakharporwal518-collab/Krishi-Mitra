"""Export the Hugging Face PlantVillage model to ONNX for in-browser inference (Netlify deploy).
Run:  python scripts/export_onnx.py [--weights finetuned/]   (needs: pip install onnx)
Writes frontend/public/model/plant_disease.onnx and labels.json
"""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
import torch  # noqa: E402
from transformers import AutoModelForImageClassification  # noqa: E402

MODEL_ID = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "model"
OUT.mkdir(parents=True, exist_ok=True)


class Wrapper(torch.nn.Module):
    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, pixel_values):
        return self.m(pixel_values=pixel_values).logits.softmax(-1)


ap = argparse.ArgumentParser()
ap.add_argument("--weights", default=MODEL_ID, help="HF model id or local folder (e.g. finetuned/)")
model = AutoModelForImageClassification.from_pretrained(ap.parse_args().weights).eval()
torch.onnx.export(Wrapper(model), torch.zeros(1, 3, 224, 224), OUT / "plant_disease.onnx",
                  input_names=["pixel_values"], output_names=["probs"], opset_version=17, dynamo=False)
labels = [model.config.id2label[i] for i in range(len(model.config.id2label))]
(OUT / "labels.json").write_text(json.dumps(labels, indent=1))
print("exported", OUT)
