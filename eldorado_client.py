"""
Eldorado.gg API Client — pure Python (no JS server dependency).
Manages cookie auth, listing CRUD, image upload for "Steal a Brainrot" (game 259).
"""

import json
import os
import re
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode

import requests as _requests

# ─── Constants ───────────────────────────────────────────────────────────────

BASE = "https://www.eldorado.gg/api"
GAME_ID = "259"
CATEGORY = "CustomItem"

COOKIE_FILE = ".eldorado_cookies.enc"
VAULT_KEY_FILE = ".eldorado_key"

DELIVERY_MAP = {
    "5 min": "Minute5",
    "10 min": "Minute10",
    "20 min": "Minute20",
    "30 min": "Minute30",
    "1 hour": "Hour1",
    "2 hours": "Hour2",
    "4 hours": "Hour4",
    "8 hours": "Hour8",
    "12 hours": "Hour12",
    "24 hours": "Hour24",
}
DELIVERY_REV = {v: k for k, v in DELIVERY_MAP.items()}

MUTATION_EMOJI = {
    "cursed": "\U0001f52e",
    "divine": "✨",
    "gold": "⭐",
    "diamond": "\U0001f48e",
    "bloodrot": "\U0001fa78",
    "candy": "\U0001f36c",
    "lava": "\U0001f30b",
    "galaxy": "\U0001f30c",
    "yin-yang": "☯️",
    "radioactive": "☢️",
    "rainbow": "\U0001f308",
    "celestial": "\U0001f31f",
    "frozen": "❄️",
    "shadow": "\U0001f311",
    "blazing": "\U0001f525",
    "toxic": "☠️",
    "electric": "⚡",
    "void": "\U0001f573️",
    "phantom": "\U0001f47b",
    "cyber": "\U0001f916",
}
ZAP = "⚡"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

HEADERS_BASE = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://www.eldorado.gg",
    "Referer": "https://www.eldorado.gg/",
}

# MS bracket mapping (mirrors server.js genToMs fallback, thresholds in RAW units)
_MS_BRACKETS = [
    (20_000_000_000, "20-plus-bs"),   # 20B
    (10_000_000_000, "10-1999-bs"),   # 10B
    (5_000_000_000, "5-999-bs"),      # 5B
    (1_000_000_000, "1-499-bs"),      # 1B
    (750_000_000, "750-99999-ms"),    # 750M
    (500_000_000, "500-74999-ms"),    # 500M
    (250_000_000, "250-49999-ms"),    # 250M
    (100_000_000, "100-24999-ms"),    # 100M
    (50_000_000, "50-9999-ms"),       # 50M
    (25_000_000, "25-4999-ms"),       # 25M
    (1_000_000, "1-2499-ms"),         # 1M
    (1_000, "0-99999-ks"),            # 1K
]


# ─── Vault (AES-256-GCM encryption for cookie persistence) ──────────────────

class Vault:
    """AES-256-GCM encrypt/decrypt for cookie persistence using pycryptodome."""
    def __init__(self, key_hex=None):
        if key_hex is None:
            key_hex = self._load_or_create_key()
        self._key = bytes.fromhex(key_hex)

    def _load_or_create_key(self):
        p = Path(VAULT_KEY_FILE)
        if p.exists():
            return p.read_text().strip()
        import secrets
        key = secrets.token_hex(32)
        p.write_text(key)
        return key

    def seal(self, plaintext):
        if not plaintext:
            return b""
        from Crypto.Cipher import AES
        nonce = os.urandom(12)
        cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce)
        ct = cipher.encrypt(plaintext.encode())
        tag = cipher.digest()
        # Store as: nonce(12) + authTag(16) + ciphertext
        return nonce + tag + ct

    def open(self, data):
        if not data:
            return ""
        try:
            from Crypto.Cipher import AES
            nonce = data[:12]
            tag = data[12:28]
            ct = data[28:]
            cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ct, tag).decode()
        except Exception:
            return ""


# ─── EldoradoClient ──────────────────────────────────────────────────────────

