#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2018, Artem Goncharov <artem.goncharov@gmail.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_tag
short_description: Manage tags on diverse OpenStack resources
extends_documentation_fragment: openstack
version_added: "2.8"
author: Artem Goncharov (@gtema)
description:
    - set or delete tags on the OpenStack resources
options:
   server:
      description:
        - Name or id of the Nova Server resource.
   floating_ip:
      description:
        - Name or id of the Floating IP resource.
   network:
      description:
        - Name or id of the Neutron Network resource.
   port:
      description:
        - Name or id of the Neutron Port resource.
   router:
      description:
        - Name or id of the Neutron Router resource.
   security_group:
      description:
        - Name or id of the Neutron SecurityGroup resource.
   security_group_rule:
      description:
        - Name or id of the Neutron SecurityGroupRule resource.
   subnet:
      description:
        - Name or id of the Neutron Subnet resource.
   trunk:
      description:
        - Name or id of the Neutron Trunk resource.
   state:
     description:
       - Should the resource be present or absent.
     choices: [ present, absent ]
     default: present
   tags:
     description:
       - List of tags
     default: []
   mode:
     description:
       - Mode to be used for tags presence ('replace' or 'set'). 'replace'
         will replace all existing tags, while 'set' only ensures given tags
         are present.
     choices: [replace, set]
     default: replace
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
notes:
    - One and only one of C(server), C(floating_ip), C(network), C(port),
      C(router), C(security_group), C(security_group_rule), C(subnet),
      C(trunk) should be set.
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''
EXAMPLES = '''
---
- name: replace all tags with a single tag on a server
  os_tag:
    server: "{{ server_name }}"
    state: present
    tags:
        - new_tag
    mode: replace

- name: replace all tags with a single tag on a network
  os_tag:
    network: "{{ network_name }}"
    state: present
    tags:
        - new_tag
    mode: replace

- name: append tags on instance
  os_tag:
    server: "{{ server_name }}"
    state: present
    mode: set
    tags:
        - new_tag1
        - new_tag2

- name: remove all tags
  os_tag:
    server: "{{ server_name }}"
    state: present
    tags:

- name: remove only given tags
  os_tag:
    server: "{{ server_name }}"
    state: present
    tags:
      - new_tag1
'''

