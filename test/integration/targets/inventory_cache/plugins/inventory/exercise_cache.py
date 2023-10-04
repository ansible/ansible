# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

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
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable
from ansible.utils.display import Display

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
        'test_initial_get',
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
        failed = []
        for test_name in self.test_cache_methods:
            try:
                getattr(self, test_name)()
            except AssertionError:
                failed.append(test_name)
            finally:
                self.cache.flush()
                self.cache.update_cache_if_changed()

        if failed:
            raise AnsibleError(f"Cache tests failed: {', '.join(failed)}")

    def test_equal(self, a, b):
        try:
            assert a == b
        except AssertionError:
            display.warning(f"Assertion {a} == {b} failed")
            raise

    def test_plugin_name(self):
        self.test_equal(self.cache._plugin_name, self.get_option('cache_plugin'))

    def test_update_cache_if_changed(self):
        self.cache._retrieved = {}
        self.cache._cache = {'foo': 'bar'}

        self.cache.update_cache_if_changed()

        self.test_equal(self.cache._retrieved, {'foo': 'bar'})
        self.test_equal(self.cache._cache, {'foo': 'bar'})

    def test_set_cache(self):
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        self.cache._cache = {cache_key1: cache1, cache_key2: cache2}
        self.cache.set_cache()

        self.test_equal(self.cache._plugin.contains(cache_key1), True)
        self.test_equal(self.cache._plugin.get(cache_key1), cache1)
        self.test_equal(self.cache._plugin.contains(cache_key2), True)
        self.test_equal(self.cache._plugin.get(cache_key2), cache2)

    def test_load_whole_cache(self):
        cache_data = {
            'key1': {'hosts': {'h1': {'foo': 'bar'}}},
            'key2': {'hosts': {'h2': {}}},
        }
        self.cache._cache = cache_data
        self.cache.set_cache()
        self.cache._cache = {}

        self.cache.load_whole_cache()
        self.test_equal(self.cache._cache, cache_data)

    def test_iter(self):
        cache_data = {
            'key1': {'hosts': {'h1': {'foo': 'bar'}}},
            'key2': {'hosts': {'h2': {}}},
        }
        self.cache._cache = cache_data
        self.test_equal(sorted(list(self.cache)), ['key1', 'key2'])

    def test_len(self):
        cache_data = {
            'key1': {'hosts': {'h1': {'foo': 'bar'}}},
            'key2': {'hosts': {'h2': {}}},
        }
        self.cache._cache = cache_data
        self.test_equal(len(self.cache), 2)

    def test_get_missing_key(self):
        # cache should behave like a dictionary
        # a missing key with __getitem__ should raise a KeyError
        try:
            self.cache['keyerror']
        except KeyError:
            pass
        else:
            assert False

        # get should return the default instead
        self.test_equal(self.cache.get('missing'), None)
        self.test_equal(self.cache.get('missing', 'default'), 'default')

    def _setup_expired(self):
        self.cache._cache = {'expired': True}
        self.cache.set_cache()

        # empty the in-memory info to test loading the key
        # keys that expire mid-use do not cause errors
        self.cache._cache = {}
        self.cache._retrieved = {}
        self.cache._plugin._cache = {}

        self.cache._plugin.set_option('timeout', 1)
        self.cache._plugin._timeout = 1
        sleep(2)

    def _cleanup_expired(self):
        # Set cache timeout back to never
        self.cache._plugin.set_option('timeout', 0)
        self.cache._plugin._timeout = 0

    def test_get_expired_key(self):
        if not hasattr(self.cache._plugin, '_timeout'):
            # DB-backed caches do not have a standard timeout interface
            return

        self._setup_expired()
        try:
            self.cache['expired']
        except KeyError:
            pass
        else:
            assert False
        finally:
            self._cleanup_expired()

        self._setup_expired()
        try:
            self.test_equal(self.cache.get('expired'), None)
            self.test_equal(self.cache.get('expired', 'default'), 'default')
        finally:
            self._cleanup_expired()

    def test_initial_get(self):
        # test cache behaves like a dictionary

        # set the cache to test getting a key that exists
        k1 = {'hosts': {'h1': {'foo': 'bar'}}}
        k2 = {'hosts': {'h2': {}}}
        self.cache._cache = {'key1': k1, 'key2': k2}
        self.cache.set_cache()

        # empty the in-memory info to test loading the key from the plugin
        self.cache._cache = {}
        self.cache._retrieved = {}
        self.cache._plugin._cache = {}

        self.test_equal(self.cache['key1'], k1)

        # empty the in-memory info to test loading the key from the plugin
        self.cache._cache = {}
        self.cache._retrieved = {}
        self.cache._plugin._cache = {}

        self.test_equal(self.cache.get('key1'), k1)

    def test_get(self):
        # test cache behaves like a dictionary

        # set the cache to test getting a key that exists
        k1 = {'hosts': {'h1': {'foo': 'bar'}}}
        k2 = {'hosts': {'h2': {}}}
        self.cache._cache = {'key1': k1, 'key2': k2}
        self.cache.set_cache()

        self.test_equal(self.cache['key1'], k1)
        self.test_equal(self.cache.get('key1'), k1)

    def test_items(self):
        self.test_equal(self.cache.items(), {}.items())

        test_items = {'hosts': {'host1': {'foo': 'bar'}}}
        self.cache._cache = test_items
        self.test_equal(self.cache.items(), test_items.items())

    def test_keys(self):
        self.test_equal(self.cache.keys(), {}.keys())

        test_items = {'hosts': {'host1': {'foo': 'bar'}}}
        self.cache._cache = test_items
        self.test_equal(self.cache.keys(), test_items.keys())

    def test_values(self):
        self.test_equal(list(self.cache.values()), list({}.values()))

        test_items = {'hosts': {'host1': {'foo': 'bar'}}}
        self.cache._cache = test_items
        self.test_equal(list(self.cache.values()), list(test_items.values()))

    def test_pop(self):
        try:
            self.cache.pop('missing')
        except KeyError:
            pass
        else:
            assert False

        self.test_equal(self.cache.pop('missing', 'default'), 'default')

        self.cache._cache = {'cache_key': 'cache'}
        self.test_equal(self.cache.pop('cache_key'), 'cache')

        # test backing plugin cache isn't modified
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        self.cache._cache = {cache_key1: cache1, cache_key2: cache2}
        self.cache.set_cache()

        self.test_equal(self.cache.pop('key1'), cache1)
        self.test_equal(self.cache._cache, {cache_key2: cache2})
        self.test_equal(self.cache._plugin._cache, {cache_key1: cache1, cache_key2: cache2})

    def test_del(self):
        try:
            del self.cache['missing']
        except KeyError:
            pass
        else:
            assert False

        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        self.cache._cache = {cache_key1: cache1, cache_key2: cache2}
        self.cache.set_cache()

        del self.cache['key1']

        self.test_equal(self.cache._cache, {cache_key2: cache2})
        self.test_equal(self.cache._plugin._cache, {cache_key1: cache1, cache_key2: cache2})

    def test_set(self):
        cache_key = 'key1'
        hosts = {'hosts': {'h1': {'foo': 'bar'}}}
        self.cache[cache_key] = hosts

        self.test_equal(self.cache._cache, {cache_key: hosts})
        self.test_equal(self.cache._plugin._cache, {})

    def test_update(self):
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        self.cache._cache = {cache_key1: cache1}
        self.cache.update({cache_key2: cache2})
        self.test_equal(self.cache._cache, {cache_key1: cache1, cache_key2: cache2})

    def test_flush(self):
        cache_key1 = 'key1'
        cache1 = {'hosts': {'h1': {'foo': 'bar'}}}
        cache_key2 = 'key2'
        cache2 = {'hosts': {'h2': {}}}

        self.cache._cache = {cache_key1: cache1, cache_key2: cache2}
        self.cache.set_cache()

        # Unlike the dict write methods, cache.flush() flushes the backing plugin
        self.cache.flush()

        self.test_equal(self.cache._cache, {})
        self.test_equal(self.cache._plugin._cache, {})
