# (c) 2017-2018, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: lmdb
    author:
      - Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
      - Ansible Core
    version_added: "2.5"
    short_description: fetch data from LMDB
    description:
      - This lookup returns a list of results from an LMDB DB corresponding to a list of items given to it
    requirements:
      - lmdb (python library https://lmdb.readthedocs.io/en/release/)
    options:
      _terms:
        description: list of keys to query
      db:
        description: path to LMDB database
        default: 'ansible.mdb'
"""

EXAMPLES = """
- name: query LMDB for a list of country codes
  debug: msg="{{ lookup('lmdb_kv', 'nl', 'be', 'lu', db='jp.mdb') }}"

- name: use list of values in a loop
  debug: msg="Hello from {{ item.0 }} a.k.a. {{ item.1 }}"
  with_lmdb_kv:
     - "n*"

"""

RETURN = """
_raw:
  description: value(s) stored in LMDB
"""


from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

HAVE_LMDB = True
try:
    import lmdb
except ImportError:
    HAVE_LMDB = False


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        '''
        terms contain any number of keys to be retrieved.
        If terms is None, all keys from the database are returned
        with their values, and if term ends in an asterisk, we
        start searching there

        The LMDB database defaults to 'ansible.mdb' if Ansible's
        variable 'lmdb_kv_db' is not set:

              vars:
                - lmdb_kv_db: "jp.mdb"
        '''

        if HAVE_LMDB is False:
            raise AnsibleError("Can't LOOKUP(lmdb_kv): this module requires lmdb to be installed")

        db = variables.get('lmdb_kv_db', None)
        if db is None:
            db = kwargs.get('db', 'ansible.mdb')
        db = str(db)

        try:
            env = lmdb.open(db, readonly=True)
        except Exception as e:
            raise AnsibleError("LMDB can't open database %s: %s" % (db, str(e)))

        ret = []
        if len(terms) == 0:
            with env.begin() as txn:
                cursor = txn.cursor()
                cursor.first()
                for key, value in cursor:
                    ret.append((key, value))

        else:
            for term in terms:
                with env.begin() as txn:
                    if term.endswith('*'):
                        cursor = txn.cursor()
                        prefix = term[:-1]           # strip asterisk
                        # cursor.set_range(prefix)
                        cursor.set_range(term)
                        while cursor.key().startswith(prefix):
                            ret.append(cursor.item())
                            cursor.next()
                    else:
                        value = txn.get(term)
                        if value is not None:
                            ret.append(value)

        return ret
