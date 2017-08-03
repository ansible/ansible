#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_pkiprofile
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of PKIProfile Avi RESTful Object
description:
    - This module is used to configure PKIProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    ca_certs:
        description:
            - List of certificate authorities (root and intermediate) trusted that is used for certificate validation.
    created_by:
        description:
            - Creator name.
    crl_check:
        description:
            - When enabled, avi will verify via crl checks that certificates in the trust chain have not been revoked.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    crls:
        description:
            - Certificate revocation lists.
    ignore_peer_chain:
        description:
            - When enabled, avi will not trust intermediate and root certs presented by a client.
            - Instead, only the chain certs configured in the certificate authority section will be used to verify trust of the client's cert.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    is_federated:
        description:
            - This field describes the object's replication scope.
            - If the field is set to false, then the object is visible within the controller-cluster and its associated service-engines.
            - If the field is set to true, then the object is replicated across the federation.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.4"
    name:
        description:
            - Name of the pki profile.
        required: true
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
    validate_only_leaf_crl:
        description:
            - When enabled, avi will only validate the revocation status of the leaf certificate using crl.
            - To enable validation for the entire chain, disable this option and provide all the relevant crls.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create PKIProfile object
  avi_pkiprofile:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_pkiprofile
"""

RETURN = '''
obj:
    description: PKIProfile (api/pkiprofile) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        ca_certs=dict(type='list',),
        created_by=dict(type='str',),
        crl_check=dict(type='bool',),
        crls=dict(type='list',),
        ignore_peer_chain=dict(type='bool',),
        is_federated=dict(type='bool',),
        name=dict(type='str', required=True),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
        validate_only_leaf_crl=dict(type='bool',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'pkiprofile',
                           set([]))

if __name__ == '__main__':
    main()
