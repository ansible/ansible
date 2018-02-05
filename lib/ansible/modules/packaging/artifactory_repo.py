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
module: artifactory_repo

short_description: Provides management operations for repositories in JFrog Artifactory

version_added: "2.5"

description:
    - "Provides basic management operations against repositories JFrog Artifactory 5+."

options:
    artifactory_url:
        description:
            - The target URL for managing artifactory. For certain operations,
              you can include the repository key appended to the end of the
              url.
        required: true
    name:
        description:
            - Name of the target repo to perform CRUD operations against.
        required: true
    repo_position:
        description:
            - Sets the resolution order for which repos of the same type are
              queried. This governs the order local, remote repositories
              and other virtual repositories are listed in the virtual
              repository configuration. By default, this is ignored so that
              the order is governed by the order of creation.
        required: false
    repo_config:
        description:
            - The configuration for the given repository as a json formatted
              string. This configuration must conform to JFrog Artifactory
              Repository Configuration JSON published at jfrog.com . Basic
              validation is performed against required fields for Artifactory
              5+ for required fields in create/replace calls, which is the
              following... 'rclass' must be defined for all create calls. If
              creating a 'virtual' repository, 'packageType'
              must be defined with an appropriate type. If creating
              a 'remote' repository, 'url' must be defined in the
              configuration.
        required: false
    username:
        description:
            - username to be used in Basic Auth against Artifactory. Not
              required if using auth_token for basic auth.
        required: false
    password:
        description:
            - password to be used in Basic Auth against Artifactory. Not
              required if using auth_token for basic auth.
        required: false
    auth_token:
        description:
            - authentication token to be used in Basic Auth against
              Artifactory. Not required if using username/password for basic
              auth.
        required: false
    validate_certs:
        description:
            - True to validate SSL certificates, False otherwise.
        required: false
        choices:
          - True
          - False
        default: False
    client_cert:
        description:
            - PEM formatted certificate chain file to be used for SSL client
              authentication. This file can also include the key as well, and
              if the key is included, I(client_key) is not required
        required: false
    client_key:
        description:
            - PEM formatted file that contains your private key to be used for
              SSL client authentication. If I(client_cert) contains both the
              certificate and key, this option is not required.
        required: false
    force_basic_auth:
        description:
            - The library used by the uri module only sends authentication
              information when a webservice responds to an initial request
              with a 401 status. Since some basic auth services do not properly
              send a 401, logins will fail. This option forces the sending of
              the Basic authentication header upon initial request.
        required: false
        choices:
          - True
          - False
        default: False
    state:
        description:
            - The state the repository should be in. 'present' ensures that a
              repository exists, but not replaced.
              'absent' ensures that the repository is deleted.
              'read' will return the configuration if the repository exists.
              'list' will return a list of all repositories that currently
              exist in the target artifactory. The configuration supplied
              will overwrite the configuration that exists. If you wish to, for
              instance, append new repositories to a virtual repository, you
              will need to construct the complete list outside of the module
              and pass it in.
        required: false
        choices:
          - present
          - absent
          - read
          - list
        default: read
    rclass:
        description:
            - The type of remote repository you wish to create.
        required: false
        choices:
          - local
          - remote
          - virtual
    url:
        description:
            - The url for the repository.
        required: false
    packageType:
        description:
            - The packageType of the repository.
        required: false
        choices:
          - bower
          - chef
          - composer
          - conan
          - debian
          - docker
          - gems
          - generic
          - gitlfs
          - gradle
          - ivy
          - maven
          - npm
          - nuget
          - puppet
          - pypi
          - sbt
          - vagrant
          - yum
    repo_config_dict:
        description:
            - A dictionary in yaml format of valid configuration values. These
              dictionary key/value pairs match the configuration spec of
              repo_config.
        required: false
    repoLayoutRef:
        description:
            - The name of the target layout for this repository.
        required: false

author:
    - Kyle Haley (@quadewarren)
'''

EXAMPLES = '''
# Create a local repository in artifactory with auth_token with minimal
# config requirements
- name: create test-local-creation repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    auth_token: my_token
    name: test-local-creation
    state: present
    repo_config: '{"rclass": "local"}'

# Create a local repository in artifactory with auth_token using top level params
# config requirements
- name: create test-local-creation repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    auth_token: my_token
    name: test-local-creation
    state: present
    rclass: local

# Create a local repository in artifactory with multiple levels of params
# config requirements
- name: create test-local-creation repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    auth_token: my_token
    name: test-local-creation
    state: present
    rclass: local
    repo_config_dict:
        packageType: generic
    repo_config: '{"description": "Test description"}'

# Delete a local repository in artifactory with auth_token
- name: delete test-local-delete repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    auth_token: your_token
    name: test-local-delete
    state: absent

