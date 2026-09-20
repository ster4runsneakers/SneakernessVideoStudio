"""Grok (xAI) per-beat video prompt pack — Sneakerness Video Studio v5.

PRIMARY workflow: generate ONE Grok clip per beat (3 or 5), then stitch in-app.
Continuous multi-beat prompts are NOT the primary UX (omitted by default).

Image-Studio quality: distinct beat roles, music↔beat map, brand letter-by-letter
locks, REQUIRED watermark exactly once (bottom-right), no morph / no hard-sell UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from captions import ProductInfo, generate_ad_texts, safe_model_name, soft_sanitize


# ---------------------------------------------------------------------------
# Shared quality / negative locks (Image-Studio parity)
# ---------------------------------------------------------------------------

NEGATIVE_CONSTRAINTS = (
    "STRICT NEGATIVE CONSTRAINTS: no celebrity faces or recognizable athletes, "
    "no Kobe/Jordan/LeBron/Messi/Ronaldo/Curry likeness, no fake or distorted brand logos, "
    "no misspelled logos, no hard UI chrome, no app mockups, no carousel numbering, "
    "no 'Slide X of Y', no page numbers, no carousel dots, no LEARN MORE buttons, "
    "no stock watermark clutter, no hard-sell buy/shop buttons, no shopping cart icons, "
    "no deepfake faces, no extra limbs or heels, no detached floating shadows, "
    "no morph/warp of the sneaker, no floaty/unnatural run physics. "
    "Keep product logos accurate only if clearly visible on the real shoe; "
    "otherwise keep logo-free hero angles."
)

QUALITY_LOCKS_CORE = (
    "QUALITY LOCKS: correct anatomy only (no extra limbs/heels); shadows firmly attached "
    "to footwear and ground contact; stable product geometry — no morph, warp, or floaty run; "
    "natural physics. Hard-distinct composition per beat — do not repeat the same framing. "
    "STRICTLY NO Slide X of Y / carousel UI / LEARN MORE / invented badges "
    "(OFFICIAL SELECTION / BESTSELLER / SNEAKERNESS seals) unless exactly requested."
)


def _required_watermark_line(wm: str) -> str:
    w = (wm or "SNEAKERNESS.EU").strip() or "SNEAKERNESS.EU"
    return (
        f"REQUIRED on-screen watermark text (exactly once, bottom-right): {w} — "
        f"phone-readable (~7–9% of frame height), clean sans-serif, strong contrast, "
        f"~2–3% edge margin; not dominating the shoe. Do not duplicate the watermark."
    )


def _brand_spell_lock(brand: str) -> str:
    b = (brand or "").strip()
    if not b:
        return (
            "Brand/logo lock: preserve exact silhouette and colorway; "
            "do not invent or misspell brand lettering."
        )
    letters = [c for c in b.upper() if c.isalnum()]
    spelled = "-".join(letters) if letters else b.upper()
    return (
        f"Brand/logo lock: when brand text is visible on shoe tongue, insole, or side panel, "
        f"spell letter-by-letter exactly as {spelled} ({b}). "
        f"Correct {b} family silhouette and color cues only — do not substitute another brand."
    )


def _quality_block(info: ProductInfo) -> str:
    wm = info.watermark.strip() or "SNEAKERNESS.EU"
    return (
        f"{QUALITY_LOCKS_CORE} {_brand_spell_lock(info.brand)} "
        f"{_required_watermark_line(wm)} {NEGATIVE_CONSTRAINTS}"
    )


GROK_PREAMBLE_CLIP = (
    "You are generating ONE cinematic sneaker commercial CLIP for Grok (xAI). "
    "This is a SINGLE beat (~4–5 seconds) — not a continuous multi-beat reel. "
    "Photorealistic motion, premium commercial grade, natural physics, smooth camera. "
    "Frame composition must match the requested aspect ratio exactly. "
    "End on a clean hold ready for an editorial cut to the next beat."
)


# ---------------------------------------------------------------------------
# Music ↔ beat maps
# ---------------------------------------------------------------------------

MUSIC_MAP_3: Dict[str, str] = {
    "beat1": (
        "Music mood (beat 1 / Hook): Soft tension / question — sparse intro, "
        "low drums or ambient pad, slight rise. No vocals."
    ),
    "beat2": (
        "Music mood (beat 2 / Product): Clarity / reveal — melody enters, "
        "clearer beat, brighter. No vocals."
    ),
    "beat3": (
        "Music mood (beat 3 / Macro+CTA): Texture then soft landing — short percussive "
        "or filtered drop into open resolving chord with space under VO. No vocals."
    ),
}

MUSIC_MAP_5: Dict[str, str] = {
    "beat1": (
        "Music mood (beat 1 / Hook): Soft tension / question — sparse intro, "
        "low drums or ambient pad, slight rise. No vocals."
    ),
    "beat2": (
        "Music mood (beat 2 / Product 3/4): Clarity / reveal — melody enters, "
        "clearer beat, brighter. No vocals."
    ),
    "beat3": (
        "Music mood (beat 3 / Macro): Texture / tech — short percussive hit or "
        "filtered drop; tighter rhythm. No vocals."
    ),
    "beat4": (
        "Music mood (beat 4 / On-foot): Motion / benefit — groove forward, "
        "walking/jogging BPM feel (~115 BPM). No vocals."
    ),
    "beat5": (
        "Music mood (beat 5 / Flat-lay CTA): Soft landing / follow — resolve to open "
        "ending, hold last chord; leave room for voice CTA. No vocals."
    ),
}


@dataclass(frozen=True)
class PromptStylePreset:
    id: str
    name_el: str
    name_en: str
    mood: str
    camera: str
    lighting: str


PROMPT_STYLE_PRESETS: Dict[str, PromptStylePreset] = {
    "cinematic_commercial": PromptStylePreset(
        id="cinematic_commercial",
        name_el="Cinematic Commercial",
        name_en="Cinematic Commercial",
        mood="premium sneaker commercial, emotional but clean",
        camera="slow push-in, subtle orbit, shallow depth of field",
        lighting="natural daylight mixed with soft studio key light, gentle volumetric haze",
    ),
    "macro_tech": PromptStylePreset(
        id="macro_tech",
        name_el="Macro / Tech Specs",
        name_en="Macro Tech",
        mood="detail-obsessed product film, tactile materials",
        camera="macro glide across midsole/outsole, rack focus",
        lighting="crisp commercial studio lighting, specular highlights on mesh and rubber",
    ),
    "urban_hype": PromptStylePreset(
        id="urban_hype",
        name_el="Urban Hype",
        name_en="Urban Hype",
        mood="street-ready energy, dynamic but tasteful",
        camera="handheld-stabilized tracking, quick but smooth whip pans",
        lighting="golden-hour urban bounce, neon accents restrained",
    ),
    "soft_lifestyle": PromptStylePreset(
        id="soft_lifestyle",
        name_el="Soft Lifestyle",
        name_en="Soft Lifestyle",
        mood="calm Kinfolk lifestyle discovery, soft-sell",
        camera="gentle lateral slide, locked-off beauty inserts",
        lighting="soft window light, warm neutral tones",
    ),
}


def list_prompt_presets() -> List[PromptStylePreset]:
    return list(PROMPT_STYLE_PRESETS.values())


def get_prompt_preset(preset_id: str) -> PromptStylePreset:
    return PROMPT_STYLE_PRESETS.get(preset_id, PROMPT_STYLE_PRESETS["cinematic_commercial"])


def _aspect_label(aspect: str) -> str:
    a = (aspect or "").strip()
    if a.startswith("9:16"):
        return "9:16"
    if a.startswith("16:9"):
        return "16:9"
    if a.startswith("2:3"):
        return "2:3"
    if a.startswith("1:1"):
        return "1:1"
    return a or "9:16"


def _aspect_line(aspect: str) -> str:
    a = (aspect or "").strip()
    if a.startswith("9:16"):
        return (
            "Aspect ratio 9:16 vertical Story/TikTok/Reels (1080x1920). "
            "Phone-first vertical framing; keep subject centered in safe mobile crop."
        )
    if a.startswith("16:9"):
        return (
            "Aspect ratio 16:9 landscape YouTube (1920x1080). "
            "Widescreen cinematic framing for YouTube; horizontal composition, "
            "generous side headroom for titles, landscape camera move."
        )
    if a.startswith("2:3"):
        return (
            "Aspect ratio 2:3 Pinterest pin vertical (1080x1620). "
            "Classic Pinterest pin portrait framing; tall vertical composition "
            "optimized for Pinterest feed pins."
        )
    if a.startswith("1:1"):
        return (
            "Aspect ratio 1:1 square (1080x1080), feed-friendly Instagram/Facebook square."
        )
    return f"Aspect ratio {a}, compose the frame to fill the canvas cleanly."


def _normalize_beat_count(beat_count: int) -> int:
    return 5 if int(beat_count) == 5 else 3


def _duration_hint(beat_index: int, beat_count: int = 3) -> str:
    bc = _normalize_beat_count(beat_count)
    if bc == 5:
        windows = {
            1: "0:00–0:04 (first ~4s of ~20s stitched ad)",
            2: "0:04–0:08 (product reveal)",
            3: "0:08–0:12 (macro)",
            4: "0:12–0:17 (on-foot)",
            5: "0:17–0:22 (flat-lay CTA)",
        }
        window = windows.get(beat_index, "~4 seconds within the ~20s stitched ad")
        return (
            f"DURATION: ~4–5 seconds for this SINGLE clip ({window}). "
            f"ONE beat only — generate this clip alone; the editor will stitch beats later. "
            f"Tight pacing, one clear action, end on a clean hold for the cut."
        )
    windows = {
        1: "0:00–0:05 (first 5 seconds of the 15s stitched ad)",
        2: "0:05–0:10 (middle 5 seconds of the 15s stitched ad)",
        3: "0:10–0:15 (final 5 seconds of the 15s stitched ad)",
    }
    window = windows.get(beat_index, "exactly 5 seconds within the 15s stitched ad")
    return (
        f"DURATION: exactly ~5 seconds for this SINGLE clip ({window}). "
        f"ONE beat only — generate this clip alone; the editor will stitch beats later. "
        f"Tight pacing, one clear action, end on a clean hold for the cut."
    )


def _product_core(info: ProductInfo) -> str:
    brand = info.brand.strip() or "premium sneaker brand"
    model = safe_model_name(info.model.strip() or "signature silhouette")
    colorway = info.colorway.strip() or "signature colorway"
    specs = info.specs.strip() or "engineered cushioning, breathable upper, supportive midsole"
    return f"{brand} {model} in {colorway} colorway ({specs})"


def _overlay_bits(info: ProductInfo, ad_texts: Dict[str, str], which: str) -> str:
    wm = info.watermark.strip() or "SNEAKERNESS.EU"
    if which in ("beat1", "hook"):
        text = ad_texts.get("slide1_text") or ad_texts.get("hook", "")
        return (
            f"Optional subtle text overlay (max 8 words): '{text}'. "
            f"No hard UI. Soft typography only. Prefer overlay OFF if cluttered."
        )
    if which in ("beat2", "product"):
        text = ad_texts.get("slide2_text") or ad_texts.get("body", "")
        return (
            f"Optional clean soft overlay once: '{text}'. "
            f"Do NOT invent seals/badges. Soft typography only."
        )
    if which in ("beat3", "macro"):
        text = ad_texts.get("body") or "Engineered cushioning and support."
        return (
            f"Optional subtle tech overlay: '{text}'. No UI chrome. Soft typography only."
        )
    if which in ("beat4", "onfoot"):
        return (
            "Optional benefit/motion overlay (max 8 words). Soft typography only. "
            "No face, no UI chrome."
        )
    if which in ("beat5", "cta", "beat3_cta"):
        text = ad_texts.get("slide3_text") or ad_texts.get("cta", f"Discover more at {wm}")
        return (
            f"Soft discovery CTA overlay (optional): '{text}'. "
            f"No buy buttons, no LEARN MORE chrome. Soft typography only."
        )
    return "Minimal soft typography only. No invented badges."


def _music_line(beat_key: str, beat_count: int, music_mood: str, include_music: bool) -> str:
    if not include_music:
        return "Music: none — natural ambience / foley only."
    bc = _normalize_beat_count(beat_count)
    mmap = MUSIC_MAP_5 if bc == 5 else MUSIC_MAP_3
    base = mmap.get(beat_key, "")
    mood = (music_mood or "soft cinematic").strip()
    return (
        f"{base} Overall bed style: original {mood} instrumental only "
        f"(no recognizable licensed songs, no artist names); tasteful, commercial."
    )


def _audio_direction(
    *,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    beat: str = "beat1",
    beat_count: int = 3,
    ad_texts: Optional[Dict[str, str]] = None,
) -> str:
    ad_texts = ad_texts or {}
    bits: List[str] = []
    bits.append(_music_line(beat, beat_count, music_mood, include_music))

    if include_voice:
        lang = (
            "Greek (modern, clear, soft discovery tone)"
            if voice_lang == "el"
            else "English (clear, soft discovery tone)"
        )
        hook = ad_texts.get("hook") or "Tired of foot fatigue after long hours?"
        cta = ad_texts.get("cta") or "Discover more."
        body = ad_texts.get("body") or "Engineered support for all-day comfort."
        if beat in ("beat1", "hook"):
            line = hook
        elif beat in ("beat2", "product"):
            line = body
        elif beat in ("beat3", "macro") and _normalize_beat_count(beat_count) == 5:
            line = body
        elif beat in ("beat4", "onfoot"):
            line = body
        elif beat in ("beat5", "cta", "beat3") or beat.endswith("cta"):
            line = cta
        else:
            line = body
        bits.append(
            f"Voiceover ON — spoken {lang}, single calm narrator, anonymous; "
            f"no celebrity voice imitation. Suggested line: \"{line}\" "
            f"Timing: short phrases synced to the beat; never hard-sell verbs."
        )
    else:
        bits.append("Voiceover OFF — no spoken dialogue, no narrator.")

    return "Audio direction: " + " ".join(bits)


def build_music_bed_prompt(
    info: ProductInfo,
    beat_count: int = 3,
    music_mood: str = "soft cinematic",
    aspect: str = "9:16",
) -> str:
    """Standalone full music-bed prompt for optional stitch-time bed."""
    bc = _normalize_beat_count(beat_count)
    mood = (music_mood or "soft cinematic").strip()
    product = _product_core(info)
    ar = _aspect_label(aspect)
    if bc == 5:
        structure = (
            "Structure: sparse ambient/low-drum intro (0–4s) → bright melody + clearer beat "
            "on product reveal (4–8s) → short percussive/filtered texture hit for macro (8–12s) → "
            "forward groove for on-foot (12–17s, ~115 BPM) → open resolving chord for CTA with "
            "space under VO (17–22s)."
        )
        dur = "18–22 seconds"
        format_note = "five-beat stitched cutdown"
    else:
        structure = (
            "Structure: sparse ambient/low-drum intro (0–5s) → bright melody + clearer beat "
            "on hero reveal (5–10s) → texture hit into soft resolve with VO space (10–15s)."
        )
        dur = "exactly 15 seconds"
        format_note = "three-beat stitched social ad"

    prompt = (
        f"MUSIC PROMPT (FULL BED) — Grok / audio bed for sneaker commercial\n"
        f"Product: {product}\n"
        f"Aspect context: {ar} · Format: {format_note} · Duration: {dur}\n"
        f"Mood: original {mood} instrumental bed only.\n\n"
        f"{structure}\n\n"
        f"Modern trap-light or soft-cinematic drums, warm bass, motivational but not cheesy, "
        f"no lyrics, no sirens, no meme sounds, no recognizable licensed songs or artist names. "
        f"Easy loop-friendly ending. Duck under VO if present."
    )
    return soft_sanitize(prompt.strip(), info.watermark)


def music_lines_for_pack(beat_count: int = 3, music_mood: str = "soft cinematic") -> Dict[str, str]:
    bc = _normalize_beat_count(beat_count)
    mmap = MUSIC_MAP_5 if bc == 5 else MUSIC_MAP_3
    mood = (music_mood or "soft cinematic").strip()
    out: Dict[str, str] = {}
    order = (
        ["beat1", "beat2", "beat3", "beat4", "beat5"]
        if bc == 5
        else ["beat1", "beat2", "beat3"]
    )
    labels = {
        "beat1": "Beat 1 Hook",
        "beat2": "Beat 2 Product" if bc == 5 else "Beat 2 Hero",
        "beat3": "Beat 3 Macro" if bc == 5 else "Beat 3 Macro+CTA",
        "beat4": "Beat 4 On-foot",
        "beat5": "Beat 5 Flat-lay CTA",
    }
    for key in order:
        out[labels[key]] = (
            f"{mmap[key]} Overall bed style: original {mood} instrumental only."
        )
    return out


# ---------------------------------------------------------------------------
# Beat builders — per-beat single clips only
# ---------------------------------------------------------------------------

def build_beat1_hook(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    beat_count: int = 3,
) -> str:
    preset = preset or get_prompt_preset("cinematic_commercial")
    ad_texts = ad_texts or generate_ad_texts(info)
    bc = _normalize_beat_count(beat_count)
    problem = info.problem_desc.strip() or (
        "a tired worker sitting on stairs touching sore feet with work boots beside them"
    )
    product = _product_core(info)
    title = (
        "GROK VIDEO — SINGLE CLIP · BEAT 1: HOOK / PROBLEM (~4–5s)"
        if bc == 5
        else "GROK VIDEO — SINGLE CLIP · BEAT 1: HOOK / PROBLEM (~5s)"
    )
    scene = (
        f"Scene: Wide establishing lifestyle / problem beat. {problem}. "
        f"High emotion, relatable fatigue, tasteful and respectful — anonymous person, "
        f"face partially obscured or turned away OR legs-only crop (no recognizable celebrity). "
        f"Hero footwear may appear small in frame OR not yet fully revealed. "
        f"CRITICAL: composition MUST be wide/environment — do not repeat a tight studio product still. "
        f"Later beats (separate clips) will showcase {product}."
        if bc == 5
        else (
            f"Scene: Cinematic portrait video of {problem}. High emotion, relatable fatigue, "
            f"tasteful and respectful — anonymous person, face partially obscured or turned away "
            f"(no recognizable celebrity)."
        )
    )
    prompt = f"""{GROK_PREAMBLE_CLIP}

