#!/usr/bin/python

#
# Copyright (c) 2015 CenturyLink
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: clc_alert_policy
short_description: Create or Delete Alert Policies at CenturyLink Cloud.
description:
  - An Ansible module to Create or Delete Alert Policies at CenturyLink Cloud.
version_added: "2.0"
options:
  alias:
    description:
      - The alias of your CLC Account
    required: True
  name:
    description:
      - The name of the alert policy. This is mutually exclusive with id
  id:
    description:
      - The alert policy id. This is mutually exclusive with name
  alert_recipients:
    description:
      - A list of recipient email ids to notify the alert.
        This is required for state 'present'
  metric:
    description:
      - The metric on which to measure the condition that will trigger the alert.
        This is required for state 'present'
    choices: ['cpu','memory','disk']
  duration:
    description:
      - The length of time in minutes that the condition must exceed the threshold.
        This is required for state 'present'
  threshold:
    description:
      - The threshold that will trigger the alert when the metric equals or exceeds it.
        This is required for state 'present'
        This number represents a percentage and must be a value between 5.0 - 95.0 that is a multiple of 5.0
  state:
    description:
      - Whether to create or delete the policy.
    default: present
    choices: ['present','absent']
requirements:
    - python = 2.7
    - requests >= 2.5.0
    - clc-sdk
author: "CLC Runner (@clc-runner)"
notes:
    - To use this module, it is required to set the below environment variables which enables access to the
      Centurylink Cloud
          - CLC_V2_API_USERNAME, the account login id for the centurylink cloud
          - CLC_V2_API_PASSWORD, the account password for the centurylink cloud
    - Alternatively, the module accepts the API token and account alias. The API token can be generated using the
      CLC account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
          - CLC_V2_API_TOKEN, the API token generated from https://api.ctl.io/v2/authentication/login
          - CLC_ACCT_ALIAS, the account alias associated with the centurylink cloud
    - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment.
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

---
- name: Create Alert Policy Example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create an Alert Policy for disk above 80% for 5 minutes
      clc_alert_policy:
        alias: wfad
        name: 'alert for disk > 80%'
        alert_recipients:
            - test1@centurylink.com
            - test2@centurylink.com
        metric: 'disk'
        duration: '00:05:00'
        threshold: 80
        state: present
      register: policy

    - name: debug
      debug: var=policy

---
- name: Delete Alert Policy Example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an Alert Policy
      clc_alert_policy:
        alias: wfad
        name: 'alert for disk > 80%'
        state: absent
      register: policy

    - name: debug
      debug: var=policy
'''

RETURN = '''
policy:
    description: The alert policy information
    returned: success
    type: dict
    sample:
        {
            "actions": [
                {
                "action": "email",
                "settings": {
                    "recipients": [
                        "user1@domain.com",
                        "user1@domain.com"
                    ]
                }
                }
            ],
            "id": "ba54ac54a60d4a4f1ed6d48c1ce240a7",
            "links": [
                {
                "href": "/v2/alertPolicies/alias/ba54ac54a60d4a4fb1d6d48c1ce240a7",
                "rel": "self",
                "verbs": [
                    "GET",
                    "DELETE",
                    "PUT"
                ]
                }
            ],
            "name": "test_alert",
            "triggers": [
                {
                "duration": "00:05:00",
                "metric": "disk",
                "threshold": 80.0
                }
            ]
        }
