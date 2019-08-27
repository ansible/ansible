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
module: aci_config_rollback
short_description: Provides rollback and rollback preview functionality (config:ImportP)
description:
- Provides rollback and rollback preview functionality for Cisco ACI fabrics.
- Config Rollbacks are done using snapshots C(aci_snapshot) with the configImportP class.
version_added: '2.4'
options:
  compare_export_policy:
    description:
    - The export policy that the C(compare_snapshot) is associated to.
    type: str
  compare_snapshot:
    description:
    - The name of the snapshot to compare with C(snapshot).
    type: str
  description:
    description:
    - The description for the Import Policy.
    type: str
    aliases: [ descr ]
  export_policy:
    description:
    - The export policy that the C(snapshot) is associated to.
    type: str
    required: yes
  fail_on_decrypt:
    description:
    - Determines if the APIC should fail the rollback if unable to decrypt secured data.
    - The APIC defaults to C(yes) when unset.
    type: bool
  import_mode:
    description:
    - Determines how the import should be handled by the APIC.
    - The APIC defaults to C(atomic) when unset.
    type: str
    choices: [ atomic, best-effort ]
  import_policy:
    description:
    - The name of the Import Policy to use for config rollback.
    type: str
  import_type:
    description:
    - Determines how the current and snapshot configuration should be compared for replacement.
    - The APIC defaults to C(replace) when unset.
    type: str
    choices: [ merge, replace ]
  snapshot:
    description:
    - The name of the snapshot to rollback to, or the base snapshot to use for comparison.
    - The C(aci_snapshot) module can be used to query the list of available snapshots.
    type: str
    required: yes
  state:
    description:
    - Use C(preview) for previewing the diff between two snapshots.
    - Use C(rollback) for reverting the configuration to a previous snapshot.
    type: str
    choices: [ preview, rollback ]
    default: rollback
extends_documentation_fragment: aci
seealso:
- module: aci_config_snapshot
- name: APIC Management Information Model reference
  description: More information about the internal APIC class B(config:ImportP).
  link: https://developer.cisco.com/docs/apic-mim-ref/
author:
- Jacob McGill (@jmcgill298)
'''

EXAMPLES = r'''
---
- name: Create a Snapshot
  aci_config_snapshot:
    host: apic
    username: admin
    password: SomeSecretPassword
    export_policy: config_backup
    state: present
  delegate_to: localhost

- name: Query Existing Snapshots
  aci_config_snapshot:
    host: apic
    username: admin
    password: SomeSecretPassword
    export_policy: config_backup
    state: query
  delegate_to: localhost

- name: Compare Snapshot Files
  aci_config_rollback:
    host: apic
    username: admin
    password: SomeSecretPassword
    export_policy: config_backup
    snapshot: run-2017-08-28T06-24-01
    compare_export_policy: config_backup
    compare_snapshot: run-2017-08-27T23-43-56
    state: preview
  delegate_to: localhost

- name: Rollback Configuration
  aci_config_rollback:
    host: apic
    username: admin
    password: SomeSecretPassword
    import_policy: rollback_config
    export_policy: config_backup
    snapshot: run-2017-08-28T06-24-01
    state: rollback
  delegate_to: localhost

- name: Rollback Configuration
  aci_config_rollback:
    host: apic
    username: admin
    password: SomeSecretPassword
    import_policy: rollback_config
    export_policy: config_backup
    snapshot: run-2017-08-28T06-24-01
    description: Rollback 8-27 changes
    import_mode: atomic
    import_type: replace
    fail_on_decrypt: yes
    state: rollback
  delegate_to: localhost
'''

RETURN = r'''
preview:
  description: A preview between two snapshots
  returned: when state is preview
  type: str
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
    argument_spec = aci_argument_spec()
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

    aci = ACIModule(module)

    description = module.params['description']
    export_policy = module.params['export_policy']
    fail_on_decrypt = aci.boolean(module.params['fail_on_decrypt'])
    import_mode = module.params['import_mode']
    import_policy = module.params['import_policy']
    import_type = module.params['import_type']
    snapshot = module.params['snapshot']
    state = module.params['state']

    if state == 'rollback':
        if snapshot.startswith('run-'):
            snapshot = snapshot.replace('run-', '', 1)

        if not snapshot.endswith('.tar.gz'):
            snapshot += '.tar.gz'

        filename = 'ce2_{0}-{1}'.format(export_policy, snapshot)

        aci.construct_url(
            root_class=dict(
                aci_class='configImportP',
                aci_rn='fabric/configimp-{0}'.format(import_policy),
                module_object=import_policy,
                target_filter={'name': import_policy},
            ),
        )

        aci.get_existing()

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

        aci.get_diff(aci_class='configImportP')

        aci.post_config()

    elif state == 'preview':
        aci.url = '%(protocol)s://%(host)s/mqapi2/snapshots.diff.xml' % module.params
        aci.filter_string = (
            '?s1dn=uni/backupst/snapshots-[uni/fabric/configexp-%(export_policy)s]/snapshot-%(snapshot)s&'
            's2dn=uni/backupst/snapshots-[uni/fabric/configexp-%(compare_export_policy)s]/snapshot-%(compare_snapshot)s'
        ) % module.params

        # Generate rollback comparison
        get_preview(aci)

    aci.exit_json()


def get_preview(aci):
    '''
    This function is used to generate a preview between two snapshots and add the parsed results to the aci module return data.
    '''
    uri = aci.url + aci.filter_string
    resp, info = fetch_url(aci.module, uri, headers=aci.headers, method='GET', timeout=aci.module.params['timeout'], use_proxy=aci.module.params['use_proxy'])
    aci.method = 'GET'
    aci.response = info['msg']
    aci.status = info['status']

    # Handle APIC response
    if info['status'] == 200:
        xml_to_json(aci, resp.read())
    else:
        aci.result['raw'] = resp.read()
        aci.fail_json(msg="Request failed: %(code)s %(text)s (see 'raw' output)" % aci.error)


def xml_to_json(aci, response_data):
    '''
    This function is used to convert preview XML data into JSON.
    '''
    if XML_TO_JSON:
        xml = lxml.etree.fromstring(to_bytes(response_data))
        xmldata = cobra.data(xml)
        aci.result['preview'] = xmldata
    else:
        aci.result['preview'] = response_data


if __name__ == "__main__":
    main()
