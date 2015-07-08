#!/usr/bin/python

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
# Copyright 2015 CenturyLink Cloud
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# CenturyLink Cloud: http://www.CenturyLinkCloud.com
# API Documentation: https://www.centurylinkcloud.com/api-docs/v2/

DOCUMENTATION = '''
module: clc_alert_policy
short_descirption: Create or Delete Alert Policies at CenturyLink Cloud.
description:
  - An Ansible module to Create or Delete Alert Policies at CenturyLink Cloud.
options:
  alias:
    description:
      - The alias of your CLC Account
    required: True
  name:
    description:
      - The name of the alert policy. This is mutually exclusive with id
    default: None
    aliases: []
  id:
    description:
      - The alert policy id. This is mutually exclusive with name
    default: None
    aliases: []
  alert_recipients:
    description:
      - A list of recipient email ids to notify the alert.
    required: True
    aliases: []
  metric:
    description:
      - The metric on which to measure the condition that will trigger the alert.
    required: True
    default: None
    choices: ['cpu','memory','disk']
    aliases: []
  duration:
    description:
      - The length of time in minutes that the condition must exceed the threshold.
    required: True
    default: None
    aliases: []
  threshold:
    description:
      - The threshold that will trigger the alert when the metric equals or exceeds it.
        This number represents a percentage and must be a value between 5.0 - 95.0 that is a multiple of 5.0
    required: True
    default: None
    aliases: []
  state:
    description:
      - Whether to create or delete the policy.
    required: False
    default: present
    choices: ['present','absent']
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

__version__ = '${version}'

import requests

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
    from clc import CLCException
except ImportError:
    clc_found = False
    clc_sdk = None
else:
    clc_found = True


class ClcAlertPolicy():

    clc = clc_sdk
    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.module = module
        self.policy_dict = {}

        if not clc_found:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

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
            alert_recipients=dict(type='list', required=False, default=None),
            metric=dict(required=False, choices=['cpu', 'memory', 'disk'], default=None),
            duration=dict(required=False, type='str', default=None),
            threshold=dict(required=False, type='int', default=None),
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

        if not clc_found:
            self.module.fail_json(
                msg='clc-python-sdk required for this module')

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
                 canged: A flag representing if anything is modified
                 policy: the created/updated alert policy
        """
        changed = False
        p = self.module.params
        policy_name = p.get('name')
        alias = p.get('alias')
        if not policy_name:
            self.module.fail_json(msg='Policy name is a required')
        policy = self._alert_policy_exists(alias, policy_name)
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
                 canged: A flag representing if anything is modified
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
        Ensures the aliert policy is updated if anything is changed in the alert policy configuration
        :param alert_policy: the targetalert policy
        :return: (changed, policy)
                 canged: A flag representing if anything is modified
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
                                        % (alias))

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
        name = p['name']
        arguments = json.dumps(
            {
                'name': name,
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
                '/v2/alertPolicies/%s' %
                (alias),
                arguments)
        except self.clc.APIFailedResponse as e:
            return self.module.fail_json(
                msg='Unable to create alert policy. %s' % str(
                    e.response_text))
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
        name = p['name']
        arguments = json.dumps(
            {
                'name': name,
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
        except self.clc.APIFailedResponse as e:
            return self.module.fail_json(
                msg='Unable to update alert policy. %s' % str(
                    e.response_text))
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
        except self.clc.APIFailedResponse as e:
            return self.module.fail_json(
                msg='Unable to delete alert policy. %s' % str(
                    e.response_text))
        return result

    def _alert_policy_exists(self, alias, policy_name):
        """
        Check to see if an alert policy exists
        :param policy_name: name of the alert policy
        :return: boolean of if the policy exists
        """
        result = False
        for id in self.policy_dict:
            if self.policy_dict.get(id).get('name') == policy_name:
                result = self.policy_dict.get(id)
        return result

    def _get_alert_policy_id(self, module, alert_policy_name):
        """
        retrieves the alert policy id of the account based on the name of the policy
        :param module: the AnsibleModule object
        :param alert_policy_name: the alert policy name
        :return: alert_policy_id: The alert policy id
        """
        alert_policy_id = None
        for id in self.policy_dict:
            if self.policy_dict.get(id).get('name') == alert_policy_name:
                if not alert_policy_id:
                    alert_policy_id = id
                else:
                    return module.fail_json(
                        msg='mutiple alert policies were found with policy name : %s' %
                        (alert_policy_name))
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

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
