#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_facts
version_added: '2.6'
deprecated:
  removed_in: '2.13'
  why: Deprecated in favor of C(_info) module.
  alternative: Use M(purefa_info) instead.
short_description: Collect facts from Pure Storage FlashArray
description:
  - Collect facts information from a Pure Storage Flasharray running the
    Purity//FA operating system. By default, the module will collect basic
    fact information including hosts, host groups, protection
    groups and volume counts. Additional fact information can be collected
    based on the configured set of arguments.
author:
  - Pure Storage ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  gather_subset:
    description:
      - When supplied, this argument will define the facts to be collected.
        Possible values for this include all, minimum, config, performance,
        capacity, network, subnet, interfaces, hgroups, pgroups, hosts,
        admins, volumes, snapshots, pods, vgroups, offload, apps and arrays.
    type: list
    required: false
    default: minimum
extends_documentation_fragment:
  - purestorage.fa
'''

EXAMPLES = r'''
- name: collect default set of facts
  purefa_facts:
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: collect configuration and capacity facts
  purefa_facts:
    gather_subset:
      - config
      - capacity
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: collect all facts
  purefa_facts:
    gather_subset:
      - all
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
ansible_facts:
  description: Returns the facts collected from the FlashArray
  returned: always
  type: complex
  sample: {
        "capacity": {},
        "config": {
            "directory_service": {
                "array_admin_group": null,
                "base_dn": null,
                "bind_password": null,
                "bind_user": null,
                "check_peer": false,
                "enabled": false,
                "group_base": null,
                "readonly_group": null,
                "storage_admin_group": null,
                "uri": []
            },
            "dns": {
                "domain": "domain.com",
                "nameservers": [
                    "8.8.8.8",
                    "8.8.4.4"
                ]
            },
            "ntp": [
                "0.ntp.pool.org",
                "1.ntp.pool.org",
                "2.ntp.pool.org",
                "3.ntp.pool.org"
            ],
            "smtp": [
                {
                    "enabled": true,
                    "name": "alerts@acme.com"
                },
                {
                    "enabled": true,
                    "name": "user@acme.com"
                }
            ],
            "snmp": [
                {
                    "auth_passphrase": null,
                    "auth_protocol": null,
                    "community": null,
                    "host": "localhost",
                    "name": "localhost",
                    "privacy_passphrase": null,
                    "privacy_protocol": null,
                    "user": null,
                    "version": "v2c"
                }
            ],
            "ssl_certs": {
                "country": null,
                "email": null,
                "issued_by": "",
                "issued_to": "",
                "key_size": 2048,
                "locality": null,
                "organization": "Acme Storage, Inc.",
                "organizational_unit": "Acme Storage, Inc.",
                "state": null,
                "status": "self-signed",
                "valid_from": "2017-08-11T23:09:06Z",
                "valid_to": "2027-08-09T23:09:06Z"
            },
            "syslog": []
        },
        "default": {
            "array_name": "flasharray1",
            "connected_arrays": 1,
            "hostgroups": 0,
            "hosts": 10,
            "pods": 3,
            "protection_groups": 1,
            "purity_version": "5.0.4",
            "snapshots": 1,
            "volume_groups": 2
        },
        "hgroups": {},
        "hosts": {
            "host1": {
                "hgroup": null,
                "iqn": [
                    "iqn.1994-05.com.redhat:2f6f5715a533"
                ],
                "wwn": []
            },
            "host2": {
                "hgroup": null,
                "iqn": [
                    "iqn.1994-05.com.redhat:d17fb13fe0b"
                ],
                "wwn": []
            },
            "host3": {
                "hgroup": null,
                "iqn": [
                    "iqn.1994-05.com.redhat:97b1351bfb2"
                ],
                "wwn": []
            },
            "host4": {
                "hgroup": null,
                "iqn": [
                    "iqn.1994-05.com.redhat:dd84e9a7b2cb"
                ],
                "wwn": [
                    "10000000C96C48D1",
                    "10000000C96C48D2"
                ]
            }
        },
        "interfaces": {
            "CT0.ETH4": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682",
            "CT0.ETH5": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682",
            "CT1.ETH4": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682",
            "CT1.ETH5": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682"
        },
        "network": {
            "ct0.eth0": {
                "address": "10.10.10.10",
                "gateway": "10.10.10.1",
                "hwaddr": "ec:f4:bb:c8:8a:04",
                "mtu": 1500,
                "netmask": "255.255.255.0",
                "services": [
                    "management"
                ],
                "speed": 1000000000
            },
            "ct0.eth2": {
                "address": "10.10.10.11",
                "gateway": null,
                "hwaddr": "ec:f4:bb:c8:8a:00",
                "mtu": 1500,
                "netmask": "255.255.255.0",
                "services": [
                    "replication"
                ],
                "speed": 10000000000
            },
            "ct0.eth3": {
                "address": "10.10.10.12",
                "gateway": null,
                "hwaddr": "ec:f4:bb:c8:8a:02",
                "mtu": 1500,
                "netmask": "255.255.255.0",
                "services": [
                    "replication"
                ],
                "speed": 10000000000
            },
            "ct0.eth4": {
                "address": "10.10.10.13",
                "gateway": null,
                "hwaddr": "90:e2:ba:83:79:0c",
                "mtu": 1500,
                "netmask": "255.255.255.0",
                "services": [
                    "iscsi"
                ],
                "speed": 10000000000
            },
            "ct0.eth5": {
                "address": "10.10.10.14",
                "gateway": null,
                "hwaddr": "90:e2:ba:83:79:0d",
                "mtu": 1500,
                "netmask": "255.255.255.0",
                "services": [
                    "iscsi"
                ],
                "speed": 10000000000
            },
            "vir0": {
                "address": "10.10.10.20",
                "gateway": "10.10.10.1",
                "hwaddr": "fe:ba:e9:e7:6b:0f",
                "mtu": 1500,
                "netmask": "255.255.255.0",
                "services": [
                    "management"
                ],
                "speed": 1000000000
            }
        },
        "offload": {
            "nfstarget": {
                "address": "10.0.2.53",
                "mount_options": null,
                "mount_point": "/offload",
                "protocol": "nfs",
                "status": "scanning"
            }
        },
        "performance": {
            "input_per_sec": 8191,
            "output_per_sec": 0,
            "queue_depth": 1,
            "reads_per_sec": 0,
            "san_usec_per_write_op": 15,
            "usec_per_read_op": 0,
            "usec_per_write_op": 642,
            "writes_per_sec": 2
        },
        "pgroups": {
            "consisgroup-07b6b983-986e-46f5-bdc3-deaa3dbb299e-cinder": {
                "hgroups": null,
                "hosts": null,
                "source": "host1",
                "targets": null,
                "volumes": [
                    "volume-1"
                ]
            }
        },
        "pods": {
            "srm-pod": {
                "arrays": [
                    {
                        "array_id": "52595f7e-b460-4b46-8851-a5defd2ac192",
                        "mediator_status": "online",
                        "name": "sn1-405-c09-37",
                        "status": "online"
                    },
                    {
                        "array_id": "a2c32301-f8a0-4382-949b-e69b552ce8ca",
                        "mediator_status": "online",
                        "name": "sn1-420-c11-31",
                        "status": "online"
                    }
                ],
                "source": null
            }
        },
        "snapshots": {
            "consisgroup.cgsnapshot": {
                "created": "2018-03-28T09:34:02Z",
                "size": 13958643712,
                "source": "volume-1"
            }
        },
        "subnet": {},
        "vgroups": {
            "vvol--vSphere-HA-0ffc7dd1-vg": {
                "volumes": [
                    "vvol--vSphere-HA-0ffc7dd1-vg/Config-aad5d7c6"
                ]
            }
        },
        "volumes": {
            "ansible_data": {
                "bandwidth": null,
                "hosts": [
                    [
                        "host1",
                        1
                    ]
                ],
                "serial": "43BE47C12334399B000114A6",
                "size": 1099511627776,
                "source": null
            }
        }
    }
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


