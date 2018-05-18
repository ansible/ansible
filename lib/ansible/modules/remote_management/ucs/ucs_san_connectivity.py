#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ucs_san_connectivity
short_description: Configures SAN Connectivity Policies on Cisco UCS Manager
description:
- Configures SAN Connectivity Policies on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify SAN Connectivity Policies are present and will create if needed.
    - If C(absent), will verify SAN Connectivity Policies are absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the SAN Connectivity Policy.
    - This name can be between 1 and 16 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the policy is created.
    required: yes
  description:
    description:
    - A description of the policy.
    - Cisco recommends including information about where and when to use the policy.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
  wwnn_pool:
    description:
    - Name of the WWNN pool to use for WWNN assignment.
    default: default
  vhba_list:
    description:
    - List of vHBAs used by the SAN Connectivity Policy.
    - vHBAs used by the SAN Connectivity Policy must be created from a vHBA template.
    - "Each list element has the following suboptions:"
    - "= name"
    - "  The name of the virtual HBA (required)."
    - "= vhba_template"
    - "  The name of the virtual HBA template (required)."
    - "- adapter_policy"
    - "  The name of the Fibre Channel adapter policy."
    - "  A user defined policy can be used, or one of the system defined policies (default, Linux, Solaris, VMware, Windows, WindowsBoot)"
    - "  [Default: default]"
    - "- order"
    - "  String specifying the vHBA assignment order (e.g., '1', '2')."
    - "  [Default: unspecified]"
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
- name: Configure SAN Connectivity Policy
  ucs_san_connectivity:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: Cntr-FC-Boot
    wwnn_pool: WWNN-Pool
    vhba_list:
    - name: Fabric-A
      vhba_template: vHBA-Template-A
      adapter_policy: Linux
    - name: Fabric-B
      vhba_template: vHBA-Template-B
      adapter_policy: Linux

- name: Remove SAN Connectivity Policy
  ucs_san_connectivity:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: Cntr-FC-Boot
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
        wwnn_pool=dict(type='str', default='default'),
        vhba_list=dict(type='list'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        san_connectivity_list=dict(type='list'),
    )

    # Note that use of san_connectivity_list is an experimental feature which allows multiple resource updates with a single UCSM connection.
    # Support for san_connectivity_list may change or be removed once persistent UCS connections are supported.
    # Either san_connectivity_list or name is required (user can specify either a list or single resource).

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['san_connectivity_list', 'name'],
        ],
        mutually_exclusive=[
            ['san_connectivity_list', 'name'],
        ],
    )
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.vnic.VnicSanConnPolicy import VnicSanConnPolicy
    from ucsmsdk.mometa.vnic.VnicFcNode import VnicFcNode
    from ucsmsdk.mometa.vnic.VnicFc import VnicFc
    from ucsmsdk.mometa.vnic.VnicFcIf import VnicFcIf

    changed = False
    try:
        # Only documented use is a single resource, but to also support experimental
        # feature allowing multiple updates all params are converted to a san_connectivity_list below.

        if module.params['san_connectivity_list']:
            # directly use the list (single resource and list are mutually exclusive
            san_connectivity_list = module.params['san_connectivity_list']
        else:
            # single resource specified, create list from the current params
            san_connectivity_list = [module.params]
        for san_connectivity in san_connectivity_list:
            mo_exists = False
            props_match = False
            # set default params.  Done here to set values for lists which can't be done in the argument_spec
            if not san_connectivity.get('descr'):
                san_connectivity['descr'] = ''
            if not san_connectivity.get('wwnn_pool'):
                san_connectivity['wwnn_pool'] = 'default'
            if san_connectivity.get('vhba_list'):
                for vhba in san_connectivity['vhba_list']:
                    if not vhba.get('adapter_policy'):
                        vhba['adapter_policy'] = ''
                    if not vhba.get('order'):
                        vhba['order'] = 'unspecified'
            # dn is <org_dn>/san-conn-pol-<name>
            dn = module.params['org_dn'] + '/san-conn-pol-' + san_connectivity['name']

            mo = ucs.login_handle.query_dn(dn)
            if mo:
                mo_exists = True
                # check top-level mo props
                kwargs = dict(descr=san_connectivity['descr'])
                if (mo.check_prop_match(**kwargs)):
                    # top-level props match, check next level mo/props
                    # vnicFcNode object
                    child_dn = dn + '/fc-node'
                    mo_1 = ucs.login_handle.query_dn(child_dn)
                    if mo_1:
                        kwargs = dict(ident_pool_name=san_connectivity['wwnn_pool'])
                        if (mo_1.check_prop_match(**kwargs)):
                            if not san_connectivity.get('vhba_list'):
                                props_match = True
                            else:
                                # check vnicFc props
                                for vhba in san_connectivity['vhba_list']:
                                    child_dn = dn + '/fc-' + vhba['name']
                                    mo_2 = ucs.login_handle.query_dn(child_dn)
                                    kwargs = {}
                                    kwargs['adaptor_profile_name'] = vhba['adapter_policy']
                                    kwargs['order'] = vhba['order']
                                    kwargs['nw_templ_name'] = vhba['vhba_template']
                                    if (mo_2.check_prop_match(**kwargs)):
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
                        mo = VnicSanConnPolicy(
                            parent_mo_or_dn=module.params['org_dn'],
                            name=san_connectivity['name'],
                            descr=san_connectivity['descr'],
                        )
                        mo_1 = VnicFcNode(
                            parent_mo_or_dn=mo,
                            ident_pool_name=san_connectivity['wwnn_pool'],
                            addr='pool-derived',
                        )
                        if san_connectivity.get('vhba_list'):
                            for vhba in san_connectivity['vhba_list']:
                                mo_2 = VnicFc(
                                    parent_mo_or_dn=mo,
                                    name=vhba['name'],
                                    adaptor_profile_name=vhba['adapter_policy'],
                                    nw_templ_name=vhba['vhba_template'],
                                    order=vhba['order'],
                                )
                                mo_2_1 = VnicFcIf(
                                    parent_mo_or_dn=mo_2,
                                    name='default',
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
