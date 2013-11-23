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


    def save(self, name, val):

        f = open('/'.join([self._cache_dir, str(name)]) ,'w')
        f.write(json.dumps(val))
        f.close()
        print 'FILE save: %s = %s\n' % (name, val)


    def get(self, name):

        ret = None
        path = '/'.join([self._cache_dir, str(name)])

        if os.path.exists(path):
            if int(time.time() - os.stat(path).st_mtime) < self._expires:
                f = open(path,'r')
                ret = json.loads(f.read())
                f.close()
        return ret
