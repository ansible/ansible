#!/usr/bin/python

# (c) 2017, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: na_cdot_lun

short_description: Manage  NetApp cDOT luns
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create, destroy, resize luns on NetApp cDOT.

options:

  state:
    description:
    - Whether the specified lun should exist or not.
    required: true
    choices: ['present', 'absent']

  name:
    description:
    - The name of the lun to manage.
    required: true

  flexvol_name:
    description:
    - The name of the FlexVol the lun should exist on.
    - Required when C(state=present).

  size:
    description:
    - The size of the lun in C(size_unit).
    - Required when C(state=present).

  size_unit:
    description:
    - The unit used to interpret the size parameter.
    choices: ['bytes', 'b', 'kb', 'mb', 'gb', 'tb', 'pb', 'eb', 'zb', 'yb']
    default: 'gb'

  force_resize:
    description:
    - Forcibly reduce the size. This is required for reducing the size of the LUN to avoid accidentally reducing the LUN size.
    default: false

  force_remove:
    description:
    - If "true", override checks that prevent a LUN from being destroyed if it is online and mapped.
    - If "false", destroying an online and mapped LUN will fail.
    default: false

  force_remove_fenced:
    description:
    - If "true", override checks that prevent a LUN from being destroyed while it is fenced.
    - If "false", attempting to destroy a fenced LUN will fail.
    - The default if not specified is "false". This field is available in Data ONTAP 8.2 and later.
    default: false

  vserver:
    required: true
    description:
    - The name of the vserver to use.

