# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

#############################################
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import os
import sys
import re
import itertools
import traceback

from operator import attrgetter
from random import shuffle

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleOptionsError, AnsibleParserError
from ansible.inventory.data import InventoryData
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.loader import inventory_loader
from ansible.utils.helpers import deduplicate_list
from ansible.utils.path import unfrackpath
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars
from ansible.vars.plugins import get_vars_from_inventory_sources

display = Display()

IGNORED_ALWAYS = [br"^\.", b"^host_vars$", b"^group_vars$", b"^vars_plugins$"]
IGNORED_PATTERNS = [to_bytes(x) for x in C.INVENTORY_IGNORE_PATTERNS]
IGNORED_EXTS = [b'%s$' % to_bytes(re.escape(x)) for x in C.INVENTORY_IGNORE_EXTS]

IGNORED = re.compile(b'|'.join(IGNORED_ALWAYS + IGNORED_PATTERNS + IGNORED_EXTS))

PATTERN_WITH_SUBSCRIPT = re.compile(
    r'''^
        (.+)                    # A pattern expression ending with...
        \[(?:                   # A [subscript] expression comprising:
            (-?[0-9]+)|         # A single positive or negative number
            ([0-9]+)([:-])      # Or an x:y or x: range.
            ([0-9]*)
        )\]
        $
    ''', re.X
)


def order_patterns(patterns):
    ''' takes a list of patterns and reorders them by modifier to apply them consistently '''

    # FIXME: this goes away if we apply patterns incrementally or by groups
    pattern_regular = []
    pattern_intersection = []
    pattern_exclude = []
    for p in patterns:
        if not p:
            continue

        if p[0] == "!":
            pattern_exclude.append(p)
        elif p[0] == "&":
            pattern_intersection.append(p)
        else:
            pattern_regular.append(p)

    # if no regular pattern was given, hence only exclude and/or intersection
    # make that magically work
    if pattern_regular == []:
        pattern_regular = ['all']

    # when applying the host selectors, run those without the "&" or "!"
    # first, then the &s, then the !s.
    return pattern_regular + pattern_intersection + pattern_exclude


def split_host_pattern(pattern):
    """
    Takes a string containing host patterns separated by commas (or a list
    thereof) and returns a list of single patterns (which may not contain
    commas). Whitespace is ignored.

    Also accepts ':' as a separator for backwards compatibility, but it is
    not recommended due to the conflict with IPv6 addresses and host ranges.

    Example: 'a,b[1], c[2:3] , d' -> ['a', 'b[1]', 'c[2:3]', 'd']
    """

    if isinstance(pattern, list):
        results = (split_host_pattern(p) for p in pattern)
        # flatten the results
        return list(itertools.chain.from_iterable(results))
    elif not isinstance(pattern, string_types):
        pattern = to_text(pattern, errors='surrogate_or_strict')

    # If it's got commas in it, we'll treat it as a straightforward
    # comma-separated list of patterns.
    if u',' in pattern:
        patterns = pattern.split(u',')

    # If it doesn't, it could still be a single pattern. This accounts for
    # non-separator uses of colons: IPv6 addresses and [x:y] host ranges.
    else:
        try:
            (base, port) = parse_address(pattern, allow_ranges=True)
            patterns = [pattern]
        except Exception:
            # The only other case we accept is a ':'-separated list of patterns.
            # This mishandles IPv6 addresses, and is retained only for backwards
            # compatibility.
            patterns = re.findall(
                to_text(r'''(?:     # We want to match something comprising:
                        [^\s:\[\]]  # (anything other than whitespace or ':[]'
                        |           # ...or...
                        \[[^\]]*\]  # a single complete bracketed expression)
                    )+              # occurring once or more
                '''), pattern, re.X
            )

    return [p.strip() for p in patterns if p.strip()]


