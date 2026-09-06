"""Grok (xAI) video prompt pack builder — cinematic sneaker commercial beats.

Primary deliverable: copy-paste ready prompts for Grok video / Aurora / image-to-video.
Structured like Sneakerness carousel slides but as VIDEO beats + one continuous reel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from captions import ProductInfo, generate_ad_texts, safe_model_name, soft_sanitize


NEGATIVE_CONSTRAINTS = (
    "STRICT NEGATIVE CONSTRAINTS: no celebrity faces or recognizable athletes, "
    "no Kobe/Jordan/LeBron/Messi/Ronaldo/Curry likeness, no fake or distorted brand logos, "
    "no misspelled logos, no hard UI chrome, no app mockups, no carousel numbering, "
    "no 'Slide X of Y', no page numbers, no stock watermark clutter, no hard-sell "
    "buy/shop buttons, no shopping cart icons, no deepfake faces. Keep product logos "
    "accurate only if clearly visible on the real shoe; otherwise keep logo-free hero angles."
)

GROK_PREAMBLE = (
    "You are generating a cinematic sneaker commercial video for Grok (xAI). "
    "TARGET TOTAL DURATION: exactly 15 seconds (15s). "
    "Photorealistic motion, premium commercial grade, natural physics, smooth camera. "
    "Frame composition must match the requested aspect ratio exactly. "
    "Pacing must fit a finished 15-second social ad — no longer, no shorter."
)


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
    """Short label for UI keys / pack titles."""
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
    """Explicit aspect framing instructions for Grok video prompts."""
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


def _duration_hint(beat: bool = True, beat_index: int = 0) -> str:
    """All prompts are designed for a finished **15-second** video.
    Beats are ~5s each (3×5s = 15s). Continuous reel is exactly 15s.
    """
    if beat:
        windows = {
            1: "0:00–0:05 (first 5 seconds of the 15s ad)",
            2: "0:05–0:10 (middle 5 seconds of the 15s ad)",
            3: "0:10–0:15 (final 5 seconds of the 15s ad)",
        }
        window = windows.get(beat_index, "exactly 5 seconds within the 15s ad")
        return (
            f"DURATION: exactly 5 seconds for this beat ({window}). "
            f"Part of a complete 15-second video (3 beats × 5s). "
            f"Tight pacing, one clear action, end on a clean hold for the cut."
        )
    return (
        "DURATION: exactly 15 seconds total (15s finished video). "
        "Three beats inside one timeline: 0–5s hook, 5–10s hero, 10–15s macro+CTA. "
        "Do not exceed 15 seconds; do not end before 15 seconds."
    )


def _product_core(info: ProductInfo) -> str:
    brand = info.brand.strip() or "premium sneaker brand"
    model = safe_model_name(info.model.strip() or "signature silhouette")
    colorway = info.colorway.strip() or "signature colorway"
    specs = info.specs.strip() or "engineered cushioning, breathable upper, supportive midsole"
    return f"{brand} {model} in {colorway} colorway ({specs})"


def _overlay_bits(info: ProductInfo, ad_texts: Dict[str, str], which: str) -> str:
    wm = info.watermark.strip() or "SNEAKERNESS.EU"
    tag = info.tag
    badge = info.badge
    if which == "beat1":
        text = ad_texts.get("slide1_text") or ad_texts.get("hook", "")
        return (
            f"Optional subtle text overlay (max 8 words): '{text}'. "
            f"No hard UI. Soft typography only."
        )
    if which == "beat2":
        text = ad_texts.get("slide2_text") or ad_texts.get("body", "")
        return (
            f"Top-left fabric tag reading '{tag}', top-right badge '{badge}'. "
            f"Clean overlay: '{text}'. Bottom discreet watermark '{wm}'."
        )
    if which == "beat3":
        text = ad_texts.get("slide3_text") or ad_texts.get("cta", f"Discover more at {wm}")
        return (
            f"Floating bold watermark '{wm}' and soft discovery CTA overlay: '{text}'. "
            f"No buy buttons."
        )
    # continuous
    return (
        f"Minimal overlays only at beat transitions: hook then product name then soft CTA "
        f"'{ad_texts.get('cta', f'Discover more at {wm}')}'. Watermark '{wm}'. "
        f"Tags/badges optional and tasteful."
    )



def _audio_direction(
    *,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    beat: str = "continuous",
    ad_texts: Optional[Dict[str, str]] = None,
) -> str:
    """Build explicit audio / VO / music cues for Grok video prompts."""
    ad_texts = ad_texts or {}
    bits: list[str] = []

    if include_music:
        mood = (music_mood or "soft cinematic").strip()
        bits.append(
            f"Music: original {mood} instrumental bed only "
            f"(no recognizable licensed songs, no artist names); "
            f"tasteful, commercial, duck under VO if present."
        )
    else:
        bits.append("Music: none — natural ambience / foley only.")

    if include_voice:
        lang = "Greek (modern, clear, soft discovery tone)" if voice_lang == "el" else "English (clear, soft discovery tone)"
        hook = ad_texts.get("hook") or "Tired of foot fatigue after long hours?"
        cta = ad_texts.get("cta") or "Discover more."
        body = ad_texts.get("body") or "Engineered support for all-day comfort."
        if beat == "beat1":
            line = hook
        elif beat == "beat2":
            line = body
        elif beat == "beat3":
            line = cta
        else:
            line = f"{hook} Then: {body} End soft CTA: {cta}"
        bits.append(
            f"Voiceover ON — spoken {lang}, single calm narrator, anonymous; "
            f"no celebrity voice imitation. Suggested line: \"{line}\" "
            f"Timing: short phrases synced to the beat; never hard-sell verbs."
        )
    else:
        bits.append("Voiceover OFF — no spoken dialogue, no narrator.")

    return "Audio direction: " + " ".join(bits)


def build_beat1_hook(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
) -> str:
    preset = preset or get_prompt_preset("cinematic_commercial")
    ad_texts = ad_texts or generate_ad_texts(info)
    problem = info.problem_desc.strip() or (
        "a tired worker sitting on stairs touching sore feet with work boots beside them"
    )
    prompt = f"""{GROK_PREAMBLE}

