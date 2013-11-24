import os
import time

try:
    import json
except ImportError:
    import simplejson as json


class CacheModule(object):


    def __init__(self, *a, **kw):

        self._expires = kw.get('expires', 86400)
        self._cache_dir = os.path.expanduser(kw.get('cache_dir', "~/.cache/ansible"))

        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir)

        if not os.path.isdir(self._cache_dir):
            raise "Not a useable direcory: %s" % self._cache_dir

    def save(self, name, val):

        try:
            f = open('/'.join([self._cache_dir, str(name)]) ,'w')
        except OSError as e:
           raise "Unable to write cache: %s" % str(e)
        f.write(json.dumps(val))
        f.close()
        print 'FILE save: %s = %s\n' % (name, val)


    def get(self, name):

        ret = None
        path = '/'.join([self._cache_dir, str(name)])

        if os.path.exists(path):
            if int(time.time() - os.stat(path).st_mtime) < self._expires:
                try:
                    f = open(path,'r')
                except OSError as e:
                    raise "Unable to read cache: %s" % str(e)
                ret = json.loads(f.read())
                f.close()
        return ret


    def cached(self):

        ret = []

        for cfile in os.listdir(self._cache_dir):
            ret.append(cfile)
        return ret


    def __getattribute__(self, name):
        import inspect
        returned = object.__getattribute__(self, name)
        if inspect.isfunction(returned) or inspect.ismethod(returned):
            print 'called File.', returned.__name__
        return returned