'''

EXAMPLES = """
- name: Create LUN
  na_cdot_lun:
    state: present
    name: ansibleLUN
    flexvol_name: ansibleVolume
    vserver: ansibleVServer
    size: 5
    size_unit: mb
    hostname: "{{ netapp_hostname }}"
    username: "{{ netapp_username }}"
    password: "{{ netapp_password }}"

- name: Resize Lun
  na_cdot_lun:
    state: present
    name: ansibleLUN
    force_resize: True
    flexvol_name: ansibleVolume
    vserver: ansibleVServer
    size: 5
    size_unit: gb
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

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppCDOTLUN(object):

    def __init__(self):

        self._size_unit_map = dict(
            bytes=1,
            b=1,
            kb=1024,
            mb=1024 ** 2,
            gb=1024 ** 3,
            tb=1024 ** 4,
            pb=1024 ** 5,
            eb=1024 ** 6,
            zb=1024 ** 7,
            yb=1024 ** 8
        )

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True, type='str'),
            size=dict(type='int'),
            size_unit=dict(default='gb',
                           choices=['bytes', 'b', 'kb', 'mb', 'gb', 'tb',
                                    'pb', 'eb', 'zb', 'yb'], type='str'),
            force_resize=dict(default=False, type='bool'),
            force_remove=dict(default=False, type='bool'),
            force_remove_fenced=dict(default=False, type='bool'),
            flexvol_name=dict(type='str'),
            vserver=dict(required=True, type='str'),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['flexvol_name', 'size'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.size_unit = p['size_unit']
        if p['size'] is not None:
            self.size = p['size'] * self._size_unit_map[self.size_unit]
        else:
            self.size = None
        self.force_resize = p['force_resize']
        self.force_remove = p['force_remove']
        self.force_remove_fenced = p['force_remove_fenced']
        self.flexvol_name = p['flexvol_name']
        self.vserver = p['vserver']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_lun(self):
        """
        Return details about the LUN

        :return: Details about the lun
        :rtype: dict
        """

        luns = []
        tag = None
        while True:
            lun_info = netapp_utils.zapi.NaElement('lun-get-iter')
            if tag:
                lun_info.add_new_child('tag', tag, True)

            query_details = netapp_utils.zapi.NaElement('lun-info')
            query_details.add_new_child('vserver', self.vserver)
            query_details.add_new_child('volume', self.flexvol_name)

            query = netapp_utils.zapi.NaElement('query')
            query.add_child_elem(query_details)

            lun_info.add_child_elem(query)

            result = self.server.invoke_successfully(lun_info, True)
            if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) >= 1:
                attr_list = result.get_child_by_name('attributes-list')
                luns.extend(attr_list.get_children())

            tag = result.get_child_content('next-tag')

            if tag is None:
                break

        # The LUNs have been extracted.
        # Find the specified lun and extract details.
        return_value = None
        for lun in luns:
            path = lun.get_child_content('path')
            _rest, _splitter, found_name = path.rpartition('/')

            if found_name == self.name:
                size = lun.get_child_content('size')

                # Find out if the lun is attached
                attached_to = None
                lun_id = None
                if lun.get_child_content('mapped') == 'true':
                    lun_map_list = netapp_utils.zapi.NaElement.create_node_with_children(
                        'lun-map-list-info', **{'path': path})

                    result = self.server.invoke_successfully(
                        lun_map_list, enable_tunneling=True)

                    igroups = result.get_child_by_name('initiator-groups')
                    if igroups:
                        for igroup_info in igroups.get_children():
                            igroup = igroup_info.get_child_content(
                                'initiator-group-name')
                            attached_to = igroup
                            lun_id = igroup_info.get_child_content('lun-id')

                return_value = {
                    'name': found_name,
                    'size': size,
                    'attached_to': attached_to,
                    'lun_id': lun_id
                }
            else:
                continue

        return return_value

    def create_lun(self):
        """
        Create LUN with requested name and size
        """
        path = '/vol/%s/%s' % (self.flexvol_name, self.name)
        lun_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-create-by-size', **{'path': path,
                                     'size': str(self.size),
                                     'ostype': 'linux'})

        try:
            self.server.invoke_successfully(lun_create, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error provisioning lun %s of size %s: %s" % (self.name, self.size, to_native(e)),
                                  exception=traceback.format_exc())

    def delete_lun(self):
        """
        Delete requested LUN
        """
        path = '/vol/%s/%s' % (self.flexvol_name, self.name)

        lun_delete = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-destroy', **{'path': path,
                              'force': str(self.force_remove),
                              'destroy-fenced-lun':
                                  str(self.force_remove_fenced)})

        try:
            self.server.invoke_successfully(lun_delete, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg="Error deleting lun %s: %s" % (path, to_native(e)),
                                  exception=traceback.format_exc())

    def resize_lun(self):
        """
        Resize requested LUN.

        :return: True if LUN was actually re-sized, false otherwise.
        :rtype: bool
        """
        path = '/vol/%s/%s' % (self.flexvol_name, self.name)

        lun_resize = netapp_utils.zapi.NaElement.create_node_with_children(
            'lun-resize', **{'path': path,
                             'size': str(self.size),
                             'force': str(self.force_resize)})
        try:
            self.server.invoke_successfully(lun_resize, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            if to_native(e.code) == "9042":
                # Error 9042 denotes the new LUN size being the same as the
                # old LUN size. This happens when there's barely any difference
                # in the two sizes. For example, from 8388608 bytes to
                # 8194304 bytes. This should go away if/when the default size
                # requested/reported to/from the controller is changed to a
                # larger unit (MB/GB/TB).
                return False
            else:
                self.module.fail_json(msg="Error resizing lun %s: %s" % (path, to_native(e)),
                                      exception=traceback.format_exc())

        return True

    def apply(self):
        property_changed = False
        multiple_properties_changed = False
        size_changed = False
        lun_exists = False
        lun_detail = self.get_lun()

        if lun_detail:
            lun_exists = True
            current_size = lun_detail['size']

            if self.state == 'absent':
                property_changed = True

            elif self.state == 'present':
                if not int(current_size) == self.size:
                    size_changed = True
                    property_changed = True

        else:
            if self.state == 'present':
                property_changed = True

        if property_changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not lun_exists:
                        self.create_lun()

                    else:
                        if size_changed:
                            # Ensure that size was actually changed. Please
                            # read notes in 'resize_lun' function for details.
                            size_changed = self.resize_lun()
                            if not size_changed and not \
                                    multiple_properties_changed:
                                property_changed = False

                elif self.state == 'absent':
                    self.delete_lun()

        changed = property_changed or size_changed
        # TODO: include other details about the lun (size, etc.)
        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTLUN()
    v.apply()


if __name__ == '__main__':
    main()