ADMIN_API_VERSION = '1.14'
S3_REQUIRED_API_VERSION = '1.16'
LATENCY_REQUIRED_API_VERSION = '1.16'
AC_REQUIRED_API_VERSION = '1.14'
CAP_REQUIRED_API_VERSION = '1.6'
SAN_REQUIRED_API_VERSION = '1.10'
NVME_API_VERSION = '1.16'
PREFERRED_API_VERSION = '1.15'
CONN_STATUS_API_VERSION = '1.17'


def generate_default_dict(array):
    default_facts = {}
    defaults = array.get()
    api_version = array._list_available_rest_versions()
    if AC_REQUIRED_API_VERSION in api_version:
        default_facts['volume_groups'] = len(array.list_vgroups())
        default_facts['connected_arrays'] = len(array.list_array_connections())
        default_facts['pods'] = len(array.list_pods())
        default_facts['connection_key'] = array.get(connection_key=True)['connection_key']
    hosts = array.list_hosts()
    admins = array.list_admins()
    snaps = array.list_volumes(snap=True, pending=True)
    pgroups = array.list_pgroups(pending=True)
    hgroups = array.list_hgroups()
    # Old FA arrays only report model from the primary controller
    ct0_model = array.get_hardware('CT0')['model']
    if ct0_model:
        model = ct0_model
    else:
        ct1_model = array.get_hardware('CT1')['model']
        model = ct1_model
    default_facts['array_model'] = model
    default_facts['array_name'] = defaults['array_name']
    default_facts['purity_version'] = defaults['version']
    default_facts['hosts'] = len(hosts)
    default_facts['snapshots'] = len(snaps)
    default_facts['protection_groups'] = len(pgroups)
    default_facts['hostgroups'] = len(hgroups)
    default_facts['admins'] = len(admins)
    return default_facts