GROK VIDEO — BEAT 1: HOOK / PROBLEM SCENE (15s ad · seconds 0–5)
{_aspect_line(aspect)} {_duration_hint(True, 1)}

Scene: Cinematic portrait video of {problem}. High emotion, relatable fatigue, tasteful and respectful — anonymous person, face partially obscured or turned away (no recognizable celebrity).
Camera: {preset.camera}. Mood: {preset.mood}.
Lighting: {preset.lighting}, natural dramatic key with soft fill.
Motion: subtle breath, fabric movement, camera slowly pushes in on the feet/problem moment.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat1", ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "beat1")}

Style: photorealistic 8k commercial, filmic color grade, shallow DOF.
{NEGATIVE_CONSTRAINTS}
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
) -> str:
    preset = preset or get_prompt_preset("cinematic_commercial")
    ad_texts = ad_texts or generate_ad_texts(info)
    product = _product_core(info)
    env = info.env_desc.strip()
    props = info.props_desc.strip()
    prompt = f"""{GROK_PREAMBLE}

GROK VIDEO — BEAT 2: HERO PRODUCT SHOWCASE (15s ad · seconds 5–10)
{_aspect_line(aspect)} {_duration_hint(True, 2)}

Scene: Studio-to-location product hero of {product} placed on a surface in {env}.
EDC lifestyle props nearby: {props}.
Camera: slow 180° orbit / gentle push-in on the sneaker pair, hero angle three-quarter front. {preset.camera}.
Lighting: {preset.lighting}. Commercial reflections on mesh and midsole.
Motion: subtle shoe settle, light dust motes, prop stillness with micro parallax.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat2", ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "beat2")}

Style: photorealistic sneaker commercial, crisp materials, accurate silhouette, {preset.mood}.
{NEGATIVE_CONSTRAINTS}
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
) -> str:
    preset = preset or get_prompt_preset("macro_tech")
    ad_texts = ad_texts or generate_ad_texts(info)
    product = _product_core(info)
    env = info.env_desc.strip()
    specs = info.specs.strip() or "cushioning geometry, outsole traction, upper knit/mesh detail"
    prompt = f"""{GROK_PREAMBLE}

GROK VIDEO — BEAT 3: SPECS / MACRO + SOFT CTA (15s ad · seconds 10–15)
{_aspect_line(aspect)} {_duration_hint(True, 3)}

Scene: Sleek macro detail close-up video of the sole, cushioning, and material texture of {product}, background suggesting {env}.
Focus on: {specs}.
Camera: macro glide across midsole → outsole lugs → upper texture, rack focus. {preset.camera}.
Lighting: {preset.lighting}, tactile speculars.
Motion: ultra-slow move ending on a clean hold for soft CTA readability.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="beat3", ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "beat3")}

Style: commercial macro product film, photorealistic 8k, {preset.mood}.
{NEGATIVE_CONSTRAINTS}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


