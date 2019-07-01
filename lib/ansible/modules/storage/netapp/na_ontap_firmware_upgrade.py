#!/usr/bin/python

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
  - Update ONTAP service-prosessor firmware
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_firmware_upgrade
options:
  state:
    description:
      - Whether the specified ONTAP firmware should  be upgraded or not.
    default: present
    type: str
  node:
    description:
      - Node on which the device is located.
    type: str
    required: true
  clear_logs:
    description:
      - Clear logs on the device after update. Default value is true
    type: bool
    default: true
  package:
    description:
      - Name of the package file containing the firmware to be installed. Not required when -baseline is true.
    type: str
  shelf_module_fw:
    description:
      - Shelf module firmware to be updated to.
    type: str
  disk_fw:
    description:
      - disk firmware to be updated to.
    type: str
  update_type:
    description:
      -  Type of firmware update to be performed. Options include serial_full, serial_differential, network_full.
    type: str
  install_baseline_image:
    description:
      - Install the version packaged with ONTAP if this parameter is set to true. Otherwise, package must be used to specify the package to install.
    type: bool
    default: false
  firmware_type:
    description:
      - Type of firmware to be upgraded. Options include shelf, ACP, service-processor, and disk.
      - For shelf firmware upgrade the operation is asynchronous, and therefore returns no errors that might occur during the download process.
      - Shelf firmware upgrade is idempotent if shelf_module_fw is provided .
      - disk firmware upgrade is idempotent if disk_fw is provided .
      - With check mode, SP, ACP, disk, and shelf firmware upgrade is not idempotent.
      - This operation will only update firmware on shelves/disk that do not have the latest firmware-revision.
    choices: ['service-processor', 'shelf', 'acp', 'disk']
    type: str
