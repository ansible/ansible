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
  encap:
    description:
    - The VLAN encapsulation for the EPG.
    - This acts as the secondary encap when using useg.
    aliases: [ encapsulation ]
    choices: [ range from 1 to 4096 ]
  primary_encap:
    description:
    - Determines the primary VLAN ID when using useg.
    aliases: [ primary_encapsulation ]
    choices: [ range from 1 to 4096 ]
  deploy_immediacy:
    description:
    - The Deployement Immediacy of Static EPG on PC, VPC or Interface.
    - The APIC defaults the Deployement Immediacy to C(lazy).
    choices: [ immediate, lazy ]
    default: lazy
  mode:
    description:
    - Mode of static EPG deployement.
    - The APIC defaults the mode to C(regular).
    choices: [ untagged, native, regular ]
    default: regular
    aliases: [ mode_name ]
  connection_type:
    description:
    - The Path Type for the static EPG deployement.
    - The APIC defaults the Path Type to C(access_interface) which is the same as C(Port).
    choices: [ access_interface, virtual_port_channel, direct_port_channel, fex ]
    default: access_interface
  pod:
    description:
    - The pod number part of the tDn.
    - C(pod) is usually an integer below 10.
    aliases: [ pod_number ]
  paths:
    description:
    - The C(paths) string value part of the tDn (also used for protpaths in the tDn when selecting C(virtual_port_channel) as the C(connection_type)).
    - C(paths) is usually something like '1011' or '1011-1012' depending on C(connection_type).
  interface:
    description:
    - The C(interface) string value part of the tDn.
    - Usually a policy group like "test-IntPolGrp" or an interface of the following format "1/7" depending on C(connection_type).
  extpaths:
    description:
    - The C(extpaths) integer value part of the tDn.
    - C(extpaths) is only used if C(connection_type) is C(fex).
    - Usually something like '1011'(int).
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Deploy Static EPG (Port Channel)
  aci_static_binding_to_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: accessport-code-cert
    ap: accessport_code_app
    epg: accessport_epg1
    encap: 222
    # primary_encap: 11
    deploy_immediacy: lazy
    mode: regular
    connection_type: access_interface
    pod: 1
    paths: 1011
    interface: '1/7'
    # extpaths: 1011
    state: present
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

# TODO: change 'deploy_immediacy' to 'resolution_immediacy' (as seen in aci_epg_to_domain)?
# TODO: change C(access_interface) to C(Port) or C(port_channel) as seen on GUI in the 'connection_type' parameter


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        tenant=dict(type='str', aliases=['tenant_name']),
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name']),
        epg=dict(type='str', aliases=['epg_name']),
        encap=dict(type='int', aliases=['encapsulation']),
        primary_encap=dict(type='int', aliases=['primary_encapsulation']),
        deploy_immediacy=dict(type='str', choices=['immediate', 'lazy']),
        mode=dict(type='str', choices=['untagged', 'native', 'regular'], aliases=['mode_name']),
        connection_type=dict(type='str', choices=['access_interface', 'virtual_port_channel', 'direct_port_channel', 'fex'], required=True),
        # NOTE: C(pod) is usually an integer below 10.
        pod=dict(type='int', aliases=['pod_number']),
        # NOTE: C(paths) is usually something like '1011' or '1011-1012' depending on C(connection_type).
        paths=dict(type='str'),
        # NOTE: C(interface) is usually a policy group like: "test-IntPolGrp" or an interface of the following format: "1/7" depending on C(connection_type).
        interface=dict(type='str'),
        # NOTE: C(extpaths) is only used if C(connection_type) is C(fex), it is usually something like '1011'(int)
        extpaths=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            # NOTE: extpaths is a requirement if 'connection_type' is 'fex'
            ['state', 'absent', ['tenant', 'ap', 'epg', 'pod', 'paths', 'interface']],
            ['state', 'present', ['tenant', 'ap', 'epg', 'encap', 'connection_type', 'pod', 'paths', 'interface']],
        ],
    )

    tenant = module.params['tenant']
    ap = module.params['ap']
    epg = module.params['epg']
    encap = module.params['encap']
    primary_encap = module.params['primary_encap']
    deploy_immediacy = module.params['deploy_immediacy']
    mode = module.params['mode']
    connection_type = module.params['connection_type']
    pod = module.params['pod']
    paths = module.params['paths']
    interface = module.params['interface']
    extpaths = module.params['extpaths']
    state = module.params['state']
    static_path = ''

    if encap is not None:
        if encap in range(1, 4097):
            encap = 'vlan-{0}'.format(encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')

    if primary_encap is not None:
        if primary_encap in range(1, 4097):
            primary_encap = 'vlan-{0}'.format(primary_encap)
        else:
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')

    if connection_type == 'fex' and extpaths is None:
        module.fail_json(msg='extpaths must be defined')

    CONNECTION_TYPE_MAPPING = dict(
        # NOTE: C(interface) can be a policy group like: "test-IntPolGrp" or of following format: "1/7", C(paths) can only be something like '1011'(int)
        access_interface='topology/pod-{0}/paths-{1}/pathep-[eth{2}]'.format(pod, paths, interface),
        # NOTE: C(interface) can be a policy group like: "test-IntPolGrp" or of following format: "1/7", C(paths) can only be something like '1011'(int)
        direct_port_channel='topology/pod-{0}/paths-{1}/pathep-[eth{2}]'.format(pod, paths, interface),
        # NOTE: C(interface) can be a policy group like: "test-IntPolGrp", C(paths) can be something like 1011-1012'(str)
        virtual_port_channel='topology/pod-{0}/protpaths-{1}/pathep-[{2}]'.format(pod, paths, interface),
        # NOTE: C(interface) can be of the following format: "1/7", C(paths) can only be like '1011'(int), C(extpaths) can only be like '1011'(int)
        fex='topology/pod-{0}/paths-{1}/extpaths-{2}/pathep-[eth{3}]'.format(pod, paths, extpaths, interface),
    )

    static_path = CONNECTION_TYPE_MAPPING[connection_type]

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
                encap=encap,
                primaryEncap=primary_encap,
                instrImedcy=deploy_immediacy,
                mode=mode,
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
