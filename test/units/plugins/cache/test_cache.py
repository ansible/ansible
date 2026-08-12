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


import errno
import os
import pathlib
import shutil
import tempfile


import unittest
from ansible.errors import AnsibleError
from ansible.plugins.cache import CachePluginAdjudicator
from ansible.plugins.cache.memory import CacheModule as MemoryCache
from ansible.plugins.loader import cache_loader

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
            self.cache.pop('foo')

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


class TestJsonFileCache(TestCachePluginAdjudicator):
    cache_prefix = ''

    def setUp(self):
        self.cache_dir = tempfile.mkdtemp(prefix='ansible-plugins-cache-')
        self.cache = self.get_cache(self.cache_prefix)
        self.cache['cache_key'] = {'key1': 'value1', 'key2': 'value2'}
        self.cache['cache_key_2'] = {'key': 'value'}

    def get_cache(self, prefix):
        return CachePluginAdjudicator(
            plugin_name='jsonfile', _uri=self.cache_dir,
            _prefix=prefix)

    def test_keys(self):
        # A cache without a prefix will consider all files in the cache
        # directory as valid cache entries.
        cache_writer = self.get_cache(self.cache_prefix)
        cache_writer["no_prefix"] = dict(a=1)
        cache_writer["special_test"] = dict(b=2)
        cache_writer.update_cache_if_changed()

        # The plugin does not know the CachePluginAdjudicator entries.
        assert sorted(self.cache._plugin.keys()) == [
            'no_prefix', 'special_test']

        assert 'no_prefix' in self.cache
        assert 'special_test' in self.cache
        assert 'test' not in self.cache
        assert self.cache['no_prefix'] == dict(a=1)
        assert self.cache['special_test'] == dict(b=2)

    def tearDown(self):
        shutil.rmtree(self.cache_dir)


class TestJsonFileCachePrefix(TestJsonFileCache):
    cache_prefix = 'special_'

    def test_keys(self):
        # For caches with a prefix only files that match the prefix are
        # considered. The prefix is removed from the key name.
        cache_writer = self.get_cache('')
        cache_writer["no_prefix"] = dict(a=1)
        cache_writer.update_cache_if_changed()

        cache_writer = self.get_cache(self.cache_prefix)
        cache_writer["test"] = dict(b=2)
        cache_writer.update_cache_if_changed()

        # The plugin does not know the CachePluginAdjudicator entries.
        assert sorted(self.cache._plugin.keys()) == ['test']

        assert 'no_prefix' not in self.cache
        assert 'special_test' not in self.cache
        assert 'test' in self.cache
        assert self.cache['test'] == dict(b=2)


class TestJsonFileCacheFailedWrite(unittest.TestCase):
    """A cache write that fails part way through must not destroy the entry already on disk."""

    def setUp(self):
        self.cache_dir = tempfile.mkdtemp(prefix='ansible-plugins-cache-')
        self.cache = cache_loader.get('jsonfile', _uri=self.cache_dir, _timeout=0, _prefix='ansible_facts')

    def tearDown(self):
        shutil.rmtree(self.cache_dir)

    def test_failed_dump_keeps_existing_entry(self):
        self.cache.set('host', {'ansible_os_family': 'RedHat'})
        assert self.cache.get('host') == {'ansible_os_family': 'RedHat'}

        def failing_dump(value, filepath):
            # `_dump` implementations are not atomic, so a failure can leave a truncated file behind.
            pathlib.Path(filepath).write_text('{"__payload__": "{\\"truncated')
            raise OSError(errno.ENOSPC, 'No space left on device')

        # bypass the schema-qualifying interposer to reach the file cache plugin itself
        self.cache.__wrapped__._dump = failing_dump
        self.cache.set('host', {'ansible_os_family': 'Debian'})

        # a later run must still be able to read the previously cached facts
        reader = cache_loader.get('jsonfile', _uri=self.cache_dir, _timeout=0, _prefix='ansible_facts')
        assert reader.get('host') == {'ansible_os_family': 'RedHat'}

    def test_failed_dump_leaves_no_temp_file(self):
        def failing_dump(value, filepath):
            raise OSError(errno.ENOSPC, 'No space left on device')

        self.cache.__wrapped__._dump = failing_dump
        self.cache.set('host', {'ansible_os_family': 'Debian'})

        assert os.listdir(self.cache_dir) == []


class TestCachePlugin(unittest.TestCase):
    def setUp(self):
        self.cache = cache_loader.get('memory')

    @pytest.mark.usefixtures('collection_loader')
    def test_plugin_load_failure(self):
        # See https://github.com/ansible/ansible/issues/18751
        # Note no fact_connection config set, so this will fail
        with pytest.raises(AnsibleError, match="Unable to load the cache plugin.*json.*"):
            cache_loader.get('json')

    def test_update(self):
        self.cache.set('cache_key', {'key2': 'updatedvalue'})
        assert self.cache.get('cache_key')['key2'] == 'updatedvalue'


def test_memory_cachemodule_with_loader():
    assert isinstance(cache_loader.get('memory'), MemoryCache)