class EldoradoClient:
    CLIENT_VERSION = 3  # bump khi class thay đổi method signature

    def __init__(self, log_fn=None):
        self._vault = Vault()
        self._log = log_fn or (lambda msg: print(msg))

        # Cookie state
        self._raw = ""
        self._xsrf = ""
        self.device_id = ""
        self.session_id = ""
        self._headers = dict(HEADERS_BASE)

        # Auth state
        self.logged_in = False
        self.username = ""
        self.userId = ""
        self.avatar = ""
        self.feedback = 0
        self.pos = 0
        self.neg = 0
        self.last_auth_error = None
        self.talk_token = ""

        # Game cache
        self._game_cache = {"envs": [], "attrs": [], "loaded": False}

        # Session
        self._session = _requests.Session()

        # Load persisted cookies
        self._load_cookies()

    # ── Cookie handling ──────────────────────────────────────────────────

    def set_cookies(self, raw):
        """Parse raw cookie string. Extract XSRF/session/device. Force USD."""
        parts = []
        has_currency = False
        for piece in raw.split(";"):
            piece = piece.strip()
            if "=" not in piece:
                continue
            k, _, v = piece.partition("=")
            k, v = k.strip(), v.strip()
            if k.lower() == "eldoradogg_currencypreference":
                parts.append(f"{k}=USD")
                has_currency = True
            else:
                parts.append(f"{k}={v}")
            if k == "__Host-XSRF-TOKEN":
                self._xsrf = v
            elif k == "x-session-id":
                self.session_id = v
                self._headers["X-Session-Id"] = v
            elif k == "x-device-id":
                self.device_id = v
        if not has_currency:
            parts.append("eldoradogg_currencyPreference=USD")
        self._raw = "; ".join(parts)
        if self._xsrf:
            self._headers["X-XSRF-Token"] = self._xsrf

    def _cookies_dict(self):
        d = {}
        for piece in self._raw.split(";"):
            piece = piece.strip()
            if "=" in piece:
                k, _, v = piece.partition("=")
                d[k.strip()] = v.strip()
        return d

    def save_cookies(self):
        if self._raw:
            Path(COOKIE_FILE).write_bytes(self._vault.seal(self._raw))

    def _load_cookies(self):
        p = Path(COOKIE_FILE)
        if p.exists():
            try:
                raw = self._vault.open(p.read_bytes())
                if raw:
                    self.set_cookies(raw)
            except Exception:
                pass

    # ── Core HTTP ────────────────────────────────────────────────────────

    def _req(self, method, path, *, retries=2, json_data=None, params=None,
             data=None, extra_headers=None, timeout=30, is_refresh=False):
        url = path if path.startswith("http") else BASE + path
        if params:
            qs = urlencode({k: v for k, v in params.items() if v is not None})
            url += ("&" if "?" in url else "?") + qs

        headers = dict(self._headers)
        if extra_headers:
            headers.update(extra_headers)
        headers["Cookie"] = self._raw

        kwargs = {"method": method, "url": url, "headers": headers, "timeout": timeout}
        if json_data is not None:
            kwargs["json"] = json_data
        if data is not None:
            kwargs["data"] = data

        try:
            resp = self._session.request(**kwargs)
        except _requests.exceptions.Timeout:
            return {"error": "Request timed out", "status": 0}
        except _requests.exceptions.ConnectionError as e:
            return {"error": f"Connection error: {e}", "status": 0}

        # ── Update cookies from Set-Cookie ──
        cookies_dict = self._cookies_dict()
        changed = False
        for header_val in resp.headers.get("Set-Cookie", "").split(","):
            header_val = header_val.strip()
            if "=" not in header_val:
                continue
            kv = header_val.split(";")[0].strip()
            if "=" not in kv:
                continue
            ck, _, cv = kv.partition("=")
            ck, cv = ck.strip(), cv.strip()
            if cookies_dict.get(ck) != cv:
                cookies_dict[ck] = cv
                changed = True
        # Also handle multiple Set-Cookie headers
        if hasattr(resp.headers, "get_list"):
            for sc in resp.headers.get_list("Set-Cookie"):
                if "=" not in sc:
                    continue
                kv = sc.split(";")[0].strip()
                if "=" not in kv:
                    continue
                ck, _, cv = kv.partition("=")
                ck, cv = ck.strip(), cv.strip()
                if cookies_dict.get(ck) != cv:
                    cookies_dict[ck] = cv
                    changed = True
        if changed:
            new_raw = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())
            self.set_cookies(new_raw)

        # ── Handle status codes ──
        status = resp.status_code

        if status == 401 and retries > 0 and not is_refresh:
            self._log("[AUTH] 401 — attempting token refresh...")
            if self.refresh_tokens():
                return self._req(method, path, retries=retries - 1, json_data=json_data,
                                 params=params, data=data, extra_headers=extra_headers,
                                 timeout=timeout)
            self.logged_in = False
            return {"error": "Unauthorized — session expired", "status": 401}

        if status == 401:
            self.logged_in = False
            return {"error": "Unauthorized", "status": 401}

        if status == 403:
            txt = resp.text[:200] if resp.text else ""
            return {"error": f"Forbidden: {txt}", "status": 403}

        if status == 404:
            return {"error": "Not found", "status": 404}

        if status == 429 and retries > 0:
            retry_after = int(resp.headers.get("Retry-After", "5"))
            self._log(f"[429] Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            return self._req(method, path, retries=retries - 1, json_data=json_data,
                             params=params, data=data, extra_headers=extra_headers,
                             timeout=timeout)

        if status == 204:
            return {"success": True}

        if status >= 400:
            txt = resp.text[:300] if resp.text else ""
            return {"error": f"{status}: {txt}", "status": status}

        # ── Parse response ──
        text = resp.text
        if not text:
            return {"success": True}

        if text.lstrip().startswith("<"):
            if retries > 0:
                self._log("[HTML] Cloudflare challenge, retrying in 3s...")
                time.sleep(3)
                return self._req(method, path, retries=retries - 1, json_data=json_data,
                                 params=params, data=data, extra_headers=extra_headers,
                                 timeout=timeout, is_refresh=is_refresh)
            return {"error": "API returned HTML (Cloudflare challenge)", "status": status}

        try:
            return resp.json()
        except (json.JSONDecodeError, ValueError):
            return {"error": f"Non-JSON response: {text[:100]}", "status": status}

    # ── Auth ─────────────────────────────────────────────────────────────

    def refresh_tokens(self):
        """Refresh auth tokens. Returns True on success."""
        cookies = self._cookies_dict()
        refresh_token = cookies.get("__Host-EldoradoRefreshToken")
        if not refresh_token:
            self._log("[TOKEN] No refresh token available")
            return False

        minimal_cookies = (
            f"__Host-EldoradoRefreshToken={refresh_token}; "
            f"__Host-XSRF-TOKEN={self._xsrf or ''}"
        )
        headers = dict(self._headers)
        headers["X-XSRF-Token"] = self._xsrf or ""
        headers["X-Device-Id"] = self.device_id or ""
        headers["Cookie"] = minimal_cookies

        try:
            resp = self._session.post(
                BASE + "/authentication/refreshTokens",
                headers=headers,
                json={},
                timeout=10,
            )
        except Exception as e:
            self._log(f"[TOKEN] Refresh error: {e}")
            return False

        if not resp.ok:
            self._log(f"[TOKEN] Refresh failed: HTTP {resp.status_code}")
            return False

        # Check for new IdToken in Set-Cookie
        cookies_dict = self._cookies_dict()
        has_id_token = False
        for sc in resp.headers.get("Set-Cookie", "").split(","):
            kv = sc.split(";")[0].strip()
            if "=" in kv:
                ck, _, cv = kv.partition("=")
                ck, cv = ck.strip(), cv.strip()
                if ck == "__Host-EldoradoIdToken":
                    has_id_token = True
                cookies_dict[ck] = cv
        if hasattr(resp.headers, "get_list"):
            for sc in resp.headers.get_list("Set-Cookie"):
                kv = sc.split(";")[0].strip()
                if "=" in kv:
                    ck, _, cv = kv.partition("=")
                    ck, cv = ck.strip(), cv.strip()
                    if ck == "__Host-EldoradoIdToken":
                        has_id_token = True
                    cookies_dict[ck] = cv

        if not has_id_token:
            self._log("[TOKEN] No new IdToken in response")
            return False

        new_raw = "; ".join(f"{k}={v}" for k, v in cookies_dict.items())
        self.set_cookies(new_raw)
        self.logged_in = True
        self._log("[TOKEN] Refreshed successfully")
        return True

    def check_auth(self):
        """Validate cookies and fetch user profile.
        Returns dict with ok, username, pos, neg, etc."""
        self.last_auth_error = None

        # Try authorize endpoint first
        r1 = self._req("GET", "/conversations/me/authorize")
        if isinstance(r1, dict) and "token" in r1:
            self.talk_token = r1["token"]
            self.logged_in = True
            self._profile()
            return {"ok": True, "username": self.username, "pos": self.pos,
                    "neg": self.neg, "userId": self.userId}

        # Fallback: notifications endpoint
        r2 = self._req("GET", "/notifications/me/unreadCount")
        if isinstance(r2, dict) and "unreadNotificationCount" in r2:
            self.logged_in = True
            self._profile()
            return {"ok": True, "username": self.username, "pos": self.pos,
                    "neg": self.neg, "userId": self.userId}

        self.last_auth_error = (
            r1.get("error", "") if isinstance(r1, dict) else ""
        ) or (
            r2.get("error", "") if isinstance(r2, dict) else ""
        ) or "Auth failed"
        self.logged_in = False
        return {"ok": False, "error": self.last_auth_error}

    def _profile(self):
        """Fetch user profile info after successful auth."""
        r1 = self._req("GET", "/orders/me/reviews",
                        params={"pageDirection": "Next", "pageSize": "1"})
        if isinstance(r1, dict) and "userOrderInfo" in r1:
            info = r1["userOrderInfo"]
            self.userId = info.get("userId", "")
            self.feedback = info.get("feedbackScore", 0)
            self.pos = info.get("positiveCount", 0)
            self.neg = info.get("negativeCount", 0)

        r2 = self._req("GET", "/users/me")
        if isinstance(r2, dict) and not r2.get("error"):
            self.username = r2.get("username", "")
            pic = r2.get("picture", {}) or {}
            self.avatar = pic.get("smallPicture") or pic.get("mediumPicture") or pic.get("largePicture") or ""

    # ── Game cache ───────────────────────────────────────────────────────

    def ensure_game_cache(self):
        """Load trade environments and attributes. Returns True on success."""
        if self._game_cache["loaded"] and self._game_cache["envs"]:
            return True

        self._log("[GAME] Loading game data...")

        lib = self._req("GET", f"/library/{GAME_ID}/{CATEGORY}", params={"locale": "en-US"})
        if isinstance(lib, dict) and lib.get("error"):
            return False

        attrs_resp = self._req("GET", f"/library/{GAME_ID}/{CATEGORY}/attributes/offers",
                               params={"locale": "en-US"})

        # Flatten trade environments
        raw_envs = (lib or {}).get("tradeEnvironments") or (lib or {}).get("environments") or []
        flat = []
        self._flatten_envs(raw_envs, [], flat)

        # Parse attributes
        attrs_raw = attrs_resp if isinstance(attrs_resp, list) else (attrs_resp or {}).get("attributes", [])
        attrs = []
        for a in attrs_raw:
            attrs.append({
                "id": a.get("id", ""),
                "name": a.get("name") or a.get("displayName", ""),
                "type": a.get("type") or ("Select" if a.get("selectValues") else "Numeric"),
                "isRequired": bool(a.get("isRequired")),
                "minValue": a.get("minValue"),
                "maxValue": a.get("maxValue"),
                "values": [
                    {"id": v.get("id", ""), "name": v.get("name") or v.get("displayName", "")}
                    for v in (a.get("selectValues") or a.get("attributeValues") or [])
                ],
            })

        self._game_cache["envs"] = flat
        self._game_cache["attrs"] = attrs
        self._game_cache["loaded"] = len(flat) > 0
        self._log(f"[GAME] Loaded: {len(flat)} envs, {len(attrs)} attrs")
        return self._game_cache["loaded"]

    def _flatten_envs(self, envs, parent_parts, out):
        for env in envs:
            parts = parent_parts + [env.get("value") or env.get("name", "")]
            children = env.get("childTradeEnvironments") or []
            if not children:
                out.append({
                    "id": env.get("id", ""),
                    "parts": parts,
                    "label": " | ".join(parts),
                })
            else:
                self._flatten_envs(children, parts, out)

    def find_env(self, name, rarity="", index=""):
        """Fuzzy-match an item name against cached trade environments.
        Matches server.js findEnv priority order."""
        if not self._game_cache["loaded"]:
            return None

        def norm(s):
            return re.sub(r"[^a-z0-9\s]", "", (s or "").lower().replace("&", "and")).strip()

        name_n = norm(name)
        rarity_n = norm(rarity)
        index_n = norm(index)

        # 1. name_rarity 2-part key — matches JS envLookupRR
        if rarity_n:
            key2 = name_n + "_" + rarity_n
            for env in self._game_cache["envs"]:
                parts = env["parts"]
                if len(parts) >= 2:
                    env_key = norm(parts[-1]) + "_" + norm(parts[-2])
                    if env_key == key2:
                        return env

        # 2. Exact last-part match — matches JS envLookup
        for env in self._game_cache["envs"]:
            parts = env["parts"]
            if not parts:
                continue
            last = norm(parts[-1])
            if last == name_n:
                return env

        # 3. Index fallback — matches JS: if not found && index → v337[normName(index)]
        if index_n:
            for env in self._game_cache["envs"]:
                parts = env["parts"]
                if not parts:
                    continue
                last = norm(parts[-1])
                if last == index_n:
                    return env

        # 4. Substring match (name vs last part)
        for env in self._game_cache["envs"]:
            last = norm(env["parts"][-1] if env["parts"] else "")
            if last and (last in name_n or name_n in last):
                return env

        # 5. Word overlap (>= 2 words)
        name_words = set(name_n.split())
        if len(name_words) >= 2:
            best_score = 0
            best_env = None
            for env in self._game_cache["envs"]:
                env_words = set(norm(env["label"]).split())
                overlap = len(name_words & env_words)
                if overlap > best_score:
                    best_score = overlap
                    best_env = env
            if best_score >= 2:
                return best_env

        return None

    # ── Offer attributes ─────────────────────────────────────────────────

    def _gen_to_ms_bracket(self, ms_value):
        """Convert M/s value to MS bracket ID. ms_value is in M/s units."""
        raw = ms_value * 1_000_000  # convert M/s → raw game units
        for threshold, bracket_id in _MS_BRACKETS:
            if raw >= threshold:
                return bracket_id
        return "0"

    def build_offer_attributes(self, ms, mutation=""):
        """Build offerAttributes array — mirrors JS buildOfferAttributes.
        Iterates all gameCache attrs, sets Numeric/dynamic values from ms+mutation."""
        raw = ms * 1_000_000  # convert M/s → game raw units
        # Determine multiplier from MS bracket (mirrors JS r96)
        ms_bracket_id = self._ms_bracket_id(ms)
        if ms_bracket_id and ms_bracket_id.endswith("-bs"):
            divisor = 1_000_000_000
        elif ms_bracket_id and ms_bracket_id.endswith("-ks"):
            divisor = 1_000
        else:
            divisor = 1_000_000

        attrs = []
        for a in self._game_cache.get("attrs", []):
            if a["type"] == "Numeric":
                val = None
                if "ms" in a["id"]:
                    # Use raw value divided by divisor (mirrors JS line 379-383)
                    if raw > 0:
                        val = round(raw / divisor, 2)
                if val is None:
                    val = 0
                # Clamp
                if isinstance(a.get("maxValue"), (int, float)) and val > a["maxValue"]:
                    val = a["maxValue"]
                if isinstance(a.get("minValue"), (int, float)) and val < a["minValue"]:
                    val = a["minValue"]
                attrs.append({"id": a["id"], "type": "Numeric", "value": val})
            else:
                # Select type
                if a["id"] == "steal-a-brainrot-ms":
                    attrs.append({"id": a["id"], "type": "Select", "value": ms_bracket_id or "0"})
                elif a["id"] == "steal-a-brainrot-mutations":
                    _mut = mutation.lower()
                    if _mut and _mut not in ("normal", "none"):
                        attrs.append({"id": a["id"], "type": "Select", "value": _mut})
                # any other Select attrs could be added here if needed
        return attrs

    def _ms_bracket_id(self, ms):
        """Find matching MS bracket ID (Select value) for a given M/s."""
        raw = ms * 1_000_000
        ms_attr = None
        for a in self._game_cache.get("attrs", []):
            if a["id"] == "steal-a-brainrot-ms":
                ms_attr = a
                break
        if ms_attr and ms_attr.get("values"):
            for val in ms_attr["values"]:
                vid = val["id"]
                parsed = self._parse_bracket(vid)
                if parsed and raw >= parsed[0] and raw < parsed[1]:
                    return vid
            return ms_attr["values"][-1]["id"]  # fallback > last bracket
        return self._gen_to_ms_bracket(ms)

    @staticmethod
    def _parse_bracket(bracket_id):
        """Parse a bracket ID like '1-24.99-ms' or '25-49.99-ms' or '750-99999-ms' into (low, high)."""
        import re
        m = re.match(r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)-([kmbt]s?)$", bracket_id, re.I)
        if not m:
            return None
        lo = float(m.group(1))
        hi = float(m.group(2))
        unit = m.group(3).lower()
        multiplier = {"ks": 1_000, "ms": 1_000_000, "bs": 1_000_000_000}.get(unit, 1)
        return int(lo * multiplier), int((hi + 0.01) * multiplier)

    # ── Title generation ─────────────────────────────────────────────────

    def mutation_title(self, name, namestock="", trait_count="", mutation="",
                       game="Steal a Brainrot"):
        """Generate a listing title (max 160 chars)."""
        emoji = MUTATION_EMOJI.get(mutation.lower(), "") if mutation else ""
        ns_part = f" {namestock}" if namestock and namestock.lower() not in ("none", "0", "") else ""
        mut_part = f" {mutation}" if mutation and mutation.lower() != "none" else ""

        if emoji:
            name_line = f"{emoji} {name}{ns_part} {emoji}"
        else:
            name_line = f"{ZAP} {name}{ns_part}"

        bracket = f"【{game}"
        if trait_count and trait_count not in ("None", "0", ""):
            bracket += f" {trait_count} Trait"
        bracket += f"{mut_part}】"

        title = f"{name_line} {bracket} {ZAP} INSTANT DELIVERY {ZAP}"
        return title[:160]

    # ── Image upload ─────────────────────────────────────────────────────

    def upload_image(self, file_bytes, filename="image.png"):
        """Upload image to Eldorado. Returns {smallImage, largeImage, originalSizeImage} or None."""
        boundary = "----FormBoundary" + uuid.uuid4().hex
        body_parts = []
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode())
        body_parts.append(b"Content-Type: image/png\r\n\r\n")
        body_parts.append(file_bytes)
        body_parts.append(f"\r\n--{boundary}--\r\n".encode())
        body = b"".join(body_parts)

        cookies_str = "; ".join(f"{k}={v}" for k, v in self._cookies_dict().items())
        headers = dict(self._headers)
        headers["X-XSRF-Token"] = self._xsrf or ""
        headers["X-Device-Id"] = self.device_id or ""
        headers["X-Correlation-Id"] = str(uuid.uuid4())
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        headers["Cookie"] = cookies_str
        # Remove default Content-Type for multipart
        if "Content-Type" in headers:
            pass  # overwritten above

        try:
            resp = self._session.post(
                BASE + "/files/me/Offer",
                headers=headers,
                data=body,
                timeout=60,
            )
        except Exception as e:
            self._log(f"[IMG] Upload error: {e}")
            return None

        if resp.status_code == 429:
            return {"_rate_limit": True}

        if resp.status_code == 200:
            try:
                result = resp.json()
                paths = result.get("localPaths", [])
                if len(paths) >= 3:
                    return {
                        "smallImage": paths[0].replace("/offerimages/", ""),
                        "largeImage": paths[1].replace("/offerimages/", ""),
                        "originalSizeImage": paths[2].replace("/offerimages/", ""),
                    }
                self._log(f"[IMG] 200 but no localPaths: {json.dumps(result)[:100]}")
            except Exception:
                pass
        else:
            self._log(f"[IMG] HTTP {resp.status_code}: {resp.text[:120]}")

        return None

    # ── Listing CRUD ─────────────────────────────────────────────────────

    def create_listing(self, title, description, price, ms, mutation="",
                       trade_env_id=None, delivery_time="Minute20", image_data=None,
                       quantity=1, game_id=GAME_ID, category=CATEGORY):
        """Create a new listing. Returns API response dict.
        Matches eldorado-api.js createListing signature."""
        if not trade_env_id:
            return {"error": "Missing tradeEnvironmentId"}

        offer_attrs = self.build_offer_attributes(ms, mutation)

        payload = {
            "augmentedGame": {
                "gameId": str(game_id),
                "category": category,
                "tradeEnvironmentId": trade_env_id,
                "offerAttributes": offer_attrs,
            },
            "details": {
                "pricing": {
                    "quantity": quantity,
                    "pricePerUnit": {"amount": float(price), "currency": "USD"},
                    "volumeDiscounts": [],
                },
                "description": description or "Fast delivery! Contact me if any issues.",
                "guaranteedDeliveryTime": delivery_time,
                "offerTitle": title[:160],
                "mainOfferImage": image_data or {},
                "offerImages": [],
            },
        }

        return self._req("POST", "/v1/item-management/me/offers/item", json_data=payload)

    def get_listings(self, page=1, page_size=40):
        return self._req("GET", "/v1/item-management/me/offers/me/search",
                         params={"pageIndex": page, "pageSize": page_size})

    def get_all_listings(self, category=CATEGORY):
        all_results = []
        for page in range(1, 21):
            r = self._req("GET", "/v1/item-management/me/offers/me/search",
                          params={"pageIndex": page, "pageSize": 40})
            if not isinstance(r, dict) or not r.get("results"):
                # Fallback endpoint
                r = self._req("GET", "/flexibleOffers/me/search",
                              params={"pageIndex": page, "pageSize": 40, "category": category})
            results = (r or {}).get("results", [])
            if not results:
                break
            all_results.extend(results)
            if page >= (r or {}).get("totalPages", 1):
                break
        return {"results": all_results, "recordCount": len(all_results)}

    def edit_listing(self, offer_id, title=None, description=None, price=None,
                     delivery_time=None, image_data=None, quantity=1,
                     game_id=GAME_ID, category=CATEGORY, trade_env_id=None,
                     offer_attributes=None):
        """Edit an existing listing."""
        # Fetch current offer if we need to merge fields
        current = self._req("GET", f"/v1/item-management/me/offers/{offer_id}/private")
        offer = {}
        if isinstance(current, dict):
            offer = current.get("offer") or current

        aug = offer.get("augmentedGame") or {}
        details = offer.get("details") or {}

        payload = {
            "augmentedGame": {
                "gameId": str(game_id),
                "category": category,
                "tradeEnvironmentId": trade_env_id or aug.get("tradeEnvironmentId", ""),
                "offerAttributes": offer_attributes or aug.get("offerAttributes", []),
            },
            "details": {
                "pricing": {
                    "quantity": quantity or details.get("pricing", {}).get("quantity", 1),
                    "pricePerUnit": {
                        "amount": float(price) if price is not None else (details.get("pricing", {}).get("pricePerUnit", {}).get("amount", 0)),
                        "currency": "USD",
                    },
                    "volumeDiscounts": [],
                },
                "mainOfferImage": image_data or (details.get("mainOfferImage") or {}),
                "offerImages": [],
                "offerTitle": title or details.get("offerTitle", ""),
                "description": description if description is not None else details.get("description", ""),
                "guaranteedDeliveryTime": delivery_time or details.get("guaranteedDeliveryTime", "Minute20"),
            },
        }

        return self._req("PUT", f"/v1/item-management/me/offers/item/{offer_id}/details",
                         json_data=payload)

    def change_price(self, offer_id, amount):
        return self._req("PUT", f"/v1/item-management/me/offers/{offer_id}/price",
                         json_data={"amount": float(amount), "currency": "USD"})

    def delete_listing(self, offer_id):
        return self._req("DELETE", f"/v1/item-management/me/offers/{offer_id}")

    def pause_listing(self, offer_id):
        return self._req("POST", f"/v1/item-management/me/offers/{offer_id}/pause",
                         json_data={})

    def resume_listing(self, offer_id):
        return self._req("POST", f"/v1/item-management/me/offers/{offer_id}/resume",
                         json_data={})

    # ── Spy / Browse ─────────────────────────────────────────────────────

    def spy_search(self, params):
        """Search marketplace offers."""
        defaults = {"gameId": GAME_ID, "category": CATEGORY, "useMinPurchasePrice": "true"}
        merged = {**defaults, **{k: v for k, v in params.items() if v is not None}}
        return self._req("GET", "/v1/item-management/offers", params=merged)

    def browse_offers(self, game_id=GAME_ID, category=CATEGORY, page=1):
        return self._req("GET", "/v1/item-management/offers",
                         params={"gameId": game_id, "category": category, "pageIndex": page})

    # ── Orders ───────────────────────────────────────────────────────────

    def get_orders(self, page_size=20, cursor=None):
        default_cursor = "9999-99-99 99:99:99.999999999999999-9999-9999-9999-999999999999"
        return self._req("GET", "/orders/me/seller/orders",
                         params={"pageSize": page_size, "pageDirection": "Next",
                                 "cursorValue": cursor or default_cursor})

    def get_order_stats(self):
        return self._req("GET", "/orders/me/statesCount",
                         params={"displayFilter": "DisplaySellingOrders", "orderGroup": "Regular"})

    def mark_delivered(self, order_id):
        return self._req("PUT", f"/orders/me/{order_id}/deliver")

    def get_order_detail(self, order_id):
        return self._req("GET", f"/orders/me/{order_id}")

    # ── States ─────────────────────────────────────────────────────────

    def get_states(self, category=CATEGORY):
        r = self._req("GET", "/v1/item-management/me/offers/state-count",
                       params={"category": category})
        if isinstance(r, dict) and ("activeOffers" in r or "closedOffers" in r):
            return r
        return self._req("GET", "/flexibleOffersUser/me/stateCount",
                         params={"category": category})

    def get_offer_private(self, offer_id):
        return self._req("GET", f"/v1/item-management/me/offers/{offer_id}/private")

    def change_state(self, offer_id, state):
        action = "pause" if state == "Paused" else "resume"
        return self._req("POST", f"/v1/item-management/me/offers/{offer_id}/{action}",
                         json_data={})

    # ── Offline/Online ─────────────────────────────────────────────────

    def switch_offline(self):
        return self._req("PUT", "/offerUser/me/switchOffline", json_data={})

    def switch_online(self):
        return self._req("PUT", "/offerUser/me/switchOnline", json_data={})

    def get_offline_status(self):
        r = self._req("GET", "/offerUser/me")
        if isinstance(r, dict) and isinstance(r.get("offlineMode"), str):
            return r["offlineMode"] != "Online"
        return None

    # ── Notifications ──────────────────────────────────────────────────

    def get_notifications(self, page_size=20, cursor=None):
        default_cursor = "9999-99-99 99:99:99.999999999999999-9999-9999-9999-999999999999"
        return self._req("GET", "/notifications/me", params={
            "pageSize": page_size, "pageDirection": "Next",
            "cursorValue": cursor or default_cursor,
            "notificationReadStatuses": ["IsUnread", "IsRead"],
        })

    def mark_notifications_read(self):
        return self._req("PUT", "/notifications/me/markAllAsRead")

    # ── Fees ───────────────────────────────────────────────────────────

    def get_fees(self, game_id=GAME_ID, category=CATEGORY):
        return self._req("GET", f"/fees/me/feesForGame/{game_id}",
                         params={"category": category})

    # ── Wallet ──────────────────────────────────────────────────────────

    def get_payments(self, page_size=30, cursor=None):
        default_cursor = "9999-99-99 99:99:99.999999999999999-9999-9999-9999-999999999999"
        return self._req("GET", "/userpayment/me/payments", params={
            "paymentsCategory": "All", "pageSize": page_size,
            "pageDirection": "Next", "cursorValue": cursor or default_cursor,
        })

    def get_pending_sum(self):
        return self._req("GET", "/orders/me/pendingOrdersSum")

    def get_historical_seller_stats(self):
        return self._req("GET", "/orders/me/statesCount", params={
            "displayFilter": "DisplaySellingOrders", "orderGroup": "Historical",
        })

    # ── Disconnect ───────────────────────────────────────────────────────

    def disconnect(self):
        self.logged_in = False
        self._raw = ""
        self._xsrf = ""
        self.device_id = ""
        self.session_id = ""
        self.username = ""
        self.userId = ""
        self.talk_token = ""
        p = Path(COOKIE_FILE)
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
