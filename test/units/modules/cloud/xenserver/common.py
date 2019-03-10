# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Bojan Vitnik <bvitnik@mainstream.rs>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os
import json
import copy


# Common cached fixture data loaded from files.
fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(file_name):
    """Loads and caches fixture data from files."""
    file_path = os.path.join(fixture_path, file_name)

    if file_path in fixture_data:
        return fixture_data[file_path]

    with open(file_path) as fixture:
        data = fixture.read()

    if file_path.endswith('.json'):
        data = json.loads(data)

    fixture_data[file_path] = data

    return data


def load_xenapi_db(file_name=None):
    """
    Loads a sample of XenAPI DB from file.
    """
    # We always use ansible-test-common-db.json as a base XenAPI DB sample.
    # Additional DB data is then loaded from file_name if specified.
    fake_xenapi_db_data = copy.deepcopy(load_fixture('ansible-test-common-db.json'))

    # If file_name for additional XenAPI DB data is passed, update base
    # XenAPI DB data down to a field level. Additional XenAPI DB data can
    # override base data at field level.
    if file_name:
        for xenapi_class in list(load_fixture(file_name).keys()):
            if xenapi_class not in fake_xenapi_db_data:
                fake_xenapi_db_data[xenapi_class] = copy.deepcopy(load_fixture(file_name)[xenapi_class])
            else:
                for obj_ref in list(load_fixture(file_name)[xenapi_class].keys()):
                    if obj_ref not in fake_xenapi_db_data[xenapi_class]:
                        fake_xenapi_db_data[xenapi_class][obj_ref] = copy.deepcopy(load_fixture(file_name)[xenapi_class][obj_ref])
                    else:
                        for field in list(load_fixture(file_name)[xenapi_class][obj_ref].keys()):
                            fake_xenapi_db_data[xenapi_class][obj_ref][field] = copy.deepcopy(load_fixture(file_name)[xenapi_class][obj_ref][field])

    return fake_xenapi_db_data


# Following are helper functions for expansion of module parameters, one per
# module. They simulate AnsibleModule parameter parser. Non specified module
# parameters are added with value None or default depending on argument_spec.
# That way individual functions in modules can be tested with non fully
# specified module parameters alowing testcases to be reused for testing both
# individial functions and modules themselves. These are planned for removal
# once all the modules have been converted to use module.params.get() instead
# of module.params[].

def xenserver_guest_expand_params(params):
    """Expands xenserver_guest testcase module parameters."""
    for param_name in ['name', 'name_desc', 'uuid', 'template', 'template_uuid', 'folder',
                       'hardware', 'disks', 'cdrom', 'networks', 'home_server', 'custom_params']:
        if param_name not in params:
            params[param_name] = None

    if 'state' not in params:
        params['state'] = "present"

    if 'state_change_timeout' not in params:
        params['state_change_timeout'] = 0

    for param_name in ['is_template', 'wait_for_ip_address', 'linked_clone', 'force']:
        if param_name not in params:
            params[param_name] = False

    if params['hardware'] is not None:
        for param_name in ['num_cpus', 'num_cpu_cores_per_socket', 'memory_mb']:
            if param_name not in params['hardware']:
                params['hardware'][param_name] = None

    if params['cdrom'] is not None:
        for param_name in ['type', 'iso_name']:
            if param_name not in params['cdrom']:
                params['cdrom'][param_name] = None

    if params['disks']:
        for disk_params in params['disks']:
            for param_name in ['size', 'size_tb', 'size_gb', 'size_mb', 'size_kb', 'size_b', 'name', 'name_desc', 'sr', 'sr_uuid']:
                if param_name not in disk_params:
                    disk_params[param_name] = None

    if params['networks']:
        for network_params in params['networks']:
            for param_name in ['name', 'mac', 'type', 'ip', 'netmask', 'gateway', 'type6', 'ip6', 'gateway6']:
                if param_name not in network_params:
                    network_params[param_name] = None

    if params['custom_params']:
        for custom_params in params['custom_params']:
            for param_name in ['key', 'value']:
                if param_name not in custom_params:
                    custom_params[param_name] = None


def xenserver_guest_info_expand_params(params):
    """Expands xenserver_guest_info testcase module parameters."""
    for param_name in ['name', 'uuid']:
        if param_name not in params:
            params[param_name] = None


def xenserver_guest_powerstate_expand_params(params):
    """Expands xenserver_guest_powerstate testcase module parameters."""
    for param_name in ['name', 'uuid']:
        if param_name not in params:
            params[param_name] = None

    if 'state' not in params:
        params['state'] = "present"

    if 'state_change_timeout' not in params:
        params['state_change_timeout'] = 0

    if 'wait_for_ip_address' not in params:
        params['wait_for_ip_address'] = False