{title}
{_aspect_line(aspect)} {_duration_hint(1, bc)}

{scene}
Camera: {preset.camera}. Mood: {preset.mood}.
Lighting: {preset.lighting}, natural dramatic key with soft fill.
Motion: subtle breath, fabric movement, camera slowly pushes in on the feet/problem moment.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat1", beat_count=bc, ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "beat1")}

Style: photorealistic 8k commercial, filmic color grade, shallow DOF.
{_quality_block(info)}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


def build_beat2_hero(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    beat_count: int = 3,
) -> str:
    preset = preset or get_prompt_preset("cinematic_commercial")
    ad_texts = ad_texts or generate_ad_texts(info)
    bc = _normalize_beat_count(beat_count)
    product = _product_core(info)
    env = info.env_desc.strip()
    props = info.props_desc.strip()
    title = (
        "GROK VIDEO — SINGLE CLIP · BEAT 2: PRODUCT 3/4 HERO (~4–5s)"
        if bc == 5
        else "GROK VIDEO — SINGLE CLIP · BEAT 2: HERO PRODUCT (~5s)"
    )
    scene = (
        f"Scene: Clean 3/4 hero reveal of {product} — studio-to-location clarity beat "
        f"in {env}. EDC lifestyle props nearby: {props}. Shoes slightly staggered; "
        f"crisp lighting that pops materials and colorway. "
        f"CRITICAL: distinct from wide hook — this is the clarity/reveal product beat only."
        if bc == 5
        else (
            f"Scene: Studio-to-location product hero of {product} placed on a surface in {env}. "
            f"EDC lifestyle props nearby: {props}."
        )
    )
    prompt = f"""{GROK_PREAMBLE_CLIP}

{title}
{_aspect_line(aspect)} {_duration_hint(2, bc)}

{scene}
Camera: slow 180° orbit / gentle push-in on the sneaker pair, hero angle three-quarter front. {preset.camera}.
Lighting: {preset.lighting}. Commercial reflections on mesh and midsole.
Motion: subtle shoe settle, light dust motes, prop stillness with micro parallax.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat2", beat_count=bc, ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "beat2")}

Style: photorealistic sneaker commercial, crisp materials, accurate silhouette, {preset.mood}.
{_quality_block(info)}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


def build_beat3_specs_cta(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    beat_count: int = 3,
) -> str:
    """3-beat mode: macro + soft CTA combined."""
    preset = preset or get_prompt_preset("macro_tech")
    ad_texts = ad_texts or generate_ad_texts(info)
    product = _product_core(info)
    env = info.env_desc.strip()
    specs = info.specs.strip() or "cushioning geometry, outsole traction, upper knit/mesh detail"
    prompt = f"""{GROK_PREAMBLE_CLIP}

