# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# (m) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (m) 2017, Juan Manuel Parrilla <jparrill@redhat.com>
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
'''
DOCUMENTATION:
    author:
        - Jan-Piet Mens (@jpmens)
    lookup: redis_kv
    version_added: "1.9"
    short_description: get info from redis key-value
    description:
        - Retrieves data from an Redis server
    options:
        _key:
            description:
                - The list of keys to lookup on the Redis server
            type: list, string
            element_type: string
            required: True
        _url:
            description:
                - Redis server to connect to
            default: '127.0.0.1'
            env_vars:
                - name: ANSIBLE_REDIS_URL
        _port:
            description:
                - Destination port of Redis server
            default: '6379'
            env_vars:
                - name: ANSIBLE_REDIS_PORT
EXAMPLES:
    All this examples will need a running Redis server and those keys
    fullfilled

    - name: '[CFG MGMT] Recover the file status from storage'
      set_fact:
        redis_multi_var: "{{ lookup('redis_kv', 'key1', 'key2', 'key3') }}"
        redis_array: "{{ lookup('redis_kv', files) }}"

    - name: 'Debug Key by Key'
      debug: var=redis_multi_var

    - name: 'Debug an Array of keys'
      debug: var=redis_array

RETURN:
    _list:
        description:
            - a value associated with input key
        type: strings
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: redis_kv
    author: Jan-Piet Mens <jpmens(at)gmail.com>
    version_added: "0.9"
    short_description: fetch data from Redis
    description:
      - this looup returns a list of items given to it, if any of the top level items is also a list it will flatten it, but it will not recurse
    requirements:
      - redis (python library https://github.com/andymccurdy/redis-py/)
    options:
      _terms:
        description: Two element comma separated strings composed of url of the Redis server and key to query
        options:
          _url:
            description: location of redis host in url format
            default: 'redis://localhost:6379'
          _key:
            description: key to query
            required: True
"""

EXAMPLES = """
- name: query redis for somekey
  debug: msg="{{ lookup('redis_kv', 'redis://localhost:6379,somekey') }} is value in Redis for somekey"
"""

RETURN = """
_raw:
  description: values stored in Redis
"""
import os
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
    import redis
    HAVE_REDIS = True
except ImportError:
    raise AnsibleError("Can't LOOKUP(redis_kv): module redis is not installed")

ANSIBLE_REDIS_URL = os.getenv('ANSIBLE_REDIS_URL', '127.0.0.1')
ANSIBLE_REDIS_PORT = os.getenv('ANSIBLE_REDIS_PORT', '6379')


class RedisClient:
    def __init__(self, host=ANSIBLE_REDIS_URL, port=ANSIBLE_REDIS_PORT):
        self.host = host
        self.port = port
        self.baseurl = '{}:{}'.format(ANSIBLE_REDIS_URL, ANSIBLE_REDIS_PORT)

    def get(self, key):
        url = 'redis://{}'.format(self.baseurl)

        try:
            conn = redis.Redis(host=self.host, port=self.port)

        except ConnectionError:
            raise AnsibleError("Cannot connect to Redis Server")

        res = conn.get(key)
        if res is None:
            res = ""

        return res


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        self.redis_client = RedisClient()

        ret = []
        for term in terms:
            if isinstance(term, list):
                for val in term:
                    ret.append(self.parse(val))
            else:
                ret.append(self.parse(term))

        return ret

    def parse(self, val):
        key = val.split()[0]
        value = self.redis_client.get(key)
        return value
