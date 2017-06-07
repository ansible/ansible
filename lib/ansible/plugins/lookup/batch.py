# (c) 2017, David Moreau Simard <dmsimard@redhat.com>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.lookup import LookupBase
from jinja2.filters import do_batch


class LookupModule(LookupBase):
    """
    Given a list, returns a list of lists with a max length defined by the
    batch_lookup_size variable. Defaults to 5.
    http://jinja.pocoo.org/docs/2.9/templates/#batch
    """
    def run(self, terms, **kwargs):
        try:
            batch_size = int(kwargs['variables'].get('batch_lookup_size', 5))
        except KeyError:
            batch_size = 5
        except ValueError:
            raise ValueError('batch_lookup_size needs to be a number')
        batch = []
        for subset in do_batch(terms, batch_size):
            batch.append(subset)
        return batch
