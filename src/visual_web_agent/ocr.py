from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Iterable

import numpy as np
from PIL import Image
from rapidfuzz import fuzz


@dataclass(frozen=True, slots=True)
class OCRHit:
    text: str
    confidence: float
    bbox: tuple[int, int, int, int]

    @property
    def center(self) -> tuple[int, int]:
        left, top, right, bottom = self.bbox
        return ((left + right) // 2, (top + bottom) // 2)

    @property
    def normalized_text(self) -> str:
        return " ".join(self.text.lower().split())


class OCRReader:
    def __init__(self) -> None:
        self._reader = None

    @cached_property
    def reader(self):
        try:
            import easyocr
        except ImportError as exc:  # pragma: no cover - runtime dependency guard
            raise RuntimeError(
                "easyocr is required for visual text recognition. Install project dependencies first."
            ) from exc

        return easyocr.Reader(["en"], gpu=False)

    def read_image(self, image: Image.Image) -> list[OCRHit]:
        rgb = np.array(image.convert("RGB"))
        results = self.reader.readtext(rgb, detail=1, paragraph=False)
        hits: list[OCRHit] = []
        for box, text, confidence in results:
            xs = [int(point[0]) for point in box]
            ys = [int(point[1]) for point in box]
            hits.append(
                OCRHit(
                    text=text,
                    confidence=float(confidence),
                    bbox=(min(xs), min(ys), max(xs), max(ys)),
                )
            )
        return hits

    @staticmethod
    def best_match(hits: Iterable[OCRHit], needle: str, min_confidence: float = 0.0) -> OCRHit | None:
        needle_norm = " ".join(needle.lower().split())
        best_hit: OCRHit | None = None
        best_score = 0
        for hit in hits:
            if hit.confidence < min_confidence:
                continue
            score = fuzz.partial_ratio(needle_norm, hit.normalized_text)
            if score > best_score:
                best_score = score
                best_hit = hit
        return best_hit if best_score >= 70 else None

    @staticmethod
    def find_any(hits: Iterable[OCRHit], needles: Iterable[str], min_confidence: float = 0.0) -> OCRHit | None:
        normalized_needles = [" ".join(needle.lower().split()) for needle in needles]
        for hit in hits:
            if hit.confidence < min_confidence:
                continue
            text = hit.normalized_text
            if any(needle in text for needle in normalized_needles):
                return hit
        return None
