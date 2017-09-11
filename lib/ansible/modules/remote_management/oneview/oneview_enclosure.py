#!/usr/bin/python
# Copyright (c) 2016-2017 Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: oneview_enclosure
short_description: Manage OneView Enclosure resources
description:
    - Provides an interface to manage Enclosure resources
version_added: "2.5"
requirements:
    - hpOneView >= 2.0.1
author:
    - Felipe Bulsoni (@fgbulsoni)
    - Thiago Miotto (@tmiotto)
    - Adriane Cardozo (@adriane-cardozo)
options:
    state:
      description:
        - Indicates the desired state for the Enclosure resource.
          C(present) will ensure data properties are compliant with OneView. You can rename the enclosure providing an
          attribute C(newName). You can also rename the rack providing an attribute C(rackName).
          C(absent) will remove the resource from OneView, if it exists.
          C(reconfigured) will reapply the appliance's configuration on the enclosure. This includes
          running the same configuration steps that were performed as part of the enclosure add.
          C(refreshed) will refresh the enclosure along with all of its components, including interconnects and
          servers. Any new hardware is added, and any hardware that is no longer present within the enclosure is
          removed.
          C(appliance_bays_powered_on) will set the appliance bay power state on.
          C(uid_on) will set the UID state on.
          C(uid_off) will set the UID state off.
          C(manager_bays_uid_on) will set the UID state on for the Synergy Frame Link Module.
          C(manager_bays_uid_off) will set the UID state off for the Synergy Frame Link Module.
          C(manager_bays_power_state_e_fuse) will E-Fuse the Synergy Frame Link Module bay in the path.
          C(manager_bays_power_state_reset) will Reset the Synergy Frame Link Module bay in the path.
          C(appliance_bays_power_state_e_fuse) will E-Fuse the appliance bay in the path.
          C(device_bays_power_state_e_fuse) will E-Fuse the device bay in the path.
          C(device_bays_power_state_reset) will Reset the device bay in the path.
          C(interconnect_bays_power_state_e_fuse) will E-Fuse the IC bay in the path.
          C(manager_bays_role_active) will set the active Synergy Frame Link Module.
          C(device_bays_ipv4_removed) will release the IPv4 address in the device bay.
          C(interconnect_bays_ipv4_removed) will release the IPv4 address in the interconnect bay.
          C(support_data_collection_set) will set the support data collection state for the enclosure. The supported
            values for this state are C(PendingCollection), C(Completed), C(Error) and C(NotSupported)
      default: present
      choices: [
        'present', 'absent', 'reconfigured', 'refreshed', 'appliance_bays_powered_on', 'uid_on', 'uid_off',
        'manager_bays_uid_on', 'manager_bays_uid_off', 'manager_bays_power_state_e_fuse',
        'manager_bays_power_state_reset', 'appliance_bays_power_state_e_fuse', 'device_bays_power_state_e_fuse',
        'device_bays_power_state_reset', 'interconnect_bays_power_state_e_fuse', 'manager_bays_role_active',
        'device_bays_ipv4_removed', 'interconnect_bays_ipv4_removed', 'support_data_collection_set'
        ]
    data:
      description:
        - List with the Enclosure properties.
      required: true
notes:
    - "These states are only available on HPE Synergy: C(appliance_bays_powered_on), C(uid_on), C(uid_off),
      C(manager_bays_uid_on), C(manager_bays_uid_off), C(manager_bays_power_state_e_fuse),
      C(manager_bays_power_state_reset), C(appliance_bays_power_state_e_fuse), C(device_bays_power_state_e_fuse),
      C(device_bays_power_state_reset), C(interconnect_bays_power_state_e_fuse), C(manager_bays_role_active),
      C(device_bays_ipv4_removed) and C(interconnect_bays_ipv4_removed)"

extends_documentation_fragment:
    - oneview
'''

EXAMPLES = '''
- name: Ensure that an Enclosure is present using the default configuration
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: present
    data:
      enclosureGroupUri : /rest/enclosure-groups/my-uri
      hostname : 172.18.1.13
      username : admin
      password : password
      name: Test-Enclosure
      licensingIntent : OneView

- name: Updates the enclosure to have a name of "Test-Enclosure-Renamed".
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: present
    data:
      name: Test-Enclosure
      newName : Test-Enclosure-Renamed

- name: Reconfigure the enclosure "Test-Enclosure"
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: reconfigured
    data:
      name: Test-Enclosure

- name: Ensure that enclosure is absent
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: absent
    data:
      name: Test-Enclosure

