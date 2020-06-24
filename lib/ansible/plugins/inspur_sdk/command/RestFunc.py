# -*- coding:utf-8 -*-
'''
#=========================================================================
#   @Description: RestFunc Class
#
#   @author: zhong
#   @Date:
#=========================================================================
'''
import ctypes
import json
import sys
import os
import platform
import base64
import collections
from Crypto.Cipher import Blowfish


# sys.path.append("..")
sys.path.append(os.path.dirname(sys.path[0]))

retry_count = 3


def formatError(url, response):
    try:
        code = str(response.status_code)
    except BaseException:
        code = "1500"
    try:
        info = str(response.json())
    except BaseException:
        info = "response is none or response is not json"
    res_info = "Failed to call BMC interface, response status code is " + code + ": [URL]" + url + " [MSG]" + info
    return res_info


def getRemoteServerByRest(client):
    # getinfo
    JSON = {}
    response = client.request("GET", "api/maintenance/get_remote_upgrade_server", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/get_remote_upgrade_server, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = response.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/get_remote_upgrade_server", response)
    return JSON


def setRemoteServerByRest(client, url):
    # getinfo
    JSON = {}
    data = {"server_info": url}
    response = client.request("PUT", "api/maintenance/set_remote_upgrade_server", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/set_remote_upgrade_server, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'set remote server to ' + response.json().get("server_info")
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/set_remote_upgrade_server", response)
    return JSON


def getLanByRest(client):
    # getinfo
    response = client.request("GET", "api/settings/network", client.getHearder(), None, None, None, None)
    JSON = {}
    status_dict = {0: 'Disabled', 1: 'Enabled'}
    # dhcp_dict={0:'static',-1:'disable',1:'dhcp'}
    dhcp_dict = {0: 'Static', -1: 'Disabled', 1: 'DHCP'}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/network, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        for res in result:
            res['lan_enable'] = status_dict[res['lan_enable']]
            res['ipv4_enable'] = status_dict[res['ipv4_enable']]
            res['ipv6_enable'] = status_dict[res['ipv6_enable']]
            res['vlan_enable'] = status_dict[res['vlan_enable']]
            res['ipv4_dhcp_enable'] = dhcp_dict[res['ipv4_dhcp_enable']]
            res['ipv6_dhcp_enable'] = dhcp_dict[res['ipv6_dhcp_enable']]
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/network", response)
    return JSON


def getNetworkByRest(client):
    # getinfo
    response = client.request("GET", "api/settings/network", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/network, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/network", response)
    return JSON


def setLanByRest(client, lan):
    # getinfo
    data = {
        "id": lan['id'],
        "interface_name": lan['interface_name'],
        "channel_number": lan['channel_number'],
        # "interface_name": "eth0",
        # "channel_number": 8,
        "mac_address": lan['mac_address'],
        "lan_enable": lan['lan_enable'],

        "ipv4_enable": lan['ipv4_enable'],
        "ipv4_dhcp_enable": lan['ipv4_dhcp_enable'],
        "ipv4_address": lan['ipv4_address'],
        "ipv4_subnet": lan['ipv4_subnet'],
        "ipv4_gateway": lan['ipv4_gateway'],

        "ipv6_enable": lan['ipv6_enable'],
        "ipv6_dhcp_enable": lan['ipv6_dhcp_enable'],
        "ipv6_address": lan['ipv6_address'],
        "ipv6_index": lan['ipv6_index'],
        "ipv6_prefix": lan['ipv6_prefix'],
        "ipv6_gateway": lan['ipv6_gateway'],

        "vlan_enable": lan['vlan_enable'],
        "vlan_id": lan['vlan_id'],
        "vlan_priority": lan['vlan_priority'],
    }
    response = client.request("PUT", "api/settings/network/" + str(lan['id']), client.getHearder(), json=data)
    JSON = {}
    if response is None or response == {}:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/network/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/network", response)
    return JSON

#{'data': '01 05 00 18 00 00 00', 'code': 0}


def setSysBootByRest(client, boottype, effective, device):
    InputToDev = {
        "none": 0,
        "HDD": 2,
        "PXE": 1,
        "CD": 5,
        "BIOSSETUP": 6,
    }
    InputToStyle = {
        'Once': 0,
        'Continuous': 1,
    }
    InputToType = {
        'Legacy': 0,
        'UEFI': 1,
    }
    data = {
        'dev': InputToDev.get(device, 0),
        'enable': 1,
        'style': InputToStyle.get(effective, 0),
        'boottype': InputToType.get(boottype, 1)
    }

    response = client.request("POST", "api/bootOption", client.getHearder(), json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/bootOption, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/bootOption", response)
    return JSON
# {'data': '01 05 00 18 00 00 00', 'code': 0}


def setM6BootOptionByRest(client, data):

    response = client.request("POST", "api/bootOption", client.getHearder(), json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/bootOption, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/bootOption", response)
    return JSON


def getM6BootOptionByRest(client):
    response = client.request("GET", "api/bootOption", client.getHearder(), timeout=500)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/bootOption, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/bootOption", response)
    return JSON


def getAlertLog(client):

    response = client.request("GET", "api/logs/alertLog", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/alertLog, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/alertLog", response)
    return JSON


# fileurl file path
def getOneKeyLogByRest(client, fileurl):
    # getinfo
    response = client.request("GET", "tmp/onekeylog.tar", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface tmp/onekeylog.tar, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        try:
            f = open(fileurl, 'wb')
            f.write(response.content)
            f.close()
            JSON['data'] = "Download success, log path is " + os.path.abspath(fileurl)
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = "write to onekey log file error"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("tmp/onekeylog.tar", response)
    return JSON


def getAdapterByRest(client):
    # getinfo
    response = client.request("GET", "api/status/adapter_info", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/adapter_info, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/adapter_info", response)
    return JSON


def getAdapterByRestT6(client):
    # getinfo
    response = client.request("GET", "api/status/NIC_info", client.getHearder(), None, None, None, None)
    # print(response.json())
    JSON = {}
    status_dict = {0: 'disable', 1: 'enable'}
    dhcp_dict = {0: 'static', -1: 'disable', 1: 'dhcp'}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/NIC_info, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/NIC_info", response)
    return JSON


def getChassisStatusByRest(client):
    JSON = {}
    led_status = {0: 'Off', 1: 'Blink 1HZ', 2: 'Blink 2HZ', 4: 'Blink 4HZ', 255: 'On'}
    power_status = {1: 'On', 0: 'Off'}
    response = client.request("GET", "api/chassis-status", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/chassis-status, response is none'
    elif response.status_code == 200:
        result = response.json()
        if 'led_status' in result and 'power_status' in result:
            JSON['code'] = 0
            JSON['data'] = {}
            JSON['data']['led_status'] = led_status.get(result['led_status'], result['led_status'])
            JSON['data']['power_status'] = power_status.get(result['power_status'], result['power_status'])
        else:
            JSON['code'] = 1
            JSON['data'] = 'null'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/chassis-status", response)
    return JSON


def getFruByRest(client):

    JSON = {}
    response = client.request("GET", "api/fru", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/fru, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/fru", response)
    return JSON


def getHealthSummaryByRest(client):

    JSON = {}
    response = client.request("GET", "api/status/health_summary", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/health_summary, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/health_summary", response)
    return JSON


def getPsuInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/status/psu_info", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/psu_info, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/psu_info", response)
    return JSON


def getPcieInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/status/device_inventory", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/device_inventory, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/device_inventory", response)
    return JSON


def getDiskbackplaneInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/status/diskbackplane_info", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/diskbackplane_info, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/diskbackplane_info", response)
    return JSON


def getHardDiskInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/status/harddisk_info", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/harddisk_info, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/harddisk_info", response)
    return JSON


def getPsuInfo1ByRest(client):
    JSON = {}
    response = client.request("GET", "api/psu/psu_info", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/psu/psu_info, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/psu/psu_info", response)
    return JSON


def setPsuModeByRest(client, id, mode):
    JSON = {}
    data_mode = {}
    data_mode['id'] = id
    data_mode['mode'] = mode
    response = client.request("PUT", "api/psu/psu-mode", client.getHearder(), json=data_mode)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/psu/psu-mode, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/psu/psu-mode", response)
    return JSON


def getPsuPeakByRest(client):
    JSON = {}
    response = client.request("GET", "api/powerPeak", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/powerPeak, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/powerPeak", response)
    return JSON


def setPsuPeakByRest(client, enable, time):
    JSON = {}
    data = {
        'enable': enable,
        'time': time
    }
    response = client.request("POST", "api/powerPeak", client.getHearder(), data=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/powerPeak, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/powerPeak", response)
    return JSON


def getPowerPolicyByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/power_policy", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/power_policy, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/power_policy", response)
    return JSON


def setPowerPolicyByRest(client, action):
    JSON = {}
    data = {"action": action}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    response = client.request("POST", "api/settings/power_policy", header, data=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/power_policy, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/power_policy", response)
    return JSON


def getFanInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/status/fan_info", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/fan_info, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/fan_info", response)
    return JSON


def setM6PowerByRest(client, command):
    JSON = {}
    data = {}
    data['power_command'] = command
    response = client.request("POST", "api/actions/power", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/actions/power, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/actions/power", response)
    return JSON


def setChassisLEDByRest(client, data):
    JSON = {}
    response = client.request("POST", "api/actions/chassis-led", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/actions/chassis-led, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/actions/chassis-led", response)
    return JSON


def setM5FanModeByRest(client, mode):
    JSON = {}
    data_mode = {}
    data_mode['control_mode'] = mode
    response = client.request("PUT", "api/settings/fans-mode", client.getHearder(), json=data_mode)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/fans-mode, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/fans-mode", response)
    return JSON


def setM5FanSpeedByRest(client, id, fanspeedlevel):
    JSON = {}
    data_fan = {}
    data_fan['duty'] = fanspeedlevel
    response = client.request("PUT", "api/settings/fan/" + str(id), client.getHearder(), json=data_fan)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/fan/, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/fan/" + str(id), response)
    return JSON


def getM5FanModeByRest(client):
    JSON = {}

    response = client.request("GET", "api/settings/fans-mode", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/fans-mode, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/fans-mode", response)
    return JSON


def getCpuInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/status/cpu_info", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/cpu_info, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/cpu_info", response)
    return JSON


def getSensorsInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/sensors", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/sensors, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/sensors", response)
    return JSON


def getMemoryInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/status/memory_info", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/memory_info, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/memory_info", response)
    return JSON


def getServiceInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/services", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/services, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/services", response)
    return JSON


def setServiceByRest(client, data, num):
    JSON = {}
    header = client.getHearder()
    response = client.request("PUT", "/api/settings/services/" + str(num), data=None, json=data, headers=header)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/services, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/services", response)
    return JSON


def getInterfaceByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/network-interfaces", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/network-interfaces, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/network-interfaces", response)
    return JSON


def getM5VncSessionInfoByRest(client):
    JSON = {}
    data_id = {'service_id': 256}
    response = client.request("GET", "api/settings/service-sessions?service_id=256", client.getHearder(), json=data_id, data=None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/service-sessions?service_id=256, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/service-sessions?service_id=256", response)
    return JSON


def get5568M5VncSessionInfoByRest(client):
    JSON = {}
    data_id = {'service_id': 64}
    response = client.request("GET", "api/settings/service-sessions?service_id=64", client.getHearder(), json=data_id, data=None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/service-sessions?service_id=256, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/service-sessions?service_id=256", response)
    return JSON


def deleteM5VncSessionByRest(client, id):
    JSON = {}
    response = client.request("DELETE", "api/settings/service-sessions/{0}".format(str(id)), client.getHearder(), json=None,
                              data=None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface ' + 'api/settings/service-sessions/{0}'.format(str(id)) + ', response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/service-sessions/{0}".format(str(id)), response)
    return JSON


def mountnfsByRest(client, host, path):
    data = {
        "id": 1,
        "local_media_support": 0,
        "remote_media_support": 1,
        "same_settings": 0,
        "cd_remote_server_address": host,
        "cd_remote_source_path": path,
        "cd_remote_share_type": "nfs",
        "cd_remote_domain_name": "",
        "cd_remote_user_name": "",
        "mount_cd": 1,
        "mount_fd": 0,
        "fd_remote_server_address": "",
        "fd_remote_source_path": "",
        "fd_remote_share_type": "",
        "fd_remote_domain_name": "",
        "fd_remote_user_name": "",
        "mount_hd": 0,
        "hd_remote_server_address": "",
        "hd_remote_source_path": "",
        "hd_remote_share_type": "",
        "hd_remote_domain_name": "",
        "hd_remote_user_name": ""
        }
    response = client.request("PUT", "api/settings/media/general", client.getHearder(), data=None, json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/general, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/general", response)
    return JSON


def mountM6nfsByRest(client, host, path):

    data = {
        "id": 1,
        "cd_error_code": 0,
        "cd_image_name": "",
        "cd_remote_password": "",
        "local_media_support": 0,
        "remote_media_support": 1,
        "same_settings": 0,
        "cd_remote_server_address": host,
        "cd_remote_source_path": path,
        "cd_remote_share_type": "nfs",
        "cd_remote_domain_name": "",
        "cd_remote_user_name": "",
        "mount_cd": 1,
        "mount_hd": 0,
        "hd_error_code": 0,
        "hd_image_name": "",
        "hd_remote_password": "",
        "hd_remote_server_address": "",
        "hd_remote_source_path": "",
        "hd_remote_share_type": "",
        "hd_remote_domain_name": "",
        "hd_remote_user_name": "",
        "hd_remote_retry_count": "3",
        "hd_remote_retry_interval": "15",
        "rmedia_retry_count": 3,
        "rmedia_retry_interval": 15,
        }
    response = client.request("PUT", "api/settings/media/general", client.getHearder(), data=None, json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/general, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/general", response)
    return JSON


def mountcifsByRest(client, host, path, username, passwd):
    data = {
        "id": 1,
        "local_media_support": 0,
        "remote_media_support": 1,
        "same_settings": 0,
        "cd_remote_server_address": host,
        "cd_remote_source_path": path,
        "cd_remote_share_type": "cifs",
        "cd_remote_domain_name": "",
        "cd_remote_password": passwd,
        "cd_remote_user_name": username,
        "mount_cd": 1,
        "mount_fd": 0,
        "fd_remote_server_address": "",
        "fd_remote_source_path": "",
        "fd_remote_share_type": "",
        "fd_remote_domain_name": "",
        "fd_remote_user_name": "",
        "mount_hd": 0,
        "hd_remote_server_address": "",
        "hd_remote_source_path": "",
        "hd_remote_share_type": "",
        "hd_remote_domain_name": "",
        "hd_remote_user_name": ""
        }
    response = client.request("PUT", "api/settings/media/general", client.getHearder(), data=None, json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/general, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/general", response)
    return JSON


def mountM6cifsByRest(client, host, path, username, passwd):
    data = {
        "id": 1,
        "cd_error_code": 0,
        "cd_image_name": "",
        "local_media_support": 0,
        "remote_media_support": 1,
        "same_settings": 0,
        "cd_remote_server_address": host,
        "cd_remote_source_path": path,
        "cd_remote_share_type": "cifs",
        "cd_remote_domain_name": "",
        "cd_remote_password": passwd,
        "cd_remote_user_name": username,
        "mount_cd": 1,
        "mount_hd": 0,
        "hd_error_code": 0,
        "hd_image_name": "",
        "hd_remote_password": "",
        "hd_remote_server_address": "",
        "hd_remote_source_path": "",
        "hd_remote_share_type": "",
        "hd_remote_domain_name": "",
        "hd_remote_user_name": "",
        "rmedia_retry_count": 3,
        "rmedia_retry_interval": 15,
        "hd_remote_retry_count": "3",
        "hd_remote_retry_interval": "15"
        }
    response = client.request("PUT", "api/settings/media/general", client.getHearder(), data=None, json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/general, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/general", response)
    return JSON

#{ "id": 1, "local_media_support": 0, "remote_media_support": 1, "same_settings": 0, "cd_remote_server_address": "100.2.28.203", "cd_remote_source_path": "\/data\/nfs\/server\/", "cd_remote_share_type": "nfs", "cd_remote_domain_name": "", "cd_remote_user_name": "", "mount_cd": 1, "cd_image_name": "", "cd_error_code": 0, "mount_hd": 0, "hd_remote_server_address": "100.2.28.203", "hd_remote_source_path": "\/data\/nfs\/server\/", "hd_remote_share_type": "nfs", "hd_remote_domain_name": "", "hd_remote_user_name": "", "hd_image_name": "", "hd_error_code": 0, "rmedia_retry_count": 3, "rmedia_retry_interval": 15 }


def getMediaRedirectionGeneralSettingsByRest(client):
    response = client.request("GET", "api/settings/media/general", client.getHearder(), data=None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/general, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/general", response)
    return JSON


def setMediaRedirection(client, mediaSettings):
    # print(mediaSettings)
    response = client.request("PUT", "api/settings/media/general", client.getHearder(), data=None, json=mediaSettings)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/general, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/general", response)
    return JSON


def getMediaInstance(client):
    response = client.request("GET", "api/settings/media/instance", client.getHearder(), data=None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/instance, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/instance", response)
    return JSON


def setMediaInstance(client, instance):
    response = client.request("PUT", "api/settings/media/instance", client.getHearder(), json=instance)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/instance, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = response.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/instance", response)
    return JSON

# 获取远程媒体重定向


def ConfigurationsByRest(client):
    response = client.request("GET", "api/settings/media/remote/configurations", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/remote/configurations, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/remote/configurations", response)
    return JSON


def imageByRest(client):
    response = client.request("GET", "api/settings/media/remote/images", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/remote/images, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/remote/images", response)
    return JSON


def mountStartByRest(client, index, filename, type=1):

    data = {
        'image_index': index,
        'image_name': filename,
        'image_type': type
        }
    print (data)
    response = client.request("POST", "api/settings/media/remote/start-media", client.getHearder(), data=None, json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/remote/start-media, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/remote/start-media", response)
    return JSON


def mountStopByRest(client, index=0, filename="null.iso", type=1):

    data = {
        'image_index': index,
        'image_name': filename,
        'image_type': type
        }
    print(data)
    response = client.request("POST", "api/settings/media/remote/stop-media", client.getHearder(), data=None, json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface pi/settings/media/remote/stop-media, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/remote/stop-media", response)
    return JSON


# Remote Session 远程会话

def getRemoteSession(client):
    response = client.request("GET", "api/settings/media/remotesession", client.getHearder(), data=None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/remotesession, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/remotesession", response)
    return JSON


def setRemoteSession(client, session_data):
    #data = {"vnc_non_secure":0,"vnc_over_ssh":1,"vnc_over_stunnel":1,"single_port":0,"kvm_encryption":1,"local_monitor_off":1,"automatic_off":1,"id":1,"keyboard_language":"NL-BE","local_media_enable":1,"remote_media_enable":1,"vmedia_attach":1,"retry_count":"3","retry_time_interval":"20","sd_card_status":0,"kvm_client":"1"}
    response = client.request("PUT", "api/settings/media/remotesession", client.getHearder(), json=session_data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/media/remotesession, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/media/remotesession", response)
    return JSON


def getUserByRest(client):
    # getinfo
    response = client.request("GET", "api/settings/users", client.getHearder(), None, None, None, None)
    JSON = {}
    status_dict = {0: 'disable', 1: 'enable'}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        '''
        for res in result:
            res['access']=status_dict[res['access']]
            res['vmedia']=status_dict[res['vmedia']]
            res['kvm']=status_dict[res['kvm']]
        '''
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users", response)
    return JSON


def addUserByRest(client, args):
    JSON = {}
    if args.uname is None or args.uname == "":
        JSON['code'] = 1
        JSON['data'] = 'uname cannot be none'
        return JSON
    data = {"UserOperation": 0, "password_old": "", "access": args.access, "changepassword": 1, "confirm_password": args.upass, "email_format": "ami_format", "email_id": "", "fixed_user_count": 2, "id": args.userID, "kvm": args.kvm, "name": args.uname, "group_name": args.group, "network_privilege": args.roleid, "password": args.upass, "password_size": "bytes_16", "privilege_limit_serial": "user", "snmp": 0, "snmp_access": "read_only", "snmp_authentication_protocol": "sha", "snmp_privacy_protocol": "des", "ssh_key": "Not Available", "ssh_status": 0, "vmedia": args.vmm}
    response = client.request("PUT", "api/settings/users/" + str(args.userID), client.getHearder(), data=None, json=data)

    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(args.userID), response)
    return JSON


def addUserByRestM5(client, id, data):
    JSON = {}
    response = client.request("PUT", "api/settings/users/" + str(id), client.getHearder(), data=None, json=data)

    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(id), response)
    return JSON


def addUserByRestM6(client, args):
    JSON = {}
    if args.uname is None or args.uname == "":
        JSON['code'] = 1
        JSON['data'] = 'uname cannot be none'
        return JSON
    import time
    ctime = str(time.time()).split(".")[0]
    # if args.channel == 8:
    #     id = args.uerid + 16
    # else:
    #     id = args.uerid
    roleid_dict = {"Administrator": "administrator",
                   "Operator": "operator",
                   "Commonuser": "user",
                   "OEM": "oem",
                   "NoAccess": "none"}
    roleid = roleid_dict[args.roleid]
    roleid2 = "(" + roleid + "," + roleid + ")"
    access2 = "(" + str(args.access) + "," + str(args.access) + ")"
    data = {"OEMProprietary_level_Privilege": 0,
            "UserOperation": 1,
            "access": args.access,
            "accessByChannel": access2,
            "channel": 1,
            "channel_type": 4,
            "confirm_password": args.upass,
            "creation_time": ctime,
            "email_format": "ami_format",
            "email_id": args.email,
            "fixed_user_count": 0,
            "id": args.userid,
            "kvm": args.kvm,
            "name": args.uname,
            "changepassword": 1,
            "password": args.upass,
            "password_size": "bytes_16",
            "prev_snmp": 0,
            "privilege": roleid,
            "privilegeByChannel": roleid2,
            "snmp": 0,
            "snmp_access": None,
            "snmp_authentication_protocol": None,
            "snmp_privacy_protocol": None,
            "sol": args.sol,
            "ssh_key": "Not Available",
            "userid": args.userid,
            "vmedia": args.vmm}
    response = client.request("PUT", "api/settings/users/" + str(args.userid), client.getHearder(), data=None, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(args.userid), response)
    return JSON


def setUserByRest(client, args):
    JSON = {}
    if args.uname is None or args.uname == "":
        JSON['code'] = 1
        JSON['data'] = 'uname cannot be none'
        return JSON
    data = {"UserOperation": 1, "access": args.access, "changepassword": 0, "confirm_password": "", "email_format": "ami_format", "email_id": "", "fixed_user_count": 2, "id": args.userID, "kvm": args.kvm, "name": args.uname, "group_name": args.group, "network_privilege": args.roleid, "password": "", "privilege_limit_serial": "user", "snmp": 0, "snmp_access": "read_only", "snmp_authentication_protocol": "sha", "snmp_privacy_protocol": "des", "ssh_key": "Not Available", "ssh_status": 0, "vmedia": args.vmm}
    response = client.request("PUT", "api/settings/users/" + str(args.userID), client.getHearder(), data=None, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(args.userID), response)
    return JSON


def setUserByRestM6(client, args):
    JSON = {}
    if args.uname is None or args.uname == "":
        JSON['code'] = 1
        JSON['data'] = 'uname cannot be none'
        return JSON
    response = client.request("PUT", "api/settings/users/" + str(args.userid), client.getHearder(), data=None, json=args.json)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(args.userid), response)
    return JSON


def delUserByRest(client, id, name):
    JSON = {}
    if name is None or name == "":
        JSON['code'] = 1
        JSON['data'] = 'uname cannot be none'
        return JSON
    response = client.request("DELETE", "api/settings/users/" + str(id), client.getHearder())

    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(id), response)
    return JSON


def delUserByRestM6(client, args):
    data = {"id": args.userid,
            "snmp_status": 0}
    JSON = {}
    if args.uname is None or args.uname == "":
        JSON['code'] = 1
        JSON['data'] = 'uname cannot be none'
        return JSON
    response = client.request("DELETE", "api/settings/users/" + str(args.userid), client.getHearder(), json=data)

    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(args.userid), response)
    return JSON


def setpwdByRest(client, args):
    data = {"UserOperation": 1, "password_old": args.oldupass, "access": args.access, "changepassword": 1, "confirm_password": args.upass, "email_format": "ami_format", "email_id": "", "fixed_user_count": 2, "id": args.userID, "kvm": 0, "name": args.uname, "group_name": args.group, "network_privilege": args.group, "password": args.upass, "password_size": "bytes_16", "privilege_limit_serial": "user", "snmp": 0, "snmp_access": "read_only", "snmp_authentication_protocol": "sha", "snmp_privacy_protocol": "des", "ssh_key": "Not Available", "ssh_status": 0, "vmedia": 0}
    JSON = {}
    if args.uname is None or args.uname == "":
        JSON['code'] = 1
        JSON['data'] = 'uname cannot be none'
        return JSON
    response = client.request("PUT", "api/settings/users/" + str(args.userID), client.getHearder(), json=data)

    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/users/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/users/" + str(args.userID), response)
    return JSON


def getLSICtrlCountByRest(client):
    JSON = {}
    count = client.request("GET", "api/raid/getctrlcount", client.getHearder(), None, None, None, None)
    if count is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/getctrlcount, response is none'
    elif count.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = count.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/getctrlcount", count)

    return JSON


def getLSICtrlInfoByRest(client):
    JSON = {}
    ctrlInfo = client.request("GET", "api/raid/ctrlinfo", client.getHearder(), None, None, None, None)
    if ctrlInfo is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/ctrlinfo, response is none'
    elif ctrlInfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = ctrlInfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/ctrlinfo", ctrlInfo)

    return JSON


def getLSICtrlPropByRest(client):
    JSON = {}
    respondsctrlprop = client.request("GET", "api/raid/ctrlprop", client.getHearder(), None, None, None, None)
    if respondsctrlprop is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/ctrlprop, response is none'
    elif respondsctrlprop.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = respondsctrlprop.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/ctrlprop", respondsctrlprop)

    return JSON


def getLSICtrlMfcByRest(client):
    JSON = {}
    respondsctrlmfc = client.request("GET", "api/raid/ctrlmfc", client.getHearder(), None, None, None, None)
    if respondsctrlmfc is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/ctrlmfc, response is none'
    elif respondsctrlmfc.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = respondsctrlmfc.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/ctrlmfc", respondsctrlmfc)
    return JSON


def getLSICtrlLdInfoByRest(client, ctrlIndex):
    JSON = {}
    data = '{\"ctrlIndex\":' + str(ctrlIndex) + '}'
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    ctrlldinfo = client.request("POST", "api/raid/getctrlldinfo", data=data, json=data, headers=header)
    if ctrlldinfo is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/getctrlldinfo, response is none'
    elif ctrlldinfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = ctrlldinfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/getctrlldinfo", ctrlldinfo)

    return JSON


def getLSICtrlpdInfoByRest(client, ctrlIndex):
    JSON = {}
    data = '{\"ctrlIndex\":' + str(ctrlIndex) + '}'
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"

    ctrlpdinfo = client.request("POST", "api/raid/getctrlpdinfo", data=data, json=None, headers=header)
    if ctrlpdinfo is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/getctrlpdinfo, response is none'
    elif ctrlpdinfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = ctrlpdinfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/getctrlpdinfo", ctrlpdinfo)

    return JSON


def getPMCCtrlInfoByRest(client):
    JSON = {}
    respondsctrlmfc = client.request("GET", "api/raid/PMCctrlinfo", client.getHearder(), None, None, None, None)
    if respondsctrlmfc is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/PMCctrlinfo, response is none'
    elif respondsctrlmfc.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = respondsctrlmfc.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/PMCctrlinfo", respondsctrlmfc)

    return JSON


def getPMCCtrlCountByRest(client):
    JSON = {}
    count = client.request("GET", "api/raid/getPMCCtrlCount", client.getHearder(), None, None, None, None)
    if count is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/getPMCCtrlCount, response is none'
    elif count.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = count.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/getPMCCtrlCount", count)

    return JSON


def getPMCCtrlLdInfoByRest(client, ctrlIndex):
    JSON = {}
    data = '{\"ctrlIndex\":' + str(ctrlIndex) + '}'
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    ctrlldinfo = client.request("POST", "api/raid/getPMCRAIDLDInfo", data=None, json=data, headers=header)
    if ctrlldinfo is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/getPMCRAIDLDInfo, response is none'
    elif ctrlldinfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = ctrlldinfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/getPMCRAIDLDInfo", ctrlldinfo)

    return JSON


def getPMCCtrlpdInfoByRest(client, ctrlIndex):
    JSON = {}
    data = '{\"ctrlIndex\":' + str(ctrlIndex) + '}'
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"

    ctrlpdinfo = client.request("POST", "api/raid/getPMCCtrlPDInfo", data=None, json=data, headers=header)
    if ctrlpdinfo is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/getPMCCtrlPDInfo, response is none'
    elif ctrlpdinfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = ctrlpdinfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/getPMCCtrlPDInfo", ctrlIndex)

    return JSON


def locateDiskByRest(client, ctrlId, diskid, ledstate):
    '''
    locate disk
    :param client:
    :param ctrlId:
    :param diskid:
    :param ledstate:
    :return:
    '''
    data = {
        'ctrlId': ctrlId,
        'deviceId': diskid,
        'data': ledstate
    }
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    r = client.request("POST", "api/raid/locatePD", data=None, json=data, headers=header)
    if r is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/locatePD, response is none'
    elif r.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = ledstate
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/locatePD", r)
    return JSON


def addLDiskByRest(client, data):

    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    r = client.request("POST", "api/raid/addLD", data=data, json=data, headers=header)
    if r is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/addLD, response is none'
    elif r.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = r.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/addLD", r)
    return JSON


def locateLDiskByRest(client, ctrlId, diskid, ledstate):
    data = {
        'ctrlId': ctrlId,
        'deviceId': diskid,
        'data': ledstate
    }
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    r = client.request("POST", "api/raid/locateLD", data=data, json=data, headers=header)
    if r is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/locateLD, response is none'
    elif r.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = r.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/locateLD", r)
    return JSON


def initLDiskByRest(client, ctrlId, diskid, ledstate):
    data = {
        'ctrlId': ctrlId,
        'deviceId': diskid,
        'data': ledstate
    }
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    r = client.request("POST", "api/raid/initLD", data=data, json=data, headers=header)
    if r is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/initLD, response is none'
    elif r.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = r.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/initLD", r)
    return JSON


def deleteLDiskByRest(client, ctrlId, diskid):
    data = {
        'ctrlId': ctrlId,
        'deviceID': diskid
    }
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    r = client.request("POST", "api/raid/deleteLD", data=data, json=data, headers=header)
    if r is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/raid/deleteLD, response is none'
    elif r.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = r.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/raid/deleteLD", r)
    return JSON


def importBiosCfgByRest(client, filepath):
    '''
    import bios configure file
    :param client:
    :param filepath:
    :return:
    '''
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundaryF4ZROI7nayCrLnwy"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    file_name = os.path.basename(filepath)

    if not os.path.exists(filepath):
        JSON["code"] = 1
        JSON["data"] = "File path is error."
        return JSON
    if not os.path.isfile(filepath):
        JSON["code"] = 2
        JSON["data"] = "File name is needed."
        return JSON

    try:
        with open(filepath, 'r') as f:
            # content = f.read().decode("utf8")
            content = f.read()
            data = '------{0}{1}Content-Disposition: form-data; name="fwUpload"; filename="{3}" {1}Content-Type: application/octet-stream{1}{1}{2}{1}------{0}--{1}'.format(
                'WebKitFormBoundaryF4ZROI7nayCrLnwy', '\r\n', content, file_name)

            upload = client.request("POST", "api/uploadportbiossetup", data=data, headers=header)
    except BaseException:
        JSON["code"] = 3
        JSON["data"] = "Please check the file content and check if there is Chinese in the path."
        return JSON
    if upload is None:
        JSON["code"] = 4
        JSON["data"] = 'Failed to call BMC interface api/uploadportbiossetup, response is none'
        return JSON
    elif upload.status_code == 200:
        biossetup = client.request("PUT", "api/importbiossetup", header, None, None, None)
        if biossetup is None:
            JSON["code"] = 4
            JSON["data"] = 'Failed to call BMC interface api/importbiossetup, response is none'
            return JSON
        elif biossetup.status_code == 200:
            JSON["code"] = 0
            JSON["data"] = " import bios cfg success."
            return JSON
        else:
            biossetup = client.request("GET", "api/importbiossetup", header, None, None, None)
            if biossetup is None:
                JSON["code"] = 4
                JSON["data"] = 'Failed to call BMC interface api/importbiossetup, response is none'
                return JSON
            elif biossetup.status_code == 200:
                JSON["code"] = 0
                JSON["data"] = "import bios cfg success."
                return JSON
            else:
                JSON['code'] = 1
                JSON['data'] = formatError("api/importbiossetup", biossetup)
                return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/importbiossetup", upload)
        return JSON


def exportBiosCfgByRest(client, filepath):
    '''
    export bios setup configuration
    :param client:
    :param filepath:
    :return:
    '''
    JSON = {}
    header = client.getHearder()
    file_name = os.path.basename(filepath)
    data = {'filename': file_name}
    exdata = client.request("PUT", "api/biosoptionexdata", headers=header, json=data)

    if exdata is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/biosoptionexdata, response is none'
        return JSON
    elif exdata.status_code == 200:
        response = client.request("GET", "blackbox/export/{0}".format(file_name), data=None, json=None,
                                  headers=header)
        if response is None:
            JSON["code"] = 1
            JSON["data"] = 'Failed to call BMC interface ' + 'blackbox/export/{0}'.format(file_name) + ', response is none'
            return JSON
        elif response.status_code == 200:
            file_name_all = filepath
            try:
                with open(file_name_all, 'wb') as f:
                    f.write(response.content)
                    f.close()
                    JSON["code"] = 0
                    JSON["data"] = "bios config file export success: " + os.path.abspath(filepath)
                    return JSON
            except BaseException:
                JSON["code"] = 4
                JSON["data"] = "please check the path."
                return JSON
        else:
            JSON['code'] = 1
            JSON['data'] = formatError("blackbox/export/{0}".format(file_name), response)
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/biosoptionexdata", exdata)
        return JSON


def importTwoBiosCfgByRest(client, filepath):
    '''
    import two kind bios configure file
    :param client:
    :param filepath:
    :return:
    '''
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundaryF4ZROI7nayCrLnwy"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    file_name = os.path.basename(filepath)

    if not os.path.exists(filepath):
        JSON["code"] = 1
        JSON["data"] = "File path is error."
        return JSON
    if not os.path.isfile(filepath):
        JSON["code"] = 2
        JSON["data"] = "File name is needed."
        return JSON
    if file_name.split('.')[-1] == 'json':
        format_flag = 1
    elif file_name.split('.')[-1] == 'conf':
        format_flag = 0
    else:
        JSON["code"] = 6
        JSON["data"] = "please input file with suffix .json/.conf."
        return JSON
    try:
        with open(filepath, 'r') as f:
            # content = f.read().decode("utf8")
            content = f.read()
            data = '------{0}{1}Content-Disposition: form-data; name="fwUpload"; filename="{3}" {1}Content-Type: application/octet-stream{1}{1}{2}{1}------{0}--{1}'.format(
                'WebKitFormBoundaryF4ZROI7nayCrLnwy', '\r\n', content, file_name)

            upload = client.request("POST", "api/uploadportbiossetup", data=data, headers=header)
    except BaseException:
        JSON["code"] = 3
        JSON["data"] = "Please check the file content and check if there is Chinese in the path."
        return JSON
    if upload is None:
        JSON["code"] = 4
        JSON["data"] = 'Failed to call BMC interface api/uploadportbiossetup, response is none'
        return JSON
    elif upload.status_code == 200:
        biossetup = client.request("GET", "api/importbiossetup?confformat={0}".format(format_flag), header, None, None, None)
        if biossetup is None:
            JSON["code"] = 4
            JSON["data"] = 'Failed to call BMC interface ' + 'api/importbiossetup?confformat={0}'.format(format_flag) + ', response is none'
            return JSON
        elif biossetup.status_code == 200:
            JSON["code"] = 0
            JSON["data"] = " import bios cfg success."
            return JSON
        else:
            try:
                res = biossetup.json()
                JSON['code'] = res["code"]
                JSON['data'] = 'request failed, response content: ' + str(
                    res["error"]) + ', the status code is ' + str(
                    biossetup.status_code)
            except BaseException:
                JSON['code'] = 1
                JSON['data'] = 'request failed, response status code is ' + str(biossetup.status_code)
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/importbiossetup?confformat={0}".format(format_flag), upload)
        return JSON


def exportTwoBiosCfgByRest(client, filepath, file_name):
    '''
    export conf or json bios setup configuration
    :param client:
    :param filepath:
    :return:
    '''
    JSON = {}
    header = client.getHearder()
    if file_name.split('.')[-1] == 'json':
        format_flag = 1
    elif file_name.split('.')[-1] == 'conf':
        format_flag = 0
    else:
        JSON["code"] = 6
        JSON["data"] = "please input filename with suffix .json/.conf."
        return JSON

    data = {'confformat': format_flag, 'filename': file_name}
    exdata = client.request("PUT", "api/biosoptionexdata", headers=header, json=data)

    if exdata is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/biosoptionexdata, response is none'
        return JSON
    elif exdata.status_code == 200:
        response = client.request("GET", "blackbox/export/{0}".format(file_name), data=None, json=None,
                                  headers=header)
        # print(response.content)
        if response is None:
            JSON["code"] = 1
            JSON["data"] = 'Failed to call BMC interface ' + 'blackbox/export/{0}'.format(file_name) + ', response is none'
            return JSON
        elif response.status_code == 200:
            try:
                with open(filepath, mode='wb') as f:
                    f.write(response.content)
                    f.close()
                    JSON["code"] = 0
                    JSON["data"] = "bios config file export success: " + os.path.abspath(filepath)
                    return JSON
            except BaseException:
                JSON["code"] = 4
                JSON["data"] = "please check the path."
                return JSON
        else:
            JSON['code'] = 1
            JSON['data'] = formatError("blackbox/export/{0}".format(file_name), response)
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/biosoptionexdata", exdata)
        return JSON


def exportTwoBios_436_CfgByRest(client, filepath, file_name):
    '''
    export conf or json bios setup configuration
    :param client:
    :param filepath:
    :return:
    '''
    JSON = {}
    header = client.getHearder()
    if file_name.split('.')[-1] == 'json':
        format_flag = 1
    elif file_name.split('.')[-1] == 'conf':
        format_flag = 0
    else:
        JSON["code"] = 6
        JSON["data"] = "please input filename with suffix .json/.conf."
        return JSON

    data = {'confformat': format_flag, 'filename': file_name}
    exdata = client.request("PUT", "api/biosoptionexdata", headers=header, json=data)

    if exdata is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/biosoptionexdata, response is none'
        return JSON
    elif exdata.status_code == 200:
        response = client.request("GET", "tmp/export/{0}".format(file_name), data=None, json=None,
                                  headers=header)
        # print(response.content)
        if response is None:
            JSON["code"] = 1
            JSON["data"] = 'Failed to call BMC interface ' + 'tmp/export/{0}'.format(file_name) + ', response is none'
            return JSON
        elif response.status_code == 200:
            try:
                with open(filepath, mode='wb') as f:
                    f.write(response.content)
                    f.close()
                    JSON["code"] = 0
                    JSON["data"] = "bios config file export success: " + os.path.abspath(filepath)
                    return JSON
            except BaseException:
                JSON["code"] = 4
                JSON["data"] = "please check the path."
                return JSON
        else:
            JSON['code'] = 1
            JSON['data'] = formatError("tmp/export/{0}".format(file_name), response)
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/biosoptionexdata", exdata)
        return JSON

# onekeylog


def getBiosDebugByRest(client):
    JSON = {}
    fwinfo = client.request("GET", "api/BiosDebugSwitch", data=None, json=None, headers=client.getHearder())
    if fwinfo is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/BiosDebugSwitch, response is none'
    elif fwinfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = fwinfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/BiosDebugSwitch", fwinfo)

    return JSON


def setBiosDebugByRest(client, enabled):
    JSON = {}
    data = {'Bios Debug': enabled}
    fwinfo = client.request("POST", "api/BiosDebugSwitch", data=None, json=data, headers=client.getHearder())
    if fwinfo is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/BiosDebugSwitch", response is none'
    elif fwinfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = fwinfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/BiosDebugSwitch", fwinfo)

    return JSON

# NF5280M5


def generateOnekeylogByRest(client):
    # getinfo
    JSON = {}
    response = client.request("GET", "api/logs/onekeylog", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/onekeylog, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'start generate log'
    elif response.status_code == 404:
        JSON['code'] = 404
        JSON['data'] = formatError("api/logs/onekeylog", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/onekeylog", response)
    return JSON


# NF5280M5
def exportOnekeylogByRest(client):
    JSON = {}
    response = client.request("POST", "api/logs/exportonekeylog", client.getHearder(), timeout=600)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/exportonekeylog, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'start export log'
    elif response.status_code == 404:
        JSON['code'] = 404
        JSON['data'] = formatError("api/logs/exportonekeylog", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/exportonekeylog", response)
    return JSON

# NF5280M5


def getOnekeylogByRest(client, filepath):
    JSON = {}
    response = client.request("GET", "api/logs/getonekeylog", headers=client.getHearder())
    #print (response.status_code)
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/logs/getonekeylog, response is none'
        return JSON
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                f.close()
                JSON["code"] = 0
                #JSON["data"] = "file export success: " + os.path.abspath(filepath)
                JSON["data"] = "Download success, log path is " + os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON["code"] = 4
            JSON["data"] = "please check the path."
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/getonekeylog", response)
        return JSON


# progress
def getOnekeylogProgressByRest(client):
    # getinfo
    JSON = {}
    response = client.request("GET", "api/logs/collect-progress", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/collect-progress, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/collect-progress", response)
    return JSON


# FP5212G2
def getOnekeylogNameByRest(client):
    JSON = {}
    response = client.request("GET", "api/logs/getlogname", headers=client.getHearder())
    # print (response.status_code)
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/logs/getlogname, response is none'
        return JSON
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/getlogname", response)
    return JSON


def getLogFolderByRest(client):
    #print (filename)
    JSON = {}
    responds = client.request("GET", "api/logs/LogFolder", client.getHearder())
    if responds is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/logs/LogFolder, response is none'
    elif responds.status_code == 200:
        JSON['code'] = 0
        result = responds.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/LogFolder", responds)
    return JSON


def downloadonekeylogByRest(client, filepath, logpath):
    #print (filename)
    JSON = {}
    response = client.request("GET", logpath, data=None, json=None,
                              headers=None)
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface ' + logpath + ', response is none'
        return JSON
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                f.close()
                JSON["code"] = 0
                #JSON["data"] = "file export success: " + os.path.abspath(filepath)
                JSON["data"] = "Download success, log path is " + os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON["code"] = 4
            JSON["data"] = "please check the path."
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError(logpath, response)
        return JSON


def getblacklogfileexist(client, logType):
    # getinfo
    JSON = {}
    data = {
        # 'blackboxlogdir': "/blackbox/blackbox.log"
        'blackboxlogdir': "/blackbox/" + logType + ".log"
    }
    response = client.request("POST", "api/settings/getblacklogfileexist", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/getblacklogfileexist, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/getblacklogfileexist", response)
    return JSON


def downloadBlackboxlogByRest(client, filepath, logtype):
    #print (filename)
    JSON = {}
    response = client.request("GET", "blackbox/" + logtype + ".log", client.getHearder())
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface ' + 'blackbox/' + logtype + '.log' + ', response is none'
        return JSON
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                JSON["code"] = 0
                JSON["data"] = os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON["code"] = 4
            JSON["data"] = "please check the path."
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("blackbox/" + logtype + ".log", response)
        return JSON


# onekeylog ned


# onekey M6 start
# 查看进度
def getOnekeylogProgressByRestM6(client):
    JSON = {}
    response = client.request("GET", "api/logs/onekeylog/progress", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/onekeylog/progress, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/onekeylog/progress", response)
    return JSON


# 启动日志收集
def generateOnekeylogByRestM6(client):
    # getinfo
    JSON = {}
    response = client.request("GET", "api/logs/onekeylog/trigger", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/onekeylog/trigger, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'start generate log'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/onekeylog/trigger", response)
    return JSON

# 下载


def downloadonekeylogByRestM6(client, filepath):
    JSON = {}
    response = client.request("GET", "api/logs/onekeylog/logfile", data=None, json=None,
                              headers=client.getHearder())
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/logs/onekeylog/logfile, response is none'
        return JSON
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                f.close()
                JSON["code"] = 0
                JSON["data"] = "Download success, log path is " + os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON["code"] = 4
            JSON["data"] = "please check the path" + filepath
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/onekeylog/logfile", response)
        return JSON


# onekey M6 end


# SA5121 M5 428 log start
# 查看进度
def checkonekeylogexist(client):
    JSON = {}
    response = client.request("POST", "api/checkonekeylogexist", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/checkonekeylogexist, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/checkonekeylogexist", response)
    return JSON
    # 启动日志收集


def triggeronekeylog(client):
    # getinfo
    JSON = {}
    response = client.request("POST", "api/triggeronekeylog", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/triggeronekeylog, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'start generate log'
    elif response.status_code == 404:
        JSON['code'] = 404
        JSON['data'] = formatError("api/triggeronekeylog", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/triggeronekeylog", response)
    return JSON


# onekey SA5212M5 428 end

def getFwVersion(client):
    JSON = {}
    fwinfo = client.request("GET", "api/version_summary", data=None, json=None, headers=client.getHearder())
    if fwinfo is None:
        JSON["code"] = 1
        JSON["data"] = "Failed to call BMC interface api/version_summary, response is none"
    elif fwinfo.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = fwinfo.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/version_summary", fwinfo)

    return JSON


def login(client):
    data = {
        "username": strAsciiHex(client.username),
        "password": strAsciiHex(client.passcode),
        "encrypt_flag": 1
    }
    response = client.request("POST", "api/session", data=data)
    headers = {}
    try:
        if response is not None and response.status_code == 200:
            headers = {
                "X-CSRFToken": response.json()["CSRFToken"],
                "Cookie": response.headers["set-cookie"]
            }
        else:
            randomtag = client.request("GET", "api/randomtag", data=None, json=None)
            # print(randomtag.json())
            if randomtag is not None and randomtag.status_code == 200 and 'random' in randomtag.json():
                data = {
                    "username": strAsciiHex(client.username),
                    "password": strAsciiHex(client.passcode),
                    "encrypt_flag": 1,
                    "login_tag": randomtag.json().get('random')
                }
                response = client.request("POST", "api/session", data=data)
                if response is not None and response.status_code == 200:
                    headers = {
                        "X-CSRFToken": response.json()["CSRFToken"],
                        "Cookie": response.headers["set-cookie"]
                    }
                else:
                    data = {
                        "username": Encrypt(client.username),
                        "password": Encrypt(client.passcode),
                        "encrypt_flag": 2
                        }
                    response = client.request("POST", "api/session", data=data)
                    if response is not None and response.status_code == 200:
                        headers = {
                            "X-CSRFToken": response.json()["CSRFToken"],
                            "Cookie": response.headers["set-cookie"]
                        }
                    else:
                        randomtag = client.request("GET", "api/randomtag", data=None, json=None)
                        # print(randomtag.json())
                        if randomtag is not None and randomtag.status_code == 200 and 'random' in randomtag.json():
                            data = {
                                "username": Encrypt(client.username),
                                "password": Encrypt(client.passcode),
                                "encrypt_flag": 2,
                                "login_tag": randomtag.json().get('random')
                            }
                            response = client.request("POST", "api/session", data=data)
                            if response is not None and response.status_code == 200:
                                headers = {
                                    "X-CSRFToken": response.json()["CSRFToken"],
                                    "Cookie": response.headers["set-cookie"]
                                }
    except BaseException:
        headers = {}
    return headers


def getRandomtag(client):
    JSON = {}
    randomtag = client.request("GET", "api/randomtag", data=None, json=None)
    if randomtag is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/randomtag, response is none'
    elif randomtag.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = randomtag.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/randomtag", randomtag)

    return JSON


def login_tag(client, tag):
    data = {
        "username": strAsciiHex(client.username),
        "password": strAsciiHex(client.passcode),
        "encrypt_flag": 1,
        "login_tag": tag
    }
    response = client.request("POST", "api/session", data=data)
    headers = {}
    try:
        if response is not None and response.status_code == 200:
            headers = {
                "X-CSRFToken": response.json()["CSRFToken"],
                "Cookie": response.headers["set-cookie"]
            }
    except BaseException:
        headers = {}
    return headers


def loginNoEncrypt(client):
    data = {
        "username": client.username,
        "password": client.passcode,
    }
    response = client.request("POST", "api/session", data=data)
    headers = {}
    try:
        if response is not None and response.status_code == 200:
            headers = {
                "X-CSRFToken": response.json()["CSRFToken"],
                "Cookie": response.headers["set-cookie"]
            }
    except BaseException:
        headers = {}
    return headers


def logout(client):
    try:
        responds = client.request("DELETE", "api/session", client.getHearder())
    except BaseException:
        return
    return
    '''
    if responds is not None and responds.status_code == 200:
        print ("log out ok")
    else:
        print ("Failure: logout error" + responds.json()['error'])
    '''


def strAsciiHex(wordstr):
    list_str = []
    for word in wordstr:
        number = ord(word)
        list_str.append(str(hex(number ^ 127)[2:]))
    return "-".join(list_str)


def Encrypt(code):
    l = len(code)
    if l % 8 != 0:
        code = code + '\0' * (8 - (l % 8))
    code = code.encode('utf-8')
    cl = Blowfish.new('secret'.encode('utf-8'), Blowfish.MODE_ECB)
    encode = cl.encrypt(code)
    cryptedStr = base64.b64encode(encode)
    return cryptedStr


def getSnmpM5ByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/netsnmpconf", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/netsnmpconf, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/netsnmpconf", response)
    return JSON


def setSnmpM5ByRest(client, snmp):
    JSON = {}
    response = client.request("PUT", "api/settings/netsnmpconf", client.getHearder(), json=snmp)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/netsnmpconf, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/netsnmpconf", response)
    return JSON


def getSnmpInfoByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/snmp", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/snmp, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/snmp", response)
    return JSON


def setTrapComByRest(client, trapinfo):
    JSON = {}
    response = client.request("PUT", "api/settings/snmp", client.getHearder(), json=trapinfo)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/snmp, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/snmp", response)
    return JSON


def getAlertPoliciesByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/pef/alert_policies", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/pef/alert_policies, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/pef/alert_policies", response)
    return JSON


def setAlertPoliciesByRest(client, data):
    JSON = {}
    response = client.request("PUT", "api/settings/pef/alert_policies", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/pef/alert_policies, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/pef/alert_policies", response)
    return JSON


def getLanDestinationsByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/pef/lan_destinations", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/pef/lan_destinations, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/pef/lan_destinations", response)
    return JSON


def setLanDestinationsByRest(client, id, data):
    JSON = {}
    response = client.request("PUT", "api/settings/pef/lan_destinations/" + str(id), client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/pef/lan_destinations/' + str(
            id) + ', response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/pef/alert_policies" + str(id), response)
    return JSON


def getDatetimeByRest(client):
    # getinfo
    response = client.request("GET", "api/settings/date-time", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/date-time, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/date-time", response)
    return JSON


def getSynctimeByRest(client):
    # getinfo
    response = client.request("GET", "api/settings/synctime", client.getHearder(), None, None, None, None)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/synctime, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/synctime", response)
    return JSON


def setSynctimeByRest(client, data):
    # getinf
    response = client.request("POST", "api/settings/synctime", client.getHearder(), data=data, json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/synctime, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'set time sync success.'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/synctime", response)
    return JSON


def setTimezoneByRest(client, newzone):
    # getinfo
    data = {"id": 1,
            "localized_timestamp": 999,
            "ntp_auto_date": 0,
            "ntp_dhcp4_date": 0,
            "ntp_dhcp6_date": 0,
            "primary_ntp": "pool.ntp.org",
            "ptp_auto_date": 0,
            "ptp_delaymech": 0,
            "ptp_inlatency": None,
            "ptp_interface": None,
            "ptp_ipmode": 1,
            "ptp_logdelayint": None,
            "ptp_maxmasters": None,
            "ptp_outlatency": None,
            "ptp_panicmode": 0,
            "ptp_preset": 0,
            "ptp_priority1": None,
            "ptp_transport": 0,
            "ptp_unicastip": "",
            "secondary_ntp": "time.nist.gov",
            "timestamp": 999,
            # "timezone":"Asia/Shanghai",
            "timezone": newzone,
            "utc_minutes": 420}
    response = client.request("PUT", "api/settings/date-time", client.getHearder(), json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/date-time, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'set time zone success.'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/date-time", response)
    return JSON


def setTimeByRest(client, data):
    # getinf
    response = client.request("PUT", "api/settings/date-time", client.getHearder(), json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/date-time, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'set time success.'
    elif response.status_code == 16003 or response.status_code == 500:
        JSON['code'] = 0
        JSON['data'] = 'However Domain Name Resolution failed maybe due to network problems.'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/date-time", response)
    return JSON


def deleteEventLog(client):
    JSON = {}
    response = client.request("DELETE", "api/logs/event", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/event, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/event", response)
    return JSON


def deleteAuditLog(client):
    JSON = {}
    response = client.request("DELETE", "api/logs/audit", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/audit, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/audit", response)
    return JSON


def deleteSystemLog(client, level):
    JSON = {}
    response = client.request("DELETE", "api/logs/system?level=" + str(level), client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/system?level=' + str(level) + ', response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/system?level=" + str(level), response)
    return JSON

# T6


def deleteIDLLog(client):
    JSON = {}
    response = client.request("DELETE", "api/logs/idl", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/idl, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/idl", response)
    return JSON


# date 时间戳
# bmczone bmc ntp zone in minute
# showzone output zone in minute
def getEventLog(client, count, date, bmczone, showzone, health_flag):
    JSON = {}
    # try:
    response = client.request("GET", "api/logs/event", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/event, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        sensorType = NF5280M5_SensorType()
        sensorDesc = NF5280M5_SensorDesc()
        import time
        import datetime
        # print(result)
        # { "id": 521, "timestamp": 1109718598, "sensor_type": 15, "sensor_name": "SYS_FW_Progress", "record_type": 2, "gen_id1": 33, "event_dir_type": 111, "event_data1": 194, "event_data2": 7, "severity": 0 }
        loglist = []
        severity_dict = {0: "OK", 1: "Warning", 2: "Critical"}
        if count <= 0:
            count_flag = False
        else:
            count_flag = True

        if date == "":
            date_flag = False
        else:
            date_flag = True

        for item in result:
            if count_flag:
                count = count - 1
                if count < 0:
                    break
            #txbean = EventLogTXBean()
            #txlog = {}
            txlog = collections.OrderedDict()

            SensorType = sensorType.getSensorType(item["sensor_type"])
            SensorDesc = sensorDesc.getSensorDesc(item)  # 这个不是很准确，不知道js中第二个参数什么意思
            if " - " in SensorDesc:
                status = SensorDesc.split(" - ")[1].strip()
                msg = SensorDesc.split(" - ")[0].strip()
            else:
                msg = SensorDesc.strip()
                if "Asserted" in SensorDesc:
                    status = "Asserted"
                elif "Deasserted" in SensorDesc:
                    if health_flag:
                        continue
                    status = "Deasserted"
                else:
                    if health_flag:
                        continue
                    status = "Unknown"
            # txbean.Type(SensorType)
            # txbean.Message(msg)
            # txbean.Entity(item["sensor_name"])
            # txbean.Id(item["id"])
            # txbean.Severity(severity_dict[item['severity']])
            txlog["Id"] = item["id"]
            # txlog["Type"]=SensorType
            if item['severity'] == 0 and health_flag:
                continue
            txlog["Severity"] = severity_dict[item['severity']]
            # time 本时间戳为标准时间戳加上时区秒数，故需要减去bmc时区
            TimeStamp = item["timestamp"]
            TimeStamp0 = TimeStamp - (bmczone * 60)
            if date_flag:
                if date > TimeStamp0:
                    break
            #timeArray = time.localtime(TimeStamp)
            TimeStamp = TimeStamp + int((showzone - bmczone) * 60)
            timeArray = time.gmtime(TimeStamp)
            TimeStamp = time.strftime('%Y-%m-%dT%H:%M', timeArray)

            if showzone >= 0:
                ew = "+"
            else:
                ew = "-"
            zone_m = int(abs(showzone) % 60)
            zone_h = int(abs(showzone / 60))
            if zone_h < 10:
                zone_h = "0" + str(zone_h)
            else:
                zone_h = str(zone_h)
            if zone_m < 10:
                zone_m = "0" + str(zone_m)
            else:
                zone_m = str(zone_m)

            zone_x = ew + str(zone_h) + ":" + str(zone_m)
            time_x = TimeStamp + zone_x
            # txbean.EventTimestamp(time_x)
            # txbean.EntitySN("-")
            # txbean.EventId("-")
            # txbean.Status(status)
            txlog["EventTimestamp"] = time_x
            txlog["Entity"] = item["sensor_name"]
            if not health_flag:
                txlog["EntitySN"] = None
            txlog["Message"] = msg
            txlog["EventId"] = None
            if not health_flag:
                txlog["Status"] = status
            loglist.append(txlog)

        JSON["code"] = 0
        JSON["data"] = loglist
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/event", response)
    return JSON


def getAuditLogByRest(client, count, date, bmczone, showzone, health_flag):
    JSON = {}
    response = client.request("GET", "api/logs/audit", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/audit, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        import time
        import datetime
        loglist = []
        if count <= 0:
            count_flag = False
        else:
            count_flag = True

        if date == "":
            date_flag = False
        else:
            date_flag = True

        for item in result:
            if count_flag:
                count = count - 1
                if count < 0:
                    break
            txlog = collections.OrderedDict()
            txlog["Id"] = item["id"]

            # time 本时间戳为标准时间戳加上时区秒数，故需要减去bmc时区
            TimeStamp = item["timestamp"]
            TimeStamp0 = TimeStamp - (bmczone * 60)
            if date_flag:
                if date > TimeStamp0:
                    break
            #timeArray = time.localtime(TimeStamp)
            TimeStamp = TimeStamp + int((showzone - bmczone) * 60)
            timeArray = time.gmtime(TimeStamp)
            TimeStamp = time.strftime('%Y-%m-%dT%H:%M', timeArray)

            if showzone >= 0:
                ew = "+"
            else:
                ew = "-"
            zone_m = int(abs(showzone) % 60)
            zone_h = int(abs(showzone / 60))
            if zone_h < 10:
                zone_h = "0" + str(zone_h)
            else:
                zone_h = str(zone_h)
            if zone_m < 10:
                zone_m = "0" + str(zone_m)
            else:
                zone_m = str(zone_m)

            zone_x = ew + str(zone_h) + ":" + str(zone_m)
            time_x = TimeStamp + zone_x
            txlog["Timestamp"] = time_x
            txlog["HostName"] = item['hostname']
            txlog["Message"] = item['message']
            loglist.append(txlog)

        JSON["code"] = 0
        JSON["data"] = loglist
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/audit", response)
    return JSON


def getSystemLogByRest(client, level, count, date, bmczone, showzone, health_flag):
    JSON = {}
    response = client.request("GET", "api/logs/system?level=" + str(level), client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/system?level=' + str(level) + ', response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        import time
        import datetime
        loglist = []
        if count <= 0:
            count_flag = False
        else:
            count_flag = True

        if date == "":
            date_flag = False
        else:
            date_flag = True

        for item in result:
            if count_flag:
                count = count - 1
                if count < 0:
                    break
            txlog = collections.OrderedDict()
            txlog["Id"] = item["id"]

            # time 本时间戳为标准时间戳加上时区秒数，故需要减去bmc时区
            TimeStamp = item["timestamp"]
            TimeStamp0 = TimeStamp - (bmczone * 60)
            if date_flag:
                if date > TimeStamp0:
                    break
            #timeArray = time.localtime(TimeStamp)
            TimeStamp = TimeStamp + int((showzone - bmczone) * 60)
            timeArray = time.gmtime(TimeStamp)
            TimeStamp = time.strftime('%Y-%m-%dT%H:%M', timeArray)

            if showzone >= 0:
                ew = "+"
            else:
                ew = "-"
            zone_m = int(abs(showzone) % 60)
            zone_h = int(abs(showzone / 60))
            if zone_h < 10:
                zone_h = "0" + str(zone_h)
            else:
                zone_h = str(zone_h)
            if zone_m < 10:
                zone_m = "0" + str(zone_m)
            else:
                zone_m = str(zone_m)

            zone_x = ew + str(zone_h) + ":" + str(zone_m)
            time_x = TimeStamp + zone_x
            txlog["Timestamp"] = time_x
            txlog["HostName"] = item['hostname']
            txlog["Message"] = item['message']
            loglist.append(txlog)

        JSON["code"] = 0
        JSON["data"] = loglist
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/system?level=" + str(level), response)
    return JSON


def getAlertLogT6(client):
    JSON = {}
    # try:
    response = client.request("GET", "api/logs/alertLog", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/alertLog, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        # { "logtime": "2000-01-01T08:00:54+08:00", "timestamp": 946684854, "type": "BMC", "severity": "Warning", "status": "Assert", "errorCode": "1801A101", "desc": "Time_SYNC_Fail Transition to Non-Critical from OK sync ME failed", "adviser": "Step1:Check whether NTP server is normal.\nStep2:Please contact Inspur FAE.", "id": 3 },
        loglist = []
        for item in result:
            # txbean = EventLogTXBean()
            txlog = collections.OrderedDict()
            txlog["Id"] = item["id"]
            txlog['Severity'] = item["severity"]
            txlog["EventTimestamp"] = item["logtime"]
            txlog["Entity"] = item["type"]
            txlog["Message"] = item["desc"]
            txlog["EventId"] = item["errorCode"]
            #txlog["Status"] = item["status"]
            loglist.append(txlog)
        JSON["data"] = loglist

    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/alertLog", response)
    return JSON


def getidlM6(client, count, date, bmczone, showzone, health_flag):
    JSON = {}
    # try:
    response = client.request("GET", "api/logs/idl", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/idl, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        import time
        import datetime
        # { "hostName": "ProductSN", "logtime": "2000-01-01T13:15:46+08:00", "timestamp": 946703746, "type": "EVENT LOG", "severity": "Info", "status": "Assert", "errorCode": "10FF0200", "desc": "SEL_Status Log Area Reset\/Cleared ", "id": 25 }
        loglist = []
        severity_dict = {0: "OK", 1: "Warning", 2: "Critical"}
        if count <= 0:
            count_flag = False
        else:
            count_flag = True

        if date == "":
            date_flag = False
        else:
            date_flag = True

        for item in result:
            if count_flag:
                count = count - 1
                if count < 0:
                    break
            #txbean = EventLogTXBean()
            txlog = collections.OrderedDict()

            txlog["Id"] = item["id"]
            if item['severity'] == "Info" and health_flag:
                continue
            if item["severity"] == "Info":
                txlog['Severity'] = "OK"
            else:
                txlog['Severity'] = item["severity"]

            # time 只有logtime去比较
            itemtime = item["logtime"]
            itemzone = itemtime[-5:]
            itemzonewe = itemtime[-6]
            itemzoneh = itemzone.split(":")[0]
            itemzonem = itemzone.split(":")[1]
            itemzoneint = int(itemzonewe + str(int(itemzoneh) * 60 + int(itemzonem)))
            itemdate = itemtime[:-6]
            itemstructtime = time.strptime(itemdate, "%Y-%m-%dT%H:%M:%S")
            itemtimestamp = int(time.mktime(itemstructtime))
            #TimeStamp0 = TimeStamp - (bmczone * 60)
            # itemzoneint 该事件日志的时区
            # showzone 前台传递的时间的时区
            if date_flag:
                if date - 60 * int(showzone) > itemtimestamp - 60 * int(itemzoneint):
                    # break
                    # 并非按照日期排列 中间会有2000年的数据
                    continue
            # 将M6返回的日期中的时区修改为参数中默认的时区
            '''
            itemtimestamp = itemtimestamp - 60 *int(itemzoneint) + 60*int(showzone)
            timeArray = time.gmtime(itemtimestamp)
            TimeStamp = time.strftime('%Y-%m-%dT%H:%M', timeArray)
            if showzone >= 0:
                ew = "+"
            else:
                ew = "-"
            zone_m = int(abs(showzone) % 60)
            zone_h = int(abs(showzone / 60))
            if zone_h < 10:
                zone_h="0" + str(zone_h)
            else:
                zone_h=str(zone_h)
            if zone_m < 10:
                zone_m="0" + str(zone_m)
            else:
                zone_m=str(zone_m)

            zone_x = ew + str(zone_h) + ":" + str(zone_m)
            time_x=TimeStamp + zone_x
            txlog["eventTimestamp"]=time_x
            '''
            txlog["EventTimestamp"] = item["logtime"]
            txlog["Entity"] = item["type"]
            if not health_flag:
                txlog["EntitySN"] = item["hostName"]
            txlog["Message"] = item["desc"]
            txlog["EventId"] = item["errorCode"]
            if not health_flag:
                txlog["Status"] = item["status"]
            loglist.append(txlog)
        JSON["data"] = loglist

    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/idl", response)
    return JSON


def getEventLogM6(client, count, date, bmczone, showzone, health_flag):
    JSON = {}
    # try:
    responds = client.request("GET", "api/logs/eventlog?EVENTID=-3", client.getHearder(), None, None, None, None)
    result = responds.json()
    import time
    # { "id": 128, "record_type": "system_event_record", "timestamp": 946721271, "logtime": "2000-01-01T10:07:51+08:00", "GenID1": 32, "GenID2": 0, "sensor_type": "chassis", "sensor_name": "Time_SYNC_Fail", "sensor_number": 248, "ipmb_lun": 0, "event_direction": "asserted", "sensor_reading_value": 0, "event_reading_class": "discrete", "event_description": "transition_to_non_critical_from_ok" }
    loglist = []
    severity_dict = {0: "OK", 1: "Warning", 2: "Critical"}
    if count <= 0:
        count_flag = False
    else:
        count_flag = True

    if date == "":
        date_flag = False
    else:
        date_flag = True

    for item in result:
        if count_flag:
            count = count - 1
            if count < 0:
                break

        txlog = collections.OrderedDict()
        txlog["Id"] = item["id"]
        txlog['Severity'] = None

        TimeStamp = item["timestamp"]
        TimeStamp0 = TimeStamp - (bmczone * 60)
        if date_flag:
            if date > TimeStamp0:
                break
        # timeArray = time.localtime(TimeStamp)
        TimeStamp = TimeStamp + int((showzone - bmczone) * 60)
        timeArray = time.gmtime(TimeStamp)
        TimeStamp = time.strftime('%Y-%m-%dT%H:%M', timeArray)

        if showzone >= 0:
            ew = "+"
        else:
            ew = "-"
        zone_m = int(abs(showzone) % 60)
        zone_h = int(abs(showzone / 60))
        if zone_h < 10:
            zone_h = "0" + str(zone_h)
        else:
            zone_h = str(zone_h)
        if zone_m < 10:
            zone_m = "0" + str(zone_m)
        else:
            zone_m = str(zone_m)

        zone_x = ew + str(zone_h) + ":" + str(zone_m)
        time_x = TimeStamp + zone_x
        txlog["EventTimestamp"] = time_x
        txlog["Entity"] = item["sensor_name"]
        txlog["EntityType"] = item["sensor_type"]
        txlog["Message"] = item["event_description"]
        txlog["EventId"] = None
        txlog["Status"] = item["event_direction"]
        loglist.append(txlog)

    JSON["code"] = 0
    JSON["data"] = loglist
    return JSON


def getEventLogPolicyM6(client):
    JSON = {}
    # try:
    response = client.request("GET", "api/settings/log-policy", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/log-policy ,response is none'
    elif response.status_code == 200:
        try:
            result = response.json()
            pol = {
                "0": 'Linear Policy',
                "1": 'Circular Policy',
                "-1": 'N/A'
            }
            JSON['code'] = 0
            JSON["data"] = pol.get(str(result.get("policy", -1)))
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'response is not ok: ' + str(response.status_code)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/log-policy", response)
    return JSON


def setEventLogPolicyM6(client, policy):
    JSON = {}
    pol = {
        'linear': "0",
        'circular': "1"
    }
    if policy.lower() not in pol:
        JSON['code'] = 1
        JSON['data'] = "Policy should be linear or circular"
        return JSON

    data = {"id": 1, "policy": str(policy)}
    response = client.request("PUT", "api/settings/log-policy", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/log-policy ,response is none'
    elif response.status_code == 200:
        try:
            result = response.json()
            JSON['code'] = 0
            JSON['data'] = result
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/log-policy", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/log-policy", response)
    return JSON

# system debug log


def getSystemDebugLogM6(client, level):
    JSON = {}

    response = client.request("GET", "api/logs/system?level=" + str(level), client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/system?level=' + str(level) + ' ,response is none'
    elif response.status_code == 200:
        try:
            result = response.json()
            # loglist = []
            # for item in result:
            #
            #     txlog = collections.OrderedDict()
            #     txlog["Id"] = item["id"]
            #     txlog["Timestamp"] = item["logtime"]
            #     txlog["Hostname"] = item["hostname"]
            #     txlog["Message"] = item["message"]
            #     loglist.append(txlog)

            JSON["code"] = 0
            JSON["data"] = result
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/logs/system?level=" + str(level), response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/system?level=" + str(level), response)
    return JSON

# audit log


def getAuditLogM6(client):
    JSON = {}

    response = client.request("GET", "api/logs/audit", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/logs/audit ,response is none'
    elif response.status_code == 200:
        try:
            result = response.json()
            JSON["code"] = 0
            JSON["data"] = result
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/logs/audit", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/logs/audit", response)
    return JSON


def getBMCLogSettings(client):
    JSON = {}

    response = client.request("GET", "api/settings/log", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/log ,response is none'
    elif response.status_code == 200:
        try:
            result = response.json()
            JSON["code"] = 0
            JSON["data"] = result
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/log", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/log", response)
    return JSON


def setBMCLogSettings(client, settings):
    JSON = {}
    response = client.request("PUT", "api/settings/log", client.getHearder(), json=settings)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/log ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "set BMC system and audit log settings success"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/log", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/log", response)
    return JSON


def resetBMCM6(client, type):
    JSON = {}
    if type.upper() != "bmc" and type.upper() != "kvm":
        JSON['code'] = 1
        JSON['data'] = 'reset BMC or KVM only.'
    data = {"reset": type.upper()}
    response = client.request("POST", "api/diagnose/bmc-reset", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/diagnose/bmc-reset ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "reset " + type + " success"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/diagnose/bmc-reset", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/diagnose/bmc-reset", response)
    return JSON

# 开机自检代码


def getBiosPostCode(client):
    JSON = {}
    response = client.request("GET", "api/diagnose/bios-post-code", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/diagnose/bios-post-code,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/diagnose/bios-post-code", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/diagnose/bios-post-code", response)
    return JSON


# 宕机截屏状态
def getAutoState(client):
    JSON = {}
    response = client.request("GET", "api/Diagnose/GetAutoState", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/Diagnose/GetAutoState,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/Diagnose/GetAutoState", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/Diagnose/GetAutoState", response)
    return JSON

# 宕机截屏状态开启关闭
# state 0关闭1开启


def changeAutoCaptureState(client, state):
    JSON = {}
    data = {"state": state}
    response = client.request("POST", "api/Diagnose/ChangeAutoCaptureState", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/Diagnose/ChangeAutoCaptureState,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/Diagnose/ChangeAutoCaptureState", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/Diagnose/ChangeAutoCaptureState", response)
    return JSON

# TODO
# 下载宕机截图


def downloadDowntimeScreenshot(client, filepath):
    JSON = {}
    response = client.request("GET", "api/settings/download_image", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/download_image,response is none'
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                f.close()
                JSON["code"] = 0
                JSON["data"] = "download screenshots complete, screenshots file: " + os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/download_image", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/download_image", response)
    return JSON


# 手动截图
def manualCaptureScreen(client):
    JSON = {}
    response = client.request("POST", "api/diagnose/trigger-capture", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/diagnose/trigger-capture,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "Manual capture complete."
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/diagnose/trigger-capture", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/diagnose/trigger-capture", response)
    return JSON
# 删除手动截图


def deleteManualCaptureScreen(client):
    JSON = {}
    response = client.request("DELETE", "api/settings/manual_capture_image", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/manual_capture_image,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "Delete screen complete"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/manual_capture_image", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/manual_capture_image", response)
    return JSON
# 下载手动截图


def downloadManualCaptureScreen(client, filepath):
    JSON = {}
    response = client.request("GET", "api/settings/manual_capture_image", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/manual_capture_image,response is none'
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                f.close()
                JSON["code"] = 0
                JSON["data"] = "download screenshots complete, screenshots file: " + os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/manual_capture_image", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/manual_capture_image", response)
    return JSON


def getLDAPM6(client):
    JSON = {}
    response = client.request("GET", "api/settings/ldap-settings", client.getHearder(),)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ldap-settings ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/ldap-settings", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ldap-settings", response)
    return JSON


def setLDAPM6(client, ldap, data_file):
    JSON = {}
    response = client.request("PUT", "api/settings/ldap-settings", client.getHearder(), json=ldap, data=data_file)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ldap-settings ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "set ldap settings success"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/ldap-settings", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ldap-settings", response)
    return JSON


def setLDAPFile(client, files):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = 'multipart/form-data; boundary=----WebKitFormBoundaryESySkHogY2EmvMkE'
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    response = client.request("POST", "api/settings/ldap-certificates", files=files, headers=header)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ldap-certificates ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "set ldap settings success"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/ldap-certificates", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ldap-certificates", response)
    return JSON


def setLDAP(client, ldap):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    response = client.request("PUT", "api/settings/ldap-settings", header, json=ldap)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ldap-settings ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "set ldap settings success"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/ldap-settings", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ldap-settings", response)
    return JSON


def getLDAPgroupM6(client):
    JSON = {}
    response = client.request("GET", "api/settings/ldap-users", client.getHearder(),)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ldap-users ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/ldap-users", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ldap-users", response)
    return JSON


def setLDAPgroupM6(client, ldapgroup):
    JSON = {}
    id = ldapgroup.get("id", 0)
    if id not in [1, 2, 3, 4, 5]:
        JSON["code"] = 1
        JSON["data"] = "LDAP group id should be 1-5"
        return JSON
    response = client.request("PUT", "api/settings/ldap-users/" + str(id), client.getHearder(), json=ldapgroup)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = "Failed to call BMC interface api/settings/ldap-users/" + str(id) + " ,response is none"
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/ldap-users/" + str(id), response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ldap-users/" + str(id), response)
    return JSON


def delLDAPgroupM6(client, id):
    JSON = {}
    response = client.request("DELETE", "api/settings/ldap-users/" + str(id), client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = "Failed to call BMC interface api/settings/ldap-users/" + str(id) + " ,response is none"
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/ldap-users/" + str(id), response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ldap-users/" + str(id), response)
    return JSON


def getADM6(client):
    JSON = {}
    response = client.request("GET", "api/settings/active-directory-settings", client.getHearder(),)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-settings ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/active-directory-settings", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-settings", response)
    return JSON


def setADM6(client, ldap):
    JSON = {}
    response = client.request("PUT", "api/settings/active-directory-settings", client.getHearder(), json=ldap)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-settings ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "set ad settings success"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/active-directory-settings", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-settings", response)
    return JSON


def getADgroupM6(client):
    JSON = {}
    response = client.request("GET", "api/settings/active-directory-users", client.getHearder(),)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-users ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/active-directory-users", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-users", response)
    return JSON


def setADgroupM6(client, adroup):
    JSON = {}
    id = adroup.get("id", 0)
    if id not in [1, 2, 3, 4, 5]:
        JSON["code"] = 1
        JSON["data"] = "AD group id should be 1-5"
        return JSON
    response = client.request("PUT", "api/settings/active-directory-users/" + str(id), client.getHearder(), json=adroup)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = "Failed to call BMC interface api/settings/active-directory-users/" + str(id) + " ,response is none"
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/active-directory-users/" + str(id), response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-users/" + str(id), response)
    return JSON


def delADgroupM6(client, id):
    JSON = {}
    response = client.request("DELETE", "api/settings/active-directory-users/" + str(id), client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = "Failed to call BMC interface api/settings/active-directory-users/" + str(id) + " ,response is none"
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = response.json()
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/settings/active-directory-users/" + str(id), response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-users/" + str(id), response)
    return JSON


# T6
#[{'id': 2, 'name': 'MB CPLD', 'status': 'COMPLETE', 'progress': 100, 'trigger': 'POWEROFF', 'time': 900}]
def getUpdateInfoByRest(client):
    response = client.request("GET", "api/maintenance/update_info", client.getHearder(), timeout=120)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/background/update_info ,response is none'
    elif response.status_code == 200:
        try:
            result = response.json()
            JSON['code'] = 0
            JSON['data'] = result
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'response is not ok: ' + str(response.status_code)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/background/update_info", response)
    return JSON

# T6
#[ { "id": 2, "type": "UPDATE", "des": "MBCPLD update", "status": "PROCESSING", "trigger": "POWEROFF", "time": 900, "progress": 37 } ]


def getTaskInfoByRest(client):
    response = client.request("GET", "api/maintenance/background/task_info", client.getHearder(), timeout=120)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/background/task_info ,response is none'
    elif response.status_code == 200:
        try:
            result = response.json()
            JSON['code'] = 0
            JSON['data'] = result
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = 'response is not ok: ' + str(response.status_code)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/background/task_info", response)
    return JSON
# T6


def cancelTaskByRest(client, id):
    data = {"id": id}
    response = client.request("POST", "api/maintenance/background/task_cancel", client.getHearder(), json=data)
    JSON = {}
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/background/task_cancel, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/background/task_cancel", response)
    return JSON
#


def generateBMCcfgByRest(client, filename):
    # getinfo
    JSON = {}
    if ".json" not in filename:
        JSON['code'] = 1
        JSON['data'] = 'file should be xxx.json'
    data = {"filename": filename}
    response = client.request("PUT", "api/bmcConfigExData", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/bmcConfigExData, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/bmcConfigExData", response)
    return JSON

# progress


def getBMCProgressByRest(client):
    # getinfo
    JSON = {}
    response = client.request("GET", "api/export-progress", client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/export-progress, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/export-progress", response)
    return JSON


def downloadBMCcfgByRest(client, filepath, filename):
    #print (filename)
    JSON = {}
    response = client.request("GET", "tmp/export/" + filename, data=None, json=None,
                              headers=None)
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface tmp/export/, response is none'
        return JSON
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                f.close()
                JSON["code"] = 0
                JSON["data"] = "bmc config file export success: " + os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON["code"] = 4
            JSON["data"] = "please check the path."
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("tmp/export/" + filename, response)
        return JSON


def downloadBMCcfgByRestM6(client, filepath):
    JSON = {}
    response = client.request("GET", "api/maintenance/download_config", client.getHearder())
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/maintenance/download_config, response is none'
        return JSON
    elif response.status_code == 200:
        try:
            with open(filepath, 'wb') as f:
                f.write(response.content)
                f.close()
                JSON["code"] = 0
                JSON["data"] = "bmc config file export success: " + os.path.abspath(filepath)
                return JSON
        except BaseException:
            JSON["code"] = 4
            JSON["data"] = "please check the path."
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/download_config", response)


def setBMCcfgByRestM6(client, data=None):
    JSON = {}
    if data is None:
        data = {"id": 1, "snmp": 1, "kvm": 1, "network": 1, "ipmi": 1, "ntp": 1, "authentication": 1, "syslog": 1}
    response = client.request("PUT", "api/maintenance/backup_config", client.getHearder(), json=data)
    if response is None:
        JSON["code"] = 1
        JSON["data"] = 'Failed to call BMC interface api/maintenance/backup_config, response is none'
    elif response.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = ""
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/backup_config", response)
    return JSON


# t6
def importBmcRestoreByRest(client, filepath):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundaryF4ZROI7nayCrLnwy"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    file_name = os.path.basename(filepath)

    if not os.path.exists(filepath):
        JSON["code"] = 1
        JSON["data"] = "File path is error."
        return JSON
    if not os.path.isfile(filepath):
        JSON["code"] = 2
        JSON["data"] = "File name is needed."
        return JSON

    try:
        with open(filepath, 'r') as f:
            # content = f.read().decode("utf8")
            content = f.read()
            data = '------{0}{1}Content-Disposition: form-data; name="config"; filename="{3}" {1}Content-Type: application/octet-stream{1}{1}{2}{1}------{0}--{1}'.format(
                'WebKitFormBoundaryF4ZROI7nayCrLnwy', '\r\n', content, file_name)

            upload = client.request("POST", "api/maintenance/upload_restore", data=data, headers=header)
    except BaseException:
        JSON["code"] = 3
        JSON["data"] = "Please check the file content and check if there is Chinese in the path."
        return JSON
    if upload is None:
        JSON["code"] = 4
        JSON["data"] = 'Failed to call BMC interface api/maintenance/upload_restore, response is none'
        return JSON
    elif upload.status_code == 200:
        data = {"config": file_name}
        restoreconfig = client.request("POST", "api/maintenance/restore_config", data=data, headers=header)
        if restoreconfig is None:
            JSON["code"] = 4
            JSON["data"] = 'Failed to call BMC interface api/maintenance/restore_config, response is none'
            return JSON
        elif restoreconfig.status_code == 200:
            JSON["code"] = 0
            JSON["data"] = " import bmc cfg success."
            return JSON
        else:
            JSON['code'] = 1
            JSON['data'] = formatError("api/maintenance/restore_config", restoreconfig)
            return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/upload_restore", upload)
    return JSON


# T6 fwupdate
# 保存配置 sdr始终改写
def preserveBMCConfig(client, override):
    JSON = {}
    if override == 1:
        op = "preserve"
        data = {"id": 1, "sdr": 0, "fru": 0, "sel": 0, "ipmi": 0, "network": 0, "ntp": 0, "snmp": 0, "ssh": 0, "kvm": 0, "authentication": 0, "syslog": 0, "web": 0, "extlog": 0, "redfish": 0, "automationEngine": 0, "rsd": 0}
    elif override == 0:
        op = "override"
        data = {"id": 1, "sdr": 0, "fru": 1, "sel": 1, "ipmi": 1, "network": 1, "ntp": 1, "snmp": 1, "ssh": 1, "kvm": 1, "authentication": 1, "syslog": 1, "web": 1, "extlog": 1, "redfish": 1, "automationEngine": 1, "rsd": 1}
    elif isinstance(override, list):
        op = "preserve"
        data = {"id": 1, "sdr": 0, "fru": 0, "sel": 0, "ipmi": 0, "network": 0, "ntp": 0, "snmp": 0, "ssh": 0, "kvm": 0, "authentication": 0, "syslog": 0, "web": 0, "extlog": 0, "redfish": 0, "automationEngine": 0, "rsd": 0}
        for key in override:
            data[key] = 1
    response = client.request("PUT", "api/maintenance/preserve", client.getHearder(), json=data, timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/preserve, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = op + " config success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/preserve", response)
    return JSON


def getPreserveConfig(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/preserve", client.getHearder(), timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/preserve, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = response.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/preserve", response)
    return JSON


# 恢复出厂设置
def getRestoreDefaults(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/restore_defaults", client.getHearder(), timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/restore_defaults, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = response.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/restore_defaults", response)
    return JSON


def restoreDefaults(client, override):
    JSON = {}
    if override == 1:
        data = {"id": 1, "sdr": 0, "fru": 0, "sel": 0, "ipmi": 0, "network": 0, "ntp": 0, "snmp": 0, "ssh": 0, "kvm": 0, "authentication": 0, "syslog": 0, "web": 0, "extlog": 0, "redfish": 0, "automationEngine": 0, "rsd": 0}
    elif override == 0:
        data = {"id": 1, "sdr": 1, "fru": 1, "sel": 1, "ipmi": 1, "network": 1, "ntp": 1, "snmp": 1, "ssh": 1, "kvm": 1, "authentication": 1, "syslog": 1, "web": 1, "extlog": 1, "redfish": 1, "automationEngine": 1, "rsd": 1}
    elif isinstance(override, list):
        data = {"id": 1, "sdr": 0, "fru": 0, "sel": 0, "ipmi": 0, "network": 0, "ntp": 0, "snmp": 0, "ssh": 0, "kvm": 0, "authentication": 0, "syslog": 0, "web": 0, "extlog": 0, "redfish": 0, "automationEngine": 0, "rsd": 0}
        for key in override:
            data[key] = 1
    else:
        data = override
    response = client.request("PUT", "api/maintenance/restore_defaults", client.getHearder(), json=data, timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/restore_defaults, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "restore config success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/restore_defaults", response)
    return JSON


# 修改保存配置，使恢复配置&固件更新完成后改写所有配置(drop)
def setOverrideBMCConfig(client):
    JSON = {}
    data = {"id": 1, "sdr": 0, "fru": 0, "sel": 0, "ipmi": 0, "network": 0, "ntp": 0, "snmp": 0, "ssh": 0, "kvm": 0, "authentication": 0, "syslog": 0, "web": 0, "extlog": 0, "redfish": 0, "automationEngine": 0, "rsd": 0}
    response = client.request("PUT", "api/maintenance/preserve", client.getHearder(), json=data, timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/preserve, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "set override config success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/preserve", response)
    return JSON

# syncmode


def syncmodeByRest(client, flashconf, mode):
    JSON = {}
    if flashconf != 0 and flashconf != 1:
        JSON['code'] = 1
        JSON['data'] = "override should be 0 or 1"
        return JSON
    data = {"flashconf": flashconf}
    if flashconf == 1 and mode == "Manual":
        JSON['code'] = 1
        JSON['data'] = "BMC upgrade cannot set mode to manual if override configuration"
        return JSON

    if mode == "Auto":
        data["syncmode"] = 1
    elif mode == "Manual":
        data["syncmode"] = 0
    elif mode is not None:
        JSON['code'] = 1
        JSON['data'] = "mode should be Auto or Manual"
        return JSON
    response = client.request("PUT", "api/maintenance/hpm/syncmode", client.getHearder(), json=data, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/hpm/syncmode ,response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "syncmode ok"
        return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/hpm/syncmode", response)
    return JSON
# update firmware


def uploadfirmwareByRest(client, filepath):
    '''
    import bios configure file
    :param client:
    :param filepath:
    :return:
    '''
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundarydTPdpAwLgxeeqJki"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    file_name = os.path.basename(filepath)
    #print (file_name)
    if not os.path.exists(filepath):
        JSON["code"] = 1
        JSON["data"] = "File path is error."
        return JSON
    if not os.path.isfile(filepath):
        JSON["code"] = 2
        JSON["data"] = "File name is needed."
        return JSON
    file_size = os.path.getsize(filepath)
    if file_size > 5000000:
        big_flag = True
    else:
        big_flag = False
    global progress_show
    global progress_show_time
    global endflag
    progress_show = 0
    import datetime
    progress_show_time = datetime.datetime.now()
    endflag = False

    from requests_toolbelt import MultipartEncoder

    def mycalback(monitor):
        global progress_show
        global progress_show_time
        global endflag
        progess_now = monitor.bytes_read * 100 // file_size
        import datetime
        localtime = datetime.datetime.now()
        f_localtime = localtime.strftime("%Y-%m-%d %H:%M:%S ")
        # windows \b无法退回到上一行
        # linux会退回到上一行，导致每次上次的%无法被覆盖，因此必须打印多少退多少
        if not endflag:
            if progess_now >= 100:
                pro = f_localtime + "Upload file inprogress, progress: 100%"
                print(pro)
                endflag = True
            else:
                if big_flag:
                    if localtime > progress_show_time:
                        pro = f_localtime + "Upload file inprogress, progress: " + str(progess_now) + "%"
                        b_num = len(pro)
                        # print(pro + "\b"*b_num, end="",flush=True)
                        progress_show_time = localtime + datetime.timedelta(seconds=3)
                else:
                    if progess_now > progress_show:
                        pro = f_localtime + "Upload file inprogress, progress: " + str(progess_now) + "%"
                        b_num = len(pro)
                        # print(pro + "\b"*b_num, end="",flush=True)
                        progress_show = progess_now

    e = encoder.MultipartEncoder(
        fields={'fwimage': (file_name, open(filepath, 'rb').read(), 'application/octet-stream')},
        boundary='----WebKitFormBoundarydTPdpAwLgxeeqJki'
    )
    m = encoder.MultipartEncoderMonitor(e, mycalback)
    header["Content-Type"] = m.content_type

    upload = client.request("POST", "api/maintenance/hpm/firmware", data=m, headers=header, timeout=500)
    if upload is None:
        JSON["code"] = 1
        JSON["data"] = "Failed to call BMC interface api/maintenance/hpm/firmware ,response is none."
    elif upload.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = "upload firmware success."
        return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/hpm/firmware", upload)
    return JSON


def uploadfirmwarePy2(client, filepath):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundarydTPdpAwLgxeeqJki"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    file_name = os.path.basename(filepath)
    # print (file_name)
    if not os.path.exists(filepath):
        JSON["code"] = 1
        JSON["data"] = "File path is error."
        return JSON
    if not os.path.isfile(filepath):
        JSON["code"] = 2
        JSON["data"] = "File name is needed."
        return JSON

    with open(filepath.decode('utf8'), 'rb') as f:
        content = f.read()
        m = '------{0}{1}Content-Disposition: form-data; name="fwimage"; filename="{3}" {1}Content-Type: application/octet-stream{1}{1}{2}{1}------{0}--{1}'.format(
            'WebKitFormBoundarydTPdpAwLgxeeqJki', '\r\n', content, file_name)
        header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundarydTPdpAwLgxeeqJki"

    upload = client.request("POST", "api/maintenance/hpm/firmware", data=m, headers=header, timeout=500)
    if upload is None:
        JSON["code"] = 1
        JSON["data"] = "Failed to call BMC interface api/maintenance/hpm/firmware ,response is none."
    elif upload.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = "upload firmware success."
        return JSON
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/hpm/firmware", upload)
    return JSON


# getverifyresult
def getverifyresultByRest(client):
    count = 0
    while count <= retry_count:
        count = count + 1
        response = client.request("GET", "api/maintenance/hpm/getverifyresult", client.getHearder(), timeout=500)
        JSON = {}
        # print ("veri.json()")
        # print (response.json())
        if response is None:
            JSON['code'] = 1
            JSON['data'] = 'Failed to call BMC interface api/maintenance/hpm/getverifyresult ,response is none'
        elif response.status_code == 200:
            verify_result = response.json().get("verify_result", -1)
            JSON['code'] = 2
            if verify_result == 4:
                JSON['code'] = 0
                JSON['data'] = "verify pass"
                return JSON
            elif verify_result == 10:
                JSON['data'] = "verify error"
            elif verify_result == 0:
                JSON['data'] = "verify does not start yet"
            else:
                JSON['data'] = "verify error"
        else:
            JSON['code'] = 1
            JSON['data'] = formatError("api/maintenance/hpm/getverifyresult", response)
    return JSON


# T6 fwupdate end

# M5 bmc upgrade { "image_update": 3, "reboot_bmc": 1 }
# choose bmc update mode active standby both
def setFlashImageConfig(client, image):
    JSON = {}
    image_dict = {"active": '1',
                  "standby": '0',
                  "both": '3',
                  }
    if image not in image_dict:
        JSON['code'] = 1
        JSON['data'] = 'image to be updated should be active, standby or both'
        return JSON
    data = {
        'image_update': image_dict[image],
        'reboot_bmc': '1'
    }
    response = client.request("PUT", "api/maintenance/flash_image_config", client.getHearder(), json=data, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/flash_image_config, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "set flash image config success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/flash_image_config", response)
    return JSON

# enter update mode  null


def bmcFlashMode(client):
    JSON = {}
    response = client.request("PUT", "api/maintenance/flash", client.getHearder(), timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/flash, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "enter update mode success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/flash", response)
    return JSON


# upload bmc file { "cc": 0 }
def uploadBMCImageFile(client, updatefile):

    headers = client.getHearder()
    header = {}
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Connection"] = "keep-alive"
    header["X-CSRFToken"] = headers["X-CSRFToken"]
    header["Content-Length"] = "33554659"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundarydTPdpAwLgxeeqJki"
    header["Cookie"] = "" + headers["Cookie"] + ";refresh_disable=1"
    JSON = {}
    if not os.path.exists(updatefile):
        JSON['code'] = 1
        JSON['data'] = 'cannot find file.'
        return JSON
    if not os.path.isfile(updatefile):
        JSON['code'] = 1
        JSON['data'] = 'input is not a file.'
        return JSON
    if platform.system() == 'Linux':
        file_name = updatefile.split('/')[-1]
    else:
        file_name = updatefile.split('\\')[-1]

    file_size = os.path.getsize(updatefile)
    if file_size > 60000000:
        big_flag = True
    else:
        big_flag = False
    global progress_show
    global progress_show_time
    global endflag
    progress_show = 0
    import datetime
    progress_show_time = datetime.datetime.now()
    endflag = False

    from requests_toolbelt import MultipartEncoder
    from requests_toolbelt.multipart import encoder

    def mycalback(monitor):
        global progress_show
        global progress_show_time
        global endflag
        progess_now = monitor.bytes_read * 100 // file_size
        import datetime
        localtime = datetime.datetime.now()
        f_localtime = localtime.strftime("%Y-%m-%d %H:%M:%S ")
        if not endflag:
            if progess_now >= 100:
                print(f_localtime + "Upload file inprogress, progress: 100%")
                endflag = True
            else:
                if big_flag:
                    if localtime > progress_show_time:
                        pro = f_localtime + "Upload file inprogress, progress: " + str(progess_now) + "%"
                        b_num = len(pro)
                        # print(pro + "\b"*b_num, end="",flush=True)
                        progress_show_time = localtime + datetime.timedelta(seconds=3)
                else:
                    if progess_now > progress_show:
                        pro = f_localtime + "Upload file inprogress, progress: " + str(progess_now) + "%"
                        b_num = len(pro)
                        # print(pro + "\b"*b_num, end="",flush=True)
                        progress_show = progess_now

    e = encoder.MultipartEncoder(
        fields={'fwimage': (file_name, open(updatefile, 'rb').read(), 'application/octet-stream')},
        boundary='----WebKitFormBoundarydTPdpAwLgxeeqJki'
    )
    m = encoder.MultipartEncoderMonitor(e, mycalback)

    # from requests_toolbelt import MultipartEncoder
    # m = MultipartEncoder(
    #     fields={'fwimage': (file_name, open(updatefile, 'rb').read(), 'application/octet-stream')},
    #     boundary='----WebKitFormBoundarydTPdpAwLgxeeqJki'
    # )
    header["Content-Type"] = m.content_type
    upload = client.request("POST", "api/maintenance/firmware", data=m, headers=header, timeout=500)
    if upload is not None and upload.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "Upload files completed."
    else:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware, response is none'
    return JSON


# verification
def verifyUpdateImageByRest(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/firmware/verification", client.getHearder(), timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware/verification, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "verify update file success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/firmware/verification", response)
    return JSON

# 配置设置


def preserveBMCConfigM5(client, overide):
    JSON = {}
    if overide == 1:
        # override
        op = "override"
        data = {"id": 0, "sdr": 0, "fru": 0, "sel": 0, "ipmi": 0, "network": 0, "ntp": 0, "snmp": 0, "ssh": 0, "kvm": 0, "authentication": 0, "syslog": 0, "pef": 0, "sol": 0, "smtp": 0, "user": 0, "dcmi": 0, "hostname": 0}
    else:
        # preserve
        op = "preserve"
        data = {"id": 0, "sdr": 0, "fru": 1, "sel": 1, "ipmi": 1, "network": 1, "ntp": 1, "snmp": 1, "ssh": 1, "kvm": 1, "authentication": 1, "syslog": 1, "pef": 1, "sol": 1, "smtp": 1, "user": 1, "dcmi": 1, "hostname": 1}

    response = client.request("PUT", "api/maintenance/preserve", client.getHearder(), json=data, timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/preserve, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = op + " config success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/preserve", response)
    return JSON

# 修改所有配置(drop)


def setOverrideBMCConfigM5(client):
    JSON = {}
    data = {"id": 0, "sdr": 0, "fru": 0, "sel": 0, "ipmi": 0, "network": 0, "ntp": 0, "snmp": 0, "ssh": 0, "kvm": 0, "authentication": 0, "syslog": 0, "pef": 0, "sol": 0, "smtp": 0, "user": 0, "dcmi": 0, "hostname": 0}
    response = client.request("PUT", "api/maintenance/preserve", client.getHearder(), json=data, timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/preserve, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "set override config success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/preserve", response)
    return JSON

# preserve1  override0 (drop)
# 保留所有配置，除了sdr


def peserveBMCCfgExceptSDRM5(client):
    JSON = {}
    data = {"id": 0, "sdr": 0, "fru": 1, "sel": 1, "ipmi": 1, "network": 1, "ntp": 1, "snmp": 1, "ssh": 1, "kvm": 1, "authentication": 1, "syslog": 1, "pef": 1, "sol": 1, "smtp": 1, "user": 1, "dcmi": 1, "hostname": 1}
    response = client.request("PUT", "api/maintenance/preserve", client.getHearder(), json=data, timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/preserve, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "set override config success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/preserve", response)
    return JSON


# update { "preserve_config": 0, "flash_status": 1 }
# preserve_config 0 改写      1保留
def updateBMCByRest(client, preserve_config, flash_status):
    # preserve_config 0-override   1-reserve
    # flash_status 1 ： 刷写整个固件    2 ： 基于段的固件刷写    4 ： 基于版本版本比较的固件刷写  8 ：双Image 刷写
    JSON = {}
    data = {
        "preserve_config": str(preserve_config),
        "flash_status": str(flash_status)
    }
    response = client.request("PUT", "api/maintenance/firmware/upgrade", client.getHearder(), json=data, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware/upgrade, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "start to upgrade"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/firmware/upgrade", response)
    return JSON

# progress
#{ "id": 1, "action": "Flashing...", "progress": "0% done         ", "state": 0 }
#{ "id": 1, "action": "Flashing...", "progress": "100% done", "state": 0 }
#


def getBMCUpgradeProgessByRest(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/firmware/flash-progress", client.getHearder(), timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware/flash-progress, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = response.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/firmware/flash-progress", response)
    return JSON


# reset
def resetBmcByRest(client):
    JSON = {}
    response = client.request("POST", "api/maintenance/reset", client.getHearder())
    if response is not None and response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'Abort firmware update mode completed.'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/reset", response)
    return JSON

# verification


def getBMCImageByRest(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/dual_image_config", client.getHearder(), timeout=50)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/dual_image_config, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = response.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/dual_image_config", response)
    return JSON
# M5 bmc upgrade end


# M5 bios upgrade
# 获取BIOS 的Flash 模式 { "id": 1, "mode": 0 }
def getBiosFlashModeByRest(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/firmware/flash-mode", client.getHearder())
    if response is not None and response.status_code == 200:
        if response.json()['mode'] == 1:
            JSON['code'] = 1
            JSON['data'] = 'Failure: this server is in flash Mode, please wait'
        else:
            JSON['code'] = 0
            JSON['data'] = 'not in flash mode'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/firmware/flash-mode", response)
    return JSON


# power bios pnor

# 设置Pnor的Flash模式
# {"id":"false","guard":"false","attr":"false"}
def setPnorPreserveByRest(client):
    JSON = {}
    data = {"id": "false", "guard": "false", "attr": "false"}
    response = client.request("PUT", "api/maintenance/pnorPreserve", client.getHearder(), json=data)
    if response is not None and response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'ok'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/pnorPreserve", response)
    return JSON


# 获取Pnor的Flash模式
# { "id": 1, "guard": 0, "attr": 0 }
def getPnorPreserveByRest(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/pnorPreserve", client.getHearder())
    if response is not None and response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'ok'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/pnorPreserve", response)
    return JSON

# 设置BIOS 升级时的保留选项 { "preserve_setup_options": 0, "force_update_bios": "no" }
# 0 ：升级时不需要保存BIOS 选项
# 1 ：升级时需要保存BIOS 选项


def setBiosFlashOptionByRest(client, reserve):
    data = {
        'preserve_setup_options': reserve,
        'force_update_bios': 'no'
    }
    JSON = {}
    response = client.request("PUT", "api/maintenance/bios_flash", client.getHearder(), json=data)
    if response is not None and response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = 'Set BIOS Setup Options complete'
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/bios_flash", response)
    return JSON

# 上传镜像 { "cc": 0 }


def uploadBiosImageFile(client, updatefile):
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundarydTPdpAwLgxeeqJki"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    JSON = {}
    if not os.path.exists(updatefile):
        JSON['code'] = 1
        JSON['data'] = 'cannot find file.'
        return JSON
    if not os.path.isfile(updatefile):
        JSON['code'] = 1
        JSON['data'] = 'can not find file.'
        return JSON
    if platform.system() == 'Linux':
        file_name = updatefile.split('/')[-1]
    else:
        file_name = updatefile.split('\\')[-1]

    file_size = os.path.getsize(updatefile)
    if file_size > 5000000:
        big_flag = True
    else:
        big_flag = False
    global progress_show
    global progress_show_time
    global endflag
    progress_show = 0
    import datetime
    progress_show_time = datetime.datetime.now()
    endflag = False

    from requests_toolbelt import MultipartEncoder
    from requests_toolbelt.multipart import encoder

    def mycalback(monitor):
        global progress_show
        global progress_show_time
        global endflag
        progess_now = monitor.bytes_read * 100 // file_size
        import datetime
        localtime = datetime.datetime.now()
        f_localtime = localtime.strftime("%Y-%m-%d %H:%M:%S ")
        if not endflag:
            if progess_now >= 100:
                print(f_localtime + "Upload file inprogress, progress: 100%")
                endflag = True
            else:
                if big_flag:
                    if localtime > progress_show_time:
                        pro = f_localtime + "Upload file inprogress, progress: " + str(progess_now) + "%"
                        b_num = len(pro)
                        # print(pro + "\b"*b_num, end="",flush=True)
                        progress_show_time = localtime + datetime.timedelta(seconds=3)
                else:
                    if progess_now > progress_show:
                        pro = f_localtime + "Upload file inprogress, progress: " + str(progess_now) + "%"
                        b_num = len(pro)
                        # print(pro + "\b"*b_num, end="",flush=True)
                        progress_show = progess_now

    e = encoder.MultipartEncoder(
        fields={'fwimage': (file_name, open(updatefile, 'rb').read(), 'application/octet-stream')},
        boundary='----WebKitFormBoundarydTPdpAwLgxeeqJki'
    )
    m = encoder.MultipartEncoderMonitor(e, mycalback)
    header["Content-Type"] = m.content_type

    # from requests_toolbelt import MultipartEncoder
    # m = MultipartEncoder(
    #     fields={'fwimage': (file_name, open(updatefile, 'rb').read(), 'application/octet-stream')},
    #     boundary='----WebKitFormBoundarydTPdpAwLgxeeqJki'
    # )
    # header["Content-Type"] = m.content_type

    upload = client.request("POST", "api/maintenance/firmware", data=m, headers=header, timeout=500)
    if upload is not None and upload.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "Upload files completed."
    else:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware, response is none'
    return JSON

# verification []


def verifyBiosUpdateImageByRest(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/firmware/bios_verification", client.getHearder(), timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware/bios_verification, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "verify update file success"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/firmware/bios_verification", response)
    return JSON

# update { "preserve_me": 1, "preserve_setup_options": 0, "preserve_phy_image": 1, "preserve_phy_mac": 1 }
# def updateBiosByRest(client, preserve_config, flash_status):


def updateBiosByRest(client, hasme):
    image_dict = {"preserve": '1',
                  "overwrite": '0'}
    JSON = {}
    if hasme == 1:
        data = {
            "preserve_me": 0,
            "preserve_setup_options": 1,
            "preserve_phy_image": 0,
            "preserve_phy_mac": 1,
            "preserve_passwd_options": 1
        }
    else:
        data = {
            "preserve_me": 1,
            "preserve_setup_options": 1,
            "preserve_phy_image": 0,
            "preserve_phy_mac": 1,
            "preserve_passwd_options": 1
        }

    response = client.request("PUT", "api/maintenance/firmware/biosupgrade", client.getHearder(), json=data, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware/biosupgrade, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = "start to upgrade"
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/firmware/biosupgrade", response)
    return JSON

#{ "id": 1, "action": "Flashing...", "progress": "0% done         ", "state": 0 }
#{ "id": 1, "action": "Flashing...", "progress": "97% done         ", "state": 0 }
#{ "id": 1, "action": "Flashing...", "progress": "Complete...", "state": 2 }


def getBiosUpgradeProgessByRest(client):
    JSON = {}
    response = client.request("GET", "api/maintenance/firmware/flash-progress", client.getHearder(), timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/firmware/flash-progress, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        JSON['data'] = response.json()
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/firmware/flash-progress", response)
    return JSON

# M5 bios upgrade end


def uploadBMCfgByRest(client, filepath):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "multipart/form-data;boundary=----WebKitFormBoundaryF4ZROI7nayCrLnwy"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"

    if platform.system() == 'Linux':
        file_name = filepath.split('/')[-1]
    else:
        file_name = filepath.split('\\')[-1]

    if not os.path.exists(filepath):
        JSON["code"] = 1
        JSON["data"] = "File path is error."
        return JSON
    if not os.path.isfile(filepath):
        JSON["code"] = 2
        JSON["data"] = "File name is needed."
        return JSON

    try:
        with open(filepath, 'r') as f:
            # content = f.read().decode("utf8")
            content = f.read()
            data = '------{0}{1}Content-Disposition: form-data; name="fwUpload"; filename="{3}" {1}Content-Type: application/octet-stream{1}{1}{2}{1}------{0}--{1}'.format(
                'WebKitFormBoundaryF4ZROI7nayCrLnwy', '\r\n', content, file_name)

            upload = client.request("POST", "api/uploadBmcConfig", data=data, headers=header, timeout=500)
            # 上传
            if upload is None:
                JSON["code"] = 4
                JSON["data"] = 'Failed to call BMC interface api/uploadBmcConfig, response is none'
            elif upload.status_code == 200:
                JSON["code"] = 0
                JSON["data"] = "upload success."
            else:
                JSON['code'] = 1
                JSON['data'] = formatError("api/uploadBmcConfig", upload)
    except BaseException:
        JSON["code"] = 3
        JSON["data"] = "Please check if there is Chinese in the path."

    return JSON


def importBMCfgByRest(client):
    JSON = {}
    header = client.getHearder()

    import_res = client.request("GET", "api/importBmcConfig", header, None, None, None, timeout=500)
    if import_res is None:
        JSON["code"] = 4
        JSON["data"] = 'Failed to call BMC interface api/importBmcConfig, response is none'
    elif import_res.status_code == 200:
        JSON["code"] = 0
        JSON["data"] = "import bmc cfg success."
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/importBmcConfig", import_res)
    return JSON


def getBMCImportProgressByRest(client):
    JSON = {}
    header = client.getHearder()

    response = client.request("GET", "api/import-progress", header, None, None, None, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/import-progress, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/import-progress", response)
    return JSON


# progress
def restoreBMCByRest(client):
    # getinfo
    JSON = {}
    r = client.request("GET", "api/maintenance/restore_defaults", client.getHearder(), data=None, json=None)
    if r.status_code == 200:
        data = r.json()
    else:
        data = {
            'authentication': 0,
            'dcmi': 0,
            'hostname': 0,
            'ipmi': 0,
            'kvm': 0,
            'network': 0,
            'ntp': 0,
            'pef': 0,
            'sdr': 0,
            'sel': 0,
            'smtp': 0,
            'snmp': 0,
            'sol': 0,
            'ssh': 0,
            'syslog': 0,
            'user': 0,
            'fru': 0,
            'id': 1,
            'extlog': 0,
            'web': 1,
            'redfish': 1
        }
    response = client.request("PUT", "api/maintenance/restore_defaults", client.getHearder(), data=None, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/maintenance/restore_defaults, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/maintenance/restore_defaults", response)
    return JSON


def uptimeBMCByRest(client):
    JSON = {}
    header = client.getHearder()

    response = client.request("GET", "api/status/uptime", header, None, None, None, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/uptime, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/uptime", response)
    return JSON


def getSessionsBMCByRest(client):
    JSON = {}
    header = client.getHearder()

    response = client.request("GET", "api/settings/active-sessions", header, None, None, None, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-sessions, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-sessions", response)
    return JSON


def deleteSessionBMCByRest(client, id):
    JSON = {}
    response = client.request("DELETE", "api/settings/service-sessions/" + str(id), client.getHearder())
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/service-sessions/, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/service-sessions/" + str(id), response)
    return JSON


def getHddBMCByRest(client):
    JSON = {}
    header = client.getHearder()
    response = client.request("GET", "api/status/SATA_HDDinfo", header, None, None, None, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/status/SATA_HDDinfo, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/status/SATA_HDDinfo", response)
    return JSON


def getDNSBMCByRest(client):
    JSON = {}
    header = client.getHearder()
    response = client.request("GET", "api/settings/dns-info", header, None, None, None, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/dns-info, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/dns-info", response)
    return JSON


def getDomainOptionsBMCByRest(client):
    JSON = {}
    header = client.getHearder()
    response = client.request("GET", "api/settings/dns/domain-options", header, None, None, None, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/dns/domain-options, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/dns/domain-options", response)
    return JSON


def getServerOptionsBMCByRest(client):
    JSON = {}
    header = client.getHearder()
    response = client.request("GET", "api/settings/dns/server-options", header, None, None, None, timeout=500)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/dns/server-options, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/dns/server-options", response)
    return JSON


def setDNSBMCByRest(client, data):
    JSON = {}
    response = client.request("PUT", "api/settings/dns-info", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/dns-info, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/dns-info", response)
    return JSON


def setDNSRestartBMCByRest(client, data):
    JSON = {}
    response = client.request("PUT", "api/settings/dns/restart", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/dns/restart, response is none'
    elif response.status_code == 200:
        JSON['code'] = 0
        result = response.json()
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/dns/restart", response)
    return JSON


def getSMTPByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/smtpcfg", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/smtpcfg, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/smtpcfg", response)
    return JSON


def setSMTPByRest(client, smtpinfo):
    JSON = {}
    response = client.request("PUT", "api/settings/smtpcfg", client.getHearder(), json=smtpinfo)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/smtpcfg, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/smtpcfg", response)
    return JSON


def getSNMPByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/snmpconf", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/snmpconf, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/snmpconf", response)
    return JSON


def setSNMPByRest(client, smtpinfo):
    JSON = {}
    response = client.request("PUT", "api/settings/snmpconf", client.getHearder(), json=smtpinfo)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/snmpconf, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/snmpconf", response)
    return JSON


def getNCSIByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/ncsi-interfaces-adaptive-support", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ncsi-interfaces-adaptive-support, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ncsi-interfaces-adaptive-support", response)
    return JSON


def getNCSIOptionByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/ncsi-interfaces-adaptive", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ncsi-interfaces-adaptive, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ncsi-interfaces-adaptive", response)
    return JSON


def setNCSIByRest(client, ncsiinfo):
    JSON = {}
    response = client.request("POST", "api/settings/ncsi-interfaces-adaptive", client.getHearder(), data=ncsiinfo)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ncsi-interfaces-adaptive, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ncsi-interfaces-adaptive", response)
    return JSON


def getSMTPM5ByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/smtp", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/smtp, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/smtp", response)
    return JSON


def setSMTPM5ByRest(client, id, smtpinfo):
    JSON = {}
    response = client.request("PUT", "api/settings/smtp/" + str(id), client.getHearder(), json=smtpinfo)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/smtp/' + str(id) + ', response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/smtp/" + str(id), response)
    return JSON


def getNCSIM5ByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/ncsi-interfaces", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ncsi-interfaces, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ncsi-interfaces", response)
    return JSON


def getNCSIModeM5ByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/ncsi/mode", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ncsi/mode, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ncsi/mode", response)
    return JSON


def setNCSIModeM5ByRest(client, data):
    JSON = {}
    response = client.request("PUT", "api/settings/ncsi/mode", client.getHearder(), json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/ncsi/mode, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/ncsi/mode", response)
    return JSON


def getADByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/active-directory-settings", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-settings, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-settings", response)
    return JSON


def setADByRest(client, data):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    response = client.request("PUT", "api/settings/active-directory-settings", header, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-settings, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-settings", response)
    return JSON


def getADGroupByRest(client):
    JSON = {}
    response = client.request("GET", "api/settings/active-directory-users", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-users, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-users", response)
    return JSON


def setADGroupByRest(client, id, data):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    response = client.request("PUT", "api/settings/active-directory-users/" + str(id), header, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-users/' + str(id) + ', response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-users/" + str(id), response)
    return JSON


def delADGroupByRest(client, id):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    response = client.request("DELETE", "api/settings/active-directory-users/" + str(id), header)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/active-directory-users/' + str(id) + ', response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/active-directory-users/" + str(id), response)
    return JSON


def getUserGroupByRest(client):
    JSON = {}
    response = client.request("GET", "api/getusergroup", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/getusergroup, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/getusergroup", response)
    return JSON


def addUserGroupByRest(client, name, pri):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    data = {
        'GroupName': name,
        'GroupPriv': pri,
        'operator': 0
    }
    response = client.request("POST", "api/setusergroup", header, data=data, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/setusergroup, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/setusergroup", response)
    return JSON


def setUserGroupByRest(client, id, name, pri):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    data = {
        'GroupID': id,
        'GroupName': name,
        'GroupPriv': pri,
        'operator': 2
    }
    response = client.request("POST", "api/setusergroup", header, data=data, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/setusergroup, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/setusergroup", response)
    return JSON


def delUserGroupByRest(client, id, name):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    data = {
        'GroupID': id,
        'GroupName': name,
        'operator': 1
    }
    response = client.request("PSOT", "api/setusergroup", header, data=data, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC api/setusergroup, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/setusergroup", response)
    return JSON


def getDNSByRestM5(client):
    JSON = {}
    response = client.request("GET", "api/settings/dns", client.getHearder(), None, None, None, None)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/dns, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/dns", response)
    return JSON


def setDNSByRestM5(client, data):
    JSON = {}
    header = client.getHearder()
    header["X-Requested-With"] = "XMLHttpRequest"
    header["Content-Type"] = "application/json;charset=UTF-8"
    header["Cookie"] = "" + header["Cookie"] + ";refresh_disable=1"
    response = client.request("PUT", "api/settings/dns", header, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/settings/dns, response is none'
    elif response.status_code == 200:
        result = response.json()
        JSON['code'] = 0
        JSON['data'] = result
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/settings/dns", response)
    return JSON


def resetBMC(client, type):
    JSON = {}
    if type != 0 and type != 1:
        JSON['code'] = 1
        JSON['data'] = 'reset BMC or KVM only.'
    data = {"reset": type}
    response = client.request("POST", "api/diagnose/bmc-reset", client.getHearder(), data=data, json=data)
    if response is None:
        JSON['code'] = 1
        JSON['data'] = 'Failed to call BMC interface api/diagnose/bmc-reset ,response is none'
    elif response.status_code == 200:
        try:
            JSON["code"] = 0
            JSON["data"] = "reset " + type + " success"
        except BaseException:
            JSON['code'] = 1
            JSON['data'] = formatError("api/diagnose/bmc-reset", response)
    else:
        JSON['code'] = 1
        JSON['data'] = formatError("api/diagnose/bmc-reset", response)
    return JSON


class NF5280M5_SensorType():

    def __init__(self):
        self.getSensorTypeKey = getSensorTypeKey

    def getSensorType(self, var):
        return self.getSensorTypeKey("en", var)


class NF5280M5_SensorDesc():

    def __init__(self):
        command_path = os.path.dirname(os.path.realpath(__file__))
        ipmi_path = os.path.join(command_path, "M5Log")
        #print (ipmi_path)
        sys.path.append(ipmi_path)

        import eventLogString
        self.eventLogString = eventLogString.eventLogString

        import sensorSpecificEventStr
        self.sensorSpecificEventStr = sensorSpecificEventStr.sensorSpecificEventStr

        import biosPostEventStr
        self.biosPostEventStr = biosPostEventStr.biosPostEventStr

        import sensorEventStr
        self.sensorEventStr = sensorEventStr.sensorEventStr

        import commonInfoStr
        self.commonInfoStr = commonInfoStr.commonInfoStr

        # import showSensorDesc
        # ShowSensorDesc = showSensorDesc.ShowSensorDesc()
        self.showSensorDesc = showSensorDesc
        # filepath = os.path.abspath("./../script/mappers/dict/M5/showSensorDesc.py")
        # mod = os.path.splitext(filepath)[0]  # 子命令模块名称('setBios', '.py')
        # mod_im = import_module(mod)  #
        # self.showSensorDesc = getattr(mod_im, 'showSensorDesc1')

        # RecordID:2
        # RecordType:2
        # TimeStamp:1499276566
        # GenID1:32
        # GenID2:0
        # EvmRev:4
        # SensorType:13
        # SensorName:HDD0_Status
        # EventDirType:111
        # EventData1:0
        # EventData2:255
        # EventData3:255
        # Severity:0

    def getSensorDesc(self, item):
        desc = self.showSensorDesc(self.eventLogString, self.sensorSpecificEventStr, self.biosPostEventStr,
                                   self.sensorEventStr, "en", self.commonInfoStr, item)
        # print(desc)
        return desc


sensortype_strings = {}
sensortype_strings[0] = "All Sensors"
sensortype_strings[1] = "Temperature"
sensortype_strings[2] = "Voltage"
sensortype_strings[3] = "Current"
sensortype_strings[4] = "Fan"
sensortype_strings[5] = "Physical Security (Chassis Intrusion)"
sensortype_strings[6] = "Platform Security Violation Attempt"
sensortype_strings[7] = "Processor"
sensortype_strings[8] = "Power Supply"
sensortype_strings[9] = "Power Unit"
sensortype_strings[10] = "Cooling Device"
sensortype_strings[11] = "Other Units-based sensor"
sensortype_strings[12] = "Memory"
sensortype_strings[13] = "Drive Slot (Bay)"
sensortype_strings[14] = "POST Memory Resize"
sensortype_strings[15] = "BIOS POST Progress"
sensortype_strings[16] = "Event Logging disabled"
sensortype_strings[17] = "Watchdog 1"
sensortype_strings[18] = "System Event"
sensortype_strings[19] = "Critical Interrupt"
sensortype_strings[20] = "Button / Switch"
sensortype_strings[21] = "Module / Board"
sensortype_strings[22] = "Microcontroller / Coprocessor"
sensortype_strings[23] = "Add-in Card"
sensortype_strings[24] = "Chassis"
sensortype_strings[25] = "Chip Set"
sensortype_strings[26] = "Other FRU"
sensortype_strings[27] = "Cable / Interconnect"
sensortype_strings[28] = "Terminator"
sensortype_strings[29] = "System Boot / Restart Initiated"
sensortype_strings[30] = "Boot Error"
sensortype_strings[31] = "OS Boot"
sensortype_strings[32] = "OS Stop / Shutdown"
sensortype_strings[33] = "Slot / Connector"
sensortype_strings[34] = "System ACPI Power State"
sensortype_strings[35] = "Watchdog 2"
sensortype_strings[36] = "Platform Alert"
sensortype_strings[37] = "Entity Presence"
sensortype_strings[38] = "Monitor ASIC / IC"
sensortype_strings[39] = "LAN"
sensortype_strings[40] = "Management Subsystem Health"
sensortype_strings[41] = "Battery"
sensortype_strings[42] = "Session Audit"
sensortype_strings[43] = "Version Change"
sensortype_strings[44] = "FRU State"
sensortype_strings[58] = "OEM"

# liuby_20120516 ++<<
sensortype_strings[193] = "Status"
sensortype_strings[194] = "PMBus Power State"
sensortype_strings[195] = "CPU State"
sensortype_strings[196] = "Memory State"
# liuby_20120516 ++>>

# lgg_add ++<<
sensortype_strings[197] = "PMBus OV "
sensortype_strings[198] = "PMBus OI "
sensortype_strings[199] = "DISK"
# lgg_add ++>>
sensortype_strings[200] = "PSU DC Period Check"
sensortype_strings[201] = "BIOS Options Setted Outband"  # add by wxl for bios setup outband set 20150312<<>>

sensortype_strings[220] = "Node Manager Event"

sensortype_strings_cn = {}
sensortype_strings_cn[0] = "所有传感器"
sensortype_strings_cn[1] = "温度"
sensortype_strings_cn[2] = "电压"
sensortype_strings_cn[3] = "电流"
sensortype_strings_cn[4] = "风扇"
sensortype_strings_cn[5] = "物理安全"
sensortype_strings_cn[6] = "平台安全违规企图"
sensortype_strings_cn[7] = "处理器"
sensortype_strings_cn[8] = "电源供电"
sensortype_strings_cn[9] = "电源模块"
sensortype_strings_cn[10] = "冷却装置"
sensortype_strings_cn[11] = "其他单位为基础的传感器"
sensortype_strings_cn[12] = "内存"
sensortype_strings_cn[13] = "驱动器槽"
sensortype_strings_cn[14] = "进行内存大小调整"
sensortype_strings_cn[15] = "系统固件进展"
sensortype_strings_cn[16] = "禁用事件日志记录"
sensortype_strings_cn[17] = "看门狗1"
sensortype_strings_cn[18] = "系统事件"
sensortype_strings_cn[19] = "关键性中断"
sensortype_strings_cn[20] = "按键/开关"
sensortype_strings_cn[21] = "模块/主板"
sensortype_strings_cn[22] = "微控制器/协处理器"
sensortype_strings_cn[23] = "附加卡"
sensortype_strings_cn[24] = "机型"
sensortype_strings_cn[25] = "芯片组"
sensortype_strings_cn[26] = "其他FRU"
sensortype_strings_cn[27] = "有线/互联"
sensortype_strings_cn[28] = "终止"
sensortype_strings_cn[29] = "系统启动/重新启动"
sensortype_strings_cn[30] = "启动故障"
sensortype_strings_cn[31] = "操作系统启动"
sensortype_strings_cn[32] = "操作系统关键性停止"
sensortype_strings_cn[33] = "槽/连接器"
sensortype_strings_cn[34] = "系统ACPI电源状态"
sensortype_strings_cn[35] = "看门狗2"
sensortype_strings_cn[36] = "平台警报"
sensortype_strings_cn[37] = "实体存在"
sensortype_strings_cn[38] = "监控 ASIC/IC"
sensortype_strings_cn[39] = "局域网"
sensortype_strings_cn[40] = "管理子系统健康信息"
sensortype_strings_cn[41] = "电池"
sensortype_strings_cn[42] = "会话审计"
sensortype_strings_cn[43] = "版本变更"
sensortype_strings_cn[44] = "FRU状态"
sensortype_strings_cn[58] = "OEM"
# liuby_20120516 ++<<
sensortype_strings_cn[193] = "状态"
sensortype_strings_cn[194] = "PMBus电源状态"
sensortype_strings_cn[195] = "CPU状态"
sensortype_strings_cn[196] = "内存状态"
# liuby_20120516 ++>>

# lgg_add ++<<
sensortype_strings_cn[197] = "PMBus过压"
sensortype_strings_cn[198] = "PMBus过流"
sensortype_strings_cn[199] = "磁盘"
# lgg_add ++>>
sensortype_strings_cn[200] = "高压直流电源定测检测"
sensortype_strings_cn[201] = "BIOS配置参数带外设置"  # add by wxl for bios setup outband set 20150312<<>>

sensortype_strings_cn[220] = "节点管理器事件"

sensorTypeString = {}
sensorTypeString["cn"] = sensortype_strings_cn
sensorTypeString["en"] = sensortype_strings


def getSensorTypeKey(language, key):
    if (language == 'cn'):
        return sensorTypeString['cn'][key]
    elif (language == 'en'):
        return sensorTypeString['en'][key]
    else:
        return "No support language"


def showSensorDesc(eventLogString, sensorSpecificEventStr, biosPostEventStr, sensorEventStr, curLang, commonInfoStr,
                   item):
    eventLogStrings = eventLogString[curLang]
    sensor_specific_event = sensorSpecificEventStr[curLang]
    sensorEvent_Str = sensorEventStr[curLang]
    biosPostEvent_Str = biosPostEventStr[curLang]
    commonInfo_Str = commonInfoStr[curLang]
    eventdesc = ""
    m_Max_allowed_offset = {}
    m_Max_allowed_offset[0] = 0x0
    m_Max_allowed_offset[1] = 0x0b
    m_Max_allowed_offset[2] = 0x3
    m_Max_allowed_offset[3] = 0x2
    m_Max_allowed_offset[4] = 0x2
    m_Max_allowed_offset[5] = 0x2
    m_Max_allowed_offset[6] = 0x2
    m_Max_allowed_offset[7] = 0x8
    m_Max_allowed_offset[8] = 0x2
    m_Max_allowed_offset[9] = 0x2
    m_Max_allowed_offset[10] = 0x8
    m_Max_allowed_offset[11] = 0x7
    m_Max_allowed_offset[12] = 0x3

    m_Max_allowed_SensorSpecific_offset = {}
    m_Max_allowed_SensorSpecific_offset[5] = 6
    m_Max_allowed_SensorSpecific_offset[6] = 5
    m_Max_allowed_SensorSpecific_offset[7] = 12
    m_Max_allowed_SensorSpecific_offset[8] = 6
    m_Max_allowed_SensorSpecific_offset[9] = 7
    m_Max_allowed_SensorSpecific_offset[12] = 10
    m_Max_allowed_SensorSpecific_offset[13] = 8
    m_Max_allowed_SensorSpecific_offset[15] = 2
    m_Max_allowed_SensorSpecific_offset[16] = 6
    m_Max_allowed_SensorSpecific_offset[17] = 7
    m_Max_allowed_SensorSpecific_offset[18] = 5
    m_Max_allowed_SensorSpecific_offset[19] = 11

    m_Max_allowed_SensorSpecific_offset[20] = 4
    m_Max_allowed_SensorSpecific_offset[25] = 1
    m_Max_allowed_SensorSpecific_offset[27] = 1
    m_Max_allowed_SensorSpecific_offset[29] = 7
    m_Max_allowed_SensorSpecific_offset[30] = 4
    m_Max_allowed_SensorSpecific_offset[31] = 6
    m_Max_allowed_SensorSpecific_offset[32] = 5
    m_Max_allowed_SensorSpecific_offset[33] = 9
    m_Max_allowed_SensorSpecific_offset[34] = 13
    m_Max_allowed_SensorSpecific_offset[35] = 8
    m_Max_allowed_SensorSpecific_offset[36] = 3
    m_Max_allowed_SensorSpecific_offset[37] = 2
    m_Max_allowed_SensorSpecific_offset[39] = 1
    m_Max_allowed_SensorSpecific_offset[40] = 5
    m_Max_allowed_SensorSpecific_offset[41] = 2
    m_Max_allowed_SensorSpecific_offset[42] = 3
    m_Max_allowed_SensorSpecific_offset[43] = 7
    m_Max_allowed_SensorSpecific_offset[44] = 7
    m_Max_allowed_SensorSpecific_offset[200] = 8
    m_Max_allowed_SensorSpecific_offset[201] = 2

    def getbits(orig, startbit, endbit):
        temp = orig
        mask = 0x00
        for i in range(startbit, endbit - 1, -1):
            mask = mask | (1 << i)

        return (temp & mask)

    if (item['record_type'] >= 0x0 and item['record_type'] <= 0xBF):
        type = getbits(item['event_dir_type'], 6, 0)
        # if (type == 0x0):

        # elif(type == 0x6F):
        if (type == 0x6F):
            offset = getbits(item['event_data1'], 3, 0)
            if (m_Max_allowed_SensorSpecific_offset[item['sensor_type']] >= offset):
                eventdesc = sensor_specific_event[item['sensor_type']][offset]
            else:
                eventdesc = eventLogStrings.STR_EVENT_LOG_INVALID_OFFSET

        elif (type >= 0x01) and (type <= 0x0C):
            offset = getbits(item['event_data1'], 3, 0)
            if (m_Max_allowed_offset[type] >= offset):
                eventdesc = sensorEvent_Str[type][offset]
            else:
                eventdesc = eventLogStrings['STR_EVENT_LOG_INVALID_OFFSET']

        else:
            eventdesc = "OEM Discrete"

        if (item['gen_id1'] == 0x21 and item['sensor_type'] == 0xf):
            if (getbits(item['event_data1'], 7, 6) == 0xC0 and (offset >= 0 and offset <= 2)):
                if (2 == offset):
                    offset = 1

                eventdesc += "-" + biosPostEvent_Str[offset][getbits(item['event_data2'], 3, 0)]

            else:
                eventdesc += "-" + "Unknown"

        if item['gen_id1'] == 0x20:
            if item['sensor_type'] == 0x12:
                if (getbits(item['event_data2'], 7, 7) == 0):
                    eventdesc += " " + commonInfo_Str['STR_START']
                else:
                    eventdesc += " " + commonInfo_Str['STR_STOP']

        if getbits(item['event_dir_type'], 7, 7) == 0:
            if (eventdesc is not None):
                if "Asserted" not in eventdesc:
                    eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_ASSERT']
            else:
                eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_ASSERT']
        else:
            if (eventdesc is not None):
                if "Deasserted" not in eventdesc:
                    eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_DEASSERT']

            else:
                eventdesc += " - " + eventLogStrings['STR_EVENT_LOG_DEASSERT']

    elif (item['record_type'] >= 0xC0 and item['record_type'] <= 0xDF):
        eventdesc = "OEM timestamped"

    elif (item['record_type'] >= 0xE0 and item['record_type'] <= 0xFF):
        eventdesc = "OEM non-timestamped"

    return eventdesc
