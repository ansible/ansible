#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, [Sergey Shubin ($ssi444) <serg at ssid.name>]
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: proxmox_pool
short_description: management of resources pool in Proxmox VE cluster
description:
  - allows you to create/delete resources pool in Proxmox VE cluster
  - allows you to add/remove VM/Storage in resources pool in Proxmox VE cluster
version_added: "2.9"
options:
  api_host:
    description:
      - the host of the Proxmox VE cluster
    required: true
  api_user:
    description:
      - the user to authenticate with
    required: true
  api_password:
    description:
      - the password to authenticate with
      - you can use PROXMOX_PASSWORD environment variable
  comment:
    description:
      - comment of the resource pool
    default: ''
  force_delete:
    description:
      - Proxmox allows you to delete only pools that do not have storage or virtual machines.
      - An error will occur when deleting a non-empty pool.
      - This option first clears the pool of the resources contained in it and then deletes the pool itself
      - forcing delete operations for resource pool
      - can be used only with states C(absent)
      - with C(state=present) option will be ignored
    type: bool
    default: 'no'
  option:
    description:
      - Action required.
      - C(comment) for manipulations (add / remove / change) with the comment of the resource pool
      - C(pool) for manipulations (add / remove) with the resource pool itself
      - C(storage) for manipulations (add / remove) with storage pools of resources
      - C(vms) for manipulations (add / remove) with resource pool virtual machines
    choices: ['comment', 'pool', 'storage', 'vms']
    default: pool
  pool_name|pool|name:
    description:
      - Proxmox VE resource pool
  state:
    description:
      - Indicate desired state of the instance
    choices: ['present', 'absent']
    default: present
  storage:
    description:
      - target storage
  validate_certs:
    description:
      - enable / disable https certificate verification
    type: bool
    default: 'no'
  vmid:
    description:
      - the existing instance id


notes:
  - Requires proxmoxer and requests modules on host. This modules can be installed with pip.
  - check_mode isn’t supported
requirements: [ "proxmoxer", "python >= 2.7", "requests" ]
author: Sergey Shubin (@ssi444)
'''

EXAMPLES = '''
# Create three new pool
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "{{pool_item}}"
    comment: "Test environment '{{pool_item}}' for verify task"
    option: pool
    state: present
  with_items:
    - test_env_1
    - test_env_2
    - test_env_3
  loop_control:
    loop_var: pool_item

# Add VMs into pool 'test_env_1'
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "test_env_1"
    option: vms
    state: present
    vmid: "{{vm_item}}"
  with_items:
    - 109
    - 111
  loop_control:
    loop_var: vm_item

# Add storage into pool 'test_env_1'
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "test_env_1"
    option: storage
    state: present
    storage: "{{st_item}}"
  with_items:
    - "local-lvm"
    - "extra-lvm"
  loop_control:
    loop_var: st_item

# Change comment for poll 'test_env_2'
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "test_env_2"
    comment: "Changed comment for poll test_env_2"
    option: comment
    state: present

# Remove comment for poll 'test_env_2'
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "test_env_2"
    option: comment
    state: absent

# Remove VM 111 from pool test_env_1
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "test_env_1"
    option: vms
    vmid: 111
    state: absent

# Remove storage 'local-lvm' from pool test_env_1
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "test_env_1"
    option: storage
    storage: local-lvm
    state: absent

# Remove non-empty pool test_env_1
- proxmox_pool:
    api_host: node1
    api_user: root@pam
    api_password: 1q2w3e
    pool: "test_env_1"
    option: pool
    state: absent
    force_delete: yes

'''

RETURN = ''' # '''

import os

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

from ansible.module_utils.basic import AnsibleModule


def pool_exists(proxmox, pool_name):
    pools = proxmox.pools.get()
    for item in pools:
        if item['poolid'] == pool_name:
            return True
    return False


def pool_create(proxmox, pool_name, comment=''):
    if comment != '':
        res = proxmox.pools.create(poolid=pool_name, comment=comment)
    else:
        res = proxmox.pools.create(poolid=pool_name)
    return res


def pool_delete(proxmox, pool_name):
    proxmox.pools.delete(pool_name)


def pool_has_members(proxmox, pool_name):
    pool = proxmox.pools.get(pool_name)
    return len(pool['members']) > 0


def pool_vm_exists(proxmox, pool_name, vmid):
    pool = proxmox.pools.get(pool_name)
    for item in pool['members']:
        if (item['type'] == "lxc" or item['type'] == "qemu" or item['type'] == "openvz") and item['vmid'] == vmid:
            return True
    return False


def pool_vm_add(proxmox, pool_name, vmid):
    proxmox.pools.set(pool_name, vms=vmid)


def pool_vm_delete(proxmox, pool_name, vmid):
    proxmox.pools.set(pool_name, vms=vmid, delete=1)


def pool_storage_exists(proxmox, pool_name, storage):
    pool = proxmox.pools.get(pool_name)
    for item in pool['members']:
        if item['type'] == "storage" and item['storage'] == storage:
            return True
    return False


