#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

'''
Element Software Configure cluster
'''
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_elementsw_cluster_config

short_description: Configure Element SW Cluster
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.8'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Configure Element Software cluster.

options:
    modify_cluster_full_threshold:
        description:
        -  The capacity level at which the cluster generates an event
        -  Requires a stage3_block_threshold_percent or
        -  max_metadata_over_provision_factor or
        -  stage2_aware_threshold
        suboptions:
            stage3_block_threshold_percent:
                description:
                - The percentage below the "Error" threshold that triggers a cluster "Warning" alert

            max_metadata_over_provision_factor:
                description:
                - The number of times metadata space can be overprovisioned relative to the amount of space available

            stage2_aware_threshold:
                description:
                - The number of nodes of capacity remaining in the cluster before the system triggers a notification

    encryption_at_rest:
        description:
        - enable or disable the Advanced Encryption Standard (AES) 256-bit encryption at rest on the cluster
        choices: ['present', 'absent']

    set_ntp_info:
        description:
        - configure NTP on cluster node
        - Requires a list of one or more ntp_servers
        suboptions:
            ntp_servers:
                description:
                - list of NTP servers to add to each nodes NTP configuration

            broadcastclient:
                type: bool
                default: False
                description:
                - Enables every node in the cluster as a broadcast client

    enable_virtual_volumes:
        type: bool
        default: True
        description:
        - Enable the NetApp SolidFire VVols cluster feature
