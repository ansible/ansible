#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Gregory Shulov (gregory.shulov@gmail.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: infini_export
version_added: 2.3
short_description: Create, Delete or Modify NFS Exports on Infinibox
description:
    - This module creates, deletes or modifies NFS exports on Infinibox.
author: Gregory Shulov (@GR360RY)
options:
  name:
    description:
      - Export name. Should always start with C(/). (ex. name=/data)
    aliases: ['export', 'path']
    required: true
  state:
    description:
      - Creates/Modifies export when present and removes when absent.
    required: false
    default: "present"
    choices: [ "present", "absent" ]
  inner_path:
    description:
      - Internal path of the export.
    default: "/"
  client_list:
    description:
      - List of dictionaries with client entries. See examples.
        Check infini_export_client module to modify individual NFS client entries for export.
    default: "All Hosts(*), RW, no_root_squash: True"
    required: false
  filesystem:
    description:
      - Name of exported file system.
    required: true
extends_documentation_fragment:
    - infinibox
requirements:
    - munch
'''

EXAMPLES = '''
- name: Export bar filesystem under foo pool as /data
  infini_export:
    name: /data01
    filesystem: foo
    user: admin
    password: secret
    system: ibox001

- name: Export and specify client list explicitly
  infini_export:
    name: /data02
    filesystem: foo
    client_list:
      - client: 192.168.0.2
        access: RW
        no_root_squash: True
      - client: 192.168.0.100
        access: RO
        no_root_squash: False
      - client: 192.168.0.10-192.168.0.20
        access: RO
        no_root_squash: False
    system: ibox001
    user: admin
    password: secret
'''

RETURN = '''
'''
try:
    from munch import unmunchify
    HAS_MUNCH = True
except ImportError:
    HAS_MUNCH = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.infinibox import HAS_INFINISDK, api_wrapper, get_system, infinibox_argument_spec


def transform(d):
    return frozenset(d.items())


@api_wrapper
def get_filesystem(module, system):
    """Return Filesystem or None"""
    try:
        return system.filesystems.get(name=module.params['filesystem'])
    except:
        return None


@api_wrapper
def get_export(module, filesystem, system):
    """Retrun export if found. When not found return None"""

    export = None
    exports_to_list = system.exports.to_list()

    for e in exports_to_list:
        if e.get_export_path() == module.params['name']:
            export = e
            break

    return export


@api_wrapper
def update_export(module, export, filesystem, system):
    """ Create new filesystem or update existing one"""

    changed = False

    name = module.params['name']
    client_list = module.params['client_list']

    if export is None:
        if not module.check_mode:
            export = system.exports.create(export_path=name, filesystem=filesystem)
            if client_list:
                export.update_permissions(client_list)
        changed = True
    else:
        if client_list:
            if set(map(transform, unmunchify(export.get_permissions()))) != set(map(transform, client_list)):
                if not module.check_mode:
                    export.update_permissions(client_list)
                changed = True

    module.exit_json(changed=changed)


@api_wrapper
def delete_export(module, export):
    """ Delete file system"""
    if not module.check_mode:
        export.delete()
    module.exit_json(changed=True)


def main():
    argument_spec = infinibox_argument_spec()
    argument_spec.update(
        dict(
            name        = dict(required=True),
            state       = dict(default='present', choices=['present', 'absent']),
            filesystem  = dict(required=True),
            client_list = dict(type='list')
        )
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)

    if not HAS_INFINISDK:
        module.fail_json(msg='infinisdk is required for this module')
    if not HAS_MUNCH:
        module.fail_json(msg='the python munch library is required for this module')

    state      = module.params['state']
    system     = get_system(module)
    filesystem = get_filesystem(module, system)
    export     = get_export(module, filesystem, system)

    if filesystem is None:
        module.fail_json(msg='Filesystem {} not found'.format(module.params['filesystem']))

    if state == 'present':
        update_export(module, export, filesystem, system)
    elif export and state == 'absent':
        delete_export(module, export)
    elif export is None and state == 'absent':
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