def generate_perf_dict(array):
    perf_facts = {}
    api_version = array._list_available_rest_versions()
    if LATENCY_REQUIRED_API_VERSION in api_version:
        latency_info = array.get(action='monitor', latency=True)[0]
    perf_info = array.get(action='monitor')[0]
    #  IOPS
    perf_facts['writes_per_sec'] = perf_info['writes_per_sec']
    perf_facts['reads_per_sec'] = perf_info['reads_per_sec']

    #  Bandwidth
    perf_facts['input_per_sec'] = perf_info['input_per_sec']
    perf_facts['output_per_sec'] = perf_info['output_per_sec']

    #  Latency
    if LATENCY_REQUIRED_API_VERSION in api_version:
        perf_facts['san_usec_per_read_op'] = latency_info['san_usec_per_read_op']
        perf_facts['san_usec_per_write_op'] = latency_info['san_usec_per_write_op']
        perf_facts['queue_usec_per_read_op'] = latency_info['queue_usec_per_read_op']
        perf_facts['queue_usec_per_write_op'] = latency_info['queue_usec_per_write_op']
        perf_facts['qos_rate_limit_usec_per_read_op'] = latency_info['qos_rate_limit_usec_per_read_op']
        perf_facts['qos_rate_limit_usec_per_write_op'] = latency_info['qos_rate_limit_usec_per_write_op']
        perf_facts['local_queue_usec_per_op'] = perf_info['local_queue_usec_per_op']
    perf_facts['usec_per_read_op'] = perf_info['usec_per_read_op']
    perf_facts['usec_per_write_op'] = perf_info['usec_per_write_op']
    perf_facts['queue_depth'] = perf_info['queue_depth']
    return perf_facts


def generate_config_dict(array):
    config_facts = {}
    api_version = array._list_available_rest_versions()
    # DNS
    config_facts['dns'] = array.get_dns()
    # SMTP
    config_facts['smtp'] = array.list_alert_recipients()
    # SNMP
    config_facts['snmp'] = array.list_snmp_managers()
    config_facts['snmp_v3_engine_id'] = array.get_snmp_engine_id()['engine_id']
    # DS
    config_facts['directory_service'] = array.get_directory_service()
    if S3_REQUIRED_API_VERSION in api_version:
        config_facts['directory_service_roles'] = {}
        roles = array.list_directory_service_roles()
        for role in range(0, len(roles)):
            role_name = roles[role]['name']
            config_facts['directory_service_roles'][role_name] = {
                'group': roles[role]['group'],
                'group_base': roles[role]['group_base'],
            }
    else:
        config_facts['directory_service'].update(array.get_directory_service(groups=True))
    # NTP
    config_facts['ntp'] = array.get(ntpserver=True)['ntpserver']
    # SYSLOG
    config_facts['syslog'] = array.get(syslogserver=True)['syslogserver']
    # Phonehome
    config_facts['phonehome'] = array.get(phonehome=True)['phonehome']
    # Proxy
    config_facts['proxy'] = array.get(proxy=True)['proxy']
    # Relay Host
    config_facts['relayhost'] = array.get(relayhost=True)['relayhost']
    # Sender Domain
    config_facts['senderdomain'] = array.get(senderdomain=True)['senderdomain']
    # SYSLOG
    config_facts['syslog'] = array.get(syslogserver=True)['syslogserver']
    # Idle Timeout
    config_facts['idle_timeout'] = array.get(idle_timeout=True)['idle_timeout']
    # SCSI Timeout
    config_facts['scsi_timeout'] = array.get(scsi_timeout=True)['scsi_timeout']
    # SSL
    config_facts['ssl_certs'] = array.get_certificate()
    # Global Admin settings
    if S3_REQUIRED_API_VERSION in api_version:
        config_facts['global_admin'] = array.get_global_admin_attributes()
    return config_facts


