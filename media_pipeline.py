"""Turn Suno MCP media results into a YouTube-ready video file."""
import base64
import ipaddress
import json
import re
import socket
import subprocess
import textwrap
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MAX_MEDIA_BYTES = 500 * 1024 * 1024
URL_PATTERN = re.compile(r"https://[^\s<>\]\[()\"']+", re.IGNORECASE)
MEDIA_KEYS = {"audio_url", "audioUrl", "download_url", "downloadUrl", "media_url", "mediaUrl", "video_url", "videoUrl", "url", "href"}


def _safe_media_url(url):
    parsed = urllib.parse.urlparse(url.rstrip(".,;"))
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    host = parsed.hostname.lower().rstrip(".")
    if not (host == "suno.com" or host.endswith(".suno.com") or host == "suno.ai" or host.endswith(".suno.ai")):
        return None
    try:
        for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                return None
    except OSError:
        return None
    return parsed.geturl()


def _extension_from_content(content_type, url, header_bytes):
    ctype = (content_type or "").lower().split(";", 1)[0]
    path = urllib.parse.urlparse(url).path.lower()
    ext = Path(path).suffix.lower()
    if ext in {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".mp4", ".mov", ".webm"}:
        return ext
    if ctype in {"video/mp4", "audio/mp4"}: return ".mp4" if ctype.startswith("video") or b"ftyp" in header_bytes[:32] else ".m4a"
    if ctype == "video/quicktime": return ".mov"
    if ctype in {"audio/mpeg", "audio/mp3"} or header_bytes.startswith(b"ID3"): return ".mp3"
    if ctype in {"audio/wav", "audio/x-wav"} or header_bytes.startswith(b"RIFF"): return ".wav"
    if ctype == "audio/flac" or header_bytes.startswith(b"fLaC"): return ".flac"
    if ctype == "audio/ogg" or header_bytes.startswith(b"OggS"): return ".ogg"
    return None


def _download_url(url, folder):
    url = _safe_media_url(url)
    if not url:
        return None
    req = urllib.request.Request(url, headers={"User-Agent": "SunoStudio/0.2"})
    with urllib.request.urlopen(req, timeout=45) as response:
        ctype = response.headers.get("Content-Type", "")
        size = response.headers.get("Content-Length")
        if size and int(size) > MAX_MEDIA_BYTES:
            raise ValueError("Suno 반환 파일이 500MB 제한을 넘습니다.")
        payload = response.read(MAX_MEDIA_BYTES + 1)
        if len(payload) > MAX_MEDIA_BYTES:
            raise ValueError("Suno 반환 파일이 500MB 제한을 넘습니다.")
        ext = _extension_from_content(ctype, url, payload[:32])
        if not ext:
            return None
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / ("suno_output" + ext)
        path.write_bytes(payload)
        return path


def _walk_media(obj):
    urls, audio_blobs = [], []
    def visit(value, key=""):
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, str) and k in MEDIA_KEYS and v.startswith("https://"):
                    urls.append(v)
                visit(v, k)
        elif isinstance(value, (list, tuple)):
            for item in value: visit(item, key)
        elif isinstance(value, str):
            if value.startswith("https://"):
                urls.append(value)
            elif key in {"text", "data"}:
                try:
                    parsed = json.loads(value)
                    visit(parsed, key)
                except (ValueError, TypeError):
                    urls.extend(URL_PATTERN.findall(value))
    structured = getattr(obj, "structuredContent", None)
    if structured is not None:
        visit(structured)
    for block in getattr(obj, "content", []) or []:
        kind = getattr(block, "type", None)
        if kind == "audio":
            data = getattr(block, "data", "")
            mime = getattr(block, "mimeType", "audio/mpeg")
            if data:
                try: audio_blobs.append((base64.b64decode(data), mime))
                except (ValueError, TypeError): pass
        elif kind == "text":
            visit({"text": getattr(block, "text", "")})
        elif kind == "resource":
            resource = getattr(block, "resource", None)
            if resource:
                mime = getattr(resource, "mimeType", "") or ""
                blob = getattr(resource, "blob", None)
                if blob and mime.startswith("audio/"):
                    try: audio_blobs.append((base64.b64decode(blob), mime))
                    except (ValueError, TypeError): pass
                visit(getattr(resource, "text", ""))
        elif kind == "resource_link":
            visit({"url": getattr(block, "uri", "")})
    return list(dict.fromkeys(urls)), audio_blobs


def save_audio_from_result(result, folder):
    folder = Path(folder)
    urls, blobs = _walk_media(result)
    folder.mkdir(parents=True, exist_ok=True)
    for index, (data, mime) in enumerate(blobs):
        ext = _extension_from_content(mime, "", data[:32])
        if ext:
            path = folder / f"suno_output_{index}{ext}"
            path.write_bytes(data)
            return path
    for url in urls:
        try:
            path = _download_url(url, folder)
            if path:
                return path
        except OSError:
            continue
    return None


def _cover_art(title, genre, output_path):
    width, height = 1920, 1080
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        t = y / max(1, height - 1)
        row = (int(13 + 20*t), int(19 + 16*t), int(43 + 30*t))
        draw.line((0, y, width, y), fill=row)
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0)); glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((width*.48, -height*.6, width*1.15, height*.9), fill=(83, 82, 170, 76))
    image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(image)
    font_paths = [r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\gulim.ttc", r"C:\Windows\Fonts\arial.ttf"]
    font = None
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, 76); break
        except OSError: pass
    if font is None: font = ImageFont.load_default()
    small = ImageFont.truetype(font_paths[0], 32) if Path(font_paths[0]).exists() else ImageFont.load_default()
    label = "\n".join(textwrap.wrap(str(title).strip()[:60] or "Suno Studio", width=22))
    draw.rounded_rectangle((130, 150, 178, 220), radius=24, fill=(129, 140, 248))
    draw.multiline_text((130, 420), label, font=font, fill=(250, 250, 255), stroke_width=2, stroke_fill=(14, 18, 36), spacing=18)
    draw.text((136, 690), str(genre)[:60], font=small, fill=(186, 195, 226))
    draw.text((136, 920), "SUNO STUDIO  ·  ORIGINAL MUSIC", font=small, fill=(136, 149, 190))
    image.save(output_path, format="PNG")


def make_youtube_video(audio_path, title, genre, output_path):
    import imageio_ffmpeg
    audio_path, output_path = Path(audio_path), Path(output_path)
    cover_path = output_path.with_suffix(".cover.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _cover_art(title, genre, cover_path)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "1", "-i", str(cover_path), "-i", str(audio_path), "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(output_path)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0 or not output_path.exists():
        raise RuntimeError("YouTube 영상 변환에 실패했습니다: " + (proc.stderr[-1200:] if proc.stderr else "ffmpeg failed"))
    return output_path
