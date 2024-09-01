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

from __future__ import annotations

from collections import defaultdict

import platform

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts import timeout


class CycleFoundInFactDeps(Exception):
    '''Indicates there is a cycle in fact collector deps

    If collector-B requires collector-A, and collector-A requires
    collector-B, that is a cycle. In that case, there is no ordering
    that will satisfy B before A and A and before B. That will cause this
    error to be raised.
    '''
    pass


class UnresolvedFactDep(ValueError):
    pass


class CollectorNotFoundError(KeyError):
    pass


class BaseFactCollector:
    _fact_ids = set()  # type: t.Set[str]

    _platform = 'Generic'
    name = None  # type: str | None
    required_facts = set()  # type: t.Set[str]

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

        if fact_dict is None:
            return {}
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


def select_collector_classes(collector_names, all_fact_subsets):
    seen_collector_classes = set()

    selected_collector_classes = []

    for collector_name in collector_names:
        collector_classes = all_fact_subsets.get(collector_name, [])
        for collector_class in collector_classes:
            if collector_class not in seen_collector_classes:
                selected_collector_classes.append(collector_class)
                seen_collector_classes.add(collector_class)

    return selected_collector_classes


def _get_requires_by_collector_name(collector_name, all_fact_subsets):
    required_facts = set()

    try:
        collector_classes = all_fact_subsets[collector_name]
    except KeyError:
        raise CollectorNotFoundError('Fact collector "%s" not found' % collector_name)
    for collector_class in collector_classes:
        required_facts.update(collector_class.required_facts)
    return required_facts


def find_unresolved_requires(collector_names, all_fact_subsets):
    '''Find any collector names that have unresolved requires

    Returns a list of collector names that correspond to collector
    classes whose .requires_facts() are not in collector_names.
    '''
    unresolved = set()

    for collector_name in collector_names:
        required_facts = _get_requires_by_collector_name(collector_name, all_fact_subsets)
        for required_fact in required_facts:
            if required_fact not in collector_names:
                unresolved.add(required_fact)

    return unresolved


def resolve_requires(unresolved_requires, all_fact_subsets):
    new_names = set()
    failed = []
    for unresolved in unresolved_requires:
        if unresolved in all_fact_subsets:
            new_names.add(unresolved)
        else:
            failed.append(unresolved)

    if failed:
        raise UnresolvedFactDep('unresolved fact dep %s' % ','.join(failed))
    return new_names


def build_dep_data(collector_names, all_fact_subsets):
    dep_map = defaultdict(set)
    for collector_name in collector_names:
        collector_deps = set()
        for collector in all_fact_subsets[collector_name]:
            for dep in collector.required_facts:
                collector_deps.add(dep)
        dep_map[collector_name] = collector_deps
    return dep_map


def tsort(dep_map):
    sorted_list = []

    unsorted_map = dep_map.copy()

    while unsorted_map:
        acyclic = False
        for node, edges in list(unsorted_map.items()):
            for edge in edges:
                if edge in unsorted_map:
                    break
            else:
                acyclic = True
                del unsorted_map[node]
                sorted_list.append((node, edges))

        if not acyclic:
            raise CycleFoundInFactDeps('Unable to tsort deps, there was a cycle in the graph. sorted=%s' % sorted_list)

    return sorted_list


def _solve_deps(collector_names, all_fact_subsets):
    unresolved = collector_names.copy()
    solutions = collector_names.copy()

    while True:
        unresolved = find_unresolved_requires(solutions, all_fact_subsets)
        if unresolved == set():
            break

        new_names = resolve_requires(unresolved, all_fact_subsets)
        solutions.update(new_names)

    return solutions


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

    complete_collector_names = _solve_deps(collector_names, all_fact_subsets)

    dep_map = build_dep_data(complete_collector_names, all_fact_subsets)

    ordered_deps = tsort(dep_map)
    ordered_collector_names = [x[0] for x in ordered_deps]

    selected_collector_classes = select_collector_classes(ordered_collector_names,
                                                          all_fact_subsets)

    return selected_collector_classes
