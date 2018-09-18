# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: redis
    author:
      - Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
      - Ansible Core
    version_added: "2.5"
    short_description: fetch data from Redis
    description:
      - This lookup returns a list of results from a Redis DB corresponding to a list of items given to it
    requirements:
      - redis (python library https://github.com/andymccurdy/redis-py/)
    options:
      _terms:
        description: list of keys to query
      host:
        description: location of Redis host
        default: '127.0.0.1'
        env:
          - name: ANSIBLE_REDIS_HOST
        ini:
          - section: lookup_redis
            key: host
      port:
        description: port on which Redis is listening on
        default: 6379A
        type: int
        env:
          - name: ANSIBLE_REDIS_PORT
        ini:
          - section: lookup_redis
            key: port
      socket:
        description: path to socket on which to query Redis, this option overrides host and port options when set.
        type: path
        env:
          - name: ANSIBLE_REDIS_SOCKET
        ini:
          - section: lookup_redis
            key: socket
"""

EXAMPLES = """
- name: query redis for somekey (default or configured settings used)
  debug: msg="{{ lookup('redis', 'somekey'}}"

- name: query redis for list of keys and non-default host and port
  debug: msg="{{ lookup('redis', item, host='myredis.internal.com', port=2121) }}"
  loop: '{{list_of_redis_keys}}'

- name: use list directly
  debug: msg="{{ lookup('redis', 'key1', 'key2', 'key3') }}"

- name: use list directly with a socket
  debug: msg="{{ lookup('redis', 'key1', 'key2', socket='/var/tmp/redis.sock') }}"

"""

RETURN = """
_raw:
  description: value(s) stored in Redis
"""

import os

HAVE_REDIS = False
try:
    import redis
    HAVE_REDIS = True
except ImportError:
    pass

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        if not HAVE_REDIS:
            raise AnsibleError("Can't LOOKUP(redis_kv): module redis is not installed")

        # get options
        self.set_options(direct=kwargs)

        # setup connection
        host = self.get_option('host')
        port = self.get_option('port')
        socket = self.get_option('socket')
        if socket is None:
            conn = redis.Redis(host=host, port=port)
        else:
            conn = redis.Redis(unix_socket_path=socket)

        ret = []
        for term in terms:
            try:
                res = conn.get(term)
                if res is None:
                    res = ""
                ret.append(res)
            except Exception:
                ret.append("")  # connection failed or key not found
        return ret
