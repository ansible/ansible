#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Huawei
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

###############################################################################
# Documentation
###############################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ["preview"],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: hwc_ecs_instance
description:
    - instance management.
short_description: Creates a resource of Ecs/Instance in Huawei Cloud
version_added: '2.10'
author: Huawei Inc. (@huaweicloud)
requirements:
    - keystoneauth1 >= 3.6.0
options:
    state:
        description:
            - Whether the given object should exist in Huawei Cloud.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    timeouts:
        description:
            - The timeouts for each operations.
        type: dict
        suboptions:
            create:
                description:
                    - The timeouts for create operation.
                type: str
                default: '30m'
            update:
                description:
                    - The timeouts for update operation.
                type: str
                default: '30m'
            delete:
                description:
                    - The timeouts for delete operation.
                type: str
                default: '30m'
    availability_zone:
        description:
            - Specifies the name of the AZ where the ECS is located.
        type: str
        required: true
    flavor_name:
        description:
            - Specifies the name of the system flavor.
        type: str
        required: true
    image_id:
        description:
            - Specifies the ID of the system image.
        type: str
        required: true
    name:
        description:
            - Specifies the ECS name. Value requirements consists of 1 to 64
              characters, including letters, digits, underscores C(_), hyphens
              (-), periods (.).
        type: str
        required: true
    nics:
        description:
            - Specifies the NIC information of the ECS. Constraints the
              network of the NIC must belong to the VPC specified by vpc_id. A
              maximum of 12 NICs can be attached to an ECS.
        type: list
        required: true
        suboptions:
            ip_address:
                description:
                    - Specifies the IP address of the NIC. The value is an IPv4
                      address. Its value must be an unused IP
                      address in the network segment of the subnet.
                type: str
                required: true
            subnet_id:
                description:
                    - Specifies the ID of subnet.
                type: str
                required: true
    root_volume:
        description:
            - Specifies the configuration of the ECS's system disks.
        type: dict
        required: true
        suboptions:
            volume_type:
                description:
                    - Specifies the ECS system disk type.
                    - SATA is common I/O disk type.
                    - SAS is high I/O disk type.
                    - SSD is ultra-high I/O disk type.
                    - co-p1 is high I/O (performance-optimized I) disk type.
                    - uh-l1 is ultra-high I/O (latency-optimized) disk type.
                    - NOTE is For HANA, HL1, and HL2 ECSs, use co-p1 and uh-l1
                      disks. For other ECSs, do not use co-p1 or uh-l1 disks.
                type: str
                required: true
            size:
                description:
                    - Specifies the system disk size, in GB. The value range is
                      1 to 1024. The system disk size must be
                      greater than or equal to the minimum system disk size
                      supported by the image (min_disk attribute of the image).
                      If this parameter is not specified or is set to 0, the
                      default system disk size is the minimum value of the
                      system disk in the image (min_disk attribute of the
                      image).
                type: int
                required: false
            snapshot_id:
                description:
                    - Specifies the snapshot ID or ID of the original data disk
                      contained in the full-ECS image.
                type: str
                required: false
    vpc_id:
        description:
            - Specifies the ID of the VPC to which the ECS belongs.
        type: str
        required: true
    admin_pass:
        description:
            - Specifies the initial login password of the administrator account
              for logging in to an ECS using password authentication. The Linux
              administrator is root, and the Windows administrator is
              Administrator. Password complexity requirements, consists of 8 to
              26 characters. The password must contain at least three of the
              following character types 'uppercase letters, lowercase letters,
              digits, and special characters (!@$%^-_=+[{}]:,./?)'. The password
              cannot contain the username or the username in reverse. The
              Windows ECS password cannot contain the username, the username in
              reverse, or more than two consecutive characters in the username.
        type: str
        required: false
    data_volumes:
        description:
            - Specifies the data disks of ECS instance.
        type: list
        required: false
        suboptions:
            volume_id:
                description:
                    - Specifies the disk ID.
                type: str
                required: true
            device:
                description:
                    - Specifies the disk device name.
                type: str
                required: false
    description:
        description:
            - Specifies the description of an ECS, which is a null string by
              default. Can contain a maximum of 85 characters. Cannot contain
              special characters, such as < and >.
        type: str
        required: false
    eip_id:
        description:
            - Specifies the ID of the elastic IP address assigned to the ECS.
              Only elastic IP addresses in the DOWN state can be
              assigned.
        type: str
        required: false
    enable_auto_recovery:
        description:
            - Specifies whether automatic recovery is enabled on the ECS.
        type: bool
        required: false
    enterprise_project_id:
        description:
            - Specifies the ID of the enterprise project to which the ECS
              belongs.
        type: str
        required: false
    security_groups:
        description:
            - Specifies the security groups of the ECS. If this
              parameter is left blank, the default security group is bound to
              the ECS by default.
        type: list
        required: false
    server_metadata:
        description:
            - Specifies the metadata of ECS to be created.
        type: dict
        required: false
    server_tags:
        description:
            - Specifies the tags of an ECS. When you create ECSs, one ECS
              supports up to 10 tags.
        type: dict
        required: false
    ssh_key_name:
        description:
            - Specifies the name of the SSH key used for logging in to the ECS.
        type: str
        required: false
    user_data:
        description:
            - Specifies the user data to be injected during the ECS creation
              process. Text, text files, and gzip files can be injected.
              The content to be injected must be encoded with
              base64. The maximum size of the content to be injected (before
              encoding) is 32 KB. For Linux ECSs, this parameter does not take
              effect when adminPass is used.
        type: str
        required: false
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create an ecs instance
- name: create a vpc
  hwc_network_vpc:
    cidr: "192.168.100.0/24"
    name: "ansible_network_vpc_test"
  register: vpc
- name: create a subnet
  hwc_vpc_subnet:
    gateway_ip: "192.168.100.32"
    name: "ansible_network_subnet_test"
    dhcp_enable: true
    vpc_id: "{{ vpc.id }}"
    cidr: "192.168.100.0/26"
  register: subnet
