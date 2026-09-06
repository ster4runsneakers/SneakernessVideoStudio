"""Optional sneaker image analysis via xAI Grok or Google Gemini.

Uses XAI_API_KEY / GROK_API_KEY and/or GEMINI_API_KEY from env / Streamlit secrets.
Priority (Auto): try XAI/GROK first if key present, else Gemini, else deterministic defaults.
Does NOT require any API key for offline Grok prompt generation.
"""

from __future__ import annotations

import base64
import json
import os
import re
import re
from typing import Any, Dict, Literal, Optional, Tuple

from captions import sanitize_celebrity_names


ProviderChoice = Literal["auto", "grok", "gemini"]

DEFAULT_ANALYSIS: Dict[str, str] = {
    "brand": "",
    "model": "",
    "specs": "",
    "colorway": "",
    "env_desc": "minimalist concrete urban street with natural daylight",
    "props_desc": "an open Kinfolk magazine, a ceramic cup of cappuccino, brass keys, succulent",
    "problem_desc": (
        "a tired worker sitting on stairs touching sore feet with work boots beside them"
    ),
}

ANALYZE_SYSTEM = (
    "You are an expert footwear product analyst and sneaker commercial creative director. "
    "Return ONLY valid JSON. Never include celebrity athlete names."
)

ANALYZE_PROMPT = """Examine the provided sneaker image with extreme precision.

CRITICAL IDENTIFICATION & DYNAMIC SCENE CREATION RULES:
1. "brand": Identify the EXACT footwear brand name visible on the shoe or tongue.
2. "model": Identify the EXACT shoe model name based on visible text. Never use celebrity names; if model contains athlete names replace with neutral product naming.
3. "colorway": Describe the exact observed colors (e.g., "Cream / Red / Navy Blue").
4. "specs": Technical specifications specific to this exact model.
5. "env_desc": One detailed English sentence for the IDEAL background environment for this shoe archetype.
6. "props_desc": One English sentence listing 3-4 EDC props matching its lifestyle/vibe.
7. "problem_desc": One English sentence describing a realistic human pain-point scene matching this shoe's category (anonymous person, no celebrity).

Return ONLY a valid raw JSON object:
{
  "brand": "...",
  "model": "...",
  "specs": "...",
  "colorway": "...",
  "env_desc": "...",
  "props_desc": "...",
  "problem_desc": "..."
}"""


def _clean_secret(val: str) -> str:
    v = (val or "").strip()
    if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        v = v[1:-1].strip()
    return v


def _secret_lookup(name: str) -> Optional[str]:
    """Resolve a single key from env, then Streamlit secrets (flat or nested)."""
    val = _clean_secret(os.getenv(name, ""))
    if val:
        return val
    try:
        import streamlit as st

        secrets = getattr(st, "secrets", None)
        if secrets is None:
            return None
        # Flat: GEMINI_API_KEY = "..."
        try:
            val = _clean_secret(str(secrets[name]))
            if val and val != "None":
                return val
        except Exception:
            pass
        try:
            val = _clean_secret(str(secrets.get(name, "") or ""))
            if val:
                return val
        except Exception:
            pass
        # Nested common mistakes: [gemini] api_key / GEMINI_API_KEY
        for section in ("gemini", "google", "genai", "api"):
            try:
                sect = secrets[section]
            except Exception:
                continue
            for alt in (name, "api_key", "API_KEY", "key"):
                try:
                    val = _clean_secret(str(sect[alt]))
                    if val and val != "None":
                        return val
                except Exception:
                    try:
                        val = _clean_secret(str(sect.get(alt, "") or ""))
                        if val:
                            return val
                    except Exception:
                        pass
    except Exception:
        pass
    return None


def get_xai_api_key() -> Optional[str]:
    """Resolve xAI / Grok API key from env or Streamlit secrets."""
    for name in ("XAI_API_KEY", "GROK_API_KEY"):
        val = _secret_lookup(name)
        if val:
            return val
    return None


def get_gemini_api_key() -> Optional[str]:
    """Resolve Gemini API key from env or Streamlit secrets."""
    return _secret_lookup("GEMINI_API_KEY")


def has_xai_key() -> bool:
    return bool(get_xai_api_key())


def has_gemini_key() -> bool:
    return bool(get_gemini_api_key())


def available_providers() -> Dict[str, bool]:
    return {"grok": has_xai_key(), "gemini": has_gemini_key()}


def _mime_from_name(filename: str) -> str:
    lower = (filename or "").lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"


def _strip_json_fence(text: str) -> str:
    clean = text.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    elif clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    return clean.strip()


def _sanitize_analysis(data: Dict[str, Any]) -> Dict[str, str]:
    out = dict(DEFAULT_ANALYSIS)
    for key in out:
        if key in data and data[key] is not None:
            out[key] = sanitize_celebrity_names(str(data[key]).strip())
    return out


def analyze_shoe_fallback(
    brand_name: str = "",
    model_name: str = "",
) -> Dict[str, str]:
    data = dict(DEFAULT_ANALYSIS)
    data["brand"] = sanitize_celebrity_names(brand_name or "")
    data["model"] = sanitize_celebrity_names(model_name or "")
    return data


