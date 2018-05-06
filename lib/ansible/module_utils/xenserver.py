# -*- coding: utf-8 -*-

# (c) 2018, Bojan Vitnik <bvitnik@mainstream.rs>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import atexit
import time

HAS_XENAPI = False
try:
    import XenAPI
    HAS_XENAPI = True
except ImportError:
    pass

from ansible.module_utils._text import to_text
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six import integer_types, iteritems, string_types
from ansible.module_utils.basic import env_fallback

def xenserver_common_argument_spec():
    return dict(
        hostname=dict(type='str',
                      required=False,
                      default='localhost',
                      fallback=(env_fallback, ['XENSERVER_HOST']),
                      ),
        username=dict(type='str',
                      aliases=['user', 'admin'],
                      required=False,
                      default='root',
                      fallback=(env_fallback, ['XENSERVER_USER'])),
        password=dict(type='str',
                      aliases=['pass', 'pwd'],
                      required=False,
                      no_log=True,
                      fallback=(env_fallback, ['XENSERVER_PASSWORD'])),
        validate_certs=dict(type='bool',
                            required=False,
                            default=True,
                            fallback=(env_fallback, ['XENSERVER_VALIDATE_CERTS'])),
    )

def gather_vm_params(module, vm_ref):
    # We silently return empty vm_params if bad vm_ref was supplied.
    if not vm_ref or vm_ref == "OpaqueRef:NULL":
        return {}

    xapi_session = XAPI.connect(module)

    try:
        vm_params = xapi_session.xenapi.VM.get_record(vm_ref)

        # We need some params like affinity, VBDs, VIFs, VDIs etc. dereferenced.

        # Affinity.
        if vm_params['affinity'] != "OpaqueRef:NULL":
            vm_affinity = xapi_session.xenapi.host.get_record(vm_params['affinity'])
            vm_params['affinity'] = vm_affinity
        else:
            vm_params['affinity'] = {}

        # VBDs.
        vm_vbd_params_list = [ xapi_session.xenapi.VBD.get_record(vm_vbd_ref) for vm_vbd_ref in vm_params['VBDs'] ]

        # List of VBDs is usually sorted by userdevice but we sort just
        # in case. We need this list sorted by userdevice so that we can
        # make positional pairing with module.params['disks'].
        vm_vbd_params_list = sorted(vm_vbd_params_list, key=lambda vm_vbd_params: int(vm_vbd_params['userdevice']))
        vm_params['VBDs'] = vm_vbd_params_list

        # VDIs.
        for vm_vbd_params in vm_params['VBDs']:
            if vm_vbd_params['VDI'] != "OpaqueRef:NULL":
                vm_vdi_params = xapi_session.xenapi.VDI.get_record(vm_vbd_params['VDI'])
            else:
                vm_vdi_params = {}

            vm_vbd_params['VDI'] = vm_vdi_params

        # VIFs.
        vm_vif_params_list = [ xapi_session.xenapi.VIF.get_record(vm_vif_ref) for vm_vif_ref in vm_params['VIFs'] ]

        # List of VIFs is usually sorted by device but we sort just
        # in case. We need this list sorted by device so that we can
        # make positional pairing with module.params['networks'].
        vm_vif_params_list = sorted(vm_vif_params_list, key=lambda vm_vif_params: int(vm_vif_params['device']))
        vm_params['VIFs'] = vm_vif_params_list

        # Networks.
        for vm_vif_params in vm_params['VIFs']:
            if vm_vif_params['network'] != "OpaqueRef:NULL":
                vm_network_params = xapi_session.xenapi.network.get_record(vm_vif_params['network'])
            else:
                vm_network_params = {}

            vm_vif_params['network'] = vm_network_params

        # Guest metrics.
        if vm_params['guest_metrics'] != "OpaqueRef:NULL":
            vm_guest_metrics = xapi_session.xenapi.VM_guest_metrics.get_record(vm_params['guest_metrics'])
            vm_params['guest_metrics'] = vm_guest_metrics
        else:
            vm_params['guest_metrics'] = {}

    except XenAPI.Failure as f:
        module.fail_json(msg="XAPI ERROR: %s" % f.details)

    return vm_params

