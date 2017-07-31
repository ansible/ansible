# (c) 2017, Brian Coca
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
'''
DOCUMENTATION:
    cache: yaml
    short_description: Pickle formatted files.
    description:
        - This cache uses Python's pickle serialization format, in per host files, saved to the filesystem.
    version_added: "2.3"
    author: Brian Coca (@bcoca)
'''

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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
