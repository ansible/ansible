#!/usr/bin/python
# coding: utf-8
#
# Copyright: (c) 2019, Vladimir Porshkevich (@porshkevich) <neosonic@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = u'''
module: docker_plugin
version_added: "2.8"
short_description: Manage Docker plugins
description:
  - Install/remove Docker plugins.
  - Performs largely the same function as the "docker plugin" CLI subcommand.
options:
  name:
    description:
      - Name of the plugin to operate on.
    required: true
    type: str

  alias:
    description:
      - Alias of the plugin to operate on. Same plugin can be installed with different alias.
    type: str

  plugin_options:
    description:
      - Dictionary of plugin settings.
    type: dict

  state:
    description:
      - C(absent) remove the plugin.
      - C(present) install the plugin, if it does not already exist.
      - C(enable) enable the plugin.
      - C(disable) disable the plugin.
    default: present
    choices:
      - absent
      - present
      - enable
      - disable

extends_documentation_fragment:
  - docker
  - docker.docker_py_2_documentation

author:
  - Vladimir Porshkevich (@porshkevich)

requirements:
  - "python >= 2.7"
  - "docker-py >= 2.6.0"
  - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
    module has been superseded by L(docker,https://pypi.org/project/docker/)
    (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
    Version 2.1.0 or newer is only available with the C(docker) module."
  - "Docker API >= 1.25"
'''

EXAMPLES = '''
- name: Install a plugin
  docker_plugin:
    name: plugin_one

- name: Remove a plugin
  docker_plugin:
    name: plugin_one
    state: absent

- name: Install a plugin with options
  docker_plugin:
    name: weaveworks/net-plugin:latest_release
    alias: weave-net-plugin
    plugin_options:
      IPALLOC_RANGE: "10.32.0.0/12"
      WEAVE_PASSWORD: XXXXXXXX
'''

RETURN = '''
facts:
    description: Plugin inspection results for the affected plugin.
    returned: success
    type: dict
    sample: {}
'''

try:
    from docker.errors import APIError, NotFound
    from docker.models.plugins import Plugin
    from docker import DockerClient
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker.common import DockerBaseClass, AnsibleDockerClient
from ansible.module_utils.six import iteritems, text_type


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()
        self.client = client

        self.name = None
        self.alias = None
        self.plugin_options = None
        self.debug = None

        for key, value in iteritems(client.module.params):
            setattr(self, key, value)


def prepare_options(options):
    return ['%s=%s' % (k, v if v is not None else "") for k, v in iteritems(options)] if options else []


def parse_options(options_list):
    return dict((k, v) for k, v in map(lambda x: x.split('=', 1), options_list)) if options_list else {}


class DockerPluginManager(object):

    def __init__(self, client):
        self.client = client

        self.dclient = DockerClient()
        self.dclient.api = client

        self.parameters = TaskParameters(client)
        self.check_mode = self.client.check_mode
        self.results = {
            u'changed': False,
            u'actions': []
        }
        self.diff = self.client.module._diff

        self.existing_plugin = self.get_existing_plugin()

        state = self.parameters.state
        if state == 'present':
            self.present()
        elif state == 'absent':
            self.absent()
        elif state == 'enable':
            self.enable()
        elif state == 'disable':
            self.disable()

    def get_plugin_name(self):
        return self.parameters.alias or self.parameters.name

    def get_existing_plugin(self):
        name = self.get_plugin_name()
        try:
            plugin = self.dclient.plugins.get(name)
        except NotFound:
            return None
        except APIError as e:
            self.client.fail(text_type(e))

        return plugin

    def has_different_config(self):
        """
        Return the list of differences between the current parameters and the existing volume.

        :return: list of options that differ
        """
        differences = []
        if self.parameters.plugin_options:
            if not self.existing_plugin.settings:
                differences.append('plugin_options')
            else:
                existing_options_list = self.existing_plugin.settings['Env']
                existing_options = parse_options(existing_options_list)

                for key, value in iteritems(self.parameters.plugin_options):
                    if ((not existing_options.get(key) and value) or
                            not value or
                            value != existing_options[key]):
                        differences.append('plugin_settings.%s' % key)

        return differences

    def install_plugin(self):
        if not self.existing_plugin:
            if not self.check_mode:
                try:
                    self.existing_plugin = self.dclient.plugins.install(self.parameters.plugin_name, self.parameters.plugin_alias)
                except APIError as e:
                    self.client.fail(text_type(e))

            self.results['actions'].append("Installed plugin %s" % self.get_plugin_name())
            self.results['changed'] = True

    def remove_plugin(self):
        if self.existing_plugin:
            if not self.check_mode:
                try:
                    self.existing_plugin.remove()
                except APIError as e:
                    self.client.fail(text_type(e))

            self.results['actions'].append("Removed plugin %s" % self.get_plugin_name())
            self.results['changed'] = True

    def update_plugin(self):
        if not self.check_mode:
            try:
                if self.existing_plugin.enabled:
                    self.existing_plugin.disable()
                self.existing_plugin.configure(prepare_options(self.parameters.plugin_options))
                self.existing_plugin.enable(1)
            except APIError as e:
                self.client.fail(text_type(e))

        self.results['actions'].append("Updated plugin %s settings" % self.get_plugin_name())
        self.results['changed'] = True

    def present(self):
        differences = []
        if self.existing_plugin:
            differences = self.has_different_config()

        if self.existing_plugin:
            self.update_plugin()
        else:
            self.install_plugin()

        if self.diff or self.check_mode or self.parameters.debug:
            self.results['diff'] = differences

        if not self.check_mode and not self.parameters.debug:
            self.results.pop('actions')

    def absent(self):
        self.remove_plugin()

    def enable(self):
        if self.existing_plugin:
            if not self.check_mode:
                try:
                    self.existing_plugin.enable(1)
                except APIError as e:
                    self.client.fail(text_type(e))

            self.results['actions'].append("Enabled plugin %s" % self.get_plugin_name())
            self.results['changed'] = True
        else:
            self.fail("Cannot enable plugin: Plugin not exist")

    def disable(self):
        if self.existing_plugin:
            if not self.check_mode:
                try:
                    self.existing_plugin.disable()
                except APIError as e:
                    self.client.fail(text_type(e))

            self.results['actions'].append("Disable plugin %s" % self.get_plugin_name())
            self.results['changed'] = True
        else:
            self.fail("Cannot disable plugin: Plugin not exist")


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        alias=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent', 'enable', 'disable']),
        plugin_options=dict(type='dict', default={}),
        debug=dict(type='bool', default=False)
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='2.6.0',
        min_docker_api_version='1.25'
    )

    cm = DockerPluginManager(client)
    client.module.exit_json(**cm.results)


if __name__ == '__main__':
    main()
