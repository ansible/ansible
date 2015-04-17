#!/bin/python
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


def task_success(task):
    return True


def task_running(task):
    time.sleep(15)
    return False


def task_error(task):

    try:
        raise TaskError(task.info.error)
    except AttributeError:
        raise TaskError("Unknown error has occurred")


def task_queued(task):
    time.sleep(15)
    return False


def wait_for_task(task):

    task_state = {
        vim.TaskInfo.State.success: task_success,
        vim.TaskInfo.State.running: task_running,
        vim.TaskInfo.State.queued: task_queued,
        vim.TaskInfo.State.error: task_error,
        }

    while True:
        try:
            is_finished = task_state[task.info.state](task)
            if is_finished:
                return True, task.info.result
        # This exception should be handled in the module that calls this method
        # and fail with an appropriate message to module.fail_json()
        except TaskError:
            raise


def find_dvspg_by_name(dv_switch, portgroup_name):
    portgroups = dv_switch.portgroup

    for pg in portgroups:
        if pg.name == portgroup_name:
            return pg

    return None


def find_cluster_by_name_datacenter(datacenter, cluster_name):
    try:
        host_folder = datacenter.hostFolder
        for folder in host_folder.childEntity:
            if folder.name == cluster_name:
                return folder
        return None
    # This exception should be handled in the module that calls this method
    # and fail with an appropriate message to module.fail_json()
    except vmodl.MethodFault:
        raise


def find_datacenter_by_name(content, datacenter_name, throw=True):
    try:
        datacenters = get_all_objs(content, [vim.Datacenter])
        for dc in datacenters:
            if dc.name == datacenter_name:
                return dc

        return None
    # This exception should be handled in the module that calls this method
    # and fail with an appropriate message to module.fail_json()
    except vmodl.MethodFault:
        raise


def find_dvs_by_name(content, switch_name):
    try:
        vmware_distributed_switches = get_all_objs(content, [vim.dvs.VmwareDistributedVirtualSwitch])
        for dvs in vmware_distributed_switches:
            if dvs.name == switch_name:
                return dvs
        return None
    # This exception should be handled in the module that calls this method
    # and fail with an appropriate message to module.fail_json()
    except vmodl.MethodFault:
        raise


def find_hostsystem_by_name(content, hostname):
    try:
        host_system = get_all_objs(content, [vim.HostSystem])
        for host in host_system:
            if host.name == hostname:
                return host
        return None
    # This exception should be handled in the module that calls this method
    # and fail with an appropriate message to module.fail_json()
    except vmodl.MethodFault:
        raise


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
    except vim.fault.InvalidLogin as invalid_login:
        module.fail_json(msg=invalid_login.msg)
    except requests.ConnectionError:
        module.fail_json(msg="Unable to connect to vCenter or ESXi API on TCP/443.")


def get_all_objs(content, vimtype):
    try:
        obj = {}
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for managed_object_ref in container.view:
            obj.update({managed_object_ref: managed_object_ref.name})
        return obj
    # This exception should be handled in the module that calls this method
    # and fail with an appropriate message to module.fail_json()
    except vmodl.MethodFault:
        raise