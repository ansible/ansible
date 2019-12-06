# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import atexit
import time
import re
import traceback

XENAPI_IMP_ERR = None
try:
    import XenAPI
    HAS_XENAPI = True
except ImportError:
    HAS_XENAPI = False
    XENAPI_IMP_ERR = traceback.format_exc()

from ansible.module_utils.basic import env_fallback, missing_required_lib
from ansible.module_utils.common.network import is_mac
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


def xapi_to_module_vm_power_state(power_state):
    """Maps XAPI VM power states to module VM power states."""
    module_power_state_map = {
        "running": "poweredon",
        "halted": "poweredoff",
        "suspended": "suspended",
        "paused": "paused"
    }

    return module_power_state_map.get(power_state)


def module_to_xapi_vm_power_state(power_state):
    """Maps module VM power states to XAPI VM power states."""
    vm_power_state_map = {
        "poweredon": "running",
        "poweredoff": "halted",
        "restarted": "running",
        "suspended": "suspended",
        "shutdownguest": "halted",
        "rebootguest": "running",
    }

    return vm_power_state_map.get(power_state)


def is_valid_ip_addr(ip_addr):
    """Validates given string as IPv4 address for given string.

    Args:
        ip_addr (str): string to validate as IPv4 address.

    Returns:
        bool: True if string is valid IPv4 address, else False.
    """
    ip_addr_split = ip_addr.split('.')

    if len(ip_addr_split) != 4:
        return False

    for ip_addr_octet in ip_addr_split:
        if not ip_addr_octet.isdigit():
            return False

        ip_addr_octet_int = int(ip_addr_octet)

        if ip_addr_octet_int < 0 or ip_addr_octet_int > 255:
            return False

    return True


def is_valid_ip_netmask(ip_netmask):
    """Validates given string as IPv4 netmask.

    Args:
        ip_netmask (str): string to validate as IPv4 netmask.

    Returns:
        bool: True if string is valid IPv4 netmask, else False.
    """
    ip_netmask_split = ip_netmask.split('.')

    if len(ip_netmask_split) != 4:
        return False

    valid_octet_values = ['0', '128', '192', '224', '240', '248', '252', '254', '255']

    for ip_netmask_octet in ip_netmask_split:
        if ip_netmask_octet not in valid_octet_values:
            return False

    if ip_netmask_split[0] != '255' and (ip_netmask_split[1] != '0' or ip_netmask_split[2] != '0' or ip_netmask_split[3] != '0'):
        return False
    elif ip_netmask_split[1] != '255' and (ip_netmask_split[2] != '0' or ip_netmask_split[3] != '0'):
        return False
    elif ip_netmask_split[2] != '255' and ip_netmask_split[3] != '0':
        return False

    return True


def is_valid_ip_prefix(ip_prefix):
    """Validates given string as IPv4 prefix.

    Args:
        ip_prefix (str): string to validate as IPv4 prefix.

    Returns:
        bool: True if string is valid IPv4 prefix, else False.
    """
    if not ip_prefix.isdigit():
        return False

    ip_prefix_int = int(ip_prefix)

    if ip_prefix_int < 0 or ip_prefix_int > 32:
        return False

    return True


def ip_prefix_to_netmask(ip_prefix, skip_check=False):
    """Converts IPv4 prefix to netmask.

    Args:
        ip_prefix (str): IPv4 prefix to convert.
        skip_check (bool): Skip validation of IPv4 prefix
            (default: False). Use if you are sure IPv4 prefix is valid.

    Returns:
        str: IPv4 netmask equivalent to given IPv4 prefix if
        IPv4 prefix is valid, else an empty string.
    """
    if skip_check:
        ip_prefix_valid = True
    else:
        ip_prefix_valid = is_valid_ip_prefix(ip_prefix)

    if ip_prefix_valid:
        return '.'.join([str((0xffffffff << (32 - int(ip_prefix)) >> i) & 0xff) for i in [24, 16, 8, 0]])
    else:
        return ""


