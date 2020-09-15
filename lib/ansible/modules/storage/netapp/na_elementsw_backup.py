#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Element Software Backup Manager
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''

module: na_elementsw_backup

short_description: NetApp Element Software Create Backups
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create backup

options:

    src_volume_id:
        description:
        - ID of the backup source volume.
        required: true
        aliases:
        - volume_id

    dest_hostname:
        description:
        - hostname for the backup source cluster
        - will be set equal to hostname if not specified
        required: false

    dest_username:
        description:
        - username for the backup destination cluster
        - will be set equal to username if not specified
        required: false

    dest_password:
        description:
        - password for the backup destination cluster
        - will be set equal to password if not specified
        required: false

    dest_volume_id:
        description:
        - ID of the backup destination volume
        required: true

    format:
        description:
        - Backup format to use
        choices: ['native','uncompressed']
        required: false
        default: 'native'

    script:
        description:
        - the backup script to be executed
        required: false

    script_parameters:
        description:
        - the backup script parameters
        required: false

'''

EXAMPLES = """
na_elementsw_backup:
  hostname: "{{ source_cluster_hostname }}"
  username: "{{ source_cluster_username }}"
  password: "{{ source_cluster_password }}"
  src_volume_id: 1
  dest_hostname: "{{ destination_cluster_hostname }}"
  dest_username: "{{ destination_cluster_username }}"
  dest_password: "{{ destination_cluster_password }}"
  dest_volume_id: 3
  format: native
"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule
import time

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    import solidfire.common
except ImportError:
    HAS_SF_SDK = False


class ElementSWBackup(object):
    ''' class to handle backup operations '''

    def __init__(self):
        """
            Setup Ansible parameters and SolidFire connection
        """
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()

        self.argument_spec.update(dict(

            src_volume_id=dict(aliases=['volume_id'], required=True, type='str'),
            dest_hostname=dict(required=False, type='str'),
            dest_username=dict(required=False, type='str'),
            dest_password=dict(required=False, type='str', no_log=True),
            dest_volume_id=dict(required=True, type='str'),
            format=dict(required=False, choices=['native', 'uncompressed'], default='native'),
            script=dict(required=False, type='str'),
            script_parameters=dict(required=False, type='dict')


        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_together=[['script', 'script_parameters']],
            supports_check_mode=True
        )
        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")

        # If destination cluster details are not specified , set the destination to be the same as the source
        if self.module.params["dest_hostname"] is None:
            self.module.params["dest_hostname"] = self.module.params["hostname"]
        if self.module.params["dest_username"] is None:
            self.module.params["dest_username"] = self.module.params["username"]
        if self.module.params["dest_password"] is None:
            self.module.params["dest_password"] = self.module.params["password"]

        params = self.module.params

        # establish a connection to both source and destination elementsw clusters
        self.src_connection = netapp_utils.create_sf_connection(self.module)
        self.module.params["username"] = params["dest_username"]
        self.module.params["password"] = params["dest_password"]
        self.module.params["hostname"] = params["dest_hostname"]
        self.dest_connection = netapp_utils.create_sf_connection(self.module)

        self.elementsw_helper = NaElementSWModule(self.src_connection)

        # add telemetry attributes
        self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_backup')

    def apply(self):
        """
            Apply backup creation logic
        """
        self.create_backup()
        self.module.exit_json(changed=True)

    def create_backup(self):
        """
            Create backup
        """

        # Start volume write on destination cluster

        try:
            write_obj = self.dest_connection.start_bulk_volume_write(volume_id=self.module.params["dest_volume_id"],
                                                                     format=self.module.params["format"],
                                                                     attributes=self.attributes)
            write_key = write_obj.key
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error starting bulk write on destination cluster", exception=to_native(err))

        # Set script parameters if not passed by user
        # These parameters are equivalent to the options used when a backup is executed via the GUI

        if self.module.params["script"] is None and self.module.params["script_parameters"] is None:

            self.module.params["script"] = 'bv_internal.py'
            self.module.params["script_parameters"] = {"write": {
                "mvip": self.module.params["dest_hostname"],
                "username": self.module.params["dest_username"],
                "password": self.module.params["dest_password"],
                "key": write_key,
                "endpoint": "solidfire",
                "format": self.module.params["format"]},
                "range": {"lba": 0, "blocks": 244224}}

        # Start volume read on source cluster

        try:
            read_obj = self.src_connection.start_bulk_volume_read(self.module.params["src_volume_id"],
                                                                  self.module.params["format"],
                                                                  script=self.module.params["script"],
                                                                  script_parameters=self.module.params["script_parameters"],
                                                                  attributes=self.attributes)
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error starting bulk read on source cluster", exception=to_native(err))

        # Poll job status until it has completed
        # SF will automatically timeout if the job is not successful after certain amount of time

        completed = False
        while completed is not True:
            # Sleep between polling iterations to reduce api load
            time.sleep(2)
            try:
                result = self.src_connection.get_async_result(read_obj.async_handle, True)
            except solidfire.common.ApiServerError as err:
                self.module.fail_json(msg="Unable to check backup job status", exception=to_native(err))

            if result["status"] != 'running':
                completed = True
        if 'error' in result:
            self.module.fail_json(msg=result['error']['message'])


def main():
    """ Run backup operation"""
    vol_obj = ElementSWBackup()
    vol_obj.apply()


if __name__ == '__main__':
    main()
