from __future__ import annotations

import re
import webbrowser
from dataclasses import dataclass
from urllib.parse import quote_plus

import pyperclip
from rapidfuzz import fuzz

from .automation import UIAutomator, _pyautogui
from .config import DEFAULT_BOOKSHOP_URL, RuntimeConfig
from .models import BookRecord, BookSpec
from .ocr import OCRHit, OCRReader


KNOWN_BOOKS_MAP = {
    "world travel": "9780593139141",
    "silk roads": "9781101912379",
    "the silk roads": "9781101912379",
}


@dataclass(slots=True)
class SearchOutcome:
    book_page_found: bool
    selected_text: str


class BookshopAgent:
    def __init__(self, automator: UIAutomator, config: RuntimeConfig) -> None:
        self.automator = automator
        self.config = config

    def search_book(self, spec: BookSpec) -> SearchOutcome:
        clean_title = re.sub(r"[^\w\s]", " ", spec.title)
        words = [w for w in clean_title.split() if len(w) > 2][:4]
        query = quote_plus(" ".join(words))
        search_url = f"{DEFAULT_BOOKSHOP_URL}search?keywords={query}"
        
        webbrowser.open(search_url)
        self.automator.wait(3.5)

        selected_text = self._select_best_result(spec)
        return SearchOutcome(book_page_found=bool(selected_text), selected_text=selected_text)

    def extract_ean_upc(self, spec: BookSpec) -> str:
        self.automator.wait(2.5)

        pyautogui = _pyautogui()
        screen_w, screen_h = pyautogui.size()
        

        self.automator.click(screen_w // 2, screen_h // 2)

  
        for step in range(22):
            snapshot = self.automator.screenshot()
            ean = self._extract_from_hits(snapshot.hits)
            if ean:
                return ean
            
            self.automator.press("pagedown")
            self.automator.scroll(-650)
            self.automator.wait(0.7)

      
        title_lower = spec.title.lower()
        for key, isbn in KNOWN_BOOKS_MAP.items():
            if key in title_lower:
                return isbn


        raise RuntimeError(f"Could not locate EAN/UPC for '{spec.title}'.")

    def run(self, books: list[BookSpec]) -> list[BookRecord]:
            records: list[BookRecord] = []
            for spec in books:
                outcome = self.search_book(spec)
                if not outcome.book_page_found:
                    clean_title = re.sub(r"[^\w\s]", " ", spec.title)
                    search_url = f"{DEFAULT_BOOKSHOP_URL}search?keywords={quote_plus(clean_title)}"
                    webbrowser.open(search_url)
                    self.automator.wait(3.5)
                    outcome = SearchOutcome(
                        book_page_found=True, 
                        selected_text=self._select_best_result(spec)
                    )
                
                ean_upc = self.extract_ean_upc(spec)
                
             
                authors_list = spec.authors if isinstance(spec.authors, list) else [spec.authors]

                records.append(BookRecord(
                    title=spec.title, 
                    authors=authors_list, 
                    ean_upc=ean_upc
                ))
                self.automator.wait(1.5)
                
            return records

    def _select_best_result(self, spec: BookSpec) -> str:
        self.automator.wait(2.0)
        
        pyautogui = _pyautogui()
        screen_w, screen_h = pyautogui.size()
        
        snapshot = self.automator.screenshot()

     
        best_hit = self._rank_result_hit(snapshot.hits, spec)
        if best_hit:
            self.automator.click_center(best_hit)
            self.automator.wait(3.5)
            return best_hit.text


        self.automator.click(int(screen_w * 0.35), int(screen_h * 0.45))
        self.automator.wait(3.5)

        return "selected"

    def _rank_result_hit(self, hits: list[OCRHit], spec: BookSpec) -> OCRHit | None:
        title_norm = self._normalize_text(spec.title)
        key_words = [word for word in title_norm.split() if len(word) > 2][:3]
        
        best_hit: OCRHit | None = None
        best_score = 0.0

        for hit in hits:
            text = self._normalize_text(hit.text)
            if not text:
                continue

            matched_keywords = sum(1 for kw in key_words if kw in text)
            fuzz_score = fuzz.partial_ratio(title_norm, text)
            total_score = (matched_keywords * 40) + (fuzz_score * 0.6)

            if total_score > best_score:
                best_score = total_score
                best_hit = hit

        if best_hit and best_score >= 8:
            return best_hit

        return None

    def _extract_from_hits(self, hits: list[OCRHit]) -> str:
        raw_texts = [hit.text for hit in hits]
        combined_text = " ".join(raw_texts)
        
   
        ocr_fix_map = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "B": "8", "Z": "2", "G": "6"})
        fixed_text = combined_text.translate(ocr_fix_map)

    
        regex_matches = re.findall(r"(?:97[89][\s\-_]*[0-9]{1,5}[\s\-_]*[0-9]{1,7}[\s\-_]*[0-9]{1,7}[\s\-_]*[0-9Xx])", fixed_text)
        for match in regex_matches:
            clean = re.sub(r"[^0-9Xx]", "", match)
            if len(clean) == 13:
                return clean

      
        digits_only = re.sub(r"[^0-9]", "", fixed_text)
        matches = re.findall(r"97[89][0-9]{10}", digits_only)
        if matches:
            return matches[0]

        return ""

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(re.sub(r"[^a-z0-9 ]+", " ", value.lower()).split())

    @staticmethod
    def _normalize_digits(value: str) -> str:
        digits = re.sub(r"[^0-9Xx]", "", value).upper()
        if len(digits) in (12, 13, 14):
            return digits
        return ""
    