def ip_netmask_to_prefix(ip_netmask, skip_check=False):
    """Converts IPv4 netmask to prefix.

    Args:
        ip_netmask (str): IPv4 netmask to convert.
        skip_check (bool): Skip validation of IPv4 netmask
            (default: False). Use if you are sure IPv4 netmask is valid.

    Returns:
        str: IPv4 prefix equivalent to given IPv4 netmask if
        IPv4 netmask is valid, else an empty string.
    """
    if skip_check:
        ip_netmask_valid = True
    else:
        ip_netmask_valid = is_valid_ip_netmask(ip_netmask)

    if ip_netmask_valid:
        return str(sum([bin(int(i)).count("1") for i in ip_netmask.split(".")]))
    else:
        return ""


def is_valid_ip6_addr(ip6_addr):
    """Validates given string as IPv6 address.

    Args:
        ip6_addr (str): string to validate as IPv6 address.

    Returns:
        bool: True if string is valid IPv6 address, else False.
    """
    ip6_addr = ip6_addr.lower()
    ip6_addr_split = ip6_addr.split(':')

    if ip6_addr_split[0] == "":
        ip6_addr_split.pop(0)

    if ip6_addr_split[-1] == "":
        ip6_addr_split.pop(-1)

    if len(ip6_addr_split) > 8:
        return False

    if ip6_addr_split.count("") > 1:
        return False
    elif ip6_addr_split.count("") == 1:
        ip6_addr_split.remove("")
    else:
        if len(ip6_addr_split) != 8:
            return False

    ip6_addr_hextet_regex = re.compile('^[0-9a-f]{1,4}$')

    for ip6_addr_hextet in ip6_addr_split:
        if not bool(ip6_addr_hextet_regex.match(ip6_addr_hextet)):
            return False

    return True


def is_valid_ip6_prefix(ip6_prefix):
    """Validates given string as IPv6 prefix.

    Args:
        ip6_prefix (str): string to validate as IPv6 prefix.

    Returns:
        bool: True if string is valid IPv6 prefix, else False.
    """
    if not ip6_prefix.isdigit():
        return False

    ip6_prefix_int = int(ip6_prefix)

    if ip6_prefix_int < 0 or ip6_prefix_int > 128:
        return False

    return True


def get_object_ref(module, name, uuid=None, obj_type="VM", fail=True, msg_prefix=""):
    """Finds and returns a reference to arbitrary XAPI object.

    An object is searched by using either name (name_label) or UUID
    with UUID taken precedence over name.

    Args:
        module: Reference to Ansible module object.
        name (str): Name (name_label) of an object to search for.
        uuid (str): UUID of an object to search for.
        obj_type (str): Any valid XAPI object type. See XAPI docs.
        fail (bool): Should function fail with error message if object
            is not found or exit silently (default: True). The function
            always fails if multiple objects with same name are found.
        msg_prefix (str): A string error messages should be prefixed
            with (default: "").

    Returns:
        XAPI reference to found object or None if object is not found
        and fail=False.
    """
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

    # UUID has precedence over name.
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
    """Gathers all VM parameters available in XAPI database.

    Args:
        module: Reference to Ansible module object.
        vm_ref (str): XAPI reference to VM.

    Returns:
        dict: VM parameters.
    """
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

        # Detect customization agent.
        xenserver_version = get_xenserver_version(module)

        if (xenserver_version[0] >= 7 and xenserver_version[1] >= 0 and vm_params.get('guest_metrics') and
                "feature-static-ip-setting" in vm_params['guest_metrics']['other']):
            vm_params['customization_agent'] = "native"
        else:
            vm_params['customization_agent'] = "custom"

    except XenAPI.Failure as f:
        module.fail_json(msg="XAPI ERROR: %s" % f.details)

    return vm_params