def pool_storage_add(proxmox, pool_name, storage):
    proxmox.pools.set(pool_name, storage=storage)


def pool_storage_delete(proxmox, pool_name, storage):
    proxmox.pools.set(pool_name, storage=storage, delete=1)


def pool_comment_get(proxmox, pool_name):
    pool = proxmox.pools.get(pool_name)
    if 'comment' in pool:
        return pool['comment']
    else:
        return ''


def pool_comment_set(proxmox, pool_name, comment):
    proxmox.pools.set(pool_name, comment=comment)


def pool_clear_force(proxmox, pool_name):
    pool = proxmox.pools.get(pool_name)
    for item in pool['members']:
        if item['type'] == "storage":
            pool_storage_delete(proxmox, pool_name, item['storage'])
        elif item['type'] == "lxc" or item['type'] == "qemu" or item['type'] == "openvz":
            pool_vm_delete(proxmox, pool_name, item['vmid'])


def cluster_storage_exists(proxmox, storage):
    for st in proxmox.cluster.resources.get(type='storage'):
        if st['storage'] == storage:
            return True
    return False


def cluster_vm_exists(proxmox, vmid):
    for vm in proxmox.cluster.resources.get(type='vm'):
        if vm['vmid'] == vmid:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_host=dict(required=True),  # the host of the Proxmox VE cluster
            api_password=dict(no_log=True, required=False, default=''),
            api_user=dict(required=True),  # the user to authenticate with
            pool_name=dict(required=True, aliases=['pool', 'name']),  # Proxmox VE resource pool
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            option=dict(required=False, choices=['comment', 'pool', 'storage', 'vms'], default='pool'),
            validate_certs=dict(type='bool', default='no'),
            vmid=dict(required=False, type='int'),
            comment=dict(required=False, default=''),
            storage=dict(required=False),
            force_delete=dict(required=False, type='bool', default='no')
        ),
        supports_check_mode=False,
        mutually_exclusive=[['vmid', 'comment', 'storage']]
    )

    api_host = module.params['api_host']
    api_user = module.params['api_user']
    api_password = module.params['api_password']
    state = module.params['state']
    comment = module.params['comment']
    pool_name = module.params['pool_name']
    storage = module.params['storage']
    vmid = module.params['vmid']
    validate_certs = module.params['validate_certs']
    option = module.params['option']
    force_delete = module.params['force_delete']

    # If password not set get it from PROXMOX_PASSWORD env
    if not api_password:
        try:
            api_password = os.environ['PROXMOX_PASSWORD']
        except KeyError as e:
            module.fail_json(msg='You should set api_password param or use PROXMOX_PASSWORD environment variable')

    try:
        proxmox = ProxmoxAPI(api_host, user=api_user, password=api_password, verify_ssl=validate_certs)
    except Exception as e:
        module.fail_json(msg='authorization on proxmox cluster failed with exception: %s' % e)

    if state == 'present':
        if option == 'comment':  # Обновление комментария пула
            try:
                if pool_exists(proxmox, pool_name):
                    current_comment = pool_comment_get(proxmox, pool_name)
                    if current_comment == comment:  # Всё есть, ничего не делаем
                        module.exit_json(changed=False, msg="Comment is valid")
                    else:  # Обновление комментария
                        pool_comment_set(proxmox, pool_name, comment)
                        module.exit_json(changed=True, msg="Comment changed")
                else:  # Пул не найден, ничего не делаем
                    module.fail_json(msg="Pool '%s' not exists" % (pool_name))
            except Exception as e:
                module.fail_json(msg="Adding comment '%s' to pool '%s' failed with exception: %s" % (comment, pool_name, e))
        elif option == 'pool':  # Создание пула, обновление комментария к пулу
            try:
                if pool_exists(proxmox, pool_name):
                    current_comment = pool_comment_get(proxmox, pool_name)
                    if current_comment == comment:  # Всё есть, ничего не делаем
                        module.exit_json(changed=False, msg="Comment is valid")
                    else:  # Обновление комментария
                        pool_comment_set(proxmox, pool_name, comment)
                        module.exit_json(changed=True, msg="Comment changed")
                else:  # Создание пула
                    pool_create(proxmox, pool_name, comment)
                    module.exit_json(changed=True, msg="Pool created successfully")
            except Exception as e:
                module.fail_json(msg="Creation pool '%s' failed with exception: %s" % (pool_name, e))

        elif option == 'storage':  # Добавление хранилища в пул
            try:
                if pool_exists(proxmox, pool_name):
                    if pool_storage_exists(proxmox, pool_name, storage):  # Всё есть, ничего не делаем
                        module.exit_json(changed=False, msg="Storage exists in pool")
                    else:  # Добавить хранилище в пул
                        if cluster_storage_exists(proxmox, storage):  # Проверим, существует ли такое хранилище в кластере
                            pool_storage_add(proxmox, pool_name, storage)
                            module.exit_json(changed=True, msg="Storage added in pool successfully")
                        else:
                            module.fail_json(msg="Storage '%s' not exists in cluster" % (storage))
                else:  # Пул не найден, ничего не делаем
                    module.fail_json(msg="Pool '%s' not exists" % (pool_name))
            except Exception as e:
                module.fail_json(msg="Adding storage '%s' to pool '%s' failed with exception: %s" % (storage, pool_name, e))

        elif option == 'vms':  # Добавление VM в пул
            try:
                if pool_exists(proxmox, pool_name):
                    if pool_vm_exists(proxmox, pool_name, vmid):  # Всё есть, ничего не делаем
                        module.exit_json(changed=False, msg="VM exists in pool")
                    else:  # Добавить VM в пул
                        if cluster_vm_exists(proxmox, vmid):  # Проверим, существует ли такая VM в кластере
                            pool_vm_add(proxmox, pool_name, vmid)
                            module.exit_json(changed=True, msg="VM added in pool successfully")
                        else:
                            module.fail_json(msg="VM '%s' not exists in cluster" % (vmid))
                else:  # Пул не найден, ничего не делаем
                    module.fail_json(msg="Pool '%s' not exists" % (pool_name))
            except Exception as e:
                module.fail_json(msg="Adding VM '%s' to pool '%s' failed with exception: %s" % (vmid, pool_name, e))

    elif state == 'absent':
        if option == 'comment':  # Очистка комментария пула
            try:
                if pool_exists(proxmox, pool_name):
                    current_comment = pool_comment_get(proxmox, pool_name)
                    if current_comment == '':  # Комментарий пустой, ничего не делаем
                        module.exit_json(changed=False, msg="Comment is empty")
                    else:  # Обновление комментария
                        pool_comment_set(proxmox, pool_name, '')
                        module.exit_json(changed=True, msg="Comment is removed")
                else:  # Пул не найден, ничего не делаем
                    module.fail_json(msg="Pool '%s' not exists" % (pool_name))
            except Exception as e:
                module.fail_json(msg="Removing comment from pool '%s' failed with exception: %s" % (pool_name, e))
        elif option == 'pool':  # Удаление пула
            try:
                if pool_exists(proxmox, pool_name):  # Удалим пул
                    if pool_has_members(proxmox, pool_name):
                        if force_delete is False:
                            module.fail_json(msg="The pool '%s' has members. The pool must be empty. \
                                                  Or use the 'force_delete' option to automatically \
                                                  delete all pool members" % (pool_name))
                        else:
                            pool_clear_force(proxmox, pool_name)
                            pool_delete(proxmox, pool_name)
                            module.exit_json(changed=True, msg="Forced deleting pool '%s' is successfully" % (pool_name))
                    else:
                        pool_delete(proxmox, pool_name)
                        module.exit_json(changed=True, msg="Pool '%s' deleted successfully" % (pool_name))
                else:  # Пул не существует, ничего не делаем
                    module.exit_json(changed=False, msg="Pool not exists")
            except Exception as e:
                module.fail_json(msg="Deleting pool '%s' failed with exception: %s" % (pool_name, e))

        elif option == 'storage':  # Удаление хранилища из пула
            try:
                if pool_exists(proxmox, pool_name):
                    if pool_storage_exists(proxmox, pool_name, storage):  # Удалим хранилище из пула
                        pool_storage_delete(proxmox, pool_name, storage)
                        module.exit_json(changed=True, msg="Removing storage '%s' from pool '%s' is successfully" % (storage, pool_name))
                    else:  # Хранилище в пуле не найдено, ничего не делаем
                        module.exit_json(changed=False, msg="Storage not found in pool")
                else:  # Пул не найден, ничего не делаем
                    module.fail_json(msg="Pool '%s' not exists" % (pool_name))
            except Exception as e:
                module.fail_json(msg="Removing storage '%s' from pool '%s' failed with exception: %s" % (storage, pool_name, e))

        elif option == 'vms':  # Удаление VM из пула
            try:
                if pool_exists(proxmox, pool_name):
                    if pool_vm_exists(proxmox, pool_name, vmid):  # Удалим хранилище из пула
                        pool_vm_delete(proxmox, pool_name, vmid)
                        module.exit_json(changed=True, msg="Removing VM '%s' from pool '%s' is successfully" % (vmid, pool_name))
                    else:  # Хранилище в пуле не найдено, ничего не делаем
                        module.exit_json(changed=False, msg="VM not found in pool")
                else:  # Пул не найден, ничего не делаем
                    module.fail_json(msg="Pool '%s' not exists" % (pool_name))
            except Exception as e:
                module.fail_json(msg="Removing VM '%s' from pool '%s' failed with exception: %s" % (vmid, pool_name, e))
    else:
        module.exit_json(changed=True, msg="OLOLO--00000")


if __name__ == "__main__":
    main()
