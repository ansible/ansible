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

from ansible.compat.tests import unittest, mock
from ansible.errors import AnsibleError
from ansible.plugins.cache import FactCache
from ansible.plugins.cache.base import BaseCacheModule
from ansible.plugins.cache.memory import CacheModule as MemoryCache

HAVE_MEMCACHED = True
try:
    import memcache
except ImportError:
    HAVE_MEMCACHED = False
else:
    # Use an else so that the only reason we skip this is for lack of
    # memcached, not errors importing the plugin
    from ansible.plugins.cache.memcached import CacheModule as MemcachedCache

HAVE_REDIS = True
try:
    import redis
except ImportError:
    HAVE_REDIS = False
else:
    from ansible.plugins.cache.redis import CacheModule as RedisCache


class TestFactCache(unittest.TestCase):

    def setUp(self):
        with mock.patch('ansible.constants.CACHE_PLUGIN', 'memory'):
            self.cache = FactCache()

    def test_copy(self):
        self.cache['avocado'] = 'fruit'
        self.cache['daisy'] = 'flower'
        a_copy = self.cache.copy()
        self.assertEqual(type(a_copy), dict)
        self.assertEqual(a_copy, dict(avocado='fruit', daisy='flower'))

    def test_plugin_load_failure(self):
        # See https://github.com/ansible/ansible/issues/18751
        # Note no fact_connection config set, so this will fail
        with mock.patch('ansible.constants.CACHE_PLUGIN', 'json'):
            self.assertRaisesRegexp(AnsibleError,
                                    "Unable to load the facts cache plugin.*json.*",
                                    FactCache)


class TestAbstractClass(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_subclass_error(self):
        class CacheModule1(BaseCacheModule):
            pass
        with self.assertRaises(TypeError):
            CacheModule1()  # pylint: disable=abstract-class-instantiated

        class CacheModule2(BaseCacheModule):
            def get(self, key):
                super(CacheModule2, self).get(key)

        with self.assertRaises(TypeError):
            CacheModule2()  # pylint: disable=abstract-class-instantiated

    def test_subclass_success(self):
        class CacheModule3(BaseCacheModule):
            def get(self, key):
                super(CacheModule3, self).get(key)

            def set(self, key, value):
                super(CacheModule3, self).set(key, value)

            def keys(self):
                super(CacheModule3, self).keys()

            def contains(self, key):
                super(CacheModule3, self).contains(key)

            def delete(self, key):
                super(CacheModule3, self).delete(key)

            def flush(self):
                super(CacheModule3, self).flush()

            def copy(self):
                super(CacheModule3, self).copy()

        self.assertIsInstance(CacheModule3(), CacheModule3)

    @unittest.skipUnless(HAVE_MEMCACHED, 'python-memcached module not installed')
    def test_memcached_cachemodule(self):
        self.assertIsInstance(MemcachedCache(), MemcachedCache)

    def test_memory_cachemodule(self):
        self.assertIsInstance(MemoryCache(), MemoryCache)

    @unittest.skipUnless(HAVE_REDIS, 'Redis python module not installed')
    def test_redis_cachemodule(self):
        self.assertIsInstance(RedisCache(), RedisCache)