def gather_vm_facts(module, vm_params):
    """Gathers VM facts.

    Args:
        module: Reference to Ansible module object.
        vm_params (dict): A dictionary with VM parameters as returned
            by gather_vm_params() function.

    Returns:
        dict: VM facts.
    """
    # We silently return empty vm_facts if no vm_params are available.
    if not vm_params:
        return {}

    xapi_session = XAPI.connect(module)

    # Gather facts.
    vm_facts = {
        "state": xapi_to_module_vm_power_state(vm_params['power_state'].lower()),
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
        "customization_agent": vm_params['customization_agent'],
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
                "os_device": vm_vbd_params['device'],
                "vbd_userdevice": vm_vbd_params['userdevice'],
            }

            vm_facts['disks'].append(vm_disk_params)
        elif vm_vbd_params['type'] == "CD":
            if vm_vbd_params['empty']:
                vm_facts['cdrom'].update(type="none")
            else:
                vm_facts['cdrom'].update(type="iso")
                vm_facts['cdrom'].update(iso_name=vm_vbd_params['VDI']['name_label'])

    for vm_vif_params in vm_params['VIFs']:
        vm_guest_metrics_networks = vm_params['guest_metrics'].get('networks', {})

        vm_network_params = {
            "name": vm_vif_params['network']['name_label'],
            "mac": vm_vif_params['MAC'],
            "vif_device": vm_vif_params['device'],
            "mtu": vm_vif_params['MTU'],
            "ip": vm_guest_metrics_networks.get("%s/ip" % vm_vif_params['device'], ''),
            "prefix": "",
            "netmask": "",
            "gateway": "",
            "ip6": [vm_guest_metrics_networks[ipv6] for ipv6 in sorted(vm_guest_metrics_networks.keys()) if ipv6.startswith("%s/ipv6/" %
                                                                                                                            vm_vif_params['device'])],
            "prefix6": "",
            "gateway6": "",
        }

        if vm_params['customization_agent'] == "native":
            if vm_vif_params['ipv4_addresses'] and vm_vif_params['ipv4_addresses'][0]:
                vm_network_params['prefix'] = vm_vif_params['ipv4_addresses'][0].split('/')[1]
                vm_network_params['netmask'] = ip_prefix_to_netmask(vm_network_params['prefix'])

            vm_network_params['gateway'] = vm_vif_params['ipv4_gateway']

            if vm_vif_params['ipv6_addresses'] and vm_vif_params['ipv6_addresses'][0]:
                vm_network_params['prefix6'] = vm_vif_params['ipv6_addresses'][0].split('/')[1]

            vm_network_params['gateway6'] = vm_vif_params['ipv6_gateway']

        elif vm_params['customization_agent'] == "custom":
            vm_xenstore_data = vm_params['xenstore_data']

            for f in ['prefix', 'netmask', 'gateway', 'prefix6', 'gateway6']:
                vm_network_params[f] = vm_xenstore_data.get("vm-data/networks/%s/%s" % (vm_vif_params['device'], f), "")

        vm_facts['networks'].append(vm_network_params)

    return vm_facts


def set_vm_power_state(module, vm_ref, power_state, timeout=300):
    """Controls VM power state.

    Args:
        module: Reference to Ansible module object.
        vm_ref (str): XAPI reference to VM.
        power_state (str): Power state to put VM into. Accepted values:

            - poweredon
            - poweredoff
            - restarted
            - suspended
            - shutdownguest
            - rebootguest

        timeout (int): timeout in seconds (default: 300).

    Returns:
        tuple (bool, str): Bool element is True if VM power state has
        changed by calling this function, else False. Str element carries
        a value of resulting power state as defined by XAPI - 'running',
        'halted' or 'suspended'.
    """
    # Fail if we don't have a valid VM reference.
    if not vm_ref or vm_ref == "OpaqueRef:NULL":
        module.fail_json(msg="Cannot set VM power state. Invalid VM reference supplied!")

    xapi_session = XAPI.connect(module)

    power_state = power_state.replace('_', '').replace('-', '').lower()
    vm_power_state_resulting = module_to_xapi_vm_power_state(power_state)

    state_changed = False

    try:
        # Get current state of the VM.
        vm_power_state_current = xapi_to_module_vm_power_state(xapi_session.xenapi.VM.get_power_state(vm_ref).lower())

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
                # hard_reboot will restart VM only if VM is in paused or running state.
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
                    module.fail_json(msg="Cannot shutdown guest when VM is in state '%s'!" % vm_power_state_current)
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
                    module.fail_json(msg="Cannot reboot guest when VM is in state '%s'!" % vm_power_state_current)
            else:
                module.fail_json(msg="Requested VM power state '%s' is unsupported!" % power_state)

            state_changed = True
    except XenAPI.Failure as f:
        module.fail_json(msg="XAPI ERROR: %s" % f.details)

    return (state_changed, vm_power_state_resulting)


