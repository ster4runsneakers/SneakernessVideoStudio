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
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp {
    background: radial-gradient(1200px 600px at 10% -10%, #1a1a22 0%, #0b0b0f 45%, #050508 100%);
    color: #f2f2f5;
  }
  h1, h2, h3 { letter-spacing: -0.02em; }
  .hero {
    padding: 1.2rem 1.4rem;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(255,45,85,0.18), rgba(0,229,255,0.08));
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1rem;
  }
  .hero h1 { margin: 0 0 0.35rem 0; font-weight: 800; font-size: 1.85rem; }
  .hero p { margin: 0; opacity: 0.85; }
  .step-badge {
    display: inline-block;
    background: #ff2d55;
    color: white;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    margin-bottom: 0.4rem;
  }
  .grok-badge {
    display: inline-block;
    background: linear-gradient(90deg, #00e5ff, #7c5cff);
    color: #0b0b0f;
    font-weight: 800;
    font-size: 0.7rem;
    padding: 0.15rem 0.5rem;
    border-radius: 6px;
    letter-spacing: 0.04em;
  }
  div[data-testid="stSidebar"] {
    background: #0e0e14;
    border-right: 1px solid rgba(255,255,255,0.06);
  }
  .stButton > button {
    background: linear-gradient(90deg, #ff2d55, #ff6b35);
    color: white;
    border: none;
    font-weight: 700;
    border-radius: 12px;
  }
  .stButton > button:hover {
    filter: brightness(1.08);
    border: none;
    color: white;
  }
  .stDownloadButton > button {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.15);
    color: #fff;
    border-radius: 12px;
    font-weight: 600;
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
              <h1>👟 Sneakerness Grok Video Studio</h1>
              <p>
                <span class="grok-badge">GROK / xAI</span>
                &nbsp; Soft-discovery · Grok Prompt Pack · optional Gemini/xAI analyze · τοπικό slideshow
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

    with st.sidebar:
        st.markdown("### Ρυθμίσεις")
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
        provider_label = st.selectbox(
            "Vision analyze provider",
            list(provider_labels.keys()),
            index=0,
            help="Auto δοκιμάζει xAI/Grok πρώτα αν υπάρχει key, αλλιώς Gemini, αλλιώς defaults.",
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
            "1. Upload / πεδία  \n"
            "2. Grok Prompts (κύριο)  \n"
            "3. Captions + Content Pack  \n"
            "4. Τοπικό Slideshow (δευτερεύον)"
        )

    # ---- Upload ----
    st.markdown('<div class="step-badge">ΒΗΜΑ 1</div>', unsafe_allow_html=True)
    st.subheader("Φωτογραφία / προϊόν")

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
                if data.get(src):
                    st.session_state[dst] = data[src]
            if status == "xai":
                st.success("Ανάλυση μέσω xAI Grok ολοκληρώθηκε.")
            elif status == "gemini":
                st.success("Ανάλυση μέσω Google Gemini ολοκληρώθηκε.")
            elif status.startswith("fallback"):
                st.warning(
                    "Χωρίς vision API / fallback defaults — συμπλήρωσε τα πεδία χειροκίνητα."
                )
            st.rerun()

    # ---- Fields ----
    st.markdown("#### Στοιχεία προϊόντος")
    c1, c2, c3 = st.columns(3)
    with c1:
        brand = st.text_input(
            "Brand / Μάρκα",
            value=st.session_state["brand_val"],
            placeholder="π.χ. HOKA",
        )
        st.session_state["brand_val"] = brand
    with c2:
        model_name = st.text_input(
            "Model / Μοντέλο",
            value=st.session_state["model_val"],
            placeholder="π.χ. Clifton 9",
        )
        st.session_state["model_val"] = model_name
    with c3:
        colorway = st.text_input(
            "Colorway / Χρώμα",
            value=st.session_state["colorway_val"],
            placeholder="π.χ. Cream / Red",
        )
        st.session_state["colorway_val"] = colorway

    custom_watermark = st.text_input("Watermark / Domain", value="SNEAKERNESS.EU")
    key_materials = st.text_area(
        "Specs / Τεχνικά Χαρακτηριστικά",
        value=st.session_state["specs_val"],
        placeholder="π.χ. CMEVA midsole, engineered mesh…",
        height=70,
    )
    st.session_state["specs_val"] = key_materials

    col_tag, col_badge = st.columns(2)
    with col_tag:
        selected_tag = st.selectbox("Tag (Πάνω Αριστερά)", AUTHENTICITY_TAGS)
    with col_badge:
        selected_badge = st.selectbox("Badge (Πάνω Δεξιά)", CATEGORY_BADGES)

    st.markdown("#### 🎨 Δυναμικά Στοιχεία Σκηνής")
    selected_env = st.text_area(
        "Περιβάλλον Φόντου (Custom Environment)",
        value=st.session_state["env_desc_val"],
        height=60,
    )
    st.session_state["env_desc_val"] = selected_env
    selected_props = st.text_area(
        "Αξεσουάρ / EDC Props",
        value=st.session_state["props_desc_val"],
        height=60,
    )
    st.session_state["props_desc_val"] = selected_props
    selected_problem = st.text_area(
        "Σενάριο Προβλήματος (Custom Problem Scene)",
        value=st.session_state["problem_desc_val"],
        height=60,
    )
    st.session_state["problem_desc_val"] = selected_problem

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

    tab_grok, tab_local = st.tabs(["🎬 Grok Prompts", "🎞️ Τοπικό Slideshow"])

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
                st.success("Έτοιμο — Grok prompts παρακάτω.")

        pack = st.session_state.get("last_grok_pack")
        ad_texts = st.session_state.get("last_ad_texts")
        content = st.session_state.get("last_content_pack")

        if pack:
            st.markdown("#### ✨ Grok Video Prompts (copy-paste)")
            # Prefer showing primary aspect beats first (dict preserves insertion order)
            for label, body in pack.items():
                st.markdown(f"**{label}**")
                st.code(body, language="text")

            st.markdown("---")
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
            st.info("Πάτα «Δημιουργία Grok Content Pack» για prompts βελτιστοποιημένα για Grok.")

    # =====================================================================
    # TAB: Local Slideshow (secondary)
    # =====================================================================
    with tab_local:
        st.markdown('<div class="step-badge">ΔΕΥΤΕΡΕΥΟΝ</div>', unsafe_allow_html=True)
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
