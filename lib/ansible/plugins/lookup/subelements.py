# (c) 2013, Serge van Ginderachter <serge@vanginderachter.be>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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
        if not isinstance(flags, dict) and not all([isinstance(key, string_types) and key in FLAGS for key in flags]):
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
