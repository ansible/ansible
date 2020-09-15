#!/usr/bin/python

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_object_store
short_description: NetApp ONTAP manage object store config.
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create or delete object store config on ONTAP.

options:

  state:
    description:
    - Whether the specified object store config should exist or not.
    choices: ['present', 'absent']
    default: 'present'
    type: str

  name:
    required: true
    description:
    - The name of the object store config to manage.
    type: str

  provider_type:
    required: false
    description:
    - The name of the object store config provider.
    type: str

  server:
    required: false
    description:
    - Fully qualified domain name of the object store config.
    type: str

  container:
    required: false
    description:
    - Data bucket/container name used in S3 requests.
    type: str

  access_key:
    required: false
    description:
    - Access key ID for AWS_S3 and SGWS provider types.
    type: str

  secret_password:
    required: false
    description:
    - Secret access key for AWS_S3 and SGWS provider types.
    type: str
'''

EXAMPLES = """
- name: object store Create
  na_ontap_object_store:
    state: present
    name: ansible
    provider_type: SGWS
    server: abc
    container: abc
    access_key: s3.amazonaws.com
    secret_password: abc
    hostname: "{{ hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"

- name: object store Create
  na_ontap_object_store:
    state: absent
    name: ansible
    hostname: "{{ hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
"""

RETURN = """

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapObjectStoreConfig(object):
    ''' object initialize and class methods '''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            name=dict(required=True, type='str'),
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            provider_type=dict(required=False, type='str'),
            server=dict(required=False, type='str'),
            container=dict(required=False, type='str'),
            access_key=dict(required=False, type='str'),
            secret_password=dict(required=False, type='str', no_log=True)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def get_aggr_object_store(self):
        """
        Fetch details if object store config exists.
        :return:
            Dictionary of current details if object store config found
            None if object store config is not found
        """
        aggr_object_store_get_iter = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-object-store-config-get', **{'object-store-name': self.parameters['name']})
        result = None
        try:
            result = self.server.invoke_successfully(aggr_object_store_get_iter, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            # Error 15661 denotes an object store not being found.
            if to_native(error.code) == "15661":
                pass
            else:
                self.module.fail_json(msg=to_native(error), exception=traceback.format_exc())
        return result

    def create_aggr_object_store(self):
        """
        Create aggregate object store config
        :return: None
        """
        required_keys = set(['provider_type', 'server', 'container', 'access_key'])
        if not required_keys.issubset(set(self.parameters.keys())):
            self.module.fail_json(msg='Error provisioning object store %s: one of the following parameters are missing '
                                      '%s' % (self.parameters['name'], ', '.join(required_keys)))
        options = {'object-store-name': self.parameters['name'],
                   'provider-type': self.parameters['provider_type'],
                   'server': self.parameters['server'],
                   's3-name': self.parameters['container'],
                   'access-key': self.parameters['access_key']}
        if self.parameters.get('secret_password'):
            options['secret-password'] = self.parameters['secret_password']
        object_store_create = netapp_utils.zapi.NaElement.create_node_with_children('aggr-object-store-config-create', **options)

        try:
            self.server.invoke_successfully(object_store_create, enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error provisioning object store config %s: %s"
                                      % (self.parameters['name'], to_native(error)),
                                  exception=traceback.format_exc())

    def delete_aggr_object_store(self):
        """
        Delete aggregate object store config
        :return: None
        """
        object_store_destroy = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-object-store-config-delete', **{'object-store-name': self.parameters['name']})

        try:
            self.server.invoke_successfully(object_store_destroy,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg="Error removing object store config %s: %s" %
                                      (self.parameters['name'], to_native(error)), exception=traceback.format_exc())

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)

    def apply(self):
        """
        Apply action to the object store config
        :return: None
        """
        self.asup_log_for_cserver("na_ontap_object_store_config")
        current = self.get_aggr_object_store()
        cd_action = self.na_helper.get_cd_action(current, self.parameters)

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'create':
                    self.create_aggr_object_store()
                elif cd_action == 'delete':
                    self.delete_aggr_object_store()
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Create Object Store Config class instance and invoke apply
    :return: None
    """
    obj_store = NetAppOntapObjectStoreConfig()
    obj_store.apply()


if __name__ == '__main__':
    main()
