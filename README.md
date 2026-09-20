# Sneakerness Video Studio v5

Greek UI · English creative prompts · **one Grok clip per beat** → stitch → captions.

`UI_VERSION.txt` → **UI v5.0**

## Workflow (one clip per beat)

1. **Προϊόν** — upload shoe photo, fill brand / model / colorway / specs, environment & props & problem scene, watermark, aspect, caption language. Optional AI analyze (Grok / Gemini).
2. **Beats & prompts** — choose **3 or 5** beats. Each beat card has role, shot prompt, music prompt, ~4–5s duration. Copy each shot prompt into Grok and generate **ONE clip per beat**. Download TXT / JSON / ZIP pack. Continuous multi-beat is **not** the primary path.
3. **Συναρμολόγηση** — upload one clip per beat in order. Optional full music bed + VO. Burn watermark. Render final MP4 (moviepy / ffmpeg).
4. **Captions & εξαγωγή** — FB/IG, TikTok, Pinterest, YouTube, VO script. Download captions + final video.

Soft-discovery CTAs only (no hard BUY / SHOP).

## Run

```bash
cd SneakernessVideoStudio-v5
pip install -r requirements.txt
streamlit run app.py
# or: streamlit run streamlit_app.py
```

Optional secrets / env: `XAI_API_KEY` or `GROK_API_KEY`, `GEMINI_API_KEY`.

## Modules

| File | Role |
|------|------|
| `app.py` | Streamlit 4-tab UI |
| `streamlit_app.py` | Thin entry alias |
| `captions.py` | Soft-discovery captions + ProductInfo |
| `analyze.py` | Optional shoe image analysis |
| `grok_prompts.py` | Per-beat Grok prompts + quality locks |
| `beats.py` | BeatCard + pack TXT/JSON/ZIP export |
| `stitch.py` | Concatenate clips → final MP4 |
| `requirements.txt` | Streamlit-practical deps |

## Copy to PC

```
F:\SNEAKERNESS.EU\SneakernessVideoStudio-v5
```

## EL / EN

- **UI labels:** Ελληνικά
- **Creative prompts / VO / most ad copy:** English
- Soft discovery philosophy preserved from v4.4
