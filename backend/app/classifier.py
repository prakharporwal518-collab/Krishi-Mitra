"""Plant disease classifier.

Primary: Hugging Face MobileNetV2 trained on PlantVillage (38 classes), loaded with `transformers`.
Fallback: a vision LLM (Anthropic Claude) asked to choose one of the same 38 labels.
"""
import base64
import json
import logging
import os
import re
import threading

import httpx

# Plain HTTPS downloads are more proxy-friendly than the Xet protocol
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

log = logging.getLogger("krishi.classifier")
MODEL_ID = os.getenv("HF_MODEL_ID", "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification")

_pipe = None
_error = None
_lock = threading.Lock()


class ClassifierUnavailable(Exception):
    pass


def _load():
    global _pipe, _error
    with _lock:
        if _pipe is not None or _error is not None:
            return
        try:
            import torch
            from transformers import AutoModelForImageClassification
            try:  # transformers >= 5 (PIL backend, no torchvision needed)
                from transformers import MobileNetV2ImageProcessorPil as MobileNetV2ImageProcessor
            except ImportError:
                from transformers import MobileNetV2ImageProcessor
            log.info("Loading model %s ...", MODEL_ID)
            # Explicit processor class: the repo's config names a deprecated FeatureExtractor
            proc = MobileNetV2ImageProcessor.from_pretrained(MODEL_ID)
            model = AutoModelForImageClassification.from_pretrained(MODEL_ID).eval()

            def run(img, top_k=5):
                with torch.no_grad():
                    probs = model(**proc(images=img, return_tensors="pt")).logits.softmax(-1)[0]
                vals, idx = probs.topk(top_k)
                return [{"label": model.config.id2label[int(i)], "score": float(v)} for v, i in zip(vals, idx)]

            _pipe = run
            log.info("Model loaded")
        except Exception as e:  # network / disk / missing torch
            _error = f"{type(e).__name__}: {e}"
            log.warning("Model failed to load, will use LLM fallback: %s", _error)


def warm_up_async():
    threading.Thread(target=_load, daemon=True).start()


def status():
    if _pipe is not None:
        return {"engine": "huggingface", "model": MODEL_ID, "ready": True}
    return {"engine": "llm-fallback" if _error else "loading", "error": _error,
            "llm_configured": bool(os.getenv("ANTHROPIC_API_KEY")), "ready": _error is not None and bool(os.getenv("ANTHROPIC_API_KEY"))}


def predict(img, raw_bytes, labels):
    """Return ([(label, score), ...] sorted desc, engine)."""
    _load()
    if _pipe is not None:
        out = _pipe(img, top_k=5)
        return [(o["label"], float(o["score"])) for o in out], "huggingface"
    return _llm_predict(raw_bytes, labels), "llm"


def _media_type(b):
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _llm_predict(raw, labels):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ClassifierUnavailable(f"Image model unavailable ({_error}) and no ANTHROPIC_API_KEY set for fallback.")
    prompt = ("You are a plant pathologist. Look at this leaf photo and pick the single best matching label from this list, "
              "plus a confidence between 0 and 1. If the image is not a plant leaf, use confidence 0.\n"
              f"Labels: {json.dumps(labels)}\n"
              'Reply ONLY with JSON: {"label": "<exact label>", "confidence": <number>}')
    body = {"model": os.getenv("LLM_MODEL", "claude-sonnet-5-5"), "max_tokens": 100,
            "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": _media_type(raw), "data": base64.b64encode(raw).decode()}},
                {"type": "text", "text": prompt}]}]}
    try:
        r = httpx.post("https://api.anthropic.com/v1/messages", json=body, timeout=60,
                       headers={"x-api-key": key, "anthropic-version": "2023-06-01"})
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
    except Exception as e:
        raise ClassifierUnavailable(f"Vision LLM fallback failed: {e}")
    label = data.get("label") if data.get("label") in labels else labels[-1]
    return [(label, float(data.get("confidence", 0.5)))]