def wait_for_task(module, task_ref, timeout=300):
    """Waits for async XAPI task to finish.

    Args:
        module: Reference to Ansible module object.
        task_ref (str): XAPI reference to task.
        timeout (int): timeout in seconds (default: 300).

    Returns:
        str: failure message on failure, else an empty string.
    """
    # Fail if we don't have a valid task reference.
    if not task_ref or task_ref == "OpaqueRef:NULL":
        module.fail_json(msg="Cannot wait for task. Invalid task reference supplied!")

    xapi_session = XAPI.connect(module)

    interval = 2

    result = ""

    # If we have to wait indefinitely, make time_left larger than 0 so we can
    # enter while loop.
    if timeout == 0:
        time_left = 1
    else:
        time_left = timeout

    try:
        while time_left > 0:
            task_status = xapi_session.xenapi.task.get_status(task_ref).lower()

            if task_status == "pending":
                # Task is still running.
                time.sleep(interval)

                # We decrease time_left only if we don't wait indefinitely.
                if timeout != 0:
                    time_left -= interval

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
    """Waits for VM to acquire an IP address.

    Args:
        module: Reference to Ansible module object.
        vm_ref (str): XAPI reference to VM.
        timeout (int): timeout in seconds (default: 300).

    Returns:
        dict: VM guest metrics as retrieved by
        VM_guest_metrics.get_record() XAPI method with info
        on IP address acquired.
    """
    # Fail if we don't have a valid VM reference.
    if not vm_ref or vm_ref == "OpaqueRef:NULL":
        module.fail_json(msg="Cannot wait for VM IP address. Invalid VM reference supplied!")

    xapi_session = XAPI.connect(module)

    vm_guest_metrics = {}

    try:
        # We translate VM power state string so that error message can be
        # consistent with module VM power states.
        vm_power_state = xapi_to_module_vm_power_state(xapi_session.xenapi.VM.get_power_state(vm_ref).lower())

        if vm_power_state != 'poweredon':
            module.fail_json(msg="Cannot wait for VM IP address when VM is in state '%s'!" % vm_power_state)

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


def get_xenserver_version(module):
    """Returns XenServer version.

    Args:
        module: Reference to Ansible module object.

    Returns:
        list: Element [0] is major version. Element [1] is minor version.
        Element [2] is update number.
    """
    xapi_session = XAPI.connect(module)

    host_ref = xapi_session.xenapi.session.get_this_host(xapi_session._session)

    try:
        xenserver_version = [int(version_number) for version_number in xapi_session.xenapi.host.get_software_version(host_ref)['product_version'].split('.')]
    except ValueError:
        xenserver_version = [0, 0, 0]

    return xenserver_version


class XAPI(object):
    """Class for XAPI session management."""
    _xapi_session = None

    @classmethod
    def connect(cls, module, disconnect_atexit=True):
        """Establishes XAPI connection and returns session reference.

        If no existing session is available, establishes a new one
        and returns it, else returns existing one.

        Args:
            module: Reference to Ansible module object.
            disconnect_atexit (bool): Controls if method should
                register atexit handler to disconnect from XenServer
                on module exit (default: True).

        Returns:
            XAPI session reference.
        """
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
                # ignore_ssl is supported in XenAPI library from XenServer 7.2
                # SDK onward but there is no way to tell which version we
                # are using. TypeError will be raised if ignore_ssl is not
                # supported. Additionally, ignore_ssl requires Python 2.7.9
                # or newer.
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
    """Base class for all XenServer objects.

    This class contains active XAPI session reference and common
    attributes with useful info about XenServer host/pool.

    Attributes:
        module: Reference to Ansible module object.
        xapi_session: Reference to XAPI session.
        pool_ref (str): XAPI reference to a pool currently connected to.
        default_sr_ref (str): XAPI reference to a pool default
            Storage Repository.
        host_ref (str): XAPI rerefence to a host currently connected to.
        xenserver_version (list of str): Contains XenServer major and
            minor version.
    """

    def __init__(self, module):
        """Inits XenServerObject using common module parameters.

        Args:
            module: Reference to Ansible module object.
        """
        if not HAS_XENAPI:
            module.fail_json(changed=False, msg=missing_required_lib("XenAPI"), exception=XENAPI_IMP_ERR)

        self.module = module
        self.xapi_session = XAPI.connect(module)

        try:
            self.pool_ref = self.xapi_session.xenapi.pool.get_all()[0]
            self.default_sr_ref = self.xapi_session.xenapi.pool.get_default_SR(self.pool_ref)
            self.xenserver_version = get_xenserver_version(module)
        except XenAPI.Failure as f:
            self.module.fail_json(msg="XAPI ERROR: %s" % f.details)