short_description:  NetApp ONTAP firmware upgrade for SP, shelf, ACP, and disk.
version_added: "2.9"
'''

EXAMPLES = """

    - name: SP firmware upgrade
      na_ontap_firmware_upgrade:
        state: present
        node: vsim1
        package: "{{ file name }}"
        clear_logs: True
        install_baseline_image: False
        update_type: serial_full
        firmware_type: service-processor
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: ACP firmware upgrade
      na_ontap_firmware_upgrade:
        state: present
        node: vsim1
        firmware_type: acp
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: shelf firmware upgrade
      na_ontap_firmware_upgrade:
        state: present
        firmware_type: shelf
        shelf_module_fw: 1221
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
    - name: disk firmware upgrade
      na_ontap_firmware_upgrade:
        state: present
        firmware_type: disk
        disk_fw: NA02
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
"""

RETURN = """
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
import time

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPFirmwareUpgrade(object):
    """
    Class with ONTAP firmware upgrade methods
    """

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', default='present'),
            node=dict(required=False, type='str'),
            firmware_type=dict(required=True, type='str', choices=['service-processor', 'shelf', 'acp', 'disk']),
            clear_logs=dict(required=False, type='bool', default=True),
            package=dict(required=False, type='str'),
            install_baseline_image=dict(required=False, type='bool', default=False),
            update_type=dict(required=False, type='str'),
            shelf_module_fw=dict(required=False, type='str'),
            disk_fw=dict(required=False, type='str')

        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('firmware_type', 'acp', ['node']),
                ('firmware_type', 'disk', ['node']),
                ('firmware_type', 'service-processor', ['node', 'update_type']),
            ],
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        if self.parameters.get('firmware_type') == 'service-processor':
            if self.parameters.get('install_baseline_image') and self.parameters.get('package') is not None:
                self.module.fail_json(msg='Do not specify both package and install_baseline_image: true')
            if not self.parameters.get('package') and self.parameters.get('install_baseline_image') == 'False':
                self.module.fail_json(msg='Specify at least one of package or install_baseline_image')
        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def firmware_image_get_iter(self):
        """
        Compose NaElement object to query current firmware version
        :return: NaElement object for firmware_image_get_iter with query
        """
        firmware_image_get = netapp_utils.zapi.NaElement('service-processor-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        firmware_image_info = netapp_utils.zapi.NaElement('service-processor-info')
        firmware_image_info.add_new_child('node', self.parameters['node'])
        query.add_child_elem(firmware_image_info)
        firmware_image_get.add_child_elem(query)
        return firmware_image_get

    def firmware_image_get(self, node_name):
        """
        Get current firmware image info
        :return: True if query successful, else return None
        """
        firmware_image_get_iter = self.firmware_image_get_iter()
        try:
            result = self.server.invoke_successfully(firmware_image_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching firmware image details: %s: %s'
                                      % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())
        # return firmware image details
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            sp_info = result.get_child_by_name('attributes-list').get_child_by_name('service-processor-info')
            firmware_version = sp_info.get_child_content('firmware-version')
            return firmware_version
        return None

    def acp_firmware_required_get(self):
        """
        where acp firmware upgrade is required
        :return:  True is firmware upgrade is required else return None
        """
        acp_firmware_get_iter = netapp_utils.zapi.NaElement('storage-shelf-acp-module-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        acp_info = netapp_utils.zapi.NaElement('storage-shelf-acp-module')
        query.add_child_elem(acp_info)
        acp_firmware_get_iter.add_child_elem(query)
        try:
            result = self.server.invoke_successfully(acp_firmware_get_iter, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching acp firmware details details: %s'
                                  % (to_native(error)), exception=traceback.format_exc())
        if result.get_child_by_name('attributes-list').get_child_by_name('storage-shelf-acp-module'):
            acp_module_info = result.get_child_by_name('attributes-list').get_child_by_name(
                'storage-shelf-acp-module')
            state = acp_module_info.get_child_content('state')
            if state == 'firmware_update_required':
                # acp firmware version upgrade required
                return True
        return False

    def sp_firmware_image_update_progress_get(self, node_name):
        """
        Get current firmware image update progress info
        :return: Dictionary of firmware image update progress if query successful, else return None
        """
        firmware_update_progress_get = netapp_utils.zapi.NaElement('service-processor-image-update-progress-get')
        firmware_update_progress_get.add_new_child('node', self.parameters['node'])

        firmware_update_progress_info = dict()
        try:
            result = self.server.invoke_successfully(firmware_update_progress_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching firmware image upgrade progress details: %s'
                                      % (to_native(error)), exception=traceback.format_exc())
        # return firmware image update progress details
        if result.get_child_by_name('attributes').get_child_by_name('service-processor-image-update-progress-info'):
            update_progress_info = result.get_child_by_name('attributes').get_child_by_name('service-processor-image-update-progress-info')
            firmware_update_progress_info['is-in-progress'] = update_progress_info.get_child_content('is-in-progress')
            firmware_update_progress_info['node'] = update_progress_info.get_child_content('node')
        return firmware_update_progress_info

    def shelf_firmware_info_get(self):
        """
        Get the current firmware of shelf module
        :return:dict with module id and firmware info
        """
        shelf_id_fw_info = dict()
        shelf_firmware_info_get = netapp_utils.zapi.NaElement('storage-shelf-info-get-iter')
        desired_attributes = netapp_utils.zapi.NaElement('desired-attributes')
        storage_shelf_info = netapp_utils.zapi.NaElement('storage-shelf-info')
        shelf_module = netapp_utils.zapi.NaElement('shelf-modules')
        shelf_module_info = netapp_utils.zapi.NaElement('storage-shelf-module-info')
        shelf_module.add_child_elem(shelf_module_info)
        storage_shelf_info.add_child_elem(shelf_module)
        desired_attributes.add_child_elem(storage_shelf_info)
        shelf_firmware_info_get.add_child_elem(desired_attributes)

        try:
            result = self.server.invoke_successfully(shelf_firmware_info_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching shelf module firmware  details: %s'
                                      % (to_native(error)), exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            shelf_info = result.get_child_by_name('attributes-list').get_child_by_name('storage-shelf-info')
            if (shelf_info.get_child_by_name('shelf-modules') and
                    shelf_info.get_child_by_name('shelf-modules').get_child_by_name('storage-shelf-module-info')):
                shelves = shelf_info['shelf-modules'].get_children()
                for shelf in shelves:
                    shelf_id_fw_info[shelf.get_child_content('module-id')] = shelf.get_child_content('module-fw-revision')
        return shelf_id_fw_info

    def disk_firmware_info_get(self):
        """
        Get the current firmware of disks module
        :return:
        """
        disk_id_fw_info = dict()
        disk_firmware_info_get = netapp_utils.zapi.NaElement('storage-disk-get-iter')
        desired_attributes = netapp_utils.zapi.NaElement('desired-attributes')
        storage_disk_info = netapp_utils.zapi.NaElement('storage-disk-info')
        disk_inv = netapp_utils.zapi.NaElement('disk-inventory-info')
        storage_disk_info.add_child_elem(disk_inv)
        desired_attributes.add_child_elem(storage_disk_info)
        disk_firmware_info_get.add_child_elem(desired_attributes)
        try:
            result = self.server.invoke_successfully(disk_firmware_info_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching disk module firmware  details: %s'
                                      % (to_native(error)), exception=traceback.format_exc())
        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            disk_info = result.get_child_by_name('attributes-list')
            disks = disk_info.get_children()
            for disk in disks:
                disk_id_fw_info[disk.get_child_content('disk-uid')] = disk.get_child_by_name('disk-inventory-info').get_child_content('firmware-revision')
        return disk_id_fw_info

    def disk_firmware_required_get(self):
        """
        Check weather disk firmware upgrade is required or not
        :return: True if the firmware upgrade is required
        """
        disk_firmware_info = self.disk_firmware_info_get()
        for disk in disk_firmware_info:
            if (disk_firmware_info[disk]) != self.parameters['disk_fw']:
                return True
        return False

    def shelf_firmware_required_get(self):
        """
        Check weather shelf firmware upgrade is required or not
        :return: True if the firmware upgrade is required
        """
        shelf_firmware_info = self.shelf_firmware_info_get()
        for module in shelf_firmware_info:
            if (shelf_firmware_info[module]) != self.parameters['shelf_module_fw']:
                return True
        return False

    def sp_firmware_image_update(self):
        """
        Update current firmware image
        """
        firmware_update_info = netapp_utils.zapi.NaElement('service-processor-image-update')
        if self.parameters.get('package') is not None:
            firmware_update_info.add_new_child('package', self.parameters['package'])
        if self.parameters.get('clear_logs') is not None:
            firmware_update_info.add_new_child('clear-logs', str(self.parameters['clear_logs']))
        if self.parameters.get('install_baseline_image') is not None:
            firmware_update_info.add_new_child('install-baseline-image', str(self.parameters['install_baseline_image']))
        firmware_update_info.add_new_child('node', self.parameters['node'])
        firmware_update_info.add_new_child('update-type', self.parameters['update_type'])

        try:
            self.server.invoke_successfully(firmware_update_info, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            # Current firmware version matches the version to be installed
            if to_native(error.code) == '13001' and (error.message.startswith('Service Processor update skipped')):
                return False
            self.module.fail_json(msg='Error updating firmware image for %s: %s'
                                      % (self.parameters['node'], to_native(error)),
                                  exception=traceback.format_exc())
        return True

    def shelf_firmware_upgrade(self):
        """
        Upgrade shelf firmware image
        """
        shelf_firmware_update_info = netapp_utils.zapi.NaElement('storage-shelf-firmware-update')
        try:
            self.server.invoke_successfully(shelf_firmware_update_info, enable_tunneling=True)
            return True
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error updating shelf firmware image : %s'
                                      % (to_native(error)), exception=traceback.format_exc())

    def acp_firmware_upgrade(self):

        """
        Upgrade shelf firmware image
        """
        acp_firmware_update_info = netapp_utils.zapi.NaElement('storage-shelf-acp-firmware-update')
        acp_firmware_update_info.add_new_child('node-name', self.parameters['node'])
        try:
            self.server.invoke_successfully(acp_firmware_update_info, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error updating acp firmware image : %s'
                                  % (to_native(error)), exception=traceback.format_exc())

    def disk_firmware_upgrade(self):

        """
        Upgrade disk firmware
        """
        disk_firmware_update_info = netapp_utils.zapi.NaElement('disk-update-disk-fw')
        disk_firmware_update_info.add_new_child('node-name', self.parameters['node'])
        try:
            self.server.invoke_successfully(disk_firmware_update_info, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error updating disk firmware image : %s'
                                  % (to_native(error)), exception=traceback.format_exc())
        return True

    def autosupport_log(self):
        """
        Autosupport log for software_update
        :return:
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_firmware_upgrade", cserver)

    def apply(self):
        """
        Apply action to upgrade firmware
        """
        changed = False
        self.autosupport_log()
        firmware_update_progress = dict()
        if self.parameters.get('firmware_type') == 'service-processor':
            # service-processor firmware upgrade
            current = self.firmware_image_get(self.parameters['node'])

            if self.parameters.get('state') == 'present' and current:
                if not self.module.check_mode:
                    if self.sp_firmware_image_update():
                        changed = True
                    firmware_update_progress = self.sp_firmware_image_update_progress_get(self.parameters['node'])
                    while firmware_update_progress.get('is-in-progress') == 'true':
                        time.sleep(25)
                        firmware_update_progress = self.sp_firmware_image_update_progress_get(self.parameters['node'])
                else:
                    # we don't know until we try the upgrade
                    changed = True

        elif self.parameters.get('firmware_type') == 'shelf':
            # shelf firmware upgrade
            if self.parameters.get('shelf_module_fw'):
                if self.shelf_firmware_required_get():
                    if not self.module.check_mode:
                        changed = self.shelf_firmware_upgrade()
                    else:
                        changed = True
            else:
                if not self.module.check_mode:
                    changed = self.shelf_firmware_upgrade()
                else:
                    # we don't know until we try the upgrade -- assuming the worst
                    changed = True
        elif self.parameters.get('firmware_type') == 'acp':
            # acp firmware upgrade
            if self.acp_firmware_required_get():
                if not self.module.check_mode:
                    self.acp_firmware_upgrade()
                changed = True
        elif self.parameters.get('firmware_type') == 'disk':
            # Disk firmware upgrade
            if self.parameters.get('disk_fw'):
                if self.disk_firmware_required_get():
                    if not self.module.check_mode:
                        changed = self.disk_firmware_upgrade()
                    else:
                        changed = True
            else:
                if not self.module.check_mode:
                    changed = self.disk_firmware_upgrade()
                else:
                    # we don't know until we try the upgrade -- assuming the worst
                    changed = True

        self.module.exit_json(changed=changed)


def main():
    """Execute action"""
    community_obj = NetAppONTAPFirmwareUpgrade()
    community_obj.apply()


if __name__ == '__main__':
    main()
