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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import cPickle as pickle
except ImportError:
    import pickle

from ansible.plugins.cache.base import BaseFileCacheModule

class CacheModule(BaseFileCacheModule):
    """
    A caching module backed by pickle files.
    """
    plugin_name = 'pickle'
    read_mode = 'rb'
    write_mode = 'wb'
    encoding = None

    def _load(self, f):
        return pickle.load(f)

    def _dump(self, value, f):
        pickle.dump(value, f)
