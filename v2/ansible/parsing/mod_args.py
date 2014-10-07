# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

import exceptions

class ModuleArgsParser(object):

    """
    There are several ways a module and argument set can be expressed:

    # legacy form (for a shell command)
    - action: shell echo hi
   
    # common shorthand for local actions vs delegate_to
    - local_action: shell echo hi

    # most commonly:
    - copy: src=a dest=b
      
    # legacy form
    - action: copy src=a dest=b

    # complex args form, for passing structured data
    - copy: 
        src: a
        dest: b

    # gross, but technically legal
    - action:
        module: copy
        args: 
          src: a
          dest: b

    This class exists so other things don't have to remember how this
    all works.  Pass it "part1" and "part2", and the parse function
    will tell you about the modules in a predictable way.
    """

    def __init__(self):
        pass

    def parse(self, thing1, thing2):
        raise exceptions.NotImplementedError


