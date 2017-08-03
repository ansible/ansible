# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
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
import os
import ssl
import time

try:
    # requests is required for exception handling of the ConnectionError
    import requests
    from pyVim import connect
    from pyVmomi import vim
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six import integer_types, iteritems, string_types


class TaskError(Exception):
    pass


def wait_for_task(task):

    while True:
        if task.info.state == vim.TaskInfo.State.success:
            return True, task.info.result
        if task.info.state == vim.TaskInfo.State.error:
            try:
                raise TaskError(task.info.error)
            except AttributeError:
                raise TaskError("An unknown error has occurred")
        if task.info.state == vim.TaskInfo.State.running:
            time.sleep(15)
        if task.info.state == vim.TaskInfo.State.queued:
            time.sleep(15)


def find_obj(content, vimtype, name, first=True):
    container = content.viewManager.CreateContainerView(container=content.rootFolder, recursive=True, type=vimtype)
    obj_list = container.view
    container.Destroy()

    # Backward compatible with former get_obj() function
    if name is None:
        if obj_list:
            return obj_list[0]
        return None

    # Select the first match
    if first is True:
        for obj in obj_list:
            if obj.name == name:
                return obj

        # If no object found, return None
        return None

    # Return all matching objects if needed
    return [obj for obj in obj_list if obj.name == name]


def find_dvspg_by_name(dv_switch, portgroup_name):

    portgroups = dv_switch.portgroup

    for pg in portgroups:
        if pg.name == portgroup_name:
            return pg

    return None


def find_entity_child_by_path(content, entityRootFolder, path):

    entity = entityRootFolder
    searchIndex = content.searchIndex
    paths = path.split("/")
    try:
        for path in paths:
            entity = searchIndex.FindChild(entity, path)

        if entity.name == paths[-1]:
            return entity
    except:
        pass

    return None


# Maintain for legacy, or remove with 2.1 ?
# Should be replaced with find_cluster_by_name
def find_cluster_by_name_datacenter(datacenter, cluster_name):

    host_folder = datacenter.hostFolder
    for folder in host_folder.childEntity:
        if folder.name == cluster_name:
            return folder
    return None


def find_cluster_by_name(content, cluster_name, datacenter=None):

    if datacenter:
        folder = datacenter.hostFolder
    else:
        folder = content.rootFolder

    clusters = get_all_objs(content, [vim.ClusterComputeResource], folder)
    for cluster in clusters:
        if cluster.name == cluster_name:
            return cluster

    return None


def find_datacenter_by_name(content, datacenter_name):

    datacenters = get_all_objs(content, [vim.Datacenter])
    for dc in datacenters:
        if dc.name == datacenter_name:
            return dc

    return None


def find_datastore_by_name(content, datastore_name):

    datastores = get_all_objs(content, [vim.Datastore])
    for ds in datastores:
        if ds.name == datastore_name:
            return ds

    return None


def find_dvs_by_name(content, switch_name):

    vmware_distributed_switches = get_all_objs(content, [vim.dvs.VmwareDistributedVirtualSwitch])
    for dvs in vmware_distributed_switches:
        if dvs.name == switch_name:
            return dvs
    return None


def find_hostsystem_by_name(content, hostname):

    host_system = get_all_objs(content, [vim.HostSystem])
    for host in host_system:
        if host.name == hostname:
            return host
    return None


def find_vm_by_id(content, vm_id, vm_id_type="vm_name", datacenter=None, cluster=None, folder=None, match_first=False):
    """ UUID is unique to a VM, every other id returns the first match. """
    si = content.searchIndex
    vm = None

    if vm_id_type == 'dns_name':
        vm = si.FindByDnsName(datacenter=datacenter, dnsName=vm_id, vmSearch=True)
    elif vm_id_type == 'uuid':
        # Search By BIOS UUID rather than instance UUID
        vm = si.FindByUuid(datacenter=datacenter, instanceUuid=False, uuid=vm_id, vmSearch=True)
    elif vm_id_type == 'ip':
        vm = si.FindByIp(datacenter=datacenter, ip=vm_id, vmSearch=True)
    elif vm_id_type == 'vm_name':
        folder = None
        if cluster:
            folder = cluster
        elif datacenter:
            folder = datacenter.hostFolder
        vm = find_vm_by_name(content, vm_id, folder)
    elif vm_id_type == 'inventory_path':
        searchpath = folder
        # get all objects for this path
        f_obj = si.FindByInventoryPath(searchpath)
        if f_obj:
            if isinstance(f_obj, vim.Datacenter):
                f_obj = f_obj.vmFolder
            for c_obj in f_obj.childEntity:
                if not isinstance(c_obj, vim.VirtualMachine):
                    continue
                if c_obj.name == vm_id:
                    vm = c_obj
                    if match_first:
                        break
    return vm


