#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Element OS Software Volume Manager"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_volume

short_description: NetApp Element Software Manage Volumes
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Create, destroy, or update volumes on ElementSW

options:

    state:
        description:
        - Whether the specified volume should exist or not.
        required: true
        choices: ['present', 'absent']

    name:
        description:
        - The name of the volume to manage.
        - It accepts volume_name or volume_id
        required: true

    account_id:
        description:
        - Account ID for the owner of this volume.
        - It accepts Account_id or Account_name
        required: true

    enable512e:
        description:
        - Required when C(state=present)
        - Should the volume provide 512-byte sector emulation?
        type: bool
        aliases:
        - 512emulation

    qos:
        description: Initial quality of service settings for this volume. Configure as dict in playbooks.

    attributes:
        description: A YAML dictionary of attributes that you would like to apply on this volume.

    size:
        description:
        - The size of the volume in (size_unit).
        - Required when C(state = present).

    size_unit:
        description:
        - The unit used to interpret the size parameter.
        choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
        default: 'gb'

    access:
        description:
        - Access allowed for the volume.
        - readOnly           Only read operations are allowed.
        - readWrite          Reads and writes are allowed.
        - locked             No reads or writes are allowed.
        - replicationTarget  Identify a volume as the target volume for a paired set of volumes.
        - If the volume is not paired, the access status is locked.
        - If unspecified, the access settings of the clone will be the same as the source.
        choices: ['readOnly', 'readWrite', 'locked', 'replicationTarget']

    password:
        description:
        - ElementSW access account password
        aliases:
        - pass

    username:
        description:
        - ElementSW access account user-name
        aliases:
        - user

