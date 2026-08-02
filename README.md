# Visual Web Agent

Visual browser automation for Bookshop.org that uses screenshots, OCR, and GUI input only.

## Overview

The project opens Bookshop.org in a local browser, searches for the requested books, reads the visible EAN/UPC values, and writes the result to JSON.

## Requirements

- Python 3.10+
- A local desktop session
- Chrome, Firefox, or Edge installed locally

## Project structure

- `src/visual_web_agent/browser.py` - browser launcher
- `src/visual_web_agent/automation.py` - screen capture and keyboard/mouse input
- `src/visual_web_agent/ocr.py` - OCR helpers
- `src/visual_web_agent/bookshop.py` - Bookshop workflow
- `src/visual_web_agent/cli.py` - CLI entrypoint
- `src/visual_web_agent/__main__.py` - `python -m visual_web_agent` support
- `output.json` - generated JSON output

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

`requirements.txt` contains the runtime and test dependencies. `pip install -e .` installs the package in editable mode so the CLI becomes available.

If OCR fails to initialize, confirm that the session has access to a visible desktop and that the dependencies installed successfully.

## Run

```bash
python -m visual_web_agent --output output.json
```

Or with explicit browser choice:

```bash
python -m visual_web_agent --browser chrome
```

## Testing

Run the test suite and a sample execution with:

```bash
pytest
python -m visual_web_agent --output output.json
```

After the run, verify that:

1. The browser opens in a visible desktop window.
2. The script searches for both target books.
3. `output.json` is created.
4. The JSON contains two book records with `ean_upc` values.

For reviewers, the same commands work in any normal desktop session with a local browser installed.

## Notes

- No browser automation framework is used.
- The workflow relies on screenshots, OCR, and GUI automation.
- The output format matches the assessment requirement.
