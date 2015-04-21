# (c) 2014, Brian Coca, Josh Drake, et al
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

    def copy(self):
        raise exceptions.NotImplementedError
