"""Optional sneaker image analysis via xAI Grok or Google Gemini.

Uses XAI_API_KEY / GROK_API_KEY and/or GEMINI_API_KEY from env / Streamlit secrets.
Priority (Auto): try XAI/GROK first if key present, else Gemini, else deterministic defaults.
Does NOT require any API key for offline Grok prompt generation.
"""

from __future__ import annotations

import base64
import json
import os
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


def _secret_lookup(name: str) -> Optional[str]:
    """Resolve a single key from env, then Streamlit secrets."""
    val = os.getenv(name, "").strip()
    if val:
        return val
    try:
        import streamlit as st

        secrets = getattr(st, "secrets", None)
        if secrets is not None:
            try:
                val = str(secrets.get(name, "") or "").strip()
                if val:
                    return val
            except Exception:
                try:
                    val = str(secrets[name]).strip()
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
    model: str = "grok-2-vision-1212",
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

    models_to_try = [model, "grok-2-vision-1212", "grok-vision-beta", "grok-2-latest"]
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


def analyze_shoe_with_gemini(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    brand_hint: str = "",
    model_hint: str = "",
    model: str = "gemini-2.0-flash",
) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Call Google Gemini via google-genai SDK (sneakerness-engine style).
    Returns (analysis_dict, error_message_or_None).
    Safe to import/call without a key — returns fallback + 'no_api_key'.
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

    user_text = ANALYZE_PROMPT
    if brand_hint or model_hint:
        user_text += f"\n\nHints (may be empty): brand={brand_hint!r}, model={model_hint!r}"

    models_to_try = [
        model,
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
    ]
    last_err: Optional[str] = None

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return analyze_shoe_fallback(brand_hint, model_hint), str(e)

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    for m in models_to_try:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=[
                    ANALYZE_SYSTEM + "\n\n" + user_text,
                    image_part,
                ],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
            text = (getattr(resp, "text", None) or "").strip()
            if not text:
                last_err = "empty_response"
                continue
            parsed = json.loads(_strip_json_fence(text))
            if isinstance(parsed, dict):
                return _sanitize_analysis(parsed), None
            last_err = "invalid JSON shape"
        except Exception as e:
            last_err = str(e)
            # Retry without response_mime_type for older models
            try:
                resp = client.models.generate_content(
                    model=m,
                    contents=[ANALYZE_SYSTEM + "\n\n" + user_text, image_part],
                    config=types.GenerateContentConfig(
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                    ),
                )
                text = (getattr(resp, "text", None) or "").strip()
                if text:
                    parsed = json.loads(_strip_json_fence(text))
                    if isinstance(parsed, dict):
                        return _sanitize_analysis(parsed), None
            except Exception as e2:
                last_err = str(e2)
            continue

    return analyze_shoe_fallback(brand_hint, model_hint), last_err


def generate_copy_with_xai(
    brand: str,
    model_name: str,
    colorway: str,
    specs: str,
    watermark: str,
    model: str = "grok-2-latest",
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
