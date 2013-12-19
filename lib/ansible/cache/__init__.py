from ansible import utils

class Cache(dict):


    def __init__(self, default=None, *a, **kw):

        if (default is not None and not hasattr(default, '__call__')):
            raise TypeError('first argument must be callable')

        #TODO: pull single/list from config, maybe ALL as special keyword
        self._caches = utils.plugins.cache_loader.all()
        self._default = default

        # initialize dict
        self.update(*a, **kw)


    def __contains__(self, name):
        res = self.__getitem__(name) # force cache load if needed
        if res is None or res == {}:
            res = dict.__contains__(self, name)
        return res

    def __getitem__(self, name):
        value = None
        had = False
        try:
            value = dict.__getitem__(self, name)
            had = True
        except KeyError:
            for cache in self._caches:
                value = cache.get(name)
                if value is not None:
                    break

        if value is None:
            value = self._default()

        if not had:
            dict.__setitem__(self, name, value)

        return value


    def __setitem__(self, name, value):

        for cache in self._caches:
            cache.save(name, value)
        dict.__setitem__(self, name, value)


    def update(self, *a, **kw):

        if a and len(a) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(a))
            other = dict(*a, **kw)
            for key in other:
                self.__setitem__(name, other[key])

        for key in kw:
            self.__setitem__(name, kw[key])


    def setdefault(self, name, value=None):

        if value is None:
            value = self._default()
            self.__setitem__(name, value)

        return value


    def keys(self):

        print 'doing keys'
        ret = []

        for cache in self._caches:
            ret.update(cache.cached())
        ret.update(dict.keys(self))
        print 'ret %s' % ret

        return ret


    def _validate_key(self, name):

        if dict._validate_key(self, name):
            return True

        for cache in self._caches:
            if cache.get(name):
                return True

        return False

    def close(self):
      for name in self.keys():
        for cache in self._caches:
            cache.save(name, self[name])
    
    def __del__(self):
      self.close()

# for debug
#    def __getattribute__(self, name):
#        import inspect
#        returned = object.__getattribute__(self, name)
#        if inspect.isfunction(returned) or inspect.ismethod(returned):
#            print 'called Cache.', returned.__name__
#        return returned
#
