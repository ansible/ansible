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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from collections.abc import MutableMapping

from ansible.utils.vars import merge_hash


class AggregateStats:
    ''' holds stats about per-host activity during playbook runs '''

    def __init__(self):

        self.processed = {}
        self.failures = {}
        self.ok = {}
        self.dark = {}
        self.changed = {}
        self.skipped = {}
        self.rescued = {}
        self.ignored = {}

        # user defined stats, which can be per host or global
        self.custom = {}

    def increment(self, what, host):
        ''' helper function to bump a statistic '''

        self.processed[host] = 1
        prev = (getattr(self, what)).get(host, 0)
        getattr(self, what)[host] = prev + 1

    def decrement(self, what, host):
        _what = getattr(self, what)
        try:
            if _what[host] - 1 < 0:
                # This should never happen, but let's be safe
                raise KeyError("Don't be so negative")
            _what[host] -= 1
        except KeyError:
            _what[host] = 0

    def summarize(self, host):
        ''' return information about a particular host '''

        return dict(
            ok=self.ok.get(host, 0),
            failures=self.failures.get(host, 0),
            unreachable=self.dark.get(host, 0),
            changed=self.changed.get(host, 0),
            skipped=self.skipped.get(host, 0),
            rescued=self.rescued.get(host, 0),
            ignored=self.ignored.get(host, 0),
        )

    def set_custom_stats(self, which, what, host=None):
        ''' allow setting of a custom stat'''

        if host is None:
            host = '_run'
        if host not in self.custom:
            self.custom[host] = {which: what}
        else:
            self.custom[host][which] = what

    def update_custom_stats(self, which, what, host=None):
        ''' allow aggregation of a custom stat'''

        if host is None:
            host = '_run'
        if host not in self.custom or which not in self.custom[host]:
            return self.set_custom_stats(which, what, host)

        # mismatching types
        if not isinstance(what, type(self.custom[host][which])):
            return None

        if isinstance(what, MutableMapping):
            self.custom[host][which] = merge_hash(self.custom[host][which], what)
        else:
            # let overloaded + take care of other types
            self.custom[host][which] += what
