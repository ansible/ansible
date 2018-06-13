# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

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
from ansible.module_utils.ansible_release import __version__ as ANSIBLE_VERSION


def xenserver_common_argument_spec():
    return dict(
        hostname=dict(type='str',
                      aliases=['host', 'pool'],
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


def translate_to_module_vm_power_state(vm_power_state):
    # Map VM power states to states as presented by a module.
    module_power_state_map = {
        "running": "poweredon",
        "halted": "poweredoff",
        "suspended": "suspended",
        "paused": "paused"
    }

    return module_power_state_map.get(vm_power_state)


def translate_to_vm_power_state(module_vm_power_state):
    # Map power states as presented by a module to VM power states.
    vm_power_state_map = {
        "poweredon": "running",
        "poweredoff": "halted",
        "restarted": "running",
        "suspended": "suspended",
        "shutdownguest": "halted",
        "rebootguest": "running",
    }

    return vm_power_state_map.get(module_vm_power_state)


def get_object_ref(module, name, uuid=None, obj_type="VM", fail=True, msg_prefix=""):
    xapi_session = XAPI.connect(module)

    if obj_type in ["template", "snapshot"]:
        real_obj_type = "VM"
    elif obj_type == "home server":
        real_obj_type = "host"
    elif obj_type == "ISO image":
        real_obj_type = "VDI"
    else:
        real_obj_type = obj_type

    obj_ref = None

    # UUID has precendence over name.
    if uuid:
        try:
            # Find object by UUID. If no object is found using given UUID,
            # an exception will be generated.
            obj_ref = xapi_session.xenapi_request("%s.get_by_uuid" % real_obj_type, (uuid,))
        except XenAPI.Failure as f:
            if fail:
                module.fail_json(msg="%s%s with UUID '%s' not found!" % (msg_prefix, obj_type, uuid))
    elif name:
        try:
            # Find object by name (name_label).
            obj_ref_list = xapi_session.xenapi_request("%s.get_by_name_label" % real_obj_type, (name,))
        except XenAPI.Failure as f:
            module.fail_json(msg="XAPI ERROR: %s" % f.details)

        # If obj_ref_list is empty.
        if not obj_ref_list:
            if fail:
                module.fail_json(msg="%s%s with name '%s' not found!" % (msg_prefix, obj_type, name))
        # If obj_ref_list contains multiple object references.
        elif len(obj_ref_list) > 1:
            module.fail_json(msg="%smultiple %ss with name '%s' found! Please use UUID." % (msg_prefix, obj_type, name))
        # The obj_ref_list contains only one object reference.
        else:
            obj_ref = obj_ref_list[0]
    else:
        module.fail_json(msg="%sno valid name or UUID supplied for %s!" % (msg_prefix, obj_type))

    return obj_ref


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
        vm_vbd_params_list = [xapi_session.xenapi.VBD.get_record(vm_vbd_ref) for vm_vbd_ref in vm_params['VBDs']]

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
        vm_vif_params_list = [xapi_session.xenapi.VIF.get_record(vm_vif_ref) for vm_vif_ref in vm_params['VIFs']]

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

    vm_facts = {
        "state": translate_to_module_vm_power_state(vm_params['power_state'].lower()),
        "name": vm_params['name_label'],
        "name_desc": vm_params['name_description'],
        "uuid": vm_params['uuid'],
        "is_template": vm_params['is_a_template'],
        "folder": vm_params['other_config'].get('folder', ''),
        "hardware": {
            "num_cpus": int(vm_params['VCPUs_max']),
            "num_cpu_cores_per_socket": int(vm_params['platform'].get('cores-per-socket', '1')),
            "memory_mb": int(int(vm_params['memory_dynamic_max']) / 1048576),
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
            "ip6": vm_guest_metrics_networks.get("%s/ipv6/0" % vm_vif_params['device'], ''),
        }

        vm_facts['networks'].append(vm_network_params)

    return vm_facts


def set_vm_power_state(module, vm_ref, power_state, timeout=300):
    # Fail if we don't have a valid VM reference.
    if not vm_ref or vm_ref == "OpaqueRef:NULL":
        module.fail_json(msg="Cannot set VM power state. Invalid VM reference supplied!")

    xapi_session = XAPI.connect(module)

    vm_power_state_resulting = translate_to_vm_power_state(power_state)

    state_changed = False

    try:
        # Get current state of the VM.
        vm_power_state_current = translate_to_module_vm_power_state(xapi_session.xenapi.VM.get_power_state(vm_ref).lower())

        if vm_power_state_current != power_state:
            if power_state == "poweredon":
                if not module.check_mode:
                    # VM can be in either halted, suspended, paused or running state.
                    # For VM to be in running state, start has to be called on halted,
                    # resume on suspended and unpause on paused VM.
                    if vm_power_state_current == "poweredoff":
                        xapi_session.xenapi.VM.start(vm_ref, False, False)
                    elif vm_power_state_current == "suspended":
                        xapi_session.xenapi.VM.resume(vm_ref, False, False)
                    elif vm_power_state_current == "paused":
                        xapi_session.xenapi.VM.unpause(vm_ref)
            elif power_state == "poweredoff":
                if not module.check_mode:
                    # hard_shutdown will halt VM regardless of current state.
                    xapi_session.xenapi.VM.hard_shutdown(vm_ref)
            elif power_state == "restarted":
                # hard_restart will restart VM only if VM is in paused or running state.
                if vm_power_state_current in ["paused", "poweredon"]:
                    if not module.check_mode:
                        xapi_session.xenapi.VM.hard_reboot(vm_ref)
                else:
                    module.fail_json(msg="Cannot restart VM in state '%s'!" % vm_power_state_current)
            elif power_state == "suspended":
                # running state is required for suspend.
                if vm_power_state_current == "poweredon":
                    if not module.check_mode:
                        xapi_session.xenapi.VM.suspend(vm_ref)
                else:
                    module.fail_json(msg="Cannot suspend VM in state '%s'!" % vm_power_state_current)
            elif power_state == "shutdownguest":
                # running state is required for guest shutdown.
                if vm_power_state_current == "poweredon":
                    if not module.check_mode:
                        if timeout == 0:
                            xapi_session.xenapi.VM.clean_shutdown(vm_ref)
                        else:
                            task_ref = xapi_session.xenapi.Async.VM.clean_shutdown(vm_ref)
                            task_result = wait_for_task(module, task_ref, timeout)

                            if task_result:
                                module.fail_json(msg="Guest shutdown task failed: '%s'!" % task_result)
                else:
                    module.fail_json(msg="Cannot shutdown guest when VM is in state '%s'." % vm_power_state_current)
            elif power_state == "rebootguest":
                # running state is required for guest reboot.
                if vm_power_state_current == "poweredon":
                    if not module.check_mode:
                        if timeout == 0:
                            xapi_session.xenapi.VM.clean_reboot(vm_ref)
                        else:
                            task_ref = xapi_session.xenapi.Async.VM.clean_reboot(vm_ref)
                            task_result = wait_for_task(module, task_ref, timeout)

                            if task_result:
                                module.fail_json(msg="Guest reboot task failed: '%s'!" % task_result)
                else:
                    module.fail_json(msg="Cannot reboot guest when VM is in state '%s'." % vm_power_state_current)
            else:
                module.fail_json(msg="Requested VM power state '%s' is unsupported!" % power_state)

            state_changed = True
    except XenAPI.Failure as f:
        module.fail_json(msg="XAPI ERROR: %s" % f.details)

    return (state_changed, vm_power_state_resulting)


def wait_for_task(module, task_ref, timeout=300):
    # Fail if we don't have a valid task reference.
    if not task_ref or task_ref == "OpaqueRef:NULL":
        module.fail_json(msg="Cannot wait for task. Invalid task reference supplied!")

    xapi_session = XAPI.connect(module)

    interval = 2

    result = ""

    # If we have to wait indefinitely, make timeout larger than 0 so we can
    # enter while loop.
    if timeout == 0:
        timeout = 1

    try:
        while timeout > 0:
            task_status = xapi_session.xenapi.task.get_status(task_ref).lower()

            if task_status == "pending":
                # Task is still running.
                time.sleep(interval)

                # We decrease timeout only if we don't wait indefinitely.
                if timeout != 0:
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


def wait_for_vm_ip_address(module, vm_ref, timeout=300):
    # Fail if we don't have a valid VM reference.
    if not vm_ref or vm_ref == "OpaqueRef:NULL":
        module.fail_json(msg="Cannot wait for VM IP address. Invalid VM reference supplied!")

    xapi_session = XAPI.connect(module)

    vm_guest_metrics = {}

    try:
        vm_power_state = translate_to_module_vm_power_state(xapi_session.xenapi.VM.get_power_state(vm_ref).lower())

        if vm_power_state != 'poweredon':
            module.fail_json(msg="Cannot wait for VM IP address when VM is in state '%s'." % vm_power_state)

        interval = 2

        # If we have to wait indefinitely, make time_left larger than 0 so we can
        # enter while loop.
        if timeout == 0:
            time_left = 1
        else:
            time_left = timeout

        while time_left > 0:
            vm_guest_metrics_ref = xapi_session.xenapi.VM.get_guest_metrics(vm_ref)

            if vm_guest_metrics_ref != "OpaqueRef:NULL":
                vm_guest_metrics = xapi_session.xenapi.VM_guest_metrics.get_record(vm_guest_metrics_ref)
                vm_ips = vm_guest_metrics['networks']

                if "0/ip" in vm_ips:
                    break

            time.sleep(interval)

            # We decrease time_left only if we don't wait indefinitely.
            if timeout != 0:
                time_left -= interval
        else:
            # We timed out.
            module.fail_json(msg="Timed out waiting for VM IP address!")

    except XenAPI.Failure as f:
        module.fail_json(msg="XAPI ERROR: %s" % f.details)

    return vm_guest_metrics


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
            # If scheme is not specified we default to http:// because https://
            # is problematic in most setups.
            if not hostname.startswith("http://") and not hostname.startswith("https://"):
                hostname = "http://%s" % hostname

            try:
                # ignore_ssl is supported in XenAPI.py 7.2 onward but there
                # is no way to tell which version we are using. TypeError will
                # be raised if ignore_ssl is not supported. Additionally,
                # ignore_ssl requires Python 2.7.9 or newer.
                cls._xapi_session = XenAPI.Session(hostname, ignore_ssl=ignore_ssl)
            except TypeError:
                # Try without ignore_ssl.
                cls._xapi_session = XenAPI.Session(hostname)

            if not password:
                password = ''

        try:
            cls._xapi_session.login_with_password(username, password, ANSIBLE_VERSION, 'Ansible')
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
