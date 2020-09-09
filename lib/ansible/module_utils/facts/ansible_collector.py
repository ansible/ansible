# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import sys

from ansible.module_utils.facts import timeout
from ansible.module_utils.facts import collector
from ansible.module_utils.common.collections import is_string


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
        # assume filter_spec='' or filter_spec=[] is equivalent to filter_spec='*'
        if not filter_spec or filter_spec == '*':
            return facts_dict

        if is_string(filter_spec):
            filter_spec = [filter_spec]

        return [(x, y) for x, y in facts_dict.items() for f in filter_spec if not f or fnmatch.fnmatch(x, f)]

    def collect(self, module=None, collected_facts=None):
        collected_facts = collected_facts or {}

        facts_dict = {}

        for collector_obj in self.collectors:
            info_dict = {}

            try:

                # Note: this collects with namespaces, so collected_facts also includes namespaces
                info_dict = collector_obj.collect_with_namespace(module=module,
                                                                 collected_facts=collected_facts)
            except Exception as e:
                sys.stderr.write(repr(e))
                sys.stderr.write('\n')

            # shallow copy of the new facts to pass to each collector in collected_facts so facts
            # can reference other facts they depend on.
            collected_facts.update(info_dict.copy())

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

    filter_spec = filter_spec or []
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
