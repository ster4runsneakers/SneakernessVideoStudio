"""Soft-discovery Greek + English social captions (Sneakerness philosophy).

No hard-sell verbs (buy/shop/order/purchase). Soft CTAs + celebrity name filter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


UNSAFE_CELEBRITY_KEYWORDS = [
    "kobe",
    "jordan",
    "lebron",
    "messi",
    "ronaldo",
    "curry",
]

HARD_SELL_RE = re.compile(
    r"\b(buy|shop|order|purchase|αγόρασε|παράγγειλε|αγορά)\b",
    re.IGNORECASE,
)

CATEGORY_BADGES = [
    "REVIEWED ★★★★★",
    "DAILY APPROVED ★★★★★",
    "CUSHIONING APPROVED",
    "RUNNING TECH",
    "HERITAGE DROP",
    "STREET CLASSIC",
    "ULTRA COMFORT ★★★★★",
    "BESTSELLER SELECTION",
]

AUTHENTICITY_TAGS = [
    "100% AUTHENTIC GUARANTEED",
    "LIMITED EDITION DROP",
    "PREMIUM COMFORT EDITION",
    "OFFICIAL SNEAKERNESS SELECTION",
    "ORIGINAL HERITAGE DROP",
    "VERIFIED AUTHENTIC",
]

CAPTION_STYLES = {
    "soft_discovery": {"el": "Soft Discovery", "en": "Soft Discovery"},
    "story": {"el": "Story / Narrative", "en": "Story"},
    "short": {"el": "Σύντομο", "en": "Short"},
}


@dataclass
class ProductInfo:
    brand: str = ""
    model: str = ""
    colorway: str = ""
    specs: str = ""
    price: str = ""
    watermark: str = "SNEAKERNESS.EU"
    tag: str = AUTHENTICITY_TAGS[0]
    badge: str = CATEGORY_BADGES[0]
    env_desc: str = "minimalist concrete urban street with natural daylight"
    props_desc: str = "an open Kinfolk magazine, a ceramic cup of cappuccino, brass keys, succulent"
    problem_desc: str = (
        "a tired worker sitting on stairs touching sore feet with work boots beside them"
    )
    hashtags: str = ""
    extra: str = ""
    # legacy / slideshow
    cta: str = ""


def sanitize_celebrity_names(text: str) -> str:
    """Replace restricted celebrity/athlete names with neutral phrasing."""
    if not text:
        return text
    out = text
    for word in UNSAFE_CELEBRITY_KEYWORDS:
        # case-insensitive whole-ish replace
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        out = pattern.sub("signature pro", out)
    return out


def soft_sanitize(text: str, watermark: str = "SNEAKERNESS.EU") -> str:
    """Strip hard-sell verbs and celebrity names."""
    text = sanitize_celebrity_names(text)

    def _repl(m: re.Match) -> str:
        return "discover"

    text = HARD_SELL_RE.sub(_repl, text)
    return text


def safe_model_name(model: str) -> str:
    return sanitize_celebrity_names(model or "")


def _clean_hashtags(raw: str) -> str:
    parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
    tags = []
    for p in parts:
        if not p.startswith("#"):
            p = "#" + p.lstrip("#")
        tags.append(p)
    return " ".join(tags)


def _product_line(info: ProductInfo) -> str:
    bits = [b for b in [info.brand, safe_model_name(info.model), info.colorway] if b.strip()]
    return " · ".join(bits) if bits else "New drop"


def default_hashtags(info: ProductInfo, lang: str = "en") -> str:
    brand = (info.brand or "Sneakers").replace(" ", "")
    if info.hashtags.strip():
        return _clean_hashtags(info.hashtags)
    if lang == "el":
        return f"#Sneakerness #{brand} #DailyComfort #FootwearTech #sneakers #greece"
    return f"#Sneakerness #{brand} #DailyComfort #FootwearTech #SoftDiscovery #sneakers"


def generate_ad_texts(info: ProductInfo) -> Dict[str, str]:
    """Deterministic soft-discovery ad copy pack (EN creative outputs)."""
    brand = info.brand.strip() or "the brand"
    model = safe_model_name(info.model.strip() or "signature silhouette")
    wm = info.watermark.strip() or "SNEAKERNESS.EU"
    colorway = info.colorway.strip() or "signature colorway"
    specs = info.specs.strip() or "engineered cushioning and support"

    texts = {
        "hook": soft_sanitize(
            f"Tired of foot fatigue after long hours? Discover {brand} {model}.", wm
        ),
        "body": soft_sanitize(
            "Engineered to absorb impact and support posture all day.", wm
        ),
        "cta": soft_sanitize(f"Discover more at {wm}.", wm),
        "meta_caption": soft_sanitize(
            f"Long shifts and daily standing don't have to take a toll on your feet. "
            f"Explore how {brand} {model} ({colorway}) delivers posture support with {specs}. "
            f"Learn more at {wm}.",
            wm,
        ),
        "tiktok_caption": soft_sanitize(
            f"How do you deal with foot fatigue? Check out the tech behind "
            f"{brand} {model} at {wm}! 👟 #Sneakerness #{brand.replace(' ', '')} #FootwearTech #DailyComfort #FYP",
            wm,
        ),
        "hashtags_meta": default_hashtags(info, "en"),
        "slide1_text": "Tired of Foot Fatigue After Long Hours?",
        "slide2_text": soft_sanitize(f"Discover {brand} {model}.", wm),
        "slide3_text": soft_sanitize(f"Explore the Full Specs at {wm}", wm),
        "caption_el": "",
        "caption_en": "",
    }
    texts["caption_en"] = generate_caption(info, style="soft_discovery", lang="en", ad_texts=texts)
    texts["caption_el"] = generate_caption(info, style="soft_discovery", lang="el", ad_texts=texts)
    return texts


def generate_caption(
    info: ProductInfo,
    style: str = "soft_discovery",
    lang: str = "el",
    ad_texts: Optional[Dict[str, str]] = None,
) -> str:
    style = style if style in CAPTION_STYLES else "soft_discovery"
    product = _product_line(info)
    wm = info.watermark.strip() or "SNEAKERNESS.EU"
    tags = default_hashtags(info, lang)
    model = safe_model_name(info.model)
    brand = info.brand.strip()
    extra = soft_sanitize(info.extra.strip(), wm) if info.extra else ""

    if lang == "en":
        return _caption_en(style, product, brand, model, wm, tags, extra, info, ad_texts)
    return _caption_el(style, product, brand, model, wm, tags, extra, info, ad_texts)


def _caption_el(
    style: str,
    product: str,
    brand: str,
    model: str,
    wm: str,
    tags: str,
    extra: str,
    info: ProductInfo,
    ad_texts: Optional[Dict[str, str]],
) -> str:
    soft_cta = f"Μάθε περισσότερα στο {wm}"
    if style == "short":
        lines = [f"✨ {product}", soft_cta]
        if tags:
            lines.append(tags)
        return soft_sanitize("\n".join(lines), wm)

    if style == "story":
        lines = [
            f"✨ {product}",
            "",
            "Όταν η μέρα είναι βαριά στα πόδια, η σωστή τεχνολογία κάνει τη διαφορά.",
        ]
        if info.colorway:
            lines.append(f"🎨 Colorway: {info.colorway}")
        if info.specs:
            lines.append(f"⚙️ {info.specs}")
        if extra:
            lines.append(extra)
        lines += ["", f"👉 {soft_cta}", "", tags]
        return soft_sanitize("\n".join(lines), wm)

    # soft_discovery (default)
    lines = [
        f"Κουράστηκες από την κούραση στα πόδια μετά από πολλές ώρες;",
        "",
        f"Ανακάλυψε {brand} {model}".strip() + (f" · {info.colorway}" if info.colorway else ""),
        "Σχεδιασμένο για στήριξη, απορρόφηση κραδασμών και άνεση όλη μέρα.",
    ]
    if info.specs:
        lines.append(f"Specs: {info.specs}")
    if extra:
        lines.append(extra)
    lines += ["", f"🔍 {soft_cta}", "", tags]
    return soft_sanitize("\n".join(lines), wm)


def _caption_en(
    style: str,
    product: str,
    brand: str,
    model: str,
    wm: str,
    tags: str,
    extra: str,
    info: ProductInfo,
    ad_texts: Optional[Dict[str, str]],
) -> str:
    soft_cta = f"Discover more at {wm}"
    if ad_texts and style == "soft_discovery":
        meta = ad_texts.get("meta_caption", "")
        hash_line = ad_texts.get("hashtags_meta", tags)
        return soft_sanitize(f"{meta}\n\n{hash_line}", wm)

    if style == "short":
        lines = [f"✨ {product}", soft_cta]
        if tags:
            lines.append(tags)
        return soft_sanitize("\n".join(lines), wm)

    if style == "story":
        lines = [
            f"✨ {product}",
            "",
            "When long days hit your feet hard, the right tech changes everything.",
        ]
        if info.colorway:
            lines.append(f"🎨 Colorway: {info.colorway}")
        if info.specs:
            lines.append(f"⚙️ {info.specs}")
        if extra:
            lines.append(extra)
        lines += ["", f"👉 {soft_cta}", "", tags]
        return soft_sanitize("\n".join(lines), wm)

    lines = [
        "Tired of foot fatigue after long hours?",
        "",
        f"Explore {brand} {model}".strip() + (f" · {info.colorway}" if info.colorway else ""),
        "Engineered to absorb impact and support posture all day.",
    ]
    if info.specs:
        lines.append(f"Specs: {info.specs}")
    if extra:
        lines.append(extra)
    lines += ["", f"🔍 {soft_cta}", "", tags]
    return soft_sanitize("\n".join(lines), wm)


def video_hook_text(info: ProductInfo, lang: str = "el") -> str:
    brand = info.brand.strip()
    model = safe_model_name(info.model.strip())
    if brand and model:
        return f"{brand} {model}"
    if model:
        return model
    if brand:
        return brand
    return "Νέο Drop" if lang == "el" else "New Drop"


def video_subtitle_text(info: ProductInfo, lang: str = "el") -> str:
    bits: List[str] = []
    if info.colorway.strip():
        bits.append(info.colorway.strip())
    wm = info.watermark.strip()
    if wm:
        bits.append(wm)
    if bits:
        return " · ".join(bits)
    return "Discover more" if lang == "en" else "Μάθε περισσότερα"


def build_content_pack_text(
    info: ProductInfo,
    grok_prompts: Dict[str, str],
    ad_texts: Dict[str, str],
) -> str:
    """Assemble downloadable .txt content pack."""
    meta = f"{ad_texts.get('meta_caption', '')}\n\n{ad_texts.get('hashtags_meta', '')}"
    tiktok = ad_texts.get("tiktok_caption", "")
    el_cap = ad_texts.get("caption_el", "")
    parts = [
        "========================================",
        "GROK VIDEO PROMPT PACK (xAI)",
        "========================================",
    ]
    for label, body in grok_prompts.items():
        parts.append(f"\n--- {label} ---\n{body}\n")
    parts += [
        "========================================",
        "FACEBOOK & INSTAGRAM POST (EN — Soft Discovery)",
        "========================================",
        meta,
        "",
        "========================================",
        "TIKTOK / REEL POST (EN)",
        "========================================",
        tiktok,
        "",
        "========================================",
        "CAPTION (EL — Soft Discovery)",
        "========================================",
        el_cap,
        "",
        "========================================",
        "PRODUCT FIELDS",
        "========================================",
        f"Brand: {info.brand}",
        f"Model: {safe_model_name(info.model)}",
        f"Colorway: {info.colorway}",
        f"Specs: {info.specs}",
        f"Env: {info.env_desc}",
        f"Props: {info.props_desc}",
        f"Problem: {info.problem_desc}",
        f"Tag: {info.tag}",
        f"Badge: {info.badge}",
        f"Watermark: {info.watermark}",
    ]
    return soft_sanitize("\n".join(parts), info.watermark)
