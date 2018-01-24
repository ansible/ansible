#!/usr/bin/python
# Copyright 2018 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_facts
version_added: "2.5"
short_description: Collect GCE instances facts
description:
     - Collect facts about Google Compute Engine (GCE) instances.  See
       U(https://cloud.google.com/compute) for an overview.
options:
  instance_names:
    description:
      - a comma-separated list of instance names to collect facts,
        parameter is mutually exclusive with name parameter.
    required: false
    default: null
  name:
    description:
      - either a name of a single instance or when used with 'num_instances',
        the base name of a cluster of nodes
    required: false
    default: null
  num_instances:
    description:
      - can be used with 'name', specifies
        the number of nodes to collect facts using 'name'
        as a base name
    required: false
    default: null
  zone:
    description:
      - the GCE zone to use. The list of available zones is at
        U(https://cloud.google.com/compute/docs/regions-zones/regions-zones#available).
    required: false
    default: "us-central1-a"
  project_id:
    description:
      - your GCE project ID
    required: false
    default: null
  service_account_email:
    description:
      - service account email
    required: false
    default: null
  credentials_file:
    description:
      - path to the JSON file associated with the service account email
    default: null
    required: false

requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials"
notes:
  - Either I(instance_names) or I(name) is required.
  - JSON credentials strongly preferred.
author: "Rahul Paigavan (@Rahul-CSI) <rahul.paigavan@cambridgesemantics.com>"
'''

EXAMPLES = '''
# Basic gce fact collect example.  Collect the facts for a single instance
# test-instance-000 in the us-central1-a Zone.
  gce_facts:
    name: test-instance-000
    zone: us-central1-a
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"

# Collect the facts for multiple instances with name as base name and
# num_instances as number of instance in the us-central1-a Zone.
# (e.g. test-instance-000,test-instance-001,test-instance-002)
  gce_facts:
    name: test-instance
    num_instances: 3
    zone: us-central1-a
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"

# Create multiple instances by specifying multiple names, separated by
# commas in the instance_names field
# (e.g. test-instance-000,test-instance-001,test-instance-002)
  gce_facts:
    instance_names: test-instance-000,test-instance-001,test-instance-002
    zone: us-central1-a
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"

---
# Example Playbook for provisioning.
- name: Compute Engine Facts Instance Examples
  hosts: localhost
  vars:
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"
  tasks:
    - name: create multiple instances
      # Basic provisioning example.  Create multiple Debian 8 instances in the
      # us-central1-a Zone of n1-standard-1 machine type.
      gce:
        instance_names: test1,test2,test3
        zone: us-central1-a
        machine_type: n1-standard-1
        image: debian-8
        state: present
        service_account_email: "{{ service_account_email }}"
        credentials_file: "{{ credentials_file }}"
        project_id: "{{ project_id }}"
        metadata : '{ "startup-script" : "apt-get update" }'

# Example Playbook for collecting facts.
- name: Compute Engine Facts Instance Examples
  hosts: localhost
  vars:
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"
  tasks:
    - name: Collect instance facts
      gce_facts:
        instance_names: test1,test2,test3
        zone: us-central1-a
        service_account_email: "{{ service_account_email }}"
        credentials_file: "{{ credentials_file }}"
        project_id: "{{ project_id }}"
      register: gce_facts

    - name: Print instance facts
      debug:
        msg: "{{ gce_facts }}"
'''

try:
    import libcloud
    from libcloud.compute.types import Provider
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect, unexpected_error_msg
from ansible.module_utils.gcp import get_valid_location
from ansible.modules.cloud.google.gce import get_instance_info


def instance_info(module, gce, instance_names, number, zone):
    """Collects the information of a list of instances.

    module: Ansible module object
    gce: authenticated GCE connection object
    instance_names: a list of instance names to collect facts
    zone: GCEZone object where the instances reside

    Returns a list of dictionaries, each dictionary contains information
    about the instance.

    """
    changed = False
    node_info = []

    if isinstance(instance_names, str) and number:
        node_names = ['%s-%03d' % (instance_names, i) for i in range(number)]
    elif isinstance(instance_names, str) and not number:
        node_names = [instance_names]
    else:
        node_names = instance_names

    for name in node_names:
        inst = None
        try:
            inst = gce.ex_get_node(name, zone)
        except Exception as e:
            module.fail_json(msg=unexpected_error_msg(e), changed=False)
        else:
            node_info.append(get_instance_info(inst))
    return (changed, node_info)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance_names=dict(),
            name=dict(aliases=['base_name']),
            num_instances=dict(type='int'),
            zone=dict(default='us-central1-a'),
            service_account_email=dict(),
            credentials_file=dict(type='path'),
            project_id=dict(),
        ),
        mutually_exclusive=[('instance_names', 'name')],
        required_one_of=[('instance_names', 'name')],
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support \
            (0.17.0+) required for this module')

    gce = gce_connect(module)

    instance_names = module.params.get('instance_names')
    name = module.params.get('name')
    number = module.params.get('num_instances')
    zone = module.params.get('zone')
    changed = False

    inames = None
    if isinstance(instance_names, list):
        inames = instance_names
    elif isinstance(instance_names, str):
        inames = instance_names.split(',')
    if name:
        inames = name
    if not inames:
        module.fail_json(msg='Must specify a "name" or "instance_names"',
                         changed=False)
    if not zone:
        module.fail_json(msg='Must specify a "zone"', changed=False)
    lc_zone = get_valid_location(module, gce, zone)

    json_output = {'zone': zone}
    (changed, nodes) = instance_info(
        module, gce, inames, number, lc_zone)
    json_output['instances'] = nodes
    json_output['changed'] = changed

    module.exit_json(**json_output)

if __name__ == '__main__':
    main()
