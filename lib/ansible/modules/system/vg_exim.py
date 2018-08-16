#!/usr/bin/python
# GNU General Public License v3.0+

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author:
- Court Campbell
module: vg_exim
version_added: 2.7
short_description: Export/Import Linux LVM2 Volume Groups
description:
  - This module exports/imports volume group
options:
  vg:
    description:
    - The name of the volume group.
    required: True
    alias: name
  state:
    description:
    - state the volume group should be.
    choices: [ imported, exported ]
'''

EXAMPLES = '''
- name: Import vgtest
  vgexim:
    vg: vgtest
    state: imported

'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(type='str', required=True, aliases=['name']),
            state=dict(
                type='str',
                default=None,
                choices=['imported', 'exported']
            ),
        ),
    )

    result = {}
    vg = result['name'] = module.params['vg']
    state = result['state'] = module.params['state']

    if state == 'imported':
        # check if vg is already imported
        vgs_cmd = module.get_bin_path('vgs', True)
        rc, vg_state, err = module.run_command(
                               "%s --noheadings -o vg_exported %s"
                               % (vgs_cmd, vg)
                            )
        if rc != 0:
            module.fail_json(
                msg="Failed executing vgs command.", rc=rc, err=err
            )
        if 'exported' in vg_state:
            vgimport_cmd = module.get_bin_path('vgimport', True)
            rc, vgimport_out, err = module.run_command(
                                        "%s -v %s" % (vgimport_cmd, vg)
                                    )
            if rc != 0:
                module.fail_json(
                    msg="Failed executing vgimport command.", rc=rc, err=err
                )
            else:
                result['changed'] = True
        else:
            result['changed'] = False

    if state == 'exported':
        # check if vg is already exported
        vgs_cmd = module.get_bin_path('vgs', True)
        rc, vg_state, err = module.run_command(
                                "%s --noheadings -o vg_exported %s"
                                % (vgs_cmd, vg)
                            )
        if rc != 0:
            module.fail_json(
               msg="Failed executing vgs command.", rc=rc, err=err
            )
        if 'exported' in vg_state:
            result['changed'] = False
        else:
            vgexport_cmd = module.get_bin_path('vgexport', True)
            rc, vgexport_out, err = module.run_command(
                                        "%s -v %s" % (vgexport_cmd, vg)
                                    )
            if rc != 0:
                module.fail_json(
                    msg="Failed executing vgexport command.", rc=rc, err=err
                )
            else:
                result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
