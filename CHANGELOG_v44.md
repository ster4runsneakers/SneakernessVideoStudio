# Changelog — Video Studio v4.4

**UI v4.4 · Electric Midnight · 5-beat Image-Studio quality**

## Fixes
- Aligned `grok_prompts.py` with `captions.py` exports (`ProductInfo`, `generate_ad_texts`, `soft_sanitize`, `safe_model_name`) so `build_grok_prompt_pack` / `dual_aspect_pack` run cleanly under `from __future__ import annotations`.

## Features
- **5-beat mode** (Hook / Product 3–4 / Macro / On-foot no-face / Flat-lay CTA) plus existing **3-beat + continuous** (15s). `beat_count` on `build_grok_prompt_pack` and Streamlit UI radio.
- **Music ↔ beat map** baked into audio direction; standalone **full music-bed** prompt + per-beat music lines in the pack.
- **Quality locks**: no extra limbs/heels, attached shadows, no morph/warp/floaty run, brand spelled letter-by-letter when known, **REQUIRED** watermark once bottom-right, strictly no Slide X of Y / carousel UI / LEARN MORE / invented badges, hard-distinct compositions.
- **Richer export**: `build_content_pack_text` sections VIDEO SHOT PROMPTS | MUSIC | VOICEOVER | FB/IG | TIKTOK | PINTEREST | YOUTUBE | RAW JSON; ZIP download (`prompts.txt` + `meta.json`).

## Files
- `grok_prompts.py`, `captions.py`, `app.py`, `UI_VERSION.txt`, `CHANGELOG_v44.md`
