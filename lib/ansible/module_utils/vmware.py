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


try:
    import atexit
    import time
    # requests is required for exception handling of the ConnectionError
    import requests
    from pyVim import connect
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


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


def find_dvspg_by_name(dv_switch, portgroup_name):

    portgroups = dv_switch.portgroup

    for pg in portgroups:
        if pg.name == portgroup_name:
            return pg

    return None


def find_cluster_by_name_datacenter(datacenter, cluster_name):

    host_folder = datacenter.hostFolder
    for folder in host_folder.childEntity:
        if folder.name == cluster_name:
            return folder
    return None


def find_datacenter_by_name(content, datacenter_name):

    datacenters = get_all_objs(content, [vim.Datacenter])
    for dc in datacenters:
        if dc.name == datacenter_name:
            return dc

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


def vmware_argument_spec():

    return dict(
        hostname=dict(type='str', required=True),
        username=dict(type='str', aliases=['user', 'admin'], required=True),
        password=dict(type='str', aliases=['pass', 'pwd'], required=True, no_log=True),
    )


def connect_to_api(module, disconnect_atexit=True):

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    try:
        service_instance = connect.SmartConnect(host=hostname, user=username, pwd=password)

        # Disabling atexit should be used in special cases only.
        # Such as IP change of the ESXi host which removes the connection anyway.
        # Also removal significantly speeds up the return of the module

        if disconnect_atexit:
            atexit.register(connect.Disconnect, service_instance)
        return service_instance.RetrieveContent()
    except vim.fault.InvalidLogin, invalid_login:
        module.fail_json(msg=invalid_login.msg, apierror=str(invalid_login))
    except requests.ConnectionError, connection_error:
        module.fail_json(msg="Unable to connect to vCenter or ESXi API on TCP/443.", apierror=str(connection_error))


def get_all_objs(content, vimtype):

    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    return obj