def gather_vm_facts(module, vm_params):
    # We silently return empty vm_facts if no vm_params are available.
    if not vm_params:
        return {}

    xapi_session = XAPI.connect(module)

    state_map = {
        "running": "poweredon",
        "halted": "poweredoff",
        "suspended": "suspended",
        "paused": "paused",
    }

    vm_facts = {
        "state": state_map[vm_params['power_state'].lower()],
        "name": vm_params['name_label'],
        "name_desc": vm_params['name_description'],
        "uuid": vm_params['uuid'],
        "is_template": vm_params['is_a_template'],
        "folder": vm_params['other_config'].get('folder', ''),
        "hardware": {
            "num_cpus": int(vm_params['VCPUs_max']),
            "num_cpu_cores_per_socket": int(vm_params['platform'].get('cores-per-socket', '1')),
            "memory_mb": int(vm_params['memory_dynamic_max'])/1048576,
        },
        "disks": [],
        "cdrom": {},
        "networks": [],
        "home_server": vm_params['affinity'].get('name_label', ''),
        "domid": vm_params['domid'],
        "platform": vm_params['platform'],
        "other_config": vm_params['other_config'],
        "xenstore_data": vm_params['xenstore_data'],
    }

    for vm_vbd_params in vm_params['VBDs']:
        if vm_vbd_params['type'] == "Disk":
            vm_disk_sr_params = xapi_session.xenapi.SR.get_record(vm_vbd_params['VDI']['SR'])

            vm_disk_params = {
                "size": int(vm_vbd_params['VDI']['virtual_size']),
                "name": vm_vbd_params['VDI']['name_label'],
                "name_desc": vm_vbd_params['VDI']['name_description'],
                "sr": vm_disk_sr_params['name_label'],
                "sr_uuid": vm_disk_sr_params['uuid'],
                "device": vm_vbd_params['device'],
                "userdevice": vm_vbd_params['userdevice'],
            }

            vm_facts['disks'].append(vm_disk_params)
        elif vm_vbd_params['type'] == "CD":
            if vm_vbd_params['empty']:
                vm_facts['cdrom'].update(type="none")
            else:
                vm_facts['cdrom'].update(type="iso")
                vm_facts['cdrom'].update(iso=vm_vbd_params['VDI']['name_label'])

    for vm_vif_params in vm_params['VIFs']:
        vm_guest_metrics_networks = vm_params['guest_metrics'].get('networks', {})

        vm_network_params = {
            "name": vm_vif_params['network']['name_label'],
            "mac": vm_vif_params['MAC'],
            "device": vm_vif_params['device'],
            "mtu": vm_vif_params['MTU'],
            "ip": vm_guest_metrics_networks.get("%s/ip" % vm_vif_params['device'], ''),
            "ipv6": vm_guest_metrics_networks.get("%s/ipv6/0" % vm_vif_params['device'], ''),
        }

        vm_facts['networks'].append(vm_network_params)

    return vm_facts

def wait_for_task(module, task_ref, timeout=300):
    xapi_session = XAPI.connect(module)

    interval = 1

    result = ""

    try:
        while timeout > 0:
            task_status = xapi_session.xenapi.task.get_status(task_ref).lower()

            if task_status == "pending":
                # Task is still running.
                time.sleep(interval)
                timeout -= interval
                continue
            elif task_status == "success":
                # Task is done.
                break
            else:
                # Task failed.
                result = task_status
                break
        else:
            # We timed out.
            result = "timeout"

        xapi_session.xenapi.task.destroy(task_ref)
    except XenAPI.Failure as f:
        module.fail_json(msg="XAPI ERROR: %s" % f.details)

    return result

class XAPI(object):
    _xapi_session = None

    @classmethod
    def connect(cls, module, disconnect_atexit=True):
        if cls._xapi_session is not None:
            return cls._xapi_session

        hostname = module.params['hostname']
        username = module.params['username']
        password = module.params['password']
        ignore_ssl = not module.params['validate_certs']

        if hostname == 'localhost':
            cls._xapi_session = XenAPI.xapi_local()
            username = ''
            password = ''
        else:
            cls._xapi_session = XenAPI.Session("http://%s/" % hostname, ignore_ssl=ignore_ssl)

            if not password:
                password = ''

        try:
            cls._xapi_session.login_with_password(username, password, '1.0', 'xenserver_guest.py')
        except XenAPI.Failure as f:
            module.fail_json(msg="Unable to log on to XenServer at %s as %s: %s" % (hostname, username, f.details))

        # Disabling atexit should be used in special cases only.
        if disconnect_atexit:
            atexit.register(cls._xapi_session.logout)
        return cls._xapi_session

class XenServerObject(object):
    def __init__(self, module):
        if not HAS_XENAPI:
            module.fail_json(changed=False, msg="XenAPI.py required for this module! Please download XenServer SDK and copy XenAPI.py to your site-packages.")

        if module:
            self.module = module
        else:
            module.fail_json(msg="XenServerObject: Invalid module object passed!")

        self.xapi_session = XAPI.connect(module)

        try:
            self.pool_ref = self.xapi_session.xenapi.pool.get_all()[0]
            self.default_sr_ref = self.xapi_session.xenapi.pool.get_default_SR(self.pool_ref)
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)
