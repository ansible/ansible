# (c) 2013, Herby Gillot <herby.gillot@gmail.com>
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

import ansible.utils as utils
import ansible.errors as errors
from itertools import cycle, izip


class LookupModule(object):
    """
    Allocate a list of items over another list of "slots".

    "Slots" are really just another list of items.

    This will round-robin distribute items into slots, and returns a list
    of each item and its assigned slot as a dict:

    ['a', 'b'], [1, 2, 3, 4] -> [
        {'current': 1, 'slot' 'a'},
        {'current': 2, 'slot' 'b'},
        {'current': 3, 'slot' 'a'},
        {'current': 4, 'slot' 'b'},
    ]

    Can be accessed in Ansible as item.current, item.slot
    """

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir
        self.plugin_name = 'allocate'

    def run(self, terms, inject=None, **kwargs):

        slots = utils.listify_lookup_plugin_terms(
            terms.get('slots'), self.basedir, inject)

        items = utils.listify_lookup_plugin_terms(
            terms.get('items'), self.basedir, inject)

        if not items:
            return []

        if not slots:
            raise errors.AnsibleError(
                'Missing "slots" parameter: '
                'with_{} requires "slots" to be a list (over which the list '
                'of "items" are allocated)'.format(self.plugin_name))

        idict = lambda item: {'current': item[1], 'slot': item[0]}
        return [idict(x) for x in izip(*[cycle(slots), items])]
