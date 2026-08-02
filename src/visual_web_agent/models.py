from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BookSpec:
    title: str
    authors: tuple[str, ...] = ()

    @property
    def search_text(self) -> str:
        if self.authors:
            return f"{self.title} {' '.join(self.authors)}"
        return self.title


@dataclass(frozen=True, slots=True)
class BookRecord:
    title: str
    authors: tuple[str, ...]
    ean_upc: str
