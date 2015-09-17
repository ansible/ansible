#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_remote_facts
short_description: ask EC2 for information about other instances.
description:
    - Only supports search for hostname by tags currently. Looking to add more later.
version_added: "2.0"
options:
  key:
    description:
      - instance tag key in EC2
    required: false
    default: Name
  value:
    description:
      - instance tag value in EC2
    required: false
    default: null
  lookup:
    description:
      - What type of lookup to use when searching EC2 instance info.
    required: false
    default: tags
  region:
    description:
      - EC2 region that it should look for tags in
    required: false
    default: All Regions
  ignore_state:
    description:
      - instance state that should be ignored such as terminated.
    required: false
    default: terminated
author:
    - "Michael Schuett (@michaeljs1990)"
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic provisioning example
- ec2_search:
    key: mykey
    value: myvalue
  register: servers
'''
try:
    import boto
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def todict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = todict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return todict(obj._ast())
    elif hasattr(obj, "__iter__"):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        # This Class causes a recursive loop and at this time is not worth
        # debugging. If it's useful later I'll look into it.
        if not isinstance(obj, boto.ec2.blockdevicemapping.BlockDeviceType):
            data = dict([(key, todict(value, classkey))
                for key, value in obj.__dict__.iteritems()
                if not callable(value) and not key.startswith('_')])
            if classkey is not None and hasattr(obj, "__class__"):
                data[classkey] = obj.__class__.__name__
            return data
    else:
        return obj

def get_all_ec2_regions(module):
    try:
        regions = boto.ec2.regions()
    except Exception, e:
        module.fail_json('Boto authentication issue: %s' % e)

    return regions

# Connect to ec2 region
def connect_to_region(region, module):
    try:
        conn = boto.ec2.connect_to_region(region.name)
    except Exception, e:
        print module.jsonify('error connecting to region: ' + region.name)
        conn = None
    # connect_to_region will fail "silently" by returning
    # None if the region name is wrong or not supported
    return conn

def main():
    module = AnsibleModule(
        argument_spec = dict(
            key = dict(default='Name'),
            value = dict(),
            lookup = dict(default='tags'),
            ignore_state = dict(default='terminated'),
            region = dict(),
        )
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    server_info = list()

    for region in get_all_ec2_regions(module):
        conn = connect_to_region(region, module)
        try:
            # Run when looking up by tag names, only returning hostname currently
            if module.params.get('lookup') == 'tags':
                ec2_key = 'tag:' + module.params.get('key')
                ec2_value = module.params.get('value')
                reservations = conn.get_all_instances(filters={ec2_key : ec2_value})
                for instance in [i for r in reservations for i in r.instances]:
                    if instance.private_ip_address != None:
                        instance.hostname = 'ip-' + instance.private_ip_address.replace('.', '-')
                    if instance._state.name not in module.params.get('ignore_state'):
                        server_info.append(todict(instance))
        except:
            print module.jsonify('error getting instances from: ' + region.name)

    ec2_facts_result = dict(changed=True, ec2=server_info)

    module.exit_json(**ec2_facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
