# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: redis_kv
    author: Jan-Piet Mens <jpmens(at)gmail.com>
    version_added: "0.9"
    short_description: fetch data from Redis
    deprecated:
        why: This lookup uses options intermingled with terms which blurs the interface between settings and data
        version: '2.9'
        alternative: new 'redis' lookup
    description:
      - this lookup returns a list of items given to it, if any of the top level items is also a list it will flatten it, but it will not recurse
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
import re

HAVE_REDIS = False
try:
    import redis
    HAVE_REDIS = True
except ImportError:
    pass

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


# ==============================================================
# REDISGET: Obtain value from a GET on a Redis key. Terms
# expected: 0 = URL, 1 = Key
# URL may be empty, in which case redis://localhost:6379 assumed
# --------------------------------------------------------------
class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        if not HAVE_REDIS:
            raise AnsibleError("Can't LOOKUP(redis_kv): module redis is not installed")

        ret = []
        for term in terms:
            (url, key) = term.split(',')
            if url == "":
                url = 'redis://localhost:6379'

            # urlsplit on Python 2.6.1 is broken. Hmm. Probably also the reason
            # Redis' from_url() doesn't work here.

            p = '(?P<scheme>[^:]+)://?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'

            try:
                m = re.search(p, url)
                host = m.group('host')
                port = int(m.group('port'))
            except AttributeError:
                raise AnsibleError("Bad URI in redis lookup")

            try:
                conn = redis.Redis(host=host, port=port)
                res = conn.get(key)
                if res is None:
                    res = ""
                ret.append(res)
            except Exception:
                ret.append("")  # connection failed or key not found
        return ret
