from __future__ import annotations

import functools
import json
import json.encoder
import json.decoder
import typing as t

from .._wrapt import ObjectProxy
from .._json._profiles import _cache_persistence
from ansible import release as _release
from ansible import constants as _constants
from ansible.utils.display import Display

display = Display()


class PluginInterposer(ObjectProxy):
    """Proxies a Cache plugin instance to implement transparent encapsulation of serialized Ansible internal data types."""

    _PAYLOAD_KEY = '__payload__'
    """The key used to store the serialized payload."""

    def get(self, key: str) -> dict[str, object]:
        value = self.__wrapped__.get(self._get_key(key))
        if value is None:
            # If there exists a wrapped key that restores to this key but does
            # not start with the current prefix, it likely indicates a version
            # mismatch. Log a verbose message to aid debugging.
            try:
                prefix = self._get_wrapped_key_prefix()
                for wk in self.__wrapped__.keys():
                    restored = self._restore_key(wk)
                    if restored == key and not wk.startswith(prefix):
                        display.vvv(f"Cache key '{key}' skipped due to Ansible version mismatch.")
                        break
            except Exception:
                # Best-effort logging only; do not raise on errors
                pass

            return None

        return self._decode(value)

    def set(self, key: str, value: dict[str, object]) -> None:
        self.__wrapped__.set(self._get_key(key), self._encode(value))

    def keys(self) -> t.Sequence[str]:
        return [k for k in (self._restore_key(k) for k in self.__wrapped__.keys()) if k is not None]

    def contains(self, key: t.Any) -> bool:
        return self.__wrapped__.contains(self._get_key(key))

    def delete(self, key: str) -> None:
        self.__wrapped__.delete(self._get_key(key))

    @classmethod
    def _restore_key(cls, wrapped_key: str) -> str | None:
        prefix = cls._get_wrapped_key_prefix()

        if not wrapped_key.startswith(prefix):
            return None

        return wrapped_key[len(prefix) :]

    @classmethod
    @functools.cache
    def _get_wrapped_key_prefix(cls) -> str:
        # Base schema prefix (keeps existing behavior)
        prefix = f's{_cache_persistence._Profile.schema_id}_'

        # Optionally include Ansible core version as an additional prefix to
        # invalidate caches automatically when core version changes. This is
        # controlled by the `fact_caching_version_invalidation` config option
        # (ini key: fact_caching_version_invalidation, env: ANSIBLE_CACHE_PLUGIN_VERSION_INVALIDATION).
        try:
            enabled = bool(_constants.config.get_config_value('fact_caching_version_invalidation'))
        except Exception:
            # If config subsystem isn't available for any reason, default to True
            enabled = True

        if enabled:
            # Use release.__version__ for the current core version. Normalize to a safe string.
            version = getattr(_release, '__version__', None) or ''
            # Sanitize version by replacing whitespace or ':' to avoid interfering with key formats
            version = str(version).replace(':', '_').replace(' ', '_')
            return f'{version}:{prefix}'

        return prefix

    @classmethod
    def _get_key(cls, key: str) -> str:
        """Augment the supplied key with a schema identifier to allow for side-by-side caching across incompatible schemas."""
        return f'{cls._get_wrapped_key_prefix()}{key}'

    def _encode(self, value: dict[str, object]) -> dict[str, object]:
        return {self._PAYLOAD_KEY: json.dumps(value, cls=_cache_persistence.Encoder)}

    def _decode(self, value: dict[str, t.Any]) -> dict[str, object]:
        return json.loads(value[self._PAYLOAD_KEY], cls=_cache_persistence.Decoder)
