from __future__ import annotations

import pkgutil

from my_module import sub


def run() -> list[str]:
    return [m[1] for m in pkgutil.iter_modules(sub.__path__)]
