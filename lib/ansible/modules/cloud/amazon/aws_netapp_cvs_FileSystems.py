#!/usr/bin/python

# (c) 2019, NetApp Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""AWS Cloud Volumes Services - Manage fileSystem"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: aws_netapp_cvs_FileSystems

short_description: NetApp AWS Cloud Volumes Service Manage FileSystem.
extends_documentation_fragment:
    - netapp.awscvs
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, Update, Delete fileSystem on AWS Cloud Volumes Service.

options:
  state:
    description:
    - Whether the specified fileSystem should exist or not.
    required: true
    choices: ['present', 'absent']
    type: str

  region:
    description:
    - The region to which the filesystem belongs to.
    required: true
    type: str

  creationToken:
    description:
    - Name of the filesystem
    required: true
    type: str

  quotaInBytes:
    description:
    - Size of the filesystem
    - Required for create
    type: int

  serviceLevel:
    description:
    - Service Level of a filesystem.
    choices: ['standard', 'premium', 'extreme']
    type: str

  exportPolicy:
    description:
    - The policy rules to export the filesystem
    type: dict
    suboptions:
        rules:
            description:
            - Set of rules to export the filesystem
            - Requires allowedClients, access and protocol
            type: list
            suboptions:
                allowedClients:
                  description:
                  - Comma separated list of ip address blocks of the clients to access the fileSystem
                  - Each address block contains the starting IP address and size for the block
                  type: str

                cifs:
                  description:
                  - Enable or disable cifs filesystem
                  type: bool

                nfsv3:
                  description:
                  - Enable or disable nfsv3 fileSystem
                  type: bool

                nfsv4:
                  description:
                  - Enable or disable nfsv4 filesystem
                  type: bool

                ruleIndex:
                  description:
                  - Index number of the rule
                  type: int

                unixReadOnly:
                  description:
                  - Should fileSystem have read only permission or not
                  type: bool

                unixReadWrite:
                  description:
                  - Should fileSystem have read write permission or not
                  type: bool
