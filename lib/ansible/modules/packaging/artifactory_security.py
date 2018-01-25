#!/usr/bin/python
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: artifactory_security

short_description: Provides management operations for security operations in JFrog Artifactory

version_added: "2.5"

description:
    - Provides basic management operations against security operations in JFrog
      Artifactory 5+. Please reference this configuration spec for the creation
      of users, groups, or permission targets.
      U(https://www.jfrog.com/confluence/display/RTF/Security+Configuration+JSON)

options:
    artifactory_url:
        description:
            - The target URL for managing artifactory. For certain operations,
              you can include the group name appended to the end of the
              url.
        required: true
    name:
        description:
            - Name of the target user/group/permission target to perform
              CRUD operations against.
        required: true
    sec_config:
        description:
            - The string representations of the JSON used to create the target
              security objects, whether it be a user, group, or permission
              target. Please reference the JFrog Artifactory Security
              Configuration JSON for directions on what key/values to use.
    username:
        description:
            - username to be used in Basic Auth against Artifactory. Not
              required if using auth_token for basic auth.
    auth_password:
        description:
            - password to be used in Basic Auth against Artifactory. Not
              required if using auth_token for basic auth.
    auth_token:
        description:
            - authentication token to be used in Basic Auth against
              Artifactory. Not required if using username/auth_password for
              basic auth.
    validate_certs:
        description:
            - True to validate SSL certificates, False otherwise.
        type: bool
        default: false
    client_cert:
        description:
            - PEM formatted certificate chain file to be used for SSL client
              authentication. This file can also include the key as well, and
              if the key is included, I(client_key) is not required
    client_key:
        description:
            - PEM formatted file that contains your private key to be used for
              SSL client authentication. If I(client_cert) contains both the
              certificate and key, this option is not required.
    force_basic_auth:
        description:
            - The library used by the uri module only sends authentication
              information when a webservice responds to an initial request
              with a 401 status. Since some basic auth services do not properly
              send a 401, logins will fail. This option forces the sending of
              the Basic authentication header upon initial request.
        type: bool
        default: false
    state:
        description:
            - The state the target (permission target/group/user) should be in.
              'present' ensures that the target exists, but is not replaced.
              The configuration supplied will overwrite the configuration that
              exists. 'absent' ensures that the the target is deleted.
              'read' will return the configuration if the target exists.
              'list' will return a list of all targets against the specified
              url that currently exist in the target artifactory. If you wish
              to, for instance, append a list of repositories that a permission
              target has access to, you will need to construct the complete
              list outside of the module and pass it in.
        choices:
          - present
          - absent
          - read
          - list
        default: read
    sec_config_dict:
        description:
            - A dictionary in yaml format of valid configuration values against
              a permission target, group, or user. These
              dictionary values must match any other values passed in, such as
              those within top-level parameters or within the configuration
              string in sec_config.
    password:
        description:
            - The password used for creating a new user within Artifactory. It
              will not be displayed in the log output.
    email:
        description:
            - The email used for creating a new user within Artifactory.
    repositories:
        description:
            - The list of repositories associated with a permission target,
              which represents the list of repositories that permission target,
              can access.

author:
    - Kyle Haley (@quadewarren)
'''

EXAMPLES = '''
# Create a user using top-level parameters
- name: create a temp user
  artifactory_security:
    artifactory_url: http://artifactory.url.com/artifactory/api/security/users
    auth_token: MY_TOKEN
    name: temp-user
    email: whatever@email.com
    password: whatever
    state: present

# Update the user config using top-level parameters
- name: update a user config using top-level parameters
  artifactory_security:
    artifactory_url: http://artifactory.url.com/artifactory/api/security/users
    auth_token: MY_TOKEN
    name: temp-user
    email: whatever@diffemail.com
    state: present

- name: delete the temp user
  artifactory_security:
    artifactory_url: http://artifactory.url.com/artifactory/api/security/users
    auth_token: MY_TOKEN
    name: temp-user
    state: absent

- name: create a new group using config hash
  artifactory_security:
    artifactory_url: '{{ art_url_group }}'
    auth_token: '{{ auth_token }}'
    name: "temp-group"
    sec_config_dict:
      description: A group representing a collection of users. Can be LDAP.
    state: present

- name: update the group using config hash
  artifactory_security:
    artifactory_url: '{{ art_url_group }}'
    auth_token: '{{ auth_token }}'
    name: "temp-group"
    sec_config_dict:
      description: A group of users from LDAP. Can be LDAP.
      realm: "Realm name (e.g. ARTIFACTORY, CROWD)"
    state: present

- name: create a temp user
  artifactory_security:
    artifactory_url: '{{ art_url_group }}'
    auth_token: '{{ auth_token }}'
    name: "temp-group"
    state: absent
'''

RETURN = '''
original_message:
    description:
        - A brief sentence describing what action the module was attempting
          to take against which user/group/permission and what artifactory url.
    returned: success
    type: str
message:
    description: The result of the attempted action.
    returned: success
    type: str
config:
    description:
        - The configuration of a successfully created user/group/permission,
          an updated user/group/permission (whether or not changed=True), or
          the config of a user/group/permission that was successfully deleted.
    returned: success
    type: dict
'''


import ast
import json

import ansible.module_utils.artifactory as art_base
import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible.module_utils.basic import AnsibleModule


USER_CONFIG_MAP = {
    "email":
        {"always_required": True},
    "password":
        {"always_required": True}}

PERMISSION_CONFIG_MAP = {
    "repositories":
        {"always_required": True}}

URI_CONFIG_MAP = {"api/security/users": USER_CONFIG_MAP}
URI_CONFIG_MAP["api/security/permissions"] = PERMISSION_CONFIG_MAP
# There are no required values for groups, but if they are not defined
# a validation error will be thrown.
URI_CONFIG_MAP["api/security/groups"] = True


class ArtifactorySecurity(art_base.ArtifactoryBase):
    def __init__(self, artifactory_url, name=None,
                 sec_config=None, username=None, password=None,
                 auth_token=None, validate_certs=False, client_cert=None,
                 client_key=None, force_basic_auth=False, config_map=None):
        super(ArtifactorySecurity, self).__init__(
            username=username,
            password=password,
            auth_token=auth_token,
            validate_certs=validate_certs,
            client_cert=client_cert,
            client_key=client_key,
            force_basic_auth=force_basic_auth,
            config_map=config_map)
        self.artifactory_url = artifactory_url
        self.name = name
        self.sec_config = sec_config

        if self.name:
            self.working_url = '%s/%s' % (self.artifactory_url, self.name)
        else:
            self.working_url = self.artifactory_url

    def get_targets(self):
        return self.query_artifactory(self.artifactory_url, 'GET')

    def get_target_config(self):
        return self.query_artifactory(self.working_url, 'GET')

    def delete_target(self):
        return self.query_artifactory(self.working_url, 'DELETE')

    def create_target(self):
        method = 'PUT'
        serial_config_data = self.get_valid_conf(method)
        create_target_url = self.working_url
        return self.query_artifactory(create_target_url, method,
                                      data=serial_config_data)

    def update_target_config(self):
        method = 'POST'
        serial_config_data = self.get_valid_conf(method)
        return self.query_artifactory(self.working_url, method,
                                      data=serial_config_data)

    def get_valid_conf(self, method):
        config_dict = self.convert_config_to_dict(self.sec_config)
        if method == 'PUT':
            self.validate_config_required_keys(self.artifactory_url,
                                               config_dict)
        self.validate_config_values(self.artifactory_url, config_dict)
        serial_config_data = self.serialize_config_data(config_dict)
        return serial_config_data


def run_module():
    state_map = ['present', 'absent', 'read', 'list']
    module_args = dict(
        artifactory_url=dict(type='str', required=True),
        name=dict(type='str', required=True),
        sec_config=dict(type='str', default=None),
        username=dict(type='str', default=None),
        auth_password=dict(type='str', no_log=True, default=None),
        auth_token=dict(type='str', no_log=True, default=None),
        validate_certs=dict(type='bool', default=False),
        client_cert=dict(type='path', default=None),
        client_key=dict(type='path', default=None),
        force_basic_auth=dict(type='bool', default=False),
        state=dict(type='str', default='read', choices=state_map),
        sec_config_dict=dict(type='dict', default=dict()),
        password=dict(type='str', no_log=True, default=None),
        email=dict(type='str', default=None),
        repositories=dict(type='list', default=None),
    )

    result = dict(
        changed=False,
        original_message='',
        message='',
        config=dict()
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_together=[['username', 'auth_password']],
        required_one_of=[['auth_password', 'auth_token']],
        mutually_exclusive=[['auth_password', 'auth_token']],
        required_if=[['state', 'present', ['artifactory_url', 'name']],
                     ['state', 'absent', ['artifactory_url', 'name']],
                     ['state', 'list', ['artifactory_url', 'name']],
                     ['state', 'read', ['artifactory_url', 'name']]],
        supports_check_mode=True,
    )

    artifactory_url = module.params['artifactory_url']
    name = module.params['name']
    sec_config = module.params['sec_config']
    username = module.params['username']
    auth_password = module.params['auth_password']
    auth_token = module.params['auth_token']
    validate_certs = module.params['validate_certs']
    client_cert = module.params['client_cert']
    client_key = module.params['client_key']
    force_basic_auth = module.params['force_basic_auth']
    state = module.params['state']
    sec_config_dict = module.params['sec_config_dict']

    if sec_config:
        # temporarily convert to dict for validation
        sec_config = ast.literal_eval(sec_config)

    fail_messages = []

    fails = art_base.validate_config_params(sec_config, sec_config_dict,
                                            'sec_config',
                                            'sec_config_dict')
    fail_messages.extend(fails)
    fails = art_base.validate_top_level_params('name', module, sec_config,
                                               sec_config_dict,
                                               'sec_config',
                                               'sec_config_dict')
    fail_messages.extend(fails)
    fails = art_base.validate_top_level_params('password', module, sec_config,
                                               sec_config_dict,
                                               'sec_config',
                                               'sec_config_dict')
    fail_messages.extend(fails)
    fails = art_base.validate_top_level_params('email', module, sec_config,
                                               sec_config_dict,
                                               'sec_config',
                                               'sec_config_dict')
    fail_messages.extend(fails)
    fails = art_base.validate_top_level_params('repositories', module,
                                               sec_config,
                                               sec_config_dict,
                                               'sec_config',
                                               'sec_config_dict')
    fail_messages.extend(fails)

    # Populate failure messages
    failure_message = "".join(fail_messages)

    # Conflicting config values should not be resolved
    if failure_message:
        module.fail_json(msg=failure_message, **result)

    sec_dict = dict()
    if module.params['name']:
        sec_dict['name'] = module.params['name']
    if module.params['password']:
        sec_dict['password'] = module.params['password']
    if module.params['email']:
        sec_dict['email'] = module.params['email']
    if module.params['repositories']:
        sec_dict['repositories'] = module.params['repositories']
    if sec_config:
        sec_dict.update(sec_config)
    if sec_config_dict:
        sec_dict.update(sec_config_dict)
    sec_config = json.dumps(sec_dict)

    result['original_message'] = ("Perform state '%s' against group '%s' "
                                  "within artifactory '%s'"
                                  % (state, name, artifactory_url))

    art_sec = ArtifactorySecurity(
        artifactory_url=artifactory_url,
        name=name,
        sec_config=sec_config,
        username=username,
        password=auth_password,
        auth_token=auth_token,
        validate_certs=validate_certs,
        client_cert=client_cert,
        client_key=client_key,
        force_basic_auth=force_basic_auth,
        config_map=URI_CONFIG_MAP)

    target_exists = False
    try:
        art_sec.get_target_config()
        target_exists = True
    except urllib_error.HTTPError as http_e:
        if http_e.getcode() == 404:
            # If 404, the target is just not found. Continue on.
            pass
        else:
            message = ("HTTP response code was '%s'. Response message was"
                       " '%s'. " % (http_e.getcode(), http_e.read()))
            fail_messages.append(message)
    except urllib_error.URLError as url_e:
        message = ("A generic URLError was thrown. URLError: %s" % str(url_e))
        fail_messages.append(message)

    try:
        # Now that configs are lined up, verify required values in configs
        if state == 'present':
            art_sec.validate_config_values(artifactory_url,
                                           sec_dict)
            if not target_exists:
                art_sec.validate_config_required_keys(artifactory_url,
                                                      sec_dict)
    except art_base.ConfigValueTypeMismatch as cvtm:
        fail_messages.append(cvtm.message + ". ")
    except art_base.InvalidConfigurationData as icd:
        fail_messages.append(icd.message + ". ")
    except art_base.InvalidArtifactoryURL as iau:
        fail_messages.append(iau.message + ". ")

    # Populate failure messages
    failure_message = "".join(fail_messages)

    # Fail fast here, conflicting config values or invalid urls should not
    # be resolved.
    if failure_message:
        module.fail_json(msg=failure_message, **result)

    if module.check_mode:
        result['message'] = 'check_mode success'
        module.exit_json(**result)

    target_not_exists_msg = ("Target '%s' does not exist." % name)
    resp_is_invalid_failure = ("An unknown error occurred while attempting to "
                               "'%s' target '%s'. Response should "
                               "not be None.")
    try:
        if state == 'list':
            result['message'] = ("List of all targets against "
                                 "artifactory_url: %s" % artifactory_url)
            resp = art_sec.get_targets()
            result['config'] = json.loads(resp.read())
        elif state == 'read':
            if not target_exists:
                result['message'] = target_not_exists_msg
            else:
                resp = art_sec.get_target_config()
                if resp:
                    result['message'] = ("Successfully read config "
                                         "on target '%s'." % name)
                    result['config'] = json.loads(resp.read())
                    result['changed'] = True
                else:
                    failure_message = (resp_is_invalid_failure
                                       % (state, name))
        elif state == 'present':
            # If the target doesn't exist, create it.
            # If the target does exist, perform an update on it ONLY if
            # configuration supplied has values that don't match the remote
            # config. Some values may be read only, but these will not be
            # caught up front.
            if not target_exists:
                result['message'] = ('Attempting to create target: %s'
                                     % name)
                resp = art_sec.create_target()
                if resp:
                    result['message'] = resp.read()
                    result['changed'] = True
                else:
                    failure_message = (resp_is_invalid_failure
                                       % (state, name))
            else:
                result['message'] = ('Attempting to update target: %s'
                                     % name)
                current_config = art_sec.get_target_config()
                current_config = json.loads(current_config.read())
                desired_config = ast.literal_eval(sec_config)
                # Compare desired config with current config against target.
                # If config values are identical, don't update.
                resp = None
                for key in current_config:
                    if key in desired_config:
                        if desired_config[key] != current_config[key]:
                            resp = art_sec.update_target_config()
                if resp:
                    result['message'] = ("Successfully updated config "
                                         "on target '%s'." % name)
                    result['changed'] = True
                else:
                    # Config values were identical.
                    result['message'] = ("Target '%s' was not updated because "
                                         "config was identical." % name)
            # Attach the target config to result
            current_config = art_sec.get_target_config()
            result['config'] = json.loads(current_config.read())
        elif state == 'absent':
            if not target_exists:
                result['message'] = target_not_exists_msg
            else:
                # save config for output on successful delete so it can be
                # used later in play if recreating targets
                current_config = art_sec.get_target_config()
                resp = art_sec.delete_target()
                if resp:
                    result['message'] = ("Successfully deleted target '%s'."
                                         % name)
                    result['changed'] = True
                    result['config'] = json.loads(current_config.read())
                else:
                    failure_message = (resp_is_invalid_failure
                                       % (state, name))
    except urllib_error.HTTPError as http_e:
        message = ("HTTP response code was '%s'. Response message was"
                   " '%s'. " % (http_e.getcode(), http_e.read()))
        failure_message = message
    except urllib_error.URLError as url_e:
        message = ("A generic URLError was thrown. URLError: %s"
                   % str(url_e))
        failure_message = message
    except SyntaxError as s_e:
        message = ("%s. Response from artifactory was malformed: '%s' . "
                   % (str(s_e), resp))
        failure_message = message
    except ValueError as v_e:
        message = ("%s. Response from artifactory was malformed: '%s' . "
                   % (str(v_e), resp))
        failure_message = message
    except art_base.ConfigValueTypeMismatch as cvtm:
        failure_message = cvtm.message
    except art_base.InvalidConfigurationData as icd:
        failure_message = icd.message

    if failure_message:
        module.fail_json(msg=failure_message, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
