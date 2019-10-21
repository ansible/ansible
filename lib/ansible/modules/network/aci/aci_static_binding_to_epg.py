#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Bruno Calogero <brunocalogero@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: aci_static_binding_to_epg
short_description: Bind static paths to EPGs (fv:RsPathAtt)
description:
- Bind static paths to EPGs on Cisco ACI fabrics.
version_added: '2.5'
options:
  tenant:
    description:
    - Name of an existing tenant.
    type: str
    aliases: [ tenant_name ]
  ap:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    type: str
    aliases: [ app_profile, app_profile_name ]
  epg:
    description:
    - The name of the end point group.
    type: str
    aliases: [ epg_name ]
  description:
    description:
    - Description for the static path to EPG binding.
    type: str
    aliases: [ descr ]
    version_added: '2.7'
  encap_id:
    description:
    - The encapsulation ID associating the C(epg) with the interface path.
    - This acts as the secondary C(encap_id) when using micro-segmentation.
    - Accepted values are any valid encap ID for specified encap, currently ranges between C(1) and C(4096).
    type: int
    aliases: [ vlan, vlan_id ]
  primary_encap_id:
    description:
    - Determines the primary encapsulation ID associating the C(epg)
      with the interface path when using micro-segmentation.
    - Accepted values are any valid encap ID for specified encap, currently ranges between C(1) and C(4096).
    type: int
    aliases: [ primary_vlan, primary_vlan_id ]
  deploy_immediacy:
    description:
    - The Deployment Immediacy of Static EPG on PC, VPC or Interface.
    - The APIC defaults to C(lazy) when unset during creation.
    type: str
    choices: [ immediate, lazy ]
  interface_mode:
    description:
    - Determines how layer 2 tags will be read from and added to frames.
    - Values C(802.1p) and C(native) are identical.
    - Values C(access) and C(untagged) are identical.
    - Values C(regular), C(tagged) and C(trunk) are identical.
    - The APIC defaults to C(trunk) when unset during creation.
    type: str
    choices: [ 802.1p, access, native, regular, tagged, trunk, untagged ]
    aliases: [ interface_mode_name, mode ]
  interface_type:
    description:
    - The type of interface for the static EPG deployment.
    type: str
    choices: [ fex, port_channel, switch_port, vpc ]
    default: switch_port
  pod_id:
    description:
    - The pod number part of the tDn.
    - C(pod_id) is usually an integer below C(10).
    type: int
    aliases: [ pod, pod_number ]
  leafs:
    description:
    - The switch ID(s) that the C(interface) belongs to.
    - When C(interface_type) is C(switch_port), C(port_channel), or C(fex), then C(leafs) is a string of the leaf ID.
    - When C(interface_type) is C(vpc), then C(leafs) is a list with both leaf IDs.
    - The C(leafs) value is usually something like '101' or '101-102' depending on C(connection_type).
    type: list
    aliases: [ leaves, nodes, paths, switches ]
  interface:
    description:
    - The C(interface) string value part of the tDn.
    - Usually a policy group like C(test-IntPolGrp) or an interface of the following format C(1/7) depending on C(interface_type).
    type: str
  extpaths:
    description:
    - The C(extpaths) integer value part of the tDn.
    - C(extpaths) is only used if C(interface_type) is C(fex).
    - Usually something like C(1011).
    type: int
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
notes:
- The C(tenant), C(ap), C(epg) used must exist before using this module in your playbook.
  The M(aci_tenant), M(aci_ap), M(aci_epg) modules can be used for this.
seealso:
- module: aci_tenant
- module: aci_ap
- module: aci_epg
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(fv:RsPathAtt).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Bruno Calogero (@brunocalogero)
'''

EXAMPLES = r'''
- name: Deploy Static Path binding for given EPG
  aci_static_binding_to_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: accessport-code-cert
    ap: accessport_code_app
    epg: accessport_epg1
    encap_id: 222
    deploy_immediacy: lazy
    interface_mode: untagged
    interface_type: switch_port
    pod_id: 1
    leafs: 101
    interface: '1/7'
    state: present
  delegate_to: localhost

