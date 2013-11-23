from ansible import utils
from UserDict import DictMixin

class Cache(DictMixin, dict):


    def __init__(self, default=dict, *a, **kw):
        if (default is not None and not hasattr(default, '__call__')):
            raise TypeError('first argument must be callable')
        self._default = default
        #TODO: pull single/list from config, maybe ALL as special keyword
        self._caches = utils.plugins.cache_loader.all()


    def __getitem__(self, name):
        value = None
        try:
            value = super(Cache, self).__getitem__(name)
        except KeyError:
            pass

        if value is None or not value:
            for cache in self._caches:
                value = cache.get(name)
                if value is not None:
                    break

        if value is None:
            value = self._default()

        super(Cache, self).__setitem__(name, value)
        return value


    def __setitem__(self, name, value):

        for cache in self._caches:
            cache.save(name, value)
        super(Cache, self).__setitem__(name, value)


    def update(self, *a, **kw):

        if a and len(a) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(a))
            other = dict(*a, **kw)
            for key in other:
                super(Cache, self).__setitem__(name, other[key])
                for cache in self._caches:
                    cache.save(key, other[key])

        for key in kw:
            super(Cache, self).__setitem__(name, kw[key])
            for cache in self._caches:
                cache.save(key, kw[key])


    def setdefault(self, name, value=None):

        if value is None:
            value = self._default()
            super(Cache, self).__setitem__(name, value)

        return value