def generate_admin_dict(array):
    api_version = array._list_available_rest_versions()
    admin_facts = {}
    if ADMIN_API_VERSION in api_version:
        admins = array.list_admins()
        for admin in range(0, len(admins)):
            admin_name = admins[admin]['name']
            admin_facts[admin_name] = {
                'type': admins[admin]['type'],
                'role': admins[admin]['role'],
            }
    return admin_facts


def generate_subnet_dict(array):
    sub_facts = {}
    subnets = array.list_subnets()
    for sub in range(0, len(subnets)):
        sub_name = subnets[sub]['name']
        if subnets[sub]['enabled']:
            sub_facts[sub_name] = {
                'gateway': subnets[sub]['gateway'],
                'mtu': subnets[sub]['mtu'],
                'vlan': subnets[sub]['vlan'],
                'prefix': subnets[sub]['prefix'],
                'interfaces': subnets[sub]['interfaces'],
                'services': subnets[sub]['services'],
            }
    return sub_facts


def generate_network_dict(array):
    net_facts = {}
    ports = array.list_network_interfaces()
    for port in range(0, len(ports)):
        int_name = ports[port]['name']
        net_facts[int_name] = {
            'hwaddr': ports[port]['hwaddr'],
            'mtu': ports[port]['mtu'],
            'enabled': ports[port]['enabled'],
            'speed': ports[port]['speed'],
            'address': ports[port]['address'],
            'slaves': ports[port]['slaves'],
            'services': ports[port]['services'],
            'gateway': ports[port]['gateway'],
            'netmask': ports[port]['netmask'],
        }
        if ports[port]['subnet']:
            subnets = array.get_subnet(ports[port]['subnet'])
            if subnets['enabled']:
                net_facts[int_name]['subnet'] = {
                    'name': subnets['name'],
                    'prefix': subnets['prefix'],
                    'vlan': subnets['vlan'],
                }
    return net_facts


def generate_capacity_dict(array):
    capacity_facts = {}
    api_version = array._list_available_rest_versions()
    if CAP_REQUIRED_API_VERSION in api_version:
        volumes = array.list_volumes(pending=True)
        capacity_facts['provisioned_space'] = sum(item['size'] for item in volumes)
        capacity = array.get(space=True)
        total_capacity = capacity[0]['capacity']
        used_space = capacity[0]["total"]
        capacity_facts['free_space'] = total_capacity - used_space
        capacity_facts['total_capacity'] = total_capacity
        capacity_facts['data_reduction'] = capacity[0]['data_reduction']
        capacity_facts['system_space'] = capacity[0]['system']
        capacity_facts['volume_space'] = capacity[0]['volumes']
        capacity_facts['shared_space'] = capacity[0]['shared_space']
        capacity_facts['snapshot_space'] = capacity[0]['snapshots']
        capacity_facts['thin_provisioning'] = capacity[0]['thin_provisioning']
        capacity_facts['total_reduction'] = capacity[0]['total_reduction']

    return capacity_facts


def generate_snap_dict(array):
    snap_facts = {}
    snaps = array.list_volumes(snap=True)
    for snap in range(0, len(snaps)):
        snapshot = snaps[snap]['name']
        snap_facts[snapshot] = {
            'size': snaps[snap]['size'],
            'source': snaps[snap]['source'],
            'created': snaps[snap]['created'],
        }
    return snap_facts


