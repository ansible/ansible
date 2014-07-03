class BaseCacheModule(object):
    def get(self, key):
        raise NotImplementedError("Subclasses of {} must implement the '{}' method".format(self.__class__.__name__, self.__name__))

    def set(self, key, value):
        raise NotImplementedError("Subclasses of {} must implement the '{}' method".format(self.__class__.__name__, self.__name__))

    def keys(self):
        raise NotImplementedError("Subclasses of {} must implement the '{}' method".format(self.__class__.__name__, self.__name__))

    def contains(self, key):
        raise NotImplementedError("Subclasses of {} must implement the '{}' method".format(self.__class__.__name__, self.__name__))

    def delete(self, key):
        raise NotImplementedError("Subclasses of {} must implement the '{}' method".format(self.__class__.__name__, self.__name__))

    def flush(self):
        raise NotImplementedError("Subclasses of {} must implement the '{}' method".format(self.__class__.__name__, self.__name__))
