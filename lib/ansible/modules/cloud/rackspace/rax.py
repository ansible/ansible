#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rax
short_description: create / delete an instance in Rackspace Public Cloud
description:
     - creates / deletes a Rackspace Public Cloud instance and optionally
       waits for it to be 'running'.
version_added: "1.2"
options:
  auto_increment:
    description:
      - Whether or not to increment a single number with the name of the
        created servers. Only applicable when used with the I(group) attribute
        or meta key.
    type: bool
    default: 'yes'
    version_added: 1.5
  boot_from_volume:
    description:
      - Whether or not to boot the instance from a Cloud Block Storage volume.
        If C(yes) and I(image) is specified a new volume will be created at
        boot time. I(boot_volume_size) is required with I(image) to create a
        new volume at boot time.
    type: bool
    default: 'no'
    version_added: 1.9
  boot_volume:
    description:
      - Cloud Block Storage ID or Name to use as the boot volume of the
        instance
    version_added: 1.9
  boot_volume_size:
    description:
      - Size of the volume to create in Gigabytes. This is only required with
        I(image) and I(boot_from_volume).
    default: 100
    version_added: 1.9
  boot_volume_terminate:
    description:
      - Whether the I(boot_volume) or newly created volume from I(image) will
        be terminated when the server is terminated
    type: bool
    default: 'no'
    version_added: 1.9
  config_drive:
    description:
      - Attach read-only configuration drive to server as label config-2
    type: bool
    default: 'no'
    version_added: 1.7
  count:
    description:
      - number of instances to launch
    default: 1
    version_added: 1.4
  count_offset:
    description:
      - number count to start at
    default: 1
    version_added: 1.4
  disk_config:
    description:
      - Disk partitioning strategy
    choices:
      - auto
      - manual
    version_added: '1.4'
    default: auto
  exact_count:
    description:
      - Explicitly ensure an exact count of instances, used with
        state=active/present. If specified as C(yes) and I(count) is less than
        the servers matched, servers will be deleted to match the count. If
        the number of matched servers is fewer than specified in I(count)
        additional servers will be added.
    type: bool
    default: 'no'
    version_added: 1.4
  extra_client_args:
    description:
      - A hash of key/value pairs to be used when creating the cloudservers
        client. This is considered an advanced option, use it wisely and
        with caution.
    version_added: 1.6
  extra_create_args:
    description:
      - A hash of key/value pairs to be used when creating a new server.
        This is considered an advanced option, use it wisely and with caution.
    version_added: 1.6
  files:
    description:
      - Files to insert into the instance. remotefilename:localcontent
  flavor:
    description:
      - flavor to use for the instance
  group:
    description:
      - host group to assign to server, is also used for idempotent operations
        to ensure a specific number of instances
    version_added: 1.4
  image:
    description:
      - image to use for the instance. Can be an C(id), C(human_id) or C(name).
        With I(boot_from_volume), a Cloud Block Storage volume will be created
        with this image
  instance_ids:
    description:
      - list of instance ids, currently only used when state='absent' to
        remove instances
    version_added: 1.4
  key_name:
    description:
      - key pair to use on the instance
    aliases:
      - keypair
  meta:
    description:
      - A hash of metadata to associate with the instance
  name:
    description:
      - Name to give the instance
  networks:
    description:
      - The network to attach to the instances. If specified, you must include
        ALL networks including the public and private interfaces. Can be C(id)
        or C(label).
    default:
      - public
      - private
    version_added: 1.4
  state:
    description:
      - Indicate desired state of the resource
    choices:
      - present
      - absent
    default: present
  user_data:
    description:
      - Data to be uploaded to the servers config drive. This option implies
        I(config_drive). Can be a file path or a string
    version_added: 1.7
  wait:
    description:
      - wait for the instance to be in state 'running' before returning
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
author:
    - "Jesse Keating (@omgjlk)"
    - "Matt Martz (@sivel)"
notes:
  - I(exact_count) can be "destructive" if the number of running servers in
    the I(group) is larger than that specified in I(count). In such a case, the
    I(state) is effectively set to C(absent) and the extra servers are deleted.
    In the case of deletion, the returned data structure will have C(action)
    set to C(delete), and the oldest servers in the group will be deleted.