def generate_vol_dict(array):
    volume_facts = {}
    vols = array.list_volumes()
    for vol in range(0, len(vols)):
        volume = vols[vol]['name']
        volume_facts[volume] = {
            'source': vols[vol]['source'],
            'size': vols[vol]['size'],
            'serial': vols[vol]['serial'],
            'hosts': [],
            'bandwidth': ""
        }
    api_version = array._list_available_rest_versions()
    if AC_REQUIRED_API_VERSION in api_version:
        qvols = array.list_volumes(qos=True)
        for qvol in range(0, len(qvols)):
            volume = qvols[qvol]['name']
            qos = qvols[qvol]['bandwidth_limit']
            volume_facts[volume]['bandwidth'] = qos
        vvols = array.list_volumes(protocol_endpoint=True)
        for vvol in range(0, len(vvols)):
            volume = vvols[vvol]['name']
            volume_facts[volume] = {
                'source': vvols[vvol]['source'],
                'serial': vvols[vvol]['serial'],
                'hosts': []
            }
    cvols = array.list_volumes(connect=True)
    for cvol in range(0, len(cvols)):
        volume = cvols[cvol]['name']
        voldict = [cvols[cvol]['host'], cvols[cvol]['lun']]
        volume_facts[volume]['hosts'].append(voldict)
    return volume_facts


def generate_host_dict(array):
    api_version = array._list_available_rest_versions()
    host_facts = {}
    hosts = array.list_hosts()
    for host in range(0, len(hosts)):
        hostname = hosts[host]['name']
        tports = []
        host_all_info = array.get_host(hostname, all=True)
        if host_all_info:
            tports = host_all_info[0]['target_port']
        host_facts[hostname] = {
            'hgroup': hosts[host]['hgroup'],
            'iqn': hosts[host]['iqn'],
            'wwn': hosts[host]['wwn'],
            'personality': array.get_host(hostname,
                                          personality=True)['personality'],
            'target_port': tports
        }
        if NVME_API_VERSION in api_version:
            host_facts[hostname]['nqn'] = hosts[host]['nqn']
    if PREFERRED_API_VERSION in api_version:
        hosts = array.list_hosts(preferred_array=True)
        for host in range(0, len(hosts)):
            hostname = hosts[host]['name']
            host_facts[hostname]['preferred_array'] = hosts[host]['preferred_array']
    return host_facts


def generate_pgroups_dict(array):
    pgroups_facts = {}
    pgroups = array.list_pgroups()
    for pgroup in range(0, len(pgroups)):
        protgroup = pgroups[pgroup]['name']
        pgroups_facts[protgroup] = {
            'hgroups': pgroups[pgroup]['hgroups'],
            'hosts': pgroups[pgroup]['hosts'],
            'source': pgroups[pgroup]['source'],
            'targets': pgroups[pgroup]['targets'],
            'volumes': pgroups[pgroup]['volumes'],
        }
        prot_sched = array.get_pgroup(protgroup, schedule=True)
        prot_reten = array.get_pgroup(protgroup, retention=True)
        if prot_sched['snap_enabled'] or prot_sched['replicate_enabled']:
            pgroups_facts[protgroup]['snap_freqyency'] = prot_sched['snap_frequency']
            pgroups_facts[protgroup]['replicate_freqyency'] = prot_sched['replicate_frequency']
            pgroups_facts[protgroup]['snap_enabled'] = prot_sched['snap_enabled']
            pgroups_facts[protgroup]['replicate_enabled'] = prot_sched['replicate_enabled']
            pgroups_facts[protgroup]['snap_at'] = prot_sched['snap_at']
            pgroups_facts[protgroup]['replicate_at'] = prot_sched['replicate_at']
            pgroups_facts[protgroup]['replicate_blackout'] = prot_sched['replicate_blackout']
            pgroups_facts[protgroup]['per_day'] = prot_reten['per_day']
            pgroups_facts[protgroup]['target_per_day'] = prot_reten['target_per_day']
            pgroups_facts[protgroup]['target_days'] = prot_reten['target_days']
            pgroups_facts[protgroup]['days'] = prot_reten['days']
            pgroups_facts[protgroup]['all_for'] = prot_reten['all_for']
            pgroups_facts[protgroup]['target_all_for'] = prot_reten['target_all_for']
        if ":" in protgroup:
            snap_transfers = array.get_pgroup(protgroup, snap=True, transfer=True)
            pgroups_facts[protgroup]['snaps'] = {}
            for snap_transfer in range(0, len(snap_transfers)):
                snap = snap_transfers[snap_transfer]['name']
                pgroups_facts[protgroup]['snaps'][snap] = {
                    'created': snap_transfers[snap_transfer]['created'],
                    'started': snap_transfers[snap_transfer]['started'],
                    'completed': snap_transfers[snap_transfer]['completed'],
                    'physical_bytes_written': snap_transfers[snap_transfer]['physical_bytes_written'],
                    'data_transferred': snap_transfers[snap_transfer]['data_transferred'],
                    'progress': snap_transfers[snap_transfer]['progress'],
                }
    return pgroups_facts