- name: Remove Static Path binding for given EPG
  aci_static_binding_to_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: accessport-code-cert
    ap: accessport_code_app
    epg: accessport_epg1
    interface_type: switch_port
    pod: 1
    leafs: 101
    interface: '1/7'
    state: absent
  delegate_to: localhost

- name: Get specific Static Path binding for given EPG
  aci_static_binding_to_epg:
    host: apic
    username: admin
    password: SomeSecretPassword
    tenant: accessport-code-cert
    ap: accessport_code_app
    epg: accessport_epg1
    interface_type: switch_port
    pod: 1
    leafs: 101
    interface: '1/7'
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
current:
  description: The existing configuration from the APIC after the module has finished
  returned: success
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production environment",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
error:
  description: The error information as returned from the APIC
  returned: failure
  type: dict
  sample:
    {
        "code": "122",
        "text": "unknown managed object class foo"
    }
raw:
  description: The raw output returned by the APIC REST API (xml or json)
  returned: parse error
  type: str
  sample: '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1"><error code="122" text="unknown managed object class foo"/></imdata>'
sent:
  description: The actual/minimal configuration pushed to the APIC
  returned: info
  type: list
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment"
            }
        }
    }
previous:
  description: The original configuration from the APIC before the module has started
  returned: info
  type: list
  sample:
    [
        {
            "fvTenant": {
                "attributes": {
                    "descr": "Production",
                    "dn": "uni/tn-production",
                    "name": "production",
                    "nameAlias": "",
                    "ownerKey": "",
                    "ownerTag": ""
                }
            }
        }
    ]
proposed:
  description: The assembled configuration from the user-provided parameters
  returned: info
  type: dict
  sample:
    {
        "fvTenant": {
            "attributes": {
                "descr": "Production environment",
                "name": "production"
            }
        }
    }
filter_string:
  description: The filter string used for the request
  returned: failure or debug
  type: str
  sample: ?rsp-prop-include=config-only
method:
  description: The HTTP method used for the request to the APIC
  returned: failure or debug
  type: str
  sample: POST
response:
  description: The HTTP response from the APIC
  returned: failure or debug
  type: str
  sample: OK (30 bytes)
status:
  description: The HTTP status from the APIC
  returned: failure or debug
  type: int
  sample: 200
url:
  description: The HTTP url used for the request to the APIC
  returned: failure or debug
  type: str
  sample: https://10.11.12.13/api/mo/uni/tn-production.json
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec

INTERFACE_MODE_MAPPING = {
    '802.1p': 'native',
    'access': 'untagged',
    'native': 'native',
    'regular': 'regular',
    'tagged': 'regular',
    'trunk': 'regular',
    'untagged': 'untagged',
}

INTERFACE_TYPE_MAPPING = dict(
    fex='topology/pod-{pod_id}/paths-{leafs}/extpaths-{extpaths}/pathep-[eth{interface}]',
    port_channel='topology/pod-{pod_id}/paths-{leafs}/pathep-[{interface}]',
    switch_port='topology/pod-{pod_id}/paths-{leafs}/pathep-[eth{interface}]',
    vpc='topology/pod-{pod_id}/protpaths-{leafs}/pathep-[{interface}]',
)

