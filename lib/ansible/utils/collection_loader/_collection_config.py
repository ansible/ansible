# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# CAUTION: There are two implementations of the collection loader.
#          They must be kept functionally identical, although their implementations may differ.
#
# 1) The controller implementation resides in the "lib/ansible/utils/collection_loader/" directory.
#    It must function on all Python versions supported on the controller.
# 2) The ansible-test implementation resides in the "test/lib/ansible_test/_util/target/legacy_collection_loader/" directory.
#    It must function on all Python versions supported on managed hosts which are not supported by the controller.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.six import with_metaclass


class _EventSource:
    def __init__(self):
        self._handlers = set()

    def __iadd__(self, handler):
        if not callable(handler):
            raise ValueError('handler must be callable')
        self._handlers.add(handler)
        return self

    def __isub__(self, handler):
        try:
            self._handlers.remove(handler)
        except KeyError:
            pass

        return self

    def _on_exception(self, handler, exc, *args, **kwargs):
        # if we return True, we want the caller to re-raise
        return True

    def fire(self, *args, **kwargs):
        for h in self._handlers:
            try:
                h(*args, **kwargs)
            except Exception as ex:
                if self._on_exception(h, ex, *args, **kwargs):
                    raise


class _AnsibleCollectionConfig(type):
    def __init__(cls, meta, name, bases):
        cls._collection_finder = None
        cls._default_collection = None
        cls._on_collection_load = _EventSource()

    @property
    def collection_finder(cls):
        return cls._collection_finder

    @collection_finder.setter
    def collection_finder(cls, value):
        if cls._collection_finder:
            raise ValueError('an AnsibleCollectionFinder has already been configured')

        cls._collection_finder = value

    @property
    def collection_paths(cls):
        cls._require_finder()
        return [to_text(p) for p in cls._collection_finder._n_collection_paths]

    @property
    def default_collection(cls):
        return cls._default_collection

    @default_collection.setter
    def default_collection(cls, value):

        cls._default_collection = value

    @property
    def on_collection_load(cls):
        return cls._on_collection_load

    @on_collection_load.setter
    def on_collection_load(cls, value):
        if value is not cls._on_collection_load:
            raise ValueError('on_collection_load is not directly settable (use +=)')

    @property
    def playbook_paths(cls):
        cls._require_finder()
        return [to_text(p) for p in cls._collection_finder._n_playbook_paths]

    @playbook_paths.setter
    def playbook_paths(cls, value):
        cls._require_finder()
        cls._collection_finder.set_playbook_paths(value)

    def _require_finder(cls):
        if not cls._collection_finder:
            raise NotImplementedError('an AnsibleCollectionFinder has not been installed in this process')


# concrete class of our metaclass type that defines the class properties we want
class AnsibleCollectionConfig(with_metaclass(_AnsibleCollectionConfig)):
    pass
