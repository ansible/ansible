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

import fnmatch
import sys

from ansible.module_utils.facts import timeout
from ansible.module_utils.facts import collector


class AnsibleFactCollector(collector.BaseFactCollector):
    '''A FactCollector that returns results under 'ansible_facts' top level key.

       If a namespace if provided, facts will be collected under that namespace.
       For ex, a ansible.module_utils.facts.namespace.PrefixFactNamespace(prefix='ansible_')

       Has a 'from_gather_subset() constructor that populates collectors based on a
       gather_subset specifier.'''

    def __init__(self, collectors=None, namespace=None, filter_spec=None):

        super(AnsibleFactCollector, self).__init__(collectors=collectors,
                                                   namespace=namespace)

        self.filter_spec = filter_spec

    def _filter(self, facts_dict, filter_spec):
        # assume a filter_spec='' is equilv to filter_spec='*'
        if not filter_spec or filter_spec == '*':
            return facts_dict

        return [(x, y) for x, y in facts_dict.items() if fnmatch.fnmatch(x, filter_spec)]

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}

        facts_dict = {}

        for collector_obj in self.collectors:
            info_dict = {}

            # shallow copy of the accumulated collected facts to pass to each collector
            # for reference.
            collected_facts.update(facts_dict.copy())

            try:

                # Note: this collects with namespaces, so collected_facts also includes namespaces
                info_dict = collector_obj.collect_with_namespace(module=module,
                                                                 collected_facts=collected_facts)
            except Exception as e:
                sys.stderr.write(repr(e))
                sys.stderr.write('\n')

            # NOTE: If we want complicated fact dict merging, this is where it would hook in
            facts_dict.update(self._filter(info_dict, self.filter_spec))

        return facts_dict


class CollectorMetaDataCollector(collector.BaseFactCollector):
    '''Collector that provides a facts with the gather_subset metadata.'''

    name = 'gather_subset'
    _fact_ids = set([])

    def __init__(self, collectors=None, namespace=None, gather_subset=None, module_setup=None):
        super(CollectorMetaDataCollector, self).__init__(collectors, namespace)
        self.gather_subset = gather_subset
        self.module_setup = module_setup

    def collect(self, module=None, collected_facts=None):
        meta_facts = {'gather_subset': self.gather_subset}
        if self.module_setup:
            meta_facts['module_setup'] = self.module_setup
        return meta_facts


def get_ansible_collector(all_collector_classes,
                          namespace=None,
                          filter_spec=None,
                          gather_subset=None,
                          gather_timeout=None,
                          minimal_gather_subset=None):

    filter_spec = filter_spec or '*'
    gather_subset = gather_subset or ['all']
    gather_timeout = gather_timeout or timeout.DEFAULT_GATHER_TIMEOUT
    minimal_gather_subset = minimal_gather_subset or frozenset()

    collector_classes = \
        collector.collector_classes_from_gather_subset(
            all_collector_classes=all_collector_classes,
            minimal_gather_subset=minimal_gather_subset,
            gather_subset=gather_subset,
            gather_timeout=gather_timeout)

    collectors = []
    for collector_class in collector_classes:
        collector_obj = collector_class(namespace=namespace)
        collectors.append(collector_obj)

    # Add a collector that knows what gather_subset we used so it it can provide a fact
    collector_meta_data_collector = \
        CollectorMetaDataCollector(gather_subset=gather_subset,
                                   module_setup=True)
    collectors.append(collector_meta_data_collector)

    fact_collector = \
        AnsibleFactCollector(collectors=collectors,
                             filter_spec=filter_spec,
                             namespace=namespace)

    return fact_collector
