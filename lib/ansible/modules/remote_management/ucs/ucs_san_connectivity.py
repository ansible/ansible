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
  san_connectivity_list:
    description:
    - List of SAN Connectivity Policies.  Allows multiple resource updates with a single UCSM connection.
    - Either san_connectivity_list or name is required (user can specify either a list or single resource)
    - See descriptions for name and other options for information on specifying each list element
  name:
    description:
    - Name of the SAN Connectivity Policy
    - If specifying a single SAN Connectivity Policy, name is required
  descr:
    description:
    - Description for the SAN Connectivity Policy
  wwnn_pool:
    description:
    - WWNN Pool name
    default: default
  vhba_list:
    description:
    - List of vHBAs contained in the SAN Connectivity Policy
    - Each list element has the following suboptions
    - name (Name of the vHBA (required))
    - vhba_template (vHBA template (required))
    - adapter_policy ('' (default), Linux, Solaris, VMware, Windows, WindowsBoot, or default)
    - order (string specifying vHBA assignment order (unspecified (default), '1', '2', etc.)
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
- name: Configure multiple SAN Connectivity Policies
  ucs_san_connectivity:
    hostname: 172.16.143.150
    username: admin
    password: password
    san_connectivity_list:
    - name: Cntr-FC-Boot
      wwnn_pool: WWNN-Pool
      vhba_list:
      - name: Fabric-A
        vhba_template: vHBA-Template-A
        adapter_policy: Linux
      - name: Fabric-B
        vhba_template: vHBA-Template-B
        adapter_policy: Linux

- name: Configure single SAN Connectivity Policy
  ucs_san_connectivity:
    hostname: 172.16.143.150
    username: admin
    name: Cntr-FC-Boot
    wwnn_pool: WWNN-Pool
    vhba_list:
    - name: Fabric-A
      vhba_template: vHBA-Template-A
      adapter_policy: Linux
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(san_connectivity_list=dict(type='list'),
                         org_dn=dict(type='str', default='org-root'),
                         name=dict(type='str'),
                         descr=dict(type='str'),
                         wwnn_pool=dict(type='str', default='default'),
                         vhba_list=dict(type='list'),
                         state=dict(type='str', default='present', choices=['present', 'absent']))
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           required_one_of=[
                               ['san_connectivity_list', 'name']
                           ],
                           mutually_exclusive=[
                               ['san_connectivity_list', 'name']
                           ])
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.vnic.VnicSanConnPolicy import VnicSanConnPolicy
    from ucsmsdk.mometa.vnic.VnicFcNode import VnicFcNode
    from ucsmsdk.mometa.vnic.VnicFc import VnicFc
    from ucsmsdk.mometa.vnic.VnicFcIf import VnicFcIf

    changed = False
    try:
        if module.params['san_connectivity_list']:
            # directly use the list (single resource and list are mutually exclusive
            san_connectivity_list = module.params['san_connectivity_list']
        else:
            # single resource specified, create list from the current params
            san_connectivity_list = [module.params]
        for san_connectivity in san_connectivity_list:
            exists = False
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
                # check top-level mo props
                kwargs = {}
                kwargs['descr'] = san_connectivity['descr']
                if (mo.check_prop_match(**kwargs)):
                    # top-level props match, check next level mo/props
                    # vnicFcNode object
                    child_dn = dn + '/fc-node'
                    mo_1 = ucs.login_handle.query_dn(child_dn)
                    if mo_1:
                        kwargs = {}
                        kwargs['ident_pool_name'] = san_connectivity['wwnn_pool']
                        if (mo_1.check_prop_match(**kwargs)):
                            if not san_connectivity.get('vhba_list'):
                                exists = True
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
                                        exists = True

            if module.params['state'] == 'absent':
                if exists:
                    if not module.check_mode:
                        ucs.login_handle.remove_mo(mo)
                        ucs.login_handle.commit()
                    changed = True
            else:
                if not exists:
                    if not module.check_mode:
                        # create if mo does not already exist
                        mo = VnicSanConnPolicy(parent_mo_or_dn=module.params['org_dn'],
                                               name=san_connectivity['name'],
                                               descr=san_connectivity['descr'])
                        mo_1 = VnicFcNode(parent_mo_or_dn=mo,
                                          ident_pool_name=san_connectivity['wwnn_pool'],
                                          addr='pool-derived')
                        if san_connectivity.get('vhba_list'):
                            for vhba in san_connectivity['vhba_list']:
                                mo_2 = VnicFc(parent_mo_or_dn=mo,
                                              name=vhba['name'],
                                              adaptor_profile_name=vhba['adapter_policy'],
                                              nw_templ_name=vhba['vhba_template'],
                                              order=vhba['order'])
                                mo_2_1 = VnicFcIf(parent_mo_or_dn=mo_2, name='default')

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
