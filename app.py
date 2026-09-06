"""
Sneakerness × Grok Video Studio
Greek UI · English creative outputs · Grok (xAI) video prompt pack primary deliverable.
Optional local slideshow MP4 secondary export.
Compatible entry for Streamlit Cloud / sneakerness-engine style (app.py).
"""

from __future__ import annotations

import io
import os
import tempfile
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from PIL import Image

from analyze import (
    analyze_shoe,
    generate_copy_with_xai,
    has_gemini_key,
    has_xai_key,
)
from captions import (
    AUTHENTICITY_TAGS,
    CAPTION_STYLES,
    CATEGORY_BADGES,
    ProductInfo,
    build_content_pack_text,
    generate_ad_texts,
    generate_caption,
    safe_model_name,
    video_hook_text,
    video_subtitle_text,
)
from grok_prompts import build_grok_prompt_pack, list_prompt_presets
from templates import (
    ASPECT_OPTIONS_EL,
    get_template,
    list_templates,
    prompt_preset_options_el,
    template_options_el,
)
from video_builder import build_slideshow, make_placeholder_images

st.set_page_config(
    page_title="Sneakerness Grok Video Studio",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

  :root {
    --em-emerald: #10b981;
    --em-emerald-deep: #059669;
    --em-gold: #fbbf24;
    --em-gold-soft: #f59e0b;
    --em-navy: #06101c;
    --em-teal: #0a1f2e;
    --em-panel: rgba(8, 28, 42, 0.92);
    --em-border: rgba(16, 185, 129, 0.18);
  }

  html, body, [class*="css"], .stApp {
    font-family: 'Outfit', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  }

  .stApp {
    background:
      radial-gradient(1000px 500px at 6% -10%, rgba(16,185,129,0.18) 0%, transparent 55%),
      radial-gradient(900px 480px at 96% 4%, rgba(251,191,36,0.10) 0%, transparent 50%),
      radial-gradient(700px 500px at 50% 105%, rgba(6,78,92,0.35) 0%, transparent 45%),
      linear-gradient(165deg, #0a1f2e 0%, #06101c 45%, #030b14 100%);
    color: #e8f5f0;
  }

  .block-container {
    padding-top: 1rem;
    padding-bottom: 2.6rem;
    max-width: 1180px;
  }
  header[data-testid="stHeader"] { background: transparent; }
  footer { visibility: hidden; }
  h1, h2, h3, h4 { letter-spacing: -0.02em; color: #f0fdf8; }

  /* Status strip */
  .status-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin: 0 0 1rem 0;
  }
  .status-chip {
    flex: 1 1 140px;
    min-width: 120px;
    background: linear-gradient(145deg, rgba(8,36,52,0.95) 0%, rgba(4,20,32,0.98) 100%);
    border: 1px solid rgba(16,185,129,0.28);
    border-left: 3px solid var(--em-gold);
    border-radius: 12px;
    padding: 0.7rem 0.9rem;
    box-shadow: 0 8px 22px rgba(0,0,0,0.32);
  }
  .status-chip .chip-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #fbbf24;
    margin-bottom: 0.2rem;
  }
  .status-chip .chip-value {
    font-size: 0.95rem;
    font-weight: 700;
    color: #ecfdf5;
  }

  /* Hero — Electric Midnight */
  .hero {
    padding: 1.4rem 1.55rem 1.3rem;
    border-radius: 18px;
    background:
      linear-gradient(135deg, rgba(16,185,129,0.20) 0%, rgba(6,78,92,0.35) 45%, rgba(251,191,36,0.08) 100%),
      rgba(4, 22, 34, 0.88);
    border: 1px solid rgba(16,185,129,0.32);
    border-left: 4px solid #fbbf24;
    box-shadow: 0 16px 44px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-bottom: 0.75rem;
    position: relative;
    overflow: hidden;
  }
  .hero::after {
    content: "";
    position: absolute;
    right: -50px; top: -50px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(251,191,36,0.16), transparent 70%);
    pointer-events: none;
  }
  .hero h1 {
    margin: 0.35rem 0 0.45rem 0;
    font-weight: 800;
    font-size: clamp(1.45rem, 3.6vw, 1.95rem);
    line-height: 1.15;
    color: #f0fdf8;
  }
  .hero p { margin: 0; opacity: 0.9; font-size: 0.95rem; line-height: 1.45; color: #c8e6d8; }
  .hero-kicker {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #34d399;
    margin-bottom: 0.25rem;
  }
  .ui-version-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    background: linear-gradient(90deg, #10b981, #059669);
    color: #041018;
    font-weight: 700;
    font-size: 0.72rem;
    padding: 0.28rem 0.7rem;
    border-radius: 8px;
    letter-spacing: 0.04em;
    margin-bottom: 0.45rem;
    border: 1px solid rgba(251,191,36,0.55);
    box-shadow: 0 0 18px rgba(16,185,129,0.35), 0 0 8px rgba(251,191,36,0.2);
  }

  .grok-badge {
    display: inline-block;
    background: linear-gradient(90deg, #fbbf24, #10b981);
    color: #041018;
    font-weight: 800;
    font-size: 0.68rem;
    padding: 0.18rem 0.55rem;
    border-radius: 6px;
    letter-spacing: 0.05em;
    vertical-align: middle;
  }

  .step-badge {
    display: inline-block;
    background: linear-gradient(90deg, #10b981, #059669);
    color: #041018;
    font-weight: 700;
    font-size: 0.72rem;
    padding: 0.22rem 0.6rem;
    border-radius: 999px;
    margin-bottom: 0.45rem;
    letter-spacing: 0.04em;
    box-shadow: 0 4px 14px rgba(16,185,129,0.32);
  }
  .step-badge.secondary {
    background: linear-gradient(90deg, #fbbf24, #f59e0b);
    color: #1a1200;
    box-shadow: 0 4px 14px rgba(251,191,36,0.28);
  }
  .step-badge.muted {
    background: rgba(16,185,129,0.14);
    color: #a7f3d0;
    border: 1px solid rgba(16,185,129,0.28);
    box-shadow: none;
  }

  /* Section cards — left gold border */
  .ui-card {
    background: linear-gradient(160deg, rgba(10,40,56,0.95) 0%, rgba(4,18,28,0.98) 100%);
    border: 1px solid rgba(16,185,129,0.16);
    border-left: 4px solid #fbbf24;
    border-radius: 14px;
    padding: 1rem 1.15rem 1.05rem;
    margin: 0.55rem 0 1rem 0;
    box-shadow: 0 10px 28px rgba(0,0,0,0.32);
  }
  .ui-card-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #fbbf24;
    margin: 0 0 0.55rem 0;
  }

  .flow-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(16,185,129,0.10);
    border: 1px solid rgba(16,185,129,0.22);
    border-radius: 999px;
    padding: 0.28rem 0.7rem;
    font-size: 0.78rem;
    color: #a7f3d0;
    margin: 0.15rem 0.25rem 0.15rem 0;
  }

  /* Sidebar — gold uppercase title */
  div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #051820 0%, #030d14 100%);
    border-right: 1px solid rgba(16,185,129,0.14);
  }
  div[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
  .sidebar-title {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #fbbf24;
    margin: 0 0 0.65rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid rgba(251,191,36,0.35);
  }

  /* Buttons — emerald gradient */
  .stButton > button {
    background: linear-gradient(90deg, #10b981, #059669) !important;
    color: #041018 !important;
    border: none !important;
    font-weight: 700;
    border-radius: 12px;
    min-height: 2.6rem;
    box-shadow: 0 6px 18px rgba(16,185,129,0.28);
  }
  .stButton > button:hover {
    filter: brightness(1.1);
    border: none !important;
    color: #041018 !important;
    box-shadow: 0 8px 22px rgba(16,185,129,0.4);
  }
  .stButton > button:disabled {
    opacity: 0.45;
    box-shadow: none;
  }
  .stDownloadButton > button {
    background: #0a2434 !important;
    border: 1px solid rgba(251,191,36,0.35) !important;
    color: #fbbf24 !important;
    border-radius: 12px;
    font-weight: 600;
    min-height: 2.55rem;
  }
  .stDownloadButton > button:hover {
    border-color: rgba(16,185,129,0.55) !important;
    color: #34d399 !important;
  }

  /* Inputs */
  .stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div {
    border-radius: 10px !important;
  }

  /* Tabs — emerald selected */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    background: rgba(4, 22, 34, 0.85);
    border-radius: 14px;
    padding: 0.35rem;
    border: 1px solid rgba(16,185,129,0.18);
    margin-bottom: 0.35rem;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 0.55rem 0.95rem;
    color: #7dd3b0;
    font-weight: 600;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, rgba(16,185,129,0.45), rgba(5,150,105,0.28)) !important;
    color: #ecfdf5 !important;
    box-shadow: inset 0 -2px 0 #10b981;
  }

  /* Code / prompts */
  .stCodeBlock {
    border-radius: 12px !important;
    border: 1px solid rgba(16,185,129,0.15);
  }

  /* Mobile */
  @media (max-width: 768px) {
    .block-container {
      padding-left: 0.85rem;
      padding-right: 0.85rem;
      padding-top: 0.75rem;
    }
    .hero { padding: 1.1rem 1rem; border-radius: 16px; }
    .ui-card { padding: 0.85rem 0.85rem; border-radius: 14px; }
    .stTabs [data-baseweb="tab"] { padding: 0.5rem 0.65rem; font-size: 0.85rem; }
    .status-chip { flex: 1 1 100%; }
  }
</style>
""",
    unsafe_allow_html=True,
)



def _init_session() -> None:
    defaults = {
        "brand_val": "",
        "model_val": "",
        "colorway_val": "",
        "specs_val": "",
        "env_desc_val": "minimalist concrete urban street with natural daylight",
        "props_desc_val": "an open Kinfolk magazine, a ceramic cup of cappuccino, brass keys, succulent",
        "problem_desc_val": (
            "a tired worker sitting on stairs touching sore feet with work boots beside them"
        ),
        "uploader_key": 0,
        "last_ad_texts": None,
        "last_grok_pack": None,
        "last_content_pack": None,
        "last_video": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def clear_all_fields() -> None:
    st.session_state["brand_val"] = ""
    st.session_state["model_val"] = ""
    st.session_state["colorway_val"] = ""
    st.session_state["specs_val"] = ""
    st.session_state["env_desc_val"] = "minimalist concrete urban street with natural daylight"
    st.session_state["props_desc_val"] = (
        "an open Kinfolk magazine, a ceramic cup of cappuccino, brass keys, succulent"
    )
    st.session_state["problem_desc_val"] = (
        "a tired worker sitting on stairs touching sore feet with work boots beside them"
    )
    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
    st.session_state["last_ad_texts"] = None
    st.session_state["last_grok_pack"] = None
    st.session_state["last_content_pack"] = None
    st.session_state["last_video"] = None


def _save_uploads(files, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for i, f in enumerate(files):
        suffix = Path(f.name).suffix.lower() or ".jpg"
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"
        p = dest / f"upload_{i:03d}{suffix}"
        data = f.getvalue()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.save(p, format="JPEG", quality=95)
        paths.append(str(p.resolve()))
    return paths


def _product_from_state(
    brand: str,
    model_name: str,
    colorway: str,
    specs: str,
    watermark: str,
    tag: str,
    badge: str,
    env_desc: str,
    props_desc: str,
    problem_desc: str,
    hashtags: str,
    extra: str,
) -> ProductInfo:
    return ProductInfo(
        brand=brand,
        model=model_name,
        colorway=colorway,
        specs=specs,
        watermark=watermark,
        tag=tag,
        badge=badge,
        env_desc=env_desc,
        props_desc=props_desc,
        problem_desc=problem_desc,
        hashtags=hashtags,
        extra=extra,
    )


def main() -> None:
    _init_session()

    col_header, col_reset = st.columns([4, 1])
    with col_header:
        st.markdown(
            """
            <div class="hero">
              <div class="ui-version-badge">UI v4 · Electric Midnight</div>
              <div class="hero-kicker">Sneakerness · Marketing Studio</div>
              <h1>👟 Sneakerness Grok Video Studio</h1>
              <p>
                <span class="grok-badge">GROK / xAI</span>
                &nbsp; Soft-discovery creatives · cinematic prompt pack · Gemini/xAI analyze · τοπικό slideshow
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_reset:
        st.write("")
        st.write("")
        if st.button("🧹 Νέο Παπούτσι / Clear", width="stretch"):
            clear_all_fields()
            st.rerun()

    st.markdown(
        """
        <div class="status-strip">
          <div class="status-chip">
            <div class="chip-label">Analyze</div>
            <div class="chip-value">Gemini · Grok Vision</div>
          </div>
          <div class="status-chip">
            <div class="chip-label">Grok Pack</div>
            <div class="chip-value">Cinematic Prompts</div>
          </div>
          <div class="status-chip">
            <div class="chip-label">Slideshow</div>
            <div class="chip-value">Local MP4 Export</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown('<div class="sidebar-title">Ρυθμίσεις</div>', unsafe_allow_html=True)
        st.caption("API keys · captions · aspects")
        api_ok = has_xai_key()
        gemini_ok = has_gemini_key()
        if api_ok:
            st.success("xAI / Grok key βρέθηκε (XAI_API_KEY / GROK_API_KEY)")
        else:
            st.caption("Χωρίς XAI/GROK key")
        if gemini_ok:
            st.success("Gemini key βρέθηκε (GEMINI_API_KEY)")
        else:
            st.caption("Χωρίς GEMINI_API_KEY")
        if not api_ok and not gemini_ok:
            st.info(
                "Χωρίς API key — πλήρης λειτουργία με manual fields + "
                "deterministic Grok prompts & captions."
            )
        st.caption("Optional keys σε `.env` ή Streamlit Secrets.")
        st.markdown("---")
        provider_labels = {
            "Auto (Grok → Gemini → defaults)": "auto",
            "Grok (xAI)": "grok",
            "Gemini": "gemini",
        }
        _prov_default = 0
        if (not api_ok) and gemini_ok:
            _prov_default = list(provider_labels.keys()).index("Gemini")
        provider_label = st.selectbox(
            "Vision analyze provider",
            list(provider_labels.keys()),
            index=_prov_default,
            help="Αν έχεις μόνο Gemini key, διάλεξε Gemini (ή άσε Auto).",
        )
        analyze_provider = provider_labels[provider_label]
        st.markdown("---")
        include_en_caption = st.checkbox("English captions (soft discovery)", value=True)
        include_el_caption = st.checkbox("Ελληνικά captions", value=True)
        dual_aspect = st.checkbox(
            "Επιπλέον aspects στο pack (9:16 + 1:1 + 16:9 + 2:3)",
            value=False,
            help="Αν ενεργό, προσθέτει prompts και για τα υπόλοιπα δημοφιλή ratios.",
        )
        st.markdown("---")
        st.markdown("**Ροή**")
        st.markdown(
            '<span class="flow-chip">1 Upload</span>'
            '<span class="flow-chip">2 Grok Prompts</span>'
            '<span class="flow-chip">3 Captions/Pack</span>'
            '<span class="flow-chip">4 Slideshow</span>',
            unsafe_allow_html=True,
        )

    # ---- Upload ----
    st.markdown(
        '<div class="ui-card"><div class="ui-card-title">Upload &amp; Analyze</div>'
        '<div class="step-badge">ΒΗΜΑ 1</div></div>',
        unsafe_allow_html=True,
    )
    st.subheader("Φωτογραφία / προϊόν")
    st.caption("Upload · analyze · συμπλήρωση πεδίων")

    col_up, col_preview = st.columns([2, 1])
    with col_up:
        uploaded_file = st.file_uploader(
            "📷 Ανέβασε φωτογραφία παπουτσιού (ή πολλές για slideshow)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state['uploader_key']}",
        )
    with col_preview:
        if uploaded_file:
            st.image(uploaded_file[0], caption="Προεπισκόπηση", width="stretch")

    analyze_col1, analyze_col2 = st.columns([2, 1])
    with analyze_col1:
        do_analyze = st.button(
            "🔍 Ανίχνευση / Scene (Auto: Grok → Gemini → defaults)",
            width="stretch",
        )
    with analyze_col2:
        use_demo = st.checkbox("Demo placeholders", value=False)

    if do_analyze:
        img_bytes = None
        fname = "shoe.jpg"
        if uploaded_file:
            img_bytes = uploaded_file[0].getvalue()
            fname = uploaded_file[0].name
        with st.spinner("Ανάλυση…"):
            data, status = analyze_shoe(
                image_bytes=img_bytes,
                filename=fname,
                brand_hint=st.session_state.get("brand_val", ""),
                model_hint=st.session_state.get("model_val", ""),
                provider=analyze_provider,
            )
            for src, dst in [
                ("brand", "brand_val"),
                ("model", "model_val"),
                ("colorway", "colorway_val"),
                ("specs", "specs_val"),
                ("env_desc", "env_desc_val"),
                ("props_desc", "props_desc_val"),
                ("problem_desc", "problem_desc_val"),
            ]:
                val = (data.get(src) or "").strip()
                if val:
                    st.session_state[dst] = val
            filled = bool(data.get("brand") or data.get("model") or data.get("colorway"))
            st.session_state["last_analyze_status"] = status
            st.session_state["last_analyze_filled"] = filled
            if status in ("xai", "gemini") and filled:
                st.success(
                    f"Ανάλυση μέσω {'xAI Grok' if status == 'xai' else 'Google Gemini'} ολοκληρώθηκε."
                )
            elif status.startswith("fallback_error:"):
                st.error(
                    "Η ανίχνευση απέτυχε: "
                    + status.replace("fallback_error:", "", 1)[:500]
                )
                st.info(
                    "Sidebar: provider Gemini. Secrets: GEMINI_API_KEY = your-key "
                    "(χωρίς [section]), μετά Save + Reboot."
                )
            else:
                st.warning(
                    f"Δεν συμπληρώθηκαν μάρκα/μοντέλο (status: `{status}`). "
                    "Διάλεξε Gemini στο sidebar ή συμπλήρωσε χειροκίνητα."
                )
            st.rerun()

    # ---- Fields ----
    st.markdown(
        '<div class="ui-card"><div class="ui-card-title">Product Details</div>'
        '<div class="step-badge muted">ΒΗΜΑ 2</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Στοιχεία προϊόντος")
    c1, c2, c3 = st.columns(3)
    with c1:
        brand = st.text_input(
            "Brand / Μάρκα",
            key="brand_val",
            placeholder="π.χ. HOKA",
        )
    with c2:
        model_name = st.text_input(
            "Model / Μοντέλο",
            key="model_val",
            placeholder="π.χ. Clifton 9",
        )
    with c3:
        colorway = st.text_input(
            "Colorway / Χρώμα",
            key="colorway_val",
            placeholder="π.χ. Cream / Red",
        )

    custom_watermark = st.text_input("Watermark / Domain", value="SNEAKERNESS.EU")
    key_materials = st.text_area(
        "Specs / Τεχνικά Χαρακτηριστικά",
        key="specs_val",
        placeholder="π.χ. CMEVA midsole, engineered mesh…",
        height=70,
    )

    col_tag, col_badge = st.columns(2)
    with col_tag:
        selected_tag = st.selectbox("Tag (Πάνω Αριστερά)", AUTHENTICITY_TAGS)
    with col_badge:
        selected_badge = st.selectbox("Badge (Πάνω Δεξιά)", CATEGORY_BADGES)

    st.markdown("#### 🎨 Δυναμικά Στοιχεία Σκηνής")
    selected_env = st.text_area(
        "Περιβάλλον Φόντου (Custom Environment)",
        key="env_desc_val",
        height=60,
    )
    selected_props = st.text_area(
        "Αξεσουάρ / EDC Props",
        key="props_desc_val",
        height=60,
    )
    selected_problem = st.text_area(
        "Σενάριο Προβλήματος (Custom Problem Scene)",
        key="problem_desc_val",
        height=60,
    )

    hashtags = st.text_input(
        "Hashtags (προαιρετικό)",
        value="#Sneakerness #DailyComfort #FootwearTech",
    )
    extra = st.text_area("Επιπλέον σημείωση (προαιρετικό)", value="", height=50)

    preset_opts = prompt_preset_options_el()
    p1, p2 = st.columns(2)
    with p1:
        preset_label = st.selectbox("Grok prompt style preset", list(preset_opts.keys()))
        preset_id = preset_opts[preset_label]
    with p2:
        aspect_labels = list(ASPECT_OPTIONS_EL.keys())
        aspect_choice = st.selectbox(
            "Κύριο aspect για Grok / slideshow",
            aspect_labels,
            index=0,
            help="9:16 Story · 1:1 Square · 16:9 YouTube · 2:3 Pinterest",
        )
    aspect = ASPECT_OPTIONS_EL[aspect_choice]

    info = _product_from_state(
        brand,
        model_name,
        colorway,
        key_materials,
        custom_watermark,
        selected_tag,
        selected_badge,
        selected_env,
        selected_props,
        selected_problem,
        hashtags,
        extra,
    )

    st.markdown("---")

    tab_grok, tab_caps, tab_local = st.tabs(
        ["🎬 Grok Prompts", "📲 Captions / Pack", "🎞️ Τοπικό Slideshow"]
    )

    # =====================================================================
    # TAB: Grok Prompts (primary)
    # =====================================================================
    with tab_grok:
        st.markdown('<div class="step-badge">ΚΥΡΙΟ</div>', unsafe_allow_html=True)
        st.subheader("Grok Video Prompt Pack")
        st.caption(
            "Copy-paste prompts βελτιστοποιημένα για Grok video / Aurora / image-to-video. "
            "Αγγλικά · cinematic sneaker commercial · soft discovery · celebrity safety."
        )

        use_xai_copy = st.checkbox(
            "Χρήση xAI για captions (αν υπάρχει key)",
            value=False,
            disabled=not api_ok,
        )

        if st.button("🚀 Δημιουργία Grok Content Pack", type="primary", width="stretch"):
            if not brand or not model_name:
                st.error("⚠️ Συμπλήρωσε Brand και Model.")
            else:
                with st.spinner("Δημιουργία Grok prompts + soft-discovery captions…"):
                    if use_xai_copy and api_ok:
                        ad_texts, copy_err = generate_copy_with_xai(
                            brand,
                            model_name,
                            colorway,
                            key_materials,
                            custom_watermark,
                        )
                        if copy_err and copy_err != "no_api_key":
                            st.warning(f"Copy API fallback: {copy_err}")
                    else:
                        ad_texts = generate_ad_texts(info)

                    pack = build_grok_prompt_pack(
                        info,
                        aspect=aspect,
                        preset_id=preset_id,
                        include_beats=True,
                        include_continuous=True,
                        ad_texts=ad_texts,
                    )
                    if dual_aspect:
                        for other in ("9:16", "1:1", "16:9", "2:3"):
                            if other == aspect:
                                continue
                            pack.update(
                                build_grok_prompt_pack(
                                    info,
                                    aspect=other,
                                    preset_id=preset_id,
                                    include_beats=True,
                                    include_continuous=True,
                                    ad_texts=ad_texts,
                                )
                            )

                    content = build_content_pack_text(info, pack, ad_texts)
                    st.session_state["last_ad_texts"] = ad_texts
                    st.session_state["last_grok_pack"] = pack
                    st.session_state["last_content_pack"] = content
                st.success("Έτοιμο — Grok prompts παρακάτω · captions στο tab Captions/Pack.")

        pack = st.session_state.get("last_grok_pack")
        ad_texts = st.session_state.get("last_ad_texts")
        content = st.session_state.get("last_content_pack")

        if pack:
            st.markdown(
                '<div class="ui-card"><div class="ui-card-title">Copy-paste into Grok</div>'
                '<div style="opacity:0.85;font-size:0.9rem;margin:0">'
                'Beats + continuous prompts ready for Grok video / image-to-video.'
                '</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### ✨ Grok Video Prompts")
            for label, body in pack.items():
                st.markdown(f"**{label}**")
                st.code(body, language="text")
            st.info("Captions & downloadable Content Pack → tab **Captions / Pack**.")
        else:
            st.info("Πάτα «Δημιουργία Grok Content Pack» για prompts βελτιστοποιημένα για Grok.")

    # =====================================================================
    # TAB: Captions / Pack
    # =====================================================================
    with tab_caps:
        st.markdown('<div class="step-badge secondary">CAPTIONS</div>', unsafe_allow_html=True)
        st.subheader("Soft Discovery Captions & Content Pack")
        st.caption("EN soft-discovery captions · Ελληνικά · downloadable .txt pack.")

        pack = st.session_state.get("last_grok_pack")
        ad_texts = st.session_state.get("last_ad_texts")
        content = st.session_state.get("last_content_pack")

        if ad_texts or content:
            st.markdown("### 📲 Soft Discovery Captions")
            t1, t2, t3 = st.tabs(
                ["📘 FB / IG (EN)", "🎵 TikTok (EN)", "🇬🇷 Ελληνικά"]
            )
            with t1:
                if ad_texts:
                    meta = (
                        f"{ad_texts.get('meta_caption', '')}\n\n"
                        f"{ad_texts.get('hashtags_meta', '')}"
                    )
                    st.text_area("FB / IG", value=meta if include_en_caption else "", height=160)
            with t2:
                if ad_texts and include_en_caption:
                    st.text_area(
                        "TikTok",
                        value=ad_texts.get("tiktok_caption", ""),
                        height=120,
                    )
            with t3:
                if ad_texts and include_el_caption:
                    st.text_area(
                        "EL",
                        value=ad_texts.get("caption_el", ""),
                        height=160,
                    )

            if content:
                safe_name = f"{brand}_{safe_model_name(model_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in safe_name)
                st.download_button(
                    "📥 Download Content Pack (.txt)",
                    data=content,
                    file_name=safe_name,
                    mime="text/plain",
                    width="stretch",
                )
                out_dir = Path("output")
                out_dir.mkdir(exist_ok=True)
                try:
                    (out_dir / safe_name).write_text(content, encoding="utf-8")
                    st.caption(f"Αποθηκεύτηκε επίσης στο `output/{safe_name}`")
                except Exception:
                    pass
        else:
            st.info(
                "Δημιούργησε πρώτα Content Pack από το tab Grok Prompts για captions & download."
            )

        # =====================================================================
    # TAB: Local Slideshow (secondary)
    # =====================================================================
    with tab_local:
        st.markdown('<div class="step-badge muted">ΔΕΥΤΕΡΕΥΟΝ</div>', unsafe_allow_html=True)
        st.subheader("Τοπικό Slideshow MP4")
        st.caption("Υπάρχον video_builder — slideshow από uploaded φωτό. Δεν αντικαθιστά τα Grok prompts.")

        work = Path(tempfile.gettempdir()) / "sneaker_video_studio"
        work.mkdir(parents=True, exist_ok=True)

        image_paths: list[str] = []
        if use_demo:
            image_paths = make_placeholder_images(work / "demo", n=3)
            st.info("Demo placeholders ενεργά.")
        elif uploaded_file:
            image_paths = _save_uploads(uploaded_file, work / "uploads")
            st.success(f"Φορτώθηκαν {len(image_paths)} εικόνες.")
        else:
            st.warning("Ανέβασε φωτό ή ενεργοποίησε demo placeholders.")

        if image_paths:
            cols = st.columns(min(4, len(image_paths)))
            for i, p in enumerate(image_paths[:8]):
                with cols[i % len(cols)]:
                    st.image(p, width="stretch", caption=f"#{i+1}")

        opts = template_options_el()
        label = st.selectbox("Οπτικό template (slideshow)", list(opts.keys()), index=0)
        tid = opts[label]
        tmpl = get_template(tid)
        st.caption(
            f"{tmpl.description_el} · {tmpl.aspect} · transition={tmpl.transition} · "
            f"ken_burns={tmpl.ken_burns}"
        )

        lang_video = st.selectbox(
            "Γλώσσα burn-in",
            ["el", "en"],
            format_func=lambda x: "Ελληνικά" if x == "el" else "English",
        )
        burn_hook = st.checkbox("Burn-in τίτλος στο βίντεο", value=True)
        duration = st.slider("Διάρκεια ανά φωτό (δευτ.)", 0.8, 4.0, 2.0, 0.1)

        hook = video_hook_text(info, lang=lang_video)
        sub = video_subtitle_text(info, lang=lang_video)
        st.caption(f"On-video hook: **{hook}** · subtitle: **{sub}**")

        can_run = len(image_paths) > 0
        if st.button("🎬 Δημιουργία τοπικού MP4", disabled=not can_run, width="stretch"):
            with st.spinner("Rendering slideshow…"):
                out_path = work / "output" / f"sneaker_{tid}.mp4"
                try:
                    dur = duration
                    if abs(duration - 2.0) < 0.05:
                        dur = tmpl.default_duration
                    result = build_slideshow(
                        image_paths=image_paths,
                        template=tmpl,
                        output_path=out_path,
                        title=hook if burn_hook else "",
                        subtitle=sub if burn_hook else "",
                        duration_per_image=dur,
                        fps=24,
                        burn_captions=burn_hook,
                    )
                    st.session_state["last_video"] = result
                    st.success("Έτοιμο!")
                except Exception as e:
                    st.error(f"Αποτυχία render: {e}")
                    st.exception(e)

        if st.session_state.get("last_video") and Path(st.session_state["last_video"]).is_file():
            vp = st.session_state["last_video"]
            st.video(vp)
            with open(vp, "rb") as f:
                st.download_button(
                    "⬇️ Download MP4",
                    data=f,
                    file_name=Path(vp).name,
                    mime="video/mp4",
                    width="stretch",
                )

        with st.expander("Όλα τα slideshow templates"):
            for t in list_templates():
                st.markdown(
                    f"- **{t.name_el}** (`{t.id}`) — {t.aspect}, prompt_preset=`{t.prompt_preset_id}`"
                )

        with st.expander("Grok prompt style presets"):
            for p in list_prompt_presets():
                st.markdown(f"- **{p.name_el}** — {p.mood}")


if __name__ == "__main__":
    main()
