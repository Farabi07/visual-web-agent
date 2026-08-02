from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote_plus

from .automation import UIAutomator
from .config import DEFAULT_BOOKSHOP_URL, RuntimeConfig
from .models import BookRecord, BookSpec
from .ocr import OCRHit, OCRReader

EAN_RE = re.compile(r"\b(?:EAN/UPC|UPC|EAN)\b[^0-9A-Za-z]{0,12}([0-9Xx-]{12,14})\b")
NUMERIC_RE = re.compile(r"\b(?:97[89][0-9]{10}|[0-9]{12,13})\b")


@dataclass(slots=True)
class SearchOutcome:
    book_page_found: bool
    selected_text: str


class BookshopAgent:
    def __init__(self, automator: UIAutomator, config: RuntimeConfig) -> None:
        self.automator = automator
        self.config = config

    def search_book(self, spec: BookSpec) -> SearchOutcome:
        self.automator.hotkey("ctrl", "l")
        self.automator.type_text(DEFAULT_BOOKSHOP_URL)
        self.automator.press("enter")
        self.automator.wait(self.config.page_wait_seconds)

        if not self._search_via_visible_ui(spec):
            self._search_via_url(spec)

        selected_text = self._select_best_result(spec)
        return SearchOutcome(book_page_found=bool(selected_text), selected_text=selected_text)

    def extract_ean_upc(self, spec: BookSpec) -> str:
        for _ in range(self.config.scroll_limit):
            snapshot = self.automator.screenshot()
            ean = self._extract_from_hits(snapshot.hits)
            if ean:
                return ean
            self.automator.scroll(-self.config.scroll_step)
            self.automator.wait(0.6)
        raise RuntimeError(f"Could not locate EAN/UPC for '{spec.title}'.")

    def run(self, books: list[BookSpec]) -> list[BookRecord]:
        records: list[BookRecord] = []
        for spec in books:
            self._open_homepage()
            outcome = self.search_book(spec)
            if not outcome.book_page_found:
                raise RuntimeError(f"Could not select a matching result for '{spec.title}'.")
            ean_upc = self.extract_ean_upc(spec)
            records.append(BookRecord(title=spec.title, authors=spec.authors, ean_upc=ean_upc))
        return records

    def _open_homepage(self) -> None:
        self.automator.hotkey("ctrl", "l")
        self.automator.type_text(DEFAULT_BOOKSHOP_URL)
        self.automator.press("enter")
        self.automator.wait(self.config.page_wait_seconds)

    def _search_via_visible_ui(self, spec: BookSpec) -> bool:
        snapshot = self.automator.screenshot()
        search_hit = OCRReader.find_any(snapshot.hits, ["search", "search books", "search for books"], self.config.ocr_confidence)
        if not search_hit:
            return False
        self.automator.click_center(search_hit)
        self.automator.type_text(spec.search_text)
        self.automator.press("enter")
        self.automator.wait(self.config.page_wait_seconds)
        return True

    def _search_via_url(self, spec: BookSpec) -> None:
        query = quote_plus(spec.search_text)
        self.automator.hotkey("ctrl", "l")
        self.automator.type_text(f"{DEFAULT_BOOKSHOP_URL}search?keywords={query}")
        self.automator.press("enter")
        self.automator.wait(self.config.page_wait_seconds)

    def _select_best_result(self, spec: BookSpec) -> str:
        target_text = spec.search_text
        for _ in range(6):
            snapshot = self.automator.screenshot()
            best_hit = OCRReader.best_match(snapshot.hits, target_text, self.config.ocr_confidence)
            if best_hit and self._looks_like_book_result(best_hit, spec):
                self.automator.click_center(best_hit)
                self.automator.wait(self.config.page_wait_seconds)
                return best_hit.text
            self.automator.scroll(-self.config.scroll_step)
            self.automator.wait(0.5)
        return ""

    def _looks_like_book_result(self, hit: OCRHit, spec: BookSpec) -> bool:
        text = hit.normalized_text
        title_tokens = [token.lower() for token in spec.title.split() if len(token) > 2]
        author_tokens = [token.lower() for author in spec.authors for token in author.split() if len(token) > 2]
        title_matches = sum(1 for token in title_tokens if token in text)
        author_matches = sum(1 for token in author_tokens if token in text)
        return title_matches >= max(2, len(title_tokens) // 3) and (author_matches >= 1 or not spec.authors)

    def _extract_from_hits(self, hits: list[OCRHit]) -> str:
        for hit in hits:
            label = hit.normalized_text
            label_match = EAN_RE.search(label)
            if label_match:
                candidate = self._normalize_digits(label_match.group(1))
                if candidate:
                    return candidate
        for hit in hits:
            numeric_match = NUMERIC_RE.search(hit.normalized_text)
            if numeric_match:
                candidate = self._normalize_digits(numeric_match.group(0))
                if candidate:
                    return candidate
        return ""

    @staticmethod
    def _normalize_digits(value: str) -> str:
        digits = re.sub(r"[^0-9Xx]", "", value).upper()
        if len(digits) in (12, 13, 14):
            return digits
        return ""
