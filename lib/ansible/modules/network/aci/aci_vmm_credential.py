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
module: aci_vmm_credential
short_description: Manage virtual domain credential profiles (vmm:UsrAccP)
description:
- Manage virtual domain credential profiles on Cisco ACI fabrics.
version_added: '2.9'
options:
  name:
    description:
    - Name of the credential profile.
    type: str
    aliases: [ credential_name, credential_profile ]
  credential_password:
    description:
    - VMM controller password.
    type: str
    aliases: []
  credential_username:
    description:
    - VMM controller username.
    type: str
    aliases: []
  description:
    description:
    - Description for the tenant.
    type: str
    aliases: [ descr ]
  domain:
    description:
    - Name of the virtual domain profile.
    type: str
    aliases: [ domain_name, domain_profile, name ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
  vm_provider:
    description:
    - The VM platform for VMM Domains.
    - Support for Kubernetes was added in ACI v3.0.
    - Support for CloudFoundry, OpenShift and Red Hat was added in ACI v3.1.
    type: str
    choices: [ cloudfoundry, kubernetes, microsoft, openshift, openstack, redhat, vmware ]
extends_documentation_fragment: aci
seealso:
- module: aci_domain
- name: APIC Management Information Model reference
  description: More information about the internal APIC classes B(vmm:DomP)
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Jason Juenger (@jasonjuenger)
'''

EXAMPLES = r'''
- name: Add credential to VMware VMM domain
  aci_vmm_credential:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain: vmware_dom
    description: secure credential
    name: vCenterCredential
    credential_username: vCenterUsername
    credential_password: vCenterPassword
    vm_provider: vmware
    state: present

- name: Remove credential from VMware VMM domain
  aci_vmm_credential:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain: vmware_dom
    name: myCredential
    vm_provider: vmware
    state: absent

- name: Query a specific VMware VMM credential
  aci_vmm_credential:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain: vmware_dom
    name: vCenterCredential
    vm_provider: vmware
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all VMware VMM credentials
  aci_vmm_credential:
    host: apic
    username: admin
    password: SomeSecretPassword
    domain: vmware_dom
    vm_provider: vmware
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

VM_PROVIDER_MAPPING = dict(
    cloudfoundry='CloudFoundry',
    kubernetes='Kubernetes',
    microsoft='Microsoft',
    openshift='OpenShift',
    openstack='OpenStack',
    redhat='Redhat',
    vmware='VMware',
)


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        name=dict(type='str', aliases=['credential_name', 'credential_profile']),
        credential_password=dict(type='str'),
        credential_username=dict(type='str'),
        description=dict(type='str', aliases=['descr']),
        domain=dict(type='str', aliases=['domain_name', 'domain_profile']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        vm_provider=dict(type='str', choices=VM_PROVIDER_MAPPING.keys())
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['domain']],
            ['state', 'present', ['domain']],
        ],
    )

    name = module.params['name']
    credential_password = module.params['credential_password']
    credential_username = module.params['credential_username']
    description = module.params['description']
    domain = module.params['domain']
    state = module.params['state']
    vm_provider = module.params['vm_provider']

    credential_class = 'vmmUsrAccP'
    usracc_mo = 'uni/vmmp-{0}/dom-{1}/usracc-{2}'.format(VM_PROVIDER_MAPPING[vm_provider], domain, name)
    usracc_rn = 'vmmp-{0}/dom-{1}/usracc-{2}'.format(VM_PROVIDER_MAPPING[vm_provider], domain, name)

    # Ensure that querying all objects works when only domain is provided
    if name is None:
        usracc_mo = None

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class=credential_class,
            aci_rn=usracc_rn,
            module_object=usracc_mo,
            target_filter={'name': domain, 'usracc': name},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class=credential_class,
            class_config=dict(
                descr=description,
                name=name,
                pwd=credential_password,
                usr=credential_username
            ),
        )

        aci.get_diff(aci_class=credential_class)

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == "__main__":
    main()
