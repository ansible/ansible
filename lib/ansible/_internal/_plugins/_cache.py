from __future__ import annotations

from ansible._internal._datatag._tags import Origin
from .._wrapt import ObjectProxy


class PluginInterposer(ObjectProxy):
    """Proxies a Cache plugin instance to ensure origin tracking for fact_cache plugins"""

    def get(self, key: str) -> dict[str, object]:
        value = self.__wrapped__.get(key)
        if not Origin.is_tagged_on(value):
            value = Origin(description='<fact cache>').tag(value)
        return value
