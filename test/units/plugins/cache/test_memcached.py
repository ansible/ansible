# (c) 2012-2015, Michael DeHaan <michael.dehaan@gmail.com>
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

import pytest

pytest.importorskip('memcache')

from ansible.plugins.loader import cache_loader
from ansible.plugins.cache.memcached import CacheModule as MemcachedCache


def test_memcached_cachemodule():
    assert isinstance(MemcachedCache(), MemcachedCache)


def test_memcached_cachemodule_with_loader():
    assert isinstance(cache_loader.get('memcached'), MemcachedCache)