def generate_pods_dict(array):
    pods_facts = {}
    api_version = array._list_available_rest_versions()
    if AC_REQUIRED_API_VERSION in api_version:
        pods = array.list_pods()
        for pod in range(0, len(pods)):
            acpod = pods[pod]['name']
            pods_facts[acpod] = {
                'source': pods[pod]['source'],
                'arrays': pods[pod]['arrays'],
            }
    return pods_facts


def generate_conn_array_dict(array):
    conn_array_facts = {}
    api_version = array._list_available_rest_versions()
    if CONN_STATUS_API_VERSION in api_version:
        carrays = array.list_connected_arrays()
        for carray in range(0, len(carrays)):
            arrayname = carrays[carray]['array_name']
            conn_array_facts[arrayname] = {
                'array_id': carrays[carray]['id'],
                'throtled': carrays[carray]['throtled'],
                'version': carrays[carray]['version'],
                'type': carrays[carray]['type'],
                'mgmt_ip': carrays[carray]['management_address'],
                'repl_ip': carrays[carray]['replication_address'],
            }
            if CONN_STATUS_API_VERSION in api_version:
                conn_array_facts[arrayname]['status'] = carrays[carray]['status']
    return conn_array_facts


def generate_apps_dict(array):
    apps_facts = {}
    api_version = array._list_available_rest_versions()
    if SAN_REQUIRED_API_VERSION in api_version:
        apps = array.list_apps()
        for app in range(0, len(apps)):
            appname = apps[app]['name']
            apps_facts[appname] = {
                'version': apps[app]['version'],
                'status': apps[app]['status'],
                'description': apps[app]['description'],
            }
    return apps_facts


def generate_vgroups_dict(array):
    vgroups_facts = {}
    api_version = array._list_available_rest_versions()
    if AC_REQUIRED_API_VERSION in api_version:
        vgroups = array.list_vgroups()
        for vgroup in range(0, len(vgroups)):
            virtgroup = vgroups[vgroup]['name']
            vgroups_facts[virtgroup] = {
                'volumes': vgroups[vgroup]['volumes'],
            }
    return vgroups_facts


def generate_nfs_offload_dict(array):
    offload_facts = {}
    api_version = array._list_available_rest_versions()
    if AC_REQUIRED_API_VERSION in api_version:
        offload = array.list_nfs_offload()
        for target in range(0, len(offload)):
            offloadt = offload[target]['name']
            offload_facts[offloadt] = {
                'status': offload[target]['status'],
                'mount_point': offload[target]['mount_point'],
                'protocol': offload[target]['protocol'],
                'mount_options': offload[target]['mount_options'],
                'address': offload[target]['address'],
            }
    return offload_facts


def generate_s3_offload_dict(array):
    offload_facts = {}
    api_version = array._list_available_rest_versions()
    if S3_REQUIRED_API_VERSION in api_version:
        offload = array.list_s3_offload()
        for target in range(0, len(offload)):
            offloadt = offload[target]['name']
            offload_facts[offloadt] = {
                'status': offload[target]['status'],
                'bucket': offload[target]['bucket'],
                'protocol': offload[target]['protocol'],
                'access_key_id': offload[target]['access_key_id'],
            }
    return offload_facts


