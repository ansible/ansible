#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: ucs_vhba_template
short_description: Configures vHBA templates on Cisco UCS Manager
description:
- Configures vHBA templates on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify vHBA templates are present and will create if needed.
    - If C(absent), will verify vHBA templates are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the virtual HBA template.
    - This name can be between 1 and 16 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the template is created.
    required: yes
  description:
    description:
    - A user-defined description of the template.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
  fabric:
    description:
    - The Fabric ID field.
    - The name of the fabric interconnect that vHBAs created with this template are associated with.
    choices: [A, B]
    default: A
  redundancy_type:
    description:
    - The Redundancy Type used for template pairing from the Primary or Secondary redundancy template.
    - "primary — Creates configurations that can be shared with the Secondary template."
    - Any other shared changes on the Primary template are automatically synchronized to the Secondary template.
    - "secondary — All shared configurations are inherited from the Primary template."
    - "none - Legacy vHBA template behavior. Select this option if you do not want to use redundancy."
    choices: [none, primary, secondary]
    default: none
  vsan:
    description:
    - The VSAN to associate with vHBAs created from this template.
    default: default
  template_type:
    description:
    - The Template Type field.
    - "This can be one of the following:"
    - "initial-template — vHBAs created from this template are not updated if the template changes."
    - "updating-template - vHBAs created from this template are updated if the template changes."
    choices: [initial-template, updating-template]
    default: initial-template
  max_data:
    description:
    - The Max Data Field Size field.
    - The maximum size of the Fibre Channel frame payload bytes that the vHBA supports.
    - Enter an string between '256' and '2112'.
    default: '2048'
  wwpn_pool:
    description:
    - The WWPN pool that a vHBA created from this template uses to derive its WWPN address.
    default: default
  qos_policy:
    description:
    - The QoS policy that is associated with vHBAs created from this template.
  pin_group:
    description:
    - The SAN pin group that is associated with vHBAs created from this template.
  stats_policy:
    description:
    - The statistics collection policy that is associated with vHBAs created from this template.
    default: default
  org_dn:
    description:
    - Org dn (distinguished name)
    default: org-root
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.5'
'''

EXAMPLES = r'''
- name: Configure vHBA template
  ucs_vhba_template:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vHBA-A
    fabric: A
    vsan: VSAN-A
    wwpn_pool: WWPN-Pool-A

- name: Remote vHBA template
  ucs_vhba_template:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: vHBA-A
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str'),
        descr=dict(type='str'),
        fabric=dict(type='str', default='A', choices=['A', 'B']),
        redundancy_type=dict(type='str', default='none', choices=['none', 'primary', 'secondary']),
        vsan=dict(type='str', default='default'),
        template_type=dict(type='str', default='initial-template', choices=['initial-template', 'updating-template']),
        max_data=dict(type='str', default='2048'),
        wwpn_pool=dict(type='str', default='default'),
        qos_policy=dict(type='str'),
        pin_group=dict(type='str'),
        stats_policy=dict(type='str', default='default'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        vhba_template_list=dict(type='list'),
    )

    # Note that use of vhba_template_list is an experimental feature which allows multiple resource updates with a single UCSM connection.
    # Support for vhba_template_list may change or be removed once persistent UCS connections are supported.
    # Either vhba_template_list or name is required (user can specify either a list of single resource).

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['vhba_template_list', 'name']
        ],
        mutually_exclusive=[
            ['vhba_template_list', 'name']
        ],
    )
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.vnic.VnicSanConnTempl import VnicSanConnTempl
    from ucsmsdk.mometa.vnic.VnicFcIf import VnicFcIf

    changed = False
    try:
        # Only documented use is a single resource, but to also support experimental
        # feature allowing multiple updates all params are converted to a vhba_template_list below.

        if module.params['vhba_template_list']:
            # directly use the list (single resource and list are mutually exclusive
            vhba_template_list = module.params['vhba_template_list']
        else:
            # single resource specified, create list from the current params
            vhba_template_list = [module.params]
        for vhba_template in vhba_template_list:
            mo_exists = False
            props_match = False
            # set default params.  Done here to set values for lists which can't be done in the argument_spec
            if not vhba_template.get('descr'):
                vhba_template['descr'] = ''
            if not vhba_template.get('fabric'):
                vhba_template['fabric'] = 'A'
            if not vhba_template.get('redundancy_type'):
                vhba_template['redundancy_type'] = 'none'
            if not vhba_template.get('vsan'):
                vhba_template['vsan'] = 'default'
            if not vhba_template.get('template_type'):
                vhba_template['template_type'] = 'initial-template'
            if not vhba_template.get('max_data'):
                vhba_template['max_data'] = '2048'
            if not vhba_template.get('wwpn_pool'):
                vhba_template['wwpn_pool'] = 'default'
            if not vhba_template.get('qos_policy'):
                vhba_template['qos_policy'] = ''
            if not vhba_template.get('pin_group'):
                vhba_template['pin_group'] = ''
            if not vhba_template.get('stats_policy'):
                vhba_template['stats_policy'] = 'default'
            # dn is <org_dn>/san-conn-templ-<name>
            dn = module.params['org_dn'] + '/san-conn-templ-' + vhba_template['name']

            mo = ucs.login_handle.query_dn(dn)
            if mo:
                mo_exists = True
                # check top-level mo props
                kwargs = dict(descr=vhba_template['descr'])
                kwargs['switch_id'] = vhba_template['fabric']
                kwargs['redundancy_pair_type'] = vhba_template['redundancy_type']
                kwargs['templ_type'] = vhba_template['template_type']
                kwargs['max_data_field_size'] = vhba_template['max_data']
                kwargs['ident_pool_name'] = vhba_template['wwpn_pool']
                kwargs['qos_policy_name'] = vhba_template['qos_policy']
                kwargs['pin_to_group_name'] = vhba_template['pin_group']
                kwargs['stats_policy_name'] = vhba_template['stats_policy']
                if (mo.check_prop_match(**kwargs)):
                    # top-level props match, check next level mo/props
                    child_dn = dn + '/if-default'
                    mo_1 = ucs.login_handle.query_dn(child_dn)
                    if mo_1:
                        kwargs = dict(name=vhba_template['vsan'])
                        if (mo_1.check_prop_match(**kwargs)):
                            props_match = True

            if module.params['state'] == 'absent':
                # mo must exist but all properties do not have to match
                if mo_exists:
                    if not module.check_mode:
                        ucs.login_handle.remove_mo(mo)
                        ucs.login_handle.commit()
                    changed = True
            else:
                if not props_match:
                    if not module.check_mode:
                        # create if mo does not already exist
                        mo = VnicSanConnTempl(
                            parent_mo_or_dn=module.params['org_dn'],
                            name=vhba_template['name'],
                            descr=vhba_template['descr'],
                            switch_id=vhba_template['fabric'],
                            redundancy_pair_type=vhba_template['redundancy_type'],
                            templ_type=vhba_template['template_type'],
                            max_data_field_size=vhba_template['max_data'],
                            ident_pool_name=vhba_template['wwpn_pool'],
                            qos_policy_name=vhba_template['qos_policy'],
                            pin_to_group_name=vhba_template['pin_group'],
                            stats_policy_name=vhba_template['stats_policy'],
                        )

                        mo_1 = VnicFcIf(
                            parent_mo_or_dn=mo,
                            name=vhba_template['vsan'],
                        )

                        ucs.login_handle.add_mo(mo, True)
                        ucs.login_handle.commit()
                    changed = True

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