- name: Ensure that an enclosure is refreshed
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: refreshed
    data:
      name: Test-Enclosure
      refreshState: Refreshing

- name: Set the calibrated max power of an unmanaged or unsupported enclosure
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: present
    data:
      name: Test-Enclosure
      calibratedMaxPower: 1700

- name: Set the appliance bay power state on
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: appliance_bays_powered_on
    data:
      name: Test-Enclosure
      bayNumber: 1

- name: Set the appliance UID state on
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: uid_on
    data:
      name: Test-Enclosure

- name: Set the appliance UID state off
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: uid_off
    data:
      name: Test-Enclosure

- name: Set the UID for the Synergy Frame Link Module state on
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: manager_bays_uid_on
    data:
      name: Test-Enclosure
      bayNumber: 1

- name: Set the UID for the Synergy Frame Link Module state off
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: manager_bays_uid_off
    data:
      name: Test-Enclosure
      bayNumber: 1

- name: E-Fuse the Synergy Frame Link Module bay 1
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: manager_bays_power_state_e_fuse
    data:
      name: Test-Enclosure
      bayNumber: 1

- name: Reset the Synergy Frame Link Module bay 1
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: manager_bays_power_state_reset
    data:
      name: Test-Enclosure
      bayNumber: 1

- name: E-Fuse the appliance bay 1
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: appliance_bays_power_state_e_fuse
    data:
      name: Test-Enclosure
      bayNumber: 1

- name: E-Fuse the device bay 10
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: device_bays_power_state_e_fuse
    data:
      name: Test-Enclosure
      bayNumber: 10

- name: Reset the device bay 8
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: device_bays_power_state_reset
    data:
      name: Test-Enclosure
      bayNumber: 8

- name: E-Fuse the IC bay 3
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: interconnect_bays_power_state_e_fuse
    data:
      name: Test-Enclosure
      bayNumber: 3

- name: Set the active Synergy Frame Link Module on bay 2
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: manager_bays_role_active
    data:
      name: Test-Enclosure
      bayNumber: 2

- name: Release IPv4 address in the device bay 2
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: device_bays_ipv4_removed
    data:
      name: Test-Enclosure
      bayNumber: 2

- name: Release IPv4 address in the interconnect bay 2
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: interconnect_bays_ipv4_removed
    data:
      name: Test-Enclosure
      bayNumber: 2

- name: Set the supportDataCollectionState for the enclosure
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: support_data_collection_set
    data:
      name: Test-Enclosure
      supportDataCollectionState: PendingCollection

- name: Ensure that the Enclosure is present and is inserted in the desired scopes
  oneview_enclosure:
    config: /etc/oneview/oneview_config.json
    state: present
    data:
      name: Test-Enclosure
      scopeUris:
        - /rest/scopes/00SC123456
        - /rest/scopes/01SC123456
'''

RETURN = '''
enclosure:
    description: Has all the facts about the enclosure.
    returned: On states 'present', 'reconfigured', and 'refreshed'. Can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase, OneViewModuleResourceNotFound


