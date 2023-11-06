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

from __future__ import annotations

import os
import shutil
import tempfile

from unittest import mock

import unittest
from ansible.errors import AnsibleError
from ansible.plugins.cache import CachePluginAdjudicator
from ansible.plugins.cache.memory import CacheModule as MemoryCache
from ansible.plugins.loader import cache_loader, init_plugin_loader
from ansible.vars.fact_cache import FactCache

import pytest


class TestCachePluginAdjudicator(unittest.TestCase):
    def setUp(self):
        # memory plugin cache
        self.cache = CachePluginAdjudicator()
        self.cache['cache_key'] = {'key1': 'value1', 'key2': 'value2'}
        self.cache['cache_key_2'] = {'key': 'value'}

    def test___setitem__(self):
        self.cache['new_cache_key'] = {'new_key1': ['new_value1', 'new_value2']}
        assert self.cache['new_cache_key'] == {'new_key1': ['new_value1', 'new_value2']}

    def test_inner___setitem__(self):
        self.cache['new_cache_key'] = {'new_key1': ['new_value1', 'new_value2']}
        self.cache['new_cache_key']['new_key1'][0] = 'updated_value1'
        assert self.cache['new_cache_key'] == {'new_key1': ['updated_value1', 'new_value2']}

    def test___contains__(self):
        assert 'cache_key' in self.cache
        assert 'not_cache_key' not in self.cache

    def test_get(self):
        assert self.cache.get('cache_key') == {'key1': 'value1', 'key2': 'value2'}

    def test_get_with_default(self):
        assert self.cache.get('foo', 'bar') == 'bar'

    def test_get_without_default(self):
        assert self.cache.get('foo') is None

    def test___getitem__(self):
        with pytest.raises(KeyError):
            self.cache['foo']  # pylint: disable=pointless-statement

    def test_pop_with_default(self):
        assert self.cache.pop('foo', 'bar') == 'bar'

    def test_pop_without_default(self):
        with pytest.raises(KeyError):
            assert self.cache.pop('foo')

    def test_pop(self):
        v = self.cache.pop('cache_key_2')
        assert v == {'key': 'value'}
        assert 'cache_key_2' not in self.cache

    def test_update(self):
        self.cache.update({'cache_key': {'key2': 'updatedvalue'}})
        assert self.cache['cache_key']['key2'] == 'updatedvalue'

    def test_update_cache_if_changed(self):
        # Changes are stored in the CachePluginAdjudicator and will be
        # persisted to the plugin when calling update_cache_if_changed()
        # The exception is flush which flushes the plugin immediately.
        assert len(self.cache.keys()) == 2
        assert len(self.cache._plugin.keys()) == 0
        self.cache.update_cache_if_changed()
        assert len(self.cache._plugin.keys()) == 2

    def test_flush(self):
        # Fake that the cache already has some data in it but the adjudicator
        # hasn't loaded it in.
        self.cache._plugin.set('monkey', 'animal')
        self.cache._plugin.set('wolf', 'animal')
        self.cache._plugin.set('another wolf', 'another animal')

        # The adjudicator does't know about the new entries
        assert len(self.cache.keys()) == 2
        # But the cache itself does
        assert len(self.cache._plugin.keys()) == 3

        # If we call flush, both the adjudicator and the cache should flush
        self.cache.flush()
        assert len(self.cache.keys()) == 0
        assert len(self.cache._plugin.keys()) == 0


class TestJsonFileCache(TestCachePluginAdjudicator):
    cache_prefix = ''

    def setUp(self):
        self.cache_dir = tempfile.mkdtemp(prefix='ansible-plugins-cache-')
        self.cache = CachePluginAdjudicator(
            plugin_name='jsonfile', _uri=self.cache_dir,
            _prefix=self.cache_prefix)
        self.cache['cache_key'] = {'key1': 'value1', 'key2': 'value2'}
        self.cache['cache_key_2'] = {'key': 'value'}

    def test_keys(self):
        # A cache without a prefix will consider all files in the cache
        # directory as valid cache entries.
        self.cache._plugin._dump(
            'no prefix', os.path.join(self.cache_dir, 'no_prefix'))
        self.cache._plugin._dump(
            'special cache', os.path.join(self.cache_dir, 'special_test'))

        # The plugin does not know the CachePluginAdjudicator entries.
        assert sorted(self.cache._plugin.keys()) == [
            'no_prefix', 'special_test']

        assert 'no_prefix' in self.cache
        assert 'special_test' in self.cache
        assert 'test' not in self.cache
        assert self.cache['no_prefix'] == 'no prefix'
        assert self.cache['special_test'] == 'special cache'

    def tearDown(self):
        shutil.rmtree(self.cache_dir)


class TestJsonFileCachePrefix(TestJsonFileCache):
    cache_prefix = 'special_'

    def test_keys(self):
        # For caches with a prefix only files that match the prefix are
        # considered. The prefix is removed from the key name.
        self.cache._plugin._dump(
            'no prefix', os.path.join(self.cache_dir, 'no_prefix'))
        self.cache._plugin._dump(
            'special cache', os.path.join(self.cache_dir, 'special_test'))

        # The plugin does not know the CachePluginAdjudicator entries.
        assert sorted(self.cache._plugin.keys()) == ['test']

        assert 'no_prefix' not in self.cache
        assert 'special_test' not in self.cache
        assert 'test' in self.cache
        assert self.cache['test'] == 'special cache'


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

    def test_flush(self):
        self.cache['motorcycle'] = 'vehicle'
        self.cache['sock'] = 'clothing'
        self.cache.flush()
        assert len(self.cache.keys()) == 0

    def test_plugin_load_failure(self):
        init_plugin_loader()
        # See https://github.com/ansible/ansible/issues/18751
        # Note no fact_connection config set, so this will fail
        with mock.patch('ansible.constants.CACHE_PLUGIN', 'json'):
            self.assertRaisesRegex(AnsibleError,
                                   "Unable to load the facts cache plugin.*json.*",
                                   FactCache)

    def test_update(self):
        self.cache.update({'cache_key': {'key2': 'updatedvalue'}})
        assert self.cache['cache_key']['key2'] == 'updatedvalue'


def test_memory_cachemodule_with_loader():
    assert isinstance(cache_loader.get('memory'), MemoryCache)
