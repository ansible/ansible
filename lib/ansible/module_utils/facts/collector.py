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

from collections import defaultdict

import platform

from ansible.module_utils.facts import timeout


class BaseFactCollector:
    _fact_ids = set()

    _platform = 'Generic'
    name = None

    def __init__(self, collectors=None, namespace=None):
        '''Base class for things that collect facts.

        'collectors' is an optional list of other FactCollectors for composing.'''
        self.collectors = collectors or []

        # self.namespace is a object with a 'transform' method that transforms
        # the name to indicate the namespace (ie, adds a prefix or suffix).
        self.namespace = namespace

        self.fact_ids = set([self.name])
        self.fact_ids.update(self._fact_ids)

    @classmethod
    def platform_match(cls, platform_info):
        if platform_info.get('system', None) == cls._platform:
            return cls
        return None

    def _transform_name(self, key_name):
        if self.namespace:
            return self.namespace.transform(key_name)
        return key_name

    def _transform_dict_keys(self, fact_dict):
        '''update a dicts keys to use new names as transformed by self._transform_name'''

        for old_key in list(fact_dict.keys()):
            new_key = self._transform_name(old_key)
            # pop the item by old_key and replace it using new_key
            fact_dict[new_key] = fact_dict.pop(old_key)
        return fact_dict

    # TODO/MAYBE: rename to 'collect' and add 'collect_without_namespace'
    def collect_with_namespace(self, module=None, collected_facts=None):
        # collect, then transform the key names if needed
        facts_dict = self.collect(module=module, collected_facts=collected_facts)
        if self.namespace:
            facts_dict = self._transform_dict_keys(facts_dict)
        return facts_dict

    def collect(self, module=None, collected_facts=None):
        '''do the fact collection

        'collected_facts' is a object (a dict, likely) that holds all previously
          facts. This is intended to be used if a FactCollector needs to reference
          another fact (for ex, the system arch) and should not be modified (usually).

          Returns a dict of facts.

          '''
        facts_dict = {}
        return facts_dict


def get_collector_names(valid_subsets=None,
                        minimal_gather_subset=None,
                        gather_subset=None,
                        aliases_map=None,
                        platform_info=None):
    '''return a set of FactCollector names based on gather_subset spec.

    gather_subset is a spec describing which facts to gather.
    valid_subsets is a frozenset of potential matches for gather_subset ('all', 'network') etc
    minimal_gather_subsets is a frozenset of matches to always use, even for gather_subset='!all'
    '''

    # Retrieve module parameters
    gather_subset = gather_subset or ['all']

    # the list of everything that 'all' expands to
    valid_subsets = valid_subsets or frozenset()

    # if provided, minimal_gather_subset is always added, even after all negations
    minimal_gather_subset = minimal_gather_subset or frozenset()

    aliases_map = aliases_map or defaultdict(set)

    # Retrieve all facts elements
    additional_subsets = set()
    exclude_subsets = set()

    # total always starts with the min set, then
    # adds of the additions in gather_subset, then
    # excludes all of the excludes, then add any explicitly
    # requested subsets.
    gather_subset_with_min = ['min']
    gather_subset_with_min.extend(gather_subset)

    # subsets we mention in gather_subset explicitly, except for 'all'/'min'
    explicitly_added = set()

    for subset in gather_subset_with_min:
        subset_id = subset
        if subset_id == 'min':
            additional_subsets.update(minimal_gather_subset)
            continue
        if subset_id == 'all':
            additional_subsets.update(valid_subsets)
            continue
        if subset_id.startswith('!'):
            subset = subset[1:]
            if subset == 'min':
                exclude_subsets.update(minimal_gather_subset)
                continue
            if subset == 'all':
                exclude_subsets.update(valid_subsets - minimal_gather_subset)
                continue
            exclude = True
        else:
            exclude = False

        if exclude:
            # include 'devices', 'dmi' etc for '!hardware'
            exclude_subsets.update(aliases_map.get(subset, set()))
            exclude_subsets.add(subset)
        else:
            # NOTE: this only considers adding an unknown gather subsetup an error. Asking to
            #       exclude an unknown gather subset is ignored.
            if subset_id not in valid_subsets:
                raise TypeError("Bad subset '%s' given to Ansible. gather_subset options allowed: all, %s" %
                                (subset, ", ".join(sorted(valid_subsets))))

            explicitly_added.add(subset)
            additional_subsets.add(subset)

    if not additional_subsets:
        additional_subsets.update(valid_subsets)

    additional_subsets.difference_update(exclude_subsets - explicitly_added)

    return additional_subsets