def find_vm_by_name(content, vm_name, folder=None, recurse=True):

    vms = get_all_objs(content, [vim.VirtualMachine], folder, recurse=recurse)
    for vm in vms:
        if vm.name == vm_name:
            return vm
    return None


def find_host_portgroup_by_name(host, portgroup_name):

    for portgroup in host.config.network.portgroup:
        if portgroup.spec.name == portgroup_name:
            return portgroup
    return None


def compile_folder_path_for_object(vobj):
    """ make a /vm/foo/bar/baz like folder path for an object """

    paths = []
    if isinstance(vobj, vim.Folder):
        paths.append(vobj.name)

    thisobj = vobj
    while hasattr(thisobj, 'parent'):
        thisobj = thisobj.parent
        if isinstance(thisobj, vim.Folder):
            paths.append(thisobj.name)
    paths.reverse()
    if paths[0] == 'Datacenters':
        paths.remove('Datacenters')
    return '/' + '/'.join(paths)


def _get_vm_prop(vm, attributes):
    """Safely get a property or return None"""
    result = vm
    for attribute in attributes:
        try:
            result = getattr(result, attribute)
        except (AttributeError, IndexError):
            return None
    return result


def gather_vm_facts(content, vm):
    """ Gather facts from vim.VirtualMachine object. """
    facts = {
        'module_hw': True,
        'hw_name': vm.config.name,
        'hw_power_status': vm.summary.runtime.powerState,
        'hw_guest_full_name': vm.summary.guest.guestFullName,
        'hw_guest_id': vm.summary.guest.guestId,
        'hw_product_uuid': vm.config.uuid,
        'hw_processor_count': vm.config.hardware.numCPU,
        'hw_memtotal_mb': vm.config.hardware.memoryMB,
        'hw_interfaces': [],
        'guest_tools_status': _get_vm_prop(vm, ('guest', 'toolsRunningStatus')),
        'guest_tools_version': _get_vm_prop(vm, ('guest', 'toolsVersion')),
        'ipv4': None,
        'ipv6': None,
        'annotation': vm.config.annotation,
        'customvalues': {},
        'snapshots': [],
        'current_snapshot': None,
    }

    cfm = content.customFieldsManager
    # Resolve custom values
    for value_obj in vm.summary.customValue:
        kn = value_obj.key
        if cfm is not None and cfm.field:
            for f in cfm.field:
                if f.key == value_obj.key:
                    kn = f.name
                    # Exit the loop immediately, we found it
                    break

        facts['customvalues'][kn] = value_obj.value

    net_dict = {}
    vmnet = _get_vm_prop(vm, ('guest', 'net'))
    if vmnet:
        for device in vmnet:
            net_dict[device.macAddress] = list(device.ipAddress)

    for k, v in iteritems(net_dict):
        for ipaddress in v:
            if ipaddress:
                if '::' in ipaddress:
                    facts['ipv6'] = ipaddress
                else:
                    facts['ipv4'] = ipaddress

    ethernet_idx = 0
    for idx, entry in enumerate(vm.config.hardware.device):
        if not hasattr(entry, 'macAddress'):
            continue

        if entry.macAddress:
            mac_addr = entry.macAddress
            mac_addr_dash = mac_addr.replace(':', '-')
        else:
            mac_addr = mac_addr_dash = None

        factname = 'hw_eth' + str(ethernet_idx)
        facts[factname] = {
            'addresstype': entry.addressType,
            'label': entry.deviceInfo.label,
            'macaddress': mac_addr,
            'ipaddresses': net_dict.get(entry.macAddress, None),
            'macaddress_dash': mac_addr_dash,
            'summary': entry.deviceInfo.summary,
        }
        facts['hw_interfaces'].append('eth' + str(ethernet_idx))
        ethernet_idx += 1

    snapshot_facts = list_snapshots(vm)
    if 'snapshots' in snapshot_facts:
        facts['snapshots'] = snapshot_facts['snapshots']
        facts['current_snapshot'] = snapshot_facts['current_snapshot']
    return facts


def deserialize_snapshot_obj(obj):
    return {'id': obj.id,
            'name': obj.name,
            'description': obj.description,
            'creation_time': obj.createTime,
            'state': obj.state}


