"""Krishi Mitra – FastAPI backend.

Endpoints
  POST /api/predict           image -> crop, disease, confidence, disease_id
  POST /api/symptoms          {crop, symptoms[], text?} -> top 3 matches
  GET  /api/disease/{id}      ?lang=hi&state=..&season=.. -> full recommendation
  GET  /api/crops             ?lang=hi
  GET  /api/symptom-list      ?lang=hi
  GET  /api/languages
  GET  /api/health
"""
import io
import json
import logging
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent.parent
load_dotenv(BASE / ".env")

from . import classifier, translate  # noqa: E402  (after .env is loaded)
log = logging.getLogger("krishi")
logging.basicConfig(level=logging.INFO)


def _load(name):
    return json.loads((BASE / "data" / name).read_text(encoding="utf-8"))


KB = {d["id"]: d for d in _load("diseases.json")["diseases"]}
CLASS_MAP = _load("class_map.json")
_crops = _load("crops.json")
LANGS = _crops["languages"]
LANG_CODES = {l["code"] for l in LANGS}
CROPS = {c["id"]: c for c in _crops["crops"]}
_sym = _load("symptoms.json")
SYMPTOMS = {s["id"]: s for s in _sym["symptoms"]}
ALIASES = _sym["aliases"]
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.6"))
MAX_UPLOAD_MB = 8

app = FastAPI(title="Krishi Mitra API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _warm():
    classifier.warm_up_async()


# ---------------- helpers ----------------
def _lang(lang: str) -> str:
    return lang if lang in LANG_CODES else "en"


def crop_name(crop_id: str, lang: str) -> str:
    c = CROPS.get(crop_id)
    return c["names"].get(lang, c["names"]["en"]) if c else crop_id.title()


def disease_name(did: str, lang: str) -> str:
    content = KB[did]["content"]
    return content.get(lang, content["en"])["name"]


def ui_tags(d) -> set:
    return {ALIASES.get(t, t) for t in d["symptom_tags"]} & SYMPTOMS.keys()


# ---------------- basic endpoints ----------------
@app.get("/api/health")
def health():
    return {"status": "ok", "model": classifier.status(), "diseases": len(KB)}


@app.get("/api/languages")
def languages():
    return LANGS


@app.get("/api/crops")
def crops(lang: str = "en", all: bool = False):
    lang = _lang(lang)
    return [{"id": c["id"], "icon": c["icon"], "name": crop_name(c["id"], lang), "main": c["main"]}
            for c in CROPS.values() if all or c["main"] or any(d["crop"] == c["id"] for d in KB.values())]


@app.get("/api/symptom-list")
def symptom_list(lang: str = "en", crop: str | None = None):
    lang = _lang(lang)
    relevant = set().union(*(ui_tags(d) for d in KB.values() if d["crop"] == crop)) if crop else set(SYMPTOMS)
    return [{"id": s["id"], "icon": s["icon"], "name": s["names"].get(lang, s["names"]["en"])}
            for s in SYMPTOMS.values() if s["id"] in relevant]


# ---------------- image prediction ----------------
@app.post("/api/predict")
async def predict(file: UploadFile = File(...), lang: str = "en"):
    lang = _lang(lang)
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file. Please upload a leaf photo.")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Image too large (max {MAX_UPLOAD_MB} MB).")
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "This file is not a valid image (use JPG or PNG).")

    try:
        preds, engine = classifier.predict(img, data, list(CLASS_MAP))
    except classifier.ClassifierUnavailable as e:
        raise HTTPException(503, str(e))

    def enrich(label, score):
        m = CLASS_MAP.get(label, {"crop": "unknown", "disease_id": "healthy"})
        return {"label": label, "crop": m["crop"], "crop_name": crop_name(m["crop"], lang),
                "disease_id": m["disease_id"],
                "disease": "Not a plant leaf" if m["disease_id"] == "invalid" else disease_name(m["disease_id"], lang),
                "confidence": round(score * 100, 1)}

    top = [enrich(l, s) for l, s in preds[:4]]
    best = top[0]
    not_leaf = best["disease_id"] == "invalid"  # model's "Not a Plant Leaf" class
    return {**best, "is_healthy": best["disease_id"] == "healthy", "not_leaf": not_leaf,
            "low_confidence": not_leaf or best["confidence"] < MIN_CONFIDENCE * 100,
            "alternatives": [x for x in top[1:] if x["disease_id"] != "invalid"][:2], "engine": engine}


# ---------------- symptom matching ----------------
class SymptomQuery(BaseModel):
    crop: str
    symptoms: list[str] = []
    text: str | None = None  # free text from voice input
    lang: str = "en"


def symptoms_from_text(text: str) -> set:
    t = text.lower()
    return {s["id"] for s in SYMPTOMS.values() if any(k.lower() in t for k in s["kw"])}


@app.post("/api/symptoms")
def match_symptoms(q: SymptomQuery):
    lang = _lang(q.lang)
    selected = {ALIASES.get(s, s) for s in q.symptoms} & SYMPTOMS.keys()
    if q.text:
        selected |= symptoms_from_text(q.text)
    if not selected:
        raise HTTPException(400, "Please select or speak at least one symptom.")
    candidates = [d for d in KB.values() if d["crop"] == q.crop]
    if not candidates:
        raise HTTPException(404, f"No diseases found for crop '{q.crop}'.")
    results = []
    for d in candidates:
        tags = ui_tags(d)
        hit = selected & tags
        if not hit:
            continue
        score = len(hit) / math.sqrt(len(selected) * len(tags))  # cosine similarity
        results.append({"disease_id": d["id"], "disease": disease_name(d["id"], lang), "crop": d["crop"],
                        "crop_name": crop_name(d["crop"], lang), "score": round(score * 100),
                        "matched": [SYMPTOMS[s]["names"].get(lang, SYMPTOMS[s]["names"]["en"]) for s in sorted(hit)]})
    results.sort(key=lambda r: -r["score"])
    return {"detected_symptoms": sorted(selected), "matches": results[:3]}


# ---------------- disease detail ----------------
@app.get("/api/disease/{disease_id}")
async def disease(disease_id: str, lang: str = "en", state: str | None = None,
                  season: str | None = Query(None, pattern="^(kharif|rabi|zaid)?$"), crop: str | None = None):
    lang = _lang(lang)
    d = KB.get(disease_id)
    if not d:
        raise HTTPException(404, "Disease not found")
    content, translated = d["content"].get(lang), True
    if content is None:  # te / ta / bn: try dynamic translation, else English
        content, translated = await translate.translate_content(d["content"]["en"], lang)
    tips = []
    for t in d["region_tips"]:
        if (not state or state in t["states"]) and (not season or season in t["seasons"]):
            tips.append({"states": t["states"], "seasons": t["seasons"], "tip": t["tip"].get(lang) or t["tip"]["en"]})
    crop_id = crop if d["crop"] == "any" and crop else d["crop"]
    return {"id": d["id"], "crop": crop_id, "crop_name": crop_name(crop_id, lang), "kind": d["kind"],
            "pathogen": d["pathogen"], "source": d["source"], "lang": lang if translated else "en",
            "translated": translated, **content, "region_tips": tips,
            "region_match": bool(state or season) and bool(tips)}


SAMPLES = BASE.parent / "samples"
if SAMPLES.exists():
    app.mount("/samples", StaticFiles(directory=SAMPLES), name="samples")

# ---------------- serve built frontend (optional, for single-port demo) ----------------
DIST = BASE.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
