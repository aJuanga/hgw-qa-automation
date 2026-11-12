"""Compresión de capturas para reportes livianos (aptos para enviar por correo)."""
import io
from pathlib import Path

from PIL import Image


def compact_jpeg(path, max_width=1000, quality=68):
    img = Image.open(Path(path)).convert("RGB")
    if img.width > max_width:
        img = img.resize((max_width, int(img.height * max_width / img.width)))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True)
    buf.seek(0)
    return buf
