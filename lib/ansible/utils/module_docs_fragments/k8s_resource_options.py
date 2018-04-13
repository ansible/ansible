#
#  Copyright 2018 Red Hat | Ansible
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

# Options for providing an object configuration


class ModuleDocFragment(object):

    DOCUMENTATION = '''
options:
  resource_definition:
    description:
    - "Provide a valid YAML definition for an object when creating or updating. NOTE: I(kind), I(api_version), I(name),
      and I(namespace) will be overwritten by corresponding values found in the provided I(resource_definition)."
    aliases:
    - definition
    - inline
  src:
    description:
    - "Provide a path to a file containing a valid YAML definition of an object to be created or updated. Mutually
      exclusive with I(resource_definition). NOTE: I(kind), I(api_version), I(name), and I(namespace) will be
      overwritten by corresponding values found in the configuration read in from the I(src) file."
    - Reads from the local file system. To read from the Ansible controller's file system, use the file lookup
      plugin or template lookup plugin, combined with the from_yaml filter, and pass the result to
      I(resource_definition). See Examples below.
'''
