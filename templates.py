"""Video slideshow templates + Grok prompt style preset helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# Re-export prompt presets for UI convenience
from grok_prompts import PROMPT_STYLE_PRESETS, PromptStylePreset, get_prompt_preset, list_prompt_presets


@dataclass(frozen=True)
class VideoTemplate:
    id: str
    name_el: str
    name_en: str
    description_el: str
    aspect: str  # "9:16" | "1:1" | "16:9" | "2:3"
    width: int
    height: int
    bg_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]
    secondary_text_color: Tuple[int, int, int]
    font_style: str  # "minimal" | "bold" | "story"
    overlay_layout: str  # "bottom" | "center" | "top_bottom"
    default_duration: float
    transition: str  # "cut" | "crossfade" | "zoom"
    ken_burns: bool = False
    caption_style: str = "soft_discovery"
    prompt_preset_id: str = "cinematic_commercial"


TEMPLATES: Dict[str, VideoTemplate] = {
    "clean_reel": VideoTemplate(
        id="clean_reel",
        name_el="Καθαρό Product Reel",
        name_en="Clean Product Reel",
        description_el="Μινιμαλιστικό — ιδανικό για τοπικό slideshow + soft lifestyle Grok prompts.",
        aspect="1:1",
        width=1080,
        height=1080,
        bg_color=(12, 12, 14),
        accent_color=(255, 255, 255),
        text_color=(255, 255, 255),
        secondary_text_color=(180, 180, 185),
        font_style="minimal",
        overlay_layout="bottom",
        default_duration=2.5,
        transition="crossfade",
        ken_burns=True,
        caption_style="soft_discovery",
        prompt_preset_id="soft_lifestyle",
    ),
    "hype_drop": VideoTemplate(
        id="hype_drop",
        name_el="Hype Drop",
        name_en="Hype Drop",
        description_el="Έντονο κείμενο, γρήγορα cuts — urban hype Grok style.",
        aspect="1:1",
        width=1080,
        height=1080,
        bg_color=(8, 8, 10),
        accent_color=(255, 45, 85),
        text_color=(255, 255, 255),
        secondary_text_color=(255, 200, 50),
        font_style="bold",
        overlay_layout="center",
        default_duration=1.4,
        transition="cut",
        ken_burns=False,
        caption_style="short",
        prompt_preset_id="urban_hype",
    ),
    "story_vertical": VideoTemplate(
        id="story_vertical",
        name_el="Story / Vertical 9:16",
        name_en="Story / Vertical 9:16",
        description_el="Κάθετο για Instagram Stories & TikTok — cinematic commercial Grok.",
        aspect="9:16",
        width=1080,
        height=1920,
        bg_color=(10, 10, 16),
        accent_color=(0, 229, 255),
        text_color=(255, 255, 255),
        secondary_text_color=(200, 210, 230),
        font_style="story",
        overlay_layout="top_bottom",
        default_duration=2.2,
        transition="crossfade",
        ken_burns=True,
        caption_style="story",
        prompt_preset_id="cinematic_commercial",
    ),
    "youtube_landscape": VideoTemplate(
        id="youtube_landscape",
        name_el="YouTube 16:9 Landscape",
        name_en="YouTube 16:9 Landscape",
        description_el="Οριζόντιο 1920×1080 για YouTube — cinematic widescreen Grok.",
        aspect="16:9",
        width=1920,
        height=1080,
        bg_color=(10, 10, 14),
        accent_color=(255, 45, 85),
        text_color=(255, 255, 255),
        secondary_text_color=(200, 205, 215),
        font_style="minimal",
        overlay_layout="bottom",
        default_duration=2.4,
        transition="crossfade",
        ken_burns=True,
        caption_style="soft_discovery",
        prompt_preset_id="cinematic_commercial",
    ),
    "pinterest_pin": VideoTemplate(
        id="pinterest_pin",
        name_el="Pinterest 2:3 Pin",
        name_en="Pinterest 2:3 Pin",
        description_el="Κλασικό Pinterest pin 1080×1620 (2:3) — soft lifestyle Grok.",
        aspect="2:3",
        width=1080,
        height=1620,
        bg_color=(14, 12, 12),
        accent_color=(230, 0, 35),
        text_color=(255, 255, 255),
        secondary_text_color=(220, 200, 200),
        font_style="story",
        overlay_layout="top_bottom",
        default_duration=2.3,
        transition="crossfade",
        ken_burns=True,
        caption_style="soft_discovery",
        prompt_preset_id="soft_lifestyle",
    ),
}


def list_templates() -> List[VideoTemplate]:
    return list(TEMPLATES.values())


def get_template(template_id: str) -> VideoTemplate:
    if template_id not in TEMPLATES:
        raise KeyError(f"Unknown template: {template_id}")
    return TEMPLATES[template_id]


def template_options_el() -> Dict[str, str]:
    """Map display label (EL) -> template id."""
    return {f"{t.name_el} ({t.aspect})": t.id for t in TEMPLATES.values()}


def prompt_preset_options_el() -> Dict[str, str]:
    """Map display label -> preset id."""
    return {f"{p.name_el}": p.id for p in list_prompt_presets()}



# Canonical pixel sizes for aspect ratios (local slideshow + docs)
ASPECT_PIXELS = {
    "9:16": (1080, 1920),   # Story / TikTok / Reels
    "1:1": (1080, 1080),    # Square feed
    "16:9": (1920, 1080),   # YouTube landscape
    "2:3": (1080, 1620),    # Pinterest classic pin
}

ASPECT_OPTIONS_EL = {
    "9:16 Story/TikTok/Reels (κάθετο)": "9:16",
    "1:1 Square (τετράγωνο)": "1:1",
    "16:9 YouTube (οριζόντιο landscape)": "16:9",
    "2:3 Pinterest Pin (κλασικό pin)": "2:3",
}


def aspect_pixels(aspect: str) -> tuple:
    """Return (width, height) for a known aspect key."""
    key = (aspect or "9:16").strip()
    for k, wh in ASPECT_PIXELS.items():
        if key.startswith(k):
            return wh
    return ASPECT_PIXELS["9:16"]


def list_aspect_options_el() -> dict:
    """Map bilingual display label -> aspect id."""
    return dict(ASPECT_OPTIONS_EL)

__all__ = [
    "VideoTemplate",
    "TEMPLATES",
    "list_templates",
    "get_template",
    "template_options_el",
    "prompt_preset_options_el",
    "ASPECT_PIXELS",
    "ASPECT_OPTIONS_EL",
    "aspect_pixels",
    "list_aspect_options_el",
    "PROMPT_STYLE_PRESETS",
    "PromptStylePreset",
    "get_prompt_preset",
    "list_prompt_presets",
]
