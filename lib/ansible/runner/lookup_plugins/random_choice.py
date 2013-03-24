# (c) 2013, Michael DeHaan <michael.dehaan@gmail.com>
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

import random

# useful for introducing chaos ... or just somewhat reasonably fair selection
# amongst available mirrors
#
#    tasks:
#        - debug: msg=$item
#          with_random_choice:
#             - one
#             - two 
#             - three

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, **kwargs):
        if isinstance(terms, basestring):
            terms = [ terms ]
        return [ random.choice(terms) ]

