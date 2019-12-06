#!/usr/bin/python

# (c) 2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_volume_autosize
short_description: NetApp ONTAP manage volume autosize
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Modify Volume AutoSize
options:
  volume:
    description:
    - The name of the flexible volume for which we want to set autosize.
    type: str
    required: true

  mode:
    description:
    - Specify the flexible volume's autosize mode of operation.
    type: str
    choices: ['grow', 'grow_shrink', 'off']

  vserver:
    description:
    - Name of the vserver to use.
    required: true
    type: str

  grow_threshold_percent:
    description:
    - Specifies the percentage of the flexible volume's capacity at which autogrow is initiated.
    - The default grow threshold varies from 85% to 98%, depending on the volume size.
    - It is an error for the grow threshold to be less than or equal to the shrink threshold.
    - Range between 0 and 100
    type: int

  increment_size:
    description:
    - Specify the flexible volume's increment size using the following format < number > [k|m|g|t]
    - The amount is the absolute size to set.
    - The trailing 'k', 'm', 'g', and 't' indicates the desired units, namely 'kilobytes', 'megabytes', 'gigabytes', and 'terabytes' (respectively).
    type: str

  maximum_size:
    description:
    - Specify the flexible volume's maximum allowed size using the following format < number > [k|m|g|t]
    - The amount is the absolute size to set.
    - The trailing 'k', 'm', 'g', and 't' indicates the desired units, namely 'kilobytes', 'megabytes', 'gigabytes', and 'terabytes' (respectively).
    - The default value is 20% greater than the volume size at the time autosize was enabled.
    - It is an error for the maximum volume size to be less than the current volume size.
    - It is also an error for the maximum size to be less than or equal to the minimum size.
    type: str

  minimum_size:
    description:
    - Specify the flexible volume's minimum allowed size using the following format < number > [k|m|g|t] The amount is the absolute size to set.
    - The trailing 'k', 'm', 'g', and 't' indicates the desired units, namely 'kilobytes', 'megabytes', 'gigabytes', and 'terabytes' (respectively).
    - The default value is the size of the volume at the time the 'grow_shrink' mode was enabled.
    - It is an error for the minimum size to be greater than or equal to the maximum size.
    type: str

  reset:
    description:
    - "Sets the values of maximum_size, increment_size, minimum_size, grow_threshold_percent, shrink_threshold_percent and mode to their defaults"
    type: bool

  shrink_threshold_percent:
    description:
    - Specifies the percentage of the flexible volume's capacity at which autoshrink is initiated.
    - The default shrink threshold is 50%. It is an error for the shrink threshold to be greater than or equal to the grow threshold.
    - Range between 0 and 100
    type: int
