#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vg_exim
author:
- Court Campbell
version_added: "2.7"
short_description: Export/Import Linux LVM2 Volume Groups
description:
  - This module exports/imports volume group
options:
  vg:
    description:
    - The name of the volume group.
    required: True
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

RETURN = '''
name:
    description: name of vg
    returned: success
    type: string
state:
    description: imported or exported value
    returned: success
    type: string
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(type='str', required=True),
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
            # check if vg has any active lvs, if so deactivate them
            lvs_cmd = module.get_bin_path('lvs', True)
            rc, lv_active, err = module.run_command(
                                 "%s --noheadings --rows -o lv_active %s"
                                 % (lvs_cmd, vg)
                                 )
            if rc != 0:
                module.fail_json(
                    msg="Failed getting lvs info for volume group.",
                    rc=rc, err=err
                )
            if 'active' in lv_active:
                vgchange_cmd = module.get_bin_path('vgchange', True)
                rc, lv_state, err = module.run_command(
                                     "%s -a n %s"
                                     % (vgchange_cmd, vg)
                                     )
                if rc != 0:
                    module.fail_json(
                        msg="Failed to deactive volume group.",
                        rc=rc, err=err
                    )
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
