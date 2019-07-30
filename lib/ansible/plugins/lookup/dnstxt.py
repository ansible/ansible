# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: dnstxt
    author: Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
    version_added: "0.9"
    short_description: query a domain(s)'s DNS txt fields
    requirements:
      - dns/dns.resolver (python library)
    description:
      - Uses a python library to return the DNS TXT record for a domain.
    options:
      _terms:
        description: domain or list of domains to query TXT records from
        required: True
        type: list
"""

EXAMPLES = """
- name: show txt entry
  debug: msg="{{lookup('dnstxt', ['test.example.com'])}}"

- name: iterate over txt entries
  debug: msg="{{item}}"
  with_dnstxt:
    - 'test.example.com'
    - 'other.example.com'
    - 'last.example.com'

- name: iterate of a comma delimited DNS TXT entry
  debug: msg="{{item}}"
  with_dnstxt: "{{lookup('dnstxt', ['test.example.com']).split(',')}}"
"""

RETURN = """
  _list:
    description:
      - values returned by the DNS TXT record.
    type: list
"""

HAVE_DNS = False
try:
    import dns.resolver
    from dns.exception import DNSException
    HAVE_DNS = True
except ImportError:
    pass

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.plugins.lookup import LookupBase

# ==============================================================
# DNSTXT: DNS TXT records
#
#       key=domainname
# TODO: configurable resolver IPs
# --------------------------------------------------------------


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        if HAVE_DNS is False:
            raise AnsibleError("Can't LOOKUP(dnstxt): module dns.resolver is not installed")

        ret = []
        for term in terms:
            domain = term.split()[0]
            string = []
            try:
                answers = dns.resolver.query(domain, 'TXT')
                for rdata in answers:
                    s = rdata.to_text()
                    string.append(s[1:-1])  # Strip outside quotes on TXT rdata

            except dns.resolver.NXDOMAIN:
                string = 'NXDOMAIN'
            except dns.resolver.Timeout:
                string = ''
            except dns.resolver.NoAnswer:
                string = ''
            except DNSException as e:
                raise AnsibleError("dns.resolver unhandled exception %s" % to_native(e))

            ret.append(''.join(string))

        return ret
