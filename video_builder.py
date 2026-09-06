"""Build sneaker marketing slideshow MP4 from images + template."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from templates import VideoTemplate

PathLike = Union[str, Path]


def _ensure_imageio_ffmpeg() -> Optional[str]:
    """Prefer bundled ffmpeg from imageio-ffmpeg (works on Streamlit Cloud)."""
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            os.environ.setdefault("IMAGEIO_FFMPEG_EXE", exe)
            os.environ.setdefault("FFMPEG_BINARY", exe)
            return exe
    except Exception:
        pass
    return None


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "C:\\Windows\\Fonts\\arialbd.ttf",
            ]
        )
    candidates.extend(
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
    )
    for path in candidates:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _fit_cover(img: Image.Image, target_w: int, target_h: int, scale: float = 1.0) -> Image.Image:
    """Resize/crop to cover target, optional overscale for Ken Burns."""
    tw, th = int(target_w * scale), int(target_h * scale)
    src_w, src_h = img.size
    ratio = max(tw / src_w, th / src_h)
    new_w, new_h = max(1, int(src_w * ratio)), max(1, int(src_h * ratio))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    shadow: Tuple[int, int, int, int] = (0, 0, 0, 180),
) -> None:
    x, y = xy
    # soft shadow
    for dx, dy in ((2, 2), (1, 1), (0, 2)):
        draw.text((x + dx, y + dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    current = words[0]
    for w in words[1:]:
        trial = f"{current} {w}"
        tw, _ = _text_size(draw, trial, font)
        if tw <= max_width:
            current = trial
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return lines


def compose_frame(
    image_path: PathLike,
    template: VideoTemplate,
    title: str = "",
    subtitle: str = "",
    frame_index: int = 0,
    total_frames: int = 1,
    progress: float = 0.0,
) -> Image.Image:
    """Create one overlayed frame (RGB). progress in [0,1] for Ken Burns."""
    W, H = template.width, template.height
    canvas = Image.new("RGB", (W, H), template.bg_color)

    img = Image.open(image_path).convert("RGB")

    # Ken Burns: slow zoom + slight pan
    if template.ken_burns:
        scale = 1.08 + 0.07 * progress
        # alternate pan direction per frame index
        direction = 1 if frame_index % 2 == 0 else -1
        cover = _fit_cover(img, W, H, scale=scale)
        # pan within overscaled image
        max_dx = cover.width - W
        max_dy = cover.height - H
        ox = int(max_dx * (0.5 + direction * 0.35 * (progress - 0.5))) if max_dx > 0 else 0
        oy = int(max_dy * (0.35 * progress)) if max_dy > 0 else 0
        ox = max(0, min(ox, max_dx))
        oy = max(0, min(oy, max_dy))
        photo = cover.crop((ox, oy, ox + W, oy + H))
    else:
        photo = _fit_cover(img, W, H, scale=1.0)

    # subtle vignette / darken for text readability
    darkened = ImageEnhance.Brightness(photo).enhance(0.88)
    canvas.paste(darkened, (0, 0))

    # gradient bar for text
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    if template.overlay_layout == "bottom":
        for i in range(H // 3):
            alpha = int(200 * (i / (H // 3)))
            y = H - 1 - i
            od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    elif template.overlay_layout == "top_bottom":
        for i in range(H // 5):
            alpha = int(180 * (1 - i / (H // 5)))
            od.line([(0, i), (W, i)], fill=(0, 0, 0, alpha))
        for i in range(H // 3):
            alpha = int(210 * (i / (H // 3)))
            y = H - 1 - i
            od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    else:  # center — soft full vignette
        for i in range(min(H // 4, 200)):
            alpha = int(90 * (1 - i / (H // 4)))
            od.line([(0, i), (W, i)], fill=(0, 0, 0, alpha))
            od.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(0, 0, 0, alpha))

    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Font sizes by style / resolution
    base = max(28, W // 18)
    if template.font_style == "bold":
        title_font = _load_font(int(base * 1.35), bold=True)
        sub_font = _load_font(int(base * 0.7), bold=True)
    elif template.font_style == "story":
        title_font = _load_font(int(base * 1.15), bold=True)
        sub_font = _load_font(int(base * 0.65), bold=False)
    else:
        title_font = _load_font(int(base * 1.0), bold=True)
        sub_font = _load_font(int(base * 0.55), bold=False)

    margin = int(W * 0.06)
    max_text_w = W - 2 * margin

    title_lines = _wrap_text(draw, title.upper() if template.font_style == "bold" else title, title_font, max_text_w) if title else []
    sub_lines = _wrap_text(draw, subtitle, sub_font, max_text_w) if subtitle else []

    line_gap = int(base * 0.15)
    title_block_h = sum(_text_size(draw, ln, title_font)[1] + line_gap for ln in title_lines)
    sub_block_h = sum(_text_size(draw, ln, sub_font)[1] + line_gap for ln in sub_lines)

    # Accent bar
    accent = template.accent_color

    if template.overlay_layout == "center":
        total_h = title_block_h + sub_block_h + int(base * 0.4)
        y = (H - total_h) // 2
        # accent pill behind
        pad = int(base * 0.5)
        box = [
            margin - pad // 2,
            y - pad,
            W - margin + pad // 2,
            y + total_h + pad,
        ]
        accent_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ad = ImageDraw.Draw(accent_overlay)
        ad.rounded_rectangle(box, radius=24, fill=(*template.bg_color, 160))
        ad.rectangle(
            [margin, y - pad // 2, margin + 8, y + total_h + pad // 2],
            fill=(*accent, 255),
        )
        canvas = Image.alpha_composite(canvas.convert("RGBA"), accent_overlay).convert("RGB")
        draw = ImageDraw.Draw(canvas)
        for ln in title_lines:
            tw, th = _text_size(draw, ln, title_font)
            _draw_text_with_shadow(draw, ((W - tw) // 2, y), ln, title_font, template.text_color)
            y += th + line_gap
        y += int(base * 0.2)
        for ln in sub_lines:
            tw, th = _text_size(draw, ln, sub_font)
            _draw_text_with_shadow(draw, ((W - tw) // 2, y), ln, sub_font, template.secondary_text_color)
            y += th + line_gap

    elif template.overlay_layout == "top_bottom":
        # title near top
        y = int(H * 0.06)
        for ln in title_lines:
            tw, th = _text_size(draw, ln, title_font)
            _draw_text_with_shadow(draw, (margin, y), ln, title_font, template.text_color)
            y += th + line_gap
        # accent line
        if title_lines:
            draw.rectangle([margin, y + 4, margin + int(W * 0.2), y + 10], fill=accent)
        # subtitle near bottom
        y = H - int(H * 0.08) - sub_block_h
        for ln in sub_lines:
            tw, th = _text_size(draw, ln, sub_font)
            _draw_text_with_shadow(draw, (margin, y), ln, sub_font, template.secondary_text_color)
            y += th + line_gap

    else:  # bottom
        y = H - int(H * 0.08) - title_block_h - sub_block_h
        if title_lines:
            draw.rectangle([margin, y - 14, margin + int(W * 0.18), y - 6], fill=accent)
        for ln in title_lines:
            tw, th = _text_size(draw, ln, title_font)
            _draw_text_with_shadow(draw, (margin, y), ln, title_font, template.text_color)
            y += th + line_gap
        y += int(base * 0.1)
        for ln in sub_lines:
            tw, th = _text_size(draw, ln, sub_font)
            _draw_text_with_shadow(draw, (margin, y), ln, sub_font, template.secondary_text_color)
            y += th + line_gap

    return canvas


def _render_clip_frames(
    image_path: PathLike,
    template: VideoTemplate,
    title: str,
    subtitle: str,
    duration: float,
    fps: int,
    frame_index: int,
    out_dir: Path,
) -> List[Path]:
    n = max(1, int(round(duration * fps)))
    paths: List[Path] = []
    for i in range(n):
        progress = i / max(1, n - 1)
        frame = compose_frame(
            image_path,
            template,
            title=title,
            subtitle=subtitle,
            frame_index=frame_index,
            progress=progress,
        )
        fp = out_dir / f"f{frame_index:03d}_{i:04d}.jpg"
        frame.save(fp, quality=92, optimize=True)
        paths.append(fp)
    return paths


def build_slideshow(
    image_paths: Sequence[PathLike],
    template: VideoTemplate,
    output_path: PathLike,
    title: str = "",
    subtitle: str = "",
    duration_per_image: Optional[float] = None,
    fps: int = 24,
    burn_captions: bool = True,
) -> str:
    """
    Stitch images into an MP4 slideshow.
    Returns absolute path to the written MP4.
    """
    if not image_paths:
        raise ValueError("At least one image is required")

    _ensure_imageio_ffmpeg()

    duration = duration_per_image if duration_per_image is not None else template.default_duration
    duration = max(0.6, float(duration))
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Try moviepy v1 / v2 APIs
    try:
        return _build_with_moviepy(
            image_paths, template, out, title, subtitle, duration, fps, burn_captions
        )
    except Exception as primary_err:
        # Fallback: ffmpeg concat of rendered frames via imageio
        try:
            return _build_with_imageio(
                image_paths, template, out, title, subtitle, duration, fps, burn_captions
            )
        except Exception as secondary_err:
            raise RuntimeError(
                f"Video build failed.\nmoviepy: {primary_err}\nimageio: {secondary_err}"
            ) from secondary_err


def _build_with_moviepy(
    image_paths: Sequence[PathLike],
    template: VideoTemplate,
    out: Path,
    title: str,
    subtitle: str,
    duration: float,
    fps: int,
    burn_captions: bool,
) -> str:
    ffmpeg_exe = _ensure_imageio_ffmpeg()

    # moviepy 2.x vs 1.x imports
    try:
        from moviepy import ImageClip, concatenate_videoclips, vfx
    except ImportError:
        from moviepy.editor import ImageClip, concatenate_videoclips
        vfx = None

    clips = []
    with tempfile.TemporaryDirectory(prefix="sneaker_frames_") as tmp:
        tmp_path = Path(tmp)
        for idx, img_path in enumerate(image_paths):
            t = title if burn_captions else ""
            s = subtitle if burn_captions else ""
            # For Ken Burns we need multiple frames; otherwise one still is enough
            if template.ken_burns:
                frame_paths = _render_clip_frames(
                    img_path, template, t, s, duration, fps, idx, tmp_path
                )
                # sequence as short clips or use ImageSequence — build via imageio path below if needed
                # Use first/mid/last as approx zoom via crossfade of stills if ImageSequenceClip unavailable
                try:
                    from moviepy import ImageSequenceClip
                except ImportError:
                    try:
                        from moviepy.editor import ImageSequenceClip
                    except ImportError:
                        ImageSequenceClip = None
                if ImageSequenceClip is not None:
                    seq = ImageSequenceClip([str(p) for p in frame_paths], fps=fps)
                    clips.append(seq)
                else:
                    # mid-frame still
                    mid = frame_paths[len(frame_paths) // 2]
                    clip = ImageClip(str(mid), duration=duration)
                    clips.append(clip)
            else:
                frame = compose_frame(img_path, template, title=t, subtitle=s, frame_index=idx)
                fp = tmp_path / f"still_{idx:03d}.jpg"
                frame.save(fp, quality=93)
                clip = ImageClip(str(fp), duration=duration)
                clips.append(clip)

        # Transitions
        fade = 0.25 if template.transition == "crossfade" else 0.0
        processed = []
        for i, c in enumerate(clips):
            # ensure size / fps
            try:
                c = c.with_fps(fps) if hasattr(c, "with_fps") else c.set_fps(fps)
            except Exception:
                pass
            if fade > 0 and len(clips) > 1:
                try:
                    if hasattr(c, "with_effects") and vfx is not None:
                        # moviepy 2
                        effects = []
                        if i > 0:
                            effects.append(vfx.FadeIn(fade))
                        if i < len(clips) - 1:
                            effects.append(vfx.FadeOut(fade))
                        if effects:
                            c = c.with_effects(effects)
                    else:
                        if i > 0:
                            c = c.crossfadein(fade) if hasattr(c, "crossfadein") else c.fadein(fade)
                        if i < len(clips) - 1:
                            c = c.crossfadeout(fade) if hasattr(c, "crossfadeout") else c.fadeout(fade)
                except Exception:
                    pass
            processed.append(c)

        if fade > 0 and len(processed) > 1:
            try:
                final = concatenate_videoclips(processed, method="compose", padding=-fade)
            except TypeError:
                final = concatenate_videoclips(processed, method="compose")
        else:
            final = concatenate_videoclips(processed, method="compose")

        write_kwargs = {
            "fps": fps,
            "codec": "libx264",
            "audio": False,
            "preset": "medium",
            "threads": 2,
        }
        # moviepy 1 uses ffmpeg_params; both accept logger
        try:
            write_kwargs["logger"] = None
        except Exception:
            pass
        if ffmpeg_exe:
            # Some moviepy versions pick up IMAGEIO_FFMPEG_EXE automatically
            pass

        try:
            final.write_videofile(str(out), **write_kwargs)
        except TypeError:
            write_kwargs.pop("logger", None)
            final.write_videofile(str(out), **write_kwargs)
        finally:
            try:
                final.close()
            except Exception:
                pass
            for c in processed:
                try:
                    c.close()
                except Exception:
                    pass

    if not out.is_file() or out.stat().st_size < 100:
        raise RuntimeError("MP4 was not written correctly")
    return str(out.resolve())


def _build_with_imageio(
    image_paths: Sequence[PathLike],
    template: VideoTemplate,
    out: Path,
    title: str,
    subtitle: str,
    duration: float,
    fps: int,
    burn_captions: bool,
) -> str:
    import imageio.v2 as imageio
    import numpy as np

    _ensure_imageio_ffmpeg()

    frames = []
    for idx, img_path in enumerate(image_paths):
        t = title if burn_captions else ""
        s = subtitle if burn_captions else ""
        n = max(1, int(round(duration * fps)))
        for i in range(n):
            progress = i / max(1, n - 1)
            frame = compose_frame(
                img_path,
                template,
                title=t,
                subtitle=s,
                frame_index=idx,
                progress=progress if template.ken_burns else 0.0,
            )
            frames.append(np.asarray(frame))

    # simple cut / optional crossfade between clips handled by consecutive frames
    if template.transition == "crossfade" and len(image_paths) > 1:
        # light blend already approximated by ken burns continuity; skip heavy reprocess
        pass

    imageio.mimwrite(
        str(out),
        frames,
        fps=fps,
        codec="libx264",
        quality=8,
        macro_block_size=None,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    if not out.is_file() or out.stat().st_size < 100:
        raise RuntimeError("imageio failed to write MP4")
    return str(out.resolve())


def make_placeholder_images(dir_path: PathLike, n: int = 3) -> List[str]:
    """Create solid-color placeholder sneaker-like cards for smoke tests."""
    d = Path(dir_path)
    d.mkdir(parents=True, exist_ok=True)
    colors = [
        (30, 30, 35),
        (220, 40, 70),
        (20, 120, 200),
        (240, 200, 40),
        (40, 180, 120),
    ]
    paths = []
    for i in range(n):
        c = colors[i % len(colors)]
        img = Image.new("RGB", (800, 800), c)
        draw = ImageDraw.Draw(img)
        font = _load_font(48, bold=True)
        label = f"SNEAKER {i + 1}"
        # shoe-ish ellipse
        draw.ellipse([150, 280, 650, 520], fill=(245, 245, 248), outline=(15, 15, 18), width=6)
        draw.ellipse([200, 320, 400, 420], fill=c)
        tw, th = _text_size(draw, label, font)
        draw.text(((800 - tw) // 2, 560), label, fill=(255, 255, 255), font=font)
        p = d / f"placeholder_{i + 1}.png"
        img.save(p)
        paths.append(str(p.resolve()))
    return paths
