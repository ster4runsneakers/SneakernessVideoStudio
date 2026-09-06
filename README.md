# 👟 Sneakerness Grok Video Studio

Streamlit studio in the **Sneakerness** philosophy: Greek UI, English soft-discovery creatives, celebrity-name safety, tags/badges/watermark — with the **primary deliverable optimized for Grok (xAI) video prompts** (not Midjourney / Nano Banana).

Optional secondary export: local slideshow MP4 from uploaded photos (existing `video_builder`).

---

## English

### What it does
1. **Upload** a sneaker photo (or multiple for local slideshow)
2. **Fill / edit** brand, model, colorway, specs, environment / props / problem scenes
3. **Generate Grok Video Prompt Pack** — copy-paste ready English prompts:
   - Beat 1 Hook / Problem
   - Beat 2 Hero product showcase
   - Beat 3 Specs / macro + soft CTA
   - Continuous single-shot reel
   - Aspect options **9:16** (Story/TikTok), **1:1** (Square), **16:9** (YouTube), **2:3** (Pinterest)
   - Negative constraints (no celebrity faces, no fake logos, no hard UI chrome…)
4. **Soft-discovery captions** (EL + EN) — no hard sell buy/shop
5. **Download Content Pack** (`.txt`)
6. Optional **Τοπικό Slideshow** tab → local MP4

### Grok paste workflow
1. Run the app → complete product fields (or optional xAI vision analyze)
2. Open tab **Grok Prompts** → **Δημιουργία Grok Content Pack**
3. Copy a prompt labeled `Grok · Beat …` or `Grok · Continuous…`
4. Paste into **Grok** (video / Aurora / image-to-video). For image-to-video, attach the same sneaker photo and keep the “preserve silhouette” guidance in the continuous prompt.
5. Use the Soft Discovery captions for IG / TikTok posts
6. Download the `.txt` pack for your archive

### Optional vision APIs (xAI Grok + Gemini)
- **No key required** — deterministic Grok prompt builder + caption templates always work offline
- Provider picker in UI: **Auto** / **Grok (xAI)** / **Gemini** (default Auto)
- Auto priority: try `XAI_API_KEY` / `GROK_API_KEY` first → else `GEMINI_API_KEY` → else empty defaults
- xAI base URL: `https://api.x.ai/v1` (OpenAI-compatible client) — optional analyze + caption enrichment
- Gemini via `google-genai` SDK — optional vision analyze (same JSON schema)

```bash
# .env
XAI_API_KEY=your_xai_api_key_here
# GROK_API_KEY=your_xai_api_key_here   # alias
GEMINI_API_KEY=your_gemini_api_key_here
```

Streamlit Cloud Secrets (also see `.streamlit/secrets.toml.example`):
```toml
XAI_API_KEY = "your_xai_api_key_here"
GEMINI_API_KEY = "your_gemini_api_key_here"
```

### Run locally
```bash
cd sneaker-video-studio
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
# or: streamlit run streamlit_app.py
```

### Streamlit Cloud
- **Main file path: `app.py`**
- `streamlit_app.py` is a thin alias that imports/runs the same app

### Project layout
```
sneaker-video-studio/
├── app.py                 # Main Streamlit entry (Sneakerness-compatible)
├── streamlit_app.py       # Thin alias → app.main()
├── grok_prompts.py        # Grok video prompt pack builder
├── captions.py            # Soft-discovery EL+EN + celebrity filter
├── analyze.py             # Optional xAI / Gemini vision + xAI copy
├── video_builder.py       # Local slideshow MP4
├── templates.py           # Slideshow templates + prompt style presets
├── requirements.txt
├── .env.example
├── .streamlit/config.toml
└── README.md
```

### Philosophy (mirrored from sneakerness-engine)
- Soft-discovery CTAs (`Discover more at …`) — never hard buy/shop
- Celebrity name safety filter (kobe / jordan / lebron / …)
- Tags, badges, watermark / domain
- Content pack download
- Clear session / **Νέο Παπούτσι** button

---

## Ελληνικά

### Τι κάνει
1. Upload φωτό sneaker → συμπλήρωση brand / model / colorway / specs / σκηνές
2. **Grok Video Prompt Pack** (κύριο αποτέλεσμα) — prompts στα Αγγλικά · aspects 9:16 / 1:1 / 16:9 YouTube / 2:3 Pinterest
3. Soft-discovery captions (EL + EN)
4. Download `.txt` content pack
5. Δευτερεύον: **Τοπικό Slideshow** MP4 από τις φωτό σου

### Εκτέλεση
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Secrets
Δες `.env.example` και `.streamlit/secrets.toml.example`. Keys: `XAI_API_KEY`/`GROK_API_KEY`, `GEMINI_API_KEY` (όλα προαιρετικά). Χωρίς κλειδί η εφαρμογή δουλεύει κανονικά με deterministic builders.

### Main file (Cloud)
`app.py`
