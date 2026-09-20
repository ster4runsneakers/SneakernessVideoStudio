"""Beat cards + pack export helpers for Video Studio v5 (one clip per beat)."""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence

from captions import (
    ProductInfo,
    build_content_pack_text,
    generate_ad_texts,
    safe_model_name,
)
from grok_prompts import (
    build_grok_prompt_pack,
    build_pack_meta_json,
    get_prompt_preset,
    list_prompt_presets,
    music_lines_for_pack,
)


BEAT_ROLES_3 = [
    {"index": 1, "role": "hook", "label_el": "Hook / Πρόβλημα", "label_en": "Hook / Problem", "duration_s": 5.0},
    {"index": 2, "role": "hero", "label_el": "Hero προϊόν", "label_en": "Hero product", "duration_s": 5.0},
    {"index": 3, "role": "macro_cta", "label_el": "Macro + Soft CTA", "label_en": "Macro + Soft CTA", "duration_s": 5.0},
]

BEAT_ROLES_5 = [
    {"index": 1, "role": "hook", "label_el": "Hook / Πρόβλημα", "label_en": "Hook / Problem", "duration_s": 4.5},
    {"index": 2, "role": "product_3_4", "label_el": "Product 3/4", "label_en": "Product 3/4 reveal", "duration_s": 4.5},
    {"index": 3, "role": "macro_sole", "label_el": "Macro σόλα", "label_en": "Macro sole", "duration_s": 4.5},
    {"index": 4, "role": "on_foot", "label_el": "On-foot", "label_en": "On-foot motion", "duration_s": 5.0},
    {"index": 5, "role": "flat_lay_cta", "label_el": "Flat-lay CTA", "label_en": "Flat-lay soft CTA", "duration_s": 5.0},
]


@dataclass
class BeatCard:
    index: int
    role: str
    label_el: str
    label_en: str
    duration_s: float
    shot_prompt: str
    music_prompt: str
    pack_key: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


def beat_roles(beat_count: int = 3) -> List[Dict]:
    return BEAT_ROLES_5 if int(beat_count) == 5 else BEAT_ROLES_3


def _match_shot_key(pack: Dict[str, str], index: int) -> Optional[str]:
    needle = f"Beat {index}"
    for k in pack:
        if k.startswith("Grok") and needle in k:
            return k
    return None


def _match_music_key(pack: Dict[str, str], index: int, role_label_en: str) -> Optional[str]:
    # Prefer Music · Beat N …
    for k in pack:
        if k.startswith("Music · Beat") and f"Beat {index}" in k:
            return k
    # Fallback: music_lines labels
    for k in pack:
        if k.startswith("Music ·") and role_label_en.split()[0].lower() in k.lower():
            return k
    return None


def build_beat_cards(
    info: ProductInfo,
    *,
    beat_count: int = 5,
    aspect: str = "9:16",
    preset_id: str = "cinematic_commercial",
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    ad_texts: Optional[Dict[str, str]] = None,
) -> List[BeatCard]:
    """Build structured BeatCard list — one Grok clip prompt per beat."""
    ad_texts = ad_texts or generate_ad_texts(info)
    pack = build_grok_prompt_pack(
        info,
        aspect=aspect,
        preset_id=preset_id,
        include_beats=True,
        include_continuous=False,
        ad_texts=ad_texts,
        include_voice=include_voice,
        voice_lang=voice_lang,
        include_music=include_music,
        music_mood=music_mood,
        beat_count=beat_count,
    )
    cards: List[BeatCard] = []
    for meta in beat_roles(beat_count):
        idx = meta["index"]
        shot_key = _match_shot_key(pack, idx)
        music_key = _match_music_key(pack, idx, meta["label_en"])
        shot = pack.get(shot_key, "") if shot_key else ""
        music = pack.get(music_key, "") if music_key else ""
        if not music and include_music:
            # fallback from music_lines_for_pack
            lines = music_lines_for_pack(beat_count, music_mood)
            for lab, line in lines.items():
                if f"Beat {idx}" in lab:
                    music = line
                    break
        cards.append(
            BeatCard(
                index=idx,
                role=meta["role"],
                label_el=meta["label_el"],
                label_en=meta["label_en"],
                duration_s=float(meta["duration_s"]),
                shot_prompt=shot,
                music_prompt=music,
                pack_key=shot_key or "",
            )
        )
    return cards


