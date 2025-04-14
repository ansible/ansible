from __future__ import annotations

DOCUMENTATION = """
    name: dummy_cache
    short_description: dummy cache
    options:
      dummy:
        type: str
"""

import json
import os
import pathlib
import typing as t

from ansible.plugins.cache import BaseCacheModule


class CacheModule(BaseCacheModule):
    def __init__(self, *args, **kwargs):
        if not os.environ.get('DUMMY_CACHE_SKIP_SUPER'):
            super().__init__(*args, **kwargs)

        self._storage_dir = pathlib.Path(os.environ.get('OUTPUT_DIR')) / 'cache-storage'
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_key_path(self, key: str) -> pathlib.Path:
        return self._storage_dir / key

    def get(self, key: t.Any) -> object:
        try:
            return json.loads(self._get_key_path(key).read_text())
        except FileNotFoundError:
            raise KeyError(key) from None

    def set(self, key: str, value: object) -> None:
        self._get_key_path(key).write_text(json.dumps(value))

    def keys(self) -> list[str]:
        path: pathlib.Path

        return [path.name for path in self._storage_dir.iterdir()]

    def contains(self, key: object) -> bool:
        try:
            self.get(key)
        except KeyError:
            return False

        return True

    def delete(self, key: str) -> None:
        self._get_key_path(key).unlink(missing_ok=True)

    def flush(self) -> None:
        for key in self.keys():
            self.delete(key)
