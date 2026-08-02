from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


BROWSER_CANDIDATES = {
    "chrome": ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser"),
    "edge": ("microsoft-edge", "microsoft-edge-stable"),
    "firefox": ("firefox",),
}

DEFAULT_BOOKSHOP_URL = "https://bookshop.org/"
DEFAULT_OUTPUT = Path("output.json")
DEFAULT_PAGE_WAIT_SECONDS = 2.5
DEFAULT_SCROLL_STEP = 700
DEFAULT_SCROLL_LIMIT = 8
DEFAULT_OCR_CONFIDENCE = 0.35


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    browser: str = "chrome"
    output_path: Path = DEFAULT_OUTPUT
    page_wait_seconds: float = DEFAULT_PAGE_WAIT_SECONDS
    scroll_step: int = DEFAULT_SCROLL_STEP
    scroll_limit: int = DEFAULT_SCROLL_LIMIT
    ocr_confidence: float = DEFAULT_OCR_CONFIDENCE
