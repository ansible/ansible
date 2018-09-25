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

module: manageiq_alerts

short_description: Configuration of alerts in ManageIQ
extends_documentation_fragment: manageiq
version_added: '2.5'
author: Elad Alfassa (ealfassa@redhat.com)
description:
  - The manageiq_alerts module supports adding, updating and deleting alerts in ManageIQ.

options:
  state:
    description:
      - absent - alert should not exist,
      - present - alert should exist,
    required: False
    choices: ['absent', 'present']
    default: 'present'
  description:
    description:
      - The unique alert description in ManageIQ.
      - Required when state is "absent" or "present".
  resource_type:
    description:
      - The entity type for the alert in ManageIQ. Required when state is "present".
    choices: ['Vm', 'ContainerNode', 'MiqServer', 'Host', 'Storage', 'EmsCluster',
              'ExtManagementSystem', 'MiddlewareServer']
  expression_type:
    description:
      - Expression type.
    default: hash
    choices: ["hash", "miq"]
  expression:
    description:
      - The alert expression for ManageIQ.
      - Can either be in the "Miq Expression" format or the "Hash Expression format".
      - Required if state is "present".
  enabled:
    description:
      - Enable or disable the alert. Required if state is "present".
    type: bool
  options:
    description:
      - Additional alert options, such as notification type and frequency


'''

EXAMPLES = '''
- name: Add an alert with a "hash expression" to ManageIQ
  manageiq_alerts:
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

- name: Add an alert with a "miq expression" to ManageIQ
  manageiq_alerts:
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

- name: Delete an alert from ManageIQ
  manageiq_alerts:
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


class ManageIQAlert(object):
    """ Represent a ManageIQ alert. Can be initialized with both the format
    we recieve from the server and the format we get from the user.
    """
    def __init__(self, alert):
        self.description = alert['description']
        self.db = alert['db']
        self.enabled = alert['enabled']
        self.options = alert['options']
        self.hash_expression = None
        self.miq_expressipn = None

        if 'hash_expression' in alert:
            self.hash_expression = alert['hash_expression']
        if 'miq_expression' in alert:
            self.miq_expression = alert['miq_expression']
            if 'exp' in self.miq_expression:
                # miq_expression is a field that needs a special case, because
                # it's returned surrounded by a dict named exp even though we don't
                # send it with that dict.
                self.miq_expression = self.miq_expression['exp']

    def __eq__(self, other):
        """ Compare two ManageIQAlert objects
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
        self.alerts_url = '{api_url}/alert_definitions'.format(api_url=self.api_url)

    def get_alerts(self):
        """ Get all alerts from ManageIQ
        """
        try:
            response = self.client.get(self.alerts_url + '?expand=resources')
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

    def create_alert_dict(self, params):
        """ Create a dict representing an alert
        """
        if params['expression_type'] == 'hash':
            # hash expression supports depends on https://github.com/ManageIQ/manageiq-api/pull/76
            self.validate_hash_expression(params['expression'])
            expression_type = 'hash_expression'
        else:
            # actually miq_expression, but we call it "expression" for backwards-compatibility
            expression_type = 'expression'

        # build the alret
        alert = dict(description=params['description'],
                     db=params['resource_type'],
                     options=params['options'],
                     enabled=params['enabled'])

        # add the actual expression.
        alert.update({expression_type: params['expression']})

        return alert

    def add_alert(self, alert):
        """ Add a new alert to ManageIQ
        """
        try:
            result = self.client.post(self.alerts_url, action='create', resource=alert)

            msg = "Alert {description} created successfully: {details}"
            msg = msg.format(description=alert['description'], details=result)
            return dict(changed=True, msg=msg)
        except Exception as e:
            msg = "Creating alert {description} failed: {error}"
            if "Resource expression needs be specified" in str(e):
                # Running on an older version of ManageIQ and trying to create a hash expression
                msg = msg.format(description=alert['description'],
                                 error="Your version of ManageIQ does not support hash_expression")
            else:
                msg = msg.format(description=alert['description'], error=e)
            self.module.fail_json(msg=msg)

    def delete_alert(self, alert):
        """ Delete an alert
        """
        try:
            result = self.client.post('{url}/{id}'.format(url=self.alerts_url,
                                                          id=alert['id']),
                                      action="delete")
            msg = "Alert {description} deleted: {details}"
            msg = msg.format(description=alert['description'], details=result)
            return dict(changed=True, msg=msg)
        except Exception as e:
            msg = "Deleting alert {description} failed: {error}"
            msg = msg.format(description=alert['description'], error=e)
            self.module.fail_json(msg=msg)

    def update_alert(self, existing_alert, new_alert):
        """ Update an existing alert with the values from `new_alert`
        """
        new_alert_obj = ManageIQAlert(new_alert)
        if new_alert_obj == ManageIQAlert(existing_alert):
            # no change needed - alerts are identical
            return dict(changed=False, msg="No update needed")
        else:
            try:
                url = '{url}/{id}'.format(url=self.alerts_url, id=existing_alert['id'])
                result = self.client.post(url, action="edit", resource=new_alert)

                # make sure that the update was indeed successful by comparing
                # the result to the expected result.
                if new_alert_obj == ManageIQAlert(result):
                    # success!
                    msg = "Alert {description} upated successfully: {details}"
                    msg = msg.format(description=existing_alert['description'], details=result)

                    return dict(changed=True, msg=msg)
                else:
                    # unexpected result
                    msg = "Updating alert {description} failed, unexpected result {details}"
                    msg = msg.format(description=existing_alert['description'], details=result)

                    self.module.fail_json(msg=msg)

            except Exception as e:
                msg = "Updating alert {description} failed: {error}"
                if "Resource expression needs be specified" in str(e):
                    # Running on an older version of ManageIQ and trying to update a hash expression
                    msg = msg.format(description=existing_alert['description'],
                                     error="Your version of ManageIQ does not support hash_expression")
                else:
                    msg = msg.format(description=existing_alert['description'], error=e)
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
                   choices=['present', 'absent']),
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

    existing_alert = manageiq.find_collection_resource_by("alert_definitions",
                                                          description=description)

    # we need to add or update the alert
    if state == "present":
        alert = manageiq_alerts.create_alert_dict(module.params)

        if not existing_alert:
            # an alert with this description doesn't exist yet, let's create it
            res_args = manageiq_alerts.add_alert(alert)
        else:
            # an alert with this description exists, we might need to update it
            res_args = manageiq_alerts.update_alert(existing_alert, alert)

    # this alert should not exist
    elif state == "absent":
        # if we have an alert with this description, delete it
        if existing_alert:
            res_args = manageiq_alerts.delete_alert(existing_alert)
        else:
            # it doesn't exist, and that's okay
            msg = "Alert '{description}' does not exist in ManageIQ"
            msg = msg.format(description=description)
            res_args = dict(changed=False, msg=msg)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
