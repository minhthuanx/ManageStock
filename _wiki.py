"""
Wiki integration — Steal a Brainrot fandom wiki.

Fetches the canonical pet name list from the fandom API, caches it to a JSON
file (7-day TTL), and provides fuzzy name normalization for AI Vision results.

The pet list is used to:
  1. Constrain the AI vision prompt to real pet names.
  2. Post-correct OCR-ish typos from the model (e.g. "Tung Tung Sahur" -> "Tung Tung Tung Sahur").
"""
import os
import re
import json
import time
from difflib import SequenceMatcher

import requests

WIKI_API = "https://stealabrainrot.fandom.com/api.php"
CACHE_FILE = "wiki_pets_cache.json"
CACHE_TTL = 7 * 24 * 3600  # 7 days

# Categories that are not individual pets (meta pages) — keep out of the list.
_META_RE = re.compile(
    r"(disambiguation|/gallery|^user:|^user blog:|^file:|^category:|"
    r"brainrot god$|brainrot trader$|^brainrots$|^duo brainrots$|"
    r"^taco brainrots$|^red carpet$|^leaks$|^legendary$|^rebirth$|"
    r"^newformatting$|^unused content$|^update log|^family$|family$)", re.I
)


def _fetch_pet_titles() -> list:
    """Fetch all page titles in Category:Brainrots via the fandom API."""
    titles = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Brainrots",
            "cmlimit": "500",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        r = requests.get(WIKI_API, params=params, timeout=15,
                         headers={"User-Agent": "ManageStockApp/1.0 (pet inventory helper)"})
        r.raise_for_status()
        data = r.json()
        for m in data.get("query", {}).get("categorymembers", []):
            titles.append(m["title"])
        cont = data.get("continue")
        if not cont:
            break
        cmcontinue = cont.get("cmcontinue")
    return titles


def _clean_titles(titles: list) -> list:
    """Filter out meta pages / user pages, normalize whitespace & accents."""
    out = []
    for t in titles:
        t = (t or "").strip()
        if not t or _META_RE.search(t):
            continue
        t = re.sub(r"\s+", " ", t).strip()
        if t and t not in out:
            out.append(t)
    return out


def _load_cache() -> dict | None:
    """Return cached data if fresh, else None."""
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("fetched_at", 0) > CACHE_TTL:
            return None
        return data
    except Exception:
        return None


def _save_cache(titles: list):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.time(), "titles": titles}, f, ensure_ascii=False)
    except Exception:
        pass


def get_pet_list(refresh: bool = False) -> list:
    """Return the canonical pet name list (from cache or fresh fetch).

    On fetch failure, silently falls back to the stale cache if present,
    else an empty list — the caller should degrade gracefully.
    """
    if not refresh:
        cached = _load_cache()
        if cached:
            return cached.get("titles", [])
    try:
        titles = _clean_titles(_fetch_pet_titles())
        if titles:
            _save_cache(titles)
            return titles
    except Exception:
        pass
    stale = _load_cache()  # tolerate TTL expiry — better than nothing
    return stale.get("titles", []) if stale else []


def _norm(s: str) -> str:
    """Lowercase, strip diacritics, collapse punctuation — for fuzzy matching."""
    s = (s or "").lower()
    s = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", s)
    s = re.sub(r"[èéẹẻẽêềếệểễ]", "e", s)
    s = re.sub(r"[ìíịỉĩ]", "i", s)
    s = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", s)
    s = re.sub(r"[ùúụủũưừứựửữ]", "u", s)
    s = re.sub(r"[ỳýỵỷỹ]", "y", s)
    s = re.sub(r"[đ]", "d", s)
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_pet_name(raw: str, pet_list: list, threshold: float = 0.82) -> str:
    """Best-effort correction of an AI-read pet name against the wiki list.

    Returns the exact wiki name when a fuzzy match is found, else the raw name
    unchanged. Exact (case-insensitive) matches short-circuit.
    """
    raw = (raw or "").strip()
    if not raw or not pet_list:
        return raw
    raw_l = raw.lower()
    for p in pet_list:
        if p.lower() == raw_l:
            return p
    raw_n = _norm(raw)
    if not raw_n:
        return raw
    best, best_ratio = "", 0.0
    for p in pet_list:
        ratio = SequenceMatcher(None, raw_n, _norm(p)).ratio()
        if ratio > best_ratio:
            best, best_ratio = p, ratio
    return best if best_ratio >= threshold else raw
