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
module: aci_config_snapshot
short_description: Manage Config Snapshots on Cisco ACI fabrics (config:Snapshot, config:ExportP)
description:
- Manage Config Snapshots on Cisco ACI fabrics.
- Creating new Snapshots is done using the configExportP class.
- Removing Snapshots is done using the configSnapshot class.
- More information from the internal APIC classes
  I(config:Snapshot) at U(https://developer.cisco.com/media/mim-ref/MO-configSnapshot.html) and
  I(config:ExportP) at U(https://developer.cisco.com/media/mim-ref/MO-configExportP.html).
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- Tested with ACI Fabric 1.0(3f)+
notes:
- The APIC does not provide a mechanism for naming the snapshots.
- 'Snapshot files use the following naming structure: ce_<config export policy name>-<yyyy>-<mm>-<dd>T<hh>:<mm>:<ss>.<mss>+<hh>:<mm>.'
- 'Snapshot objects use the following naming structure: run-<yyyy>-<mm>-<dd>T<hh>-<mm>-<ss>.'
options:
  description:
    description:
    - The description for the Config Export Policy.
    aliases: [ descr ]
  export_policy:
    description:
    - The name of the Export Policy to use for Config Snapshots.
    aliases: [ name ]
  format:
    description:
    - Sets the config backup to be formatted in JSON or XML.
    - The APIC defaults new Export Policies to C(json)
    choices: [ json, xml ]
    default: json
  include_secure:
    description:
    - Determines if secure information should be included in the backup.
    - The APIC defaults new Export Policies to C(yes).
    choices: [ 'no', 'yes' ]
    default: 'yes'
  max_count:
    description:
    - Determines how many snapshots can exist for the Export Policy before the APIC starts to rollover.
    - The APIC defaults new Export Policies to C(3).
    choices: [ range between 1 and 10 ]
    default: 3
  snapshot:
    description:
    - The name of the snapshot to delete.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- name: Create a Snapshot
  aci_config_snapshot:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: present
    export_policy: config_backup
    max_count: 10
    description: Backups taken before new configs are applied.

- name: Query all Snapshots
  aci_config_snapshot:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query

- name: Query Snapshots associated with a particular Export Policy
  aci_config_snapshot:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query
    export_policy: config_backup

- name: Delete a Snapshot
  aci_config_snapshot:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: absent
    export_policy: config_backup
    snapshot: run-2017-08-24T17-20-05
'''

RETURN = r''' # '''

from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        description=dict(type='str', aliases=['descr']),
        export_policy=dict(type='str', aliases=['name']),
        format=dict(type='str', choices=['json', 'xml']),
        include_secure=dict(type='str', choices=['no', 'yes']),
        max_count=dict(type='int'),
        snapshot=dict(type='str'),
        state=dict(type='str', choices=['absent', 'present', 'query'], default='present'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_if=[
            ['state', 'absent', ['export_policy', 'snapshot']],
            ['state', 'present', ['export_policy']],
        ],
    )

    description = module.params['description']
    export_policy = module.params['export_policy']
    file_format = module.params['format']
    include_secure = module.params['include_secure']
    max_count = module.params['max_count']
    if max_count is not None:
        if max_count in range(1, 11):
            max_count = str(max_count)
        else:
            module.fail_json(msg='The "max_count" must be a number between 1 and 10')
    snapshot = module.params['snapshot']
    if snapshot is not None and not snapshot.startswith('run-'):
        snapshot = 'run-' + snapshot
    state = module.params['state']

    aci = ACIModule(module)

    if state == 'present':
        aci.construct_url(
            root_class=dict(
                aci_class='configExportP',
                aci_rn='fabric/configexp-{}'.format(export_policy),
                filter_target='eq(configExportP.name, "{}")'.format(export_policy),
                module_object=export_policy,
            ),
        )

        aci.get_existing()

        # Filter out module params with null values
        aci.payload(
            aci_class='configExportP',
            class_config=dict(
                adminSt='triggered',
                descr=description,
                format=file_format,
                includeSecureFields=include_secure,
                maxSnapshotCount=max_count,
                name=export_policy,
                snapshot='yes',
            ),
        )

        aci.get_diff('configExportP')

        # Create a new Snapshot
        aci.post_config()

    else:
        # Prefix the proper url to export_policy
        if export_policy is not None:
            export_policy = 'uni/fabric/configexp-{}'.format(export_policy)

        aci.construct_url(
            root_class=dict(
                aci_class='configSnapshotCont',
                aci_rn='backupst/snapshots-[{}]'.format(export_policy),
                filter_target='(configSnapshotCont.name, "{}")'.format(export_policy),
                module_object=export_policy,
            ),
            subclass_1=dict(
                aci_class='configSnapshot',
                aci_rn='snapshot-{}'.format(snapshot),
                filter_target='(configSnapshot.name, "{}")'.format(snapshot),
                module_object=snapshot,
            ),
        )

        aci.get_existing()

        if state == 'absent':
            # Build POST request to used to remove Snapshot
            aci.payload(
                aci_class='configSnapshot',
                class_config=dict(
                    name=snapshot,
                    retire="yes",
                ),
            )

            if aci.result['existing']:
                aci.get_diff('configSnapshot')

                # Mark Snapshot for Deletion
                aci.post_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