'''

EXAMPLES = """
    - name: Modify volume autosize
      na_ontap_volume_autosize:
        hostname: 10.193.79.189
        username: admin
        password: netapp1!
        volume: ansibleVolumesize12
        mode: grow
        grow_threshold_percent: 99
        increment_size: 50m
        maximum_size: 10g
        minimum_size: 21m
        shrink_threshold_percent: 40
        vserver: ansible_vserver

    - name: Reset volume autosize
      na_ontap_volume_autosize:
        hostname: 10.193.79.189
        username: admin
        password: netapp1!
        volume: ansibleVolumesize12
        reset: true
        vserver: ansible_vserver
"""

RETURN = """
"""
import sys
import copy
import traceback
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import OntapRestAPI
from ansible.module_utils._text import to_native

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapVolumeAutosize(object):
    def __init__(self):
        self.use_rest = False
        # Volume_autosize returns KB and not B like Volume so values are shifted down 1
        self._size_unit_map = dict(
            k=1,
            m=1024,
            g=1024 ** 2,
            t=1024 ** 3,
        )
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            volume=dict(required=True, type="str"),
            mode=dict(required=False, choices=['grow', 'grow_shrink', 'off']),
            vserver=dict(required=True, type='str'),
            grow_threshold_percent=dict(required=False, type='int'),
            increment_size=dict(required=False, type='str'),
            maximum_size=dict(required=False, type='str'),
            minimum_size=dict(required=False, type='str'),
            reset=dict(required=False, type='bool'),
            shrink_threshold_percent=dict(required=False, type='int')
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
            mutually_exclusive=[
                ['reset', 'maximum_size'],
                ['reset', 'increment_size'],
                ['reset', 'minimum_size'],
                ['reset', 'grow_threshold_percent'],
                ['reset', 'shrink_threshold_percent'],
                ['reset', 'mode']
            ]
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        # API should be used for ONTAP 9.6 or higher, ZAPI for lower version
        self.restApi = OntapRestAPI(self.module)
        if self.restApi.is_rest():
            self.use_rest = True
            # increment size and reset are not supported with rest api
            if self.parameters.get('increment_size'):
                self.module.fail_json(msg="Rest API does not support increment size, please switch to ZAPI")
            if self.parameters.get('reset'):
                self.module.fail_json(msg="Rest API does not support reset, please switch to ZAPI")
        else:
            if HAS_NETAPP_LIB is False:
                self.module.fail_json(msg="the python NetApp-Lib module is required")
            else:
                self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def get_volume_autosize(self, uuid=None):
        """
        Get volume_autosize information from the ONTAP system
        :return:
        """
        if self.use_rest:
            params = {'fields': 'autosize'}
            api = 'storage/volumes/' + uuid
            message, error = self.restApi.get(api, params)
            if error is not None:
                self.module.fail_json(msg="%s" % error)
            return self._create_get_volume_return(message['autosize'])
        else:
            volume_autosize_info = netapp_utils.zapi.NaElement('volume-autosize-get')
            volume_autosize_info.add_new_child('volume', self.parameters['volume'])
            try:
                result = self.server.invoke_successfully(volume_autosize_info, True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error fetching volume autosize infor for %s : %s' % (self.parameters['volume'],
                                                                                                to_native(error)),
                                      exception=traceback.format_exc())
            return self._create_get_volume_return(result)

    def _create_get_volume_return(self, results):
        """
        Create a return value from volume-autosize-get info file
        :param results:
        :return:
        """
        return_value = {}
        if self.use_rest:
            if 'mode' in results:
                return_value['mode'] = results['mode']
            if 'grow_threshold' in results:
                return_value['grow_threshold_percent'] = results['grow_threshold']
            if 'maximum' in results:
                return_value['maximum_size'] = results['maximum']
            if 'minimum' in results:
                return_value['minimum_size'] = results['minimum']
            if 'shrink_threshold' in results:
                return_value['shrink_threshold_percent'] = results['shrink_threshold']
        else:
            if results.get_child_by_name('mode'):
                return_value['mode'] = results.get_child_content('mode')
            if results.get_child_by_name('grow-threshold-percent'):
                return_value['grow_threshold_percent'] = int(results.get_child_content('grow-threshold-percent'))
            if results.get_child_by_name('increment-size'):
                return_value['increment_size'] = results.get_child_content('increment-size')
            if results.get_child_by_name('maximum-size'):
                return_value['maximum_size'] = results.get_child_content('maximum-size')
            if results.get_child_by_name('minimum-size'):
                return_value['minimum_size'] = results.get_child_content('minimum-size')
            if results.get_child_by_name('shrink-threshold-percent'):
                return_value['shrink_threshold_percent'] = int(results.get_child_content('shrink-threshold-percent'))
        if return_value == {}:
            return_value = None
        return return_value

    def modify_volume_autosize(self, uuid=None):
        """
        Modify a Volumes autosize
        :return:
        """
        if self.use_rest:
            params = {}
            data = {}
            autosize = {}
            if self.parameters.get('mode'):
                autosize['mode'] = self.parameters['mode']
            if self.parameters.get('grow_threshold_percent'):
                autosize['grow_threshold'] = self.parameters['grow_threshold_percent']
            if self.parameters.get('maximum_size'):
                autosize['maximum'] = self.parameters['maximum_size']
            if self.parameters.get('minimum_size'):
                autosize['minimum'] = self.parameters['minimum_size']
            if self.parameters.get('shrink_threshold_percent'):
                autosize['shrink_threshold'] = self.parameters['shrink_threshold_percent']
            data['autosize'] = autosize
            api = "storage/volumes/" + uuid
            message, error = self.restApi.patch(api, data, params)
            if error is not None:
                self.module.fail_json(msg="%s" % error)

        else:
            volume_autosize_info = netapp_utils.zapi.NaElement('volume-autosize-set')
            volume_autosize_info.add_new_child('volume', self.parameters['volume'])
            if self.parameters.get('mode'):
                volume_autosize_info.add_new_child('mode', self.parameters['mode'])
            if self.parameters.get('grow_threshold_percent'):
                volume_autosize_info.add_new_child('grow-threshold-percent', str(self.parameters['grow_threshold_percent']))
            if self.parameters.get('increment_size'):
                volume_autosize_info.add_new_child('increment-size', self.parameters['increment_size'])
            if self.parameters.get('reset') is not None:
                volume_autosize_info.add_new_child('reset', str(self.parameters['reset']))
            if self.parameters.get('maximum_size'):
                volume_autosize_info.add_new_child('maximum-size', self.parameters['maximum_size'])
            if self.parameters.get('minimum_size'):
                volume_autosize_info.add_new_child('minimum-size', self.parameters['minimum_size'])
            if self.parameters.get('shrink_threshold_percent'):
                volume_autosize_info.add_new_child('shrink-threshold-percent', str(self.parameters['shrink_threshold_percent']))
            try:
                self.server.invoke_successfully(volume_autosize_info, True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg="Error modify volume autosize for %s: %s" % (self.parameters["volume"], to_native(error)),
                                      exception=traceback.format_exc())

    def modify_to_kb(self, converted_parameters):
        """
        Save a converted parameter
        :param converted_parameters: Dic of all parameters
        :return:
        """
        for attr in ['maximum_size', 'minimum_size', 'increment_size']:
            if converted_parameters.get(attr):
                if self.use_rest:
                    converted_parameters[attr] = self.convert_to_byte(attr, converted_parameters)
                else:
                    converted_parameters[attr] = str(self.convert_to_kb(attr, converted_parameters))
        return converted_parameters

    def convert_to_kb(self, variable, converted_parameters):
        """
        Convert a number 10m in to its correct KB size
        :param variable: the Parameter we are going to covert
        :param converted_parameters: Dic of all parameters
        :return:
        """
        if converted_parameters.get(variable)[-1] not in ['k', 'm', 'g', 't']:
            self.module.fail_json(msg="%s must end with a k, m, g or t" % variable)
        return self._size_unit_map[converted_parameters.get(variable)[-1]] * int(converted_parameters.get(variable)[:-1])

    def convert_to_byte(self, variable, converted_parameters):
        if converted_parameters.get(variable)[-1] not in ['k', 'm', 'g', 't']:
            self.module.fail_json(msg="%s must end with a k, m, g or t" % variable)
        return (self._size_unit_map[converted_parameters.get(variable)[-1]] * int(converted_parameters.get(variable)[:-1])) * 1024

    def get_volume_uuid(self):
        """
        Get a volume's UUID
        :return: uuid of the volume
        """
        params = {'fields': '*',
                  'name': self.parameters['volume'],
                  'svm.name': self.parameters['vserver']}
        api = "storage/volumes"
        message, error = self.restApi.get(api, params)
        if error is not None:
            self.module.fail_json(msg="%s" % error)
        return message['records'][0]['uuid']

    def apply(self):
        # TODO Logging for rest
        uuid = None
        if not self.use_rest:
            netapp_utils.ems_log_event("na_ontap_volume_autosize", self.server)
        if self.use_rest:
            # we only have the volume name, we need to the the uuid for the volume
            uuid = self.get_volume_uuid()
        current = self.get_volume_autosize(uuid=uuid)
        converted_parameters = copy.deepcopy(self.parameters)
        converted_parameters = self.modify_to_kb(converted_parameters)
        self.na_helper.get_modified_attributes(current, converted_parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                self.modify_volume_autosize(uuid=uuid)
        if self.parameters.get('reset') is True:
            self.modify_volume_autosize(uuid=uuid)
            self.na_helper.changed = True
        self.module.exit_json(changed=self.na_helper.changed)


def main():
    """
    Apply volume autosize operations from playbook
    :return:
    """
    obj = NetAppOntapVolumeAutosize()
    obj.apply()


if __name__ == '__main__':
    main()