# Create a remote repository in artifactory with username/password with
# minimal config requirements
- name: create test-remote-creation repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    username: your_username
    password: your_pass
    name: test-remote-creation
    state: present
    repo_config: '{"rclass": "remote", "url": "http://http://host:port/some-repo"}'

# Create a virtual repository in artifactory with auth_token with
# minimal config requirements
- name: create test-remote-creation repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    auth_token: your_token
    name: test-virtual-creation
    state: present
    repo_config: '{"rclass": "virtual", "packageType": "generic"}'

# Update a virtual repository in artifactory with username/password
- name: update test-virtual-update repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    username: your_username
    password: your_pass
    name: test-virtual-update
    state: present
    repo_config: '{"description": "New public description."}'
  register: test_virtual_config

# Repository config is in response for successful create/update calls,
# regardless if call resulted in a change. Successful delete calls
# contain the config of the repo just before deletion for later use in play.
- name: dump test_virtual_config config json
  debug:
    msg: '{{ test_virtual_config.config }}'

# Update a virtual repository with a config hash
# Configuration provided replaces the existing configuration, so
# if you want to append values to an existing list, that list needs to be
# constructed outside of the module and passed in.
- name: update test-virtual-update repo
  artifactory_repo:
    artifactory_url: https://artifactory.repo.example.com
    auth_token: your_token
    name: test-virtual-update
    state: present
    repo_config_dict:
      description: "Another new public description"
      repositories:
        - pypi-remote
        - mypi-local
'''

RETURN = '''
original_message:
    description:
        - A brief sentence describing what action the module was attempting
          to take against which repository and what artifactory url.
    returned: success
    type: str
message:
    description: The result of the attempted action.
    returned: success
    type: str
config:
    description:
        - The configuration of a successfully created repository, an updated
          repository (whether or not changed=True), or the config
          of a repository that was successfully deleted.
    returned: success
    type: dict
