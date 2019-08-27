#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: netapp_e_facts
short_description: NetApp E-Series retrieve facts about NetApp E-Series storage arrays
description:
    - The netapp_e_facts module returns a collection of facts regarding NetApp E-Series storage arrays.
    - When contacting a storage array directly the collection includes details about the array, controllers, management
      interfaces, hostside interfaces, driveside interfaces, disks, storage pools, volumes, snapshots, and features.
    - When contacting a web services proxy the collection will include basic information regarding the storage systems
      that are under its management.
version_added: '2.2'
author:
    - Kevin Hulquest (@hulquest)
    - Nathan Swartz (@ndswartz)
extends_documentation_fragment:
    - netapp.eseries
'''

EXAMPLES = """
---
- name: Get array facts
  netapp_e_facts:
      ssid: "{{ netapp_array_id }}"
      api_url: "https://{{ netapp_e_api_host }}:8443/devmgr/v2"
      api_username: "{{ netapp_api_username }}"
      api_password: "{{ netapp_api_password }}"
      validate_certs: "{{ netapp_api_validate_certs }}"
- name: Get array facts
  netapp_e_facts:
      ssid: 1
      api_url: https://192.168.1.100:8443/devmgr/v2
      api_username: myApiUser
      api_password: myApiPass
      validate_certs: true
"""

RETURN = """
    msg:
        description: Success message
        returned: on success
        type: str
        sample:
            - Gathered facts for storage array. Array ID [1].
            - Gathered facts for web services proxy.
    storage_array_facts:
        description: provides details about the array, controllers, management interfaces, hostside interfaces,
                     driveside interfaces, disks, storage pools, volumes, snapshots, and features.
        returned: on successful inquiry from from embedded web services rest api
        type: complex
        contains:
            netapp_controllers:
                description: storage array controller list that contains basic controller identification and status
                type: complex
                sample:
                    - [{"name": "A", "serial": "021632007299", "status": "optimal"},
                       {"name": "B", "serial": "021632007300", "status": "failed"}]
            netapp_disks:
                description: drive list that contains identification, type, and status information for each drive
                type: complex
                sample:
                    - [{"available": false,
                        "firmware_version": "MS02",
                        "id": "01000000500003960C8B67880000000000000000",
                        "media_type": "ssd",
                        "product_id": "PX02SMU080      ",
                        "serial_number": "15R0A08LT2BA",
                        "status": "optimal",
                        "tray_ref": "0E00000000000000000000000000000000000000",
                        "usable_bytes": "799629205504" }]
            netapp_driveside_interfaces:
                description: drive side interface list that contains identification, type, and speed for each interface
                type: complex
                sample:
                    - [{ "controller": "A", "interface_speed": "12g", "interface_type": "sas" }]
                    - [{ "controller": "B", "interface_speed": "10g", "interface_type": "iscsi" }]
            netapp_enabled_features:
                description: specifies the enabled features on the storage array.
                returned: on success
                type: complex
                sample:
                    - [ "flashReadCache", "performanceTier", "protectionInformation", "secureVolume" ]
            netapp_host_groups:
                description: specifies the host groups on the storage arrays.
                returned: on success
                type: complex
                sample:
                    - [{ "id": "85000000600A098000A4B28D003610705C40B964", "name": "group1" }]
            netapp_hosts:
                description: specifies the hosts on the storage arrays.
                returned: on success
                type: complex
                sample:
                    - [{ "id": "8203800000000000000000000000000000000000",
                         "name": "host1",
                         "group_id": "85000000600A098000A4B28D003610705C40B964",
                         "host_type_index": 28,
                         "ports": [{ "type": "fc", "address": "1000FF7CFFFFFF01", "label": "FC_1" },
                                   { "type": "fc", "address": "1000FF7CFFFFFF00", "label": "FC_2" }]}]
            netapp_host_types:
                description: lists the available host types on the storage array.
                returned: on success
                type: complex
                sample:
                    - [{ "index": 0, "type": "FactoryDefault" },
                       { "index": 1, "type": "W2KNETNCL"},
                       { "index": 2, "type": "SOL" },
                       { "index": 5, "type": "AVT_4M" },
                       { "index": 6, "type": "LNX" },
                       { "index": 7, "type": "LnxALUA" },
                       { "index": 8, "type": "W2KNETCL" },
                       { "index": 9, "type": "AIX MPIO" },
                       { "index": 10, "type": "VmwTPGSALUA" },
                       { "index": 15, "type": "HPXTPGS" },
                       { "index": 17, "type": "SolTPGSALUA" },
                       { "index": 18, "type": "SVC" },
                       { "index": 22, "type": "MacTPGSALUA" },
                       { "index": 23, "type": "WinTPGSALUA" },
                       { "index": 24, "type": "LnxTPGSALUA" },
                       { "index": 25, "type": "LnxTPGSALUA_PM" },
                       { "index": 26, "type": "ONTAP_ALUA" },
                       { "index": 27, "type": "LnxTPGSALUA_SF" },
                       { "index": 28, "type": "LnxDHALUA" },
                       { "index": 29, "type": "ATTOClusterAllOS" }]
            netapp_hostside_interfaces:
                description: host side interface list that contains identification, configuration, type, speed, and
                             status information for each interface
                type: complex
                sample:
                    - [{"iscsi":
                        [{ "controller": "A",
                            "current_interface_speed": "10g",
                            "ipv4_address": "10.10.10.1",
                            "ipv4_enabled": true,
                            "ipv4_gateway": "10.10.10.1",
                            "ipv4_subnet_mask": "255.255.255.0",
                            "ipv6_enabled": false,
                            "iqn": "iqn.1996-03.com.netapp:2806.600a098000a81b6d0000000059d60c76",
                            "link_status": "up",
                            "mtu": 9000,
                            "supported_interface_speeds": [ "10g" ] }]}]
            netapp_management_interfaces:
                description: management interface list that contains identification, configuration, and status for
                             each interface
                type: complex
                sample:
                    - [{"alias": "ict-2800-A",
                        "channel": 1,
                        "controller": "A",
                        "dns_config_method": "dhcp",
                        "dns_servers": [],
                        "ipv4_address": "10.1.1.1",
                        "ipv4_address_config_method": "static",
                        "ipv4_enabled": true,
                        "ipv4_gateway": "10.113.1.1",
                        "ipv4_subnet_mask": "255.255.255.0",
                        "ipv6_enabled": false,
                        "link_status": "up",
                        "mac_address": "00A098A81B5D",
                        "name": "wan0",
                        "ntp_config_method": "disabled",
                        "ntp_servers": [],
                        "remote_ssh_access": false }]
            netapp_storage_array:
                description: provides storage array identification, firmware version, and available capabilities
                type: dict
                sample:
                    - {"chassis_serial": "021540006043",
                       "firmware": "08.40.00.01",
                       "name": "ict-2800-11_40",
                       "wwn": "600A098000A81B5D0000000059D60C76",
                       "cacheBlockSizes": [4096,
                                           8192,
                                           16384,
                                           32768],
                       "supportedSegSizes": [8192,
                                             16384,
                                             32768,
                                             65536,
                                             131072,
                                             262144,
                                             524288]}
            netapp_storage_pools:
                description: storage pool list that contains identification and capacity information for each pool
                type: complex
                sample:
                    - [{"available_capacity": "3490353782784",
                        "id": "04000000600A098000A81B5D000002B45A953A61",
                        "name": "Raid6",
                        "total_capacity": "5399466745856",
                        "used_capacity": "1909112963072" }]
            netapp_volumes:
                description: storage volume list that contains identification and capacity information for each volume
                type: complex
                sample:
                    - [{"capacity": "5368709120",
                        "id": "02000000600A098000AAC0C3000002C45A952BAA",
                        "is_thin_provisioned": false,
                        "name": "5G",
                        "parent_storage_pool_id": "04000000600A098000A81B5D000002B45A953A61" }]
            netapp_workload_tags:
                description: workload tag list
                type: complex
                sample:
                    - [{"id": "87e19568-43fb-4d8d-99ea-2811daaa2b38",
                        "name": "ftp_server",
                        "workloadAttributes": [{"key": "use",
                                                "value": "general"}]}]
            netapp_volumes_by_initiators:
                description: list of available volumes keyed by the mapped initiators.
                type: complex
                sample:
                   - {"192_168_1_1": [{"id": "02000000600A098000A4B9D1000015FD5C8F7F9E",
                                       "meta_data": {"filetype": "xfs", "public": true},
                                       "name": "some_volume",
                                       "workload_name": "test2_volumes",
                                       "wwn": "600A098000A4B9D1000015FD5C8F7F9E"}]}
            snapshot_images:
                description: snapshot image list that contains identification, capacity, and status information for each
                             snapshot image
                type: complex
                sample:
                    - [{"active_cow": true,
                        "creation_method": "user",
                        "id": "34000000600A098000A81B5D00630A965B0535AC",
                        "pit_capacity": "5368709120",
                        "reposity_cap_utilization": "0",
                        "rollback_source": false,
                        "status": "optimal" }]
"""

from re import match
from pprint import pformat
from ansible.module_utils.netapp import NetAppESeriesModule


class Facts(NetAppESeriesModule):
    def __init__(self):
        web_services_version = "02.00.0000.0000"
        super(Facts, self).__init__(ansible_options={},
                                    web_services_version=web_services_version,
                                    supports_check_mode=True)

    def get_controllers(self):
        """Retrieve a mapping of controller references to their labels."""
        controllers = list()
        try:
            rc, controllers = self.request('storage-systems/%s/graph/xpath-filter?query=/controller/id' % self.ssid)
        except Exception as err:
            self.module.fail_json(
                msg="Failed to retrieve controller list! Array Id [%s]. Error [%s]."
                    % (self.ssid, str(err)))

        controllers.sort()

        controllers_dict = {}
        i = ord('A')
        for controller in controllers:
            label = chr(i)
            controllers_dict[controller] = label
            i += 1

        return controllers_dict

    def get_array_facts(self):
        """Extract particular facts from the storage array graph"""
        facts = dict(facts_from_proxy=False, ssid=self.ssid)
        controller_reference_label = self.get_controllers()
        array_facts = None

        # Get the storage array graph
        try:
            rc, array_facts = self.request("storage-systems/%s/graph" % self.ssid)
        except Exception as error:
            self.module.fail_json(msg="Failed to obtain facts from storage array with id [%s]. Error [%s]"
                                      % (self.ssid, str(error)))

        facts['netapp_storage_array'] = dict(
            name=array_facts['sa']['saData']['storageArrayLabel'],
            chassis_serial=array_facts['sa']['saData']['chassisSerialNumber'],
            firmware=array_facts['sa']['saData']['fwVersion'],
            wwn=array_facts['sa']['saData']['saId']['worldWideName'],
            segment_sizes=array_facts['sa']['featureParameters']['supportedSegSizes'],
            cache_block_sizes=array_facts['sa']['featureParameters']['cacheBlockSizes'])

        facts['netapp_controllers'] = [
            dict(
                name=controller_reference_label[controller['controllerRef']],
                serial=controller['serialNumber'].strip(),
                status=controller['status'],
            ) for controller in array_facts['controller']]

        facts['netapp_host_groups'] = [
            dict(
                id=group['id'],
                name=group['name']
            ) for group in array_facts['storagePoolBundle']['cluster']]

        facts['netapp_hosts'] = [
            dict(
                group_id=host['clusterRef'],
                hosts_reference=host['hostRef'],
                id=host['id'],
                name=host['name'],
                host_type_index=host['hostTypeIndex'],
                posts=host['hostSidePorts']
            ) for host in array_facts['storagePoolBundle']['host']]

        facts['netapp_host_types'] = [
            dict(
                type=host_type['hostType'],
                index=host_type['index']
            ) for host_type in array_facts['sa']['hostSpecificVals']
            if 'hostType' in host_type.keys() and host_type['hostType']
            # This conditional ignores zero-length strings which indicates that the associated host-specific NVSRAM region has been cleared.
        ]
        facts['snapshot_images'] = [
            dict(
                id=snapshot['id'],
                status=snapshot['status'],
                pit_capacity=snapshot['pitCapacity'],
                creation_method=snapshot['creationMethod'],
                reposity_cap_utilization=snapshot['repositoryCapacityUtilization'],
                active_cow=snapshot['activeCOW'],
                rollback_source=snapshot['isRollbackSource']
            ) for snapshot in array_facts['highLevelVolBundle']['pit']]

        facts['netapp_disks'] = [
            dict(
                id=disk['id'],
                available=disk['available'],
                media_type=disk['driveMediaType'],
                status=disk['status'],
                usable_bytes=disk['usableCapacity'],
                tray_ref=disk['physicalLocation']['trayRef'],
                product_id=disk['productID'],
                firmware_version=disk['firmwareVersion'],
                serial_number=disk['serialNumber'].lstrip()
            ) for disk in array_facts['drive']]

        facts['netapp_management_interfaces'] = [
            dict(controller=controller_reference_label[controller['controllerRef']],
                 name=iface['ethernet']['interfaceName'],
                 alias=iface['ethernet']['alias'],
                 channel=iface['ethernet']['channel'],
                 mac_address=iface['ethernet']['macAddr'],
                 remote_ssh_access=iface['ethernet']['rloginEnabled'],
                 link_status=iface['ethernet']['linkStatus'],
                 ipv4_enabled=iface['ethernet']['ipv4Enabled'],
                 ipv4_address_config_method=iface['ethernet']['ipv4AddressConfigMethod'].lower().replace("config", ""),
                 ipv4_address=iface['ethernet']['ipv4Address'],
                 ipv4_subnet_mask=iface['ethernet']['ipv4SubnetMask'],
                 ipv4_gateway=iface['ethernet']['ipv4GatewayAddress'],
                 ipv6_enabled=iface['ethernet']['ipv6Enabled'],
                 dns_config_method=iface['ethernet']['dnsProperties']['acquisitionProperties']['dnsAcquisitionType'],
                 dns_servers=(iface['ethernet']['dnsProperties']['acquisitionProperties']['dnsServers']
                              if iface['ethernet']['dnsProperties']['acquisitionProperties']['dnsServers'] else []),
                 ntp_config_method=iface['ethernet']['ntpProperties']['acquisitionProperties']['ntpAcquisitionType'],
                 ntp_servers=(iface['ethernet']['ntpProperties']['acquisitionProperties']['ntpServers']
                              if iface['ethernet']['ntpProperties']['acquisitionProperties']['ntpServers'] else [])
                 ) for controller in array_facts['controller'] for iface in controller['netInterfaces']]

        facts['netapp_hostside_interfaces'] = [
            dict(
                fc=[dict(controller=controller_reference_label[controller['controllerRef']],
                         channel=iface['fibre']['channel'],
                         link_status=iface['fibre']['linkStatus'],
                         current_interface_speed=strip_interface_speed(iface['fibre']['currentInterfaceSpeed']),
                         maximum_interface_speed=strip_interface_speed(iface['fibre']['maximumInterfaceSpeed']))
                    for controller in array_facts['controller']
                    for iface in controller['hostInterfaces']
                    if iface['interfaceType'] == 'fc'],
                ib=[dict(controller=controller_reference_label[controller['controllerRef']],
                         channel=iface['ib']['channel'],
                         link_status=iface['ib']['linkState'],
                         mtu=iface['ib']['maximumTransmissionUnit'],
                         current_interface_speed=strip_interface_speed(iface['ib']['currentSpeed']),
                         maximum_interface_speed=strip_interface_speed(iface['ib']['supportedSpeed']))
                    for controller in array_facts['controller']
                    for iface in controller['hostInterfaces']
                    if iface['interfaceType'] == 'ib'],
                iscsi=[dict(controller=controller_reference_label[controller['controllerRef']],
                            iqn=iface['iscsi']['iqn'],
                            link_status=iface['iscsi']['interfaceData']['ethernetData']['linkStatus'],
                            ipv4_enabled=iface['iscsi']['ipv4Enabled'],
                            ipv4_address=iface['iscsi']['ipv4Data']['ipv4AddressData']['ipv4Address'],
                            ipv4_subnet_mask=iface['iscsi']['ipv4Data']['ipv4AddressData']['ipv4SubnetMask'],
                            ipv4_gateway=iface['iscsi']['ipv4Data']['ipv4AddressData']['ipv4GatewayAddress'],
                            ipv6_enabled=iface['iscsi']['ipv6Enabled'],
                            mtu=iface['iscsi']['interfaceData']['ethernetData']['maximumFramePayloadSize'],
                            current_interface_speed=strip_interface_speed(iface['iscsi']['interfaceData']
                                                                          ['ethernetData']['currentInterfaceSpeed']),
                            supported_interface_speeds=strip_interface_speed(iface['iscsi']['interfaceData']
                                                                             ['ethernetData']
                                                                             ['supportedInterfaceSpeeds']))
                       for controller in array_facts['controller']
                       for iface in controller['hostInterfaces']
                       if iface['interfaceType'] == 'iscsi'],
                sas=[dict(controller=controller_reference_label[controller['controllerRef']],
                          channel=iface['sas']['channel'],
                          current_interface_speed=strip_interface_speed(iface['sas']['currentInterfaceSpeed']),
                          maximum_interface_speed=strip_interface_speed(iface['sas']['maximumInterfaceSpeed']),
                          link_status=iface['sas']['iocPort']['state'])
                     for controller in array_facts['controller']
                     for iface in controller['hostInterfaces']
                     if iface['interfaceType'] == 'sas'])]

        facts['netapp_driveside_interfaces'] = [
            dict(
                controller=controller_reference_label[controller['controllerRef']],
                interface_type=interface['interfaceType'],
                interface_speed=strip_interface_speed(
                    interface[interface['interfaceType']]['maximumInterfaceSpeed']
                    if (interface['interfaceType'] == 'sata' or
                        interface['interfaceType'] == 'sas' or
                        interface['interfaceType'] == 'fibre')
                    else (
                        interface[interface['interfaceType']]['currentSpeed']
                        if interface['interfaceType'] == 'ib'
                        else (
                            interface[interface['interfaceType']]['interfaceData']['maximumInterfaceSpeed']
                            if interface['interfaceType'] == 'iscsi' else 'unknown'
                        ))),
            )
            for controller in array_facts['controller']
            for interface in controller['driveInterfaces']]

        facts['netapp_storage_pools'] = [
            dict(
                id=storage_pool['id'],
                name=storage_pool['name'],
                available_capacity=storage_pool['freeSpace'],
                total_capacity=storage_pool['totalRaidedSpace'],
                used_capacity=storage_pool['usedSpace']
            ) for storage_pool in array_facts['volumeGroup']]

        all_volumes = list(array_facts['volume'])

        facts['netapp_volumes'] = [
            dict(
                id=v['id'],
                name=v['name'],
                parent_storage_pool_id=v['volumeGroupRef'],
                capacity=v['capacity'],
                is_thin_provisioned=v['thinProvisioned'],
                workload=v['metadata'],
            ) for v in all_volumes]

        workload_tags = None
        try:
            rc, workload_tags = self.request("storage-systems/%s/workloads" % self.ssid)
        except Exception as error:
            self.module.fail_json(msg="Failed to retrieve workload tags. Array [%s]." % self.ssid)

        facts['netapp_workload_tags'] = [
            dict(
                id=workload_tag['id'],
                name=workload_tag['name'],
                attributes=workload_tag['workloadAttributes']
            ) for workload_tag in workload_tags]

        # Create a dictionary of volume lists keyed by host names
        facts['netapp_volumes_by_initiators'] = dict()
        for mapping in array_facts['storagePoolBundle']['lunMapping']:
            for host in facts['netapp_hosts']:
                if mapping['mapRef'] == host['hosts_reference'] or mapping['mapRef'] == host['group_id']:
                    if host['name'] not in facts['netapp_volumes_by_initiators'].keys():
                        facts['netapp_volumes_by_initiators'].update({host['name']: []})

                    for volume in all_volumes:
                        if mapping['id'] in [volume_mapping['id'] for volume_mapping in volume['listOfMappings']]:

                            # Determine workload name if there is one
                            workload_name = ""
                            metadata = dict()
                            for volume_tag in volume['metadata']:
                                if volume_tag['key'] == 'workloadId':
                                    for workload_tag in facts['netapp_workload_tags']:
                                        if volume_tag['value'] == workload_tag['id']:
                                            workload_name = workload_tag['name']
                                            metadata = dict((entry['key'], entry['value'])
                                                            for entry in workload_tag['attributes']
                                                            if entry['key'] != 'profileId')

                            facts['netapp_volumes_by_initiators'][host['name']].append(
                                dict(name=volume['name'],
                                     id=volume['id'],
                                     wwn=volume['wwn'],
                                     workload_name=workload_name,
                                     meta_data=metadata))

        features = [feature for feature in array_facts['sa']['capabilities']]
        features.extend([feature['capability'] for feature in array_facts['sa']['premiumFeatures']
                         if feature['isEnabled']])
        features = list(set(features))  # ensure unique
        features.sort()
        facts['netapp_enabled_features'] = features

        return facts

    def get_facts(self):
        """Get the embedded or web services proxy information."""
        facts = self.get_array_facts()

        self.module.log("isEmbedded: %s" % self.is_embedded())
        self.module.log(pformat(facts))

        self.module.exit_json(msg="Gathered facts for storage array. Array ID: [%s]." % self.ssid,
                              storage_array_facts=facts)


def strip_interface_speed(speed):
    """Converts symbol interface speeds to a more common notation. Example: 'speed10gig' -> '10g'"""
    if isinstance(speed, list):
        result = [match(r"speed[0-9]{1,3}[gm]", sp) for sp in speed]
        result = [sp.group().replace("speed", "") if result else "unknown" for sp in result if sp]
        result = ["auto" if match(r"auto", sp) else sp for sp in result]
    else:
        result = match(r"speed[0-9]{1,3}[gm]", speed)
        result = result.group().replace("speed", "") if result else "unknown"
        result = "auto" if match(r"auto", result.lower()) else result
    return result


def main():
    facts = Facts()
    facts.get_facts()


if __name__ == "__main__":
    main()
