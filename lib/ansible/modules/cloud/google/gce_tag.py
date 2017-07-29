#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_tag
version_added: "2.0"
short_description: add or remove tag(s) to/from GCE instances
description:
    - This module can add or remove tags U(https://cloud.google.com/compute/docs/label-or-tag-resources#tags)
      to/from GCE instances.  Use 'instance_pattern' to update multiple instances in a specify zone
options:
  instance_name:
    description:
      - The name of the GCE instance to add/remove tags.  Required if instance_pattern is not specified.
    required: false
    default: null
    aliases: []
  instance_pattern:
    description:
      - The pattern of GCE instance names to match for adding/removing tags.  Full-Python regex is supported.
        See U(https://docs.python.org/2/library/re.html) for details.
        If instance_name is not specified, this field is required.
    required: false
    default: null
    aliases: []
    version_added: "2.3"
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
    - "apache-libcloud >= 0.17.0"
notes:
 - Either I(instance_name) or I(instance_pattern) is required.
author:
 - Do Hoang Khiem (dohoangkhiem@gmail.com)
 - Tom Melendez (@supertom)
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

# Add tags 'foo', 'bar' to instances in zone that match pattern
- gce_tag:
    instance_pattern: test-server-*
    tags: foo,bar
    zone: us-central1-a
    state: present

'''
import re
import traceback

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
        ResourceExistsError, ResourceNotFoundError, InvalidRequestError

    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect


def _union_items(baselist, comparelist):
    """Combine two lists, removing duplicates."""
    return list(set(baselist) | set(comparelist))

def _intersect_items(baselist, comparelist):
    """Return matching items in both lists."""
    return list(set(baselist) & set(comparelist))

def _get_changed_items(baselist, comparelist):
    """Return changed items as they relate to baselist."""
    return list(set(baselist) & set(set(baselist) ^ set(comparelist)))

def modify_tags(gce, module, node, tags, state='present'):
    """Modify tags on an instance."""

    existing_tags = node.extra['tags']
    tags = [x.lower() for x in tags]
    tags_changed = []

    if state == 'absent':
        # tags changed are any that intersect
        tags_changed = _intersect_items(existing_tags, tags)
        if not tags_changed:
            return False, None
        # update instance with tags in existing tags that weren't specified
        node_tags = _get_changed_items(existing_tags, tags)
    else:
        # tags changed are any that in the new list that weren't in existing
        tags_changed = _get_changed_items(tags, existing_tags)
        if not tags_changed:
            return False, None
        # update instance with the combined list
        node_tags = _union_items(existing_tags, tags)

    try:
        gce.ex_set_node_tags(node, node_tags)
        return True, tags_changed
    except (GoogleBaseError, InvalidRequestError) as e:
        module.fail_json(msg=str(e), changed=False)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance_name=dict(required=False),
            instance_pattern=dict(required=False),
            tags=dict(type='list', required=True),
            state=dict(default='present', choices=['present', 'absent']),
            zone=dict(default='us-central1-a'),
            service_account_email=dict(),
            pem_file=dict(type='path'),
            project_id=dict(),
        ),
        mutually_exclusive=[
            [ 'instance_name', 'instance_pattern' ]
        ],
        required_one_of=[
            [ 'instance_name', 'instance_pattern' ]
        ]
    )

    instance_name = module.params.get('instance_name')
    instance_pattern = module.params.get('instance_pattern')
    state = module.params.get('state')
    tags = module.params.get('tags')
    zone = module.params.get('zone')
    changed = False

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.17.0+) required for this module')

    gce = gce_connect(module)

    # Create list of nodes to operate on
    matching_nodes = []
    try:
        if instance_pattern:
            instances = gce.list_nodes(ex_zone=zone)
            # no instances in zone
            if not instances:
                module.exit_json(changed=False, tags=tags, zone=zone, instances_updated=[])
            try:
                # Python regex fully supported: https://docs.python.org/2/library/re.html
                p = re.compile(instance_pattern)
                matching_nodes = [i for i in instances if p.search(i.name) is not None]
            except re.error as e:
                module.fail_json(msg='Regex error for pattern %s: %s' % (instance_pattern, e), changed=False)
        else:
            matching_nodes = [gce.ex_get_node(instance_name, zone=zone)]
    except ResourceNotFoundError:
        module.fail_json(msg='Instance %s not found in zone %s' % (instance_name, zone), changed=False)
    except GoogleBaseError as e:
        module.fail_json(msg=str(e), changed=False, exception=traceback.format_exc())

    # Tag nodes
    instance_pattern_matches = []
    tags_changed = []
    for node in matching_nodes:
        changed, tags_changed = modify_tags(gce, module, node, tags, state)
        if changed:
            instance_pattern_matches.append({'instance_name': node.name, 'tags_changed': tags_changed})
    if instance_pattern:
        module.exit_json(changed=changed, instance_pattern=instance_pattern, tags=tags_changed, zone=zone, instances_updated=instance_pattern_matches)
    else:
        module.exit_json(changed=changed, instance_name=instance_name, tags=tags_changed, zone=zone)


if __name__ == '__main__':
    main()