# TODO: change 'deploy_immediacy' to 'resolution_immediacy' (as seen in aci_epg_to_domain)?


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        tenant=dict(type='str', aliases=['tenant_name']),  # Not required for querying all objects
        ap=dict(type='str', aliases=['app_profile', 'app_profile_name']),  # Not required for querying all objects
        epg=dict(type='str', aliases=['epg_name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        encap_id=dict(type='int', aliases=['vlan', 'vlan_id']),
        primary_encap_id=dict(type='int', aliases=['primary_vlan', 'primary_vlan_id']),
        deploy_immediacy=dict(type='str', choices=['immediate', 'lazy']),
        interface_mode=dict(type='str', choices=['802.1p', 'access', 'native', 'regular', 'tagged', 'trunk', 'untagged'],
                            aliases=['interface_mode_name', 'mode']),
        interface_type=dict(type='str', default='switch_port', choices=['fex', 'port_channel', 'switch_port', 'vpc']),
        pod_id=dict(type='int', aliases=['pod', 'pod_number']),  # Not required for querying all objects
        leafs=dict(type='list', aliases=['leaves', 'nodes', 'paths', 'switches']),  # Not required for querying all objects
        interface=dict(type='str'),  # Not required for querying all objects
        extpaths=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['interface_type', 'fex', ['extpaths']],
            ['state', 'absent', ['ap', 'epg', 'interface', 'leafs', 'pod_id', 'tenant']],
            ['state', 'present', ['ap', 'encap_id', 'epg', 'interface', 'leafs', 'pod_id', 'tenant']],
        ],
    )

    tenant = module.params['tenant']
    ap = module.params['ap']
    epg = module.params['epg']
    description = module.params['description']
    encap_id = module.params['encap_id']
    primary_encap_id = module.params['primary_encap_id']
    deploy_immediacy = module.params['deploy_immediacy']
    interface_mode = module.params['interface_mode']
    interface_type = module.params['interface_type']
    pod_id = module.params['pod_id']
    leafs = module.params['leafs']
    if leafs is not None:
        # Process leafs, and support dash-delimited leafs
        leafs = []
        for leaf in module.params['leafs']:
            # Users are likely to use integers for leaf IDs, which would raise an exception when using the join method
            leafs.extend(str(leaf).split('-'))
        if len(leafs) == 1:
            if interface_type == 'vpc':
                module.fail_json(msg='A interface_type of "vpc" requires 2 leafs')
            leafs = leafs[0]
        elif len(leafs) == 2:
            if interface_type != 'vpc':
                module.fail_json(msg='The interface_types "switch_port", "port_channel", and "fex" \
                    do not support using multiple leafs for a single binding')
            leafs = "-".join(leafs)
        else:
            module.fail_json(msg='The "leafs" parameter must not have more than 2 entries')
    interface = module.params['interface']
    extpaths = module.params['extpaths']
    state = module.params['state']

    if encap_id is not None:
        if encap_id not in range(1, 4097):
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
        encap_id = 'vlan-{0}'.format(encap_id)

    if primary_encap_id is not None:
        if primary_encap_id not in range(1, 4097):
            module.fail_json(msg='Valid VLAN assigments are from 1 to 4096')
        primary_encap_id = 'vlan-{0}'.format(primary_encap_id)

    static_path = INTERFACE_TYPE_MAPPING[interface_type].format(pod_id=pod_id, leafs=leafs, extpaths=extpaths, interface=interface)

    path_target_filter = {}
    if pod_id is not None and leafs is not None and interface is not None and (interface_type != 'fex' or extpaths is not None):
        path_target_filter = {'tDn': static_path}

    if interface_mode is not None:
        interface_mode = INTERFACE_MODE_MAPPING[interface_mode]

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='fvTenant',
            aci_rn='tn-{0}'.format(tenant),
            module_object=tenant,
            target_filter={'name': tenant},
        ),
        subclass_1=dict(
            aci_class='fvAp',
            aci_rn='ap-{0}'.format(ap),
            module_object=ap,
            target_filter={'name': ap},
        ),
        subclass_2=dict(
            aci_class='fvAEPg',
            aci_rn='epg-{0}'.format(epg),
            module_object=epg,
            target_filter={'name': epg},
        ),
        subclass_3=dict(
            aci_class='fvRsPathAtt',
            aci_rn='rspathAtt-[{0}]'.format(static_path),
            module_object=static_path,
            target_filter=path_target_filter,
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='fvRsPathAtt',
            class_config=dict(
                descr=description,
                encap=encap_id,
                primaryEncap=primary_encap_id,
                instrImedcy=deploy_immediacy,
                mode=interface_mode,
                tDn=static_path,
            ),
        )

        aci.get_diff(aci_class='fvRsPathAtt')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
