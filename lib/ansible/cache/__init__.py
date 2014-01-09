from ansible import utils
from ansible import constants as C
from ansible import errors

GET = None
SET = None

class FactCache(dict):

    def __init__(self, *args, **kwargs):

        global GET
        global SET

        self._plugin = utils.plugins.cache_loader.get(C.CACHE_PLUGIN)
        if self._plugin is None:
            return

        self.update(*args, **kwargs)
        GET = self._plugin.get
        SET = self._plugin.set

    def __getitem__(self, key, default={}):
        return GET(key, default)

    def __setitem__(self, key, val):
        SET(key, value)

    def __repr__(self):
        return '%s' % (type(self))

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).iteritems():
            SET(k,v)


