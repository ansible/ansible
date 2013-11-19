import os

try:
    import json
except ImportError:
    import simplejson as json


class CacheModule(dict):

    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        self.cache_dir = kw.get('cache_dir', '$HOME/.cache/ansible')
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def __getitem__(self, name):
        return _deserialize(name)

    def __setitem__(self, name, val):
        return _serialize(name, val)

    def update(self, *a, **kw):
        if a and len(a) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(a))
            other = dict(*a, **kw)
            for key in other:
                _serialize(key, other[key])
        for key in kw:
                _serialize(key, kw[key])

    def _serialize(self, name, val):
        f = open(self.cache_dir + name ,'w')
        f.write(json.dumps(val))
        f.close()

    def _deserialize(self, name):
        f = open(self.cache_dir + name ,'r')
        ret = json.loads(f.read())
        f.close()
        return ret
