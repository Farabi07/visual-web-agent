from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .ocr import OCRHit, OCRReader


def _pyautogui():
    try:
        import pyautogui
    except Exception as exc: 
        raise RuntimeError(
            "pyautogui could not be initialized. Run this project from a visible desktop session with a local display."
        ) from exc

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.15
    return pyautogui


def _capture_screen() -> Image.Image:
    try:
        import mss
    except ImportError as exc:
        raise RuntimeError("mss is required for screenshots. Install project dependencies first.") from exc

    try:
        with mss.mss() as capture:
            monitor = capture.monitors[0]
            pixels = capture.grab(monitor)
            return Image.frombytes("RGB", pixels.size, pixels.rgb)
    except Exception as exc:
        raise RuntimeError(
            "Unable to capture the screen. Run this project from a visible desktop session with a local display."
        ) from exc


@dataclass(slots=True)
class ScreenSnapshot:
    image_path: Path | None
    image: Image.Image
    hits: list[OCRHit]


class UIAutomator:
    def __init__(self, ocr_reader: OCRReader) -> None:
        self.ocr_reader = ocr_reader

    def focus_browser(self) -> None:
        pyautogui = _pyautogui()
        try:
            subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "chrome", "windowactivate"], check=False)
            subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "firefox", "windowactivate"], check=False)
        except Exception:
            pass

        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(0.3)

    def screenshot(self, path: Path | None = None) -> ScreenSnapshot:
        image = _capture_screen()
        if path is not None:
            image.save(path)
        hits = self.ocr_reader.read_image(image)
        return ScreenSnapshot(image_path=path, image=image, hits=hits)

    def wait(self, seconds: float) -> None:
        time.sleep(seconds)

    def click(self, x: int, y: int) -> None:
        pyautogui = _pyautogui()
        pyautogui.click(x, y)

    def click_center(self, hit: OCRHit) -> None:
        pyautogui = _pyautogui()
        pyautogui.click(*hit.center)

    def type_text(self, value: str) -> None:
        pyautogui = _pyautogui()
        pyautogui.write(value, interval=0.02)

    def hotkey(self, *keys: str) -> None:
        pyautogui = _pyautogui()
        pyautogui.hotkey(*keys)

    def press(self, key: str) -> None:
        pyautogui = _pyautogui()
        pyautogui.press(key)

    def scroll(self, amount: int) -> None:
        pyautogui = _pyautogui()
        pyautogui.scroll(amount)

    def copy_selection(self) -> str:
        self.hotkey("ctrl", "c")
        self.wait(0.2)
        try:
            import pyperclip
        except ImportError:
            return ""
        return pyperclip.paste()