'''

EXAMPLES = """
   - name: Create Volume
     na_elementsw_volume:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       name: AnsibleVol
       qos: {minIOPS: 1000, maxIOPS: 20000, burstIOPS: 50000}
       account_id: 3
       enable512e: False
       size: 1
       size_unit: gb

   - name: Update Volume
     na_elementsw_volume:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: present
       name: AnsibleVol
       account_id: 3
       access: readWrite

   - name: Delete Volume
     na_elementsw_volume:
       hostname: "{{ elementsw_hostname }}"
       username: "{{ elementsw_username }}"
       password: "{{ elementsw_password }}"
       state: absent
       name: AnsibleVol
       account_id: 2
"""

RETURN = """

msg:
    description: Success message
    returned: success
    type: str

"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_elementsw_module import NaElementSWModule

HAS_SF_SDK = netapp_utils.has_sf_sdk()
try:
    import solidfire.common
except Exception:
    HAS_SF_SDK = False


class ElementOSVolume(object):
    """
    Contains methods to parse arguments,
    derive details of  ElementSW objects
    and send requests to ElementOS via
    the ElementSW SDK
    """

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check parameters and ensure SDK is installed
        """
        self._size_unit_map = netapp_utils.SF_BYTE_MAP

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            account_id=dict(required=True),
            enable512e=dict(type='bool', aliases=['512emulation']),
            qos=dict(required=False, type='dict', default=None),
            attributes=dict(required=False, type='dict', default=None),
            size=dict(type='int'),
            size_unit=dict(default='gb',
                           choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                    'pb', 'eb', 'zb', 'yb'], type='str'),

            access=dict(required=False, type='str', default=None, choices=['readOnly', 'readWrite',
                                                                           'locked', 'replicationTarget']),

        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['size', 'enable512e'])
            ],
            supports_check_mode=True
        )

        param = self.module.params

        # set up state variables
        self.state = param['state']
        self.name = param['name']
        self.account_id = param['account_id']
        self.enable512e = param['enable512e']
        self.qos = param['qos']
        self.attributes = param['attributes']
        self.access = param['access']
        self.size_unit = param['size_unit']
        if param['size'] is not None:
            self.size = param['size'] * self._size_unit_map[self.size_unit]
        else:
            self.size = None

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the ElementSW Python SDK")
        else:
            try:
                self.sfe = netapp_utils.create_sf_connection(module=self.module)
            except solidfire.common.ApiServerError:
                self.module.fail_json(msg="Unable to create the connection")

        self.elementsw_helper = NaElementSWModule(self.sfe)

        # add telemetry attributes
        if self.attributes is not None:
            self.attributes.update(self.elementsw_helper.set_element_attributes(source='na_elementsw_volume'))
        else:
            self.attributes = self.elementsw_helper.set_element_attributes(source='na_elementsw_volume')

    def get_account_id(self):
        """
            Return account id if found
        """
        try:
            # Update and return self.account_id
            self.account_id = self.elementsw_helper.account_exists(self.account_id)
            return self.account_id
        except Exception as err:
            self.module.fail_json(msg="Error: account_id %s does not exist" % self.account_id, exception=to_native(err))

    def get_volume(self):
        """
            Return volume details if found
        """
        # Get volume details
        volume_id = self.elementsw_helper.volume_exists(self.name, self.account_id)

        if volume_id is not None:
            # Return volume_details
            volume_details = self.elementsw_helper.get_volume(volume_id)
            if volume_details is not None:
                return volume_details
        return None

    def create_volume(self):
        """
        Create Volume

        :return: True if created, False if fails
        """
        try:
            self.sfe.create_volume(name=self.name,
                                   account_id=self.account_id,
                                   total_size=self.size,
                                   enable512e=self.enable512e,
                                   qos=self.qos,
                                   attributes=self.attributes)

        except Exception as err:
            self.module.fail_json(msg="Error provisioning volume %s of size %s" % (self.name, self.size),
                                  exception=to_native(err))

    def delete_volume(self, volume_id):
        """
         Delete and purge the volume using volume id

         :return: Success : True , Failed : False
        """
        try:
            self.sfe.delete_volume(volume_id=volume_id)
            self.sfe.purge_deleted_volume(volume_id=volume_id)
            # Delete method will delete and also purge the volume instead of moving the volume state to inactive.

        except Exception as err:
            # Throwing the exact error message instead of generic error message
            self.module.fail_json(msg=err.message,
                                  exception=to_native(err))

    def update_volume(self, volume_id):
        """

        Update the volume with the specified param

        :return: Success : True, Failed : False
        """
        try:
            self.sfe.modify_volume(volume_id,
                                   account_id=self.account_id,
                                   access=self.access,
                                   qos=self.qos,
                                   total_size=self.size,
                                   attributes=self.attributes)

        except Exception as err:
            # Throwing the exact error message instead of generic error message
            self.module.fail_json(msg=err.message,
                                  exception=to_native(err))

    def apply(self):
        # Perform pre-checks, call functions and exit
        changed = False
        volume_exists = False
        update_volume = False

        self.get_account_id()
        volume_detail = self.get_volume()

        if volume_detail:
            volume_exists = True
            volume_id = volume_detail.volume_id
            if self.state == 'absent':
                # Checking for state change(s) here, and applying it later in the code allows us to support
                # check_mode

                changed = True

            elif self.state == 'present':
                # Checking all the params for update operation
                if volume_detail.access is not None and self.access is not None and volume_detail.access != self.access:
                    update_volume = True
                    changed = True

                elif volume_detail.account_id is not None and self.account_id is not None \
                        and volume_detail.account_id != self.account_id:
                    update_volume = True
                    changed = True

                elif volume_detail.qos is not None and self.qos is not None:
                    """
                    Actual volume_detail.qos has ['burst_iops', 'burst_time', 'curve', 'max_iops', 'min_iops'] keys.
                    As only minOPS, maxOPS, burstOPS is important to consider, checking only these values.
                    """
                    volume_qos = volume_detail.qos.__dict__
                    if volume_qos['min_iops'] != self.qos['minIOPS'] or volume_qos['max_iops'] != self.qos['maxIOPS'] \
                       or volume_qos['burst_iops'] != self.qos['burstIOPS']:
                        update_volume = True
                        changed = True
                else:
                    # If check fails, do nothing
                    pass

                if volume_detail.total_size is not None and volume_detail.total_size != self.size:
                    size_difference = abs(float(volume_detail.total_size - self.size))
                    # Change size only if difference is bigger than 0.001
                    if size_difference / self.size > 0.001:
                        update_volume = True
                        changed = True

                else:
                    # If check fails, do nothing
                    pass

                if volume_detail.attributes is not None and self.attributes is not None and \
                        volume_detail.attributes != self.attributes:
                    update_volume = True
                    changed = True
        else:
            if self.state == 'present':
                changed = True

        result_message = ""

        if changed:
            if self.module.check_mode:
                result_message = "Check mode, skipping changes"
            else:
                if self.state == 'present':
                    if not volume_exists:
                        self.create_volume()
                        result_message = "Volume created"
                    elif update_volume:
                        self.update_volume(volume_id)
                        result_message = "Volume updated"

                elif self.state == 'absent':
                    self.delete_volume(volume_id)
                    result_message = "Volume deleted"

        self.module.exit_json(changed=changed, msg=result_message)


def main():
    # Create object and call apply
    na_elementsw_volume = ElementOSVolume()
    na_elementsw_volume.apply()


if __name__ == '__main__':
    main()
