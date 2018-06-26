class Bang(object):
    def __init__(self, _tripwire_keys=frozenset()):
        self._tripwire_keys = frozenset(_tripwire_keys)

    def _warn_on_touch(self, k=None):
        if self._tripwire_keys and k:
            if k not in self._tripwire_keys:
                return

        if k:
            print("*** USE OF DEPRECATED RETURN VALUE {0} ***".format(k))


class DeprecatedProxy(dict, Bang):
    def __init__(self, mapping=None, *args, **kwargs):
        dict.__init__(self, mapping, *args, **kwargs)

        tripwire_keys = frozenset(self.pop('_ansible_deprecated_returns').keys())

        Bang.__init__(self, _tripwire_keys=tripwire_keys)


    def get(self, k, default=None):
        self._warn_on_touch(k)
        return super(DeprecatedProxy, self).get(k, default)

    def __getitem__(self, k):
        self._warn_on_touch(k)
        return super(DeprecatedProxy, self).__getitem__(k)

