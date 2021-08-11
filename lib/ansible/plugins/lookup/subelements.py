# (c) 2013, Serge van Ginderachter <serge@vanginderachter.be>
# (c) 2012-17 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: subelements
    author: Serge van Ginderachter (!UNKNOWN) <serge@vanginderachter.be>
    version_added: "1.4"
    short_description: traverse nested key from a list of dictionaries
    description:
      - Subelements walks a list of hashes (aka dictionaries) and then traverses a list with a given (nested sub-)key inside of those records.
    options:
      _terms:
         description: tuple of list of dictionaries and dictionary key to extract
         required: True
      skip_missing:
        default: False
        description:
          - Lookup accepts this flag from a dictionary as optional. See Example section for more information.
          - If set to C(True), the lookup plugin will skip the lists items that do not contain the given subkey.
          - If set to C(False), the plugin will yield an error and complain about the missing subkey.
"""

EXAMPLES = """
- name: show var structure as it is needed for example to make sense
  hosts: all
  vars:
    users:
      - name: alice
        authorized:
          - /tmp/alice/onekey.pub
          - /tmp/alice/twokey.pub
        mysql:
            password: mysql-password
            hosts:
              - "%"
              - "127.0.0.1"
              - "::1"
              - "localhost"
            privs:
              - "*.*:SELECT"
              - "DB1.*:ALL"
        groups:
          - wheel
      - name: bob
        authorized:
          - /tmp/bob/id_rsa.pub
        mysql:
            password: other-mysql-password
            hosts:
              - "db1"
            privs:
              - "*.*:SELECT"
              - "DB2.*:ALL"
  tasks:
    - name: Set authorized ssh key, extracting just that data from 'users'
      authorized_key:
        user: "{{ item.0.name }}"
        key: "{{ lookup('file', item.1) }}"
      with_subelements:
         - "{{ users }}"
         - authorized

    - name: Setup MySQL users, given the mysql hosts and privs subkey lists
      mysql_user:
        name: "{{ item.0.name }}"
        password: "{{ item.0.mysql.password }}"
        host: "{{ item.1 }}"
        priv: "{{ item.0.mysql.privs | join('/') }}"
      with_subelements:
        - "{{ users }}"
        - mysql.hosts

    - name: list groups for users that have them, don't error if groups key is missing
      debug: var=item
      loop: "{{ q('subelements', users, 'groups', {'skip_missing': True}) }}"
"""

RETURN = """
_list:
  description: list of subelements extracted
"""

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms


FLAGS = ('skip_missing',)


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        def _raise_terms_error(msg=""):
            raise AnsibleError(
                "subelements lookup expects a list of two or three items, " + msg)

        terms[0] = listify_lookup_plugin_terms(terms[0], templar=self._templar, loader=self._loader)

        # check lookup terms - check number of terms
        if not isinstance(terms, list) or not 2 <= len(terms) <= 3:
            _raise_terms_error()

        # first term should be a list (or dict), second a string holding the subkey
        if not isinstance(terms[0], (list, dict)) or not isinstance(terms[1], string_types):
            _raise_terms_error("first a dict or a list, second a string pointing to the subkey")
        subelements = terms[1].split(".")

        if isinstance(terms[0], dict):  # convert to list:
            if terms[0].get('skipped', False) is not False:
                # the registered result was completely skipped
                return []
            elementlist = []
            for key in terms[0]:
                elementlist.append(terms[0][key])
        else:
            elementlist = terms[0]

        # check for optional flags in third term
        flags = {}
        if len(terms) == 3:
            flags = terms[2]
        if not isinstance(flags, dict) and not all(isinstance(key, string_types) and key in FLAGS for key in flags):
            _raise_terms_error("the optional third item must be a dict with flags %s" % FLAGS)

        # build_items
        ret = []
        for item0 in elementlist:
            if not isinstance(item0, dict):
                raise AnsibleError("subelements lookup expects a dictionary, got '%s'" % item0)
            if item0.get('skipped', False) is not False:
                # this particular item is to be skipped
                continue

            skip_missing = boolean(flags.get('skip_missing', False), strict=False)
            subvalue = item0
            lastsubkey = False
            sublist = []
            for subkey in subelements:
                if subkey == subelements[-1]:
                    lastsubkey = True
                if subkey not in subvalue:
                    if skip_missing:
                        continue
                    else:
                        raise AnsibleError("could not find '%s' key in iterated item '%s'" % (subkey, subvalue))
                if not lastsubkey:
                    if not isinstance(subvalue[subkey], dict):
                        if skip_missing:
                            continue
                        else:
                            raise AnsibleError("the key %s should point to a dictionary, got '%s'" % (subkey, subvalue[subkey]))
                    else:
                        subvalue = subvalue[subkey]
                else:  # lastsubkey
                    if not isinstance(subvalue[subkey], list):
                        raise AnsibleError("the key %s should point to a list, got '%s'" % (subkey, subvalue[subkey]))
                    else:
                        sublist = subvalue.pop(subkey, [])
            for item1 in sublist:
                ret.append((item0, item1))

        return ret
