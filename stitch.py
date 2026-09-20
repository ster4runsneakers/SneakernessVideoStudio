"""Assemble per-beat Grok clips into a final MP4 (Video Studio v5).

Supports optional music bed, optional VO audio, and burn-in watermark via Pillow.
Uses moviepy when available; falls back to imageio-ffmpeg concat where needed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

PathLike = Union[str, Path]


ASPECT_SIZES = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "2:3": (1080, 1620),
}


def _ensure_imageio_ffmpeg() -> Optional[str]:
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            os.environ.setdefault("IMAGEIO_FFMPEG_EXE", exe)
            os.environ.setdefault("FFMPEG_BINARY", exe)
            return exe
    except Exception:
        pass
    # system ffmpeg
    which = shutil.which("ffmpeg")
    return which


def _load_font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates.extend(
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "C:\\Windows\\Fonts\\arialbd.ttf",
            ]
        )
    candidates.extend(
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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


def resolve_aspect_size(aspect: str) -> Tuple[int, int]:
    a = (aspect or "9:16").strip()
    for key, size in ASPECT_SIZES.items():
        if a.startswith(key):
            return size
    return ASPECT_SIZES["9:16"]


def timeline_labels(beat_count: int = 5) -> List[str]:
    if int(beat_count) == 5:
        return [
            "1 · Hook",
            "2 · Product 3/4",
            "3 · Macro",
            "4 · On-foot",
            "5 · Flat-lay CTA",
        ]
    return ["1 · Hook", "2 · Hero", "3 · Macro+CTA"]


def burn_watermark_on_frame(
    frame_rgb,
    watermark: str = "SNEAKERNESS.EU",
    *,
    margin_pct: float = 0.03,
    height_pct: float = 0.08,
) -> "object":
    """Burn a single bottom-right watermark onto an RGB numpy frame / PIL image."""
    import numpy as np

    if isinstance(frame_rgb, Image.Image):
        img = frame_rgb.convert("RGB")
    else:
        img = Image.fromarray(np.asarray(frame_rgb).astype("uint8")).convert("RGB")

    w, h = img.size
    text = (watermark or "SNEAKERNESS.EU").strip() or "SNEAKERNESS.EU"
    font_size = max(18, int(h * height_pct * 0.55))
    font = _load_font(font_size, bold=True)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin_x = int(w * margin_pct)
    margin_y = int(h * margin_pct)
    x = w - tw - margin_x
    y = h - th - margin_y
    # soft shadow + text
    for dx, dy in ((2, 2), (1, 1)):
        draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    return np.asarray(img)


def _moviepy_import():
    try:
        from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip  # type: ignore

        return VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, "v2"
    except Exception:
        from moviepy.editor import (  # type: ignore
            VideoFileClip,
            AudioFileClip,
            concatenate_videoclips,
            CompositeAudioClip,
        )

        return VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, "v1"


def stitch_clips(
    clip_paths: Sequence[PathLike],
    output_path: PathLike,
    *,
    aspect: str = "9:16",
    watermark: str = "SNEAKERNESS.EU",
    burn_watermark: bool = True,
    music_path: Optional[PathLike] = None,
    voice_path: Optional[PathLike] = None,
    music_volume: float = 0.55,
    voice_volume: float = 1.0,
    fade_s: float = 0.15,
    fps: int = 24,
) -> str:
    """
    Concatenate beat clips in order → final MP4.
    Optional: burn watermark once (bottom-right), mix music bed + VO.
    """
    paths = [Path(p) for p in clip_paths if p and Path(p).is_file()]
    if not paths:
        raise ValueError("No valid clip files to stitch")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    target_w, target_h = resolve_aspect_size(aspect)
    ffmpeg_exe = _ensure_imageio_ffmpeg()

    VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, _ver = _moviepy_import()

    clips = []
    try:
        for p in paths:
            clip = VideoFileClip(str(p))
            # resize / letterbox to target
            try:
                # moviepy 2: resized; moviepy 1: resize
                if hasattr(clip, "resized"):
                    clip = clip.resized(height=target_h)
                    if clip.w > target_w:
                        clip = clip.resized(width=target_w)
                else:
                    clip = clip.resize(height=target_h)
                    if clip.w > target_w:
                        clip = clip.resize(width=target_w)
            except Exception:
                pass

            if burn_watermark and watermark:
                wm = watermark

                def _fl(get_frame, t, _wm=wm):
                    frame = get_frame(t)
                    return burn_watermark_on_frame(frame, _wm)

                try:
                    if hasattr(clip, "transform"):
                        clip = clip.transform(lambda gf, t: _fl(gf, t))
                    else:
                        clip = clip.fl(_fl)
                except Exception:
                    pass

            if fade_s > 0:
                try:
                    if hasattr(clip, "with_effects"):
                        from moviepy import vfx  # type: ignore

                        effects = []
                        if clips:  # not first
                            effects.append(vfx.FadeIn(fade_s))
                        effects.append(vfx.FadeOut(fade_s))
                        if effects:
                            clip = clip.with_effects(effects)
                    else:
                        if clips:
                            clip = clip.fadein(fade_s)
                        clip = clip.fadeout(fade_s)
                except Exception:
                    pass

            clips.append(clip)

        if fade_s > 0 and len(clips) > 1:
            try:
                final = concatenate_videoclips(clips, method="compose", padding=-fade_s)
            except TypeError:
                final = concatenate_videoclips(clips, method="compose")
        else:
            final = concatenate_videoclips(clips, method="compose")

        # Audio mix
        audio_parts = []
        if music_path and Path(music_path).is_file():
            try:
                music = AudioFileClip(str(music_path))
                if hasattr(music, "with_duration"):
                    music = music.with_duration(final.duration)
                else:
                    music = music.set_duration(final.duration)
                if hasattr(music, "volumex"):
                    music = music.volumex(music_volume)
                elif hasattr(music, "with_volume_scaled"):
                    music = music.with_volume_scaled(music_volume)
                audio_parts.append(music)
            except Exception:
                pass
        if voice_path and Path(voice_path).is_file():
            try:
                vo = AudioFileClip(str(voice_path))
                if hasattr(vo, "with_duration"):
                    # keep natural length, do not stretch past video
                    if vo.duration > final.duration:
                        vo = vo.subclipped(0, final.duration) if hasattr(vo, "subclipped") else vo.subclip(0, final.duration)
                else:
                    if vo.duration > final.duration:
                        vo = vo.subclip(0, final.duration)
                if hasattr(vo, "volumex"):
                    vo = vo.volumex(voice_volume)
                elif hasattr(vo, "with_volume_scaled"):
                    vo = vo.with_volume_scaled(voice_volume)
                audio_parts.append(vo)
            except Exception:
                pass

        if audio_parts:
            try:
                mixed = CompositeAudioClip(audio_parts) if len(audio_parts) > 1 else audio_parts[0]
                if hasattr(final, "with_audio"):
                    final = final.with_audio(mixed)
                else:
                    final = final.set_audio(mixed)
            except Exception:
                pass

        write_kwargs = {
            "fps": fps,
            "codec": "libx264",
            "audio_codec": "aac" if audio_parts else None,
            "preset": "medium",
            "threads": 2,
        }
        # drop None audio_codec
        if write_kwargs["audio_codec"] is None:
            write_kwargs["audio"] = False
            write_kwargs.pop("audio_codec")
        try:
            write_kwargs["logger"] = None
        except Exception:
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
            for c in clips:
                try:
                    c.close()
                except Exception:
                    pass

    except Exception:
        # Fallback: ffmpeg concat demuxer (no watermark / audio mix)
        return _ffmpeg_concat(paths, out, ffmpeg_exe)

    if not out.is_file() or out.stat().st_size < 100:
        raise RuntimeError("Stitch failed — MP4 not written")
    return str(out.resolve())


def _ffmpeg_concat(paths: Sequence[Path], out: Path, ffmpeg_exe: Optional[str]) -> str:
    exe = ffmpeg_exe or _ensure_imageio_ffmpeg() or "ffmpeg"
    with tempfile.TemporaryDirectory() as td:
        lst = Path(td) / "list.txt"
        lines = []
        for p in paths:
            # escape single quotes for concat demuxer
            safe = str(p.resolve()).replace("'", "'\\''")
            lines.append(f"file '{safe}'")
        lst.write_text("\n".join(lines), encoding="utf-8")
        cmd = [
            exe,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c",
            "copy",
            str(out),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except Exception:
            # re-encode fallback
            cmd = [
                exe,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(lst),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(out),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
    if not out.is_file() or out.stat().st_size < 100:
        raise RuntimeError("ffmpeg concat failed")
    return str(out.resolve())


def save_upload_bytes(data: bytes, dest: PathLike) -> str:
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return str(p.resolve())