def find_collectors_for_platform(all_collector_classes, compat_platforms):
    found_collectors = set()
    found_collectors_names = set()

    # start from specific platform, then try generic
    for compat_platform in compat_platforms:
        platform_match = None
        for all_collector_class in all_collector_classes:

            # ask the class if it is compatible with the platform info
            platform_match = all_collector_class.platform_match(compat_platform)

            if not platform_match:
                continue

            primary_name = all_collector_class.name

            if primary_name not in found_collectors_names:
                found_collectors.add(all_collector_class)
                found_collectors_names.add(all_collector_class.name)

    return found_collectors


def build_fact_id_to_collector_map(collectors_for_platform):
    fact_id_to_collector_map = defaultdict(list)
    aliases_map = defaultdict(set)

    for collector_class in collectors_for_platform:
        primary_name = collector_class.name

        fact_id_to_collector_map[primary_name].append(collector_class)

        for fact_id in collector_class._fact_ids:
            fact_id_to_collector_map[fact_id].append(collector_class)
            aliases_map[primary_name].add(fact_id)

    return fact_id_to_collector_map, aliases_map


def collector_classes_from_gather_subset(all_collector_classes=None,
                                         valid_subsets=None,
                                         minimal_gather_subset=None,
                                         gather_subset=None,
                                         gather_timeout=None,
                                         platform_info=None):
    '''return a list of collector classes that match the args'''

    # use gather_name etc to get the list of collectors

    all_collector_classes = all_collector_classes or []

    minimal_gather_subset = minimal_gather_subset or frozenset()

    platform_info = platform_info or {'system': platform.system()}

    gather_timeout = gather_timeout or timeout.DEFAULT_GATHER_TIMEOUT

    # tweak the modules GATHER_TIMEOUT
    timeout.GATHER_TIMEOUT = gather_timeout

    valid_subsets = valid_subsets or frozenset()

    # maps alias names like 'hardware' to the list of names that are part of hardware
    # like 'devices' and 'dmi'
    aliases_map = defaultdict(set)

    compat_platforms = [platform_info, {'system': 'Generic'}]

    collectors_for_platform = find_collectors_for_platform(all_collector_classes, compat_platforms)

    # all_facts_subsets maps the subset name ('hardware') to the class that provides it.

    # TODO: name collisions here? are there facts with the same name as a gather_subset (all, network, hardware, virtual, ohai, facter)
    all_fact_subsets, aliases_map = build_fact_id_to_collector_map(collectors_for_platform)

    all_valid_subsets = frozenset(all_fact_subsets.keys())

    # expand any fact_id/collectorname/gather_subset term ('all', 'env', etc) to the list of names that represents
    collector_names = get_collector_names(valid_subsets=all_valid_subsets,
                                          minimal_gather_subset=minimal_gather_subset,
                                          gather_subset=gather_subset,
                                          aliases_map=aliases_map,
                                          platform_info=platform_info)

    # TODO: can be a set()
    seen_collector_classes = []

    selected_collector_classes = []

    for collector_name in collector_names:
        collector_classes = all_fact_subsets.get(collector_name, [])

        # TODO? log/warn if we dont find an implementation of a fact_id?

        for collector_class in collector_classes:
            if collector_class not in seen_collector_classes:
                selected_collector_classes.append(collector_class)
                seen_collector_classes.append(collector_class)

    return selected_collector_classes