def list_snapshots_recursively(snapshots):
    snapshot_data = []
    for snapshot in snapshots:
        snapshot_data.append(deserialize_snapshot_obj(snapshot))
        snapshot_data = snapshot_data + list_snapshots_recursively(snapshot.childSnapshotList)
    return snapshot_data


def get_current_snap_obj(snapshots, snapob):
    snap_obj = []
    for snapshot in snapshots:
        if snapshot.snapshot == snapob:
            snap_obj.append(snapshot)
        snap_obj = snap_obj + get_current_snap_obj(snapshot.childSnapshotList, snapob)
    return snap_obj


def list_snapshots(vm):
    result = {}
    snapshot = _get_vm_prop(vm, ('vm', 'snapshot'))
    if not snapshot:
        return result
    if vm.snapshot is None:
        return result

    result['snapshots'] = list_snapshots_recursively(vm.snapshot.rootSnapshotList)
    current_snapref = vm.snapshot.currentSnapshot
    current_snap_obj = get_current_snap_obj(vm.snapshot.rootSnapshotList, current_snapref)
    result['current_snapshot'] = deserialize_snapshot_obj(current_snap_obj[0])

    return result


def vmware_argument_spec():

    return dict(
        hostname=dict(type='str', required=True),
        username=dict(type='str', aliases=['user', 'admin'], required=True),
        password=dict(type='str', aliases=['pass', 'pwd'], required=True, no_log=True),
        validate_certs=dict(type='bool', required=False, default=True),
    )


def connect_to_api(module, disconnect_atexit=True):

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    validate_certs = module.params['validate_certs']

    if validate_certs and not hasattr(ssl, 'SSLContext'):
        module.fail_json(msg='pyVim does not support changing verification mode with python < 2.7.9. Either update '
                             'python or or use validate_certs=false')

    try:
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password)
    except vim.fault.InvalidLogin as invalid_login:
        module.fail_json(msg=invalid_login.msg, apierror=str(invalid_login))
    except (requests.ConnectionError, ssl.SSLError) as connection_error:
        if '[SSL: CERTIFICATE_VERIFY_FAILED]' in str(connection_error) and not validate_certs:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
            service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password, sslContext=context)
        else:
            module.fail_json(msg="Unable to connect to vCenter or ESXi API on TCP/443.", apierror=str(connection_error))
    except:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password, sslContext=context)

    # Disabling atexit should be used in special cases only.
    # Such as IP change of the ESXi host which removes the connection anyway.
    # Also removal significantly speeds up the return of the module
    if disconnect_atexit:
        atexit.register(connect.Disconnect, service_instance)
    return service_instance.RetrieveContent()


def get_all_objs(content, vimtype, folder=None, recurse=True):
    if not folder:
        folder = content.rootFolder

    obj = {}
    container = content.viewManager.CreateContainerView(folder, vimtype, recurse)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    return obj


def fetch_file_from_guest(module, content, vm, username, password, src, dest):
    """ Use VMWare's filemanager api to fetch a file over http """

    result = {'failed': False}

    tools_status = vm.guest.toolsStatus
    if tools_status == 'toolsNotInstalled' or tools_status == 'toolsNotRunning':
        result['failed'] = True
        result['msg'] = "VMwareTools is not installed or is not running in the guest"
        return result

    # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/NamePasswordAuthentication.rst
    creds = vim.vm.guest.NamePasswordAuthentication(
        username=username, password=password
    )

    # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/FileManager/FileTransferInformation.rst
    fti = content.guestOperationsManager.fileManager. \
        InitiateFileTransferFromGuest(vm, creds, src)

    result['size'] = fti.size
    result['url'] = fti.url

    # Use module_utils to fetch the remote url returned from the api
    rsp, info = fetch_url(module, fti.url, use_proxy=False,
                          force=True, last_mod_time=None,
                          timeout=10, headers=None)

    # save all of the transfer data
    for k, v in iteritems(info):
        result[k] = v

    # exit early if xfer failed
    if info['status'] != 200:
        result['failed'] = True
        return result

    # attempt to read the content and write it
    try:
        with open(dest, 'wb') as f:
            f.write(rsp.read())
    except Exception as e:
        result['failed'] = True
        result['msg'] = str(e)

    return result