'''


import ast
import json

import ansible.module_utils.artifactory as art_base
import ansible.module_utils.six.moves.urllib.error as urllib_error

from ansible.module_utils.basic import AnsibleModule


LOCAL_RCLASS = "local"
REMOTE_RCLASS = "remote"
VIRTUAL_RCLASS = "virtual"

VALID_RCLASSES = [LOCAL_RCLASS, REMOTE_RCLASS, VIRTUAL_RCLASS]

VALID_PACKAGETYPES = ["bower",
                      "chef",
                      "composer",
                      "conan",
                      "debian",
                      "docker",
                      "gems",
                      "generic",
                      "gitlfs",
                      "gradle",
                      "ivy",
                      "maven",
                      "npm",
                      "nuget",
                      "puppet",
                      "pypi",
                      "sbt",
                      "vagrant",
                      "yum"]

KEY_CONFIG_MAP = {
    "rclass":
        {"valid_values": VALID_RCLASSES,
         "values_require_keys":
            {VIRTUAL_RCLASS: ["packageType"],
             REMOTE_RCLASS: ["url"]},
         "always_required": True},
    "packageType":
        {"valid_values": VALID_PACKAGETYPES}}

URI_CONFIG_MAP = {"api/repositories": KEY_CONFIG_MAP}


class ArtifactoryRepoManagement(art_base.ArtifactoryBase):
    def __init__(self, artifactory_url, repo=None, repo_position=None,
                 repo_config=None, username=None, password=None,
                 auth_token=None, validate_certs=False, client_cert=None,
                 client_key=None, force_basic_auth=False, config_map=None):
        super(ArtifactoryRepoManagement, self).__init__(
            username=username,
            password=password,
            auth_token=auth_token,
            validate_certs=validate_certs,
            client_cert=client_cert,
            client_key=client_key,
            force_basic_auth=force_basic_auth,
            config_map=config_map)
        self.artifactory_url = artifactory_url
        self.repo = repo
        self.repo_position = repo_position
        self.repo_config = repo_config

        if self.repo:
            self.working_url = '%s/%s' % (self.artifactory_url, self.repo)
        else:
            self.working_url = self.artifactory_url

    def get_repositories(self):
        return self.query_artifactory(self.artifactory_url, 'GET')

    def get_repository_config(self):
        return self.query_artifactory(self.working_url, 'GET')

    def delete_repository(self):
        return self.query_artifactory(self.working_url, 'DELETE')

    def create_repository(self):
        method = 'PUT'
        serial_config_data = self.get_valid_conf(method)
        create_repo_url = self.working_url
        if self.repo_position:
            if isinstance(self.repo_position, int):
                create_repo_url = '%s?pos=%d' % (create_repo_url,
                                                 self.repo_position)
            else:
                raise ValueError("repo_position must be an integer.")

        return self.query_artifactory(create_repo_url, method,
                                      data=serial_config_data)

    def update_repository_config(self):
        method = 'POST'
        serial_config_data = self.get_valid_conf(method)
        return self.query_artifactory(self.working_url, method,
                                      data=serial_config_data)

    def get_valid_conf(self, method):
        config_dict = self.convert_config_to_dict(self.repo_config)
        if method == 'PUT':
            self.validate_config_required_keys(self.artifactory_url,
                                               config_dict)
        self.validate_config_values(self.artifactory_url, config_dict)
        serial_config_data = self.serialize_config_data(config_dict)
        return serial_config_data


def run_module():
    state_map = ['present', 'absent', 'read', 'list']
    rclass_state_map = VALID_RCLASSES
    packageType_state_map = VALID_PACKAGETYPES
    module_args = dict(
        artifactory_url=dict(type='str', required=True),
        name=dict(type='str', required=True),
        repo_position=dict(type='int', default=None),
        repo_config=dict(type='str', default=None),
        username=dict(type='str', default=None),
        password=dict(type='str', no_log=True, default=None),
        auth_token=dict(type='str', no_log=True, default=None),
        validate_certs=dict(type='bool', default=False),
        client_cert=dict(type='path', default=None),
        client_key=dict(type='path', default=None),
        force_basic_auth=dict(type='bool', default=False),
        state=dict(type='str', default='read', choices=state_map),
        rclass=dict(type='str', default=None, choices=rclass_state_map),
        packageType=dict(type='str', default=None,
                         choices=packageType_state_map),
        url=dict(type='str', default=None),
        repoLayoutRef=dict(type='str', default=None),
        repo_config_dict=dict(type='dict', default=dict()),
    )

    result = dict(
        changed=False,
        original_message='',
        message='',
        config=dict()
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_together=[['username', 'password']],
        required_one_of=[['password', 'auth_token']],
        mutually_exclusive=[['password', 'auth_token']],
        required_if=[['state', 'present', ['artifactory_url', 'name']],
                     ['state', 'absent', ['artifactory_url', 'name']],
                     ['state', 'list', ['artifactory_url', 'name']],
                     ['state', 'read', ['artifactory_url', 'name']]],
        supports_check_mode=True,
    )

    artifactory_url = module.params['artifactory_url']
    repository = module.params['name']
    repo_position = module.params['repo_position']
    repo_config = module.params['repo_config']
    username = module.params['username']
    password = module.params['password']
    auth_token = module.params['auth_token']
    validate_certs = module.params['validate_certs']
    client_cert = module.params['client_cert']
    client_key = module.params['client_key']
    force_basic_auth = module.params['force_basic_auth']
    state = module.params['state']
    repo_config_dict = module.params['repo_config_dict']

    if repo_config:
        # temporarily convert to dict for validation
        repo_config = ast.literal_eval(repo_config)

    fail_messages = []

    fails = art_base.validate_config_params(repo_config, repo_config_dict,
                                            'repo_config', 'repo_config_dict')
    fail_messages.extend(fails)

    fails = art_base.validate_top_level_params('rclass', module, repo_config,
                                               repo_config_dict, 'repo_config',
                                               'repo_config_dict')
    fail_messages.extend(fails)
    fails = art_base.validate_top_level_params('packageType', module,
                                               repo_config, repo_config_dict,
                                               'repo_config',
                                               'repo_config_dict')
    fail_messages.extend(fails)
    fails = art_base.validate_top_level_params('url', module, repo_config,
                                               repo_config_dict, 'repo_config',
                                               'repo_config_dict')
    fail_messages.extend(fails)
    fails = art_base.validate_top_level_params('repoLayoutRef',
                                               module, repo_config,
                                               repo_config_dict, 'repo_config',
                                               'repo_config_dict')
    fail_messages.extend(fails)

    # Populate failure messages
    failure_message = "".join(fail_messages)

    # Conflicting config values should not be resolved
    if failure_message:
        module.fail_json(msg=failure_message, **result)

    repo_dict = dict()
    if module.params['name']:
        repo_dict['key'] = module.params['name']
    if module.params['rclass']:
        repo_dict['rclass'] = module.params['rclass']
    if module.params['packageType']:
        repo_dict['packageType'] = module.params['packageType']
    if module.params['url']:
        repo_dict['url'] = module.params['url']
    if module.params['repoLayoutRef']:
        repo_dict['repoLayoutRef'] = module.params['repoLayoutRef']
    if repo_config:
        repo_dict.update(repo_config)
    if repo_config_dict:
        repo_dict.update(repo_config_dict)
    repo_config = json.dumps(repo_dict)

    result['original_message'] = ("Perform state '%s' against repo '%s' "
                                  "within artifactory '%s'"
                                  % (state, repository, artifactory_url))

    artifactory_repo = ArtifactoryRepoManagement(
        artifactory_url=artifactory_url,
        repo=repository,
        repo_position=repo_position,
        repo_config=repo_config,
        username=username,
        password=password,
        auth_token=auth_token,
        validate_certs=validate_certs,
        client_cert=client_cert,
        client_key=client_key,
        force_basic_auth=force_basic_auth,
        config_map=URI_CONFIG_MAP)

    repository_exists = False
    try:
        artifactory_repo.get_repository_config()
        repository_exists = True
    except urllib_error.HTTPError as http_e:
        if http_e.getcode() == 400:
            # Instead of throwing a 404, a 400 is thrown if a repo doesn't
            # exist. Have to fall through and assume the repo doesn't exist
            # and that another error did not occur. If there is another problem
            # it will have to be caught by try/catch blocks further below.
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
            artifactory_repo.validate_config_values(artifactory_url,
                                                    repo_dict)
            if not repository_exists:
                artifactory_repo.validate_config_required_keys(artifactory_url,
                                                               repo_dict)
    except art_base.ConfigValueTypeMismatch as cvtm:
        fail_messages.append(cvtm.message + ". ")
    except art_base.InvalidConfigurationData as icd:
        fail_messages.append(icd.message + ". ")
    except art_base.InvalidArtifactoryURL as iau:
        fail_messages.append(iau.message + ". ")

    # Populate failure messages
    failure_message = "".join(fail_messages)

    if failure_message:
        module.fail_json(msg=failure_message, **result)

    if module.check_mode:
        result['message'] = 'check_mode success'
        module.exit_json(**result)

    repo_not_exists_msg = ("Repository '%s' does not exist." % repository)
    resp_is_invalid_failure = ("An unknown error occurred while attempting to "
                               "'%s' repo '%s'. Response should "
                               "not be None.")
    try:
        if state == 'list':
            result['message'] = ("List of all repos against "
                                 "artifactory_url: %s" % artifactory_url)
            resp = artifactory_repo.get_repositories()
            result['config'] = json.loads(resp.read())
        elif state == 'read':
            if not repository_exists:
                result['message'] = repo_not_exists_msg
            else:
                resp = artifactory_repo.get_repository_config()
                if resp:
                    result['message'] = ("Successfully read config "
                                         "on repo '%s'." % repository)
                    result['config'] = json.loads(resp.read())
                    result['changed'] = True
                else:
                    failure_message = (resp_is_invalid_failure
                                       % (state, repository))
        elif state == 'present':
            # If the repo doesn't exist, create it.
            # If the repo does exist, perform an update on it ONLY if
            # configuration supplied has values that don't match the remote
            # config.
            if not repository_exists:
                result['message'] = ('Attempting to create repo: %s'
                                     % repository)
                resp = artifactory_repo.create_repository()
                if resp:
                    result['message'] = resp.read()
                    result['changed'] = True
                else:
                    failure_message = (resp_is_invalid_failure
                                       % (state, repository))
            else:
                result['message'] = ('Attempting to update repo: %s'
                                     % repository)
                current_config = artifactory_repo.get_repository_config()
                current_config = json.loads(current_config.read())
                desired_config = ast.literal_eval(repo_config)
                # Compare desired config with current config against repo.
                # If config values are identical, don't update.
                resp = None
                for key in current_config:
                    if key in desired_config:
                        if desired_config[key] != current_config[key]:
                            resp = artifactory_repo.update_repository_config()
                # To guarantee idempotence. If underlying libraries don't
                # throw an exception, it could incorrectly report a success
                # when there was actually a failure.
                if resp:
                    result['message'] = ("Successfully updated config "
                                         "on repo '%s'." % repository)
                    result['changed'] = True
                else:
                    # Config values were identical.
                    result['message'] = ("Repo '%s' was not updated because "
                                         "config was identical." % repository)
            # Attach the repository config to result
            current_config = artifactory_repo.get_repository_config()
            result['config'] = json.loads(current_config.read())
        elif state == 'absent':
            if not repository_exists:
                result['message'] = repo_not_exists_msg
            else:
                # save config for output on successful delete so it can be
                # used later in play if recreating repositories
                current_config = artifactory_repo.get_repository_config()
                resp = artifactory_repo.delete_repository()
                if resp:
                    result['message'] = ("Successfully deleted repo '%s'."
                                         % repository)
                    result['changed'] = True
                    result['config'] = json.loads(current_config.read())
                else:
                    failure_message = (resp_is_invalid_failure
                                       % (state, repository))
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
