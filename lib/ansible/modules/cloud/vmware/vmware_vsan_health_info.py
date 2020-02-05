#!/usr/bin/python

# Copyright: (c) 2019, OVH SAS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_vsan_health_info

short_description: Gather information about a VMware vSAN cluster's health

version_added: "2.10"

description:
    - "Gather information about a VMware vSAN cluster's health"

options:
    cluster_name:
        description:
            - Name of the vSAN cluster.
        required: true
        type: str
    fetch_from_cache:
        description:
            - C(True) to return the result from cache directly instead of running the full health check.
        required: false
        default: false
        type: bool

requirements:
    - PyVmomi
    - VMware vSAN Python's SDK

extends_documentation_fragment:
    - vmware.documentation

author:
    - Erwan Quelin (@equelin)
'''

EXAMPLES = '''
- name: Gather health info from a vSAN's cluster
  hosts: localhost
  gather_facts: 'no'
  vmware_vsan_health_info:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    cluster_name: 'vSAN01'
    fetch_from_cache: False
'''

RETURN = '''
vsan_health_info:
    description: vSAN cluster health info
    returned: on success
    type: dict
    sample: {
        "_vimtype": "vim.cluster.VsanClusterHealthSummary",
        "burnInTest": null,
        "clusterStatus": {
            "_vimtype": "vim.cluster.VsanClusterHealthSystemStatusResult",
            "goalState": "installed",
            "status": "green",
            "trackedHostsStatus": [
                {
                    "_vimtype": "vim.host.VsanHostHealthSystemStatusResult",
                    "hostname": "esxi01.example.com",
                    "issues": [],
                    "status": "green"
                },
                {
                    "_vimtype": "vim.host.VsanHostHealthSystemStatusResult",
                    "hostname": "esxi04.example.com",
                    "issues": [],
                    "status": "green"
                },
                {
                    "_vimtype": "vim.host.VsanHostHealthSystemStatusResult",
                    "hostname": "esxi02.example.com",
                    "issues": [],
                    "status": "green"
                },
                {
                    "_vimtype": "vim.host.VsanHostHealthSystemStatusResult",
                    "hostname": "esxi03.example.com",
                    "issues": [],
                    "status": "green"
                }
            ],
            "untrackedHosts": []
        }
    }
'''

import json
import traceback

try:
    from pyVmomi import vim, vmodl, VmomiSupport
    HAS_PYVMOMI = True
    HAS_PYVMOMIJSON = hasattr(VmomiSupport, 'VmomiJSONEncoder')
except ImportError:
    PYVMOMI_IMP_ERR = traceback.format_exc()
    HAS_PYVMOMI = False
    HAS_PYVMOMIJSON = False

try:
    import vsanapiutils
    import vsanmgmtObjects
    HAS_VSANPYTHONSDK = True
except ImportError:
    VSANPYTHONSDK_IMP_ERR = traceback.format_exc()
    HAS_VSANPYTHONSDK = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.vmware import connect_to_api, vmware_argument_spec, find_cluster_by_name


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(required=True, type='str'),
        fetch_from_cache=dict(required=False, type='bool')
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg=missing_required_lib('PyVmomi'), exception=PYVMOMI_IMP_ERR)

    if not HAS_VSANPYTHONSDK:
        module.fail_json(msg=missing_required_lib('vSAN Management SDK for Python'), exception=VSANPYTHONSDK_IMP_ERR)

    if not HAS_PYVMOMIJSON:
        module.fail_json(msg='The installed version of pyvmomi lacks JSON output support; need pyvmomi>6.7.1')

    try:
        si, content = connect_to_api(module, True, True)
    except Exception as e:
        module.fail_json(msg=e.msg)

    client_stub = si._GetStub()
    ssl_context = client_stub.schemeArgs.get('context')

    cluster = find_cluster_by_name(content, module.params['cluster_name'])

    if not cluster:
        module.fail_json(msg="Failed to find cluster %s" % module.params['cluster_name'])

    apiVersion = vsanapiutils.GetLatestVmodlVersion(module.params['hostname'])
    vcMos = vsanapiutils.GetVsanVcMos(client_stub, context=ssl_context, version=apiVersion)

    vsanClusterHealthSystem = vcMos['vsan-cluster-health-system']

    try:
        clusterHealth = vsanClusterHealthSystem.VsanQueryVcClusterHealthSummary(
            cluster=cluster,
            fetchFromCache=module.params['fetch_from_cache']
        )
    except vmodl.fault.NotFound as not_found:
        module.fail_json(msg=not_found.msg)
    except vmodl.fault.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)

    health = json.dumps(clusterHealth, cls=VmomiSupport.VmomiJSONEncoder, sort_keys=True, strip_dynamic=True)

    module.exit_json(changed=False, vsan_health_info=health)


if __name__ == '__main__':
    main()
