from ansible import utils
from ansible import constants as C
from ansible import errors

GET = None
SET = None
#UPDATE = None

class FactCache(dict):

    def __init__(self, *args, **kwargs):

        global GET
        global SET
        #global UPDATE

        self._plugin = utils.plugins.cache_loader.get(C.CACHE_PLUGIN)
        if self._plugin is None:
            return

        GET = self._plugin.get
        SET = self._plugin.set
        #UPDATE = self._plugin.update
        #self.update(*args, **kwargs)

    def __getitem__(self, key, default={}):
        return GET(key, default)

    def __setitem__(self, key, val):
        SET(key, value)

    def __repr__(self):
        return '%s' % (type(self))

