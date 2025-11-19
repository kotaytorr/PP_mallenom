import os
from PIL import Image, ImageOps

class ImageProcessor:
    def __init__(self):
        self.path = None
        self.original = None
        self.current = None
        self._format = None

    def load_image(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        img = Image.open(path).convert("RGBA")
        self.path = path
        self.original = img.copy()
        self.current = img.copy()
        self._format = img.format or os.path.splitext(path)[1].lstrip('.').upper()
        return self.current

    def crop(self, x1: int, y1: int, x2: int, y2: int):
        if self.current is None:
            raise RuntimeError("No image loaded")
        w, h = self.current.size
        x1c = max(0, min(w, int(round(x1))))
        x2c = max(0, min(w, int(round(x2))))
        y1c = max(0, min(h, int(round(y1))))
        y2c = max(0, min(h, int(round(y2))))
        if x2c <= x1c or y2c <= y1c:
            raise ValueError("Invalid crop coordinates")
        self.current = self.current.crop((x1c, y1c, x2c, y2c))
        return self.current

    def to_grayscale(self):
        if self.current is None:
            raise RuntimeError("No image loaded")
        rgb = self.current.convert("RGB")
        gray = ImageOps.grayscale(rgb).convert("RGBA")
        self.current = gray
        return self.current

    def resize(self, width: int, height: int, keep_aspect: bool = False):
        if self.current is None:
            raise RuntimeError("No image loaded")
        w, h = self.current.size
        if keep_aspect:
            ratio = min(width / w, height / h)
            new_w = max(1, int(round(w * ratio)))
            new_h = max(1, int(round(h * ratio)))
        else:
            new_w = max(1, int(width))
            new_h = max(1, int(height))
        self.current = self.current.resize((new_w, new_h), Image.LANCZOS)
        return self.current

    def get_info(self) -> dict:
        if self.current is None:
            return {}
        w, h = self.current.size
        try:
            size = os.path.getsize(self.path) if self.path else None
        except:
            size = None
        return {
            "path": self.path,
            "format": self._format,
            "width": w,
            "height": h,
            "filesize_bytes": size,
            "mode": self.current.mode
        }

    def get_image(self):
        return self.current.copy() if self.current else None

    def reset_to_original(self):
        if self.original is not None:
            self.current = self.original.copy()
            return self.current