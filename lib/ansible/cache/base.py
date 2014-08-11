import exceptions

class BaseCacheModule(object):

    def get(self, key):
        raise exceptions.NotImplementedError

    def set(self, key, value):
        raise exceptions.NotImplementedError

    def keys(self):
        raise exceptions.NotImplementedError

    def contains(self, key):
        raise exceptions.NotImplementedError

    def delete(self, key):
        raise exceptions.NotImplementedError

    def flush(self):
        raise exceptions.NotImplementedError
