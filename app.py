"""
Sneakerness Video Studio v5
Greek UI · English creative prompts · ONE Grok clip per beat → stitch → captions.
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

from analyze import analyze_shoe, has_gemini_key, has_xai_key
from beats import (
    build_prompt_pack_bundle,
    list_prompt_presets,
    pack_json_bytes,
    pack_txt_bytes,
    pack_zip_bytes,
    slug_product,
)
from captions import (
    AUTHENTICITY_TAGS,
    CATEGORY_BADGES,
    ProductInfo,
    generate_ad_texts,
    generate_caption,
    safe_model_name,
)
from stitch import save_upload_bytes, stitch_clips, timeline_labels

# ---------------------------------------------------------------------------
# Page / theme
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Sneakerness Video Studio v5",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded",
)

ASPECT_OPTIONS = [
    "9:16 · Stories / Reels / TikTok",
    "16:9 · YouTube",
    "1:1 · Feed square",
    "2:3 · Pinterest",
]

CAPTION_LANG_OPTIONS = {"el": "Ελληνικά (UI captions)", "en": "English"}


def _inject_css() -> None:
    st.markdown(
        """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');
  :root {
    --em-emerald: #10b981;
    --em-gold: #fbbf24;
    --em-navy: #06101c;
  }
  html, body, [class*="css"], .stApp {
    font-family: 'Outfit', system-ui, sans-serif !important;
  }
  .stApp {
    background:
      radial-gradient(1000px 500px at 6% -10%, rgba(16,185,129,0.18) 0%, transparent 55%),
      radial-gradient(900px 480px at 96% 4%, rgba(251,191,36,0.10) 0%, transparent 50%),
      linear-gradient(165deg, #0a1f2e 0%, #06101c 45%, #030b14 100%);
    color: #e8f5f0;
  }
  .block-container { padding-top: 1rem; max-width: 1180px; }
  header[data-testid="stHeader"] { background: transparent; }
  .hero {
    padding: 1.35rem 1.5rem;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(16,185,129,0.20), rgba(6,78,92,0.35)), rgba(4,22,34,0.88);
    border: 1px solid rgba(16,185,129,0.32);
    border-left: 4px solid #fbbf24;
    margin-bottom: 0.85rem;
  }
  .hero h1 { margin: 0 0 0.35rem 0; font-size: 1.65rem; color: #f0fdf8; }
  .hero p { margin: 0; color: #a7f3d0; font-size: 0.95rem; }
  .note-box {
    background: rgba(251,191,36,0.10);
    border: 1px solid rgba(251,191,36,0.35);
    border-radius: 12px;
    padding: 0.85rem 1rem;
    margin: 0.5rem 0 1rem;
    color: #fef3c7;
    font-size: 0.92rem;
  }
  .beat-card {
    background: rgba(8,28,42,0.92);
    border: 1px solid rgba(16,185,129,0.22);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.75rem;
  }
  .chip {
    display: inline-block;
    background: rgba(16,185,129,0.15);
    border: 1px solid rgba(16,185,129,0.35);
    color: #a7f3d0;
    border-radius: 999px;
    padding: 0.15rem 0.65rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.35rem;
  }
  .timeline {
    display: flex; gap: 0.4rem; flex-wrap: wrap; margin: 0.5rem 0 1rem;
  }
  .tl-item {
    flex: 1 1 80px; text-align: center;
    background: rgba(8,36,52,0.95);
    border: 1px solid rgba(16,185,129,0.28);
    border-radius: 10px; padding: 0.55rem 0.4rem;
    font-size: 0.78rem; color: #ecfdf5;
  }
  .tl-item.on { border-color: #fbbf24; box-shadow: 0 0 0 1px rgba(251,191,36,0.4); }
</style>
""",
        unsafe_allow_html=True,
    )


def _ui_version() -> str:
    p = Path(__file__).with_name("UI_VERSION.txt")
    try:
        return p.read_text(encoding="utf-8").strip()
    except Exception:
        return "UI v5.0"


def _init_state() -> None:
    defaults = {
        "brand": "",
        "model": "",
        "colorway": "",
        "specs": "",
        "env_desc": "minimalist concrete urban street with natural daylight",
        "props_desc": "an open Kinfolk magazine, a ceramic cup of cappuccino, brass keys, succulent",
        "problem_desc": "a tired worker sitting on stairs touching sore feet with work boots beside them",
        "watermark": "SNEAKERNESS.EU",
        "tag": AUTHENTICITY_TAGS[0],
        "badge": CATEGORY_BADGES[0],
        "aspect": ASPECT_OPTIONS[0],
        "caption_lang": "el",
        "beat_count": 5,
        "preset_id": "cinematic_commercial",
        "music_mood": "soft cinematic",
        "include_music": True,
        "include_voice": False,
        "voice_lang": "en",
        "bundle": None,
        "ad_texts": None,
        "final_mp4": None,
        "shoe_bytes": None,
        "shoe_name": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _product_info() -> ProductInfo:
    return ProductInfo(
        brand=st.session_state.brand,
        model=st.session_state.model,
        colorway=st.session_state.colorway,
        specs=st.session_state.specs,
        watermark=st.session_state.watermark or "SNEAKERNESS.EU",
        tag=st.session_state.tag,
        badge=st.session_state.badge,
        env_desc=st.session_state.env_desc,
        props_desc=st.session_state.props_desc,
        problem_desc=st.session_state.problem_desc,
    )


def _aspect_code() -> str:
    a = st.session_state.aspect or ASPECT_OPTIONS[0]
    return a.split("·")[0].strip()


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

def tab_product() -> None:
    st.subheader("1 · Προϊόν")
    st.caption("Ανέβασε παπούτσι · συμπλήρωσε brand/model · προαιρετική ανάλυση εικόνας.")

    c1, c2 = st.columns([1, 1.2])
    with c1:
        up = st.file_uploader("Φωτογραφία παπουτσιού", type=["jpg", "jpeg", "png", "webp"], key="shoe_up")
        if up is not None:
            st.session_state.shoe_bytes = up.getvalue()
            st.session_state.shoe_name = up.name
            try:
                st.image(Image.open(io.BytesIO(st.session_state.shoe_bytes)), use_container_width=True)
            except Exception:
                st.info("Προεπισκόπηση μη διαθέσιμη.")

        provider = st.selectbox(
            "Analyze provider",
            ["auto", "grok", "gemini"],
            index=0,
            help="Απαιτεί XAI_API_KEY / GROK_API_KEY ή GEMINI_API_KEY. Χωρίς key → defaults.",
        )
        if st.button("🔍 Analyze shoe (προαιρετικό)", use_container_width=True):
            data, status = analyze_shoe(
                st.session_state.shoe_bytes,
                filename=st.session_state.shoe_name or "shoe.jpg",
                brand_hint=st.session_state.brand,
                model_hint=st.session_state.model,
                provider=provider,  # type: ignore[arg-type]
            )
            for k in ("brand", "model", "colorway", "specs", "env_desc", "props_desc", "problem_desc"):
                if data.get(k):
                    st.session_state[k] = data[k]
            st.success(f"Analyze status: {status}")

    with c2:
        st.session_state.brand = st.text_input("Brand", st.session_state.brand)
        st.session_state.model = st.text_input("Model", st.session_state.model)
        st.session_state.colorway = st.text_input("Colorway", st.session_state.colorway)
        st.session_state.specs = st.text_area("Specs", st.session_state.specs, height=70)
        st.session_state.env_desc = st.text_area("Environment (EN)", st.session_state.env_desc, height=60)
        st.session_state.props_desc = st.text_area("Props (EN)", st.session_state.props_desc, height=60)
        st.session_state.problem_desc = st.text_area("Problem scene (EN)", st.session_state.problem_desc, height=60)

    r1, r2, r3 = st.columns(3)
    with r1:
        st.session_state.watermark = st.text_input("Watermark", st.session_state.watermark)
        st.session_state.aspect = st.selectbox("Aspect", ASPECT_OPTIONS, index=ASPECT_OPTIONS.index(st.session_state.aspect) if st.session_state.aspect in ASPECT_OPTIONS else 0)
    with r2:
        st.session_state.caption_lang = st.selectbox(
            "Caption language",
            list(CAPTION_LANG_OPTIONS.keys()),
            format_func=lambda k: CAPTION_LANG_OPTIONS[k],
            index=0 if st.session_state.caption_lang == "el" else 1,
        )
        st.session_state.tag = st.selectbox("Authenticity tag", AUTHENTICITY_TAGS, index=0)
    with r3:
        st.session_state.badge = st.selectbox("Category badge", CATEGORY_BADGES, index=0)
        keys = f"Grok key: {'✅' if has_xai_key() else '—'} · Gemini: {'✅' if has_gemini_key() else '—'}"
        st.caption(keys)

    st.markdown(
        '<div class="note-box">💡 Soft discovery: χωρίς BUY/SHOP. Creative prompts στα Αγγλικά · UI στα Ελληνικά.</div>',
        unsafe_allow_html=True,
    )


def tab_beats() -> None:
    st.subheader("2 · Beats & prompts")
    st.markdown(
        '<div class="note-box">'
        "<b>Κανόνας v5:</b> Δημιούργησε <b>ΕΝΑ Grok clip ανά beat</b> "
        "(αντιγραφή shot prompt → Grok video). "
        "Όχι continuous ως primary. Μετά ανέβασε τα clips στη Συναρμολόγηση."
        "</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.beat_count = st.radio("Αριθμός beats", [3, 5], index=1 if st.session_state.beat_count == 5 else 0, horizontal=True)
    with c2:
        presets = list_prompt_presets()
        labels = {p.id: f"{p.name_el}" for p in presets}
        ids = list(labels.keys())
        cur = st.session_state.preset_id if st.session_state.preset_id in ids else ids[0]
        st.session_state.preset_id = st.selectbox("Style preset", ids, format_func=lambda i: labels[i], index=ids.index(cur))
    with c3:
        st.session_state.music_mood = st.text_input("Music mood", st.session_state.music_mood)
        st.session_state.include_music = st.checkbox("Include music prompts", value=st.session_state.include_music)
        st.session_state.include_voice = st.checkbox("VO hints in prompts", value=st.session_state.include_voice)

    info = _product_info()
    if not (info.brand or info.model):
        st.warning("Συμπλήρωσε τουλάχιστον Brand ή Model στο tab Προϊόν.")
        return

    if st.button("✨ Δημιουργία prompt pack", type="primary", use_container_width=True):
        with st.spinner("Building per-beat pack…"):
            bundle = build_prompt_pack_bundle(
                info,
                beat_count=int(st.session_state.beat_count),
                aspect=_aspect_code(),
                preset_id=st.session_state.preset_id,
                include_voice=bool(st.session_state.include_voice),
                voice_lang=st.session_state.voice_lang,
                include_music=bool(st.session_state.include_music),
                music_mood=st.session_state.music_mood,
            )
            st.session_state.bundle = bundle
            st.session_state.ad_texts = bundle["ad_texts"]
        st.success(f"Pack έτοιμο · {bundle['beat_count']} beats · one clip per beat")

    bundle = st.session_state.bundle
    if not bundle:
        st.info("Πάτα «Δημιουργία prompt pack» για beat cards.")
        return

    cards = bundle["cards"]
    for card in cards:
        with st.container():
            st.markdown(
                f'<div class="beat-card"><span class="chip">Beat {card.index}</span>'
                f'<span class="chip">{card.label_el}</span>'
                f'<span class="chip">~{card.duration_s}s</span>'
                f'<span class="chip">{card.role}</span></div>',
                unsafe_allow_html=True,
            )
            st.text_area(
                f"Shot prompt · Beat {card.index}",
                card.shot_prompt,
                height=180,
                key=f"shot_{card.index}",
            )
            if card.music_prompt:
                st.text_area(
                    f"Music prompt · Beat {card.index}",
                    card.music_prompt,
                    height=80,
                    key=f"music_{card.index}",
                )

    stem = f"{slug_product(info)}-{bundle['beat_count']}beat"
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("⬇️ TXT pack", pack_txt_bytes(bundle), file_name=f"{stem}.txt", mime="text/plain", use_container_width=True)
    with d2:
        st.download_button("⬇️ JSON pack", pack_json_bytes(bundle), file_name=f"{stem}.json", mime="application/json", use_container_width=True)
    with d3:
        st.download_button("⬇️ ZIP pack", pack_zip_bytes(bundle, stem=stem), file_name=f"{stem}.zip", mime="application/zip", use_container_width=True)


def tab_stitch() -> None:
    st.subheader("3 · Συναρμολόγηση")
    st.caption("Ανέβασε ένα clip ανά beat με σειρά · προαιρετικό music bed / VO · Render τελικό MP4.")

    bc = int(st.session_state.beat_count)
    labels = timeline_labels(bc)

    # Timeline preview
    items = "".join(f'<div class="tl-item">{lab}</div>' for lab in labels)
    st.markdown(f'<div class="timeline">{items}</div>', unsafe_allow_html=True)

    uploaded = []
    cols = st.columns(min(bc, 5))
    for i in range(bc):
        with cols[i % len(cols)]:
            f = st.file_uploader(
                f"Clip {labels[i]}",
                type=["mp4", "mov", "webm", "mkv"],
                key=f"clip_{i}",
            )
            uploaded.append(f)

    mcol, vcol = st.columns(2)
    with mcol:
        music_up = st.file_uploader("Music bed (προαιρετικό)", type=["mp3", "wav", "m4a", "aac"], key="music_bed")
    with vcol:
        vo_up = st.file_uploader("Voiceover (προαιρετικό)", type=["mp3", "wav", "m4a", "aac"], key="vo_bed")

    burn = st.checkbox("Burn watermark στο τελικό", value=True)
    wm = st.session_state.watermark or "SNEAKERNESS.EU"

    ready = all(u is not None for u in uploaded)
    if not ready:
        st.info(f"Χρειάζονται {bc} clips (ένα ανά beat) για render.")
    if st.button("🎬 Render τελικό MP4", type="primary", disabled=not ready, use_container_width=True):
        with st.spinner("Stitching clips…"):
            try:
                with tempfile.TemporaryDirectory() as td:
                    td_path = Path(td)
                    clip_paths = []
                    for i, up in enumerate(uploaded):
                        ext = Path(up.name).suffix or ".mp4"
                        dest = td_path / f"beat_{i+1:02d}{ext}"
                        save_upload_bytes(up.getvalue(), dest)
                        clip_paths.append(dest)
                    music_path = None
                    vo_path = None
                    if music_up:
                        music_path = td_path / f"music{Path(music_up.name).suffix or '.mp3'}"
                        save_upload_bytes(music_up.getvalue(), music_path)
                    if vo_up:
                        vo_path = td_path / f"vo{Path(vo_up.name).suffix or '.mp3'}"
                        save_upload_bytes(vo_up.getvalue(), vo_path)

                    out_dir = Path(tempfile.gettempdir()) / "sneakerness_v5"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_file = out_dir / f"final_{stamp}.mp4"
                    result = stitch_clips(
                        clip_paths,
                        out_file,
                        aspect=_aspect_code(),
                        watermark=wm,
                        burn_watermark=burn,
                        music_path=music_path,
                        voice_path=vo_path,
                    )
                    data = Path(result).read_bytes()
                    st.session_state.final_mp4 = data
                st.success("Render OK")
            except Exception as e:
                st.error(f"Render error: {e}")

    if st.session_state.final_mp4:
        st.video(st.session_state.final_mp4)
        st.download_button(
            "⬇️ Download final MP4",
            st.session_state.final_mp4,
            file_name="sneakerness-final.mp4",
            mime="video/mp4",
            use_container_width=True,
        )


def tab_captions() -> None:
    st.subheader("4 · Captions & εξαγωγή")
    info = _product_info()
    ad = st.session_state.ad_texts or generate_ad_texts(info)
    st.session_state.ad_texts = ad

    lang = st.session_state.caption_lang
    el = generate_caption(info, style="soft_discovery", lang="el", ad_texts=ad)
    en = generate_caption(info, style="soft_discovery", lang="en", ad_texts=ad)

    st.markdown("#### FB / IG")
    st.text_area("Meta caption (EN)", ad.get("meta_caption", ""), height=120)
    st.text_area("Caption EL", el, height=120)

    st.markdown("#### TikTok")
    st.text_area("TikTok", ad.get("tiktok_caption", ""), height=80)

    st.markdown("#### Pinterest")
    st.text_area("Pinterest EN", ad.get("pinterest_caption", ""), height=140)
    st.text_area("Pinterest EL", ad.get("pinterest_caption_el", ""), height=140)

    st.markdown("#### YouTube")
    yt = ad.get("youtube_caption") or (
        f"{info.brand} {safe_model_name(info.model)} — soft discovery cutdown · {info.watermark}"
    )
    st.text_area("YouTube", yt, height=80)

    st.markdown("#### VO script")
    vo = (
        f"{ad.get('hook', '')}\n{ad.get('body', '')}\n{ad.get('cta', '')}"
    ).strip()
    st.text_area("Voiceover (EN soft discovery)", vo, height=100)

    # Downloads
    cap_blob = "\n\n".join(
        [
            "=== FB/IG EN ===",
            ad.get("meta_caption", ""),
            "=== FB/IG EL ===",
            el,
            "=== TIKTOK ===",
            ad.get("tiktok_caption", ""),
            "=== PINTEREST EN ===",
            ad.get("pinterest_caption", ""),
            "=== PINTEREST EL ===",
            ad.get("pinterest_caption_el", ""),
            "=== YOUTUBE ===",
            yt,
            "=== VO ===",
            vo,
        ]
    ).encode("utf-8")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Captions TXT", cap_blob, file_name="sneakerness-captions.txt", mime="text/plain", use_container_width=True)
    with c2:
        if st.session_state.final_mp4:
            st.download_button(
                "⬇️ Final video",
                st.session_state.final_mp4,
                file_name="sneakerness-final.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
        else:
            st.caption("Render στο tab Συναρμολόγηση για download video.")


def main() -> None:
    _inject_css()
    _init_state()
    ver = _ui_version()
    st.markdown(
        f"""
<div class="hero">
  <h1>👟 Sneakerness Video Studio</h1>
  <p>{ver} · One Grok clip per beat · Soft discovery · EL UI / EN prompts</p>
</div>
""",
        unsafe_allow_html=True,
    )

    t1, t2, t3, t4 = st.tabs(["1 · Προϊόν", "2 · Beats & prompts", "3 · Συναρμολόγηση", "4 · Captions & εξαγωγή"])
    with t1:
        tab_product()
    with t2:
        tab_beats()
    with t3:
        tab_stitch()
    with t4:
        tab_captions()

    st.caption("Sneakerness.eu · Soft discovery CTAs · No hard BUY/SHOP")


if __name__ == "__main__":
    main()