RETURN = '''
tags:
    description: Present tags on the instance.
    returned: success
    type: list
    sample: ["tag1", "tag2"]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module
from ansible.module_utils._text import to_native


def _get_tags_url(url_prefix, instance):
    """Construct direct REST query URL for tags"""
    return (
        '%(url_prefix)s/%(instance)s/tags'
        % {'url_prefix': url_prefix, 'instance': instance.id}
    )


def _get_tag_url(url_prefix, instance, tag):
    """Construct direct REST query URL for individual tag"""
    return (
        '%(url_prefix)s/%(instance)s/tags/%(tag)s'
        % {
            'url_prefix': url_prefix,
            'instance': instance.id,
            'tag': tag
        }
    )


def fetch_tags(module, conn, url_prefix, microver, instance):
    """Get current tags"""
    result = None
    try:
        inst = instance.fetch_tags(conn)
        result = inst.tags
    except AttributeError:
        # Try a low-level access if SDK version is old
        response = conn.get(
            _get_tags_url(url_prefix, instance),
            microversion=microver)

        if response.content and response.status_code < 400:
            result = response.json()['tags']
        else:
            module.fail_json(msg='Request failed: %s' % response.reason)

    return result


def replace_tags(module, conn, url_prefix, microver, instance, tags):
    """Replace all tags at once"""
    result = None
    try:
        inst = instance.set_tags(conn, tags)
        result = inst.tags
    except AttributeError:
        # Try a low-level access if SDK version is old
        data = {'tags': tags}
        response = conn.put(
            _get_tags_url(url_prefix, instance),
            json=data, microversion=microver)
        if response.content and response.status_code < 400:
            result = response.json()['tags']
        else:
            module.fail_json(
                msg='API returned something bad %s' % response.reason)
    return result


def set_tags(module, conn, url_prefix, microver, instance, tags):
    """Set tag on a server one by one"""
    try:
        for tag in tags:
            instance.add_tag(conn, tag)
    except AttributeError:
        # Try a low-level access if SDK version is old
        for tag in tags:
            response = conn.put(
                _get_tag_url(url_prefix, instance, tag),
                microversion=microver)
            if response.status_code not in [201, 204]:
                module.fail_json(
                    msg='API returned something bad %s' % response.reason)
    return fetch_tags(module, conn, url_prefix, microver, instance)


def delete_tags(module, conn, url_prefix, microver, instance, tags):
    """Set tag on a resource one by one"""
    try:
        for tag in tags:
            instance.remove_tag(conn, tag)
    except AttributeError:
        # Try a low-level access if SDK version is old
        for tag in tags:
            response = conn.delete(
                _get_tag_url(url_prefix, instance, tag),
                microversion=microver)
            if response.status_code not in [204, 404]:
                module.fail_json(
                    msg='API returned something bad %s' % response.reason)
    return fetch_tags(module, conn, url_prefix, microver, instance)


def main():

    argument_spec = openstack_full_argument_spec(
        server=dict(default=None),
        floating_ip=dict(default=None),
        network=dict(default=None),
        port=dict(default=None),
        router=dict(default=None),
        security_group_rule=dict(default=None),
        security_group=dict(default=None),
        subnet=dict(default=None),
        trunk=dict(default=None),
        state=dict(default='present', choices=['absent', 'present']),
        tags=dict(default=[], type=list),
        mode=dict(default='replace', choices=['replace', 'set'])
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    server = module.params['server']
    floating_ip = module.params['floating_ip']
    network = module.params['network']
    port = module.params['port']
    router = module.params['router']
    security_group_rule = module.params['security_group_rule']
    security_group = module.params['security_group']
    subnet = module.params['subnet']
    trunk = module.params['trunk']
    state = module.params['state']
    new_tags = module.params['tags'] or []
    mode = module.params['mode']
    changed = False
    resource = None
    microver = None

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if server:
            instance = cloud.get_server(server)
            url_prefix = '/servers'
            endpoint = cloud.compute
            resource = server
            microver = '2.26'
        elif floating_ip:
            instance = cloud.get_floating_ip(floating_ip)
            url_prefix = '/floatingips'
            endpoint = cloud.network
            resource = floating_ip
        elif network:
            instance = cloud.get_network(network)
            url_prefix = '/networks'
            endpoint = cloud.network
            resource = network
        elif port:
            instance = cloud.get_port(port)
            url_prefix = '/ports'
            endpoint = cloud.network
            resource = port
        elif router:
            instance = cloud.get_router(router)
            url_prefix = '/routers'
            endpoint = cloud.network
            resource = router
        elif security_group_rule:
            instance = cloud.get_security_group_rule(security_group_rule)
            url_prefix = '/security-group-rules'
            endpoint = cloud.network
            resource = security_group_rule
        elif security_group:
            instance = cloud.get_security_group(security_group)
            url_prefix = '/security-groups'
            endpoint = cloud.network
            resource = security_group
        elif subnet:
            instance = cloud.get_subnet(subnet)
            url_prefix = '/subnets'
            endpoint = cloud.network
            resource = subnet
        elif trunk:
            instance = cloud.get_trunk(trunk)
            url_prefix = '/trunks'
            endpoint = cloud.network
            resource = trunk
        else:
            module.fail_json(msg='Any of the supported should be given')

        if instance:
            current_tags = fetch_tags(
                module, endpoint, url_prefix, microver, instance)
            if state == 'present':
                if mode == 'replace' and set(current_tags) != set(new_tags):
                    # Any of the tags mismatch
                    changed = True
                elif mode == 'set' and any(
                        x not in current_tags for x in new_tags):
                    # At least one tag should be set
                    changed = True
            elif state == 'absent' and any(
                    x in current_tags for x in new_tags):
                # At least one tag should be removed
                changed = True

            if module.check_mode or not changed:
                module.exit_json(
                    changed=changed,
                    tags=new_tags)

            if state == 'present':
                if mode == 'replace':
                    tags = replace_tags(
                        module, endpoint, url_prefix, microver,
                        instance, new_tags)
                elif mode == 'set':
                    tags = set_tags(
                        module, endpoint, url_prefix, microver,
                        instance, new_tags)
            elif state == 'absent':
                tags = delete_tags(
                    module, endpoint, url_prefix, microver,
                    instance, new_tags)

            module.exit_json(
                changed=changed,
                tags=tags)
        else:
            module.fail_json(msg='Instance %s can not be found'
                             % resource)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
