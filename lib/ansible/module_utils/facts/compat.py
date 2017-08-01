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

from ansible.module_utils.facts.namespace import PrefixFactNamespace
from ansible.module_utils.facts import default_collectors
from ansible.module_utils.facts import ansible_collector


def get_all_facts(module):
    '''compat api for ansible 2.2/2.3 module_utils.facts.get_all_facts method

    Expects module to be an instance of AnsibleModule, with a 'gather_subset' param.

    returns a dict mapping the bare fact name ('default_ipv4' with no 'ansible_' namespace) to
    the fact value.'''

    gather_subset = module.params['gather_subset']
    return ansible_facts(module, gather_subset=gather_subset)


def ansible_facts(module, gather_subset=None):
    '''Compat api for ansible 2.0/2.2/2.3 module_utils.facts.ansible_facts method

    2.3/2.3 expects a gather_subset arg.
    2.0/2.1 does not except a gather_subset arg

    So make gather_subsets an optional arg, defaulting to configured DEFAULT_GATHER_TIMEOUT

    'module' should be an instance of an AnsibleModule.

    returns a dict mapping the bare fact name ('default_ipv4' with no 'ansible_' namespace) to
    the fact value.
    '''

    gather_subset = gather_subset or module.params.get('gather_subset', ['all'])
    gather_timeout = module.params.get('gather_timeout', 10)
    filter_spec = module.params.get('filter', '*')

    minimal_gather_subset = frozenset(['apparmor', 'caps', 'cmdline', 'date_time',
                                       'distribution', 'dns', 'env', 'fips', 'local', 'lsb',
                                       'pkg_mgr', 'platform', 'python', 'selinux',
                                       'service_mgr', 'ssh_pub_keys', 'user'])

    all_collector_classes = default_collectors.collectors

    # don't add a prefix
    namespace = PrefixFactNamespace(namespace_name='ansible',
                                    prefix='')

    fact_collector = \
        ansible_collector.get_ansible_collector(all_collector_classes=all_collector_classes,
                                                namespace=namespace,
                                                filter_spec=filter_spec,
                                                gather_subset=gather_subset,
                                                gather_timeout=gather_timeout,
                                                minimal_gather_subset=minimal_gather_subset)

    facts_dict = fact_collector.collect(module=module)

    return facts_dict