extends_documentation_fragment: rackspace.openstack
'''

EXAMPLES = '''
- name: Build a Cloud Server
  gather_facts: False
  tasks:
    - name: Server build request
      local_action:
        module: rax
        credentials: ~/.raxpub
        name: rax-test1
        flavor: 5
        image: b11d9567-e412-4255-96b9-bd63ab23bcfe
        key_name: my_rackspace_key
        files:
          /root/test.txt: /home/localuser/test.txt
        wait: yes
        state: present
        networks:
          - private
          - public
      register: rax

- name: Build an exact count of cloud servers with incremented names
  hosts: local
  gather_facts: False
  tasks:
    - name: Server build requests
      local_action:
        module: rax
        credentials: ~/.raxpub
        name: test%03d.example.org
        flavor: performance1-1
        image: ubuntu-1204-lts-precise-pangolin
        state: present
        count: 10
        count_offset: 10
        exact_count: yes
        group: test
        wait: yes
      register: rax
'''

import json
import os
import re
import time

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rax import (FINAL_STATUSES, rax_argument_spec, rax_find_bootable_volume,
                                      rax_find_image, rax_find_network, rax_find_volume,
                                      rax_required_together, rax_to_dict, setup_rax_module)
from ansible.module_utils.six.moves import xrange
from ansible.module_utils.six import string_types


def rax_find_server_image(module, server, image, boot_volume):
    if not image and boot_volume:
        vol = rax_find_bootable_volume(module, pyrax, server,
                                       exit=False)
        if not vol:
            return None
        volume_image_metadata = vol.volume_image_metadata
        vol_image_id = volume_image_metadata.get('image_id')
        if vol_image_id:
            server_image = rax_find_image(module, pyrax,
                                          vol_image_id, exit=False)
            if server_image:
                server.image = dict(id=server_image)

    # Match image IDs taking care of boot from volume
    if image and not server.image:
        vol = rax_find_bootable_volume(module, pyrax, server)
        volume_image_metadata = vol.volume_image_metadata
        vol_image_id = volume_image_metadata.get('image_id')
        if not vol_image_id:
            return None
        server_image = rax_find_image(module, pyrax,
                                      vol_image_id, exit=False)
        if image != server_image:
            return None

        server.image = dict(id=server_image)
    elif image and server.image['id'] != image:
        return None

    return server.image


def create(module, names=None, flavor=None, image=None, meta=None, key_name=None,
           files=None, wait=True, wait_timeout=300, disk_config=None,
           group=None, nics=None, extra_create_args=None, user_data=None,
           config_drive=False, existing=None, block_device_mapping_v2=None):
    names = [] if names is None else names
    meta = {} if meta is None else meta
    files = {} if files is None else files
    nics = [] if nics is None else nics
    extra_create_args = {} if extra_create_args is None else extra_create_args
    existing = [] if existing is None else existing
    block_device_mapping_v2 = [] if block_device_mapping_v2 is None else block_device_mapping_v2

    cs = pyrax.cloudservers
    changed = False

    if user_data:
        config_drive = True

    if user_data and os.path.isfile(os.path.expanduser(user_data)):
        try:
            user_data = os.path.expanduser(user_data)
            f = open(user_data)
            user_data = f.read()
            f.close()
        except Exception as e:
            module.fail_json(msg='Failed to load %s' % user_data)

    # Handle the file contents
    for rpath in files.keys():
        lpath = os.path.expanduser(files[rpath])
        try:
            fileobj = open(lpath, 'r')
            files[rpath] = fileobj.read()
            fileobj.close()
        except Exception as e:
            module.fail_json(msg='Failed to load %s' % lpath)
    try:
        servers = []
        bdmv2 = block_device_mapping_v2
        for name in names:
            servers.append(cs.servers.create(name=name, image=image,
                                             flavor=flavor, meta=meta,
                                             key_name=key_name,
                                             files=files, nics=nics,
                                             disk_config=disk_config,
                                             config_drive=config_drive,
                                             userdata=user_data,
                                             block_device_mapping_v2=bdmv2,
                                             **extra_create_args))
    except Exception as e:
        if e.message:
            msg = str(e.message)
        else:
            msg = repr(e)
        module.fail_json(msg=msg)
    else:
        changed = True

    if wait:
        end_time = time.time() + wait_timeout
        infinite = wait_timeout == 0
        while infinite or time.time() < end_time:
            for server in servers:
                try:
                    server.get()
                except Exception:
                    server.status = 'ERROR'

            if not filter(lambda s: s.status not in FINAL_STATUSES,
                          servers):
                break
            time.sleep(5)

    success = []
    error = []
    timeout = []
    for server in servers:
        try:
            server.get()
        except Exception:
            server.status = 'ERROR'
        instance = rax_to_dict(server, 'server')
        if server.status == 'ACTIVE' or not wait:
            success.append(instance)
        elif server.status == 'ERROR':
            error.append(instance)
        elif wait:
            timeout.append(instance)

    untouched = [rax_to_dict(s, 'server') for s in existing]
    instances = success + untouched

    results = {
        'changed': changed,
        'action': 'create',
        'instances': instances,
        'success': success,
        'error': error,
        'timeout': timeout,
        'instance_ids': {
            'instances': [i['id'] for i in instances],
            'success': [i['id'] for i in success],
            'error': [i['id'] for i in error],
            'timeout': [i['id'] for i in timeout]
        }
    }

    if timeout:
        results['msg'] = 'Timeout waiting for all servers to build'
    elif error:
        results['msg'] = 'Failed to build all servers'

    if 'msg' in results:
        module.fail_json(**results)
    else:
        module.exit_json(**results)


def delete(module, instance_ids=None, wait=True, wait_timeout=300, kept=None):
    instance_ids = [] if instance_ids is None else instance_ids
    kept = [] if kept is None else kept

    cs = pyrax.cloudservers

    changed = False
    instances = {}
    servers = []

    for instance_id in instance_ids:
        servers.append(cs.servers.get(instance_id))

    for server in servers:
        try:
            server.delete()
        except Exception as e:
            module.fail_json(msg=e.message)
        else:
            changed = True

        instance = rax_to_dict(server, 'server')
        instances[instance['id']] = instance

    # If requested, wait for server deletion
    if wait:
        end_time = time.time() + wait_timeout
        infinite = wait_timeout == 0
        while infinite or time.time() < end_time:
            for server in servers:
                instance_id = server.id
                try:
                    server.get()
                except Exception:
                    instances[instance_id]['status'] = 'DELETED'
                    instances[instance_id]['rax_status'] = 'DELETED'

            if not filter(lambda s: s['status'] not in ('', 'DELETED',
                                                        'ERROR'),
                          instances.values()):
                break

            time.sleep(5)

    timeout = filter(lambda s: s['status'] not in ('', 'DELETED', 'ERROR'),
                     instances.values())
    error = filter(lambda s: s['status'] in ('ERROR'),
                   instances.values())
    success = filter(lambda s: s['status'] in ('', 'DELETED'),
                     instances.values())

    instances = [rax_to_dict(s, 'server') for s in kept]

    results = {
        'changed': changed,
        'action': 'delete',
        'instances': instances,
        'success': success,
        'error': error,
        'timeout': timeout,
        'instance_ids': {
            'instances': [i['id'] for i in instances],
            'success': [i['id'] for i in success],
            'error': [i['id'] for i in error],
            'timeout': [i['id'] for i in timeout]
        }
    }

    if timeout:
        results['msg'] = 'Timeout waiting for all servers to delete'
    elif error:
        results['msg'] = 'Failed to delete all servers'

    if 'msg' in results:
        module.fail_json(**results)
    else:
        module.exit_json(**results)


def cloudservers(module, state=None, name=None, flavor=None, image=None,
                 meta=None, key_name=None, files=None, wait=True, wait_timeout=300,
                 disk_config=None, count=1, group=None, instance_ids=None,
                 exact_count=False, networks=None, count_offset=0,
                 auto_increment=False, extra_create_args=None, user_data=None,
                 config_drive=False, boot_from_volume=False,
                 boot_volume=None, boot_volume_size=None,
                 boot_volume_terminate=False):
    meta = {} if meta is None else meta
    files = {} if files is None else files
    instance_ids = [] if instance_ids is None else instance_ids
    networks = [] if networks is None else networks
    extra_create_args = {} if extra_create_args is None else extra_create_args

    cs = pyrax.cloudservers
    cnw = pyrax.cloud_networks
    if not cnw:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    if state == 'present' or (state == 'absent' and instance_ids is None):
        if not boot_from_volume and not boot_volume and not image:
            module.fail_json(msg='image is required for the "rax" module')

        for arg, value in dict(name=name, flavor=flavor).items():
            if not value:
                module.fail_json(msg='%s is required for the "rax" module' %
                                     arg)

        if boot_from_volume and not image and not boot_volume:
            module.fail_json(msg='image or boot_volume are required for the '
                                 '"rax" with boot_from_volume')

        if boot_from_volume and image and not boot_volume_size:
            module.fail_json(msg='boot_volume_size is required for the "rax" '
                                 'module with boot_from_volume and image')

        if boot_from_volume and image and boot_volume:
            image = None

    servers = []

    # Add the group meta key
    if group and 'group' not in meta:
        meta['group'] = group
    elif 'group' in meta and group is None:
        group = meta['group']

    # Normalize and ensure all metadata values are strings
    for k, v in meta.items():
        if isinstance(v, list):
            meta[k] = ','.join(['%s' % i for i in v])
        elif isinstance(v, dict):
            meta[k] = json.dumps(v)
        elif not isinstance(v, string_types):
            meta[k] = '%s' % v

    # When using state=absent with group, the absent block won't match the
    # names properly. Use the exact_count functionality to decrease the count
    # to the desired level
    was_absent = False
    if group is not None and state == 'absent':
        exact_count = True
        state = 'present'
        was_absent = True

    if image:
        image = rax_find_image(module, pyrax, image)

    nics = []
    if networks:
        for network in networks:
            nics.extend(rax_find_network(module, pyrax, network))

    # act on the state
    if state == 'present':
        # Idempotent ensurance of a specific count of servers
        if exact_count is not False:
            # See if we can find servers that match our options
            if group is None:
                module.fail_json(msg='"group" must be provided when using '
                                     '"exact_count"')

            if auto_increment:
                numbers = set()

                # See if the name is a printf like string, if not append
                # %d to the end
                try:
                    name % 0
                except TypeError as e:
                    if e.message.startswith('not all'):
                        name = '%s%%d' % name
                    else:
                        module.fail_json(msg=e.message)

                # regex pattern to match printf formatting
                pattern = re.sub(r'%\d*[sd]', r'(\d+)', name)
                for server in cs.servers.list():
                    # Ignore DELETED servers
                    if server.status == 'DELETED':
                        continue
                    if server.metadata.get('group') == group:
                        servers.append(server)
                    match = re.search(pattern, server.name)
                    if match:
                        number = int(match.group(1))
                        numbers.add(number)

                number_range = xrange(count_offset, count_offset + count)
                available_numbers = list(set(number_range)
                                         .difference(numbers))
            else:  # Not auto incrementing
                for server in cs.servers.list():
                    # Ignore DELETED servers
                    if server.status == 'DELETED':
                        continue
                    if server.metadata.get('group') == group:
                        servers.append(server)
                # available_numbers not needed here, we inspect auto_increment
                # again later

            # If state was absent but the count was changed,
            # assume we only wanted to remove that number of instances
            if was_absent:
                diff = len(servers) - count
                if diff < 0:
                    count = 0
                else:
                    count = diff

            if len(servers) > count:
                # We have more servers than we need, set state='absent'
                # and delete the extras, this should delete the oldest
                state = 'absent'
                kept = servers[:count]
                del servers[:count]
                instance_ids = []
                for server in servers:
                    instance_ids.append(server.id)
                delete(module, instance_ids=instance_ids, wait=wait,
                       wait_timeout=wait_timeout, kept=kept)
            elif len(servers) < count:
                # we have fewer servers than we need
                if auto_increment:
                    # auto incrementing server numbers
                    names = []
                    name_slice = count - len(servers)
                    numbers_to_use = available_numbers[:name_slice]
                    for number in numbers_to_use:
                        names.append(name % number)
                else:
                    # We are not auto incrementing server numbers,
                    # create a list of 'name' that matches how many we need
                    names = [name] * (count - len(servers))
            else:
                # we have the right number of servers, just return info
                # about all of the matched servers
                instances = []
                instance_ids = []
                for server in servers:
                    instances.append(rax_to_dict(server, 'server'))
                    instance_ids.append(server.id)
                module.exit_json(changed=False, action=None,
                                 instances=instances,
                                 success=[], error=[], timeout=[],
                                 instance_ids={'instances': instance_ids,
                                               'success': [], 'error': [],
                                               'timeout': []})
        else:  # not called with exact_count=True
            if group is not None:
                if auto_increment:
                    # we are auto incrementing server numbers, but not with
                    # exact_count
                    numbers = set()

                    # See if the name is a printf like string, if not append
                    # %d to the end
                    try:
                        name % 0
                    except TypeError as e:
                        if e.message.startswith('not all'):
                            name = '%s%%d' % name
                        else:
                            module.fail_json(msg=e.message)

                    # regex pattern to match printf formatting
                    pattern = re.sub(r'%\d*[sd]', r'(\d+)', name)
                    for server in cs.servers.list():
                        # Ignore DELETED servers
                        if server.status == 'DELETED':
                            continue
                        if server.metadata.get('group') == group:
                            servers.append(server)
                        match = re.search(pattern, server.name)
                        if match:
                            number = int(match.group(1))
                            numbers.add(number)

                    number_range = xrange(count_offset,
                                          count_offset + count + len(numbers))
                    available_numbers = list(set(number_range)
                                             .difference(numbers))
                    names = []
                    numbers_to_use = available_numbers[:count]
                    for number in numbers_to_use:
                        names.append(name % number)
                else:
                    # Not auto incrementing
                    names = [name] * count
            else:
                # No group was specified, and not using exact_count
                # Perform more simplistic matching
                search_opts = {
                    'name': '^%s$' % name,
                    'flavor': flavor
                }
                servers = []
                for server in cs.servers.list(search_opts=search_opts):
                    # Ignore DELETED servers
                    if server.status == 'DELETED':
                        continue

                    if not rax_find_server_image(module, server, image,
                                                 boot_volume):
                        continue

                    # Ignore servers with non matching metadata
                    if server.metadata != meta:
                        continue
                    servers.append(server)

                if len(servers) >= count:
                    # We have more servers than were requested, don't do
                    # anything. Not running with exact_count=True, so we assume
                    # more is OK
                    instances = []
                    for server in servers:
                        instances.append(rax_to_dict(server, 'server'))

                    instance_ids = [i['id'] for i in instances]
                    module.exit_json(changed=False, action=None,
                                     instances=instances, success=[], error=[],
                                     timeout=[],
                                     instance_ids={'instances': instance_ids,
                                                   'success': [], 'error': [],
                                                   'timeout': []})

                # We need more servers to reach out target, create names for
                # them, we aren't performing auto_increment here
                names = [name] * (count - len(servers))

        block_device_mapping_v2 = []
        if boot_from_volume:
            mapping = {
                'boot_index': '0',
                'delete_on_termination': boot_volume_terminate,
                'destination_type': 'volume',
            }
            if image:
                mapping.update({
                    'uuid': image,
                    'source_type': 'image',
                    'volume_size': boot_volume_size,
                })
                image = None
            elif boot_volume:
                volume = rax_find_volume(module, pyrax, boot_volume)
                mapping.update({
                    'uuid': pyrax.utils.get_id(volume),
                    'source_type': 'volume',
                })
            block_device_mapping_v2.append(mapping)

        create(module, names=names, flavor=flavor, image=image,
               meta=meta, key_name=key_name, files=files, wait=wait,
               wait_timeout=wait_timeout, disk_config=disk_config, group=group,
               nics=nics, extra_create_args=extra_create_args,
               user_data=user_data, config_drive=config_drive,
               existing=servers,
               block_device_mapping_v2=block_device_mapping_v2)

    elif state == 'absent':
        if instance_ids is None:
            # We weren't given an explicit list of server IDs to delete
            # Let's match instead
            search_opts = {
                'name': '^%s$' % name,
                'flavor': flavor
            }
            for server in cs.servers.list(search_opts=search_opts):
                # Ignore DELETED servers
                if server.status == 'DELETED':
                    continue

                if not rax_find_server_image(module, server, image,
                                             boot_volume):
                    continue

                # Ignore servers with non matching metadata
                if meta != server.metadata:
                    continue

                servers.append(server)

            # Build a list of server IDs to delete
            instance_ids = []
            for server in servers:
                if len(instance_ids) < count:
                    instance_ids.append(server.id)
                else:
                    break

        if not instance_ids:
            # No server IDs were matched for deletion, or no IDs were
            # explicitly provided, just exit and don't do anything
            module.exit_json(changed=False, action=None, instances=[],
                             success=[], error=[], timeout=[],
                             instance_ids={'instances': [],
                                           'success': [], 'error': [],
                                           'timeout': []})

        delete(module, instance_ids=instance_ids, wait=wait,
               wait_timeout=wait_timeout)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            auto_increment=dict(default=True, type='bool'),
            boot_from_volume=dict(default=False, type='bool'),
            boot_volume=dict(type='str'),
            boot_volume_size=dict(type='int', default=100),
            boot_volume_terminate=dict(type='bool', default=False),
            config_drive=dict(default=False, type='bool'),
            count=dict(default=1, type='int'),
            count_offset=dict(default=1, type='int'),
            disk_config=dict(choices=['auto', 'manual']),
            exact_count=dict(default=False, type='bool'),
            extra_client_args=dict(type='dict', default={}),
            extra_create_args=dict(type='dict', default={}),
            files=dict(type='dict', default={}),
            flavor=dict(),
            group=dict(),
            image=dict(),
            instance_ids=dict(type='list'),
            key_name=dict(aliases=['keypair']),
            meta=dict(type='dict', default={}),
            name=dict(),
            networks=dict(type='list', default=['public', 'private']),
            service=dict(),
            state=dict(default='present', choices=['present', 'absent']),
            user_data=dict(no_log=True),
            wait=dict(default=False, type='bool'),
            wait_timeout=dict(default=300, type='int'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    service = module.params.get('service')

    if service is not None:
        module.fail_json(msg='The "service" attribute has been deprecated, '
                             'please remove "service: cloudservers" from your '
                             'playbook pertaining to the "rax" module')

    auto_increment = module.params.get('auto_increment')
    boot_from_volume = module.params.get('boot_from_volume')
    boot_volume = module.params.get('boot_volume')
    boot_volume_size = module.params.get('boot_volume_size')
    boot_volume_terminate = module.params.get('boot_volume_terminate')
    config_drive = module.params.get('config_drive')
    count = module.params.get('count')
    count_offset = module.params.get('count_offset')
    disk_config = module.params.get('disk_config')
    if disk_config:
        disk_config = disk_config.upper()
    exact_count = module.params.get('exact_count', False)
    extra_client_args = module.params.get('extra_client_args')
    extra_create_args = module.params.get('extra_create_args')
    files = module.params.get('files')
    flavor = module.params.get('flavor')
    group = module.params.get('group')
    image = module.params.get('image')
    instance_ids = module.params.get('instance_ids')
    key_name = module.params.get('key_name')
    meta = module.params.get('meta')
    name = module.params.get('name')
    networks = module.params.get('networks')
    state = module.params.get('state')
    user_data = module.params.get('user_data')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    setup_rax_module(module, pyrax)

    if extra_client_args:
        pyrax.cloudservers = pyrax.connect_to_cloudservers(
            region=pyrax.cloudservers.client.region_name,
            **extra_client_args)
        client = pyrax.cloudservers.client
        if 'bypass_url' in extra_client_args:
            client.management_url = extra_client_args['bypass_url']

    if pyrax.cloudservers is None:
        module.fail_json(msg='Failed to instantiate client. This '
                             'typically indicates an invalid region or an '
                             'incorrectly capitalized region name.')

    cloudservers(module, state=state, name=name, flavor=flavor,
                 image=image, meta=meta, key_name=key_name, files=files,
                 wait=wait, wait_timeout=wait_timeout, disk_config=disk_config,
                 count=count, group=group, instance_ids=instance_ids,
                 exact_count=exact_count, networks=networks,
                 count_offset=count_offset, auto_increment=auto_increment,
                 extra_create_args=extra_create_args, user_data=user_data,
                 config_drive=config_drive, boot_from_volume=boot_from_volume,
                 boot_volume=boot_volume, boot_volume_size=boot_volume_size,
                 boot_volume_terminate=boot_volume_terminate)


if __name__ == '__main__':
    main()
