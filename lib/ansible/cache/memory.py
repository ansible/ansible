
class CacheModule(object):

    def __init__(self, *args, **kwargs):
        self._cache = {}

    def get(self, key, default):
        return self._cache.get(key, default)

    def set(self, key, value):
        self._cache[key] = value