- name: create a eip
  hwc_vpc_eip:
    dedicated_bandwidth:
      charge_mode: "traffic"
      name: "ansible_test_dedicated_bandwidth"
      size: 1
    type: "5_bgp"
  register: eip
- name: create a disk
  hwc_evs_disk:
    availability_zone: "cn-north-1a"
    name: "ansible_evs_disk_test"
    volume_type: "SATA"
    size: 10
  register: disk
- name: create an instance
  hwc_ecs_instance:
    data_volumes:
      - volume_id: "{{ disk.id }}"
    enable_auto_recovery: false
    eip_id: "{{ eip.id }}"
    name: "ansible_ecs_instance_test"
    availability_zone: "cn-north-1a"
    nics:
      - subnet_id: "{{ subnet.id }}"
        ip_address: "192.168.100.33"
      - subnet_id: "{{ subnet.id }}"
        ip_address: "192.168.100.34"
    server_tags:
      my_server: "my_server"
    image_id: "8da46d6d-6079-4e31-ad6d-a7167efff892"
    flavor_name: "s3.small.1"
    vpc_id: "{{ vpc.id }}"
    root_volume:
      volume_type: "SAS"
'''

RETURN = '''
    availability_zone:
        description:
            - Specifies the name of the AZ where the ECS is located.
        type: str
        returned: success
    flavor_name:
        description:
            - Specifies the name of the system flavor.
        type: str
        returned: success
    image_id:
        description:
            - Specifies the ID of the system image.
        type: str
        returned: success
    name:
        description:
            - Specifies the ECS name. Value requirements "Consists of 1 to 64
              characters, including letters, digits, underscores C(_), hyphens
              (-), periods (.)".
        type: str
        returned: success
    nics:
        description:
            - Specifies the NIC information of the ECS. The
              network of the NIC must belong to the VPC specified by vpc_id. A
              maximum of 12 NICs can be attached to an ECS.
        type: list
        returned: success
        contains:
            ip_address:
                description:
                    - Specifies the IP address of the NIC. The value is an IPv4
                      address. Its value must be an unused IP
                      address in the network segment of the subnet.
                type: str
                returned: success
            subnet_id:
                description:
                    - Specifies the ID of subnet.
                type: str
                returned: success
            port_id:
                description:
                    - Specifies the port ID corresponding to the IP address.
                type: str
                returned: success
    root_volume:
        description:
            - Specifies the configuration of the ECS's system disks.
        type: dict
        returned: success
        contains:
            volume_type:
                description:
                    - Specifies the ECS system disk type.
                    - SATA is common I/O disk type.
                    - SAS is high I/O disk type.
                    - SSD is ultra-high I/O disk type.
                    - co-p1 is high I/O (performance-optimized I) disk type.
                    - uh-l1 is ultra-high I/O (latency-optimized) disk type.
                    - NOTE is For HANA, HL1, and HL2 ECSs, use co-p1 and uh-l1
                      disks. For other ECSs, do not use co-p1 or uh-l1 disks.
                type: str
                returned: success
            size:
                description:
                    - Specifies the system disk size, in GB. The value range is
                      1 to 1024. The system disk size must be
                      greater than or equal to the minimum system disk size
                      supported by the image (min_disk attribute of the image).
                      If this parameter is not specified or is set to 0, the
                      default system disk size is the minimum value of the
                      system disk in the image (min_disk attribute of the
                      image).
                type: int
                returned: success
            snapshot_id:
                description:
                    - Specifies the snapshot ID or ID of the original data disk
                      contained in the full-ECS image.
                type: str
                returned: success
            device:
                description:
                    - Specifies the disk device name.
                type: str
                returned: success
            volume_id:
                description:
                    - Specifies the disk ID.
                type: str
                returned: success
    vpc_id:
        description:
            - Specifies the ID of the VPC to which the ECS belongs.
        type: str
        returned: success
    admin_pass:
        description:
            - Specifies the initial login password of the administrator account
              for logging in to an ECS using password authentication. The Linux
              administrator is root, and the Windows administrator is
              Administrator. Password complexity requirements consists of 8 to
              26 characters. The password must contain at least three of the
              following character types "uppercase letters, lowercase letters,
              digits, and special characters (!@$%^-_=+[{}]:,./?)". The password
              cannot contain the username or the username in reverse. The
              Windows ECS password cannot contain the username, the username in
              reverse, or more than two consecutive characters in the username.
        type: str
        returned: success
    data_volumes:
        description:
            - Specifies the data disks of ECS instance.
        type: list
        returned: success
        contains:
            volume_id:
                description:
                    - Specifies the disk ID.
                type: str
                returned: success
            device:
                description:
                    - Specifies the disk device name.
                type: str
                returned: success
    description:
        description:
            - Specifies the description of an ECS, which is a null string by
              default. Can contain a maximum of 85 characters. Cannot contain
              special characters, such as < and >.
        type: str
        returned: success
    eip_id:
        description:
            - Specifies the ID of the elastic IP address assigned to the ECS.
              Only elastic IP addresses in the DOWN state can be assigned.
        type: str
        returned: success
    enable_auto_recovery:
        description:
            - Specifies whether automatic recovery is enabled on the ECS.
        type: bool
        returned: success
    enterprise_project_id:
        description:
            - Specifies the ID of the enterprise project to which the ECS
              belongs.
        type: str
        returned: success
    security_groups:
        description:
            - Specifies the security groups of the ECS. If this parameter is left
              blank, the default security group is bound to the ECS by default.
        type: list
        returned: success
    server_metadata:
        description:
            - Specifies the metadata of ECS to be created.
        type: dict
        returned: success
    server_tags:
        description:
            - Specifies the tags of an ECS. When you create ECSs, one ECS
              supports up to 10 tags.
        type: dict
        returned: success
    ssh_key_name:
        description:
            - Specifies the name of the SSH key used for logging in to the ECS.
        type: str
        returned: success
    user_data:
        description:
            - Specifies the user data to be injected during the ECS creation
              process. Text, text files, and gzip files can be injected.
              The content to be injected must be encoded with base64. The maximum
              size of the content to be injected (before encoding) is 32 KB. For
              Linux ECSs, this parameter does not take effect when adminPass is
              used.
        type: str
        returned: success
    config_drive:
        description:
            - Specifies the configuration driver.
        type: str
        returned: success
    created:
        description:
            - Specifies the time when an ECS was created.
        type: str
        returned: success
    disk_config_type:
        description:
            - Specifies the disk configuration type. MANUAL is The image
              space is not expanded. AUTO is the image space of the system disk
              will be expanded to be as same as the flavor.
        type: str
        returned: success
    host_name:
        description:
            - Specifies the host name of the ECS.
        type: str
        returned: success
    image_name:
        description:
            - Specifies the image name of the ECS.
        type: str
        returned: success
    power_state:
        description:
            - Specifies the power status of the ECS.
        type: int
        returned: success
    server_alias:
        description:
            - Specifies the ECS alias.
        type: str
        returned: success
    status:
        description:
            - Specifies the ECS status. Options are ACTIVE, REBOOT, HARD_REBOOT,
              REBUILD, MIGRATING, BUILD, SHUTOFF, RESIZE, VERIFY_RESIZE, ERROR,
              and DELETED.
        type: str
        returned: success
