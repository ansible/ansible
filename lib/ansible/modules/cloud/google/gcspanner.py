#!/usr/bin/python
# Copyright 2017 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcspanner
version_added: "2.3"
short_description: Create and Delete Instances/Databases on Spanner.
description:
    - Create and Delete Instances/Databases on Spanner.
      See U(https://cloud.google.com/spanner/docs) for an overview.
requirements:
  - "python >= 2.6"
  - "google-auth >= 0.5.0"
  - "google-cloud-spanner >= 0.23.0"
notes:
  - Changing the configuration on an existing instance is not supported.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  configuration:
    description:
       - Configuration the instance should use. Examples are us-central1, asia-east1 and europe-west1.
    required: True
  instance_id:
    description:
       - GCP spanner instance name.
    required: True
  database_name:
    description:
       - Name of database contained on the instance.
    required: False
  force_instance_delete:
    description:
       - To delete an instance, this argument must exist and be true (along with state being equal to absent).
    required: False
    default: False
  instance_display_name:
    description:
       - Name of Instance to display.  If not specified, instance_id will be used instead.
    required: False
  node_count:
    description:
       - Number of nodes in the instance.  If not specified while creating an instance,
         node_count will be set to 1.
    required: False
  state:
    description: State of the instance or database (absent, present). Applies to the most granular
                 resource. If a database_name is specified we remove it.  If only instance_id
                 is specified, that is what is removed.
    required: False
    default: "present"
'''
EXAMPLES = '''
# Create instance.
gcspanner:
  instance_id: "{{ instance_id }}"
  configuration: "{{ configuration }}"
  state: present
  node_count: 1

# Create database.
gcspanner:
  instance_id: "{{ instance_id }}"
  configuration: "{{ configuration }}"
  database_name: "{{ database_name }}"
  state: present

# Delete instance (and all databases)
gcspanner:
  instance_id: "{{ instance_id }}"
  configuration: "{{ configuration }}"
  state: absent
  force_instance_delete: yes
'''

RETURN = '''
state:
    description: The state of the instance or database. Value will be either 'absent' or 'present'.
    returned: Always
    type: str
    sample: "present"

database_name:
    description: Name of database.
    returned: When database name is specified
    type: str
    sample: "mydatabase"

instance_id:
    description: Name of instance.
    returned: Always
    type: str
    sample: "myinstance"

previous_values:
   description: List of dictionaries containing previous values prior to update.
   returned: When an instance update has occurred and a field has been modified.
   type: dict
   sample: "'previous_values': { 'instance': { 'instance_display_name': 'my-instance', 'node_count': 1 } }"

updated:
   description: Boolean field to denote an update has occurred.
   returned: When an update has occurred.
   type: bool
   sample: True
'''
try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

try:
    from google.cloud import spanner
    from google.gax.errors import GaxError
    HAS_GOOGLE_CLOUD_SPANNER = True
except ImportError as e:
    HAS_GOOGLE_CLOUD_SPANNER = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import check_min_pkg_version, get_google_cloud_credentials
from ansible.module_utils.six import string_types


CLOUD_CLIENT = 'google-cloud-spanner'
CLOUD_CLIENT_MINIMUM_VERSION = '0.23.0'
CLOUD_CLIENT_USER_AGENT = 'ansible-spanner-0.1'

def get_spanner_configuration_name(config_name, project_name):
    config_name = 'projects/%s/instanceConfigs/regional-%s' % (project_name,
                                                               config_name)
    return config_name


def instance_update(instance):
    """
    Call update method on spanner client.

    Note: A ValueError exception is thrown despite the client succeeding.
    So, we validate the node_count and instance_display_name parameters and then
    ignore the ValueError exception.

    :param instance: a Spanner instance object
    :type instance: class `google.cloud.spanner.Instance`

    :returns True on success, raises ValueError on type error.
    :rtype ``bool``
    """
    errmsg = ''
    if not isinstance(instance.node_count, int):
        errmsg = 'node_count must be an integer %s (%s)' % (
            instance.node_count, type(instance.node_count))
    if instance.display_name and not isinstance(instance.display_name,
                                                string_types):
        errmsg = 'instance_display_name must be an string %s (%s)' % (
            instance.display_name, type(instance.display_name))
    if errmsg:
        raise ValueError(errmsg)

    try:
        instance.update()
    except ValueError:
        # The ValueError here is the one we 'expect'.
        pass

    return True


def main():
    module = AnsibleModule(argument_spec=dict(
        instance_id=dict(type='str', required=True),
        state=dict(choices=['absent', 'present'], default='present'),
        database_name=dict(type='str', default=None),
        configuration=dict(type='str', required=True),
        node_count=dict(type='int'),
        instance_display_name=dict(type='str', default=None),
        force_instance_delete=dict(type='bool', default=False),
        service_account_email=dict(),
        credentials_file=dict(),
        project_id=dict(), ), )

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")

    if not HAS_GOOGLE_CLOUD_SPANNER:
        module.fail_json(msg="Please install google-cloud-spanner.")

    if not check_min_pkg_version(CLOUD_CLIENT, CLOUD_CLIENT_MINIMUM_VERSION):
        module.fail_json(msg="Please install %s client version %s" %
                         (CLOUD_CLIENT, CLOUD_CLIENT_MINIMUM_VERSION))

    mod_params = {}
    mod_params['state'] = module.params.get('state')
    mod_params['instance_id'] = module.params.get('instance_id')
    mod_params['database_name'] = module.params.get('database_name')
    mod_params['configuration'] = module.params.get('configuration')
    mod_params['node_count'] = module.params.get('node_count', None)
    mod_params['instance_display_name'] = module.params.get('instance_display_name')
    mod_params['force_instance_delete'] = module.params.get('force_instance_delete')

    creds, params = get_google_cloud_credentials(module)
    spanner_client = spanner.Client(project=params['project_id'],
                                    credentials=creds,
                                    user_agent=CLOUD_CLIENT_USER_AGENT)
    changed = False
    json_output = {}

    i = None
    if mod_params['instance_id']:
        config_name = get_spanner_configuration_name(
            mod_params['configuration'], params['project_id'])
        i = spanner_client.instance(mod_params['instance_id'],
                                    configuration_name=config_name)
    d = None
    if mod_params['database_name']:
        # TODO(supertom): support DDL
        ddl_statements = ''
        d = i.database(mod_params['database_name'], ddl_statements)

    if mod_params['state'] == 'absent':
        # Remove the most granular resource.  If database is specified
        # we remove it.  If only instance is specified, that is what is removed.
        if d is not None and d.exists():
            d.drop()
            changed = True
        else:
            if i.exists():
                if mod_params['force_instance_delete']:
                    i.delete()
                else:
                    module.fail_json(
                        msg=(("Cannot delete Spanner instance: "
                              "'force_instance_delete' argument not specified")))
                changed = True
    elif mod_params['state'] == 'present':
        if not i.exists():
            i = spanner_client.instance(mod_params['instance_id'],
                                        configuration_name=config_name,
                                        display_name=mod_params['instance_display_name'],
                                        node_count=mod_params['node_count'] or 1)
            i.create()
            changed = True
        else:
            # update instance
            i.reload()
            inst_prev_vals = {}
            if i.display_name != mod_params['instance_display_name']:
                inst_prev_vals['instance_display_name'] = i.display_name
                i.display_name = mod_params['instance_display_name']
            if mod_params['node_count']:
                if i.node_count != mod_params['node_count']:
                    inst_prev_vals['node_count'] = i.node_count
                    i.node_count = mod_params['node_count']
            if inst_prev_vals:
                changed = instance_update(i)
                json_output['updated'] = changed
                json_output['previous_values'] = {'instance': inst_prev_vals}
        if d:
            if not d.exists():
                d.create()
                d.reload()
                changed = True

    json_output['changed'] = changed
    json_output.update(mod_params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
