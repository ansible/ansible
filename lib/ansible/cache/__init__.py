# (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible import utils
from ansible import constants as C
from ansible import errors

class FactCache(dict):

    def __init__(self, *args, **kwargs):

        self._plugin = utils.plugins.cache_loader.get(C.CACHE_PLUGIN)
        if self._plugin is None:
            return

    def __getitem__(self, key, default={}):
        return self._plugin.get(key, default)

    def __setitem__(self, key, val):
        self._plugin.set(key, value)

    def __delitem__(self, key):
        self._plugin.delete(key)

    def __contains__(self, key):
        return self._plugin.contains(key)

    def keys(self):
        return self._plugin.keys()

    def __repr__(self):
        return '%s' % (type(self))

    
