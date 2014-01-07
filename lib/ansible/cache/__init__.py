from ansible import utils
from ansible import constants as C
from ansible import errors

class FactCache(dict):

    def __init__(self, *args, **kwargs):

        self._plugin = utils.plugins.cache_loader.get(C.CACHE_PLUGIN)
        if self._plugin is None:
            return

    def __getitem__(self, key, default={}):
        return self._plugin.get(key, default)

    def __setitem__(self, key, val):
        self._plugin.set(key, value)

    def __repr__(self):
        return '%s' % (type(self))