def analyze_shoe_with_xai(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    brand_hint: str = "",
    model_hint: str = "",
    model: str = "grok-4.6",
) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Call xAI OpenAI-compatible chat completions with vision.
    Returns (analysis_dict, error_message_or_None).
    """
    api_key = get_xai_api_key()
    if not api_key:
        return analyze_shoe_fallback(brand_hint, model_hint), "no_api_key"

    try:
        from openai import OpenAI
    except ImportError:
        return (
            analyze_shoe_fallback(brand_hint, model_hint),
            "openai package not installed",
        )

    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    user_text = ANALYZE_PROMPT
    if brand_hint or model_hint:
        user_text += f"\n\nHints (may be empty): brand={brand_hint!r}, model={model_hint!r}"

    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    models_to_try = [model, "grok-4.6", "grok-4.5", "grok-4.3"]
    last_err: Optional[str] = None

    for m in models_to_try:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": ANALYZE_SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                temperature=0.2,
            )
            text = (resp.choices[0].message.content or "").strip()
            parsed = json.loads(_strip_json_fence(text))
            if isinstance(parsed, dict):
                return _sanitize_analysis(parsed), None
            last_err = "invalid JSON shape"
        except Exception as e:
            last_err = str(e)
            continue

    return analyze_shoe_fallback(brand_hint, model_hint), last_err


def _jpeg_bytes_if_needed(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Gemini is happiest with jpeg/png; convert webp/other via Pillow when possible."""
    mime = (mime_type or "image/jpeg").lower()
    if mime in ("image/jpeg", "image/jpg", "image/png"):
        return image_bytes, "image/jpeg" if "jpeg" in mime or "jpg" in mime else "image/png"
    try:
        from io import BytesIO
        from PIL import Image

        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=92)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, "image/jpeg"


def _extract_response_text(resp) -> str:
    text = (getattr(resp, "text", None) or "").strip()
    if text:
        return text
    # Fallback when .text is empty but candidates exist
    try:
        cands = getattr(resp, "candidates", None) or []
        parts_out = []
        for c in cands:
            content = getattr(c, "content", None)
            parts = getattr(content, "parts", None) or []
            for p in parts:
                pt = getattr(p, "text", None)
                if pt:
                    parts_out.append(pt)
        return "\n".join(parts_out).strip()
    except Exception:
        return ""


