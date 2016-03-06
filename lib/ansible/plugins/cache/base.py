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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import ABCMeta, abstractmethod

from ansible.compat.six import with_metaclass

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class BaseCacheModule(with_metaclass(ABCMeta, object)):

    # Backwards compat only.  Just import the global display instead
    _display = display

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass

    @abstractmethod
    def keys(self):
        pass

    @abstractmethod
    def contains(self, key):
        pass

    @abstractmethod
    def delete(self, key):
        pass

    @abstractmethod
    def flush(self):
        pass

    @abstractmethod
    def copy(self):
        pass

