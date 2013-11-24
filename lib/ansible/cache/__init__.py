from ansible import utils
from UserDict import DictMixin

class Cache(DictMixin, dict):


    def __init__(self, default=None, *a, **kw):

        if (default is not None and not hasattr(default, '__call__')):
            raise TypeError('first argument must be callable')

        #TODO: pull single/list from config, maybe ALL as special keyword
        self._caches = utils.plugins.cache_loader.all()
        self._default = default


    def __contains__(self, name):
        throwaway = self.__getitem__(name) # force cache load if needed
        return super(Cache, self).__contains__(name)


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


    def keys(self):

        print 'doing keys'
        ret = []

        for cache in self._caches:
            ret.update(cache.cached())
        ret.update(super(Cache,self).keys())
        print 'ret %s' % ret

        return ret


    def _validate_key(self, name):

        if super(Cache, self)._validate_key(name):
            return True

        for cache in self._caches:
            if cache.get(name):
                return True

        return False


    def __getattribute__(self, name):
        import inspect
        returned = object.__getattribute__(self, name)
        if inspect.isfunction(returned) or inspect.ismethod(returned):
            print 'called Cache.', returned.__name__
        return returned

