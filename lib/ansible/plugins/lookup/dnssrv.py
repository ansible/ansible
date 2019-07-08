# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: dnssrv
    author: Ryan Kraus (@rmkraus) <rmkraus(at)gmail.com>
    version_added: "2.9"
    short_description: query a domain(s)'s DNS srv fields
    requirements:
      - dns/dns.resolver (python library)
    description:
      - "Uses a python library to return the sorted DNS SRV records for a domain."
      - "Records are returned as a list of lists of dictionaries.
         Entries in the top level are lists grouped by priority (lowest first).
         Entries in the next level are dictionaries sorted by weight (highest first).
         The dictionaries have two keys, weight (normalized to be a percentage) and target."
      - "The target values returned will be cleaned to remove any trailing dots
         and have the port appended with a semicolon seperation. Ex: test.example.com:8080"
    options:
      _terms:
        description: domain to query SRV records from
        required: True
        type: string
    notes:
      - Per RFC 2782, lowest priority entries MUST be attempted first.
        Higher weights SHOULD be used more often proportionally to their relative weight.
"""

EXAMPLES = """
- name: show all srv entries
  debug: msg="{{ lookup('dnssrv', '_test._tcp.example.com') }}"

- name: show lowest priority, highest weight target
  debug: msg="{{ lookup('dnssrv', '_test._tcp.example.com').0.0.target }}"

- name: iterate over lowest priority entries
  debug: msg="Target {{ item.target }} should be used {{ item.weight }}% of the time."
  loop: "{{ lookup('dnssrv', '_test._tcp.example.com').0 }}"
"""

RETURN = """
  _list:
    description:
      - "List of lists of dicts. Sorted and grouped by priority then weight."
      - "Dicts have keys: weight and target."
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

from collections import defaultdict


def _normalize_weights(records):
    '''Normalize all the weights in a record set to be percentages and sort.'''
    wt_sum = float(sum([rec['weight'] for rec in records]))
    [rec.update({'weight': rec['weight'] / wt_sum * 100}) for rec in records]
    records.sort(key=lambda record: 1 - record['weight'])


class LookupModule(LookupBase):

    @staticmethod
    def _do_dns_query(domain):
        '''Perform DNS query.'''
        try:
            return dns.resolver.query(domain, 'SRV')
        except dns.resolver.Timeout:
            return []
        except dns.resolver.NoAnswer:
            return []
        except DNSException as e:
            raise AnsibleError("dns.resolver unhandled exception %s" % to_native(e))

    def run(self, terms, variables=None, **kwargs):
        '''Run dnssrv lookup.'''
        if HAVE_DNS is False:
            raise AnsibleError("Can't LOOKUP(dnssrv): module dns.resolver is not installed")

        # parse inputs
        try:
            term = terms.pop(0)
        except IndexError:
            raise AnsibleError("dnssrv lookup plugin requires an input")
        domain = term.split()[0]

        # perform query
        answers = self._do_dns_query(domain)
        if not answers:
            return answers

        # extract all dns answers, group by priority
        raw = defaultdict(list)
        for rdata in answers:
            # Per RFC 2782, targets will be an absolute FQDN. This means
            # they end with a final dot. Most Python libraries break spec
            # and do not tolerate this trailing dot. This will strip it off.
            target = '.'.join(rdata.target.to_text().split('.')[:-1])
            port = '{0}'.format(rdata.port)
            weight = rdata.weight
            priority = rdata.priority

            raw[priority].append(
                {'priority': rdata.priority,
                 'weight': weight,
                 'target': ':'.join([target, port])
                 })

        # sort by priority, normalize/sort by weight
        pris = sorted(raw)
        all = []
        for pri in pris:
            all.append(raw[pri])
            _normalize_weights(all[-1])

        return all