def generate_hgroups_dict(array):
    hgroups_facts = {}
    hgroups = array.list_hgroups()
    for hgroup in range(0, len(hgroups)):
        hostgroup = hgroups[hgroup]['name']
        hgroups_facts[hostgroup] = {
            'hosts': hgroups[hgroup]['hosts'],
            'pgs': [],
            'vols': [],
        }
    pghgroups = array.list_hgroups(protect=True)
    for pghg in range(0, len(pghgroups)):
        pgname = pghgroups[pghg]['name']
        hgroups_facts[pgname]['pgs'].append(pghgroups[pghg]['protection_group'])
    volhgroups = array.list_hgroups(connect=True)
    for pgvol in range(0, len(volhgroups)):
        pgname = volhgroups[pgvol]['name']
        volpgdict = [volhgroups[pgvol]['vol'], volhgroups[pgvol]['lun']]
        hgroups_facts[pgname]['vols'].append(volpgdict)
    return hgroups_facts


def generate_interfaces_dict(array):
    api_version = array._list_available_rest_versions()
    int_facts = {}
    ports = array.list_ports()
    for port in range(0, len(ports)):
        int_name = ports[port]['name']
        if ports[port]['wwn']:
            int_facts[int_name] = ports[port]['wwn']
        if ports[port]['iqn']:
            int_facts[int_name] = ports[port]['iqn']
        if NVME_API_VERSION in api_version:
            if ports[port]['nqn']:
                int_facts[int_name] = ports[port]['nqn']
    return int_facts


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        gather_subset=dict(default='minimum', type='list',)
    ))

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    array = get_system(module)

    subset = [test.lower() for test in module.params['gather_subset']]
    valid_subsets = ('all', 'minimum', 'config', 'performance', 'capacity',
                     'network', 'subnet', 'interfaces', 'hgroups', 'pgroups',
                     'hosts', 'admins', 'volumes', 'snapshots', 'pods',
                     'vgroups', 'offload', 'apps', 'arrays')
    subset_test = (test in valid_subsets for test in subset)
    if not all(subset_test):
        module.fail_json(msg="value must gather_subset must be one or more of: %s, got: %s"
                         % (",".join(valid_subsets), ",".join(subset)))

    facts = {}

    if 'minimum' in subset or 'all' in subset:
        facts['default'] = generate_default_dict(array)
    if 'performance' in subset or 'all' in subset:
        facts['performance'] = generate_perf_dict(array)
    if 'config' in subset or 'all' in subset:
        facts['config'] = generate_config_dict(array)
    if 'capacity' in subset or 'all' in subset:
        facts['capacity'] = generate_capacity_dict(array)
    if 'network' in subset or 'all' in subset:
        facts['network'] = generate_network_dict(array)
    if 'subnet' in subset or 'all' in subset:
        facts['subnet'] = generate_subnet_dict(array)
    if 'interfaces' in subset or 'all' in subset:
        facts['interfaces'] = generate_interfaces_dict(array)
    if 'hosts' in subset or 'all' in subset:
        facts['hosts'] = generate_host_dict(array)
    if 'volumes' in subset or 'all' in subset:
        facts['volumes'] = generate_vol_dict(array)
    if 'snapshots' in subset or 'all' in subset:
        facts['snapshots'] = generate_snap_dict(array)
    if 'hgroups' in subset or 'all' in subset:
        facts['hgroups'] = generate_hgroups_dict(array)
    if 'pgroups' in subset or 'all' in subset:
        facts['pgroups'] = generate_pgroups_dict(array)
    if 'pods' in subset or 'all' in subset:
        facts['pods'] = generate_pods_dict(array)
    if 'admins' in subset or 'all' in subset:
        facts['admins'] = generate_admin_dict(array)
    if 'vgroups' in subset or 'all' in subset:
        facts['vgroups'] = generate_vgroups_dict(array)
    if 'offload' in subset or 'all' in subset:
        facts['nfs_offload'] = generate_nfs_offload_dict(array)
        facts['s3_offload'] = generate_s3_offload_dict(array)
    if 'apps' in subset or 'all' in subset:
        facts['apps'] = generate_apps_dict(array)
    if 'arrays' in subset or 'all' in subset:
        facts['arrays'] = generate_conn_array_dict(array)

    module.exit_json(ansible_facts={'ansible_purefa_facts': facts})


if __name__ == '__main__':
    main()
