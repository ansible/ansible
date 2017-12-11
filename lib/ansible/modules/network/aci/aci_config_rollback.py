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
module: aci_config_rollback
short_description: Provides rollback and rollback preview functionality for Cisco ACI fabrics (config:ImportP)
description:
- Provides rollback and rollback preview functionality for Cisco ACI fabric.
- Config Rollbacks are done using snapshots C(aci_snapshot) with the configImportP class.
- More information from the internal APIC class
  I(config:ImportP) at U(https://developer.cisco.com/media/mim-ref/MO-configImportP.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  compare_export_policy:
    description:
    - The export policy that the C(compare_snapshot) is associated to.
  compare_snapshot:
    description:
    - The name of the snapshot to compare with C(snapshot).
  description:
    description:
    - The description for the Import Policy.
    aliases: [ descr ]
  export_policy:
    description:
    - The export policy that the C(snapshot) is associated to.
    required: yes
  fail_on_decrypt:
    description:
    - Determines if the APIC should fail the rollback if unable to decrypt secured data.
    - The APIC defaults new Import Policies to C(yes).
    type: bool
    default: 'yes'
  import_mode:
    description:
    - Determines how the import should be handled by the APIC.
    - The APIC defaults new Import Policies to C(atomic).
    choices: [ atomic, best-effort ]
    default: atomic
  import_policy:
    description:
    - The name of the Import Policy to use for config rollback.
  import_type:
    description:
    - Determines how the current and snapshot configuration should be compared for replacement.
    - The APIC defaults new Import Policies to C(replace).
    choices: [ merge, replace ]
    default: replace
  snapshot:
    description:
    - The name of the snapshot to rollback to, or the base snapshot to use for comparison.
    - The C(aci_snapshot) module can be used to query the list of available snapshots.
    required: yes
  state:
    description:
    - Use C(preview) for previewing the diff between two snapshots.
    - Use C(rollback) for reverting the configuration to a previous snapshot.
    choices: [ preview, rollback ]
    default: rollback
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
---
- name: Create a Snapshot
  aci_config_snapshot:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: present
    export_policy: config_backup

- name: Query Existing Snapshots
  aci_config_snapshot:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query
    export_policy: config_backup

- name: Compare Snapshot Files
  aci_config_rollback:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: preview
    export_policy: config_backup
    snapshot: 'run-2017-08-28T06-24-01'
    compare_export_policy: config_backup
    compare_snapshot: 'run-2017-08-27T23-43-56'

- name: Rollback Configuration
  aci_config_rollback:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: rollback
    import_policy: rollback_config
    export_policy: config_backup
    snapshot: 'run-2017-08-28T06-24-01'

- name: Rollback Configuration
  aci_config_rollback:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: rollback
    import_policy: rollback_config
    export_policy: config_backup
    snapshot: 'run-2017-08-28T06-24-01'
    description: 'Rollback 8-27 changes'
    import_mode: atomic
    import_type: replace
    fail_on_decrypt: yes
'''

RETURN = r'''
#
'''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
from ansible.module_utils.urls import fetch_url

# Optional, only used for rollback preview
try:
    import lxml.etree
    from xmljson import cobra
    XML_TO_JSON = True
except ImportError:
    XML_TO_JSON = False


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        compare_export_policy=dict(type='str'),
        compare_snapshot=dict(type='str'),
        description=dict(type='str', aliases=['descr']),
        export_policy=dict(type='str'),
        fail_on_decrypt=dict(type='bool'),
        import_mode=dict(type='str', choices=['atomic', 'best-effort']),
        import_policy=dict(type='str'),
        import_type=dict(type='str', choices=['merge', 'replace']),
        snapshot=dict(type='str', required=True),
        state=dict(type='str', default='rollback', choices=['preview', 'rollback']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_if=[
            ['state', 'preview', ['compare_export_policy', 'compare_snapshot']],
            ['state', 'rollback', ['import_policy']],
        ],
    )

    description = module.params['description']
    export_policy = module.params['export_policy']
    fail_on_decrypt = module.params['fail_on_decrypt']
    if fail_on_decrypt is True:
        fail_on_decrypt = 'yes'
    elif fail_on_decrypt is False:
        fail_on_decrypt = 'no'
    import_mode = module.params['import_mode']
    import_policy = module.params['import_policy']
    import_type = module.params['import_type']
    snapshot = module.params['snapshot']
    state = module.params['state']

    aci = ACIModule(module)

    if state == 'rollback':
        if snapshot.startswith('run-'):
            snapshot = snapshot.replace('run-', '', 1)

        if not snapshot.endswith('.tar.gz'):
            snapshot += '.tar.gz'

        filename = 'ce2_{0}-{1}'.format(export_policy, snapshot)

        aci.construct_url(
            root_class=dict(
                aci_class='configImportP',
                aci_rn='fabric/configimp-{}'.format(import_policy),
                filter_target='eq(configImportP.name, "{}")'.format(import_policy),
                module_object=import_policy,
            ),
        )

        aci.get_existing()

        # Filter out module parameters with null values
        aci.payload(
            aci_class='configImportP',
            class_config=dict(
                adminSt='triggered',
                descr=description,
                failOnDecryptErrors=fail_on_decrypt,
                fileName=filename,
                importMode=import_mode,
                importType=import_type,
                name=import_policy,
                snapshot='yes',
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='configImportP')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'preview':
        aci.result['url'] = '%(protocol)s://%(hostname)s/mqapi2/snapshots.diff.xml' % module.params
        aci.result['filter_string'] = (
            '?s1dn=uni/backupst/snapshots-[uni/fabric/configexp-%(export_policy)s]/snapshot-%(snapshot)s&'
            's2dn=uni/backupst/snapshots-[uni/fabric/configexp-%(compare_export_policy)s]/snapshot-%(compare_snapshot)s'
        ) % module.params

        # Generate rollback comparison
        get_preview(aci)

    module.exit_json(**aci.result)


def get_preview(aci):
    '''
    This function is used to generate a preview between two snapshots and add the parsed results to the aci module return data.
    '''
    uri = aci.result['url'] + aci.result['filter_string']
    resp, info = fetch_url(aci.module, uri, headers=aci.headers, method='GET', timeout=aci.module.params['timeout'], use_proxy=aci.module.params['use_proxy'])
    aci.result['response'] = info['msg']
    aci.result['status'] = info['status']
    aci.result['method'] = 'GET'

    # Handle APIC response
    if info['status'] == 200:
        xml_to_json(aci, resp.read())
    else:
        aci.result['apic_response'] = resp.read()
        aci.module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % aci.result, **aci.result)


def xml_to_json(aci, response_data):
    '''
    This function is used to convert preview XML data into JSON.
    '''
    if XML_TO_JSON:
        xml = lxml.etree.fromstring(to_bytes(response_data))
        xmldata = cobra.data(xml)
        aci.result['diff'] = xmldata
    else:
        aci.result['diff'] = response_data


if __name__ == "__main__":
    main()
