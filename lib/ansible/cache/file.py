import os

try:
    import json
except ImportError:
    import simplejson as json


class CacheModule(object):

    def __init__(self, *a, **kw):
        self.cache_dir = os.path.expanduser(kw.get('cache_dir', "~/.cache/ansible"))
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def save(self, name, val):
        f = open('/'.join([self.cache_dir, name]) ,'w')
        f.write(json.dumps(val))
        f.close()

    def get(self, name):
        ret = None
        #TODO: stat file, check mtime against expires
        path = '/'.join([self.cache_dir, str(name)])
        if os.path.exists(path):
            f = open(path,'r')
            ret = json.loads(f.read())
            f.close()
        return ret
