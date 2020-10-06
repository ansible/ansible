# (c) 2014, Brian Coca, Josh Drake, et al
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: memory
    short_description: RAM backed, non persistent
    description:
        - RAM backed cache that is not persistent.
        - This is the default used if no other plugin is specified.
        - There are no options to configure.
    version_added: historical
    author: core team (@ansible-core)
'''

from ansible.plugins.cache import BaseCacheModule


class CacheModule(BaseCacheModule):

    def __init__(self, *args, **kwargs):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value):
        self._cache[key] = value

    def keys(self):
        return self._cache.keys()

    def contains(self, key):
        return key in self._cache

    def delete(self, key):
        del self._cache[key]

    def flush(self):
        self._cache = {}

    def copy(self):
        return self._cache.copy()

    def __getstate__(self):
        return self.copy()

    def __setstate__(self, data):
        self._cache = data