'''

EXAMPLES = """
- name: Create FileSystem
  aws_netapp_cvs_FileSystems:
    state: present
    region: us-east-1
    creationToken: newVolume-1
    exportPolicy:
        rules:
          - allowedClients: 172.16.0.4
            cifs: False
            nfsv3: True
            nfsv4: True
            ruleIndex: 1
            unixReadOnly: True
            unixReadWrite: False
    quotaInBytes: 100000000000
    api_url : cds-aws-bundles.netapp.com
    api_key: Q1ZRR0p0VGNuZ3VhMnJBYk5zczM1RkZ3Z0lCbUE3
    secret_key : U1FwdHdKSGRQQUhIdkIwMktMU1ZCV2x6WUowZWRD

- name: Update FileSystem
  aws_netapp_cvs_FileSystems:
     state: present
     region: us-east-1
     creationToken: newVolume-1
     exportPolicy:
         rules:
           - allowedClients: 172.16.0.4
             cifs: False
             nfsv3: True
             nfsv4: True
             ruleIndex: 1
             unixReadOnly: True
             unixReadWrite: False
     quotaInBytes: 200000000000
     api_url : cds-aws-bundles.netapp.com
     api_key: Q1ZRR0p0VGNuZ3VhMnJBYk5zczM1RkZ3Z0lCbUE3
     secret_key : U1FwdHdKSGRQQUhIdkIwMktMU1ZCV2x6WUowZWRD

- name: Delete FileSystem
  aws_netapp_cvs_FileSystems:
     state: present
     region: us-east-1
     creationToken: newVolume-1
     quotaInBytes: 100000000000
     api_url : cds-aws-bundles.netapp.com
     api_key: Q1ZRR0p0VGNuZ3VhMnJBYk5zczM1RkZ3Z0lCbUE3
     secret_key : U1FwdHdKSGRQQUhIdkIwMktMU1ZCV2x6WUowZWRD
"""

RETURN = """
"""

import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.netapp import AwsCvsRestAPI


class AwsCvsNetappFileSystem(object):
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
            creationToken=dict(required=True, type='str'),
            quotaInBytes=dict(required=False, type='int'),
            serviceLevel=dict(required=False, choices=['standard', 'premium', 'extreme']),
            exportPolicy=dict(
                type='dict',
                options=dict(
                    rules=dict(
                        type='list',
                        options=dict(
                            allowedClients=dict(required=False, type='str'),
                            cifs=dict(required=False, type='bool'),
                            nfsv3=dict(required=False, type='bool'),
                            nfsv4=dict(required=False, type='bool'),
                            ruleIndex=dict(required=False, type='int'),
                            unixReadOnly=dict(required=False, type='bool'),
                            unixReadWrite=dict(required=False, type='bool')
                        )
                    )
                )
            ),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['region', 'creationToken', 'quotaInBytes']),
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()

        # set up state variables
        self.parameters = self.na_helper.set_parameters(self.module.params)

        # Calling generic AWSCVS restApi class
        self.restApi = AwsCvsRestAPI(self.module)

        self.data = {}
        for key in self.parameters.keys():
            self.data[key] = self.parameters[key]

    def get_filesystemId(self):
        # Check given FileSystem is exists
        # Return fileSystemId is found, None otherwise
        list_filesystem, error = self.restApi.get('FileSystems')
        if error:
            self.module.fail_json(msg=error)

        for FileSystem in list_filesystem:
            if FileSystem['creationToken'] == self.parameters['creationToken']:
                return FileSystem['fileSystemId']
        return None

    def get_filesystem(self, fileSystemId):
        # Get FileSystem information by fileSystemId
        # Return fileSystem Information
        filesystemInfo, error = self.restApi.get('FileSystems/%s' % fileSystemId)
        if error:
            self.module.fail_json(msg=error)
        else:
            return filesystemInfo
        return None

    def is_job_done(self, response):
        # check jobId is present and equal to 'done'
        # return True on success, False otherwise
        try:
            job_id = response['jobs'][0]['jobId']
        except TypeError:
            job_id = None

        if job_id is not None and self.restApi.get_state(job_id) == 'done':
            return True
        return False

    def create_fileSystem(self):
        # Create fileSystem
        api = 'FileSystems'
        response, error = self.restApi.post(api, self.data)
        if not error:
            if self.is_job_done(response):
                return
            error = "Error: unexpected response on FileSystems create: %s" % str(response)
        self.module.fail_json(msg=error)

    def delete_fileSystem(self, fileSystemId):
        # Delete FileSystem
        api = 'FileSystems/' + fileSystemId
        self.data = None
        response, error = self.restApi.delete(api, self.data)
        if not error:
            if self.is_job_done(response):
                return
            error = "Error: unexpected response on FileSystems delete: %s" % str(response)
        self.module.fail_json(msg=error)

    def update_fileSystem(self, fileSystemId):
        # Update FileSystem
        api = 'FileSystems/' + fileSystemId
        response, error = self.restApi.put(api, self.data)
        if not error:
            if self.is_job_done(response):
                return
            error = "Error: unexpected response on FileSystems update: %s" % str(response)
        self.module.fail_json(msg=error)

    def apply(self):
        """
        Perform pre-checks, call functions and exit
        """

        fileSystem = None
        fileSystemId = self.get_filesystemId()

        if fileSystemId:
            # Getting the FileSystem details
            fileSystem = self.get_filesystem(fileSystemId)

        cd_action = self.na_helper.get_cd_action(fileSystem, self.parameters)

        if cd_action is None and self.parameters['state'] == 'present':
            # Check if we need to update the fileSystem
            update_fileSystem = False
            if fileSystem['quotaInBytes'] is not None and 'quotaInBytes' in self.parameters \
                    and fileSystem['quotaInBytes'] != self.parameters['quotaInBytes']:
                update_fileSystem = True
            elif fileSystem['creationToken'] is not None and 'creationToken' in self.parameters \
                    and fileSystem['creationToken'] != self.parameters['creationToken']:
                update_fileSystem = True
            elif fileSystem['serviceLevel'] is not None and 'serviceLevel' in self.parameters \
                    and fileSystem['serviceLevel'] != self.parameters['serviceLevel']:
                update_fileSystem = True
            elif fileSystem['exportPolicy']['rules'] is not None and 'exportPolicy' in self.parameters:
                for rule_org in fileSystem['exportPolicy']['rules']:
                    for rule in self.parameters['exportPolicy']['rules']:
                        if rule_org['allowedClients'] != rule['allowedClients']:
                            update_fileSystem = True
                        elif rule_org['unixReadOnly'] != rule['unixReadOnly']:
                            update_fileSystem = True
                        elif rule_org['unixReadWrite'] != rule['unixReadWrite']:
                            update_fileSystem = True

            if update_fileSystem:
                self.na_helper.changed = True

        result_message = ""

        if self.na_helper.changed:
            if self.module.check_mode:
                # Skip changes
                result_message = "Check mode, skipping changes"
            else:
                if cd_action == "create":
                    self.create_fileSystem()
                    result_message = "FileSystem Created"
                elif cd_action == "delete":
                    self.delete_fileSystem(fileSystemId)
                    result_message = "FileSystem Deleted"
                else:   # modify
                    self.update_fileSystem(fileSystemId)
                    result_message = "FileSystem Updated"
        self.module.exit_json(changed=self.na_helper.changed, msg=result_message)


def main():
    """
    Main function
    """
    aws_cvs_netapp_filesystem = AwsCvsNetappFileSystem()
    aws_cvs_netapp_filesystem.apply()


if __name__ == '__main__':
    main()
