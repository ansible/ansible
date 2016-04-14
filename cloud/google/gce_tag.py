#!/usr/bin/python
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>

DOCUMENTATION = '''
---
module: gce_tag
version_added: "2.0"
short_description: add or remove tag(s) to/from GCE instance
description:
    - This module can add or remove tags U(https://cloud.google.com/compute/docs/instances/#tags)
      to/from GCE instance.
options:
  instance_name:
    description:
      - the name of the GCE instance to add/remove tags
    required: true
    default: null
    aliases: []
  tags:
    description:
      - comma-separated list of tags to add or remove
    required: true
    default: null
    aliases: []
  state:
    description:
      - desired state of the tags
    required: false
    default: "present"
    choices: ["present", "absent"]
    aliases: []
  zone:
    description:
      - the zone of the disk specified by source
    required: false
    default: "us-central1-a"
    aliases: []
  service_account_email:
    description:
      - service account email
    required: false
    default: null
    aliases: []
  pem_file:
    description:
      - path to the pem file associated with the service account email
    required: false
    default: null
    aliases: []
  project_id:
    description:
      - your GCE project ID
    required: false
    default: null
    aliases: []

requirements:
    - "python >= 2.6"
    - "apache-libcloud"
author: "Do Hoang Khiem (dohoangkhiem@gmail.com)"
'''

EXAMPLES = '''
# Add tags 'http-server', 'https-server', 'staging' to instance name 'staging-server' in zone us-central1-a.
- gce_tag:
    instance_name: staging-server
    tags: http-server,https-server,staging
    zone: us-central1-a
    state: present

# Remove tags 'foo', 'bar' from instance 'test-server' in default zone (us-central1-a)
- gce_tag:
    instance_name: test-server
    tags: foo,bar
    state: absent

'''

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
        ResourceExistsError, ResourceNotFoundError, InvalidRequestError

    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False


def add_tags(gce, module, instance_name, tags):
    """Add tags to instance."""
    zone = module.params.get('zone')

    if not instance_name:
        module.fail_json(msg='Must supply instance_name', changed=False)

    if not tags:
        module.fail_json(msg='Must supply tags', changed=False)

    tags = [x.lower() for x in tags]

    try:
        node = gce.ex_get_node(instance_name, zone=zone)
    except ResourceNotFoundError:
        module.fail_json(msg='Instance %s not found in zone %s' % (instance_name, zone), changed=False)
    except GoogleBaseError, e:
        module.fail_json(msg=str(e), changed=False)

    node_tags = node.extra['tags']
    changed = False
    tags_changed = []

    for t in tags:
        if t not in node_tags:
            changed = True
            node_tags.append(t)
            tags_changed.append(t)

    if not changed:
        return False, None

    try:
        gce.ex_set_node_tags(node, node_tags)
        return True, tags_changed
    except (GoogleBaseError, InvalidRequestError) as e:
        module.fail_json(msg=str(e), changed=False)


def remove_tags(gce, module, instance_name, tags):
    """Remove tags from instance."""
    zone = module.params.get('zone')

    if not instance_name:
        module.fail_json(msg='Must supply instance_name', changed=False)

    if not tags:
        module.fail_json(msg='Must supply tags', changed=False)

    tags = [x.lower() for x in tags]

    try:
        node = gce.ex_get_node(instance_name, zone=zone)
    except ResourceNotFoundError:
        module.fail_json(msg='Instance %s not found in zone %s' % (instance_name, zone), changed=False)
    except GoogleBaseError, e:
        module.fail_json(msg=str(e), changed=False)

    node_tags = node.extra['tags']

    changed = False
    tags_changed = []

    for t in tags:
        if t in node_tags:
            node_tags.remove(t)
            changed = True
            tags_changed.append(t)

    if not changed:
        return False, None

    try:
        gce.ex_set_node_tags(node, node_tags)
        return True, tags_changed
    except (GoogleBaseError, InvalidRequestError) as e:
        module.fail_json(msg=str(e), changed=False)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance_name=dict(required=True),
            tags=dict(type='list'),
            state=dict(default='present', choices=['present', 'absent']),
            zone=dict(default='us-central1-a'),
            service_account_email=dict(),
            pem_file=dict(type='path'),
            project_id=dict(),
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support is required.')

    instance_name = module.params.get('instance_name')
    state = module.params.get('state')
    tags = module.params.get('tags')
    zone = module.params.get('zone')
    changed = False

    if not zone:
        module.fail_json(msg='Must specify "zone"', changed=False)

    if not tags:
        module.fail_json(msg='Must specify "tags"', changed=False)

    gce = gce_connect(module)

    # add tags to instance.
    if state == 'present':
        changed, tags_changed = add_tags(gce, module, instance_name, tags)

    # remove tags from instance
    if state == 'absent':
        changed, tags_changed = remove_tags(gce, module, instance_name, tags)

    module.exit_json(changed=changed, instance_name=instance_name, tags=tags_changed, zone=zone)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gce import *

if __name__ == '__main__':
    main()

