# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: exercise_cache
    short_description: run tests against the specified cache plugin
    description:
      - This plugin doesn't modify inventory.
      - Load a cache plugin and test the inventory cache interface is dict-like.
      - Most inventory cache write methods only apply to the in-memory cache.
      - The 'flush' and 'set_cache' methods should be used to apply changes to the backing cache plugin.
      - The inventory cache read methods prefer the in-memory cache, and fall back to reading from the cache plugin.
    extends_documentation_fragment:
      - inventory_cache
    options:
      plugin:
        required: true
        description: name of the plugin (exercise_cache)
    cache_timeout:
        ini: []
        env: []
        cli: []
        default: 0  # never expire
'''

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, get_cache_plugin
from ansible.utils.display import Display

from copy import deepcopy
from time import sleep


display = Display()


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'exercise_cache'

    test_cache_methods = [
        'test_plugin_name',
        'test_update_cache_if_changed',
        'test_set_cache',
        'test_load_whole_cache',
        'test_iter',
        'test_len',
        'test_get_missing_key',
        'test_get_expired_key',
        'test_get',
        'test_items',
        'test_keys',
        'test_values',
        'test_pop',
        'test_del',
        'test_set',
        'test_update',
        'test_flush',
    ]

    def verify_file(self, path):
        if not path.endswith(('exercise_cache.yml', 'exercise_cache.yaml',)):
            return False
        return super(InventoryModule, self).verify_file(path)

    def parse(self, inventory, loader, path, cache=None):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        try:
            self.exercise_test_cache()
        except AnsibleError:
            raise
        except Exception as e:
            raise AnsibleError("Failed to run cache tests: {0}".format(e)) from e

    def exercise_test_cache(self):
        cache_name = self.get_option('cache_plugin')
        cache_options = deepcopy(self.cache._plugin._options)
        test_cache = get_cache_plugin(cache_name, **cache_options)

        failed = []
        for test_name in self.test_cache_methods:
            test = getattr(self, test_name)
            try:
                test(test_cache)
            except AssertionError:
                failed.append(test_name)
            finally:
                test_cache.flush()
                test_cache.update_cache_if_changed()

        if failed:
            raise AnsibleError(f"Cache tests failed: {', '.join(failed)}")

    def test_equal(self, a, b):
        try:
            assert a == b
        except AssertionError:
            display.warning(f"Assertion {a} == {b} failed")
            raise

    def test_plugin_name(self, cache):
        self.test_equal(self.get_option('cache_plugin'), cache._plugin_name)

    def test_update_cache_if_changed(self, cache):
        cache._retrieved = {}
        cache._cache = {'foo': 'bar'}

        cache.update_cache_if_changed()

        self.test_equal(cache._retrieved, {'foo': 'bar'})
        self.test_equal(cache._cache, {'foo': 'bar'})

    def test_set_cache(self, cache):
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        cache._cache = {cache_key1: cache1, cache_key2: cache2}

        cache.set_cache()

        self.test_equal(cache._plugin.contains(cache_key1), True)
        self.test_equal(cache._plugin.get(cache_key1), cache1)
        self.test_equal(cache._plugin.contains(cache_key2), True)
        self.test_equal(cache._plugin.get(cache_key2), cache2)

    def test_load_whole_cache(self, cache):
        cache_data = {
            'key1': {'hosts': {'h1': {'foo': 'bar'}}},
            'key2': {'hosts': {'h2': {}}},
        }
        cache._cache = cache_data
        cache.set_cache()
        cache._cache = {}

        cache.load_whole_cache()

        self.test_equal(cache._cache, cache_data)

    def test_iter(self, cache):
        cache_data = {
            'key1': {'hosts': {'h1': {'foo': 'bar'}}},
            'key2': {'hosts': {'h2': {}}},
        }
        cache._cache = cache_data

        cache_keys = sorted(list(cache))
        self.test_equal(cache_keys, ['key1', 'key2'])

    def test_len(self, cache):
        cache_data = {
            'key1': {'hosts': {'h1': {'foo': 'bar'}}},
            'key2': {'hosts': {'h2': {}}},
        }
        cache._cache = cache_data

        self.test_equal(len(cache), 2)

    def test_get_missing_key(self, cache):
        # cache should behave like a dictionary
        # a missing key with __getitem__ should raise a KeyError
        try:
            cache['keyerror']
        except KeyError:
            pass
        else:
            assert False

        # get should return the default instead
        self.test_equal(cache.get('missing'), None)
        self.test_equal(cache.get('missing', 'default'), 'default')

    def _setup_expired(self, cache):
        cache._cache = {'expired': True}
        cache.set_cache()

        # empty the in-memory info to test loading the key
        # keys that expire mid-use do not cause errors
        cache._cache = {}
        cache._retrieved = {}
        cache._plugin._cache = {}

        cache._plugin.set_option('timeout', 1)
        cache._plugin._timeout = 1
        sleep(2)

    def _cleanup_expired(self, cache):
        # Set cache timeout back to never
        cache._plugin.set_option('timeout', 0)
        cache._plugin._timeout = 0

    def test_get_expired_key(self, cache):
        if not hasattr(cache._plugin, '_timeout'):
            # DB-backed caches do not have a standard timeout interface
            return

        self._setup_expired(cache)
        try:
            cache['key1']
        except KeyError:
            pass
        else:
            assert False
        finally:
            self._cleanup_expired(cache)

        self._setup_expired(cache)
        try:
            self.test_equal(cache.get('key1'), None)
            self.test_equal(cache.get('key1', 'default'), 'default')
        finally:
            self._cleanup_expired(cache)

    def test_get(self, cache):
        # test cache behaves like a dictionary

        # set the cache to test getting a key that exists
        k1 = {'hosts': {'h1': {'foo': 'bar'}}}
        k2 = {'hosts': {'h2': {}}}
        cache._cache = {'key1': k1, 'key2': k2}
        cache.set_cache()

        self.test_equal(cache['key1'], k1)
        self.test_equal(cache.get('key1'), k1)

        # empty the in-memory info to test loading the key from the plugin
        cache._cache = {}
        cache._retrieved = {}
        cache._plugin._cache = {}

        self.test_equal(cache['key1'], k1)
        self.test_equal(cache.get('key1'), k1)

    def test_items(self, cache):
        self.test_equal(cache.items(), {}.items())

        test_items = {'hosts': {'host1': {'foo': 'bar'}}}
        cache._cache = test_items
        self.test_equal(cache.items(), test_items.items())

    def test_keys(self, cache):
        self.test_equal(cache.keys(), {}.keys())

        test_items = {'hosts': {'host1': {'foo': 'bar'}}}
        cache._cache = test_items
        self.test_equal(cache.keys(), test_items.keys())

    def test_values(self, cache):
        self.test_equal(list(cache.values()), list({}.values()))

        test_items = {'hosts': {'host1': {'foo': 'bar'}}}
        cache._cache = test_items
        self.test_equal(list(cache.values()), list(test_items.values()))

    def test_pop(self, cache):
        try:
            cache.pop('missing')
        except KeyError:
            pass
        else:
            assert False

        self.test_equal(cache.pop('missing', 'default'), 'default')

        cache._cache = {'cache_key': 'cache'}
        self.test_equal(cache.pop('cache_key'), 'cache')

        # test backing plugin cache isn't modified
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        cache._cache = {cache_key1: cache1, cache_key2: cache2}
        cache.set_cache()

        self.test_equal(cache.pop('key1'), cache1)
        self.test_equal(cache._cache, {cache_key2: cache2})
        self.test_equal(cache._plugin._cache, {cache_key1: cache1, cache_key2: cache2})

    def test_del(self, cache):
        try:
            del cache['missing']
        except KeyError:
            pass
        else:
            assert False

        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        cache._cache = {cache_key1: cache1, cache_key2: cache2}
        cache.set_cache()

        del cache['key1']

        self.test_equal(cache._cache, {cache_key2: cache2})
        self.test_equal(cache._plugin._cache, {cache_key1: cache1, cache_key2: cache2})

    def test_set(self, cache):
        cache_key = 'key1'
        hosts = {'hosts': {'h1': {'foo': 'bar'}}}
        cache[cache_key] = hosts

        self.test_equal(cache._cache, {cache_key: hosts})
        self.test_equal(cache._plugin._cache, {})

    def test_update(self, cache):
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        cache._cache = {cache_key1: cache1}
        cache.update({cache_key2: cache2})
        self.test_equal(cache._cache, {cache_key1: cache1, cache_key2: cache2})

    def test_flush(self, cache):
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        cache._cache = {cache_key1: cache1, cache_key2: cache2}
        cache.set_cache()

        # Unlike the dict write methods, cache.flush() flushes the backing plugin
        cache.flush()

        self.test_equal(cache._cache, {})
        self.test_equal(cache._plugin._cache, {})