'''

__version__ = '${version}'

import json
import os
import traceback
from distutils.version import LooseVersion

REQUESTS_IMP_ERR = None
try:
    import requests
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
CLC_IMP_ERR = None
try:
    import clc as clc_sdk
    from clc import APIFailedResponse
except ImportError:
    CLC_IMP_ERR = traceback.format_exc()
    CLC_FOUND = False
    clc_sdk = None
else:
    CLC_FOUND = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class ClcAlertPolicy:

    clc = clc_sdk
    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        self.policy_dict = {}

        if not CLC_FOUND:
            self.module.fail_json(msg=missing_required_lib('clc-sdk'), exception=CLC_IMP_ERR)
        if not REQUESTS_FOUND:
            self.module.fail_json(msg=missing_required_lib('requests'), exception=REQUESTS_IMP_ERR)
        if requests.__version__ and LooseVersion(requests.__version__) < LooseVersion('2.5.0'):
            self.module.fail_json(
                msg='requests library  version should be >= 2.5.0')

        self._set_user_agent(self.clc)

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(default=None),
            id=dict(default=None),
            alias=dict(required=True, default=None),
            alert_recipients=dict(type='list', default=None),
            metric=dict(
                choices=[
                    'cpu',
                    'memory',
                    'disk'],
                default=None),
            duration=dict(type='str', default=None),
            threshold=dict(type='int', default=None),
            state=dict(default='present', choices=['present', 'absent'])
        )
        mutually_exclusive = [
            ['name', 'id']
        ]
        return {'argument_spec': argument_spec,
                'mutually_exclusive': mutually_exclusive}

    # Module Behavior Goodness
    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        p = self.module.params

        self._set_clc_credentials_from_env()
        self.policy_dict = self._get_alert_policies(p['alias'])

        if p['state'] == 'present':
            changed, policy = self._ensure_alert_policy_is_present()
        else:
            changed, policy = self._ensure_alert_policy_is_absent()

        self.module.exit_json(changed=changed, policy=policy)

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        api_url = env.get('CLC_V2_API_URL', False)

        if api_url:
            self.clc.defaults.ENDPOINT_URL_V2 = api_url

        if v2_api_token and clc_alias:
            self.clc._LOGIN_TOKEN_V2 = v2_api_token
            self.clc._V2_ENABLED = True
            self.clc.ALIAS = clc_alias
        elif v2_api_username and v2_api_passwd:
            self.clc.v2.SetCredentials(
                api_username=v2_api_username,
                api_passwd=v2_api_passwd)
        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")

    def _ensure_alert_policy_is_present(self):
        """
        Ensures that the alert policy is present
        :return: (changed, policy)
                 changed: A flag representing if anything is modified
                 policy: the created/updated alert policy
        """
        changed = False
        p = self.module.params
        policy_name = p.get('name')

        if not policy_name:
            self.module.fail_json(msg='Policy name is a required')
        policy = self._alert_policy_exists(policy_name)
        if not policy:
            changed = True
            policy = None
            if not self.module.check_mode:
                policy = self._create_alert_policy()
        else:
            changed_u, policy = self._ensure_alert_policy_is_updated(policy)
            if changed_u:
                changed = True
        return changed, policy

    def _ensure_alert_policy_is_absent(self):
        """
        Ensures that the alert policy is absent
        :return: (changed, None)
                 changed: A flag representing if anything is modified
        """
        changed = False
        p = self.module.params
        alert_policy_id = p.get('id')
        alert_policy_name = p.get('name')
        alias = p.get('alias')
        if not alert_policy_id and not alert_policy_name:
            self.module.fail_json(
                msg='Either alert policy id or policy name is required')
        if not alert_policy_id and alert_policy_name:
            alert_policy_id = self._get_alert_policy_id(
                self.module,
                alert_policy_name)
        if alert_policy_id and alert_policy_id in self.policy_dict:
            changed = True
            if not self.module.check_mode:
                self._delete_alert_policy(alias, alert_policy_id)
        return changed, None

    def _ensure_alert_policy_is_updated(self, alert_policy):
        """
        Ensures the alert policy is updated if anything is changed in the alert policy configuration
        :param alert_policy: the target alert policy
        :return: (changed, policy)
                 changed: A flag representing if anything is modified
                 policy: the updated the alert policy
        """
        changed = False
        p = self.module.params
        alert_policy_id = alert_policy.get('id')
        email_list = p.get('alert_recipients')
        metric = p.get('metric')
        duration = p.get('duration')
        threshold = p.get('threshold')
        policy = alert_policy
        if (metric and metric != str(alert_policy.get('triggers')[0].get('metric'))) or \
                (duration and duration != str(alert_policy.get('triggers')[0].get('duration'))) or \
                (threshold and float(threshold) != float(alert_policy.get('triggers')[0].get('threshold'))):
            changed = True
        elif email_list:
            t_email_list = list(
                alert_policy.get('actions')[0].get('settings').get('recipients'))
            if set(email_list) != set(t_email_list):
                changed = True
        if changed and not self.module.check_mode:
            policy = self._update_alert_policy(alert_policy_id)
        return changed, policy

    def _get_alert_policies(self, alias):
        """
        Get the alert policies for account alias by calling the CLC API.
        :param alias: the account alias
        :return: the alert policies for the account alias
        """
        response = {}

        policies = self.clc.v2.API.Call('GET',
                                        '/v2/alertPolicies/%s'
                                        % alias)

        for policy in policies.get('items'):
            response[policy.get('id')] = policy
        return response

    def _create_alert_policy(self):
        """
        Create an alert Policy using the CLC API.
        :return: response dictionary from the CLC API.
        """
        p = self.module.params
        alias = p['alias']
        email_list = p['alert_recipients']
        metric = p['metric']
        duration = p['duration']
        threshold = p['threshold']
        policy_name = p['name']
        arguments = json.dumps(
            {
                'name': policy_name,
                'actions': [{
                    'action': 'email',
                    'settings': {
                        'recipients': email_list
                    }
                }],
                'triggers': [{
                    'metric': metric,
                    'duration': duration,
                    'threshold': threshold
                }]
            }
        )
        try:
            result = self.clc.v2.API.Call(
                'POST',
                '/v2/alertPolicies/%s' % alias,
                arguments)
        except APIFailedResponse as e:
            return self.module.fail_json(
                msg='Unable to create alert policy "{0}". {1}'.format(
                    policy_name, str(e.response_text)))
        return result

    def _update_alert_policy(self, alert_policy_id):
        """
        Update alert policy using the CLC API.
        :param alert_policy_id: The clc alert policy id
        :return: response dictionary from the CLC API.
        """
        p = self.module.params
        alias = p['alias']
        email_list = p['alert_recipients']
        metric = p['metric']
        duration = p['duration']
        threshold = p['threshold']
        policy_name = p['name']
        arguments = json.dumps(
            {
                'name': policy_name,
                'actions': [{
                    'action': 'email',
                    'settings': {
                        'recipients': email_list
                    }
                }],
                'triggers': [{
                    'metric': metric,
                    'duration': duration,
                    'threshold': threshold
                }]
            }
        )
        try:
            result = self.clc.v2.API.Call(
                'PUT', '/v2/alertPolicies/%s/%s' %
                (alias, alert_policy_id), arguments)
        except APIFailedResponse as e:
            return self.module.fail_json(
                msg='Unable to update alert policy "{0}". {1}'.format(
                    policy_name, str(e.response_text)))
        return result

    def _delete_alert_policy(self, alias, policy_id):
        """
        Delete an alert policy using the CLC API.
        :param alias : the account alias
        :param policy_id: the alert policy id
        :return: response dictionary from the CLC API.
        """
        try:
            result = self.clc.v2.API.Call(
                'DELETE', '/v2/alertPolicies/%s/%s' %
                (alias, policy_id), None)
        except APIFailedResponse as e:
            return self.module.fail_json(
                msg='Unable to delete alert policy id "{0}". {1}'.format(
                    policy_id, str(e.response_text)))
        return result

    def _alert_policy_exists(self, policy_name):
        """
        Check to see if an alert policy exists
        :param policy_name: name of the alert policy
        :return: boolean of if the policy exists
        """
        result = False
        for policy_id in self.policy_dict:
            if self.policy_dict.get(policy_id).get('name') == policy_name:
                result = self.policy_dict.get(policy_id)
        return result

    def _get_alert_policy_id(self, module, alert_policy_name):
        """
        retrieves the alert policy id of the account based on the name of the policy
        :param module: the AnsibleModule object
        :param alert_policy_name: the alert policy name
        :return: alert_policy_id: The alert policy id
        """
        alert_policy_id = None
        for policy_id in self.policy_dict:
            if self.policy_dict.get(policy_id).get('name') == alert_policy_name:
                if not alert_policy_id:
                    alert_policy_id = policy_id
                else:
                    return module.fail_json(
                        msg='multiple alert policies were found with policy name : %s' % alert_policy_name)
        return alert_policy_id

    @staticmethod
    def _set_user_agent(clc):
        if hasattr(clc, 'SetRequestsSession'):
            agent_string = "ClcAnsibleModule/" + __version__
            ses = requests.Session()
            ses.headers.update({"Api-Client": agent_string})
            ses.headers['User-Agent'] += " " + agent_string
            clc.SetRequestsSession(ses)


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcAlertPolicy._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_alert_policy = ClcAlertPolicy(module)
    clc_alert_policy.process_request()


if __name__ == '__main__':
    main()
