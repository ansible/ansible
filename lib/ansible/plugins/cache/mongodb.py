# (c) 2018, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
    cache: mongodb
    short_description: Use MongoDB for caching
    description:
        - This cache uses per host records saved in MongoDB.
    version_added: "2.5"
    requirements:
      - pymongo>=3
    options:
      _uri:
        description:
          - MongoDB Connection String URI
        required: False
        env:
          - name: ANSIBLE_CACHE_PLUGIN_CONNECTION
        ini:
          - key: fact_caching_connection
            section: defaults
      _prefix:
        description: User defined prefix to use when creating the DB entries
        env:
          - name: ANSIBLE_CACHE_PLUGIN_PREFIX
        ini:
          - key: fact_caching_prefix
            section: defaults
      _timeout:
        default: 86400
        description: Expiration timeout in seconds for the cache plugin data
        env:
          - name: ANSIBLE_CACHE_PLUGIN_TIMEOUT
        ini:
          - key: fact_caching_timeout
            section: defaults
        type: integer
'''

import datetime

from contextlib import contextmanager

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.cache import BaseCacheModule

try:
    import pymongo
except ImportError:
    raise AnsibleError("The 'pymongo' python module is required for the mongodb fact cache, 'pip install pymongo>=3.0'")


class CacheModule(BaseCacheModule):
    """
    A caching module backed by mongodb.
    """
    def __init__(self, *args, **kwargs):
        self._timeout = int(C.CACHE_PLUGIN_TIMEOUT)
        self._prefix = C.CACHE_PLUGIN_PREFIX
        self._cache = {}
        self._managed_indexes = False

    def _manage_indexes(self, collection):
        '''
        This function manages indexes on the mongo collection.
        We only do this once, at run time based on _managed_indexes,
        rather than per connection instantiation as that would be overkill
        '''
        _timeout = self._timeout
        if _timeout and _timeout > 0:
            try:
                collection.create_index(
                    'date',
                    name='ttl',
                    expireAfterSeconds=_timeout
                )
            except pymongo.errors.OperationFailure:
                # We make it here when the fact_caching_timeout was set to a different value between runs
                collection.drop_index('ttl')
                return self._manage_indexes(collection)
        else:
            collection.drop_index('ttl')

    @contextmanager
    def _collection(self):
        '''
        This is a context manager for opening and closing mongo connections as needed. This exists as to not create a global
        connection, due to pymongo not being fork safe (http://api.mongodb.com/python/current/faq.html#is-pymongo-fork-safe)
        '''
        mongo = pymongo.MongoClient(C.CACHE_PLUGIN_CONNECTION)
        try:
            db = mongo.get_default_database()
        except pymongo.errors.ConfigurationError:
            # We'll fall back to using ``ansible`` as the database if one was not provided
            # in the MongoDB Connection String URI
            db = mongo['ansible']

        # The collection is hard coded as ``cache``, there are no configuration options for this
        collection = db['cache']
        if not self._managed_indexes:
            # Only manage the indexes once per run, not per connection
            self._manage_indexes(collection)
            self._managed_indexes = True

        yield collection

        mongo.close()

    def _make_key(self, key):
        return '%s%s' % (self._prefix, key)

    def get(self, key):
        if key not in self._cache:
            with self._collection() as collection:
                value = collection.find_one({'_id': self._make_key(key)})
            self._cache[key] = value['data']

        return self._cache.get(key)

    def set(self, key, value):
        self._cache[key] = value
        with self._collection() as collection:
            collection.update_one(
                {'_id': self._make_key(key)},
                {
                    '$set': {
                        '_id': self._make_key(key),
                        'data': value,
                        'date': datetime.datetime.utcnow()
                    }
                },
                upsert=True
            )

    def keys(self):
        with self._collection() as collection:
            return [doc['_id'] for doc in collection.find({}, {'_id': True})]

    def contains(self, key):
        with self._collection() as collection:
            return bool(collection.count({'_id': self._make_key(key)}))

    def delete(self, key):
        del self._cache[key]
        with self._collection() as collection:
            collection.delete_one({'_id': self._make_key(key)})

    def flush(self):
        with self._collection() as collection:
            collection.delete_many({})

    def copy(self):
        with self._collection() as collection:
            return dict((d['_id'], d['data']) for d in collection.find({}))

    def __getstate__(self):
        return dict()

    def __setstate__(self, data):
        self.__init__()
