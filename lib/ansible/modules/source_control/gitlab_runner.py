#!/usr/bin/python

# Copyright: (c) 2018, Samy Coenen <samy.coenen@nubera.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: gitlab_runner
short_description: Create, modify and delete GitLab Runners.
description:
  - Register, update and delete runners with the GitLab API.
  - All operations are performed using the GitLab API v4.
  - For details, consult the full API documentation at U(https://docs.gitlab.com/ee/api/runners.html).
  - A valid private API token is required for all operations. You can create as many tokens as you like using the GitLab web interface at
    U(https://$GITLAB_URL/profile/personal_access_tokens).
  - A valid registration token is required for registering a new runner.
    To create shared runners, you need to ask your administrator to give you this token.
    It can be found at U(https://$GITLAB_URL/admin/runners/).
notes:
  - Instead of the private_token parameter, the GITLAB_PRIVATE_TOKEN environment variable can be used.
  - To create a new runner at least the C(private_token), C(registration_token), C(name) and C(url) options are required.
  - Runners need to have unique names.
version_added: 2.8
author: "Samy Coenen (@SamyCoenen)"
options:
    private_token:
        description:
            - Your private token to interact with the GitLab API.
        required: True
        type: str
    name:
        description:
            - The unique name of the runner.
        required: True
        type: str
    api_timeout:
        description:
            - The maximum time that a request will be attempted to the GitLab API.
        required: False
        default: 30
        type: int
    state:
        description:
            - Make sure that the runner with the same name exists with the same configuration or delete the runner with the same name.
        required: False
        default: "present"
        choices: ["present", "absent"]
        type: str
    registration_token:
        description:
            - The registration token is used to register new runners.
        required: True
        type: str
    url:
        description:
            - The GitLab URL including the API v4 path and http or https.
        required: False
        default: "https://gitlab.com/api/v4/"
        type: str
    active:
        description:
            - Define if the runners is immediately active after creation.
        required: False
        default: True
        choices: [True, False]
        type: bool
    locked:
        description:
            - Determines if the runner is locked or not.
        required: False
        default: False
        choices: [true, false]
        type: bool
    access_level:
        description:
            - Determines if a runner can pick up jobs from protected branches.
        required: False
        default: "ref_protected"
        choices: ["ref_protected", "not_protected"]
        type: str
    maximum_timeout:
        description:
            - The maximum timeout that a runner has to pick up a specific job.
        required: False
        default: 3600
        type: int
    run_untagged:
        description:
            - Run untagged jobs or not.
        required: False
        default: True
        type: bool
    tag_list:
        description: The tags that apply to the runner.
        required: False
        default: ["docker"]
        type: list
'''

EXAMPLES = '''
# Register a new runner (if it does not exist)

- name: Register runner
  gitlab_runner:
    url: https://gitlab.com/api/v4/
    private_token: ...5432632464326432632463246...
    registration_token: ...4gfdsg345...
    name: Docker Machine t1
    state: present
    active: True
    tag_list: ['docker']
    run_untagged: False
    locked: False
    access_level: ref_protected
  register: api

# Delete a runner
- name: Delete runner
  gitlab_runner:
    url: https://gitlab.com/api/v4/
    private_token: ...5432632464326432632463246...
    registration_token: ...4gfdsg345...
    name: Docker Machine t1
    state: absent
  register: api
'''

RETURN = '''
changed:
    description: Values changed on the API
    returned: changed
    type: bool
    sample: false
msg:
    description: Information returned from the API when updating a runner, a create only returns the id and token.
    returned: always
    type: dict
    sample: {
      "id": 31,
      "description": "Docker Machine t2",
      "active": true,
      "is_shared": true,
      "name": null,
      "online": null,
      "status": "not_connected",
      "tag_list": [
          "docker"
      ],
      "run_untagged": true,
      "locked": false,
      "maximum_timeout": null,
      "access_level": "ref_protected",
      "version": null,
      "revision": null,
      "platform":null,
      "architecture": null,
      "contacted_at": null,
      "token": "ba4be.....e6a3b8",
      "projects": [],
      "groups": []
    }
token:
    description: Runner token of affected runner
    returned: when registered or updated runner
    type: str
    sample: ["2a5aeecc61dc98c4d780b14b330e3282"]
'''

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import json


class AnsibleGitlabAPI(AnsibleModule):
    def __init__(self, module, url, private_token):
        self._module = module
        self._auth_header = {'PRIVATE-TOKEN': private_token}
        self.url = url
        self.timeout = module.params['api_timeout']

    def check_response(self, info, response, api_call):
        """
        Checks response code.
        Returns: response in JSON.
        """
        if info['status'] in (200, 201):
            return json.loads(response.read())
        elif info['status'] == 204:
            return json.loads('{"msg":"Request completed"}')
        elif info['status'] in (403, 404):
            return None
        else:
            self._module.fail_json(msg='Failure while calling the GitLab API for '
                                       '"%s".' % api_call, fetch_url_info=info)

    def _get(self, api_call):
        resp, info = fetch_url(self._module, self.url + api_call,
                               headers=self._auth_header,
                               timeout=self.timeout)
        return self.check_response(info, resp, api_call)

    def _post(self, api_call, data=None):
        """
        Sends POST request.
        Returns: response.
        """
        headers = self._auth_header.copy()
        if data is not None:
            data = self._module.jsonify(data)
            headers['Content-type'] = 'application/json'

        resp, info = fetch_url(self._module,
                               self.url + api_call,
                               headers=headers,
                               method='POST',
                               data=data,
                               timeout=self.timeout)
        return self.check_response(info, resp, api_call)

    def _put(self, api_call, data=None):
        """
        Sends PUT request.
        Returns: response.
        """
        headers = self._auth_header.copy()
        if data is not None:
            data = self._module.jsonify(data)
            headers['Content-type'] = 'application/json'

        resp, info = fetch_url(self._module,
                               self.url + api_call,
                               headers=headers,
                               method='PUT',
                               data=data,
                               timeout=self.timeout)
        return self.check_response(info, resp, api_call)

    def _delete(self, api_call):
        """
        Sends DELETE request.
        Returns: response.
        """
        resp, info = fetch_url(self._module,
                               self.url + api_call,
                               headers=self._auth_header,
                               method='DELETE',
                               timeout=self.timeout)
        return self.check_response(info, resp, api_call)

    def get_runner_id(self, description):
        """
        Gets the ID for a given description.
        Returns: ID as int.
        """
        r = self._get('runners/all')
        if r is None:
            return None
        for runner in r:
            if runner['description'] == description:
                return runner.get('id')
        return None

    def delete_runner(self, id):
        """
        Sends DELETE request for runner with the same ID.
        Returns: response.
        """
        return self._delete('runners/' + str(id))

    def update_runner(self, id, runner):
        """
        Sends UPDATE request for runner to change all the fields.
        Returns: response.
        """
        form_data = runner.get_dict()
        return self._put('runners/' + str(id), form_data)

    def register_runner(self, runner, registration_token):
        """
        Sends POST request to register runner.
        Returns: response.
        """
        form_data = runner.get_dict()
        form_data["token"] = registration_token
        return self._post('runners/', form_data)

    def get_runner_list_short(self):
        """
        Sends GET request to get a global list of all runners.
        Returns: JSON list.
        """
        return self._get('runners/all')

    def get_runner_list(self, ids, primary_key):
        """
        Sends GET requests to get details of all runners.
        Returns: JSON list.
        """
        d = {}
        for i in ids:
            runner_details = self.get_runner_details(i)
            d[runner_details.get(primary_key)] = runner_details
        return d

    def get_runner_details(self, id):
        """
        Sends GET request to get the details of a specific runner .
        Returns: JSON list.
        """
        return self._get('runners/' + str(id))


class Runner():
    def __init__(self, id, description, active, tag_list, run_untagged, locked, access_level, maximum_timeout):
        self.id = id
        self.description = description
        self.active = active
        self.tag_list = tag_list
        self.run_untagged = run_untagged
        self.locked = locked
        self.access_level = access_level
        self.maximum_timeout = maximum_timeout

    def __eq__(self, other):
        """
        Compare every field and its value with the fields and values of another instance of this class.
        Returns: boolean.
        """
        return self.__dict__ == other.__dict__

    def get_dict(self):
        """
        Returns every field and its value of this class.
        Returns: dict.
        """
        return self.__dict__


def get_gitlab_argument_spec():
    """
    Returns argument spec with all optional or required Ansible arguments.
    Returns: dict.
    """
    return dict(
        private_token=dict(
            fallback=(env_fallback, ['GITLAB_PRIVATE_TOKEN']),
            no_log=True,
            required=True),
        name=dict(required=True, type='str'),
        active=dict(required=False, type='bool', default=True, choices=[True, False]),
        tag_list=dict(required=False, type='list',
                      default=["docker"]),
        run_untagged=dict(
            required=False, type='bool', default=True),
        locked=dict(required=False, type='bool', default=False, choices=[True, False]),
        access_level=dict(required=False, type='str',
                          default='ref_protected', choices=["ref_protected", "not_protected"]),
        maximum_timeout=dict(
            required=False, type='int', default=3600),
        api_timeout=dict(default=30, type='int'),
        url=dict(required=False, type='str',
                 default="https://gitlab.com/api/v4/"),
        registration_token=dict(required=True, type='str'),
        state=dict(required=False, type='str', default="present", choices=["present", "absent"]),
    )


def main():
    argument_spec = get_gitlab_argument_spec()
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    target_state = module.params['state']
    description = module.params['name']
    private_token = module.params['private_token']
    url = module.params['url']
    active = module.params['active']
    tag_list = module.params['tag_list']
    run_untagged = module.params['run_untagged']
    locked = module.params['locked']
    access_level = module.params['access_level']
    maximum_timeout = module.params['maximum_timeout']

    api = AnsibleGitlabAPI(module, url, private_token)
    id = api.get_runner_id(description)
    target_runner = Runner(id, description, active, tag_list,
                           run_untagged, locked, access_level, maximum_timeout)
    token = None
    api_runner = None
    response = None
    changed = False

    # Check if runner needs to be registered, updated or deleted
    # Don't actually change anything if module is in check_mode (dry run)
    if target_state == 'present':
        if id is None:
            if not module.check_mode:
                response = api.register_runner(
                    target_runner, module.params["registration_token"])
            token = response['token']
            changed = True
        else:
            api_runner_details = api.get_runner_details(id)
            response = api_runner_details
            token = api_runner_details['token']
            id = api_runner_details['id']
            description = api_runner_details['description']
            active = api_runner_details['active']
            tag_list = api_runner_details['tag_list']
            locked = api_runner_details['locked']
            access_level = api_runner_details['access_level']
            maximum_timeout = api_runner_details['maximum_timeout']
            api_runner = Runner(id, description, active, tag_list,
                                run_untagged, locked, access_level, maximum_timeout)
            if api_runner == target_runner:
                changed = False
            else:
                if not module.check_mode:
                    response = api.update_runner(id, target_runner)
                changed = True
    elif target_state == 'absent':
        if id is None:
            changed = False
        else:
            if not module.check_mode:
                response = api.delete_runner(id)
            changed = True
    module.exit_json(changed=changed, msg=response, token=token)


if __name__ == '__main__':
    main()
