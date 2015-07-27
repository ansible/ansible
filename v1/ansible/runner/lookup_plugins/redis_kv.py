# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
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

from ansible import utils, errors
import os
HAVE_REDIS=False
try:
    import redis        # https://github.com/andymccurdy/redis-py/
    HAVE_REDIS=True
except ImportError:
    pass
import re

# ==============================================================
# REDISGET: Obtain value from a GET on a Redis key. Terms
# expected: 0 = URL, 1 = Key
# URL may be empty, in which case redis://localhost:6379 assumed
# --------------------------------------------------------------

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

        if HAVE_REDIS == False:
            raise errors.AnsibleError("Can't LOOKUP(redis_kv): module redis is not installed")

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject) 

        ret = []
        for term in terms:
            (url,key) = term.split(',')
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
                raise errors.AnsibleError("Bad URI in redis lookup")

            try:
                conn = redis.Redis(host=host, port=port)
                res = conn.get(key)
                if res is None:
                    res = ""
                ret.append(res)
            except:
                ret.append("")  # connection failed or key not found
        return ret
