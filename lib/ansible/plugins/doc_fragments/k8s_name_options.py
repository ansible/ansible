# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Options for selecting or identifying a specific K8s object


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  api_version:
    description:
    - Use to specify the API version. Use to create, delete, or discover an object without providing a full
      resource definition. Use in conjunction with I(kind), I(name), and I(namespace) to identify a
      specific object. If I(resource definition) is provided, the I(apiVersion) from the I(resource_definition)
      will override this option.
    type: str
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
    type: str
  name:
    description:
    - Use to specify an object name. Use to create, delete, or discover an object without providing a full
      resource definition. Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a
      specific object. If I(resource definition) is provided, the I(metadata.name) value from the
      I(resource_definition) will override this option.
    type: str
  namespace:
    description:
    - Use to specify an object namespace. Useful when creating, deleting, or discovering an object without
      providing a full resource definition. Use in conjunction with I(api_version), I(kind), and I(name)
      to identify a specfic object. If I(resource definition) is provided, the I(metadata.namespace) value
      from the I(resource_definition) will override this option.
    type: str
'''
