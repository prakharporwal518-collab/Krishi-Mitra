"""Optional dynamic translation (Google Cloud Translate v2) for languages without
pre-translated knowledge-base content (Telugu, Tamil, Bengali). Falls back to English."""
import copy
import logging
import os

import httpx

log = logging.getLogger("krishi.translate")
_cache: dict = {}


def _collect(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, list):
        for x in obj:
            _collect(x, out)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect(v, out)


def _replace(obj, it):
    if isinstance(obj, str):
        return next(it)
    if isinstance(obj, list):
        return [_replace(x, it) for x in obj]
    if isinstance(obj, dict):
        return {k: _replace(v, it) for k, v in obj.items()}
    return obj


async def translate_content(content: dict, lang: str):
    """Returns (content, translated: bool)."""
    key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if not key:
        return content, False
    ck = (id(content), lang)
    if ck in _cache:
        return _cache[ck], True
    texts: list = []
    _collect(content, texts)
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post("https://translation.googleapis.com/language/translate/v2", params={"key": key},
                             json={"q": texts, "target": lang, "source": "en", "format": "text"})
            r.raise_for_status()
            out = [t["translatedText"] for t in r.json()["data"]["translations"]]
        result = _replace(copy.deepcopy(content), iter(out))
        _cache[ck] = result
        return result, True
    except Exception as e:
        log.warning("Translation failed (%s); using English", e)
        return content, False