class EnclosureModule(OneViewModuleBase):
    MSG_DELETED = 'Enclosure removed successfully.'
    MSG_ALREADY_ABSENT = 'Enclosure is already absent.'
    MSG_CREATED = 'Enclosure added successfully.'
    MSG_UPDATED = 'Enclosure updated successfully.'
    MSG_ALREADY_PRESENT = 'Enclosure is already present.'
    MSG_RECONFIGURED = 'Enclosure reconfigured successfully.'
    MSG_REFRESHED = 'Enclosure refreshed successfully.'
    MSG_ENCLOSURE_NOT_FOUND = 'Enclosure not found.'
    MSG_APPLIANCE_BAY_ALREADY_POWERED_ON = 'The device in specified bay is already powered on.'
    MSG_APPLIANCE_BAY_POWERED_ON = 'Appliance bay power state set to on successfully.'
    MSG_UID_ALREADY_POWERED_ON = 'UID state is already On.'
    MSG_UID_POWERED_ON = 'UID state set to On successfully.'
    MSG_UID_ALREADY_POWERED_OFF = 'UID state is already Off.'
    MSG_UID_POWERED_OFF = 'UID state set to Off successfully.'
    MSG_MANAGER_BAY_UID_ON = 'UID for the Synergy Frame Link Module set to On successfully.'
    MSG_MANAGER_BAY_UID_ALREADY_ON = 'The UID for the Synergy Frame Link Module is already On.'
    MSG_BAY_NOT_FOUND = 'Bay not found.'
    MSG_MANAGER_BAY_UID_ALREADY_OFF = 'The UID for the Synergy Frame Link Module is already Off.'
    MSG_MANAGER_BAY_UID_OFF = 'UID for the Synergy Frame Link Module set to Off successfully.'
    MSG_MANAGER_BAY_POWER_STATE_E_FUSED = 'E-Fuse the Synergy Frame Link Module bay in the path.'
    MSG_MANAGER_BAY_POWER_STATE_RESET = 'Reset the Synergy Frame Link Module bay in the path.'
    MSG_APPLIANCE_BAY_POWER_STATE_E_FUSED = 'E-Fuse the appliance bay in the path.'
    MSG_DEVICE_BAY_POWER_STATE_E_FUSED = 'E-Fuse the device bay in the path.'
    MSG_DEVICE_BAY_POWER_STATE_RESET = 'Reset the device bay in the path.'
    MSG_INTERCONNECT_BAY_POWER_STATE_E_FUSE = 'E-Fuse the IC bay in the path.'
    MSG_MANAGER_BAY_ROLE_ACTIVE = 'Set the active Synergy Frame Link Module.'
    MSG_DEVICE_BAY_IPV4_SETTING_REMOVED = 'Release IPv4 address in the device bay.'
    MSG_INTERCONNECT_BAY_IPV4_SETTING_REMOVED = 'Release IPv4 address in the interconnect bay'
    MSG_SUPPORT_DATA_COLLECTION_STATE_SET = 'Support data collection state set.'
    MSG_SUPPORT_DATA_COLLECTION_STATE_ALREADY_SET = \
        'The support data collection state is already set with the desired value.'
    argument_spec = dict(
        state=dict(
            type='str',
            default='present',
            choices=[
                'present',
                'absent',
                'reconfigured',
                'refreshed',
                'appliance_bays_powered_on',
                'uid_on',
                'uid_off',
                'manager_bays_uid_on',
                'manager_bays_uid_off',
                'manager_bays_power_state_e_fuse',
                'manager_bays_power_state_reset',
                'appliance_bays_power_state_e_fuse',
                'device_bays_power_state_e_fuse',
                'device_bays_power_state_reset',
                'interconnect_bays_power_state_e_fuse',
                'manager_bays_role_active',
                'device_bays_ipv4_removed',
                'interconnect_bays_ipv4_removed',
                'support_data_collection_set',
            ]
        ),
        data=dict(type='dict', required=True)
    )

    patch_params = dict(
        appliance_bays_powered_on=dict(operation='replace', path='/applianceBays/{bayNumber}/power', value='On'),
        uid_on=dict(operation='replace', path='/uidState', value='On'),
        uid_off=dict(operation='replace', path='/uidState', value='Off'),
        manager_bays_uid_on=dict(operation='replace', path='/managerBays/{bayNumber}/uidState', value='On'),
        manager_bays_uid_off=dict(operation='replace', path='/managerBays/{bayNumber}/uidState', value='Off'),
        manager_bays_power_state_e_fuse=dict(operation='replace', path='/managerBays/{bayNumber}/bayPowerState',
                                             value='E-Fuse'),
        manager_bays_power_state_reset=dict(operation='replace', path='/managerBays/{bayNumber}/bayPowerState',
                                            value='Reset'),
        appliance_bays_power_state_e_fuse=dict(operation='replace', path='/applianceBays/{bayNumber}/bayPowerState',
                                               value='E-Fuse'),
        device_bays_power_state_e_fuse=dict(operation='replace', path='/deviceBays/{bayNumber}/bayPowerState',
                                            value='E-Fuse'),
        device_bays_power_state_reset=dict(operation='replace', path='/deviceBays/{bayNumber}/bayPowerState',
                                           value='Reset'),
        interconnect_bays_power_state_e_fuse=dict(operation='replace',
                                                  path='/interconnectBays/{bayNumber}/bayPowerState', value='E-Fuse'),
        manager_bays_role_active=dict(operation='replace', path='/managerBays/{bayNumber}/role', value='active'),
        device_bays_ipv4_removed=dict(operation='remove', path='/deviceBays/{bayNumber}/ipv4Setting', value=''),
        interconnect_bays_ipv4_removed=dict(operation='remove', path='/interconnectBays/{bayNumber}/ipv4Setting',
                                            value=''),
    )

    patch_messages = dict(
        appliance_bays_powered_on=dict(changed=MSG_APPLIANCE_BAY_POWERED_ON,
                                       not_changed=MSG_APPLIANCE_BAY_ALREADY_POWERED_ON),
        uid_on=dict(changed=MSG_UID_POWERED_ON, not_changed=MSG_UID_ALREADY_POWERED_ON),
        uid_off=dict(changed=MSG_UID_POWERED_OFF, not_changed=MSG_UID_ALREADY_POWERED_OFF),
        manager_bays_uid_on=dict(changed=MSG_MANAGER_BAY_UID_ON, not_changed=MSG_MANAGER_BAY_UID_ALREADY_ON),
        manager_bays_uid_off=dict(changed=MSG_MANAGER_BAY_UID_OFF, not_changed=MSG_MANAGER_BAY_UID_ALREADY_OFF),
        manager_bays_power_state_e_fuse=dict(changed=MSG_MANAGER_BAY_POWER_STATE_E_FUSED),
        manager_bays_power_state_reset=dict(changed=MSG_MANAGER_BAY_POWER_STATE_RESET),
        appliance_bays_power_state_e_fuse=dict(changed=MSG_APPLIANCE_BAY_POWER_STATE_E_FUSED),
        device_bays_power_state_e_fuse=dict(changed=MSG_DEVICE_BAY_POWER_STATE_E_FUSED),
        device_bays_power_state_reset=dict(changed=MSG_DEVICE_BAY_POWER_STATE_RESET),
        interconnect_bays_power_state_e_fuse=dict(changed=MSG_INTERCONNECT_BAY_POWER_STATE_E_FUSE),
        manager_bays_role_active=dict(changed=MSG_MANAGER_BAY_ROLE_ACTIVE),
        device_bays_ipv4_removed=dict(changed=MSG_DEVICE_BAY_IPV4_SETTING_REMOVED),
        interconnect_bays_ipv4_removed=dict(changed=MSG_INTERCONNECT_BAY_IPV4_SETTING_REMOVED),
    )

    def __init__(self):
        super(EnclosureModule, self).__init__(additional_arg_spec=self.argument_spec)
        self.resource_client = self.oneview_client.enclosures

    def execute_module(self):

        resource = self._get_by_name(self.data)

        if self.state == 'present':
            changed, msg, resource = self._present(resource, self.data)
        elif self.state == 'absent':
            return self.resource_absent(resource, 'remove')
        else:

            if not resource:
                raise OneViewModuleResourceNotFound(self.MSG_ENCLOSURE_NOT_FOUND)

            if self.state == 'reconfigured':
                changed, msg, resource = self._reconfigure(resource)
            elif self.state == 'refreshed':
                changed, msg, resource = self._refresh(resource, self.data)
            elif self.state == 'support_data_collection_set':
                changed, msg, resource = self._support_data_collection_set(resource, self.data)
            else:
                changed, msg, resource = self._patch(resource, self.data)

        return dict(changed=changed,
                    msg=msg,
                    ansible_facts=dict(enclosure=resource))

    def _present(self, resource_by_name, data):
        changed = False
        message = self.MSG_ALREADY_PRESENT

        configuration_data = data.copy()

        name = configuration_data.pop('newName', configuration_data.pop('name', None))
        rack_name = configuration_data.pop('rackName', None)
        calibrated_max_power = configuration_data.pop('calibratedMaxPower', None)
        scope_uris = configuration_data.pop('scopeUris', None)

        if 'hostname' in data:
            resource = self._get_by_hostname(data['hostname'])
            if not resource:
                resource = self.oneview_client.enclosures.add(configuration_data)
                message = self.MSG_CREATED
                changed = True
        else:
            resource = resource_by_name

        if self._name_has_changes(resource, name):
            resource = self._replace_enclosure_name(resource, name)
            changed = True
            message = self.MSG_UPDATED

        if self._rack_name_has_changes(resource, rack_name):
            resource = self._replace_enclosure_rack_name(resource, rack_name)
            changed = True
            message = self.MSG_UPDATED

        if calibrated_max_power:
            self._set_calibrated_max_power(resource, calibrated_max_power)
            changed = True
            message = self.MSG_UPDATED

        if scope_uris is not None:
            state = {'ansible_facts': {'enclosure': resource}, 'changed': changed, 'msg': message}
            result = self.resource_scopes_set(state, 'enclosure', scope_uris)
            resource = result['ansible_facts']['enclosure']
            changed = result['changed']
            message = result['msg']

        return changed, message, resource

    def _reconfigure(self, resource):
        reconfigured_enclosure = self.oneview_client.enclosures.update_configuration(resource['uri'])
        return True, self.MSG_RECONFIGURED, reconfigured_enclosure

    def _refresh(self, resource, data):
        refresh_config = data.copy()
        refresh_config.pop('name', None)

        self.oneview_client.enclosures.refresh_state(resource['uri'], refresh_config)
        enclosure = self.oneview_client.enclosures.get(resource['uri'])

        return True, self.MSG_REFRESHED, enclosure

    def _support_data_collection_set(self, resource, data):
        current_value = resource.get('supportDataCollectionState')
        desired_value = data.get('supportDataCollectionState')

        if current_value != desired_value:
            updated_resource = self.oneview_client.enclosures.patch(resource['uri'], operation='replace',
                                                                    path='/supportDataCollectionState',
                                                                    value=desired_value)
            return True, self.MSG_SUPPORT_DATA_COLLECTION_STATE_SET, updated_resource

        return False, self.MSG_SUPPORT_DATA_COLLECTION_STATE_ALREADY_SET, resource

    def _patch(self, resource, data):
        changed = False
        state_name = self.module.params['state']
        state = self.patch_params[state_name].copy()

        property_current_value = self._get_current_property_value(state_name, state, resource, data)

        if self._is_update_needed(state_name, state, property_current_value):
            resource = self.oneview_client.enclosures.patch(resource['uri'], **state)
            changed = True

        msg = self.patch_messages[state_name]['changed'] if changed else self.patch_messages[state_name]['not_changed']

        return changed, msg, resource

    def _is_update_needed(self, state_name, state, property_current_value):
        need_request_update = False
        if state['value'] in ['E-Fuse', 'Reset', 'active']:
            need_request_update = True
        elif state['operation'] == 'remove':
            need_request_update = True
        elif state_name == 'appliance_bays_powered_on':
            if not property_current_value:
                need_request_update = True
        elif property_current_value != state['value']:
            need_request_update = True

        return need_request_update

    def _get_current_property_value(self, state_name, state, resource, data):
        property_name = state['path'].split('/')[1]
        sub_property_name = state['path'].split('/')[-1]

        if sub_property_name == property_name:
            sub_property_name = None

        if state_name == 'appliance_bays_powered_on':
            sub_property_name = 'poweredOn'

        filter_ = set(data.keys()) - set(["name"])
        if filter_:
            filter_ = filter_.pop()

        property_current_value = None

        if filter_:
            sub_resource = None
            if resource.get(property_name):
                sub_resource = next(
                    (item for item in resource[property_name] if str(item[filter_]) == str(data[filter_])), None)

            if not sub_resource:
                # Resource doesn't have that property or subproperty
                raise OneViewModuleResourceNotFound(self.MSG_BAY_NOT_FOUND)

            property_current_value = sub_resource.get(sub_property_name)
            state['path'] = state['path'].format(**data)

        else:
            property_current_value = resource[property_name]

        return property_current_value

    def _name_has_changes(self, resource, name):
        return name and resource['name'] != name

    def _rack_name_has_changes(self, resource, rack_name):
        return rack_name and resource.get('rackName', None) != rack_name

    def _replace_enclosure_name(self, resource, name):
        updated_resource = self.oneview_client.enclosures.patch(resource['uri'], 'replace', '/name', name)
        return updated_resource

    def _replace_enclosure_rack_name(self, resource, rack_name):
        updated_resource = self.oneview_client.enclosures.patch(resource['uri'], 'replace', '/rackName', rack_name)
        return updated_resource

    def _set_calibrated_max_power(self, resource, calibrated_max_power):
        body = {"calibratedMaxPower": calibrated_max_power}
        self.oneview_client.enclosures.update_environmental_configuration(resource['uri'], body)

    def _get_by_name(self, data):
        if 'name' not in data:
            return None
        result = self.oneview_client.enclosures.get_by('name', data['name'])
        return result[0] if result else None

    def _get_by_hostname(self, hostname):
        def filter_by_hostname(hostname, enclosure):
            is_primary_ip = ('activeOaPreferredIP' in enclosure and enclosure['activeOaPreferredIP'] == hostname)
            is_standby_ip = ('standbyOaPreferredIP' in enclosure and enclosure['standbyOaPreferredIP'] == hostname)
            return is_primary_ip or is_standby_ip

        enclosures = self.oneview_client.enclosures.get_all()
        result = [x for x in enclosures if filter_by_hostname(hostname, x)]
        return result[0] if result else None


def main():
    EnclosureModule().run()


if __name__ == '__main__':
    main()