class InventoryManager(object):
    ''' Creates and manages inventory '''

    def __init__(self, loader, sources=None, parse=True):

        # base objects
        self._loader = loader
        self._inventory = InventoryData()

        # a list of host(names) to contain current inquiries to
        self._restriction = None
        self._subset = None

        # caches
        self._hosts_patterns_cache = {}  # resolved full patterns
        self._pattern_cache = {}  # resolved individual patterns

        # the inventory dirs, files, script paths or lists of hosts
        if sources is None:
            self._sources = []
        elif isinstance(sources, string_types):
            self._sources = [sources]
        else:
            self._sources = sources

        # get to work!
        if parse:
            self.parse_sources(cache=True)

    @property
    def localhost(self):
        return self._inventory.localhost

    @property
    def groups(self):
        return self._inventory.groups

    @property
    def hosts(self):
        return self._inventory.hosts

    def add_host(self, host, group=None, port=None):
        return self._inventory.add_host(host, group, port)

    def add_group(self, group):
        return self._inventory.add_group(group)

    def get_groups_dict(self):
        return self._inventory.get_groups_dict()

    def reconcile_inventory(self):
        self.clear_caches()
        return self._inventory.reconcile_inventory()

    def get_host(self, hostname):
        return self._inventory.get_host(hostname)

    def _fetch_inventory_plugins(self):
        ''' sets up loaded inventory plugins for usage '''

        display.vvvv('setting up inventory plugins')

        plugins = []
        for name in C.INVENTORY_ENABLED:
            plugin = inventory_loader.get(name)
            if plugin:
                plugins.append(plugin)
            else:
                display.warning('Failed to load inventory plugin, skipping %s' % name)

        if not plugins:
            raise AnsibleError("No inventory plugins available to generate inventory, make sure you have at least one whitelisted.")

        return plugins

    def parse_sources(self, cache=False):
        ''' iterate over inventory sources and parse each one to populate it'''

        parsed = False
        # allow for multiple inventory parsing
        for source in self._sources:

            if source:
                if ',' not in source:
                    source = unfrackpath(source, follow=False)
                parse = self.parse_source(source, cache=cache)
                if parse and not parsed:
                    parsed = True

        if parsed:
            # do post processing
            self._inventory.reconcile_inventory()
        else:
            if C.INVENTORY_UNPARSED_IS_FAILED:
                raise AnsibleError("No inventory was parsed, please check your configuration and options.")
            else:
                display.warning("No inventory was parsed, only implicit localhost is available")

        for group in self.groups.values():
            group.vars = combine_vars(group.vars, get_vars_from_inventory_sources(self._loader, self._sources, [group], 'inventory'))
        for host in self.hosts.values():
            host.vars = combine_vars(host.vars, get_vars_from_inventory_sources(self._loader, self._sources, [host], 'inventory'))

    def parse_source(self, source, cache=False):
        ''' Generate or update inventory for the source provided '''

        parsed = False
        failures = []
        display.debug(u'Examining possible inventory source: %s' % source)

        # use binary for path functions
        b_source = to_bytes(source)

        # process directories as a collection of inventories
        if os.path.isdir(b_source):
            display.debug(u'Searching for inventory files in directory: %s' % source)
            for i in sorted(os.listdir(b_source)):

                display.debug(u'Considering %s' % i)
                # Skip hidden files and stuff we explicitly ignore
                if IGNORED.search(i):
                    continue

                # recursively deal with directory entries
                fullpath = to_text(os.path.join(b_source, i), errors='surrogate_or_strict')
                parsed_this_one = self.parse_source(fullpath, cache=cache)
                display.debug(u'parsed %s as %s' % (fullpath, parsed_this_one))
                if not parsed:
                    parsed = parsed_this_one
        else:
            # left with strings or files, let plugins figure it out

            # set so new hosts can use for inventory_file/dir vars
            self._inventory.current_source = source

            # try source with each plugin
            for plugin in self._fetch_inventory_plugins():

                plugin_name = to_text(getattr(plugin, '_load_name', getattr(plugin, '_original_path', '')))
                display.debug(u'Attempting to use plugin %s (%s)' % (plugin_name, plugin._original_path))

                # initialize and figure out if plugin wants to attempt parsing this file
                try:
                    plugin_wants = bool(plugin.verify_file(source))
                except Exception:
                    plugin_wants = False

                if plugin_wants:
                    try:
                        # FIXME in case plugin fails 1/2 way we have partial inventory
                        plugin.parse(self._inventory, self._loader, source, cache=cache)
                        try:
                            plugin.update_cache_if_changed()
                        except AttributeError:
                            # some plugins might not implement caching
                            pass
                        parsed = True
                        display.vvv('Parsed %s inventory source with %s plugin' % (source, plugin_name))
                        break
                    except AnsibleParserError as e:
                        display.debug('%s was not parsable by %s' % (source, plugin_name))
                        tb = ''.join(traceback.format_tb(sys.exc_info()[2]))
                        failures.append({'src': source, 'plugin': plugin_name, 'exc': e, 'tb': tb})
                    except Exception as e:
                        display.debug('%s failed while attempting to parse %s' % (plugin_name, source))
                        tb = ''.join(traceback.format_tb(sys.exc_info()[2]))
                        failures.append({'src': source, 'plugin': plugin_name, 'exc': AnsibleError(e), 'tb': tb})
                else:
                    display.vvv("%s declined parsing %s as it did not pass its verify_file() method" % (plugin_name, source))

        if parsed:
            self._inventory.processed_sources.append(self._inventory.current_source)
        else:
            # only warn/error if NOT using the default or using it and the file is present
            # TODO: handle 'non file' inventory and detect vs hardcode default
            if source != '/etc/ansible/hosts' or os.path.exists(source):

                if failures:
                    # only if no plugin processed files should we show errors.
                    for fail in failures:
                        display.warning(u'\n* Failed to parse %s with %s plugin: %s' % (to_text(fail['src']), fail['plugin'], to_text(fail['exc'])))
                        if 'tb' in fail:
                            display.vvv(to_text(fail['tb']))

                # final error/warning on inventory source failure
                if C.INVENTORY_ANY_UNPARSED_IS_FAILED:
                    raise AnsibleError(u'Completely failed to parse inventory source %s' % (source))
                else:
                    display.warning("Unable to parse %s as an inventory source" % source)

        # clear up, jic
        self._inventory.current_source = None

        return parsed

    def clear_caches(self):
        ''' clear all caches '''
        self._hosts_patterns_cache = {}
        self._pattern_cache = {}
        # FIXME: flush inventory cache

    def refresh_inventory(self):
        ''' recalculate inventory '''

        self.clear_caches()
        self._inventory = InventoryData()
        self.parse_sources(cache=False)

    def _match_list(self, items, pattern_str):
        # compile patterns
        try:
            if not pattern_str[0] == '~':
                pattern = re.compile(fnmatch.translate(pattern_str))
            else:
                pattern = re.compile(pattern_str[1:])
        except Exception:
            raise AnsibleError('Invalid host list pattern: %s' % pattern_str)

        # apply patterns
        results = []
        for item in items:
            if pattern.match(item):
                results.append(item)
        return results

    def get_hosts(self, pattern="all", ignore_limits=False, ignore_restrictions=False, order=None):
        """
        Takes a pattern or list of patterns and returns a list of matching
        inventory host names, taking into account any active restrictions
        or applied subsets
        """

        hosts = []

        # Check if pattern already computed
        if isinstance(pattern, list):
            pattern_list = pattern[:]
        else:
            pattern_list = [pattern]

        if pattern_list:
            if not ignore_limits and self._subset:
                pattern_list.extend(self._subset)

            if not ignore_restrictions and self._restriction:
                pattern_list.extend(self._restriction)

            # This is only used as a hash key in the self._hosts_patterns_cache dict
            # a tuple is faster than stringifying
            pattern_hash = tuple(pattern_list)

            if pattern_hash not in self._hosts_patterns_cache:

                patterns = split_host_pattern(pattern)
                hosts = self._evaluate_patterns(patterns)

                # mainly useful for hostvars[host] access
                if not ignore_limits and self._subset:
                    # exclude hosts not in a subset, if defined
                    subset_uuids = set(s._uuid for s in self._evaluate_patterns(self._subset))
                    hosts = [h for h in hosts if h._uuid in subset_uuids]

                if not ignore_restrictions and self._restriction:
                    # exclude hosts mentioned in any restriction (ex: failed hosts)
                    hosts = [h for h in hosts if h.name in self._restriction]

                self._hosts_patterns_cache[pattern_hash] = deduplicate_list(hosts)

            # sort hosts list if needed (should only happen when called from strategy)
            if order in ['sorted', 'reverse_sorted']:
                hosts = sorted(self._hosts_patterns_cache[pattern_hash][:], key=attrgetter('name'), reverse=(order == 'reverse_sorted'))
            elif order == 'reverse_inventory':
                hosts = self._hosts_patterns_cache[pattern_hash][::-1]
            else:
                hosts = self._hosts_patterns_cache[pattern_hash][:]
                if order == 'shuffle':
                    shuffle(hosts)
                elif order not in [None, 'inventory']:
                    raise AnsibleOptionsError("Invalid 'order' specified for inventory hosts: %s" % order)

        return hosts

    def _evaluate_patterns(self, patterns):
        """
        Takes a list of patterns and returns a list of matching host names,
        taking into account any negative and intersection patterns.
        """

        patterns = order_patterns(patterns)
        hosts = []

        for p in patterns:
            # avoid resolving a pattern that is a plain host
            if p in self._inventory.hosts:
                hosts.append(self._inventory.get_host(p))
            else:
                that = self._match_one_pattern(p)
                if p[0] == "!":
                    that = set(that)
                    hosts = [h for h in hosts if h not in that]
                elif p[0] == "&":
                    that = set(that)
                    hosts = [h for h in hosts if h in that]
                else:
                    existing_hosts = set(y.name for y in hosts)
                    hosts.extend([h for h in that if h.name not in existing_hosts])
        return hosts

    def _match_one_pattern(self, pattern):
        """
        Takes a single pattern and returns a list of matching host names.
        Ignores intersection (&) and exclusion (!) specifiers.

        The pattern may be:

            1. A regex starting with ~, e.g. '~[abc]*'
            2. A shell glob pattern with ?/*/[chars]/[!chars], e.g. 'foo*'
            3. An ordinary word that matches itself only, e.g. 'foo'

        The pattern is matched using the following rules:

            1. If it's 'all', it matches all hosts in all groups.
            2. Otherwise, for each known group name:
                (a) if it matches the group name, the results include all hosts
                    in the group or any of its children.
                (b) otherwise, if it matches any hosts in the group, the results
                    include the matching hosts.

        This means that 'foo*' may match one or more groups (thus including all
        hosts therein) but also hosts in other groups.

        The built-in groups 'all' and 'ungrouped' are special. No pattern can
        match these group names (though 'all' behaves as though it matches, as
        described above). The word 'ungrouped' can match a host of that name,
        and patterns like 'ungr*' and 'al*' can match either hosts or groups
        other than all and ungrouped.

        If the pattern matches one or more group names according to these rules,
        it may have an optional range suffix to select a subset of the results.
        This is allowed only if the pattern is not a regex, i.e. '~foo[1]' does
        not work (the [1] is interpreted as part of the regex), but 'foo*[1]'
        would work if 'foo*' matched the name of one or more groups.

        Duplicate matches are always eliminated from the results.
        """

        if pattern[0] in ("&", "!"):
            pattern = pattern[1:]

        if pattern not in self._pattern_cache:
            (expr, slice) = self._split_subscript(pattern)
            hosts = self._enumerate_matches(expr)
            try:
                hosts = self._apply_subscript(hosts, slice)
            except IndexError:
                raise AnsibleError("No hosts matched the subscripted pattern '%s'" % pattern)
            self._pattern_cache[pattern] = hosts

        return self._pattern_cache[pattern]

    def _split_subscript(self, pattern):
        """
        Takes a pattern, checks if it has a subscript, and returns the pattern
        without the subscript and a (start,end) tuple representing the given
        subscript (or None if there is no subscript).

        Validates that the subscript is in the right syntax, but doesn't make
        sure the actual indices make sense in context.
        """

        # Do not parse regexes for enumeration info
        if pattern[0] == '~':
            return (pattern, None)

        # We want a pattern followed by an integer or range subscript.
        # (We can't be more restrictive about the expression because the
        # fnmatch semantics permit [\[:\]] to occur.)

        subscript = None
        m = PATTERN_WITH_SUBSCRIPT.match(pattern)
        if m:
            (pattern, idx, start, sep, end) = m.groups()
            if idx:
                subscript = (int(idx), None)
            else:
                if not end:
                    end = -1
                subscript = (int(start), int(end))
                if sep == '-':
                    display.warning("Use [x:y] inclusive subscripts instead of [x-y] which has been removed")

        return (pattern, subscript)

    def _apply_subscript(self, hosts, subscript):
        """
        Takes a list of hosts and a (start,end) tuple and returns the subset of
        hosts based on the subscript (which may be None to return all hosts).
        """

        if not hosts or not subscript:
            return hosts

        (start, end) = subscript

        if end:
            if end == -1:
                end = len(hosts) - 1
            return hosts[start:end + 1]
        else:
            return [hosts[start]]

    def _enumerate_matches(self, pattern):
        """
        Returns a list of host names matching the given pattern according to the
        rules explained above in _match_one_pattern.
        """

        results = []
        # check if pattern matches group
        matching_groups = self._match_list(self._inventory.groups, pattern)
        if matching_groups:
            for groupname in matching_groups:
                results.extend(self._inventory.groups[groupname].get_hosts())

        # check hosts if no groups matched or it is a regex/glob pattern
        if not matching_groups or pattern[0] == '~' or any(special in pattern for special in ('.', '?', '*', '[')):
            # pattern might match host
            matching_hosts = self._match_list(self._inventory.hosts, pattern)
            if matching_hosts:
                for hostname in matching_hosts:
                    results.append(self._inventory.hosts[hostname])

        if not results and pattern in C.LOCALHOST:
            # get_host autocreates implicit when needed
            implicit = self._inventory.get_host(pattern)
            if implicit:
                results.append(implicit)

        # Display warning if specified host pattern did not match any groups or hosts
        if not results and not matching_groups and pattern != 'all':
            msg = "Could not match supplied host pattern, ignoring: %s" % pattern
            display.debug(msg)
            if C.HOST_PATTERN_MISMATCH == 'warning':
                display.warning(msg)
            elif C.HOST_PATTERN_MISMATCH == 'error':
                raise AnsibleError(msg)
            # no need to write 'ignore' state

        return results

    def list_hosts(self, pattern="all"):
        """ return a list of hostnames for a pattern """
        # FIXME: cache?
        result = self.get_hosts(pattern)

        # allow implicit localhost if pattern matches and no other results
        if len(result) == 0 and pattern in C.LOCALHOST:
            result = [pattern]

        return result

    def list_groups(self):
        # FIXME: cache?
        return sorted(self._inventory.groups.keys())

    def restrict_to_hosts(self, restriction):
        """
        Restrict list operations to the hosts given in restriction.  This is used
        to batch serial operations in main playbook code, don't use this for other
        reasons.
        """
        if restriction is None:
            return
        elif not isinstance(restriction, list):
            restriction = [restriction]
        self._restriction = set(to_text(h.name) for h in restriction)

    def subset(self, subset_pattern):
        """
        Limits inventory results to a subset of inventory that matches a given
        pattern, such as to select a given geographic of numeric slice amongst
        a previous 'hosts' selection that only select roles, or vice versa.
        Corresponds to --limit parameter to ansible-playbook
        """
        if subset_pattern is None:
            self._subset = None
        else:
            subset_patterns = split_host_pattern(subset_pattern)
            results = []
            # allow Unix style @filename data
            for x in subset_patterns:
                if not x:
                    continue

                if x[0] == "@":
                    b_limit_file = to_bytes(x[1:])
                    if not os.path.exists(b_limit_file):
                        raise AnsibleError(u'Unable to find limit file %s' % b_limit_file)
                    if not os.path.isfile(b_limit_file):
                        raise AnsibleError(u'Limit starting with "@" must be a file, not a directory: %s' % b_limit_file)
                    with open(b_limit_file) as fd:
                        results.extend([to_text(l.strip()) for l in fd.read().split("\n")])
                else:
                    results.append(to_text(x))
            self._subset = results

    def remove_restriction(self):
        """ Do not restrict list operations """
        self._restriction = None

    def clear_pattern_cache(self):
        self._pattern_cache = {}