def pack_dict_from_cards(cards: Sequence[BeatCard], *, include_music_bed: bool = True, music_bed: str = "") -> Dict[str, str]:
    """Flatten BeatCards into labeled dict for captions.build_content_pack_text."""
    out: Dict[str, str] = {}
    for c in cards:
        label = c.pack_key or f"Grok · Beat {c.index} {c.label_en}"
        out[label] = c.shot_prompt
        if c.music_prompt:
            out[f"Music · Beat {c.index} {c.label_en}"] = c.music_prompt
    if include_music_bed and music_bed:
        out["Music · Full bed"] = music_bed
    return out


def build_prompt_pack_bundle(
    info: ProductInfo,
    *,
    beat_count: int = 5,
    aspect: str = "9:16",
    preset_id: str = "cinematic_commercial",
    include_voice: bool = False,
    voice_lang: str = "en",
    include_music: bool = True,
    music_mood: str = "soft cinematic",
    ad_texts: Optional[Dict[str, str]] = None,
) -> Dict:
    """Full bundle: cards, pack dict, ad texts, meta json, TXT content."""
    ad_texts = ad_texts or generate_ad_texts(info)
    cards = build_beat_cards(
        info,
        beat_count=beat_count,
        aspect=aspect,
        preset_id=preset_id,
        include_voice=include_voice,
        voice_lang=voice_lang,
        include_music=include_music,
        music_mood=music_mood,
        ad_texts=ad_texts,
    )
    pack = build_grok_prompt_pack(
        info,
        aspect=aspect,
        preset_id=preset_id,
        include_beats=True,
        include_continuous=False,
        ad_texts=ad_texts,
        include_voice=include_voice,
        voice_lang=voice_lang,
        include_music=include_music,
        music_mood=music_mood,
        beat_count=beat_count,
    )
    meta = build_pack_meta_json(
        info,
        ad_texts,
        aspect=aspect,
        beat_count=beat_count,
        music_mood=music_mood,
        include_voice=include_voice,
        voice_lang=voice_lang,
    )
    txt = build_content_pack_text(
        info,
        pack,
        ad_texts,
        meta_json=meta,
        beat_count=beat_count,
    )
    # prepend workflow note
    note = (
        "========================================\n"
        "WORKFLOW NOTE (v5)\n"
        "========================================\n"
        "Generate ONE Grok clip per beat (copy each shot prompt separately).\n"
        "Do NOT use continuous multi-beat as primary.\n"
        "Upload clips in order on Συναρμολόγηση, then render final MP4.\n\n"
    )
    return {
        "cards": cards,
        "pack": pack,
        "ad_texts": ad_texts,
        "meta": meta,
        "txt": note + txt,
        "beat_count": int(beat_count) if int(beat_count) in (3, 5) else 3,
    }


def pack_txt_bytes(bundle: Dict) -> bytes:
    return (bundle.get("txt") or "").encode("utf-8")


def pack_json_bytes(bundle: Dict) -> bytes:
    payload = {
        "meta": bundle.get("meta"),
        "ad_texts": bundle.get("ad_texts"),
        "beats": [c.to_dict() if hasattr(c, "to_dict") else c for c in bundle.get("cards", [])],
        "prompts": bundle.get("pack"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def pack_zip_bytes(bundle: Dict, stem: str = "sneakerness-beat-pack") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{stem}.txt", pack_txt_bytes(bundle))
        zf.writestr(f"{stem}.json", pack_json_bytes(bundle))
        zf.writestr("meta.json", json.dumps(bundle.get("meta") or {}, ensure_ascii=False, indent=2))
        # per-beat prompt files
        for c in bundle.get("cards") or []:
            name = f"beats/beat_{c.index:02d}_{c.role}.txt"
            body = (
                f"# Beat {c.index} — {c.label_en} ({c.duration_s}s)\n"
                f"# Role: {c.role}\n\n"
                f"=== SHOT PROMPT ===\n{c.shot_prompt}\n\n"
                f"=== MUSIC PROMPT ===\n{c.music_prompt}\n"
            )
            zf.writestr(name, body.encode("utf-8"))
    return buf.getvalue()


def slug_product(info: ProductInfo) -> str:
    brand = "".join(c for c in (info.brand or "brand") if c.isalnum() or c in "-_")[:24]
    model = "".join(c for c in safe_model_name(info.model or "model") if c.isalnum() or c in "-_ ")[:28]
    model = model.replace(" ", "-")
    return f"{brand}-{model}".strip("-") or "sneaker-pack"


__all__ = [
    "BEAT_ROLES_3",
    "BEAT_ROLES_5",
    "BeatCard",
    "beat_roles",
    "build_beat_cards",
    "build_prompt_pack_bundle",
    "pack_dict_from_cards",
    "pack_json_bytes",
    "pack_txt_bytes",
    "pack_zip_bytes",
    "slug_product",
    "list_prompt_presets",
    "get_prompt_preset",
]
