# (c) 2017, Brian Coca
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    cache: pickle
    short_description: Pickle formatted files.
    description:
        - This cache uses Python's pickle serialization format, in per host files, saved to the filesystem.
    version_added: "2.3"
    author: Brian Coca (@bcoca)
    options:
      _uri:
        required: True
        description:
          - Path in which the cache plugin will save the files
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the files
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
        ini:
          - key: fact_caching_prefix
            section: defaults
      _timeout:
        default: 86400
        description: Expiration timeout for the cache plugin data
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
'''

try:
    import cPickle as pickle
except ImportError:
    import pickle

from ansible.module_utils.six import PY3
from ansible.plugins.cache import BaseFileCacheModule


class CacheModule(BaseFileCacheModule):
    """
    A caching module backed by pickle files.
    """

    def _load(self, filepath):
        # Pickle is a binary format
        with open(filepath, 'rb') as f:
            if PY3:
                return pickle.load(f, encoding='bytes')
            else:
                return pickle.load(f)

    def _dump(self, value, filepath):
        with open(filepath, 'wb') as f:
            # Use pickle protocol 2 which is compatible with Python 2.3+.
            pickle.dump(value, f, protocol=2)
