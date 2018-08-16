# Copyright (c) 2015 Ansible, Inc
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


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = '''
options:
    validate:
      description:
       - The validation command to run before copying into place. The path to the file to
         validate is passed in via '%s' which must be present as in the example below.
         The command is passed securely so shell features like expansion and pipes won't work.
'''
