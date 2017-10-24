#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: manageiq_alert_policies

short_description: Configuration of alert policies for ManageIQ
extends_documentation_fragment: manageiq
version_added: '2.5'
author: Elad Alfassa (ealfassa@redhat.com)
description:
  - The manageiq_alert_policies module supports listing, adding, updating and deleting alert policies in ManageIQ.

options:
  state:
    description:
      - absent - alert policy should not exist,
      - present - alert policy should exist,
      - list - return a list of alert policies.
    required: False
    choices: ['absent', 'present', 'list']
    default: 'present'
  description:
    description:
      - The unique alert policy description in ManageIQ.
      - Required when state is "absent" or "present".
  resource_type:
    description:
      - The entity type for the alert policy in ManageIQ. Required when state is "present".
    choices: ['Vm', 'ContainerNode', 'MiqServer', 'Host', 'Storage', 'EmsCluster',
              'ExtManagementSystem', 'MiddlewareServer']
  expression_type:
    description:
      - Expression type.
    default: hash
    choices: ["hash", "miq"]
  expression:
    description:
      - The alert policy expression for ManageIQ.
      - Can either be in the "Miq Expression" format or the "Hash Expression format".
      - Required if state is "present".
  enabled:
    description:
      - Enable or disable the alert policy. Required if state is "present".
    type: bool
  options:
    description:
      - Additional alert options, such as notification type and frequency


'''

EXAMPLES = '''
- name: List alert policies in ManageIQ
  manageiq_alert_policies:
    state: list
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Add alert policy with a "hash expression" to ManageIQ
  manageiq_alert_policies:
    state: present
    description: Test Alert 01
    options:
      notifications:
        email:
          to: ["example@example.com"]
          from: "example@example.com"
    resource_type: ContainerNode
    expression:
        eval_method: hostd_log_threshold
        mode: internal
        options: {}
    enabled: true
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Add alert policy with a "miq expression" to ManageIQ
  manageiq_alert_policies:
    state: present
    description: Test Alert 02
    options:
      notifications:
        email:
          to: ["example@example.com"]
          from: "example@example.com"
    resource_type: Vm
    expression_type: miq
    expression:
        and:
          - CONTAINS:
              tag: Vm.managed-environment
              value: prod
          - not:
            CONTAINS:
              tag: Vm.host.managed-environment
              value: prod
    enabled: true
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Delete an alert policy from ManageIQ
  manageiq_alert_policies:
    state: absent
    description: Test Alert 01
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec


# TODO: I copied this from yaacov's ansible/ansible PR 31233. It should be removed
# from here once that PR is merged.
def find_collection_resource_or_fail(module, manageiq, collection_name, **params):
    """ Searches the collection resource by the collection name and the param passed.

    Returns:
        the resource as an object if it exists in manageiq, Fail otherwise.
    """
    resource = manageiq.find_collection_resource_by(collection_name, **params)
    if resource:
        return resource
    else:
        msg = "{collection_name} where {params} does not exist in manageiq".format(
            collection_name=collection_name, params=str(params))
    module.fail_json(msg=msg)


class ManageIQAlertPolicy(object):
    """ Represent a ManageIQ alert policy
    """
    def __init__(self, policy):
        self.description = policy['description']
        self.db = policy['db']
        self.enabled = policy['enabled']
        self.options = policy['options']
        self.hash_expression = None
        self.miq_expressipn = None

        if 'hash_expression' in policy:
            self.hash_expression = policy['hash_expression']
        if 'miq_expression' in policy:
            self.miq_expression = policy['miq_expression']
            if 'exp' in self.miq_expression:
                # miq_expression is a field that needs a special case, because
                # it's returned surrounded by a dict named exp even though we don't
                # send it with that dict.
                self.miq_expression = self.miq_expression['exp']

    def __eq__(self, other):
        """ Compare two ManageIQAlertPolicy objects
        """
        return self.__dict__ == other.__dict__


