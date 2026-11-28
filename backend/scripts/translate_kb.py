"""Machine-translate the knowledge base into Telugu, Tamil and Bengali with Meta's open NLLB-200 model
(free, runs locally on CPU, no API key). Hindi and Marathi stay hand-written in build_kb.py.

Writes backend/data/kb_auto_translations.json  ({lang: {english text: translation}}). Already-translated
strings are kept, so re-running only translates new text. Then run:  python scripts/build_kb.py
Run:  python scripts/translate_kb.py      (first run downloads the ~2.5 GB model)
"""
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "kb_auto_translations.json"
MODEL = "facebook/nllb-200-distilled-600M"
LANGS = {"te": "tel_Telu", "ta": "tam_Taml", "bn": "ben_Beng"}


def english_strings():
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_kb  # noqa: F401  (building also defines D, SAFETY, WARNING)
    out = set(build_kb.SAFETY["en"]) | {build_kb.WARNING["en"]}
    kb = json.loads((ROOT / "data" / "diseases.json").read_text(encoding="utf-8"))["diseases"]
    for d in kb:
        c = d["content"]["en"]
        out |= {c["name"], c["about"], c["chemical"]["dosage"], c["chemical"]["timing"], *c["symptoms"], *c["organic"], *c["prevention"]}
        out |= {t["tip"]["en"] for t in d["region_tips"]}
    return sorted(s for s in out if s.strip() and s != "—")


def main():
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    torch.set_num_threads(os.cpu_count())
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    texts = english_strings()
    tok = AutoTokenizer.from_pretrained(MODEL, src_lang="eng_Latn")
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).eval()
    t0 = time.time()
    for lang, code in LANGS.items():
        cache = done.setdefault(lang, {})
        todo = [s for s in texts if s not in cache]
        print(f"{lang}: {len(todo)} strings to translate", flush=True)
        for i in range(0, len(todo), 16):
            batch = todo[i:i + 16]
            enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=256)
            with torch.no_grad():
                gen = model.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(code), num_beams=3, max_new_tokens=256)
            for src, out in zip(batch, tok.batch_decode(gen, skip_special_tokens=True)):
                out = "".join(str(unicodedata.digit(ch)) if ch.isdigit() else ch for ch in out)  # native digits -> 0-9
                # keep numbers intact: if the model dropped a number, fall back to English for that string
                cache[src] = out if set(re.findall(r"\d+(?:\.\d+)?", src)) <= set(re.findall(r"\d+(?:\.\d+)?", out)) else src
            OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {lang} {i + len(batch)}/{len(todo)} ({time.time() - t0:.0f}s)", flush=True)
    print("done")


if __name__ == "__main__":
    main()