'''

EXAMPLES = """

  - name: Configure cluster
    tags:
    - elementsw_cluster_config
    na_elementsw_cluster_config:
      hostname: "{{ elementsw_hostname }}"
      username: "{{ elementsw_username }}"
      password: "{{ elementsw_password }}"
      modify_cluster_full_threshold:
        stage2_aware_threshold: 2
        stage3_block_threshold_percent: 10
        max_metadata_over_provision_factor: 2
      encryption_at_rest: absent
      set_ntp_info:
        broadcastclient: False
        ntp_servers:
        - 1.1.1.1
        - 2.2.2.2
      enable_virtual_volumes: True
"""

RETURN = """

msg:
    description: Success message
    returned: success
    type: str

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule
from ansible.module_utils.netapp_module import NetAppModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class ElementSWClusterConfig(object):
    """
    Element Software Configure Element SW Cluster
    """
    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()

        self.argument_spec.update(dict(
            modify_cluster_full_threshold=dict(
                type='dict',
                options=dict(
                    stage2_aware_threshold=dict(type='int', default=None),
                    stage3_block_threshold_percent=dict(type='int', default=None),
                    max_metadata_over_provision_factor=dict(type='int', default=None)
                )
            ),
            encryption_at_rest=dict(type='str', choices=['present', 'absent']),
            set_ntp_info=dict(
                type='dict',
                options=dict(
                    broadcastclient=dict(type='bool', default=False),
                    ntp_servers=dict(type='list')
                )
            ),
            enable_virtual_volumes=dict(type='bool', default=True)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module)

    def get_ntp_details(self):
        """
        get ntp info
        """
        # Get ntp details
        ntp_details = self.sfe.get_ntp_info()
        return ntp_details

    def cmp(self, provided_ntp_servers, existing_ntp_servers):
        # As python3 doesn't have default cmp function, defining manually to provide same functionality.
        return (provided_ntp_servers > existing_ntp_servers) - (provided_ntp_servers < existing_ntp_servers)

    def get_cluster_details(self):
        """
        get cluster info
        """
        cluster_details = self.sfe.get_cluster_info()
        return cluster_details

    def get_vvols_status(self):
        """
        get vvols status
        """
        feature_status = self.sfe.get_feature_status(feature='vvols')
        if feature_status is not None:
            return feature_status.features[0].enabled
        return None

    def get_cluster_full_threshold_status(self):
        """
        get cluster full threshold
        """
        cluster_full_threshold_status = self.sfe.get_cluster_full_threshold()
        return cluster_full_threshold_status

    def setup_ntp_info(self, servers, broadcastclient=None):
        """
        configure ntp
        """
        # Set ntp servers
        try:
            self.sfe.set_ntp_info(servers, broadcastclient)
        except Exception as exception_object:
            self.module.fail_json(msg='Error configuring ntp %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def set_encryption_at_rest(self, state=None):
        """
        enable/disable encryption at rest
        """
        try:
            if state == 'present':
                encryption_state = 'enable'
                self.sfe.enable_encryption_at_rest()
            elif state == 'absent':
                encryption_state = 'disable'
                self.sfe.disable_encryption_at_rest()
        except Exception as exception_object:
            self.module.fail_json(msg='Failed to %s rest encryption %s' % (encryption_state,
                                  to_native(exception_object)),
                                  exception=traceback.format_exc())

    def enable_feature(self, feature):
        """
        enable feature
        """
        try:
            self.sfe.enable_feature(feature=feature)
        except Exception as exception_object:
            self.module.fail_json(msg='Error enabling %s %s' % (feature, to_native(exception_object)),
                                  exception=traceback.format_exc())

    def set_cluster_full_threshold(self, stage2_aware_threshold=None,
                                   stage3_block_threshold_percent=None,
                                   max_metadata_over_provision_factor=None):
        """
        modify cluster full threshold
        """
        try:
            self.sfe.modify_cluster_full_threshold(stage2_aware_threshold=stage2_aware_threshold,
                                                   stage3_block_threshold_percent=stage3_block_threshold_percent,
                                                   max_metadata_over_provision_factor=max_metadata_over_provision_factor)
        except Exception as exception_object:
            self.module.fail_json(msg='Failed to modify cluster full threshold %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def apply(self):
        """
        Cluster configuration
        """
        changed = False
        result_message = None

        if self.parameters.get('modify_cluster_full_threshold') is not None:
            # get cluster full threshold
            cluster_full_threshold_details = self.get_cluster_full_threshold_status()
            # maxMetadataOverProvisionFactor
            current_mmopf = cluster_full_threshold_details.max_metadata_over_provision_factor
            # stage3BlockThresholdPercent
            current_s3btp = cluster_full_threshold_details.stage3_block_threshold_percent
            # stage2AwareThreshold
            current_s2at = cluster_full_threshold_details.stage2_aware_threshold

            # is cluster full threshold state change required?
            if self.parameters.get("modify_cluster_full_threshold")['max_metadata_over_provision_factor'] is not None and \
                    current_mmopf != self.parameters['modify_cluster_full_threshold']['max_metadata_over_provision_factor'] or \
                    self.parameters.get("modify_cluster_full_threshold")['stage3_block_threshold_percent'] is not None and \
                    current_s3btp != self.parameters['modify_cluster_full_threshold']['stage3_block_threshold_percent'] or \
                    self.parameters.get("modify_cluster_full_threshold")['stage2_aware_threshold'] is not None and \
                    current_s2at != self.parameters['modify_cluster_full_threshold']['stage2_aware_threshold']:
                changed = True
                self.set_cluster_full_threshold(self.parameters['modify_cluster_full_threshold']['stage2_aware_threshold'],
                                                self.parameters['modify_cluster_full_threshold']['stage3_block_threshold_percent'],
                                                self.parameters['modify_cluster_full_threshold']['max_metadata_over_provision_factor'])

        if self.parameters.get('encryption_at_rest') is not None:
            # get all cluster info
            cluster_info = self.get_cluster_details()
            # register rest state
            current_encryption_at_rest_state = cluster_info.cluster_info.encryption_at_rest_state

            # is encryption state change required?
            if current_encryption_at_rest_state == 'disabled' and self.parameters['encryption_at_rest'] == 'present' or \
               current_encryption_at_rest_state == 'enabled' and self.parameters['encryption_at_rest'] == 'absent':
                changed = True
                self.set_encryption_at_rest(self.parameters['encryption_at_rest'])

        if self.parameters.get('set_ntp_info') is not None:
            # get all ntp details
            ntp_details = self.get_ntp_details()
            # register list of ntp servers
            ntp_servers = ntp_details.servers
            # broadcastclient
            broadcast_client = ntp_details.broadcastclient

            # has either the broadcastclient or the ntp server list changed?

            if self.parameters.get('set_ntp_info')['broadcastclient'] != broadcast_client or \
               self.cmp(self.parameters.get('set_ntp_info')['ntp_servers'], ntp_servers) != 0:
                changed = True
                self.setup_ntp_info(self.parameters.get('set_ntp_info')['ntp_servers'],
                                    self.parameters.get('set_ntp_info')['broadcastclient'])

        if self.parameters.get('enable_virtual_volumes') is not None:
            # check vvols status
            current_vvols_status = self.get_vvols_status()

            # has the vvols state changed?
            if current_vvols_status is False and self.parameters.get('enable_virtual_volumes') is True:
                changed = True
                self.enable_feature('vvols')
            elif current_vvols_status is True and self.parameters.get('enable_virtual_volumes') is not True:
                # vvols, once enabled, cannot be disabled
                self.module.fail_json(msg='Error disabling vvols: this feature cannot be undone')

        if self.module.check_mode is True:
            result_message = "Check mode, skipping changes"
        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """
    na_elementsw_cluster_config = ElementSWClusterConfig()
    na_elementsw_cluster_config.apply()


if __name__ == '__main__':
    main()