class ManageIQAlerts(object):
    """ Object to execute alert management operations in manageiq.
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq

        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client
        self.url = '{api_url}/alert_definitions'.format(api_url=self.api_url)

    def get_alerts(self):
        """ Get all alerts from ManageIQ
        """
        try:
            response = self.client.get(self.url + '?expand=resources')
        except Exception as e:
            self.module.fail_json(msg="Failed to query alerts: {error}".format(error=e))
        return response.get('resources', [])

    def validate_hash_expression(self, expression):
        """ Validate a 'hash expression' alert definition
        """
        # hash expressions must have the following fields
        for key in ['options', 'eval_method', 'mode']:
            if key not in expression:
                msg = "Hash expression is missing required field {key}".format(key=key)
                self.module.fail_json(msg)

    def create_policy_dict(self, params):
        """ Create a dict representing a policy
        """
        if params['expression_type'] == 'hash':
            # hash expression supports depends on https://github.com/ManageIQ/manageiq-api/pull/76
            self.validate_hash_expression(params['expression'])
            expression_type = 'hash_expression'
        else:
            expression_type = 'miq_expression'

        # build the policy
        policy = dict(description=params['description'],
                      db=params['resource_type'],
                      options=params['options'],
                      enabled=params['enabled'])

        # add the actual expression.
        policy.update({expression_type: params['expression']})

        return policy

    def add_alert_policy(self, policy):
        """ Add a new alert policy to ManageIQ
        """
        try:
            result = self.client.post(self.url, action='create', resource=policy)

            msg = "Alert policy {description} created successfully: {details}"
            msg = msg.format(description=policy['description'], details=result)
            return dict(changed=True, msg=msg)
        except Exception as e:
            msg = "Creating alert policy {description} failed: {error}"
            msg = msg.format(description=policy['description'], error=e)
            self.module.fail_json(msg=msg)

    def delete_alert_policy(self, alert_policy):
        """ Delete an alert policy
        """
        try:
            result = self.client.post('{url}/{id}'.format(url=self.url,
                                                          id=alert_policy['id']),
                                      action="delete")
            msg = "Alert policy {description} deleted: {details}"
            msg = msg.format(description=alert_policy['description'], details=result)
            return dict(changed=True, msg=msg)
        except Exception as e:
            msg = "Deleting alert policy {description} failed: {error}"
            msg = msg.format(description=alert_policy['description'], error=e)
            self.module.fail_json(msg=msg)

    def update_alert_policy(self, existing_policy, new_policy):
        """ Update an existing alert policy with the values from `new_policy`
        """
        new_policy_obj = ManageIQAlertPolicy(new_policy)
        if new_policy_obj == ManageIQAlertPolicy(existing_policy):
            # no change needed - alert policies are identical
            return dict(changed=False, msg="No update needed")
        else:
            try:
                url = '{url}/{id}'.format(url=self.url, id=existing_policy['id'])
                result = self.client.post(url, action="edit", resource=new_policy)

                # make sure that the update was indeed successful by comparing
                # the result to the expected result.
                if new_policy_obj == ManageIQAlertPolicy(result):
                    # success!
                    msg = "Alert policy {description} upated successfully: {details}"
                    msg = msg.format(description=existing_policy['description'], details=result)

                    return dict(changed=True, msg=msg)
                else:
                    # unexpected result
                    msg = "Updating alert policy {description} failed, unexpected result {details}"
                    msg = msg.format(description=existing_policy['description'], details=result)

                    self.module.fail_json(msg=msg)

            except Exception as e:
                msg = "Updating alert policy {description} failed: {error}"
                msg = msg.format(description=existing_policy['description'], error=e)
                self.module.fail_json(msg=msg)


def main():
    argument_spec = dict(
        description=dict(type='str'),
        resource_type=dict(type='str', choices=['Vm',
                                                'ContainerNode',
                                                'MiqServer',
                                                'Host',
                                                'Storage',
                                                'EmsCluster',
                                                'ExtManagementSystem',
                                                'MiddlewareServer']),
        expression_type=dict(type='str', default='hash', choices=['miq', 'hash']),
        expression=dict(type='dict'),
        options=dict(type='dict'),
        enabled=dict(type='bool'),
        state=dict(require=False, default='present',
                   choices=['present', 'absent', 'list']),
    )
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=[('state', 'present', ['description',
                                                              'resource_type',
                                                              'expression',
                                                              'enabled',
                                                              'options']),
                                        ('state', 'absent', ['description'])])

    state = module.params['state']
    description = module.params['description']

    manageiq = ManageIQ(module)
    manageiq_alerts = ManageIQAlerts(manageiq)

    if state == "list":
        res_args = dict(changed=False, alerts=manageiq_alerts.get_alerts())
    else:
        existing_policy = manageiq.find_collection_resource_by("alert_definitions",
                                                               description=description)

        # we need to add or update the alert policy
        if state == "present":
            policy = manageiq_alerts.create_policy_dict(module.params)

            if not existing_policy:
                # a policy with this description doesn't exist yet, let's create it
                res_args = manageiq_alerts.add_alert_policy(policy)
            else:
                # a policy with this description exists, we might need to update it
                res_args = manageiq_alerts.update_alert_policy(existing_policy, policy)

        # this alert policy should not exist
        if state == "absent":
            # if we have an alert policy with this description, delete it
            if existing_policy:
                res_args = manageiq_alerts.delete_alert_policy(existing_policy)
            else:
                # we don't have this alert policy - that's an error.
                msg = "Alert policy '{description}' does not exist in ManageIQ"
                msg = msg.format(description=description)
                module.fail_json(msg=msg)

    module.exit_json(**res_args)

if __name__ == "__main__":
    main()