def push_file_to_guest(module, content, vm, username, password, src, dest, overwrite=True):
    """ Use VMWare's filemanager api to fetch a file over http """

    result = {'failed': False}

    tools_status = vm.guest.toolsStatus
    if tools_status == 'toolsNotInstalled' or tools_status == 'toolsNotRunning':
        result['failed'] = True
        result['msg'] = "VMwareTools is not installed or is not running in the guest"
        return result

    # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/NamePasswordAuthentication.rst
    creds = vim.vm.guest.NamePasswordAuthentication(
        username=username, password=password
    )

    # the api requires a filesize in bytes
    fdata = None
    try:
        # filesize = os.path.getsize(src)
        filesize = os.stat(src).st_size
        with open(src, 'rb') as f:
            fdata = f.read()
        result['local_filesize'] = filesize
    except Exception as e:
        result['failed'] = True
        result['msg'] = "Unable to read src file: %s" % str(e)
        return result

    # https://www.vmware.com/support/developer/converter-sdk/conv60_apireference/vim.vm.guest.FileManager.html#initiateFileTransferToGuest
    file_attribute = vim.vm.guest.FileManager.FileAttributes()
    url = content.guestOperationsManager.fileManager. \
        InitiateFileTransferToGuest(vm, creds, dest, file_attribute,
                                    filesize, overwrite)

    # PUT the filedata to the url ...
    rsp, info = fetch_url(module, url, method="put", data=fdata,
                          use_proxy=False, force=True, last_mod_time=None,
                          timeout=10, headers=None)

    result['msg'] = str(rsp.read())

    # save all of the transfer data
    for k, v in iteritems(info):
        result[k] = v

    return result


def run_command_in_guest(content, vm, username, password, program_path, program_args, program_cwd, program_env):

    result = {'failed': False}

    tools_status = vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        result['failed'] = True
        result['msg'] = "VMwareTools is not installed or is not running in the guest"
        return result

    # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/NamePasswordAuthentication.rst
    creds = vim.vm.guest.NamePasswordAuthentication(
        username=username, password=password
    )

    try:
        # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/ProcessManager.rst
        pm = content.guestOperationsManager.processManager
        # https://www.vmware.com/support/developer/converter-sdk/conv51_apireference/vim.vm.guest.ProcessManager.ProgramSpec.html
        ps = vim.vm.guest.ProcessManager.ProgramSpec(
            # programPath=program,
            # arguments=args
            programPath=program_path,
            arguments=program_args,
            workingDirectory=program_cwd,
        )

        res = pm.StartProgramInGuest(vm, creds, ps)
        result['pid'] = res
        pdata = pm.ListProcessesInGuest(vm, creds, [res])

        # wait for pid to finish
        while not pdata[0].endTime:
            time.sleep(1)
            pdata = pm.ListProcessesInGuest(vm, creds, [res])

        result['owner'] = pdata[0].owner
        result['startTime'] = pdata[0].startTime.isoformat()
        result['endTime'] = pdata[0].endTime.isoformat()
        result['exitCode'] = pdata[0].exitCode
        if result['exitCode'] != 0:
            result['failed'] = True
            result['msg'] = "program exited non-zero"
        else:
            result['msg'] = "program completed successfully"

    except Exception as e:
        result['msg'] = str(e)
        result['failed'] = True

    return result


def serialize_spec(clonespec):
    """Serialize a clonespec or a relocation spec"""
    data = {}
    attrs = dir(clonespec)
    attrs = [x for x in attrs if not x.startswith('_')]
    for x in attrs:
        xo = getattr(clonespec, x)
        if callable(xo):
            continue
        xt = type(xo)
        if xo is None:
            data[x] = None
        elif issubclass(xt, list):
            data[x] = []
            for xe in xo:
                data[x].append(serialize_spec(xe))
        elif issubclass(xt, string_types + integer_types + (float, bool)):
            data[x] = xo
        elif issubclass(xt, dict):
            data[x] = {}
            for k, v in xo.items():
                data[x][k] = serialize_spec(v)
        elif isinstance(xo, vim.vm.ConfigSpec):
            data[x] = serialize_spec(xo)
        elif isinstance(xo, vim.vm.RelocateSpec):
            data[x] = serialize_spec(xo)
        elif isinstance(xo, vim.vm.device.VirtualDisk):
            data[x] = serialize_spec(xo)
        elif isinstance(xo, vim.Description):
            data[x] = {
                'dynamicProperty': serialize_spec(xo.dynamicProperty),
                'dynamicType': serialize_spec(xo.dynamicType),
                'label': serialize_spec(xo.label),
                'summary': serialize_spec(xo.summary),
            }
        elif hasattr(xo, 'name'):
            data[x] = str(xo) + ':' + xo.name
        elif isinstance(xo, vim.vm.ProfileSpec):
            pass
        else:
            data[x] = str(xt)

    return data
