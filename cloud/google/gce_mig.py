#!/usr/bin/python
# Copyright 2016 Google Inc.
#
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
module: gce_mig
version_added: "2.2"
short_description: Create, Update or Destroy a Managed Instance Group (MIG).
description:
    - Create, Update or Destroy a Managed Instance Group (MIG).  See
      U(https://cloud.google.com/compute/docs/instance-groups) for an overview.
      Full install/configuration instructions for the gce* modules can
      be found in the comments of ansible/test/gce_tests.py.
requirements:
  - "python >= 2.6"
  - "apache-libcloud >= 1.2.0"
notes:
  - Resizing and Recreating VM are also supported.
  - An existing instance template is required in order to create a
    Managed Instance Group.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  name:
    description:
       - Name of the Managed Instance Group.
    required: true
  template:
    description:
       - Instance Template to be used in creating the VMs.  See
         U(https://cloud.google.com/compute/docs/instance-templates) to learn more
         about Instance Templates.  Required for creating MIGs.
    required: false
  size:
    description:
       - Size of Managed Instance Group.  If MIG already exists, it will be
         resized to the number provided here.  Required for creating MIGs.
    required: false
  service_account_email:
    description:
      - service account email
    required: false
    default: null
  credentials_file:
    description:
      - Path to the JSON file associated with the service account email
    default: null
    required: false
  project_id:
    description:
      - GCE project ID
    required: false
    default: null
  state:
    description:
      - desired state of the resource
    required: false
    default: "present"
    choices: ["absent", "present"]
  zone:
    description:
      - The GCE zone to use for this Managed Instance Group.
    required: true
  autoscaling:
    description:
      - A dictionary of configuration for the autoscaler. 'enabled (bool)', 'name (str)'
        and policy.max_instances (int) are required fields if autoscaling is used. See
        U(https://cloud.google.com/compute/docs/reference/beta/autoscalers) for more information
        on Autoscaling.
    required: false
    default: null
'''

EXAMPLES = '''
# Following playbook creates, rebuilds instances, resizes and then deletes a MIG.
# Notes:
# - Two valid Instance Templates must exist in your GCE project in order to run
#   this playbook.  Change the fields to match the templates used in your
#   project.
# - The use of the 'pause' module is not required, it is just for convenience.
- name: Managed Instance Group Example
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Create MIG
      gce_mig:
        name: ansible-mig-example
        zone: us-central1-c
        state: present
        size: 1
        template: my-instance-template-1
    - pause: seconds=30
    - name: Recreate MIG Instances with Instance Template change.
      gce_mig:
        name: ansible-mig-example
        zone: us-central1-c
        state: present
        template: my-instance-template-2-small
        recreate_instances: yes
    - pause: seconds=30
    - name: Resize MIG
      gce_mig:
        name: ansible-mig-example
        zone: us-central1-c
        state: present
        size: 3
    - name: Update MIG with Autoscaler
      gce_mig:
        name: ansible-mig-example
        zone: us-central1-c
        state: present
        size: 3
        template: my-instance-template-2-small
        recreate_instances: yes
        autoscaling:
          enabled: yes
          name: my-autoscaler
          policy:
            min_instances: 2
            max_instances: 5
            cool_down_period: 37
            cpu_utilization:
              target: .39
            load_balancing_utilization:
              target: 0.4
    - pause: seconds=30
    - name: Delete MIG
      gce_mig:
        name: ansible-mig-example
        zone: us-central1-c
        state: absent
        autoscaling:
          enabled: no
          name: my-autoscaler
'''
RETURN = '''
zone:
    description: Zone in which to launch MIG.
    returned: always
    type: string
    sample: "us-central1-b"

template:
    description: Instance Template to use for VMs.  Must exist prior to using with MIG.
    returned: changed
    type: string
    sample: "my-instance-template"

name:
    description: Name of the Managed Instance Group.
    returned: changed
    type: string
    sample: "my-managed-instance-group"

size:
    description: Number of VMs in Managed Instance Group.
    returned: changed
    type: integer
    sample: 4

created_instances:
    description: Names of instances created.
    returned: When instances are created.
    type: list
    sample: ["ansible-mig-new-0k4y", "ansible-mig-new-0zk5", "ansible-mig-new-kp68"]

deleted_instances:
    description: Names of instances deleted.
    returned: When instances are deleted.
    type: list
    sample: ["ansible-mig-new-0k4y", "ansible-mig-new-0zk5", "ansible-mig-new-kp68"]

resize_created_instances:
    description: Names of instances created during resizing.
    returned: When a resize results in the creation of instances.
    type: list
    sample: ["ansible-mig-new-0k4y", "ansible-mig-new-0zk5", "ansible-mig-new-kp68"]

resize_deleted_instances:
    description: Names of instances deleted during resizing.
    returned: When a resize results in the deletion of instances.
    type: list
    sample: ["ansible-mig-new-0k4y", "ansible-mig-new-0zk5", "ansible-mig-new-kp68"]

recreated_instances:
    description: Names of instances recreated.
    returned: When instances are recreated.
    type: list
    sample: ["ansible-mig-new-0k4y", "ansible-mig-new-0zk5", "ansible-mig-new-kp68"]

created_autoscaler:
    description: True if Autoscaler was attempted and created.  False otherwise.
    returned: When the creation of an Autoscaler was attempted.
    type: bool
    sample: true

updated_autoscaler:
    description: True if an Autoscaler update was attempted and succeeded.
                 False returned if update failed.
    returned: When the update of an Autoscaler was attempted.
    type: bool
    sample: true

deleted_autoscaler:
    description: True if an Autoscaler delete attempted and succeeded.
                 False returned if delete failed.
    returned: When the delete of an Autoscaler was attempted.
    type: bool
    sample: true
'''

import socket

try:
    import libcloud
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
        ResourceExistsError, ResourceInUseError, ResourceNotFoundError
    from libcloud.compute.drivers.gce import GCEAddress
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False


def _check_params(params, field_list):
    """ 
    Helper to validate params.

    Use this in function definitions if they require specific fields
    to be present.

    :param params: structure that contains the fields
    :type params: ``dict``

    :param field_list: list of dict representing the fields
                       [{'name': str, 'required': True/False', 'type': cls}]
    :type field_list: ``list`` of ``dict``

    :return True, exits otherwise
    :rtype: ``bool``
    """
    for d in field_list:
        if not d['name'] in params:
            if d['required'] is True:
                return (False, "%s is required and must be of type: %s" %
                        (d['name'], str(d['type'])))
        else:
            if not isinstance(params[d['name']], d['type']):
                return (False,
                        "%s must be of type: %s" % (d['name'], str(d['type'])))

    return (True, '')


def _validate_autoscaling_params(params):
    """ 
    Validate that the minimum configuration is present for autoscaling.

    :param params: Ansible dictionary containing autoscaling configuration
                   It is expected that autoscaling config will be found at the
                   key 'autoscaling'.
    :type  params: ``dict``

    :return: Tuple containing a boolean and a string.  True if autoscaler 
             is valid, False otherwise, plus str for message.
    :rtype: ``(``bool``, ``str``)``
    """
    if not params['autoscaling']:
        # It's optional, so if not set at all, it's valid.
        return (True, '')
    if not isinstance(params['autoscaling'], dict):
        return (False,
                'autoscaling: configuration expected to be a dictionary.')

    # check first-level required fields
    as_req_fields = [
        {'name': 'name', 'required': True, 'type': str},
        {'name': 'enabled', 'required': True, 'type': bool},
        {'name': 'policy', 'required': True, 'type': dict}
    ] # yapf: disable

    (as_req_valid, as_req_msg) = _check_params(params['autoscaling'],
                                               as_req_fields)
    if not as_req_valid:
        return (False, as_req_msg)

    # check policy configuration
    as_policy_fields = [
        {'name': 'max_instances', 'required': True, 'type': int},
        {'name': 'min_instances', 'required': False, 'type': int},
        {'name': 'cool_down_period', 'required': False, 'type': int}
    ] # yapf: disable

    (as_policy_valid, as_policy_msg) = _check_params(
        params['autoscaling']['policy'], as_policy_fields)
    if not as_policy_valid:
        return (False, as_policy_msg)

    # TODO(supertom): check utilization fields

    return (True, '')


def _get_instance_list(mig, field='name', filter_list=['NONE']):
    """ 
    Helper to grab field from instances response.

    :param mig: Managed Instance Group Object from libcloud.
    :type mig:  :class: `GCEInstanceGroupManager`

    :param field: Field name in list_managed_instances response.  Defaults
                  to 'name'.
    :type  field: ``str``

    :param filter_list: list of 'currentAction' strings to filter on.  Only
                        items that match a currentAction in this list will
                        be returned.  Default is "['NONE']".
    :type  filter_list: ``list`` of ``str``

    :return: List of strings from list_managed_instances response.
    :rtype: ``list``
    """
    return [x[field] for x in mig.list_managed_instances()
            if x['currentAction'] in filter_list]


def _gen_gce_as_policy(as_params):
    """ 
    Take Autoscaler params and generate GCE-compatible policy.

    :param as_params: Dictionary in Ansible-playbook format 
                      containing policy arguments.
    :type as_params: ``dict``

    :return: GCE-compatible policy dictionary
    :rtype: ``dict``
    """
    asp_data = {}
    asp_data['maxNumReplicas'] = as_params['max_instances']
    if 'min_instances' in as_params:
        asp_data['minNumReplicas'] = as_params['min_instances']
    if 'cool_down_period' in as_params:
        asp_data['coolDownPeriodSec'] = as_params['cool_down_period']
    if 'cpu_utilization' in as_params and 'target' in as_params[
            'cpu_utilization']:
        asp_data['cpuUtilization'] = {'utilizationTarget':
                                      as_params['cpu_utilization']['target']}
    if 'load_balancing_utilization' in as_params and 'target' in as_params[
            'load_balancing_utilization']:
        asp_data['loadBalancingUtilization'] = {
            'utilizationTarget':
            as_params['load_balancing_utilization']['target']
        }

    return asp_data


def create_autoscaler(gce, mig, params):
    """
    Create a new Autoscaler for a MIG.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param mig: An initialized GCEInstanceGroupManager.
    :type mig:  :class: `GCEInstanceGroupManager`

    :param params: Dictionary of autoscaling parameters.
    :type params:  ``dict``

    :return: Tuple with changed stats.
    :rtype: tuple in the format of (bool, list)
    """
    changed = False
    as_policy = _gen_gce_as_policy(params['policy'])
    autoscaler = gce.ex_create_autoscaler(name=params['name'], zone=mig.zone,
                                          instance_group=mig, policy=as_policy)
    if autoscaler:
        changed = True
    return changed


def update_autoscaler(gce, autoscaler, params):
    """
    Update an Autoscaler.

    Takes an existing Autoscaler object, and updates it with
    the supplied params before calling libcloud's update method.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param autoscaler: An initialized GCEAutoscaler.
    :type  autoscaler:  :class: `GCEAutoscaler`

    :param params: Dictionary of autoscaling parameters.
    :type params:  ``dict``

    :return: True if changes, False otherwise.
    :rtype: ``bool``
    """
    as_policy = _gen_gce_as_policy(params['policy'])
    if autoscaler.policy != as_policy:
        autoscaler.policy = as_policy
        autoscaler = gce.ex_update_autoscaler(autoscaler)
        if autoscaler:
            return True
    return False


def delete_autoscaler(autoscaler):
    """
    Delete an Autoscaler.  Does not affect MIG.

    :param mig: Managed Instance Group Object from Libcloud.
    :type mig:  :class: `GCEInstanceGroupManager`

    :return: Tuple with changed stats and a list of affected instances.
    :rtype: tuple in the format of (bool, list)
    """
    changed = False
    if autoscaler.destroy():
        changed = True
    return changed


def get_autoscaler(gce, name, zone):
    """
    Get an Autoscaler from GCE.

    If the Autoscaler is not found, None is found.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param name: Name of the Autoscaler.
    :type name:  ``str``

    :param zone: Zone that the Autoscaler is located in.
    :type zone:  ``str``

    :return: A GCEAutoscaler object or None.
    :rtype: :class: `GCEAutoscaler` or None
    """
    try:
        # Does the Autoscaler already exist?
        return gce.ex_get_autoscaler(name, zone)

    except ResourceNotFoundError:
        return None


def create_mig(gce, params):
    """
    Create a new Managed Instance Group.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param params: Dictionary of parameters needed by the module.
    :type params:  ``dict``

    :return: Tuple with changed stats and a list of affected instances.
    :rtype: tuple in the format of (bool, list)
    """

    changed = False
    return_data = []
    actions_filter = ['CREATING']

    mig = gce.ex_create_instancegroupmanager(
        name=params['name'], size=params['size'], template=params['template'],
        zone=params['zone'])

    if mig:
        changed = True
        return_data = _get_instance_list(mig, filter_list=actions_filter)

    return (changed, return_data)


def delete_mig(mig):
    """
    Delete a Managed Instance Group.  All VMs in that MIG are also deleted."

    :param mig: Managed Instance Group Object from Libcloud.
    :type mig:  :class: `GCEInstanceGroupManager`

    :return: Tuple with changed stats and a list of affected instances.
    :rtype: tuple in the format of (bool, list)
    """
    changed = False
    return_data = []
    actions_filter = ['NONE', 'CREATING', 'RECREATING', 'DELETING',
                      'ABANDONING', 'RESTARTING', 'REFRESHING']
    instance_names = _get_instance_list(mig, filter_list=actions_filter)
    if mig.destroy():
        changed = True
        return_data = instance_names

    return (changed, return_data)


def recreate_instances_in_mig(mig):
    """
    Recreate the instances for a Managed Instance Group.

    :param mig: Managed Instance Group Object from libcloud.
    :type mig:  :class: `GCEInstanceGroupManager`

    :return: Tuple with changed stats and a list of affected instances.
    :rtype: tuple in the format of (bool, list)
    """
    changed = False
    return_data = []
    actions_filter = ['RECREATING']

    if mig.recreate_instances():
        changed = True
        return_data = _get_instance_list(mig, filter_list=actions_filter)

    return (changed, return_data)


def resize_mig(mig, size):
    """
    Resize a Managed Instance Group.

    Based on the size provided, GCE will automatically create and delete
    VMs as needed.

    :param mig: Managed Instance Group Object from libcloud.
    :type mig:  :class: `GCEInstanceGroupManager`

    :return: Tuple with changed stats and a list of affected instances.
    :rtype: tuple in the format of (bool, list)
    """
    changed = False
    return_data = []
    actions_filter = ['CREATING', 'DELETING']

    if mig.resize(size):
        changed = True
        return_data = _get_instance_list(mig, filter_list=actions_filter)

    return (changed, return_data)


def get_mig(gce, name, zone):
    """
    Get a Managed Instance Group from GCE.

    If the MIG is not found, None is found.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param name: Name of the Managed Instance Group.
    :type name:  ``str``

    :param zone: Zone that the Managed Instance Group is located in.
    :type zone:  ``str``

    :return: A GCEInstanceGroupManager object or None.
    :rtype: :class: `GCEInstanceGroupManager` or None
    """
    try:
        # Does the MIG already exist?
        return gce.ex_get_instancegroupmanager(name=name, zone=zone)

    except ResourceNotFoundError:
        return None


def main():

    module = AnsibleModule(argument_spec=dict(
        name=dict(required=True),
        template=dict(),
        recreate_instances=dict(type='bool', default=False),
        # Do not set a default size here.  For Create and some update
        # operations, it is required and should be explicitly set.
        # Below, we set it to the existing value if it has not been set.
        size=dict(type='int'),
        state=dict(choices=['absent', 'present'], default='present'),
        zone=dict(required=True),
        autoscaling=dict(type='dict', default=None),
        service_account_email=dict(),
        service_account_permissions=dict(type='list'),
        pem_file=dict(),
        credentials_file=dict(),
        project_id=dict(), ), )

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg='libcloud with GCE Managed Instance Group support (1.1+) required for this module.')

    params = {}
    params['state'] = module.params.get('state')
    params['zone'] = module.params.get('zone')
    params['name'] = module.params.get('name')
    params['size'] = module.params.get('size')
    params['template'] = module.params.get('template')
    params['recreate_instances'] = module.params.get('recreate_instances')
    params['autoscaling'] = module.params.get('autoscaling', None)

    (valid_autoscaling, as_msg) = _validate_autoscaling_params(params)
    if not valid_autoscaling:
        module.fail_json(msg=as_msg, changed=False)

    gce = gce_connect(module)
    changed = False
    json_output = {'state': params['state'], 'zone': params['zone']}
    mig = get_mig(gce, params['name'], params['zone'])

    if not mig:
        if params['state'] == 'absent':
            # Doesn't exist in GCE, and state==absent.
            changed = False
            module.fail_json(
                msg="Cannot delete unknown managed instance group: %s" %
                (params['name']))
        else:
            # Create MIG
            req_create_fields = [
                {'name': 'template', 'required': True, 'type': str},
                {'name': 'size', 'required': True, 'type': int}
            ] # yapf: disable

            (valid_create_fields, valid_create_msg) = _check_params(
                params, req_create_fields)
            if not valid_create_fields:
                module.fail_json(msg=valid_create_msg, changed=False)

            (changed, json_output['created_instances']) = create_mig(gce,
                                                                     params)
            if params['autoscaling'] and params['autoscaling'][
                    'enabled'] is True:
                # Fetch newly-created MIG and create Autoscaler for it.
                mig = get_mig(gce, params['name'], params['zone'])
                if not mig:
                    module.fail_json(
                        msg='Unable to fetch created MIG %s to create \
                        autoscaler in zone: %s' % (
                            params['name'], params['zone']), changed=False)

                if not create_autoscaler(gce, mig, params['autoscaling']):
                    module.fail_json(
                        msg='Unable to fetch MIG %s to create autoscaler \
                        in zone: %s' % (params['name'], params['zone']),
                        changed=False)

                json_output['created_autoscaler'] = True

    elif params['state'] == 'absent':
        # Delete MIG

        # First, check and remove the autoscaler, if present.
        # Note: multiple autoscalers can be associated to a single MIG.  We
        # only handle the one that is named, but we might want to think about this.
        if params['autoscaling']:
            autoscaler = get_autoscaler(gce, params['autoscaling']['name'],
                                        params['zone'])
            if not autoscaler:
                module.fail_json(msg='Unable to fetch autoscaler %s to delete \
                in zone: %s' % (params['autoscaling']['name'], params['zone']),
                                 changed=False)

            changed = delete_autoscaler(autoscaler)
            json_output['deleted_autoscaler'] = changed

        # Now, delete the MIG.
        (changed, json_output['deleted_instances']) = delete_mig(mig)

    else:
        # Update MIG
        # If we're going to update a MIG, we need a size and template values.
        # If not specified, we use the values from the existing MIG.
        if not params['size']:
            params['size'] = mig.size

        if not params['template']:
            params['template'] = mig.template.name

        if params['template'] != mig.template.name:
            # Update Instance Template.
            new_template = gce.ex_get_instancetemplate(params['template'])
            mig.set_instancetemplate(new_template)
            json_output['updated_instancetemplate'] = True
            changed = True
        if params['recreate_instances'] is True:
            # Recreate Instances.
            (changed, json_output['recreated_instances']
             ) = recreate_instances_in_mig(mig)

        if params['size'] != mig.size:
            # Resize MIG.
            keystr = 'created' if params['size'] > mig.size else 'deleted'
            (changed, json_output['resize_%s_instances' %
                                  (keystr)]) = resize_mig(mig, params['size'])

        # Update Autoscaler
        if params['autoscaling']:
            autoscaler = get_autoscaler(gce, params['autoscaling']['name'],
                                        params['zone'])
            if not autoscaler:
                # Try to create autoscaler.
                # Note: this isn't perfect, if the autoscaler name has changed
                # we wouldn't know that here.
                if not create_autoscaler(gce, mig, params['autoscaling']):
                    module.fail_json(
                        msg='Unable to create autoscaler %s for existing MIG %s\
                        in zone: %s' % (params['autoscaling']['name'],
                                        params['name'], params['zone']),
                        changed=False)
                json_output['created_autoscaler'] = True
                changed = True
            else:
                if params['autoscaling']['enabled'] is False:
                    # Delete autoscaler
                    changed = delete_autoscaler(autoscaler)
                    json_output['delete_autoscaler'] = changed
                else:
                    # Update policy, etc.
                    changed = update_autoscaler(gce, autoscaler,
                                                params['autoscaling'])
                    json_output['updated_autoscaler'] = changed

    json_output['changed'] = changed
    json_output.update(params)
    module.exit_json(**json_output)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gce import *
if __name__ == '__main__':
    main()
