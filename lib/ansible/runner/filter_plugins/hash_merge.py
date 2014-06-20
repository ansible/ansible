# (c) 2014, Leonid Evdokimov <leon@darkk.net.ru>
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

import itertools

from ansible import utils
from ansible import errors

# These are two possible behaviours expressed by `ansible.utils.combine_vars`.

def hash_merge(*terms):
    for t in terms:
        if not isinstance(t, dict):
            raise errors.AnsibleFilterError("|hash_merge expects dictionaries, got " + repr(t))

    return reduce(utils.merge_hash, terms)

def hash_replace(*terms):
    for t in terms:
        if not isinstance(t, dict):
            raise errors.AnsibleFilterError("|hash_replace expects dictionaries, got " + repr(t))

    return dict(itertools.chain(*map(dict.iteritems, terms)))

class FilterModule(object):
    ''' Ansible jinja2 filter to avoid global hash_behaviour=merge when it's needed '''

    def filters(self):
        return {
            'hash_merge': hash_merge,
            'hash_replace': hash_replace,
        }