GROK VIDEO — SINGLE CLIP · BEAT 3: SPECS / MACRO + SOFT CTA (~5s)
{_aspect_line(aspect)} {_duration_hint(3, 3)}

Scene: Sleek macro detail close-up video of the sole, cushioning, and material texture of {product}, background suggesting {env}.
Focus on: {specs}.
Camera: macro glide across midsole → outsole lugs → upper texture, rack focus. {preset.camera}.
Lighting: {preset.lighting}, tactile speculars.
Motion: ultra-slow move ending on a clean hold for soft CTA readability.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat3", beat_count=3, ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "beat3_cta")}

Style: commercial macro product film, photorealistic 8k, {preset.mood}.
{_quality_block(info)}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


def build_beat3_macro(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
) -> str:
    preset = preset or get_prompt_preset("macro_tech")
    ad_texts = ad_texts or generate_ad_texts(info)
    product = _product_core(info)
    specs = info.specs.strip() or "cushioning geometry, outsole traction, upper knit/mesh detail"
    prompt = f"""{GROK_PREAMBLE_CLIP}

GROK VIDEO — SINGLE CLIP · BEAT 3: MACRO SOLE / CUSHION (~4–5s)
{_aspect_line(aspect)} {_duration_hint(3, 5)}

Scene: MACRO fill-frame move across the midsole and outsole of {product} — foam texture and rocker/sole curve dominate the frame; no full pair on a bench. Focus on: {specs}.
Camera: slow glide or subtle orbit; sharp detail. {preset.camera}.
Lighting: {preset.lighting}, tactile speculars.
Motion: ultra-slow tech feel.
CRITICAL: composition MUST be macro sole/cushion only — visually distinct from product 3/4 hero.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat3", beat_count=5, ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "macro")}

Style: commercial macro product film, photorealistic 8k detail, {preset.mood}.
{_quality_block(info)}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


def build_beat4_onfoot(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
) -> str:
    preset = preset or get_prompt_preset("urban_hype")
    ad_texts = ad_texts or generate_ad_texts(info)
    product = _product_core(info)
    env = info.env_desc.strip() or "outdoor track or urban path"
    prompt = f"""{GROK_PREAMBLE_CLIP}

