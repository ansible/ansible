from __future__ import annotations

import functools
import json
import json.encoder
import json.decoder
import typing as t

from .._wrapt import ObjectProxy
from .._json._profiles import _cache_persistence


class PluginInterposer(ObjectProxy):
    """Proxies a Cache plugin instance to implement transparent encapsulation of serialized Ansible internal data types."""

    _PAYLOAD_KEY = '__payload__'
    """The key used to store the serialized payload."""

    def get(self, key: str) -> dict[str, object]:
        return self._decode(self.__wrapped__.get(self._get_key(key)))

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
        return f's{_cache_persistence._Profile.schema_id}_'

    @classmethod
    def _get_key(cls, key: str) -> str:
        """Augment the supplied key with a schema identifier to allow for side-by-side caching across incompatible schemas."""
        return f'{cls._get_wrapped_key_prefix()}{key}'

    def _encode(self, value: dict[str, object]) -> dict[str, object]:
        return {self._PAYLOAD_KEY: json.dumps(value, cls=_cache_persistence.Encoder)}

    def _decode(self, value: dict[str, t.Any]) -> dict[str, object]:
        return json.loads(value[self._PAYLOAD_KEY], cls=_cache_persistence.Decoder)
