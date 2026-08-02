from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import BookSpec


DEFAULT_BOOKS = [
    BookSpec(title="World Travel: An Irreverent Guide", authors=("Anthony Bourdain", "Laurie Woolever")),
    BookSpec(title="The Silk Roads - A New History of the World", authors=("Peter Frankopan",)),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract Bookshop.org EAN/UPC values using visual automation.")
    parser.add_argument("--browser", default="chrome", choices=["chrome", "edge", "firefox"], help="Local browser to launch")
    parser.add_argument("--output", default="output.json", help="Path to the JSON output file")
    parser.add_argument("--books-file", help="Optional JSON file containing a custom list of books")
    return parser


def load_books(path: str | None) -> list[BookSpec]:
    if not path:
        return DEFAULT_BOOKS
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    books = []
    for item in data["books"]:
        authors = tuple(item.get("authors") or ([item["author"]] if item.get("author") else []))
        books.append(BookSpec(title=item["title"], authors=authors))
    return books


def write_output(output_path: Path, records) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "books": [
            _format_book_record(record)
            for record in records
        ]
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _format_book_record(record: BookSpec):
    book = {"title": record.title, "ean_upc": record.ean_upc}
    if len(record.authors) == 1:
        book["author"] = record.authors[0]
    else:
        book["authors"] = list(record.authors)
    return book


def main() -> int:
    from .automation import UIAutomator
    from .bookshop import BookshopAgent
    from .browser import BrowserLauncher
    from .config import RuntimeConfig
    from .ocr import OCRReader

    parser = build_parser()
    args = parser.parse_args()

    config = RuntimeConfig(browser=args.browser, output_path=Path(args.output))
    books = load_books(args.books_file)

    launcher = BrowserLauncher(config.browser)
    launcher.open("https://bookshop.org/")

    ocr_reader = OCRReader()
    automator = UIAutomator(ocr_reader)
    agent = BookshopAgent(automator=automator, config=config)

    records = agent.run(books)
    write_output(config.output_path, records)

    print(f"Saved {len(records)} book records to {config.output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
