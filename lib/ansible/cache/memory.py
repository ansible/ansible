import os
import time

try:
    import json
except ImportError:
    import simplejson as json

_cache = {}

class CacheModule(object):

    def __init__(self, *args, **kwargs):
        global _cache
        _cache = {}

    def get(self, key, default):
        global _cache
        return _cache.get(key, default)

    def set(self, key, value):
        global _cache
        _cache[key] = value

    #def update(self, *args, **kwargs):
    #   global _cache
    #   _cache.update(args, kwargs)


