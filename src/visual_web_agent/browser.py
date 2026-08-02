from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import BROWSER_CANDIDATES


@dataclass(slots=True)
class BrowserSession:
    executable: str
    process: subprocess.Popen[str]


class BrowserLauncher:
    def __init__(self, browser_name: str = "chrome") -> None:
        self.browser_name = browser_name

    def resolve_executable(self) -> str:
        candidates = BROWSER_CANDIDATES.get(self.browser_name.lower(), BROWSER_CANDIDATES["chrome"])
        for candidate in candidates:
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
        raise FileNotFoundError(
            f"No local browser executable found for '{self.browser_name}'. "
            "Install Chrome, Edge, or Firefox and make sure it is on PATH."
        )

    def open(self, url: str) -> BrowserSession:
        executable = self.resolve_executable()
        process = subprocess.Popen(
            [executable, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return BrowserSession(executable=executable, process=process)
