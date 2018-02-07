#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Bruno Calogero <brunocalogero@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_static_binding_to_epg
short_description: Bind static paths to EPGs on Cisco ACI fabrics (fv:RsPathAtt)
description:
- Bind static paths to EPGs on Cisco ACI fabrics.
- More information from the internal APIC classes I(fv:RsPathAtt) at
  U(https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Bruno Calogero (@brunocalogero)
version_added: '2.5'
notes:
- The C(tenant), C(ap), C(epg) used must exist before using this module in your playbook.
  The M(aci_tenant), M(aci_ap), M(aci_epg) modules can be used for this.
options:
  tenant:
    description:
    - Name of an existing tenant.
    aliases: [ tenant_name ]
  ap:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    aliases: [ app_profile, app_profile_name ]
  epg:
    description:
    - The name of the end point group.
    aliases: [ epg_name ]
  encap_id:
    description:
    - The encapsulation ID associating the C(epg) with the interface path.
    - This acts as the secondary C(encap_id) when using micro-segmentation.
    aliases: [ vlan, vlan_id ]
    choices: [ Valid encap IDs for specified encap, currently 1 to 4096 ]
  primary_encap_id:
    description:
    - Determines the primary encapsulation ID associating the C(epg)
      with the interface path when using micro-segmentation.
    aliases: [ primary_vlan, primary_vlan_id ]
    choices: [ Valid encap IDs for specified encap, currently 1 to 4096 ]
  deploy_immediacy:
    description:
    - The Deployement Immediacy of Static EPG on PC, VPC or Interface.
    - The APIC defaults the Deployement Immediacy to C(lazy).
    choices: [ immediate, lazy ]
    default: lazy
  interface_mode:
    description:
    - Determines how layer 2 tags will be read from and added to frames.
    - The APIC defaults the mode to C(trunk).
    choices: [ access, trunk, 802.1p ]
    default: trunk
    aliases: [ mode, interface_mode_name ]
  interface_type:
    description:
    - The type of interface for the static EPG deployement.
    - The APIC defaults the C(interface_type) to C(switch_port).
    choices: [ switch_port, vpc, port_channel, fex ]
    default: switch_port
  pod:
    description:
    - The pod number part of the tDn.
    - C(pod) is usually an integer below 10.
    aliases: [ pod_number ]
  leafs:
    description:
    - The switch ID(s) that the C(interface) belongs to.
    - When C(interface_type) is C(switch_port), C(port_channel), or C(fex), then C(leafs) is a string of the leaf ID.
    - When C(interface_type) is C(vpc), then C(leafs) is a list with both leaf IDs.
    aliases: [ paths, leaves, nodes, switches ]
  interface:
    description:
    - The C(interface) string value part of the tDn.
    - Usually a policy group like "test-IntPolGrp" or an interface of the following format "1/7" depending on C(interface_type).
  extpaths:
    description:
    - The C(extpaths) integer value part of the tDn.
    - C(extpaths) is only used if C(interface_type) is C(fex).
    - Usually something like '1011'.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Deploy Static Path for EPG
  aci_static_binding_to_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: accessport-code-cert
    ap: accessport_code_app
    epg: accessport_epg1
    encap_id: 222
    deploy_immediacy: lazy
    interface_mode: access
    interface_type: switch_port
    pod: 1
    leafs: 101
    interface: '1/7'
    state: present
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

# TODO: change 'deploy_immediacy' to 'resolution_immediacy' (as seen in aci_epg_to_domain)?


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        tenant=dict(type='str', aliases=['tenant_name']),
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name']),
        epg=dict(type='str', aliases=['epg_name']),
        encap_id=dict(type='int', aliases=['vlan', 'vlan_id']),
        primary_encap_id=dict(type='int', aliases=['primary_vlan', 'primary_vlan_id']),
        deploy_immediacy=dict(type='str', choices=['immediate', 'lazy']),
        interface_mode=dict(type='str', choices=['access', 'tagged', '802.1p'], aliases=['mode', 'interface_mode_name']),
        interface_type=dict(type='str', choices=['switch_port', 'vpc', 'port_channel', 'fex'], required=True),
        # NOTE: C(pod) is usually an integer below 10.
        pod=dict(type='int', aliases=['pod_number']),
        # NOTE: C(leafs) is usually something like '101' or '101-102' depending on C(connection_type).
        leafs=dict(type='list', aliases=['paths', 'leaves', 'nodes', 'switches']),
        # NOTE: C(interface) is usually a policy group like: "test-IntPolGrp" or an interface of the following format: "1/7" depending on C(interface_type).
        interface=dict(type='str'),
        # NOTE: C(extpaths) is only used if C(interface_type) is C(fex), it is usually something like '1011'(int)
        extpaths=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['tenant', 'ap', 'epg', 'interface_type', 'pod', 'leafs', 'interface']],
            ['state', 'present', ['tenant', 'ap', 'epg', 'encap_id', 'interface_type', 'pod', 'leafs', 'interface']],
            ['interface_type', 'fex', ['extpaths']],
        ],
    )

    tenant = module.params['tenant']
    ap = module.params['ap']
    epg = module.params['epg']
    encap_id = module.params['encap_id']
    primary_encap_id = module.params['primary_encap_id']
    deploy_immediacy = module.params['deploy_immediacy']
    interface_mode = module.params['interface_mode']
    interface_type = module.params['interface_type']
    pod = module.params['pod']
    # Users are likely to use integers for leaf IDs, which would raise an exception when using the join method
    leafs = [str(leaf) for leaf in module.params['leafs']]
    if leafs is not None:
        if len(leafs) == 1:
            if interface_type != 'vpc':
                leafs = leafs[0]
            else:
                module.fail_json(msg='A interface_type of "vpc" requires 2 leafs')
        elif len(leafs) == 2:
            if interface_type == 'vpc':
                leafs = "-".join(leafs)
            else:
                module.fail_json(msg='The interface_types "switch_port", "port_channel", and "fex" \
                    do not support using multiple leafs for a single binding')
        else:
            module.fail_json(msg='The "leafs" parameter must not have more than 2 entries')
    interface = module.params['interface']
    extpaths = module.params['extpaths']
    state = module.params['state']
    static_path = ''

    if encap_id is not None:
        if encap_id in range(1, 4097):
            encap_id = 'vlan-{0}'.format(encap_id)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')

    if primary_encap_id is not None:
        if primary_encap_id in range(1, 4097):
            primary_encap_id = 'vlan-{0}'.format(primary_encap_id)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')

    INTERFACE_TYPE_MAPPING = dict(
        # NOTE: C(interface) can be a policy group like: 'test-IntPolGrp' or of following format: '1/7', C(leafs) can only be something like '101'
        switch_port='topology/pod-{0}/paths-{1}/pathep-[eth{2}]'.format(pod, leafs, interface),
        # NOTE: C(interface) can be a policy group like: 'test-IntPolGrp' or of following format: '1/7', C(leafs) can only be something like '101'
        port_channel='topology/pod-{0}/paths-{1}/pathep-[eth{2}]'.format(pod, leafs, interface),
        # NOTE: C(interface) can be a policy group like: 'test-IntPolGrp', C(leafs) can be something like '101-102'
        vpc='topology/pod-{0}/protpaths-{1}/pathep-[{2}]'.format(pod, leafs, interface),
        # NOTE: C(interface) can be of the following format: '1/7', C(leafs) can only be like '101', C(extpaths) can only be like '1011'
        fex='topology/pod-{0}/paths-{1}/extpaths-{2}/pathep-[eth{3}]'.format(pod, leafs, extpaths, interface),
    )

    static_path = INTERFACE_TYPE_MAPPING[interface_type]

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            filter_target='eq(fvTenant.name, "{0}")'.format(tenant),
            module_object=tenant,
        ),
        subclass_1=dict(
            aci_class='fvAp',
            aci_rn='ap-{0}'.format(ap),
            filter_target='eq(fvAp.name, "{0}")'.format(ap),
            module_object=ap,
        ),
        subclass_2=dict(
            aci_class='fvAEPg',
            aci_rn='epg-{0}'.format(epg),
            filter_target='eq(fvAEPg.name, "{0}")'.format(epg),
            module_object=epg,
        ),
        subclass_3=dict(
            aci_class='fvRsPathAtt',
            aci_rn='rspathAtt-[{0}]'.format(static_path),
            filter_target='eq(fvRsPathAtt.tDn, "{0}"'.format(static_path),
            module_object=static_path,
        ),
    )

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='fvRsPathAtt',
            class_config=dict(
                encap=encap_id,
                primaryEncap=primary_encap_id,
                instrImedcy=deploy_immediacy,
                mode=interface_mode,
                tDn=static_path,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fvRsPathAtt')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
