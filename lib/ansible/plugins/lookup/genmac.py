# (c) 2018, Abdoul Bah (@helldorado) <bahabdoul at gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: genmac
    author:
      - Abdoul Bah (@helldorado) <bahabdoul(at)gmail.com>
    version_added: "2.7"
    short_description: Generates a MAC address with the defined OUI prefix
    description:
      - This lookup return a random mac address.
    options:
      _terms:
        description: OUI prefix. See http://standards-oui.ieee.org/oui/oui.txt
        default: 'AC:DE:48'
      format:
        description: Convert MAC address to given format
"""

EXAMPLES = """
- name: Generate mac address
  debug: msg="{{ lookup('genmac', '52:54:00', format='cisco'}}"
"""

RETURN = """
_raw:
  description: random mac address.
"""

import os
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.plugins.filter import ipaddr


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        format = kwargs.get('format', None)
        if not terms:
            terms = ['AC:DE:48']
        ret = []
        for term in terms:
            ret = ipaddr.genmac(term)

        if format and format not in ['bool', 'int']:
            return ipaddr.hwaddr(ret, format).split(',')
        else:
            return ret.split(',')