GROK VIDEO — SINGLE CLIP · BEAT 4: ON-FOOT NO-FACE (~4–5s)
{_aspect_line(aspect)} {_duration_hint(4, 5)}

Scene: On-foot crop from the waist down of an anonymous adult walking/jogging easy in {env}; natural look; NO face. {product} clearly visible in motion; correct silhouette and branding cues. Benefit/motion energy.
Camera: tracking / stabilized follow at foot-to-knee height. {preset.camera}.
Lighting: {preset.lighting}.
Motion: natural stride, attached ground shadows, NO floaty/warped run, NO morph of the shoe.
CRITICAL: distinct on-foot motion beat — not a studio still, not macro sole.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat4", beat_count=5, ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "onfoot")}

Style: photoreal lifestyle commercial, natural physics, {preset.mood}.
{_quality_block(info)}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


def build_beat5_flatlay_cta(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
) -> str:
    preset = preset or get_prompt_preset("soft_lifestyle")
    ad_texts = ad_texts or generate_ad_texts(info)
    product = _product_core(info)
    env = info.env_desc.strip()
    props = info.props_desc.strip()
    prompt = f"""{GROK_PREAMBLE_CLIP}

GROK VIDEO — SINGLE CLIP · BEAT 5: FLAT-LAY / SOFT CTA (~4–5s)
{_aspect_line(aspect)} {_duration_hint(5, 5)}

Scene: Top-down flat lay OR clean still of {product} returning to calm — soft landing energy for end card. Environment cue: {env}. Props: {props}. Optional soft end-card space (no giant headline).
Camera: gentle settle / locked-off beauty. {preset.camera}.
Lighting: {preset.lighting}.
Motion: soft settle into hold for CTA readability / VO space.
CRITICAL: resolve/CTA composition — distinct from hook / product / macro / on-foot.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat5", beat_count=5, ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "cta")}

Style: photoreal commercial flat-lay, calm resolve, {preset.mood}.
{_quality_block(info)}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


# ---------------------------------------------------------------------------
# Pack builder — per-beat only (no continuous primary)
# ---------------------------------------------------------------------------

def build_grok_prompt_pack(
    info: ProductInfo,
    aspect: str = "9:16",
    preset_id: str = "cinematic_commercial",
    include_beats: bool = True,
    include_continuous: bool = False,  # v5: OFF by default — one clip per beat
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    beat_count: int = 3,
) -> Dict[str, str]:
    """
    Ordered dict of labeled Grok SINGLE-CLIP prompts.
    include_continuous defaults False in v5 (soft-deprecated; not primary UX).
    """
    preset = get_prompt_preset(preset_id)
    hero_preset = preset
    macro_preset = get_prompt_preset("macro_tech") if preset_id != "macro_tech" else preset
    onfoot_preset = get_prompt_preset("urban_hype") if preset_id == "cinematic_commercial" else preset
    flat_preset = get_prompt_preset("soft_lifestyle") if preset_id == "cinematic_commercial" else preset
    ad_texts = ad_texts or generate_ad_texts(info)
    bc = _normalize_beat_count(beat_count)

    pack: Dict[str, str] = {}
    ar_label = _aspect_label(aspect)
    audio_kw = dict(
        include_voice=include_voice,
        voice_lang=voice_lang,
        include_music=include_music,
        music_mood=music_mood,
    )

    if include_beats:
        if bc == 5:
            pack[f"Grok · Beat 1 Hook (~4–5s) ({ar_label})"] = build_beat1_hook(
                info, aspect, hero_preset, ad_texts, beat_count=5, **audio_kw
            )
            pack[f"Grok · Beat 2 Product 3/4 (~4–5s) ({ar_label})"] = build_beat2_hero(
                info, aspect, hero_preset, ad_texts, beat_count=5, **audio_kw
            )
            pack[f"Grok · Beat 3 Macro (~4–5s) ({ar_label})"] = build_beat3_macro(
                info, aspect, macro_preset, ad_texts, **audio_kw
            )
            pack[f"Grok · Beat 4 On-foot (~4–5s) ({ar_label})"] = build_beat4_onfoot(
                info, aspect, onfoot_preset, ad_texts, **audio_kw
            )
            pack[f"Grok · Beat 5 Flat-lay CTA (~4–5s) ({ar_label})"] = build_beat5_flatlay_cta(
                info, aspect, flat_preset, ad_texts, **audio_kw
            )
        else:
            pack[f"Grok · Beat 1 Hook (~5s) ({ar_label})"] = build_beat1_hook(
                info, aspect, hero_preset, ad_texts, beat_count=3, **audio_kw
            )
            pack[f"Grok · Beat 2 Hero (~5s) ({ar_label})"] = build_beat2_hero(
                info, aspect, hero_preset, ad_texts, beat_count=3, **audio_kw
            )
            pack[f"Grok · Beat 3 Macro+CTA (~5s) ({ar_label})"] = build_beat3_specs_cta(
                info, aspect, macro_preset, ad_texts, beat_count=3, **audio_kw
            )

    # Music: full bed + per-beat lines (for stitch-time bed / Grok audio)
    if include_music:
        pack[f"Music · Full bed ({'5-beat ~20s' if bc == 5 else '3-beat 15s'})"] = (
            build_music_bed_prompt(info, beat_count=bc, music_mood=music_mood, aspect=aspect)
        )
        for label, line in music_lines_for_pack(bc, music_mood).items():
            pack[f"Music · {label}"] = line

    # Continuous intentionally omitted unless caller forces include_continuous=True
    if include_continuous:
        pack[f"Grok · Continuous (legacy, not recommended) ({ar_label})"] = (
            "LEGACY continuous multi-beat prompt is disabled in Video Studio v5. "
            "Generate ONE Grok clip per beat, then stitch in Συναρμολόγηση."
        )

    return pack


def build_pack_meta_json(
    info: ProductInfo,
    ad_texts: Dict[str, str],
    *,
    aspect: str = "9:16",
    beat_count: int = 3,
    music_mood: str = "soft cinematic",
    include_voice: bool = False,
    voice_lang: str = "en",
) -> Dict:
    bc = _normalize_beat_count(beat_count)
    wm = info.watermark.strip() or "SNEAKERNESS.EU"
    brand = info.brand.strip()
    model = safe_model_name(info.model.strip())
    if bc == 5:
        beats = [
            {"role": "hook", "t": "0-4", "duration_s": 4.5, "music": "sparse_intro_tension"},
            {"role": "product_3_4", "t": "4-8", "duration_s": 4.5, "music": "reveal_melody"},
            {"role": "macro_sole", "t": "8-12", "duration_s": 4.5, "music": "texture_hit"},
            {"role": "on_foot", "t": "12-17", "duration_s": 5.0, "music": "forward_groove_115bpm"},
            {"role": "flat_lay_cta", "t": "17-22", "duration_s": 5.0, "music": "resolve_open_for_vo"},
        ]
        duration = 22
        fmt = "stitched_5"
    else:
        beats = [
            {"role": "hook", "t": "0-5", "duration_s": 5.0, "music": "sparse_intro_tension"},
            {"role": "hero", "t": "5-10", "duration_s": 5.0, "music": "reveal_melody"},
            {"role": "macro_cta", "t": "10-15", "duration_s": 5.0, "music": "texture_to_resolve"},
        ]
        duration = 15
        fmt = "stitched_3"
    return {
        "product": f"{brand} {model}".strip(),
        "brand": brand,
        "model": model,
        "colorway": info.colorway.strip(),
        "specs": info.specs.strip(),
        "aspect": _aspect_label(aspect),
        "format": fmt,
        "workflow": "one_clip_per_beat",
        "beat_count": bc,
        "duration_sec": duration,
        "watermark": wm,
        "music_mood": music_mood,
        "include_voice": include_voice,
        "voice_lang": voice_lang,
        "beats": beats,
        "vo": ad_texts.get("cta") or ad_texts.get("hook") or f"Discover more at {wm}.",
        "tag": info.tag,
        "badge": info.badge,
    }
