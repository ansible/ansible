#!/usr/bin/python

# (c) 2019, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""AWS Cloud Volumes Services - Manage Snapshots"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: aws_netapp_cvs_snapshots

short_description: NetApp AWS Cloud Volumes Service Manage Snapshots.
extends_documentation_fragment:
    - netapp.awscvs
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, Update, Delete Snapshot on AWS Cloud Volumes Service.

options:
  state:
     description:
     - Whether the specified snapshot should exist or not.
     required: true
     type: str
     choices: ['present', 'absent']

  region:
    description:
    - The region to which the snapshot belongs to.
    required: true
    type: str

  name:
    description:
    - Name of the snapshot
    required: true
    type: str

  fileSystemId:
    description:
    - Name or Id of the filesystem.
    - Required for create operation
    type: str

  from_name:
    description:
    - ID or Name of the snapshot to rename.
    - Required to create an snapshot called 'name' by renaming 'from_name'.
    type: str
'''

EXAMPLES = """
- name: Create Snapshot
  aws_netapp_cvs_snapshots:
    state: present
    region: us-east-1
    name: testSnapshot
    fileSystemId: testVolume
    api_url : cds-aws-bundles.netapp.com
    api_key: myApiKey
    secret_key : mySecretKey

- name: Update Snapshot
  aws_netapp_cvs_snapshots:
    state: present
    region: us-east-1
    name: testSnapshot - renamed
    from_name: testSnapshot
    fileSystemId: testVolume
    api_url : cds-aws-bundles.netapp.com
    api_key: myApiKey
    secret_key : mySecretKey

- name: Delete Snapshot
  aws_netapp_cvs_snapshots:
    state: absent
    region: us-east-1
    name: testSnapshot
    api_url : cds-aws-bundles.netapp.com
    api_key: myApiKey
    secret_key : mySecretKey
"""

RETURN = """
"""

import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.netapp import AwsCvsRestAPI


class AwsCvsNetappSnapshot(object):
    """
    Contains methods to parse arguments,
    derive details of AWS_CVS objects
    and send requests to AWS CVS via
    the restApi
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.aws_cvs_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            region=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            fileSystemId=dict(required=False, type='str')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['state', 'name', 'fileSystemId']),
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # Calling generic AWSCVS restApi class
        self.restApi = AwsCvsRestAPI(self.module)

        # Checking for the parameters passed and create new parameters list
        self.data = {}
        for key in self.parameters.keys():
            self.data[key] = self.parameters[key]

    def getSnapshotId(self, name):
        # Check if  snapshot exists
        # Return snapshot Id  If Snapshot is found, None otherwise
        list_snapshots, error = self.restApi.get('Snapshots')

        if error:
            self.module.fail_json(msg=error)

        for snapshot in list_snapshots:
            if snapshot['name'] == name:
                return snapshot['snapshotId']
        return None

    def getfilesystemId(self):
        # Check given FileSystem is exists
        # Return fileSystemId is found, None otherwise
        list_filesystem, error = self.restApi.get('FileSystems')

        if error:
            self.module.fail_json(msg=error)
        for FileSystem in list_filesystem:
            if FileSystem['fileSystemId'] == self.parameters['fileSystemId']:
                return FileSystem['fileSystemId']
            elif FileSystem['creationToken'] == self.parameters['fileSystemId']:
                return FileSystem['fileSystemId']
        return None

    def create_snapshot(self):
        # Create Snapshot
        api = 'Snapshots'
        response, error = self.restApi.post(api, self.data)
        if error:
            self.module.fail_json(msg=error)

    def rename_snapshot(self, snapshotId):
        # Rename Snapshot
        api = 'Snapshots/' + snapshotId
        response, error = self.restApi.put(api, self.data)
        if error:
            self.module.fail_json(msg=error)

    def delete_snapshot(self, snapshotId):
        # Delete Snapshot
        api = 'Snapshots/' + snapshotId
        data = None
        response, error = self.restApi.delete(api, self.data)
        if error:
            self.module.fail_json(msg=error)

    def apply(self):
        """
        Perform pre-checks, call functions and exit
        """
        self.snapshotId = self.getSnapshotId(self.data['name'])

        if self.snapshotId is None and 'fileSystemId' in self.data:
            self.fileSystemId = self.getfilesystemId()
            self.data['fileSystemId'] = self.fileSystemId
            if self.fileSystemId is None:
                self.module.fail_json(msg='Error: Specified filesystem id %s does not exist ' % self.data['fileSystemId'])

        cd_action = self.na_helper.get_cd_action(self.snapshotId, self.data)
        result_message = ""
        if self.na_helper.changed:
            if self.module.check_mode:
                # Skip changes
                result_message = "Check mode, skipping changes"
            else:
                if cd_action == "delete":
                    self.delete_snapshot(self.snapshotId)
                    result_message = "Snapshot Deleted"

                elif cd_action == "create":
                    if 'from_name' in self.data:
                        # If cd_action is create and from_name is given
                        snapshotId = self.getSnapshotId(self.data['from_name'])
                        if snapshotId is not None:
                            # If resource pointed by from_name exists, rename the snapshot to name
                            self.rename_snapshot(snapshotId)
                            result_message = "Snapshot Updated"
                        else:
                            # If resource pointed by from_name does not exists, error out
                            self.module.fail_json(msg="Resource does not exist : %s" % self.data['from_name'])
                    else:
                        self.create_snapshot()
                        # If from_name is not defined, Create from scratch.
                        result_message = "Snapshot Created"

        self.module.exit_json(changed=self.na_helper.changed, msg=result_message)


def main():
    """
    Main function
    """
    aws_netapp_cvs_snapshots = AwsCvsNetappSnapshot()
    aws_netapp_cvs_snapshots.apply()


if __name__ == '__main__':
    main()