def _parse_analysis_json(text: str) -> dict | None:
    clean = _strip_json_fence(text)
    try:
        parsed = json.loads(clean)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    # Recover JSON object from surrounding prose
    m = re.search(r"\{[\s\S]*\}", clean)
    if m:
        try:
            parsed = json.loads(m.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def analyze_shoe_with_gemini(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    brand_hint: str = "",
    model_hint: str = "",
    model: str = "gemini-2.5-flash",
) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Call Google Gemini via google-genai SDK — aligned with sneakerness-engine app.py.
    Returns (analysis_dict, error_message_or_None).
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return analyze_shoe_fallback(brand_hint, model_hint), "no_api_key"

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return (
            analyze_shoe_fallback(brand_hint, model_hint),
            "google-genai package not installed",
        )

    image_bytes, mime_type = _jpeg_bytes_if_needed(image_bytes, mime_type)

    user_text = ANALYZE_PROMPT
    if brand_hint or model_hint:
        user_text += f"\n\nHints (may be empty): brand={brand_hint!r}, model={model_hint!r}"

    # Same spirit as sneakerness-engine model cascade
    # Current Google AI models only (1.5-*-latest often 404 on v1beta now)
    models_to_try = [
        model,
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-flash-latest",
    ]
    # de-dupe preserve order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_err: Optional[str] = None
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return analyze_shoe_fallback(brand_hint, model_hint), f"client_init:{e}"

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    # Sneakerness order: image first, then prompt text
    contents = [image_part, user_text]

    for m in models_to_try:
        try:
            resp = client.models.generate_content(model=m, contents=contents)
            text = _extract_response_text(resp)
            if not text:
                # blocked / empty
                reason = "empty_response"
                try:
                    c0 = (resp.candidates or [None])[0]
                    fr = getattr(c0, "finish_reason", None)
                    if fr is not None:
                        reason = f"empty_response finish_reason={fr}"
                except Exception:
                    pass
                last_err = f"{m}:{reason}"
                continue
            parsed = _parse_analysis_json(text)
            if parsed:
                out = _sanitize_analysis(parsed)
                if out.get("brand") or out.get("model") or out.get("colorway"):
                    return out, None
                # Accept partial scene fill rather than failing entirely
                if any(out.get(k) for k in ("specs", "env_desc", "props_desc")):
                    return out, None
                last_err = f"{m}:json_ok_but_empty_fields"
                continue
            last_err = f"{m}:invalid_json:{text[:180]}"
        except Exception as e:
            last_err = f"{m}:{e}"
            continue

    return analyze_shoe_fallback(brand_hint, model_hint), last_err


def generate_copy_with_xai(
    brand: str,
    model_name: str,
    colorway: str,
    specs: str,
    watermark: str,
    model: str = "grok-4.6",
) -> Tuple[Dict[str, str], Optional[str]]:
    """Optional EN soft-discovery copy via Grok text. Falls back silently."""
    from captions import ProductInfo, generate_ad_texts, generate_caption, safe_model_name

    fallback = generate_ad_texts(
        ProductInfo(
            brand=brand,
            model=model_name,
            colorway=colorway,
            specs=specs,
            watermark=watermark,
        )
    )
    api_key = get_xai_api_key()
    if not api_key:
        return fallback, "no_api_key"

    try:
        from openai import OpenAI
    except ImportError:
        return fallback, "openai package not installed"

    clean_model = safe_model_name(model_name)
    script = f"""Write ALL ad assets and copy in ENGLISH for {brand} {clean_model} in {colorway} ({specs}) for website {watermark}.

CRITICAL CONSTRAINTS:
1. ALL OUTPUT MUST BE IN ENGLISH.
2. DO NOT use hard-sell verbs like "buy", "shop", "order", "purchase".
3. Use soft discovery CTAs like "Discover more at {watermark}".
4. STRICTLY DO NOT include celebrity names.

Return strict JSON with keys:
hook, body, cta, meta_caption, tiktok_caption, hashtags_meta,
slide1_text, slide2_text, slide3_text
"""
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Expert e-commerce copywriter. Soft-sell discovery footwear copy. "
                        "Never use celebrity athlete names. JSON only."
                    ),
                },
                {"role": "user", "content": script},
            ],
            temperature=0.5,
        )
        text = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(_strip_json_fence(text))
        if isinstance(parsed, dict):
            merged = dict(fallback)
            for k, v in parsed.items():
                if isinstance(v, str) and v.strip():
                    merged[k] = sanitize_celebrity_names(v.strip())
            info = ProductInfo(
                brand=brand,
                model=model_name,
                colorway=colorway,
                specs=specs,
                watermark=watermark,
            )
            merged["caption_en"] = generate_caption(
                info, style="soft_discovery", lang="en", ad_texts=merged
            )
            merged["caption_el"] = generate_caption(
                info, style="soft_discovery", lang="el", ad_texts=merged
            )
            # Always keep deterministic Pinterest short format (xAI JSON has no pinterest keys)
            merged["pinterest_caption"] = fallback.get(
                "pinterest_caption", merged.get("pinterest_caption", "")
            )
            merged["pinterest_caption_el"] = fallback.get(
                "pinterest_caption_el", merged.get("pinterest_caption_el", "")
            )
            return merged, None
    except Exception as e:
        return fallback, str(e)

    return fallback, "empty_response"


def analyze_shoe(
    image_bytes: Optional[bytes] = None,
    filename: str = "shoe.jpg",
    brand_hint: str = "",
    model_hint: str = "",
    provider: ProviderChoice = "auto",
) -> Tuple[Dict[str, str], str]:
    """
    High-level analyze entry.
    Returns (data, status) where status is:
      'xai' | 'gemini' | 'fallback' | 'fallback_no_key' | 'fallback_error:…'
    provider: 'auto' | 'grok' | 'gemini' (default auto).
    Offline / no keys → deterministic defaults (never raises).
    """
    if not image_bytes:
        return analyze_shoe_fallback(brand_hint, model_hint), "fallback"

    mime = _mime_from_name(filename)
    choice = (provider or "auto").strip().lower()
    if choice not in ("auto", "grok", "gemini"):
        choice = "auto"

    def _try_grok() -> Tuple[Dict[str, str], str]:
        if not has_xai_key():
            return analyze_shoe_fallback(brand_hint, model_hint), "fallback_no_key"
        data, err = analyze_shoe_with_xai(image_bytes, mime, brand_hint, model_hint)
        if err and err != "no_api_key":
            return data, f"fallback_error:{err}"
        if err == "no_api_key":
            return data, "fallback_no_key"
        return data, "xai"

    def _try_gemini() -> Tuple[Dict[str, str], str]:
        if not has_gemini_key():
            return analyze_shoe_fallback(brand_hint, model_hint), "fallback_no_key"
        data, err = analyze_shoe_with_gemini(image_bytes, mime, brand_hint, model_hint)
        if err and err != "no_api_key":
            return data, f"fallback_error:{err}"
        if err == "no_api_key":
            return data, "fallback_no_key"
        return data, "gemini"

    if choice == "grok":
        return _try_grok()
    if choice == "gemini":
        return _try_gemini()

    # Auto: XAI/GROK first, else Gemini, else deterministic defaults
    if has_xai_key():
        data, status = _try_grok()
        if status == "xai":
            return data, status
        # fall through to Gemini if Grok failed
        if has_gemini_key():
            g_data, g_status = _try_gemini()
            if g_status == "gemini":
                return g_data, g_status
        return data, status

    if has_gemini_key():
        return _try_gemini()

    return analyze_shoe_fallback(brand_hint, model_hint), "fallback_no_key"
