# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import uuid
import copy
import ipaddress

from mock import MagicMock
from ansible.module_utils._text import to_text


# These are patched with mocker.patch().
_XENAPI_DB = None
_MAX_VBD_DEVICES = 255
_MAX_VIF_DEVICES = 7

FAKE_API_VERSION = "1.1"


class Failure(Exception):
    def __init__(self, details):
        self.details = details

    def __str__(self):
        return str(self.details)


class _XenAPIMethodResolver:
    def __init__(self, request_handler, method):
        self.request_handler = request_handler
        self.method = method

    def __getattr__(self, method):
        if self.method is None:
            return _XenAPIMethodResolver(self.request_handler, method)
        else:
            return _XenAPIMethodResolver(self.request_handler, "%s.%s" % (self.method, method))

    def __call__(self, *params):
        return self.request_handler(self.method, params)


class Session(object):
    def __init__(self, uri, transport=None, encoding=None, verbose=0,
                 allow_none=1, ignore_ssl=False):

        self.transport = transport
        self._session = None
        self.last_login_method = None
        self.last_login_params = None
        self.API_version = FAKE_API_VERSION

        self._db = _XENAPI_DB

        # We define our own MagicMock based object to more easily track
        # XenAPI method calls.
        class XenAPIMagicMock(MagicMock):
            def xenapi_method_call_count(self, method):
                i = 0

                for args in self.call_args_list:
                    if args[0][0] == method:
                        i += 1

                return i

            def assert_xenapi_method_called(self, method):
                if self.xenapi_method_call_count(method) == 0:
                    msg = "Expected '%s' to have been called." % method
                    raise AssertionError(msg)

            def assert_xenapi_method_not_called(self, method):
                call_count = self.xenapi_method_call_count(method)

                if call_count != 0:
                    msg = "Expected '%s' to not have been called. Called %s times." % (method, call_count)
                    raise AssertionError(msg)

            def assert_xenapi_method_called_once(self, method):
                call_count = self.xenapi_method_call_count(method)

                if not call_count == 1:
                    msg = "Expected '%s' to have been called once. Called %s times." % (method, call_count)
                    raise AssertionError(msg)

        # Wrap XenAPI.Session.xenapi_request() with mock object so we can
        # track XenAPI method calls.
        self.xenapi_request = XenAPIMagicMock(wraps=self._xenapi_request)

    def _get_api_version(self):
        pool_ref = list(self._db['pool'].keys())[0]
        master_host_ref = self._db['pool'][pool_ref]['master']

        return "%s.%s" % (self._db['host'][master_host_ref]['API_version_major'],
                          self._db['host'][master_host_ref]['API_version_minor'])

    def _login(self, method, params):
        if not self._db:
            raise Failure(['DB_EMPTY'])

        session_ref = "OpaqueRef:%s" % str(uuid.uuid4())
        pool_ref = list(self._db['pool'].keys())[0]
        master_host_ref = self._db['pool'][pool_ref]['master']

        self._db['session'][session_ref] = {
            "this_host": master_host_ref,
        }

        self._session = session_ref
        self.last_login_method = method
        self.last_login_params = params
        self.API_version = self._get_api_version()

    def _logout(self):
        if self._session in self._db['session']:
            del self._db['session'][self._session]

        self._session = None
        self.last_login_method = None
        self.last_login_params = None
        self.API_version = FAKE_API_VERSION

    def _xenapi_request(self, method, params):
        if method.startswith('login'):
            self._login(method, params)
            return None
        elif method == 'logout' or method == 'session.logout':
            self._logout()
            return None
        else:
            if not self._db:
                raise Failure(['DB_EMPTY'])

            if self._session is None:
                raise Failure(['SESSION_INVALID', 'None'])

            if method.startswith("Async."):
                task_ref = "OpaqueRef:%s" % str(uuid.uuid4())

                self._db['task'][task_ref] = {
                    "name-label": method,
                    "status": "Pending",
                    "_params": params,
                }

                return task_ref

            method_split = method.split('.')

            if len(method_split) != 2 or method_split[0] not in self._db:
                raise Failure(['MESSAGE_METHOD_UNKNOWN', method])

            xenapi_class = method_split[0]
            xenapi_method = method_split[1]

            if xenapi_method == "get_all":
                return list(self._db[xenapi_class].keys())
            elif xenapi_method == "get_all_records":
                return copy.deepcopy(self._db[xenapi_class])
            elif xenapi_method == "get_record":
                obj_ref = params[0]

                if obj_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, obj_ref])
                else:
                    return copy.deepcopy(self._db[xenapi_class][obj_ref])
            elif xenapi_method == "get_by_name_label":
                return [obj_ref for obj_ref in list(self._db[xenapi_class].keys()) if self._db[xenapi_class][obj_ref]['name_label'] == params[0]]
            elif xenapi_method == "get_by_uuid":
                obj_ref_found = None

                for obj_ref in list(self._db[xenapi_class].keys()):
                    if self._db[xenapi_class][obj_ref]['uuid'] == params[0]:
                        obj_ref_found = obj_ref

                if obj_ref_found is None:
                    raise Failure(['UUID_INVALID', xenapi_class, params[0]])
                else:
                    return obj_ref_found
            elif xenapi_method.startswith('get_') and method not in ['VM.get_allowed_VBD_devices', 'VM.get_allowed_VIF_devices', 'task.get_status']:
                obj_ref = params[0]
                field = xenapi_method[4:]

                if obj_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, obj_ref])
                elif field not in self._db[xenapi_class][obj_ref]:
                    raise Failure(['MESSAGE_METHOD_UNKNOWN', method])

                return copy.deepcopy(self._db[xenapi_class][obj_ref][field])
            elif xenapi_method.startswith('set_') and method not in ['VM.set_memory_limits']:
                obj_ref = params[0]
                field = xenapi_method[4:]
                value = params[1]

                if obj_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, obj_ref])
                elif field not in self._db[xenapi_class][obj_ref]:
                    raise Failure(['MESSAGE_METHOD_UNKNOWN', method])

                self._db[xenapi_class][obj_ref][field] = value
            elif xenapi_method.startswith('add_to_'):
                obj_ref = params[0]
                field = xenapi_method[7:]
                key = params[1]
                value = params[2]

                if obj_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, obj_ref])
                elif field not in self._db[xenapi_class][obj_ref]:
                    raise Failure(['MESSAGE_METHOD_UNKNOWN', method])
                elif key in self._db[xenapi_class][obj_ref][field]:
                    raise Failure(['MAP_DUPLICATE_KEY', xenapi_class, field, obj_ref, key])

                if field == "xenstore_data" and key.startswith('vm-data'):
                    xenstore_data_path = "vm-data"

                    for xenstore_data_path_component in key.split('/')[1:-1]:
                        xenstore_data_path = "%s/%s" % (xenstore_data_path, xenstore_data_path_component)
                        self._db[xenapi_class][obj_ref][field][xenstore_data_path] = ""

                self._db[xenapi_class][obj_ref][field][key] = value
            elif xenapi_method.startswith('remove_from_'):
                obj_ref = params[0]
                field = xenapi_method[12:]
                key = params[1]

                if obj_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, obj_ref])
                elif field not in self._db[xenapi_class][obj_ref]:
                    raise Failure(['MESSAGE_METHOD_UNKNOWN', method])

                if key in self._db[xenapi_class][obj_ref][field]:
                    del self._db[xenapi_class][obj_ref][field][key]
            elif xenapi_method.startswith('add_'):
                obj_ref = params[0]
                field = xenapi_method[4:]
                value = params[1]

                if obj_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, obj_ref])
                elif field not in self._db[xenapi_class][obj_ref]:
                    raise Failure(['MESSAGE_METHOD_UNKNOWN', method])

                self._db[xenapi_class][obj_ref][field].append(value)
            elif xenapi_method.startswith('remove_'):
                obj_ref = params[0]
                field = xenapi_method[7:]
                value = params[1]

                if obj_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, obj_ref])
                elif field not in self._db[xenapi_class][obj_ref]:
                    raise Failure(['MESSAGE_METHOD_UNKNOWN', method])

                if value in self._db[xenapi_class][obj_ref][field]:
                    self._db[xenapi_class][obj_ref][field].remove(value)
            elif xenapi_class == "VM":
                vm_ref = params[0]

                if vm_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, vm_ref])

                vm_power_state = self._db[xenapi_class][vm_ref]['power_state']

                if xenapi_method == "hard_reboot":
                    if vm_power_state not in ['Running', 'Paused']:
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, ['Running', 'Paused'], vm_power_state])

                    self.xenapi_request('VM.hard_shutdown', params)
                    self.xenapi_request('VM.start', params)
                elif xenapi_method == "hard_shutdown":
                    host_ref = self._db[xenapi_class][vm_ref]['resident_on']

                    self._db[xenapi_class][vm_ref]['domid'] = "-1"
                    self._db[xenapi_class][vm_ref]['power_state'] = "Halted"
                    self._db[xenapi_class][vm_ref]['resident_on'] = "OpaqueRef:NULL"

                    for vbd_ref in self._db[xenapi_class][vm_ref]['VBDs']:
                        self._db['VBD'][vbd_ref]['currently_attached'] = False

                    for vif_ref in self._db[xenapi_class][vm_ref]['VIFs']:
                        self._db['VIF'][vif_ref]['currently_attached'] = False

                    self._db['host'][host_ref]['resident_VMs'].remove(vm_ref)
                elif xenapi_method == "clean_reboot":
                    self.xenapi_request('VM.clean_shutdown', params)
                    self.xenapi_request('VM.start', params)
                elif xenapi_method == "clean_shutdown":
                    if vm_power_state != "Running":
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, 'Running', vm_power_state])

                    self.xenapi_request('VM.hard_shutdown', params)
                elif xenapi_method == "start":
                    if vm_power_state != "Halted":
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, 'Halted', vm_power_state])

                    if self._db[xenapi_class][vm_ref]['affinity'] != "OpaqueRef:NULL":
                        host_ref = self._db[xenapi_class][vm_ref]['affinity']
                    else:
                        host_ref = list(self._db['host'].keys())[0]

                    self._db[xenapi_class][vm_ref]['domid'] = "1"
                    self._db[xenapi_class][vm_ref]['power_state'] = "Running"
                    self._db[xenapi_class][vm_ref]['resident_on'] = host_ref

                    for vbd_ref in self._db[xenapi_class][vm_ref]['VBDs']:
                        self._db['VBD'][vbd_ref]['currently_attached'] = True

                    for vif_ref in self._db[xenapi_class][vm_ref]['VIFs']:
                        self._db['VIF'][vif_ref]['currently_attached'] = True

                    self._db['host'][host_ref]['resident_VMs'].append(vm_ref)

                    vm_guest_metrics_ref = self._db[xenapi_class][vm_ref]['guest_metrics']

                    if vm_guest_metrics_ref != "OpaqueRef:NULL":
                        vif_device_list = [(vif_ref, self._db['VIF'][vif_ref]['device']) for vif_ref in self._db[xenapi_class][vm_ref]['VIFs']]
                        vm_guest_metrics_networks = self._db['VM_guest_metrics'][vm_guest_metrics_ref]['networks']

                        if self._db['VM_guest_metrics'][vm_guest_metrics_ref]['other'].get('feature-static-ip-setting') == "1":
                            for vif_ref, vif_device in vif_device_list:
                                network_type = self._db['VIF'][vif_ref]['ipv4_configuration_mode']
                                network_ip = self._db['VIF'][vif_ref]['ipv4_addresses']
                                network_type6 = self._db['VIF'][vif_ref]['ipv6_configuration_mode']
                                network_ip6 = self._db['VIF'][vif_ref]['ipv6_addresses']

                                if network_type == "Static":
                                    vm_guest_metrics_networks['%s/ip' % vif_device] = network_ip[0].split('/')[0]
                                else:
                                    network_ref = self._db['VIF'][vif_ref]['network']

                                    if self._db['network'][network_ref]['name_label'] == "Host internal management network":
                                        if vif_ref in self._db['network'][network_ref]['assigned_ips']:
                                            vm_guest_metrics_networks['%s/ip' % vif_device] = self._db['network'][network_ref]['assigned_ips'][vif_ref]
                                        else:
                                            vm_guest_metrics_networks['%s/ip' % vif_device] = '169.254.255.1'
                                            self._db['network'][network_ref]['assigned_ips'][vif_ref] = '169.254.255.1'
                                    else:
                                        vm_guest_metrics_networks['%s/ip' % vif_device] = ''

                                if network_type6 == "Static":
                                    vm_guest_metrics_networks['%s/ipv6/1' % vif_device] = ipaddress.ip_address(to_text(network_ip6[0].split('/')[0])).exploded
                                else:
                                    ipv6_key = "%s/ipv6/1" % vif_device

                                    if ipv6_key in vm_guest_metrics_networks:
                                        del vm_guest_metrics_networks[ipv6_key]
                        else:
                            for vif_ref, vif_device in vif_device_list:
                                xenstore_data_key_prefix = "vm-data/networks/%s" % vif_device
                                xenstore_data_key_type = "%s/type" % xenstore_data_key_prefix
                                xenstore_data_key_ip = "%s/ip" % xenstore_data_key_prefix
                                xenstore_data_key_type6 = "%s/type6" % xenstore_data_key_prefix
                                xenstore_data_key_ip6 = "%s/ip6" % xenstore_data_key_prefix

                                network_type = self._db[xenapi_class][vm_ref]['xenstore_data'].get(xenstore_data_key_type, 'none')
                                network_ip = self._db[xenapi_class][vm_ref]['xenstore_data'].get(xenstore_data_key_ip, '')
                                network_type6 = self._db[xenapi_class][vm_ref]['xenstore_data'].get(xenstore_data_key_type6, 'none')
                                network_ip6 = self._db[xenapi_class][vm_ref]['xenstore_data'].get(xenstore_data_key_ip6, '')

                                if network_type == "static":
                                    vm_guest_metrics_networks['%s/ip' % vif_device] = network_ip
                                elif network_type == "dhcp":
                                    network_ref = self._db['VIF'][vif_ref]['network']

                                    if self._db['network'][network_ref]['name_label'] == "Host internal management network":
                                        if vif_ref in self._db['network'][network_ref]['assigned_ips']:
                                            vm_guest_metrics_networks['%s/ip' % vif_device] = self._db['network'][network_ref]['assigned_ips'][vif_ref]
                                        else:
                                            vm_guest_metrics_networks['%s/ip' % vif_device] = '169.254.255.1'
                                            self._db['network'][network_ref]['assigned_ips'][vif_ref] = '169.254.255.1'
                                    else:
                                        vm_guest_metrics_networks['%s/ip' % vif_device] = ''

                                if network_type6 == "static":
                                    vm_guest_metrics_networks['%s/ipv6/1' % vif_device] = ipaddress.ip_address(to_text(network_ip6)).exploded
                                elif network_type6 == "dhcp":
                                    ipv6_key = "%s/ipv6/1" % vif_device

                                    if ipv6_key in vm_guest_metrics_networks:
                                        del vm_guest_metrics_networks[ipv6_key]
                elif xenapi_method == "suspend":
                    if vm_power_state != "Running":
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, 'Running', vm_power_state])

                    self._db[xenapi_class][vm_ref]['power_state'] = "Suspended"
                elif xenapi_method == "pause":
                    if vm_power_state != "Running":
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, 'Running', vm_power_state])

                    self._db[xenapi_class][vm_ref]['power_state'] = "Paused"
                elif xenapi_method == "resume":
                    if vm_power_state != "Suspended":
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, 'Suspended', vm_power_state])

                    self._db[xenapi_class][vm_ref]['power_state'] = "Running"
                elif xenapi_method == "unpause":
                    if vm_power_state != "Paused":
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, 'Paused', vm_power_state])

                    self._db[xenapi_class][vm_ref]['power_state'] = "Running"
                elif xenapi_method in ['clone', 'copy']:
                    if vm_power_state != "Halted":
                        raise Failure(['VM_BAD_POWER_STATE', vm_ref, 'Halted', vm_power_state])

                    vm_ref_new = "OpaqueRef:%s" % str(uuid.uuid4())

                    self._db[xenapi_class][vm_ref_new] = copy.deepcopy(self._db[xenapi_class][vm_ref])
                    self._db[xenapi_class][vm_ref_new]['VBDs'] = []
                    self._db[xenapi_class][vm_ref_new]['VIFs'] = []
                    self._db[xenapi_class][vm_ref_new]['guest_metrics'] = "OpaqueRef:NULL"
                    self._db[xenapi_class][vm_ref_new]['is_a_snapshot'] = False
                    self._db[xenapi_class][vm_ref_new]['is_a_template'] = False
                    self._db[xenapi_class][vm_ref_new]['name_label'] = params[1]
                    self._db[xenapi_class][vm_ref_new]['uuid'] = str(uuid.uuid4())
                    self._db[xenapi_class][vm_ref_new]['xenstore_data'] = {"vm-data": ""}

                    for vbd_ref in self._db[xenapi_class][vm_ref]['VBDs']:
                        vdi_ref = self._db['VBD'][vbd_ref]['VDI']

                        if vdi_ref != "OpaqueRef:NULL":
                            if self._db['VBD'][vbd_ref]['type'] == "Disk":
                                if xenapi_method == "clone":
                                    vdi_ref_new = self.xenapi_request('VDI.clone', (vdi_ref, {}))
                                else:
                                    sr_ref = params[2]
                                    vdi_ref_new = self.xenapi_request('VDI.copy', (vdi_ref, sr_ref, None, None))
                            else:
                                vdi_ref_new = vdi_ref

                        vbd_record = copy.deepcopy(self._db['VBD'][vbd_ref])
                        vbd_record['VDI'] = vdi_ref_new
                        vbd_record['VM'] = vm_ref_new
                        vbd_ref_new = self.xenapi_request('VBD.create', (vbd_record,))

                    vm_guest_metrics_ref = self._db[xenapi_class][vm_ref]['guest_metrics']

                    if vm_guest_metrics_ref != "OpaqueRef:NULL":
                        vm_guest_metrics_ref_new = "OpaqueRef:%s" % str(uuid.uuid4())

                        self._db['VM_guest_metrics'][vm_guest_metrics_ref_new] = copy.deepcopy(self._db['VM_guest_metrics'][vm_guest_metrics_ref])
                        self._db['VM_guest_metrics'][vm_guest_metrics_ref_new]['uuid'] = str(uuid.uuid4())
                        self._db[xenapi_class][vm_ref_new]['guest_metrics'] = vm_guest_metrics_ref_new

                    for vif_ref in self._db[xenapi_class][vm_ref]['VIFs']:
                        network_ref = self._db['VIF'][vif_ref]['network']

                        vif_record = copy.deepcopy(self._db['VIF'][vif_ref])
                        vif_record['VM'] = vm_ref_new
                        vif_record['MAC'] = ""
                        vif_ref_new = self.xenapi_request('VIF.create', (vif_record,))

                    return vm_ref_new
                elif xenapi_method == "get_allowed_VBD_devices":
                    vm_allowed_VBD_devices = [str(x) for x in range(_MAX_VBD_DEVICES)]

                    for vbd_ref in self._db[xenapi_class][vm_ref]['VBDs']:
                        vm_allowed_VBD_devices.remove(self._db['VBD'][vbd_ref]['userdevice'])

                    return vm_allowed_VBD_devices
                elif xenapi_method == "get_allowed_VIF_devices":
                    vm_allowed_VIF_devices = [str(x) for x in range(_MAX_VIF_DEVICES)]

                    for vif_ref in self._db[xenapi_class][vm_ref]['VIFs']:
                        vm_allowed_VIF_devices.remove(self._db['VIF'][vif_ref]['device'])

                    return vm_allowed_VIF_devices
                elif xenapi_method == "set_memory_limits":
                    obj_ref = params[0]
                    memory_static_min = params[1]
                    memory_static_max = params[2]
                    memory_dynamic_min = params[3]
                    memory_dynamic_max = params[4]

                    self._db[xenapi_class][vm_ref]['memory_static_min'] = memory_static_min
                    self._db[xenapi_class][vm_ref]['memory_static_max'] = memory_static_max
                    self._db[xenapi_class][vm_ref]['memory_dynamic_min'] = memory_dynamic_min
                    self._db[xenapi_class][vm_ref]['memory_dynamic_max'] = memory_dynamic_max
                elif xenapi_method == 'destroy':
                    for vbd_ref in copy.deepcopy(self._db[xenapi_class][vm_ref]['VBDs']):
                        self.xenapi_request('VBD.destroy', (vbd_ref,))

                    for vif_ref in copy.deepcopy(self._db[xenapi_class][vm_ref]['VIFs']):
                        self.xenapi_request('VIF.destroy', (vif_ref,))

                    vm_guest_metrics_ref = self._db[xenapi_class][vm_ref]['guest_metrics']
                    self._db[xenapi_class][vm_ref]['guest_metrics'] = "OpaqueRef:NULL"
                    del self._db['VM_guest_metrics'][vm_guest_metrics_ref]

                    del self._db[xenapi_class][vm_ref]
            elif xenapi_class == "VBD":
                vbd_ref = params[0]

                if xenapi_method not in ['create'] and vbd_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, vbd_ref])

                if xenapi_method == "create":
                    vbd_record = params[0]
                    vbd_ref_new = "OpaqueRef:%s" % str(uuid.uuid4())
                    vm_ref = vbd_record['VM']
                    vdi_ref = vbd_record['VDI']

                    self._db[xenapi_class][vbd_ref_new] = copy.deepcopy(vbd_record)
                    self._db[xenapi_class][vbd_ref_new]['uuid'] = str(uuid.uuid4())
                    self._db[xenapi_class][vbd_ref_new]['device'] = "xvd%s" % chr(int(vbd_record['userdevice']) + 97)
                    self._db['VM'][vm_ref]['VBDs'].append(vbd_ref_new)

                    if vdi_ref != "OpaqueRef:NULL":
                        self._db['VDI'][vdi_ref]['VBDs'].append(vbd_ref_new)

                    return vbd_ref_new
                elif xenapi_method == "insert":
                    vdi_ref = params[1]

                    if self._db[xenapi_class][vbd_ref]['type'] == "Disk":
                        raise Failure(['VBD_NOT_REMOVABLE_MEDIA', vbd_ref])
                    elif self._db[xenapi_class][vbd_ref]['empty'] is False:
                        raise Failure(['VBD_NOT_EMPTY', vbd_ref])

                    self._db[xenapi_class][vbd_ref]['VDI'] = vdi_ref
                    self._db[xenapi_class][vbd_ref]['empty'] = False
                    self._db['VDI'][vdi_ref]['VBDs'].append(vbd_ref)
                elif xenapi_method == "eject":
                    vdi_ref = self._db[xenapi_class][vbd_ref]['VDI']

                    if self._db[xenapi_class][vbd_ref]['type'] == "Disk":
                        raise Failure(['VBD_NOT_REMOVABLE_MEDIA', vbd_ref])
                    elif self._db[xenapi_class][vbd_ref]['empty'] is True:
                        raise Failure(['VBD_IS_EMPTY', vbd_ref])

                    self._db[xenapi_class][vbd_ref]['VDI'] = "OpaqueRef:NULL"
                    self._db[xenapi_class][vbd_ref]['empty'] = True
                    self._db['VDI'][vdi_ref]['VBDs'].remove(vbd_ref)
                elif xenapi_method == 'destroy':
                    vm_ref = self._db[xenapi_class][vbd_ref]['VM']
                    vdi_ref = self._db[xenapi_class][vbd_ref]['VDI']

                    self._db['VM'][vm_ref]['VBDs'].remove(vbd_ref)

                    if vdi_ref != "OpaqueRef:NULL":
                        self._db['VDI'][vdi_ref]['VBDs'].remove(vbd_ref)

                    del self._db[xenapi_class][vbd_ref]
                elif xenapi_method == "plug":
                    self._db[xenapi_class][vbd_ref]['currently_attached'] = True
                elif xenapi_method == "unplug":
                    self._db[xenapi_class][vbd_ref]['currently_attached'] = False
            elif xenapi_class == "VDI":
                vdi_ref = params[0]

                if xenapi_method not in ['create'] and vdi_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, vdi_ref])

                if xenapi_method == "create":
                    vdi_record = params[0]
                    sr_ref = vdi_record['SR']

                    sr_space_req = int(self._db['SR'][sr_ref]['virtual_allocation']) + int(vdi_record['virtual_size'])
                    sr_space_max = int(self._db['SR'][sr_ref]['physical_size'])

                    if sr_space_req > sr_space_max:
                        raise Failure(['SR_FULL', str(sr_space_req), str(sr_space_max)])

                    vdi_ref_new = "OpaqueRef:%s" % str(uuid.uuid4())
                    vdi_uuid_new = str(uuid.uuid4())
                    self._db[xenapi_class][vdi_ref_new] = copy.deepcopy(vdi_record)
                    self._db[xenapi_class][vdi_ref_new]['VBDs'] = []
                    self._db[xenapi_class][vdi_ref_new]['physical_utilisation'] = vdi_record['virtual_size']
                    self._db[xenapi_class][vdi_ref_new]['location'] = vdi_uuid_new
                    self._db[xenapi_class][vdi_ref_new]['uuid'] = vdi_uuid_new
                    self._db['SR'][sr_ref]['VDIs'].append(vdi_ref_new)
                    self._db['SR'][sr_ref]['virtual_allocation'] = str(sr_space_req)
                    self._db['SR'][sr_ref]['physical_utilisation'] = str(sr_space_req)

                    return vdi_ref_new
                elif xenapi_method == "clone":
                    vdi_ref_new = "OpaqueRef:%s" % str(uuid.uuid4())
                    vdi_uuid_new = str(uuid.uuid4())
                    sr_ref = self._db[xenapi_class][vdi_ref]['SR']

                    self._db[xenapi_class][vdi_ref_new] = copy.deepcopy(self._db[xenapi_class][vdi_ref])
                    self._db[xenapi_class][vdi_ref_new]['VBDs'] = []
                    self._db[xenapi_class][vdi_ref_new]['physical_utilisation'] = "0"
                    self._db[xenapi_class][vdi_ref_new]['location'] = vdi_uuid_new
                    self._db[xenapi_class][vdi_ref_new]['uuid'] = vdi_uuid_new
                    self._db['SR'][sr_ref]['VDIs'].append(vdi_ref_new)

                    return vdi_ref_new
                elif xenapi_method == "copy":
                    sr_ref = params[1]

                    sr_space_req = int(self._db['SR'][sr_ref]['virtual_allocation']) + int(self._db[xenapi_class][vdi_ref]['virtual_size'])
                    sr_space_max = int(self._db['SR'][sr_ref]['physical_size'])

                    if sr_space_req > sr_space_max:
                        raise Failure(['SR_FULL', str(sr_space_req), str(sr_space_max)])

                    vdi_ref_new = "OpaqueRef:%s" % str(uuid.uuid4())
                    vdi_uuid_new = str(uuid.uuid4())
                    self._db[xenapi_class][vdi_ref_new] = copy.deepcopy(self._db[xenapi_class][vdi_ref])
                    self._db[xenapi_class][vdi_ref_new]['SR'] = sr_ref
                    self._db[xenapi_class][vdi_ref_new]['VBDs'] = []
                    self._db[xenapi_class][vdi_ref_new]['location'] = vdi_uuid_new
                    self._db[xenapi_class][vdi_ref_new]['uuid'] = vdi_uuid_new
                    self._db['SR'][sr_ref]['VDIs'].append(vdi_ref_new)
                    self._db['SR'][sr_ref]['virtual_allocation'] = str(sr_space_req)
                    self._db['SR'][sr_ref]['physical_utilisation'] = str(sr_space_req)

                    return vdi_ref_new
                elif xenapi_method == "resize":
                    vdi_size = params[1]
                    sr_ref = self._db[xenapi_class][vdi_ref]['SR']

                    sr_space_req = int(self._db['SR'][sr_ref]['virtual_allocation']) + int(vdi_size)
                    sr_space_max = int(self._db['SR'][sr_ref]['physical_size'])

                    if sr_space_req > sr_space_max:
                        raise Failure(['SR_FULL', str(sr_space_req), str(sr_space_max)])

                    self._db[xenapi_class][vdi_ref]['virtual_size'] = vdi_size
                    self._db[xenapi_class][vdi_ref]['physical_utilisation'] = vdi_size
                    self._db['SR'][sr_ref]['virtual_allocation'] = str(sr_space_req)
                    self._db['SR'][sr_ref]['physical_utilisation'] = str(sr_space_req)
                elif xenapi_method == 'destroy':
                    sr_ref = self._db[xenapi_class][vdi_ref]['SR']
                    sr_space_new = int(self._db['SR'][sr_ref]['virtual_allocation']) - int(self._db[xenapi_class][vdi_ref]['virtual_size'])

                    self._db['SR'][sr_ref]['VDIs'].remove(vdi_ref)
                    self._db['SR'][sr_ref]['virtual_allocation'] = str(sr_space_new)
                    self._db['SR'][sr_ref]['physical_utilisation'] = str(sr_space_new)

                    for vbd_ref in copy.deepcopy(self._db[xenapi_class][vdi_ref]['VBDs']):
                        self.xenapi_request('VBD.destroy', (vbd_ref,))

                    del self._db[xenapi_class][vdi_ref]
            elif xenapi_class == "VIF":
                vif_ref = params[0]

                if xenapi_method not in ['create'] and vif_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, vif_ref])

                if xenapi_method == "create":
                    vif_record = params[0]
                    vif_ref_new = "OpaqueRef:%s" % str(uuid.uuid4())
                    vm_ref = vif_record['VM']
                    network_ref = vif_record['network']
                    vm_guest_metrics_ref = self._db['VM'][vm_ref]['guest_metrics']

                    self._db[xenapi_class][vif_ref_new] = copy.deepcopy(vif_record)
                    self._db[xenapi_class][vif_ref_new]['uuid'] = str(uuid.uuid4())

                    if self._db[xenapi_class][vif_ref_new]['MAC'] == "":
                        self._db[xenapi_class][vif_ref_new]['MAC'] = "00:00:00:00:00:00"
                        self._db[xenapi_class][vif_ref_new]['MAC_autogenerated'] = True
                    else:
                        self._db[xenapi_class][vif_ref_new]['MAC_autogenerated'] = False

                    self._db[xenapi_class][vif_ref_new]['ipv4_configuration_mode'] = "None"
                    self._db[xenapi_class][vif_ref_new]['ipv4_addresses'] = []
                    self._db[xenapi_class][vif_ref_new]['ipv4_gateway'] = ""
                    self._db[xenapi_class][vif_ref_new]['ipv6_configuration_mode'] = "None"
                    self._db[xenapi_class][vif_ref_new]['ipv6_addresses'] = []
                    self._db[xenapi_class][vif_ref_new]['ipv6_gateway'] = ""

                    self._db['VM'][vm_ref]['VIFs'].append(vif_ref_new)
                    self._db['network'][network_ref]['VIFs'].append(vif_ref_new)

                    if vm_guest_metrics_ref != "OpaqueRef:NULL":
                        vm_guest_metrics_networks = self._db['VM_guest_metrics'][vm_guest_metrics_ref]['networks']
                        vif_device = vif_record['device']
                        vif_mac = self._db[xenapi_class][vif_ref_new]['MAC']

                        vm_guest_metrics_networks['%s/ip' % vif_device] = ""
                        vm_guest_metrics_networks['%s/ipv6/0' % vif_device] = ("fe80:0000:0000:0000:%s%s:%sff:fe%s:%s%s" %
                                                                               ("%02x" % (int(vif_mac[0:2], 16) ^ 2),
                                                                                vif_mac[3:5],
                                                                                vif_mac[6:8],
                                                                                vif_mac[9:11],
                                                                                vif_mac[12:14],
                                                                                vif_mac[15:]))

                    return vif_ref_new
                elif xenapi_method == "plug":
                    self._db[xenapi_class][vif_ref]['currently_attached'] = True
                elif xenapi_method == "unplug":
                    self._db[xenapi_class][vif_ref]['currently_attached'] = False
                elif xenapi_method == "configure_ipv4":
                    vif_mode = params[1]
                    vif_address = params[2]
                    vif_gateway = params[3]

                    self._db[xenapi_class][vif_ref]['ipv4_configuration_mode'] = vif_mode
                    self._db[xenapi_class][vif_ref]['ipv4_addresses'] = [vif_address]
                    self._db[xenapi_class][vif_ref]['ipv4_gateway'] = vif_gateway

                    vm_ref = self._db[xenapi_class][vif_ref]['VM']
                    network_ref = self._db[xenapi_class][vif_ref]['network']
                    vif_device = self._db[xenapi_class][vif_ref]['device']
                    vm_guest_metrics_ref = self._db['VM'][vm_ref]['guest_metrics']

                    if vm_guest_metrics_ref != "OpaqueRef:NULL":
                        vm_guest_metrics_networks = self._db['VM_guest_metrics'][vm_guest_metrics_ref]['networks']

                        if vif_mode == "Static":
                            vm_guest_metrics_networks['%s/ip' % vif_device] = vif_address.split('/')[0]
                        else:
                            if self._db['network'][network_ref]['name_label'] == "Host internal management network":
                                if vif_ref in self._db['network'][network_ref]['assigned_ips']:
                                    vm_guest_metrics_networks['%s/ip' % vif_device] = self._db['network'][network_ref]['assigned_ips'][vif_ref]
                                else:
                                    vm_guest_metrics_networks['%s/ip' % vif_device] = '169.254.255.1'
                                    self._db['network'][network_ref]['assigned_ips'][vif_ref] = '169.254.255.1'
                            else:
                                vm_guest_metrics_networks['%s/ip' % vif_device] = ''
                elif xenapi_method == "configure_ipv6":
                    vif_mode = params[1]
                    vif_address = params[2]
                    vif_gateway = params[3]

                    self._db[xenapi_class][vif_ref]['ipv6_configuration_mode'] = vif_mode
                    self._db[xenapi_class][vif_ref]['ipv6_addresses'] = [vif_address]
                    self._db[xenapi_class][vif_ref]['ipv6_gateway'] = vif_gateway

                    vm_ref = self._db[xenapi_class][vif_ref]['VM']
                    network_ref = self._db[xenapi_class][vif_ref]['network']
                    vif_device = self._db[xenapi_class][vif_ref]['device']
                    vm_guest_metrics_ref = self._db['VM'][vm_ref]['guest_metrics']

                    if vm_guest_metrics_ref != "OpaqueRef:NULL":
                        vm_guest_metrics_networks = self._db['VM_guest_metrics'][vm_guest_metrics_ref]['networks']

                        if vif_mode == "Static":
                            vm_guest_metrics_networks['%s/ipv6/1' % vif_device] = ipaddress.ip_address(to_text(vif_address.split('/')[0])).exploded
                        else:
                            ipv6_key = "%s/ipv6/1" % vif_device

                            if ipv6_key in vm_guest_metrics_networks:
                                del vm_guest_metrics_networks[ipv6_key]
                elif xenapi_method == 'destroy':
                    vm_ref = self._db[xenapi_class][vif_ref]['VM']
                    network_ref = self._db[xenapi_class][vif_ref]['network']

                    self._db['VM'][vm_ref]['VIFs'].remove(vif_ref)
                    self._db['network'][network_ref]['VIFs'].remove(vif_ref)

                    del self._db[xenapi_class][vif_ref]
            elif xenapi_class == "task":
                task_ref = params[0]

                if task_ref not in self._db[xenapi_class]:
                    raise Failure(['HANDLE_INVALID', xenapi_class, task_ref])

                if xenapi_method == "get_status":
                    task_status = self._db[xenapi_class][task_ref]['status']

                    if task_status == "Pending":
                        async_method = self._db[xenapi_class][task_ref]['name-label'][6:]
                        async_method_params = self._db[xenapi_class][task_ref]['_params']
                        self.xenapi_request(async_method, async_method_params)
                        self._db[xenapi_class][task_ref]['status'] = "Success"

                    return task_status
                elif xenapi_method == 'destroy':
                    del self._db[xenapi_class][task_ref]
            else:
                # Silently ignore any other method.
                pass

    def __getattr__(self, name):
        if name == 'handle':
            return self._session
        elif name == 'xenapi':
            return _XenAPIMethodResolver(self.xenapi_request, None)
        elif name.startswith('login') or name.startswith('slave_local'):
            return lambda *params: self._login(name, params)
        elif name == 'logout':
            return self._logout


def xapi_local():
    return Session("http://_var_lib_xcp_xapi/")
