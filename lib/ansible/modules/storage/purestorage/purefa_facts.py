#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_facts
version_added: '2.6'
short_description: Collect facts from Pure Storage FlashArray
description:
  - Collect facts information from a Pure Storage Flasharray running the
    Purity//FA operating system. By default, the module will collect basic
    fact information including hosts, host groups, protection
    groups and volume counts. Additional fact information can be collected
    based on the configured set of arguements.
author:
  - Simon Dodsley (@sdodsley)
options:
  gather_subset:
    description:
      - When supplied, this argument will define the facts to be collected.
        Possible values for this include all, minimum, config, performance,
        capacity, network, subnet, interfaces, hgroups, pgroups, hosts,
        volumes and snapshots.
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
  contains:
        "capacity": {}
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
        }
        "default": {
            "array_name": "flasharray1",
            "hostgroups": 0,
            "hosts": 10,
            "protection_groups": 1,
            "purity_version": "5.0.4",
            "snapshots": 1
        }
        "hgroups": {}
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
        }
        "interfaces": {
            "CT0.ETH4": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682",
            "CT0.ETH5": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682",
            "CT1.ETH4": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682",
            "CT1.ETH5": "iqn.2010-06.com.purestorage:flasharray.2111b767484e4682"
        }
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
        }
        "performance": {
            "input_per_sec": 8191,
            "output_per_sec": 0,
            "queue_depth": 1,
            "reads_per_sec": 0,
            "san_usec_per_write_op": 15,
            "usec_per_read_op": 0,
            "usec_per_write_op": 642,
            "writes_per_sec": 2
        }
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
        }
        "snapshots": {
            "consisgroup.cgsnapshot": {
                "created": "2018-03-28T09:34:02Z",
                "size": 13958643712,
                "source": "volume-1"
            }
        }
        "subnet": {}
        "volumes": {
            "ansible_data": {
                "hosts": [
                    [
                        "host1",
                        1
                    ]
                ],
                "serial": "43BE47C12334399B000114A6",
                "size": 1099511627776
            }
        }
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


AC_REQUIRED_API_VERSION = '1.14'
CAP_REQUIRED_API_VERSION = '1.6'
SAN_REQUIRED_API_VERSION = '1.10'


def generate_default_dict(array):
    default_facts = {}
    defaults = array.get()
    api_version = array._list_available_rest_versions()
    if AC_REQUIRED_API_VERSION in api_version:
        pods = array.get_pods()
        default_facts['pods'] = len(pods)
    hosts = array.list_hosts()
    snaps = array.list_volumes(snap=True, pending=True)
    pgroups = array.list_pgroups(pending=True)
    hgroups = array.list_hgroups()
    default_facts['array_name'] = defaults['array_name']
    default_facts['purity_version'] = defaults['version']
    default_facts['hosts'] = len(hosts)
    default_facts['snapshots'] = len(snaps)
    default_facts['protection_groups'] = len(pgroups)
    default_facts['hostgroups'] = len(hgroups)
    return default_facts


def generate_perf_dict(array):
    perf_facts = {}
    perf_info = array.get(action='monitor')[0]
    #  IOPS
    perf_facts['writes_per_sec'] = perf_info['writes_per_sec']
    perf_facts['reads_per_sec'] = perf_info['reads_per_sec']

    #  Bandwidth
    perf_facts['input_per_sec'] = perf_info['input_per_sec']
    perf_facts['output_per_sec'] = perf_info['output_per_sec']

    #  Latency
    api_version = array._list_available_rest_versions()
    if SAN_REQUIRED_API_VERSION in api_version:
        perf_facts['san_usec_per_read_op'] = perf_info['san_usec_per_read_op']
        perf_facts['san_usec_per_write_op'] = perf_info['san_usec_per_write_op']
    perf_facts['usec_per_read_op'] = perf_info['usec_per_read_op']
    perf_facts['usec_per_write_op'] = perf_info['usec_per_write_op']
    perf_facts['queue_depth'] = perf_info['queue_depth']
    return perf_facts


def generate_config_dict(array):
    config_facts = {}
    # DNS
    config_facts['dns'] = array.get_dns()
    # SMTP
    config_facts['smtp'] = array.list_alert_recipients()
    # SMNP
    config_facts['snmp'] = array.list_snmp_managers()
    # DS
    config_facts['directory_service'] = array.get_directory_service()
    config_facts['directory_service'].update(array.get_directory_service(groups=True))
    # NTP
    config_facts['ntp'] = array.get(ntpserver=True)['ntpserver']
    # SYSLOG
    config_facts['syslog'] = array.get(syslogserver=True)['syslogserver']
    # SSL
    config_facts['ssl_certs'] = array.get_certificate()
    return config_facts


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
        if ports[port]['enabled']:
            net_facts[int_name] = {
                'hwaddr': ports[port]['hwaddr'],
                'mtu': ports[port]['mtu'],
                'speed': ports[port]['speed'],
                'address': ports[port]['address'],
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
            'size': vols[vol]['size'],
            'serial': vols[vol]['serial'],
            'hosts': []
        }
    cvols = array.list_volumes(connect=True)
    for cvol in range(0, len(cvols)):
        volume = cvols[cvol]['name']
        voldict = [cvols[cvol]['host'], cvols[cvol]['lun']]
        volume_facts[volume]['hosts'].append(voldict)
    return volume_facts


def generate_host_dict(array):
    host_facts = {}
    hosts = array.list_hosts()
    for host in range(0, len(hosts)):
        hostname = hosts[host]['name']
        host_facts[hostname] = {
            'hgroup': hosts[host]['hgroup'],
            'iqn': hosts[host]['iqn'],
            'wwn': hosts[host]['wwn'],
        }
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
    return pgroups_facts


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
    int_facts = {}
    ports = array.list_ports()
    for port in range(0, len(ports)):
        int_name = ports[port]['name']
        if ports[port]['wwn']:
            int_facts[int_name] = ports[port]['wwn']
        if ports[port]['iqn']:
            int_facts[int_name] = ports[port]['iqn']
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
                     'hosts', 'volumes', 'snapshots')
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

    result = dict(ansible_purefa_facts=facts,)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
