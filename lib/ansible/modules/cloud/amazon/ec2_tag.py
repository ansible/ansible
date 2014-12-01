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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_tag 
short_description: create and remove tag(s) to ec2 resources.
description:
    - Creates, removes and lists tags from any EC2 resource.  The resource is referenced by its resource id (e.g. an instance being i-XXXXXXX). It is designed to be used with complex args (tags), see the examples.  This module has a dependency on python-boto.
version_added: "1.3"
options:
  resource:
    description:
      - The EC2 resource id. 
    required: true
    default: null 
    aliases: []
  state:
    description:
      - Whether the tags should be present or absent on the resource. Use list to interrogate the tags of an instance.
    required: false
    default: present
    choices: ['present', 'absent', 'list']
    aliases: []
  region:
    description:
      - region in which the resource exists. 
    required: false
    default: null
    aliases: ['aws_region', 'ec2_region']

author: Lester Wade
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Basic example of adding tag(s)
tasks:
- name: tag a resource
  ec2_tag: resource=vol-XXXXXX region=eu-west-1 state=present
  args:
    tags:
      Name: ubervol
      env: prod

# Playbook example of adding tag(s) to spawned instances
tasks:
- name: launch some instances
  ec2: keypair={{ keypair }} group={{ security_group }} instance_type={{ instance_type }} image={{ image_id }} wait=true region=eu-west-1
  register: ec2

- name: tag my launched instances
  ec2_tag: resource={{ item.id }} region=eu-west-1 state=present
  with_items: ec2.instances
  args:
    tags:
      Name: webserver
      env: prod
'''

import sys
import time

try:
    import boto.ec2
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            resource = dict(required=True),
            tags = dict(),
            state = dict(default='present', choices=['present', 'absent', 'list']),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    resource = module.params.get('resource')
    tags = module.params.get('tags')
    state = module.params.get('state')
  
    ec2 = ec2_connect(module)
    
    # We need a comparison here so that we can accurately report back changed status.
    # Need to expand the gettags return format and compare with "tags" and then tag or detag as appropriate.
    filters = {'resource-id' : resource}
    gettags = ec2.get_all_tags(filters=filters)
   
    dictadd = {}
    dictremove = {}
    baddict = {}
    tagdict = {}
    for tag in gettags:
        tagdict[tag.name] = tag.value

    if state == 'present':
        if not tags:
            module.fail_json(msg="tags argument is required when state is present")
        if set(tags.items()).issubset(set(tagdict.items())):
            module.exit_json(msg="Tags already exists in %s." %resource, changed=False)
        else:
            for (key, value) in set(tags.items()): 
                if (key, value) not in set(tagdict.items()):
                    dictadd[key] = value
        tagger = ec2.create_tags(resource, dictadd)
        gettags = ec2.get_all_tags(filters=filters)
        module.exit_json(msg="Tags %s created for resource %s." % (dictadd,resource), changed=True)
 
    if state == 'absent':
        if not tags:
            module.fail_json(msg="tags argument is required when state is absent")
        for (key, value) in set(tags.items()):
            if (key, value) not in set(tagdict.items()):
                    baddict[key] = value
                    if set(baddict) == set(tags):
                        module.exit_json(msg="Nothing to remove here. Move along.", changed=False)
        for (key, value) in set(tags.items()):
            if (key, value) in set(tagdict.items()):
                    dictremove[key] = value
        tagger = ec2.delete_tags(resource, dictremove)
        gettags = ec2.get_all_tags(filters=filters)
        module.exit_json(msg="Tags %s removed for resource %s." % (dictremove,resource), changed=True)

    if state == 'list':
        module.exit_json(changed=False, tags=tagdict)
    sys.exit(0)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
