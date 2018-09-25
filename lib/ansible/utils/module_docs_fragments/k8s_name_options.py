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

# Options for selecting or identifying a specific K8s object


class ModuleDocFragment(object):

    DOCUMENTATION = '''
options:
  api_version:
    description:
    - Use to specify the API version. Use to create, delete, or discover an object without providing a full
      resource definition. Use in conjunction with I(kind), I(name), and I(namespace) to identify a
      specific object. If I(resource definition) is provided, the I(apiVersion) from the I(resource_definition)
      will override this option.
    default: v1
    aliases:
    - api
    - version
  kind:
    description:
    - Use to specify an object model. Use to create, delete, or discover an object without providing a full
      resource definition. Use in conjunction with I(api_version), I(name), and I(namespace) to identify a
      specific object. If I(resource definition) is provided, the I(kind) from the I(resource_definition)
      will override this option.
  name:
    description:
    - Use to specify an object name. Use to create, delete, or discover an object without providing a full
      resource definition. Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a
      specific object. If I(resource definition) is provided, the I(metadata.name) value from the
      I(resource_definition) will override this option.
  namespace:
    description:
    - Use to specify an object namespace. Useful when creating, deleting, or discovering an object without
      providing a full resource definition. Use in conjunction with I(api_version), I(kind), and I(name)
      to identify a specfic object. If I(resource definition) is provided, the I(metadata.namespace) value
      from the I(resource_definition) will override this option.
'''