'''

from ansible.module_utils.hwc_utils import (
    Config, HwcClientException, HwcModule, are_different_dicts, build_path,
    get_region, is_empty_value, navigate_value, wait_to_finish)


def build_module():
    return HwcModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'],
                       type='str'),
            timeouts=dict(type='dict', options=dict(
                create=dict(default='30m', type='str'),
                update=dict(default='30m', type='str'),
                delete=dict(default='30m', type='str'),
            ), default=dict()),
            availability_zone=dict(type='str', required=True),
            flavor_name=dict(type='str', required=True),
            image_id=dict(type='str', required=True),
            name=dict(type='str', required=True),
            nics=dict(
                type='list', required=True, elements='dict',
                options=dict(
                    ip_address=dict(type='str', required=True),
                    subnet_id=dict(type='str', required=True)
                ),
            ),
            root_volume=dict(type='dict', required=True, options=dict(
                volume_type=dict(type='str', required=True),
                size=dict(type='int'),
                snapshot_id=dict(type='str')
            )),
            vpc_id=dict(type='str', required=True),
            admin_pass=dict(type='str'),
            data_volumes=dict(type='list', elements='dict', options=dict(
                volume_id=dict(type='str', required=True),
                device=dict(type='str')
            )),
            description=dict(type='str'),
            eip_id=dict(type='str'),
            enable_auto_recovery=dict(type='bool'),
            enterprise_project_id=dict(type='str'),
            security_groups=dict(type='list', elements='str'),
            server_metadata=dict(type='dict'),
            server_tags=dict(type='dict'),
            ssh_key_name=dict(type='str'),
            user_data=dict(type='str')
        ),
        supports_check_mode=True,
    )


def main():
    """Main function"""

    module = build_module()
    config = Config(module, "ecs")

    try:
        _init(config)
        is_exist = module.params['id']

        result = None
        changed = False
        if module.params['state'] == 'present':
            if not is_exist:
                if not module.check_mode:
                    create(config)
                changed = True

            inputv = user_input_parameters(module)
            resp, array_index = read_resource(config)
            result = build_state(inputv, resp, array_index)
            set_readonly_options(inputv, result)
            if are_different_dicts(inputv, result):
                if not module.check_mode:
                    update(config, inputv, result)

                    inputv = user_input_parameters(module)
                    resp, array_index = read_resource(config)
                    result = build_state(inputv, resp, array_index)
                    set_readonly_options(inputv, result)
                    if are_different_dicts(inputv, result):
                        raise Exception("Update resource failed, "
                                        "some attributes are not updated")

                changed = True

            result['id'] = module.params.get('id')
        else:
            result = dict()
            if is_exist:
                if not module.check_mode:
                    delete(config)
                changed = True

    except Exception as ex:
        module.fail_json(msg=str(ex))

    else:
        result['changed'] = changed
        module.exit_json(**result)


def _init(config):
    module = config.module
    if module.params['id']:
        return

    v = search_resource(config)
    n = len(v)
    if n > 1:
        raise Exception("Found more than one resource(%s)" % ", ".join([
            navigate_value(i, ["id"])
            for i in v
        ]))

    if n == 1:
        module.params['id'] = navigate_value(v[0], ["id"])


def user_input_parameters(module):
    return {
        "admin_pass": module.params.get("admin_pass"),
        "availability_zone": module.params.get("availability_zone"),
        "data_volumes": module.params.get("data_volumes"),
        "description": module.params.get("description"),
        "eip_id": module.params.get("eip_id"),
        "enable_auto_recovery": module.params.get("enable_auto_recovery"),
        "enterprise_project_id": module.params.get("enterprise_project_id"),
        "flavor_name": module.params.get("flavor_name"),
        "image_id": module.params.get("image_id"),
        "name": module.params.get("name"),
        "nics": module.params.get("nics"),
        "root_volume": module.params.get("root_volume"),
        "security_groups": module.params.get("security_groups"),
        "server_metadata": module.params.get("server_metadata"),
        "server_tags": module.params.get("server_tags"),
        "ssh_key_name": module.params.get("ssh_key_name"),
        "user_data": module.params.get("user_data"),
        "vpc_id": module.params.get("vpc_id"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "ecs", "project")
    timeout = 60 * int(module.params['timeouts']['create'].rstrip('m'))
    opts = user_input_parameters(module)
    opts["ansible_module"] = module

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    obj = async_wait(config, r, client, timeout)

    sub_job_identity = {
        "job_type": "createSingleServer",
    }
    for item in navigate_value(obj, ["entities", "sub_jobs"]):
        for k, v in sub_job_identity.items():
            if item[k] != v:
                break
        else:
            obj = item
            break
    else:
        raise Exception("Can't find the sub job")
    module.params['id'] = navigate_value(obj, ["entities", "server_id"])


def update(config, expect_state, current_state):
    module = config.module
    expect_state["current_state"] = current_state
    current_state["current_state"] = current_state
    timeout = 60 * int(module.params['timeouts']['update'].rstrip('m'))
    client = config.client(get_region(module), "ecs", "project")

    params = build_delete_nics_parameters(expect_state)
    params1 = build_delete_nics_parameters(current_state)
    if params and are_different_dicts(params, params1):
        r = send_delete_nics_request(module, params, client)
        async_wait(config, r, client, timeout)

    params = build_set_auto_recovery_parameters(expect_state)
    params1 = build_set_auto_recovery_parameters(current_state)
    if params and are_different_dicts(params, params1):
        send_set_auto_recovery_request(module, params, client)

    params = build_attach_nics_parameters(expect_state)
    params1 = build_attach_nics_parameters(current_state)
    if params and are_different_dicts(params, params1):
        r = send_attach_nics_request(module, params, client)
        async_wait(config, r, client, timeout)

    multi_invoke_delete_volume(config, expect_state, client, timeout)

    multi_invoke_attach_data_disk(config, expect_state, client, timeout)


def delete(config):
    module = config.module
    client = config.client(get_region(module), "ecs", "project")
    timeout = 60 * int(module.params['timeouts']['delete'].rstrip('m'))

    opts = user_input_parameters(module)
    opts["ansible_module"] = module

    params = build_delete_parameters(opts)
    if params:
        r = send_delete_request(module, params, client)
        async_wait(config, r, client, timeout)


def read_resource(config):
    module = config.module
    client = config.client(get_region(module), "ecs", "project")

    res = {}

    r = send_read_request(module, client)
    preprocess_read_response(r)
    res["read"] = fill_read_resp_body(r)

    r = send_read_auto_recovery_request(module, client)
    res["read_auto_recovery"] = fill_read_auto_recovery_resp_body(r)

    return res, None


def preprocess_read_response(resp):
    v = resp.get("os-extended-volumes:volumes_attached")
    if v and isinstance(v, list):
        for i in range(len(v)):
            if v[i].get("bootIndex") == "0":
                root_volume = v[i]

                if (i + 1) != len(v):
                    v[i] = v[-1]

                v.pop()

                resp["root_volume"] = root_volume
                break

    v = resp.get("addresses")
    if v:
        rv = {}
        eips = []
        for val in v.values():
            for item in val:
                if item["OS-EXT-IPS:type"] == "floating":
                    eips.append(item)
                else:
                    rv[item["OS-EXT-IPS:port_id"]] = item

        for item in eips:
            k = item["OS-EXT-IPS:port_id"]
            if k in rv:
                rv[k]["eip_address"] = item.get("addr", "")
            else:
                rv[k] = item
                item["eip_address"] = item.get("addr", "")
                item["addr"] = ""

        resp["address"] = rv.values()


def build_state(opts, response, array_index):
    states = flatten_options(response, array_index)
    set_unreadable_options(opts, states)
    adjust_options(opts, states)
    return states


def _build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["enterprise_project_id"])
    if v or v in [False, 0]:
        query_params.append(
            "enterprise_project_id=" + (str(v) if v else str(v).lower()))

    v = navigate_value(opts, ["name"])
    if v or v in [False, 0]:
        query_params.append(
            "name=" + (str(v) if v else str(v).lower()))

    query_link = "?limit=10&offset={offset}"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "ecs", "project")
    opts = user_input_parameters(module)
    identity_obj = _build_identity_object(opts)
    query_link = _build_query_link(opts)
    link = "cloudservers/detail" + query_link

    result = []
    p = {'offset': 1}
    while True:
        url = link.format(**p)
        r = send_list_request(module, client, url)
        if not r:
            break

        for item in r:
            item = fill_list_resp_body(item)
            adjust_list_resp(identity_obj, item)
            if not are_different_dicts(identity_obj, item):
                result.append(item)

        if len(result) > 1:
            break

        p['offset'] += 1

    return result


def build_delete_nics_parameters(opts):
    params = dict()

    v = expand_delete_nics_nics(opts, None)
    if not is_empty_value(v):
        params["nics"] = v

    return params


def expand_delete_nics_nics(d, array_index):
    cv = d["current_state"].get("nics")
    if not cv:
        return None

    val = cv

    ev = d.get("nics")
    if ev:
        m = [item.get("ip_address") for item in ev]
        val = [item for item in cv if item.get("ip_address") not in m]

    r = []
    for item in val:
        transformed = dict()

        v = item.get("port_id")
        if not is_empty_value(v):
            transformed["id"] = v

        if transformed:
            r.append(transformed)

    return r


def send_delete_nics_request(module, params, client):
    url = build_path(module, "cloudservers/{id}/nics/delete")

    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(delete_nics), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def build_set_auto_recovery_parameters(opts):
    params = dict()

    v = expand_set_auto_recovery_support_auto_recovery(opts, None)
    if v is not None:
        params["support_auto_recovery"] = v

    return params


def expand_set_auto_recovery_support_auto_recovery(d, array_index):
    v = navigate_value(d, ["enable_auto_recovery"], None)
    return None if v is None else str(v).lower()


def send_set_auto_recovery_request(module, params, client):
    url = build_path(module, "cloudservers/{id}/autorecovery")

    try:
        r = client.put(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(set_auto_recovery), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def build_create_parameters(opts):
    params = dict()

    v = navigate_value(opts, ["admin_pass"], None)
    if not is_empty_value(v):
        params["adminPass"] = v

    v = navigate_value(opts, ["availability_zone"], None)
    if not is_empty_value(v):
        params["availability_zone"] = v

    v = navigate_value(opts, ["description"], None)
    if not is_empty_value(v):
        params["description"] = v

    v = expand_create_extendparam(opts, None)
    if not is_empty_value(v):
        params["extendparam"] = v

    v = navigate_value(opts, ["flavor_name"], None)
    if not is_empty_value(v):
        params["flavorRef"] = v

    v = navigate_value(opts, ["image_id"], None)
    if not is_empty_value(v):
        params["imageRef"] = v

    v = navigate_value(opts, ["ssh_key_name"], None)
    if not is_empty_value(v):
        params["key_name"] = v

    v = navigate_value(opts, ["server_metadata"], None)
    if not is_empty_value(v):
        params["metadata"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    v = expand_create_nics(opts, None)
    if not is_empty_value(v):
        params["nics"] = v

    v = expand_create_publicip(opts, None)
    if not is_empty_value(v):
        params["publicip"] = v

    v = expand_create_root_volume(opts, None)
    if not is_empty_value(v):
        params["root_volume"] = v

    v = expand_create_security_groups(opts, None)
    if not is_empty_value(v):
        params["security_groups"] = v

    v = expand_create_server_tags(opts, None)
    if not is_empty_value(v):
        params["server_tags"] = v

    v = navigate_value(opts, ["user_data"], None)
    if not is_empty_value(v):
        params["user_data"] = v

    v = navigate_value(opts, ["vpc_id"], None)
    if not is_empty_value(v):
        params["vpcid"] = v

    if not params:
        return params

    params = {"server": params}

    return params


def expand_create_extendparam(d, array_index):
    r = dict()

    r["chargingMode"] = 0

    v = navigate_value(d, ["enterprise_project_id"], array_index)
    if not is_empty_value(v):
        r["enterprise_project_id"] = v

    v = navigate_value(d, ["enable_auto_recovery"], array_index)
    if not is_empty_value(v):
        r["support_auto_recovery"] = v

    return r


def expand_create_nics(d, array_index):
    new_ai = dict()
    if array_index:
        new_ai.update(array_index)

    req = []

    v = navigate_value(
        d, ["nics"], new_ai)

    if not v:
        return req
    n = len(v)
    for i in range(n):
        new_ai["nics"] = i
        transformed = dict()

        v = navigate_value(d, ["nics", "ip_address"], new_ai)
        if not is_empty_value(v):
            transformed["ip_address"] = v

        v = navigate_value(d, ["nics", "subnet_id"], new_ai)
        if not is_empty_value(v):
            transformed["subnet_id"] = v

        if transformed:
            req.append(transformed)

    return req


def expand_create_publicip(d, array_index):
    r = dict()

    v = navigate_value(d, ["eip_id"], array_index)
    if not is_empty_value(v):
        r["id"] = v

    return r


def expand_create_root_volume(d, array_index):
    r = dict()

    v = expand_create_root_volume_extendparam(d, array_index)
    if not is_empty_value(v):
        r["extendparam"] = v

    v = navigate_value(d, ["root_volume", "size"], array_index)
    if not is_empty_value(v):
        r["size"] = v

    v = navigate_value(d, ["root_volume", "volume_type"], array_index)
    if not is_empty_value(v):
        r["volumetype"] = v

    return r


def expand_create_root_volume_extendparam(d, array_index):
    r = dict()

    v = navigate_value(d, ["root_volume", "snapshot_id"], array_index)
    if not is_empty_value(v):
        r["snapshotId"] = v

    return r


def expand_create_security_groups(d, array_index):
    v = d.get("security_groups")
    if not v:
        return None

    return [{"id": i} for i in v]


def expand_create_server_tags(d, array_index):
    v = d.get("server_tags")
    if not v:
        return None

    return [{"key": k, "value": v1} for k, v1 in v.items()]


def send_create_request(module, params, client):
    url = "cloudservers"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def build_attach_nics_parameters(opts):
    params = dict()

    v = expand_attach_nics_nics(opts, None)
    if not is_empty_value(v):
        params["nics"] = v

    return params


def expand_attach_nics_nics(d, array_index):
    ev = d.get("nics")
    if not ev:
        return None

    val = ev

    cv = d["current_state"].get("nics")
    if cv:
        m = [item.get("ip_address") for item in cv]
        val = [item for item in ev if item.get("ip_address") not in m]

    r = []
    for item in val:
        transformed = dict()

        v = item.get("ip_address")
        if not is_empty_value(v):
            transformed["ip_address"] = v

        v = item.get("subnet_id")
        if not is_empty_value(v):
            transformed["subnet_id"] = v

        if transformed:
            r.append(transformed)

    return r


def send_attach_nics_request(module, params, client):
    url = build_path(module, "cloudservers/{id}/nics")

    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(attach_nics), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_delete_volume_request(module, params, client, info):
    path_parameters = {
        "volume_id": ["volume_id"],
    }
    data = dict((key, navigate_value(info, path))
                for key, path in path_parameters.items())

    url = build_path(module, "cloudservers/{id}/detachvolume/{volume_id}", data)

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(delete_volume), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def build_attach_data_disk_parameters(opts, array_index):
    params = dict()

    v = expand_attach_data_disk_volume_attachment(opts, array_index)
    if not is_empty_value(v):
        params["volumeAttachment"] = v

    return params


def expand_attach_data_disk_volume_attachment(d, array_index):
    r = dict()

    v = navigate_value(d, ["data_volumes", "device"], array_index)
    if not is_empty_value(v):
        r["device"] = v

    v = navigate_value(d, ["data_volumes", "volume_id"], array_index)
    if not is_empty_value(v):
        r["volumeId"] = v

    return r


def send_attach_data_disk_request(module, params, client):
    url = build_path(module, "cloudservers/{id}/attachvolume")

    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(attach_data_disk), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def build_delete_parameters(opts):
    params = dict()

    params["delete_publicip"] = False

    params["delete_volume"] = False

    v = expand_delete_servers(opts, None)
    if not is_empty_value(v):
        params["servers"] = v

    return params


def expand_delete_servers(d, array_index):
    new_ai = dict()
    if array_index:
        new_ai.update(array_index)

    req = []

    n = 1
    for i in range(n):
        transformed = dict()

        v = expand_delete_servers_id(d, new_ai)
        if not is_empty_value(v):
            transformed["id"] = v

        if transformed:
            req.append(transformed)

    return req


def expand_delete_servers_id(d, array_index):
    return d["ansible_module"].params.get("id")


def send_delete_request(module, params, client):
    url = "cloudservers/delete"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def async_wait(config, result, client, timeout):
    module = config.module

    url = build_path(module, "jobs/{job_id}", result)

    def _query_status():
        r = None
        try:
            r = client.get(url, timeout=timeout)
        except HwcClientException:
            return None, ""

        try:
            s = navigate_value(r, ["status"])
            return r, s
        except Exception:
            return None, ""

    try:
        return wait_to_finish(
            ["SUCCESS"],
            ["RUNNING", "INIT"],
            _query_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_ecs_instance): error "
                             "waiting to be done, error= %s" % str(ex))


def multi_invoke_delete_volume(config, opts, client, timeout):
    module = config.module

    opts1 = None
    expect = opts["data_volumes"]
    current = opts["current_state"]["data_volumes"]
    if expect and current:
        v = [i["volume_id"] for i in expect]
        opts1 = {
            "data_volumes": [
                i for i in current if i["volume_id"] not in v
            ]
        }

    loop_val = navigate_value(opts1, ["data_volumes"])
    if not loop_val:
        return

    for i in range(len(loop_val)):
        r = send_delete_volume_request(module, None, client, loop_val[i])
        async_wait(config, r, client, timeout)


def multi_invoke_attach_data_disk(config, opts, client, timeout):
    module = config.module

    opts1 = opts
    expect = opts["data_volumes"]
    current = opts["current_state"]["data_volumes"]
    if expect and current:
        v = [i["volume_id"] for i in current]
        opts1 = {
            "data_volumes": [
                i for i in expect if i["volume_id"] not in v
            ]
        }

    loop_val = navigate_value(opts1, ["data_volumes"])
    if not loop_val:
        return

    for i in range(len(loop_val)):
        params = build_attach_data_disk_parameters(opts1, {"data_volumes": i})
        r = send_attach_data_disk_request(module, params, client)
        async_wait(config, r, client, timeout)


def send_read_request(module, client):
    url = build_path(module, "cloudservers/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["server"], None)


def fill_read_resp_body(body):
    result = dict()

    result["OS-DCF:diskConfig"] = body.get("OS-DCF:diskConfig")

    result["OS-EXT-AZ:availability_zone"] = body.get(
        "OS-EXT-AZ:availability_zone")

    result["OS-EXT-SRV-ATTR:hostname"] = body.get("OS-EXT-SRV-ATTR:hostname")

    result["OS-EXT-SRV-ATTR:instance_name"] = body.get(
        "OS-EXT-SRV-ATTR:instance_name")

    result["OS-EXT-SRV-ATTR:user_data"] = body.get("OS-EXT-SRV-ATTR:user_data")

    result["OS-EXT-STS:power_state"] = body.get("OS-EXT-STS:power_state")

    v = fill_read_resp_address(body.get("address"))
    result["address"] = v

    result["config_drive"] = body.get("config_drive")

    result["created"] = body.get("created")

    result["description"] = body.get("description")

    result["enterprise_project_id"] = body.get("enterprise_project_id")

    v = fill_read_resp_flavor(body.get("flavor"))
    result["flavor"] = v

    result["id"] = body.get("id")

    v = fill_read_resp_image(body.get("image"))
    result["image"] = v

    result["key_name"] = body.get("key_name")

    v = fill_read_resp_metadata(body.get("metadata"))
    result["metadata"] = v

    result["name"] = body.get("name")

    v = fill_read_resp_os_extended_volumes_volumes_attached(
        body.get("os-extended-volumes:volumes_attached"))
    result["os-extended-volumes:volumes_attached"] = v

    v = fill_read_resp_root_volume(body.get("root_volume"))
    result["root_volume"] = v

    result["status"] = body.get("status")

    result["tags"] = body.get("tags")

    return result


def fill_read_resp_address(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["OS-EXT-IPS:port_id"] = item.get("OS-EXT-IPS:port_id")

        val["OS-EXT-IPS:type"] = item.get("OS-EXT-IPS:type")

        val["addr"] = item.get("addr")

        result.append(val)

    return result


def fill_read_resp_flavor(value):
    if not value:
        return None

    result = dict()

    result["id"] = value.get("id")

    return result


def fill_read_resp_image(value):
    if not value:
        return None

    result = dict()

    result["id"] = value.get("id")

    return result


def fill_read_resp_metadata(value):
    if not value:
        return None

    result = dict()

    result["image_name"] = value.get("image_name")

    result["vpc_id"] = value.get("vpc_id")

    return result


def fill_read_resp_os_extended_volumes_volumes_attached(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["bootIndex"] = item.get("bootIndex")

        val["device"] = item.get("device")

        val["id"] = item.get("id")

        result.append(val)

    return result


def fill_read_resp_root_volume(value):
    if not value:
        return None

    result = dict()

    result["device"] = value.get("device")

    result["id"] = value.get("id")

    return result


def send_read_auto_recovery_request(module, client):
    url = build_path(module, "cloudservers/{id}/autorecovery")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(read_auto_recovery), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def fill_read_auto_recovery_resp_body(body):
    result = dict()

    result["support_auto_recovery"] = body.get("support_auto_recovery")

    return result


def flatten_options(response, array_index):
    r = dict()

    v = navigate_value(
        response, ["read", "OS-EXT-AZ:availability_zone"], array_index)
    r["availability_zone"] = v

    v = navigate_value(response, ["read", "config_drive"], array_index)
    r["config_drive"] = v

    v = navigate_value(response, ["read", "created"], array_index)
    r["created"] = v

    v = flatten_data_volumes(response, array_index)
    r["data_volumes"] = v

    v = navigate_value(response, ["read", "description"], array_index)
    r["description"] = v

    v = navigate_value(response, ["read", "OS-DCF:diskConfig"], array_index)
    r["disk_config_type"] = v

    v = flatten_enable_auto_recovery(response, array_index)
    r["enable_auto_recovery"] = v

    v = navigate_value(
        response, ["read", "enterprise_project_id"], array_index)
    r["enterprise_project_id"] = v

    v = navigate_value(response, ["read", "flavor", "id"], array_index)
    r["flavor_name"] = v

    v = navigate_value(
        response, ["read", "OS-EXT-SRV-ATTR:hostname"], array_index)
    r["host_name"] = v

    v = navigate_value(response, ["read", "image", "id"], array_index)
    r["image_id"] = v

    v = navigate_value(
        response, ["read", "metadata", "image_name"], array_index)
    r["image_name"] = v

    v = navigate_value(response, ["read", "name"], array_index)
    r["name"] = v

    v = flatten_nics(response, array_index)
    r["nics"] = v

    v = navigate_value(
        response, ["read", "OS-EXT-STS:power_state"], array_index)
    r["power_state"] = v

    v = flatten_root_volume(response, array_index)
    r["root_volume"] = v

    v = navigate_value(
        response, ["read", "OS-EXT-SRV-ATTR:instance_name"], array_index)
    r["server_alias"] = v

    v = flatten_server_tags(response, array_index)
    r["server_tags"] = v

    v = navigate_value(response, ["read", "key_name"], array_index)
    r["ssh_key_name"] = v

    v = navigate_value(response, ["read", "status"], array_index)
    r["status"] = v

    v = navigate_value(
        response, ["read", "OS-EXT-SRV-ATTR:user_data"], array_index)
    r["user_data"] = v

    v = navigate_value(response, ["read", "metadata", "vpc_id"], array_index)
    r["vpc_id"] = v

    return r


def flatten_data_volumes(d, array_index):
    v = navigate_value(d, ["read", "os-extended-volumes:volumes_attached"],
                       array_index)
    if not v:
        return None
    n = len(v)
    result = []

    new_ai = dict()
    if array_index:
        new_ai.update(array_index)

    for i in range(n):
        new_ai["read.os-extended-volumes:volumes_attached"] = i

        val = dict()

        v = navigate_value(
            d, ["read", "os-extended-volumes:volumes_attached", "device"], new_ai)
        val["device"] = v

        v = navigate_value(
            d, ["read", "os-extended-volumes:volumes_attached", "id"], new_ai)
        val["volume_id"] = v

        for v in val.values():
            if v is not None:
                result.append(val)
                break

    return result if result else None


def flatten_enable_auto_recovery(d, array_index):
    v = navigate_value(d, ["read_auto_recovery", "support_auto_recovery"],
                       array_index)
    return v == "true"


def flatten_nics(d, array_index):
    v = navigate_value(d, ["read", "address"],
                       array_index)
    if not v:
        return None
    n = len(v)
    result = []

    new_ai = dict()
    if array_index:
        new_ai.update(array_index)

    for i in range(n):
        new_ai["read.address"] = i

        val = dict()

        v = navigate_value(d, ["read", "address", "addr"], new_ai)
        val["ip_address"] = v

        v = navigate_value(
            d, ["read", "address", "OS-EXT-IPS:port_id"], new_ai)
        val["port_id"] = v

        for v in val.values():
            if v is not None:
                result.append(val)
                break

    return result if result else None


def flatten_root_volume(d, array_index):
    result = dict()

    v = navigate_value(d, ["read", "root_volume", "device"], array_index)
    result["device"] = v

    v = navigate_value(d, ["read", "root_volume", "id"], array_index)
    result["volume_id"] = v

    for v in result.values():
        if v is not None:
            return result
    return None


def flatten_server_tags(d, array_index):
    v = navigate_value(d, ["read", "tags"], array_index)
    if not v:
        return None

    r = dict()
    for item in v:
        v1 = item.split("=")
        if v1:
            r[v1[0]] = v1[1]
    return r


def adjust_options(opts, states):
    adjust_data_volumes(opts, states)

    adjust_nics(opts, states)


def adjust_data_volumes(parent_input, parent_cur):
    iv = parent_input.get("data_volumes")
    if not (iv and isinstance(iv, list)):
        return

    cv = parent_cur.get("data_volumes")
    if not (cv and isinstance(cv, list)):
        return

    lcv = len(cv)
    result = []
    q = []
    for iiv in iv:
        if len(q) == lcv:
            break

        icv = None
        for j in range(lcv):
            if j in q:
                continue

            icv = cv[j]

            if iiv["volume_id"] != icv["volume_id"]:
                continue

            result.append(icv)
            q.append(j)
            break
        else:
            break

    if len(q) != lcv:
        for i in range(lcv):
            if i not in q:
                result.append(cv[i])

    if len(result) != lcv:
        raise Exception("adjust property(data_volumes) failed, "
                        "the array number is not equal")

    parent_cur["data_volumes"] = result


def adjust_nics(parent_input, parent_cur):
    iv = parent_input.get("nics")
    if not (iv and isinstance(iv, list)):
        return

    cv = parent_cur.get("nics")
    if not (cv and isinstance(cv, list)):
        return

    lcv = len(cv)
    result = []
    q = []
    for iiv in iv:
        if len(q) == lcv:
            break

        icv = None
        for j in range(lcv):
            if j in q:
                continue

            icv = cv[j]

            if iiv["ip_address"] != icv["ip_address"]:
                continue

            result.append(icv)
            q.append(j)
            break
        else:
            break

    if len(q) != lcv:
        for i in range(lcv):
            if i not in q:
                result.append(cv[i])

    if len(result) != lcv:
        raise Exception("adjust property(nics) failed, "
                        "the array number is not equal")

    parent_cur["nics"] = result


def set_unreadable_options(opts, states):
    states["admin_pass"] = opts.get("admin_pass")

    states["eip_id"] = opts.get("eip_id")

    set_unread_nics(
        opts.get("nics"), states.get("nics"))

    set_unread_root_volume(
        opts.get("root_volume"), states.get("root_volume"))

    states["security_groups"] = opts.get("security_groups")

    states["server_metadata"] = opts.get("server_metadata")


def set_unread_nics(inputv, curv):
    if not (inputv and isinstance(inputv, list)):
        return

    if not (curv and isinstance(curv, list)):
        return

    lcv = len(curv)
    q = []
    for iv in inputv:
        if len(q) == lcv:
            break

        cv = None
        for j in range(lcv):
            if j in q:
                continue

            cv = curv[j]

            if iv["ip_address"] != cv["ip_address"]:
                continue

            q.append(j)
            break
        else:
            continue

        cv["subnet_id"] = iv.get("subnet_id")


def set_unread_root_volume(inputv, curv):
    if not (inputv and isinstance(inputv, dict)):
        return

    if not (curv and isinstance(curv, dict)):
        return

    curv["size"] = inputv.get("size")

    curv["snapshot_id"] = inputv.get("snapshot_id")

    curv["volume_type"] = inputv.get("volume_type")


def set_readonly_options(opts, states):
    opts["config_drive"] = states.get("config_drive")

    opts["created"] = states.get("created")

    opts["disk_config_type"] = states.get("disk_config_type")

    opts["host_name"] = states.get("host_name")

    opts["image_name"] = states.get("image_name")

    set_readonly_nics(
        opts.get("nics"), states.get("nics"))

    opts["power_state"] = states.get("power_state")

    set_readonly_root_volume(
        opts.get("root_volume"), states.get("root_volume"))

    opts["server_alias"] = states.get("server_alias")

    opts["status"] = states.get("status")


def set_readonly_nics(inputv, curv):
    if not (curv and isinstance(curv, list)):
        return

    if not (inputv and isinstance(inputv, list)):
        return

    lcv = len(curv)
    q = []
    for iv in inputv:
        if len(q) == lcv:
            break

        cv = None
        for j in range(lcv):
            if j in q:
                continue

            cv = curv[j]

            if iv["ip_address"] != cv["ip_address"]:
                continue

            q.append(j)
            break
        else:
            continue

        iv["port_id"] = cv.get("port_id")


def set_readonly_root_volume(inputv, curv):
    if not (inputv and isinstance(inputv, dict)):
        return

    if not (curv and isinstance(curv, dict)):
        return

    inputv["device"] = curv.get("device")

    inputv["volume_id"] = curv.get("volume_id")


def send_list_request(module, client, url):

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_ecs_instance): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["servers"], None)


def _build_identity_object(all_opts):
    result = dict()

    result["OS-DCF:diskConfig"] = None

    v = navigate_value(all_opts, ["availability_zone"], None)
    result["OS-EXT-AZ:availability_zone"] = v

    result["OS-EXT-SRV-ATTR:hostname"] = None

    result["OS-EXT-SRV-ATTR:instance_name"] = None

    v = navigate_value(all_opts, ["user_data"], None)
    result["OS-EXT-SRV-ATTR:user_data"] = v

    result["OS-EXT-STS:power_state"] = None

    result["config_drive"] = None

    result["created"] = None

    v = navigate_value(all_opts, ["description"], None)
    result["description"] = v

    v = navigate_value(all_opts, ["enterprise_project_id"], None)
    result["enterprise_project_id"] = v

    v = expand_list_flavor(all_opts, None)
    result["flavor"] = v

    result["id"] = None

    v = expand_list_image(all_opts, None)
    result["image"] = v

    v = navigate_value(all_opts, ["ssh_key_name"], None)
    result["key_name"] = v

    v = expand_list_metadata(all_opts, None)
    result["metadata"] = v

    v = navigate_value(all_opts, ["name"], None)
    result["name"] = v

    result["status"] = None

    v = expand_list_tags(all_opts, None)
    result["tags"] = v

    return result


def expand_list_flavor(d, array_index):
    r = dict()

    v = navigate_value(d, ["flavor_name"], array_index)
    r["id"] = v

    for v in r.values():
        if v is not None:
            return r
    return None


def expand_list_image(d, array_index):
    r = dict()

    v = navigate_value(d, ["image_id"], array_index)
    r["id"] = v

    for v in r.values():
        if v is not None:
            return r
    return None


def expand_list_metadata(d, array_index):
    r = dict()

    v = navigate_value(d, ["vpc_id"], array_index)
    r["vpc_id"] = v

    for v in r.values():
        if v is not None:
            return r
    return None


def expand_list_tags(d, array_index):
    v = d.get("server_tags")
    if not v:
        return None

    return [k + "=" + v1 for k, v1 in v.items()]


def fill_list_resp_body(body):
    result = dict()

    result["OS-DCF:diskConfig"] = body.get("OS-DCF:diskConfig")

    result["OS-EXT-AZ:availability_zone"] = body.get(
        "OS-EXT-AZ:availability_zone")

    result["OS-EXT-SRV-ATTR:hostname"] = body.get("OS-EXT-SRV-ATTR:hostname")

    result["OS-EXT-SRV-ATTR:instance_name"] = body.get(
        "OS-EXT-SRV-ATTR:instance_name")

    result["OS-EXT-SRV-ATTR:user_data"] = body.get("OS-EXT-SRV-ATTR:user_data")

    result["OS-EXT-STS:power_state"] = body.get("OS-EXT-STS:power_state")

    result["config_drive"] = body.get("config_drive")

    result["created"] = body.get("created")

    result["description"] = body.get("description")

    result["enterprise_project_id"] = body.get("enterprise_project_id")

    v = fill_list_resp_flavor(body.get("flavor"))
    result["flavor"] = v

    result["id"] = body.get("id")

    v = fill_list_resp_image(body.get("image"))
    result["image"] = v

    result["key_name"] = body.get("key_name")

    v = fill_list_resp_metadata(body.get("metadata"))
    result["metadata"] = v

    result["name"] = body.get("name")

    result["status"] = body.get("status")

    result["tags"] = body.get("tags")

    return result


def fill_list_resp_flavor(value):
    if not value:
        return None

    result = dict()

    result["id"] = value.get("id")

    return result


def fill_list_resp_image(value):
    if not value:
        return None

    result = dict()

    result["id"] = value.get("id")

    return result


def fill_list_resp_metadata(value):
    if not value:
        return None

    result = dict()

    result["vpc_id"] = value.get("vpc_id")

    return result


def adjust_list_resp(opts, resp):
    adjust_list_api_tags(opts, resp)


def adjust_list_api_tags(parent_input, parent_cur):
    iv = parent_input.get("tags")
    if not (iv and isinstance(iv, list)):
        return

    cv = parent_cur.get("tags")
    if not (cv and isinstance(cv, list)):
        return

    result = []
    for iiv in iv:
        if iiv not in cv:
            break

        result.append(iiv)

        j = cv.index(iiv)
        cv[j] = cv[-1]
        cv.pop()

    if cv:
        result.extend(cv)
    parent_cur["tags"] = result


if __name__ == '__main__':
    main()
