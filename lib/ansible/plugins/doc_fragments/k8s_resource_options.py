# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Options for providing an object configuration


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  resource_definition:
    description:
    - "Provide a valid YAML definition (either as a string, list, or dict) for an object when creating or updating. NOTE: I(kind), I(api_version), I(name),
      and I(namespace) will be overwritten by corresponding values found in the provided I(resource_definition)."
    aliases:
    - definition
    - inline
  src:
    description:
    - "Provide a path to a file containing a valid YAML definition of an object or objects to be created or updated. Mutually
      exclusive with I(resource_definition). NOTE: I(kind), I(api_version), I(name), and I(namespace) will be
      overwritten by corresponding values found in the configuration read in from the I(src) file."
    - Reads from the local file system. To read from the Ansible controller's file system, including vaulted files, use the file lookup
      plugin or template lookup plugin, combined with the from_yaml filter, and pass the result to
      I(resource_definition). See Examples below.
    type: path
'''