def build_continuous_reel(
    info: ProductInfo,
    aspect: str = "9:16",
    preset: Optional[PromptStylePreset] = None,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
) -> str:
    preset = preset or get_prompt_preset("cinematic_commercial")
    ad_texts = ad_texts or generate_ad_texts(info)
    product = _product_core(info)
    problem = info.problem_desc.strip()
    env = info.env_desc.strip()
    props = info.props_desc.strip()
    prompt = f"""{GROK_PREAMBLE}

GROK VIDEO — CONTINUOUS 15-SECOND REEL (exact length: 15 seconds)
{_aspect_line(aspect)} {_duration_hint(False)}

One cohesive 15-second sneaker commercial with three internal beats
(hard cuts OK if seamless color-matched). TOTAL RUNTIME = 15 SECONDS:

BEAT A (0–5s) HOOK: Open on {problem}. Anonymous subject, no celebrity likeness. Emotional fatigue → hope. End ready for cut at 0:05.
BEAT B (5–10s) HERO: Transition to {product} on {env}, props: {props}. Slow orbit / push-in hero showcase. End at 0:10.
BEAT C (10–15s) MACRO + SOFT CTA: Macro of cushioning/outsole, hold final frame for soft discovery CTA; finish exactly at 0:15.

Camera language: {preset.camera}. Mood: {preset.mood}. Lighting: {preset.lighting}.
{_audio_direction(include_voice=include_voice, voice_lang=voice_lang, include_music=include_music, music_mood=music_mood, beat="continuous", ad_texts=ad_texts)}
{_overlay_bits(info, ad_texts, "continuous")}

Image-to-video note (if starting from uploaded sneaker photo): preserve exact sneaker identity, colorway, and silhouette; animate camera and light only; do not morph logos.
Aurora / Grok video style: cinematic motion, stable product geometry, commercial grade.

Style: photorealistic 8k sneaker commercial, filmic grade, social-ready.
{NEGATIVE_CONSTRAINTS}
"""
    return soft_sanitize(prompt.strip(), info.watermark)


def build_grok_prompt_pack(
    info: ProductInfo,
    aspect: str = "9:16",
    preset_id: str = "cinematic_commercial",
    include_beats: bool = True,
    include_continuous: bool = True,
    ad_texts: Optional[Dict[str, str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
) -> Dict[str, str]:
    """
    Return ordered dict of labeled Grok prompts ready to copy-paste.
    Keys are human-readable labels for the UI.
    """
    preset = get_prompt_preset(preset_id)
    # Use cinematic for hook/hero unless user picked another; macro for beat3 always benefits
    hero_preset = preset
    macro_preset = get_prompt_preset("macro_tech") if preset_id != "macro_tech" else preset
    ad_texts = ad_texts or generate_ad_texts(info)

    pack: Dict[str, str] = {}
    ar_label = _aspect_label(aspect)
    audio_kw = dict(
        include_voice=include_voice,
        voice_lang=voice_lang,
        include_music=include_music,
        music_mood=music_mood,
    )

    if include_beats:
        pack[f"Grok · 15s Beat 1 Hook 0–5s ({ar_label})"] = build_beat1_hook(
            info, aspect, hero_preset, ad_texts, **audio_kw
        )
        pack[f"Grok · 15s Beat 2 Hero 5–10s ({ar_label})"] = build_beat2_hero(
            info, aspect, hero_preset, ad_texts, **audio_kw
        )
        pack[f"Grok · 15s Beat 3 Macro+CTA 10–15s ({ar_label})"] = build_beat3_specs_cta(
            info, aspect, macro_preset, ad_texts, **audio_kw
        )
    if include_continuous:
        pack[f"Grok · Continuous 15s Reel ({ar_label})"] = build_continuous_reel(
            info, aspect, hero_preset, ad_texts, **audio_kw
        )
    return pack


def dual_aspect_pack(
    info: ProductInfo,
    preset_id: str = "cinematic_commercial",
    ad_texts: Optional[Dict[str, str]] = None,
    aspects: Optional[List[str]] = None,
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
) -> Dict[str, str]:
    """Generate packs for multiple aspects (default: 9:16 + 1:1)."""
    ad_texts = ad_texts or generate_ad_texts(info)
    aspects = aspects or ["9:16", "1:1"]
    out: Dict[str, str] = {}
    for ar in aspects:
        out.update(
            build_grok_prompt_pack(
                info,
                ar,
                preset_id,
                True,
                True,
                ad_texts,
                include_voice=include_voice,
                voice_lang=voice_lang,
                include_music=include_music,
                music_mood=music_mood,
            )
        )
    return out
