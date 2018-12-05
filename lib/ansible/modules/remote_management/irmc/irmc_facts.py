#!/usr/bin/python

# FUJITSU LIMITED
# Copyright 2018 FUJITSU LIMITED
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: irmc_facts

short_description: get or set PRIMERGY server and iRMC facts

description:
    - Ansible module to get or set basic iRMC and PRIMERGY server data via iRMC RedFish interface.
    - For more iRMC modules see U(https://github.com/FujitsuPrimergy/fujitsu-ansible-irmc-integration).

requirements:
    - The module needs to run locally.
    - iRMC S4 needs FW >= 9.04, iRMC S5 needs FW >= 1.25.

version_added: "2.8"

author:
    - Fujitsu Server PRIMERGY (@FujitsuPrimergy)

options:
    irmc_url:
        description: IP address of the iRMC to be requested for data.
        required:    true
    irmc_username:
        description: iRMC user for basic authentication.
        required:    true
    irmc_password:
        description: Password for iRMC user for basic authentication.
        required:    true
    validate_certs:
        description: If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
        type:        bool
        required:    false
        default:     true
    command:
        description: How to access server facts.
        required:    false
        default:     get
        choices:     ['get', 'set']
    asset_tag:
        description: Server asset tag.
        required:    false
    location:
        description: Server location.
        required:    false
    description:
        description: Server description.
        required:    false
    contact:
        description: System contact.
        required:    false
    helpdesk_message:
        description: Help desk message.
        required:    false

notes:
    - See http://manuals.ts.fujitsu.com/file/13371/irmc-restful-spec-en.pdf
    - See http://manuals.ts.fujitsu.com/file/13372/irmc-redfish-wp-en.pdf
'''

EXAMPLES = '''
# Get basic server and iRMC facts
- name: Get basic server and iRMC facts
  irmc_facts:
    irmc_url: "{{ inventory_hostname }}"
    irmc_username: "{{ irmc_user }}"
    irmc_password: "{{ irmc_password }}"
    validate_certs: "{{ validate_certificate }}"
    command: "get"
  register: facts
  delegate_to: localhost
- name: Show server and iRMC facts
  debug:
    msg: "{{ facts.facts }}"

# Set server asset tag
- name: Set server asset tag
  irmc_facts:
    irmc_url: "{{ inventory_hostname }}"
    irmc_username: "{{ irmc_user }}"
    irmc_password: "{{ irmc_password }}"
    validate_certs: "{{ validate_certificate }}"
    command: "set"
    asset_tag: "Ansible test server"
  delegate_to: localhost
'''

RETURN = '''
# facts returned by "get":
    hardware.ethernetinterfaces:
        description:
             dict with total number (count)
             and list of ethernet interfaces (devices)
             with relevant data (id, macaddress, name)
        returned: always
        type: dict
        sample:
            {
                "count": 2,
                "devices": [
                    { "id": "0", "macaddress": "01:02:03:04:05:06", "name": "eth0" },
                    { "id": "1", "macaddress": "01:02:03:04:05:06", "name": "eth1" }
                ]
            }
    hardware.fans:
        description:
             dict with available fan slots (sockets)
             and total number (count)
             and list of existing fans (devices)
             with relevant data (id, manufacturer, name, size)<br/>
             <i>note that fan devices are only returned if server is 'On'</i>
        returned: always
        type: dict
        sample:
            {
                "count": 2,
                "devices": [
                    { "id": "0", "manufacturer": "Micron Technology", "name": "DIMM-1A", "size": 8192 },
                    { "id": "12", "manufacturer": "SK Hynix", "name": "DIMM-1E", "size": 16384 }
                ],
                "sockets": 24
            }
    hardware.memory:
        description:
             dict with available memory slots (sockets)
             and total number (count)
             and list of existing memories (devices)
             with relevant data (id, manufacturer, name, size)
        returned: always
        type: dict
        sample:
            {
                "count": 6,
                "devices": [
                    { "id": "0", "location": "SystemBoard", "name": "FAN1 SYS" },
                    { "id": "1", "location": "SystemBoard", "name": "FAN2 SYS" },
                    { "id": "2", "location": "SystemBoard", "name": "FAN3 SYS" },
                    { "id": "3", "location": "SystemBoard", "name": "FAN4 SYS" },
                    { "id": "4", "location": "SystemBoard", "name": "FAN5 SYS" },
                    { "id": "5", "location": "PowerSupply", "name": "FAN PSU1" }
                ],
                "sockets": 7
            }
    hardware.powersupplies:
        description:
             dict with available power supply slots (sockets)
             and total number (count)
             and list of existing power supplies (devices)
             with relevant data (id, manufacturer, model, name)
        returned: always
        type: dict
        sample:
            {
                "count": 1,
                "devices": [
                    { "id": "0", "manufacturer": "CHICONY", "model": "S13-450P1A", "name": "PSU1" }
                ],
                "sockets": 2
            }
    hardware.processors:
        description:
             dict with available processor slots (sockets)
             and total number (count)
             and list of existing processors (devices)
             with relevant data (cores, id, name, threads)
        returned: always
        type: dict
        sample:
            {
                "count": 2,
                "devices": [
                    { "cores": 6, "id": "0", "name": "Genuine Intel(R) CPU @ 2.00GHz", "threads": 6 },
                    { "cores": 6, "id": "1", "name": "Genuine Intel(R) CPU @ 2.00GHz", "threads": 6 }
                ],
                "sockets": 2
            }
    hardware.storagecontrollers:
        description:
             dict with total number (count)
             and list of storage controllers (devices)
             with relevant data (drives, firmware, id, name, volume)<br/>
             <i>note that storage controllers are only returned if server is 'On'</i>
        returned: always
        type: dict
        sample:
            {
                "count": 1,
                "devices": [
                    { "drives": 4, "firmware": "4.270.00-4869", "id": "1000", "name": "PRAID EP400i", "volumes": 1 }
                ]
            }
    irmc:
        description:
             dict with relevant iRMC data
             (fw_builddate, fw_running, fw_version, hostname, macaddress, sdrr_version)
        returned: always
        type: dict
        sample:
            {
                "fw_builddate": "2018-03-05T14:02:44",
                "fw_running": "LowFWImage",
                "fw_version": "9.08F",
                "hostname": "iRMC01CA5C-iRMC",
                "macaddress": "90:1B:0E:01:CA:5C",
                "sdrr_version": "3.73"
            }
    mainboard:
        description:
             dict with relevant mainboard data
             (dnumber, manufacturer, part_number, serial_number, version)
        returned: always
        type: dict
        sample:
            {
                "dnumber": "D3289",
                "manufacturer": "FUJITSU",
                "part_number": "S26361-D3289-D13",
                "serial_number": "44617895",
                "version": "WGS04 GS50"
            }
    system:
        description:
             dict with relevant system data
             (asset_tag, bios_version, description, health, helpdesk_message, host_name,
             idled_state, ip, location, manufacturer, memory_size, model, part_number,
             power_state, serial_number, uuid)
        returned: always
        type: dict
        sample:
            {
                "asset_tag": "New AssetTag",
                "bios_version": "V5.0.0.9 R1.36.0 for D3289-A1x",
                "contact": "Admin (admin@server.room)",
                "description": "server description",
                "health": "OK",
                "helpdesk_message": "New helpdesk message",
                "host_name": "STK-SLES11SP4x64",
                "idled_state": "Off",
                "ip": 101.102.103.104,
                "location": "Server Room",
                "manufacturer": "FUJITSU",
                "memory_size": "24 GB",
                "model": "PRIMERGY RX2540 M1",
                "part_number": "ABN:K1495-VXXX-XX",
                "power_state": "On",
                "serial_number": "YLVT000098",
                "uuid": "11223344-5566-cafe-babe-deadbeef1234"
            }
'''


import json
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.irmc import irmc_redfish_get, irmc_redfish_patch, get_irmc_json


def irmc_facts(module):
    result = dict(
        changed=False,
        status=0
    )

    if module.check_mode:
        result['msg'] = "module was not run"
        module.exit_json(**result)

    # parameter check
    if module.params['command'] == "set" and \
       module.params['asset_tag'] is None and module.params['description'] is None and \
       module.params['helpdesk_message'] is None and module.params['location'] is None and \
       module.params['contact'] is None:
        result['msg'] = "Command 'set' requires at least one parameter to be set!"
        result['status'] = 10
        module.fail_json(**result)

    # Get iRMC OEM system data
    status, oemdata, msg = irmc_redfish_get(module, "redfish/v1/Systems/0/Oem/ts_fujitsu/System")
    if status < 100:
        module.fail_json(msg=msg, status=status, exception=oemdata)
    elif status != 200:
        module.fail_json(msg=msg, status=status)

    if module.params['command'] == "get":
        # Get iRMC system data
        status, sysdata, msg = irmc_redfish_get(module, "redfish/v1/Systems/0/")
        if status < 100:
            module.fail_json(msg=msg, status=status, exception=sysdata)
        elif status != 200:
            module.fail_json(msg=msg, status=status)
        power_state = get_irmc_json(sysdata, "PowerState")

        # Get iRMC FW data
        status, fwdata, msg = irmc_redfish_get(module, "redfish/v1/Systems/0/Oem/ts_fujitsu/FirmwareInventory")
        if status < 100:
            module.fail_json(msg=msg, status=status, exception=fwdata)
        elif status != 200:
            module.fail_json(msg=msg, status=status)

        result['facts'] = setup_resultdata(sysdata, oemdata, fwdata)
        result = add_system_hw_info(power_state, module, result)
        result = add_chassis_hw_info(module, result)
        result = add_irmc_hw_info(module, result)
        module.exit_json(**result)

    # Set iRMC OEM system data
    body = setup_oem_data(module.params)
    etag = get_irmc_json(oemdata, "@odata.etag")
    status, patch, msg = irmc_redfish_patch(module, "redfish/v1/Systems/0/Oem/ts_fujitsu/System/",
                                            json.dumps(body), etag)
    if status < 100:
        module.fail_json(msg=msg, status=status, exception=patch)
    elif status != 200:
        module.fail_json(msg=msg, status=status)

    result['changed'] = True
    module.exit_json(**result)


def add_system_hw_info(power_state, module, result):
    # get system hardware
    for hw in ("Memory", "Processors", "EthernetInterfaces", "Storage"):
        status, hwdata, msg = irmc_redfish_get(module, "redfish/v1/Systems/0/{0}?$expand=Members".format(hw))
        if status < 100:
            module.fail_json(msg=msg, status=status, exception=hwdata)
        elif status != 200:
            module.fail_json(msg=msg, status=status)
        items = 0
        hw_dict = {}
        hw_dict['devices'] = []
        for member in get_irmc_json(hwdata, "Members"):
            hw_list = {}
            if get_irmc_json(member, ["Status", "State"]) == "Enabled":
                if hw == "Memory":
                    hw_list['id'] = get_irmc_json(member, ["Id"])
                    hw_list['name'] = get_irmc_json(member, ["DeviceLocator"])
                    hw_list['manufacturer'] = get_irmc_json(member, ["Manufacturer"])
                    hw_list['size'] = get_irmc_json(member, ["CapacityMiB"])
                if hw == "Processors":
                    hw_list['id'] = get_irmc_json(member, ["Id"])
                    hw_list['name'] = get_irmc_json(member, ["Model"])
                    hw_list['cores'] = get_irmc_json(member, ["TotalCores"])
                    hw_list['threads'] = get_irmc_json(member, ["TotalThreads"])
                if hw == "EthernetInterfaces":
                    hw_list['id'] = get_irmc_json(member, ["Id"])
                    hw_list['name'] = get_irmc_json(member, ["Description"])
                    if "does not exist" in hw_list['name']:
                        hw_list['name'] = "{0} {1}".format(get_irmc_json(member, ["Name"]), hw_list['id'])
                    hw_list['macaddress'] = get_irmc_json(member, ["MACAddress"])
                if hw == "Storage" and power_state == "On":
                    # iRMC has each StroageController with its own Storage
                    for ctrl in get_irmc_json(member, "StorageControllers"):
                        hw_list['id'] = get_irmc_json(member, ["Id"])
                        hw_list['name'] = get_irmc_json(ctrl, ["Model"])
                        hw_list['firmware'] = get_irmc_json(ctrl, ["FirmwareVersion"])
                        hw_list['drives'] = get_irmc_json(ctrl, ["Oem", "ts_fujitsu", "DriveCount"])
                        hw_list['volumes'] = get_irmc_json(ctrl, ["Oem", "ts_fujitsu", "VolumeCount"])
                items += 1
                if hw_list:
                    hw_dict['devices'].append(hw_list)
        hw_dict['count'] = items
        if hw == "Storage":
            hw = "StorageControllers"
        if hw in ("Memory", "Processors"):
            hw_dict['sockets'] = get_irmc_json(hwdata, "Members@odata.count")
        result['facts']['hardware'][hw.lower()] = hw_dict
    return result


def add_chassis_hw_info(module, result):
    # get chassis hardware
    hw_source = {
        "redfish/v1/Chassis/0/Thermal#/Fans": ["Fans"],
        "redfish/v1/Chassis/0/Power#/PowerSupplies": ["PowerSupplies"],
    }
    for hw_link, hw_list in hw_source.items():
        status, hwdata, msg = irmc_redfish_get(module, hw_link)
        if status < 100:
            module.fail_json(msg=msg, status=status, exception=hwdata)
        elif status != 200:
            module.fail_json(msg=msg, status=status)
        for hw in hw_list:
            items = 0
            hw_dict = {}
            hw_dict['devices'] = []
            for member in get_irmc_json(hwdata, hw):
                hw_list = {}
                if get_irmc_json(member, ["Status", "State"]) == "Enabled":
                    if hw == "PowerSupplies":
                        hw_list['id'] = get_irmc_json(member, ["MemberId"])
                        hw_list['name'] = get_irmc_json(member, ["Name"])
                        hw_list['manufacturer'] = get_irmc_json(member, ["Manufacturer"])
                        hw_list['model'] = get_irmc_json(member, ["Model"])
                    elif hw == "Voltages":
                        hw_list['id'] = get_irmc_json(member, ["MemberId"])
                        hw_list['name'] = get_irmc_json(member, ["Name"])
                    else:
                        hw_list['id'] = get_irmc_json(member, ["MemberId"])
                        hw_list['name'] = get_irmc_json(member, ["Name"])
                        hw_list['location'] = get_irmc_json(member, ["PhysicalContext"])
                    items += 1
                    if hw_list:
                        hw_dict['devices'].append(hw_list)
            hw_dict['count'] = items
            hw_dict['sockets'] = get_irmc_json(hwdata, "{0}@odata.count".format(hw))
            result['facts']['hardware'][hw.lower()] = hw_dict
    return result


def add_irmc_hw_info(module, result):
    # get iRMC info
    status, hwdata, msg = irmc_redfish_get(module, "redfish/v1/Managers/iRMC/EthernetInterfaces?$expand=Members")
    if status < 100:
        module.fail_json(msg=msg, status=status, exception=hwdata)
    elif status != 200:
        module.fail_json(msg=msg, status=status)
    for member in get_irmc_json(hwdata, "Members"):
        result['facts']['irmc']['macaddress'] = "{0}".format(get_irmc_json(member, ["MACAddress"]))
        result['facts']['irmc']['hostname'] = "{0}".format(get_irmc_json(member, ["HostName"]))
    return result


def setup_oem_data(data):
    body = dict()
    if data['asset_tag'] is not None:
        body['AssetTag'] = data['asset_tag']
    if data['location'] is not None:
        body['Location'] = data['location']
    if data['description'] is not None:
        body['Description'] = data['description']
    if data['contact'] is not None:
        body['Contact'] = data['contact']
    if data['helpdesk_message'] is not None:
        body['HelpdeskMessage'] = data['helpdesk_message']
    return body


def setup_resultdata(data, data2, data3):
    data = {
        'system': {
            'bios_version': get_irmc_json(data, "BiosVersion"),
            'idled_state': get_irmc_json(data, "IndicatorLED"),
            'asset_tag': get_irmc_json(data2, "AssetTag"),
            'host_name': get_irmc_json(data, "HostName"),
            'manufacturer': get_irmc_json(data, "Manufacturer"),
            'model': get_irmc_json(data, "Model"),
            # 'name': get_irmc_json(data, "Name"),
            'part_number': get_irmc_json(data, "PartNumber"),
            'serial_number': get_irmc_json(data, "SerialNumber"),
            'uuid': get_irmc_json(data, "UUID"),
            'ip': get_irmc_json(data2, "SystemIP"),
            'location': get_irmc_json(data2, "Location"),
            'description': get_irmc_json(data2, "Description"),
            'contact': get_irmc_json(data2, "Contact"),
            'helpdesk_message': get_irmc_json(data2, "HelpdeskMessage"),
            'power_state': get_irmc_json(data, "PowerState"),
            'memory_size': "{0} GB".format(get_irmc_json(data, ["MemorySummary", "TotalSystemMemoryGiB"])),
            'health': get_irmc_json(data, ["Status", "HealthRollup"]),
        },
        'mainboard': {
            'manufacturer': get_irmc_json(data, ["Oem", "ts_fujitsu", "MainBoard", "Manufacturer"]),
            'dnumber': get_irmc_json(data, ["Oem", "ts_fujitsu", "MainBoard", "Model"]),
            'part_number': get_irmc_json(data, ["Oem", "ts_fujitsu", "MainBoard", "PartNumber"]),
            'serial_number': get_irmc_json(data, ["Oem", "ts_fujitsu", "MainBoard", "SerialNumber"]),
            'version': get_irmc_json(data, ["Oem", "ts_fujitsu", "MainBoard", "Version"]),
        },
        'irmc': {
            'fw_version': get_irmc_json(data3, "BMCFirmware"),
            'fw_builddate': get_irmc_json(data3, "BMCFirmwareBuildDate"),
            'fw_running': get_irmc_json(data3, "BMCFirmwareRunning"),
            'sdrr_version': get_irmc_json(data3, "SDRRVersion"),
        },
        'hardware': {
        },
    }
    return data


def main():
    # import pdb; pdb.set_trace()
    module_args = dict(
        irmc_url=dict(required=True, type="str"),
        irmc_username=dict(required=True, type="str"),
        irmc_password=dict(required=True, type="str", no_log=True),
        validate_certs=dict(required=False, type="bool", default=True),
        command=dict(required=False, type="str", default="get", choices=["get", "set"]),
        asset_tag=dict(required=False, type="str"),
        location=dict(required=False, type="str"),
        description=dict(required=False, type="str"),
        contact=dict(required=False, type="str"),
        helpdesk_message=dict(required=False, type="str"),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    irmc_facts(module)


if __name__ == '__main__':
    main()
