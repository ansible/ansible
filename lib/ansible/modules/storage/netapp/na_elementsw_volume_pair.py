#!/usr/bin/python
# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''

module: na_elementsw_volume_pair

short_description: NetApp Element Software Volume Pair
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, delete volume pair

options:

    state:
      description:
      - Whether the specified volume pair should exist or not.
      choices: ['present', 'absent']
      default: present

    src_volume:
      description:
      - Source volume name or volume ID
      required: true

    src_account:
      description:
      - Source account name or ID
      required: true

    dest_volume:
      description:
      - Destination volume name or volume ID
      required: true

    dest_account:
      description:
      - Destination account name or ID
      required: true

    mode:
      description:
      - Mode to start the volume pairing
      choices: ['async', 'sync', 'snapshotsonly']
      default: async

    dest_mvip:
      description:
      - Destination IP address of the paired cluster.
      required: true

    dest_username:
      description:
      - Destination username for the paired cluster
      - Optional if this is same as source cluster username.

    dest_password:
      description:
      - Destination password for the paired cluster
      - Optional if this is same as source cluster password.

'''

EXAMPLES = """
   - name: Create volume pair
     na_elementsw_volume_pair:
       hostname: "{{ src_cluster_hostname }}"
       username: "{{ src_cluster_username }}"
       password: "{{ src_cluster_password }}"
       state: present
       src_volume: test1
       src_account: test2
       dest_volume: test3
       dest_account: test4
       mode: sync
       dest_mvip: "{{ dest_cluster_hostname }}"

   - name: Delete volume pair
     na_elementsw_volume_pair:
       hostname: "{{ src_cluster_hostname }}"
       username: "{{ src_cluster_username }}"
       password: "{{ src_cluster_password }}"
       state: absent
       src_volume: 3
       src_account: 1
       dest_volume: 2
       dest_account: 1
       dest_mvip: "{{ dest_cluster_hostname }}"
       dest_username: "{{ dest_cluster_username }}"
       dest_password: "{{ dest_cluster_password }}"

"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule
from ansible.module_utils.netapp_module import NetAppModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    import solidfire.common
except ImportError:
    HAS_SF_SDK = False


class ElementSWVolumePair(object):
    ''' class to handle volume pairing operations '''

    def __init__(self):
        """
            Setup Ansible parameters and SolidFire connection
        """
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
            src_volume=dict(required=True, type='str'),
            src_account=dict(required=True, type='str'),
            dest_volume=dict(required=True, type='str'),
            dest_account=dict(required=True, type='str'),
            mode=dict(required=False, type='str',
                      choices=['async', 'sync', 'snapshotsonly'],
                      default='async'),
            dest_mvip=dict(required=True, type='str'),
            dest_username=dict(required=False, type='str'),
            dest_password=dict(required=False, type='str', no_log=True)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.elem = netapp_utils.create_sf_connection(module=self.module)

        self.elementsw_helper = NaElementSWModule(self.elem)
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # get element_sw_connection for destination cluster
        # overwrite existing source host, user and password with destination credentials
        self.module.params['hostname'] = self.parameters['dest_mvip']
        # username and password is same as source,
        # if dest_username and dest_password aren't specified
        if self.parameters.get('dest_username'):
            self.module.params['username'] = self.parameters['dest_username']
        if self.parameters.get('dest_password'):
            self.module.params['password'] = self.parameters['dest_password']
        self.dest_elem = netapp_utils.create_sf_connection(module=self.module)
        self.dest_elementsw_helper = NaElementSWModule(self.dest_elem)

    def check_if_already_paired(self, vol_id):
        """
            Check for idempotency
            A volume can have only one pair
            Return paired-volume-id if volume is paired already
            None if volume is not paired
        """
        paired_volumes = self.elem.list_volumes(volume_ids=[vol_id],
                                                is_paired=True)
        for vol in paired_volumes.volumes:
            for pair in vol.volume_pairs:
                if pair is not None:
                    return pair.remote_volume_id
        return None

    def pair_volumes(self):
        """
            Start volume pairing on source, and complete on target volume
        """
        try:
            pair_key = self.elem.start_volume_pairing(
                volume_id=self.parameters['src_vol_id'],
                mode=self.parameters['mode'])
            self.dest_elem.complete_volume_pairing(
                volume_pairing_key=pair_key.volume_pairing_key,
                volume_id=self.parameters['dest_vol_id'])
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error pairing volume id %s"
                                      % (self.parameters['src_vol_id']),
                                  exception=to_native(err))

    def pairing_exists(self, src_id, dest_id):
        src_paired = self.check_if_already_paired(self.parameters['src_vol_id'])
        dest_paired = self.check_if_already_paired(self.parameters['dest_vol_id'])
        if src_paired is not None or dest_paired is not None:
            return True
        return None

    def unpair_volumes(self):
        """
            Delete volume pair
        """
        try:
            self.elem.remove_volume_pair(volume_id=self.parameters['src_vol_id'])
            self.dest_elem.remove_volume_pair(volume_id=self.parameters['dest_vol_id'])
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error unpairing volume ids %s and %s"
                                      % (self.parameters['src_vol_id'],
                                         self.parameters['dest_vol_id']),
                                  exception=to_native(err))

    def get_account_id(self, account, type):
        """
            Get source and destination account IDs
        """
        try:
            if type == 'src':
                self.parameters['src_account_id'] = self.elementsw_helper.account_exists(account)
            elif type == 'dest':
                self.parameters['dest_account_id'] = self.dest_elementsw_helper.account_exists(account)
        except solidfire.common.ApiServerError as err:
            self.module.fail_json(msg="Error: either account %s or %s does not exist"
                                      % (self.parameters['src_account'],
                                         self.parameters['dest_account']),
                                  exception=to_native(err))

    def get_volume_id(self, volume, type):
        """
            Get source and destination volume IDs
        """
        if type == 'src':
            self.parameters['src_vol_id'] = self.elementsw_helper.volume_exists(volume, self.parameters['src_account_id'])
            if self.parameters['src_vol_id'] is None:
                self.module.fail_json(msg="Error: source volume %s does not exist"
                                          % (self.parameters['src_volume']))
        elif type == 'dest':
            self.parameters['dest_vol_id'] = self.dest_elementsw_helper.volume_exists(volume, self.parameters['dest_account_id'])
            if self.parameters['dest_vol_id'] is None:
                self.module.fail_json(msg="Error: destination volume %s does not exist"
                                      % (self.parameters['dest_volume']))

    def get_ids(self):
        """
            Get IDs for volumes and accounts
        """
        self.get_account_id(self.parameters['src_account'], 'src')
        self.get_account_id(self.parameters['dest_account'], 'dest')
        self.get_volume_id(self.parameters['src_volume'], 'src')
        self.get_volume_id(self.parameters['dest_volume'], 'dest')

    def apply(self):
        """
            Call create / delete volume pair methods
        """
        self.get_ids()
        paired = self.pairing_exists(self.parameters['src_vol_id'],
                                     self.parameters['dest_vol_id'])
        # calling helper to determine action
        cd_action = self.na_helper.get_cd_action(paired, self.parameters)
        if cd_action == "create":
            self.pair_volumes()
        elif cd_action == "delete":
            self.unpair_volumes()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """ Apply volume pair actions """
    vol_obj = ElementSWVolumePair()
    vol_obj.apply()


if __name__ == '__main__':
    main()
