# (c) 2018 Stoned Elipot <stoned.elipot(at)gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: dbm
    author: Stoned Elipot <stoned.elipot(at)gmail.com>
    version_added: "2.7"
    short_description: return a list of values from a DBM database
    description:
        - The dbm lookup fetches the values of a list of keys from a DBM database.
    options:
      _terms:
        description: the list of keys to fetch from the DBM database.
        type: list
        elements: string
      file:
        description: Name of the DBM database file.
        type: path
        required: True
      default:
        description: Return value for an absent key.
        type: string
        default: ''
"""

EXAMPLES = """
- debug: msg="{{ lookup('dbm','key1', 'key2', file='/tmp/my.dbm') }}"
"""

RETURN = """
  _list:
    description:
      - values of keys.
    type: list
"""
try:
    from anydbm import open as dbm_open
except ImportError:
    from dbm import open as dbm_open

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        dbm_file = kwargs.get('file')
        if not dbm_file:
            raise AnsibleError('dbm lookup: missing file option')

        dflt = kwargs.get('default')

        try:
            dbm = dbm_open(dbm_file, 'r')
        except Exception as e:
            raise AnsibleError('dbm lookup: unable to open DBM %s: %s' % (dbm_file, to_native(e)))

        ret = []
        for term in terms:
            try:
                value = dbm[term]
            except KeyError:
                value = dflt
            ret.append(value)

        dbm.close()
        return ret
