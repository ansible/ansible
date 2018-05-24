#!/usr/bin/python
# encoding: utf-8

# (c) 2016, Jiri Tyr <jiri.tyr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: jenkins_plugin
author: Jiri Tyr (@jtyr)
version_added: '2.2'
short_description: Add or remove Jenkins plugin
description:
  - Ansible module which helps to manage Jenkins plugins.

options:
  group:
    description:
      - Name of the Jenkins group on the OS.
    default: jenkins
  jenkins_home:
    description:
      - Home directory of the Jenkins user.
    default: /var/lib/jenkins
  mode:
    description:
      - File mode applied on versioned plugins.
  name:
    description:
      - Plugin name.
  owner:
    description:
      - Name of the Jenkins user on the OS.
    default: jenkins
  state:
    description:
      - Desired plugin state.
      - If the C(latest) is set, the check for new version will be performed
        every time. This is suitable to keep the plugin up-to-date.
    choices: [absent, present, pinned, unpinned, enabled, disabled, latest]
    default: present
  timeout:
    description:
      - Server connection timeout in secs.
    default: 30
  updates_expiration:
    description:
      - Number of seconds after which a new copy of the I(update-center.json)
        file is downloaded. This is used to avoid the need to download the
        plugin to calculate its checksum when C(latest) is specified.
      - Set it to C(0) if no cache file should be used. In that case, the
        plugin file will always be downloaded to calculate its checksum when
        C(latest) is specified.
    default: 86400
  updates_url:
    description:
      - URL of the Update Centre.
      - Used as the base URL to download the plugins and the
        I(update-center.json) JSON file.
    default: https://updates.jenkins-ci.org
  url:
    description:
      - URL of the Jenkins server.
    default: http://localhost:8080
  version:
    description:
      - Plugin version number.
      - If this option is specified, all plugin dependencies must be installed
        manually.
      - It might take longer to verify that the correct version is installed.
        This is especially true if a specific version number is specified.
      - Quote the version to prevent the value to be interpreted as float. For
        example if C(1.20) would be unquoted, it would become C(1.2).
  with_dependencies:
    description:
      - Defines whether to install plugin dependencies.
      - This option takes effect only if the I(version) is not defined.
    type: bool
    default: 'yes'

notes:
  - Plugin installation should be run under root or the same user which owns
    the plugin files on the disk. Only if the plugin is not installed yet and
    no version is specified, the API installation is performed which requires
    only the Web UI credentials.
  - It's necessary to notify the handler or call the I(service) module to
    restart the Jenkins service after a new plugin was installed.
  - Pinning works only if the plugin is installed and Jenkis service was
    successfully restarted after the plugin installation.
  - It is not possible to run the module remotely by changing the I(url)
    parameter to point to the Jenkins server. The module must be used on the
    host where Jenkins runs as it needs direct access to the plugin files.
  - "The C(params) option was removed in Ansible 2.5 due to circumventing Ansible's
    option handling"
extends_documentation_fragment:
  - url
'''

EXAMPLES = '''
- name: Install plugin
  jenkins_plugin:
    name: build-pipeline-plugin

- name: Install plugin without its dependencies
  jenkins_plugin:
    name: build-pipeline-plugin
    with_dependencies: no

- name: Make sure the plugin is always up-to-date
  jenkins_plugin:
    name: token-macro
    state: latest

- name: Install specific version of the plugin
  jenkins_plugin:
    name: token-macro
    version: "1.15"

- name: Pin the plugin
  jenkins_plugin:
    name: token-macro
    state: pinned

- name: Unpin the plugin
  jenkins_plugin:
    name: token-macro
    state: unpinned

- name: Enable the plugin
  jenkins_plugin:
    name: token-macro
    state: enabled

- name: Disable the plugin
  jenkins_plugin:
    name: token-macro
    state: disabled

- name: Uninstall plugin
  jenkins_plugin:
    name: build-pipeline-plugin
    state: absent

#
# Example of how to authenticate
#
- name: Install plugin
  jenkins_plugin:
    name: build-pipeline-plugin
    url_username: admin
    url_password: p4ssw0rd
    url: http://localhost:8888

#
# Example of a Play which handles Jenkins restarts during the state changes
#
- name: Jenkins Master play
  hosts: jenkins-master
  vars:
    my_jenkins_plugins:
      token-macro:
        enabled: yes
      build-pipeline-plugin:
        version: "1.4.9"
        pinned: no
        enabled: yes
  tasks:
    - name: Install plugins without a specific version
      jenkins_plugin:
        name: "{{ item.key }}"
      register: my_jenkins_plugin_unversioned
      when: >
        'version' not in item.value
      with_dict: "{{ my_jenkins_plugins }}"

    - name: Install plugins with a specific version
      jenkins_plugin:
        name: "{{ item.key }}"
        version: "{{ item.value['version'] }}"
      register: my_jenkins_plugin_versioned
      when: >
        'version' in item.value
      with_dict: "{{ my_jenkins_plugins }}"

    - name: Initiate the fact
      set_fact:
        jenkins_restart_required: no

    - name: Check if restart is required by any of the versioned plugins
      set_fact:
        jenkins_restart_required: yes
      when: item.changed
      with_items: "{{ my_jenkins_plugin_versioned.results }}"

    - name: Check if restart is required by any of the unversioned plugins
      set_fact:
        jenkins_restart_required: yes
      when: item.changed
      with_items: "{{ my_jenkins_plugin_unversioned.results }}"

    - name: Restart Jenkins if required
      service:
        name: jenkins
        state: restarted
      when: jenkins_restart_required

    - name: Wait for Jenkins to start up
      uri:
        url: http://localhost:8080
        status_code: 200
        timeout: 5
      register: jenkins_service_status
      # Keep trying for 5 mins in 5 sec intervals
      retries: 60
      delay: 5
      until: >
         'status' in jenkins_service_status and
         jenkins_service_status['status'] == 200
      when: jenkins_restart_required

    - name: Reset the fact
      set_fact:
        jenkins_restart_required: no
      when: jenkins_restart_required

    - name: Plugin pinning
      jenkins_plugin:
        name: "{{ item.key }}"
        state: "{{ 'pinned' if item.value['pinned'] else 'unpinned'}}"
      when: >
        'pinned' in item.value
      with_dict: "{{ my_jenkins_plugins }}"

    - name: Plugin enabling
      jenkins_plugin:
        name: "{{ item.key }}"
        state: "{{ 'enabled' if item.value['enabled'] else 'disabled'}}"
      when: >
        'enabled' in item.value
      with_dict: "{{ my_jenkins_plugins }}"
'''

RETURN = '''
plugin:
    description: plugin name
    returned: success
    type: string
    sample: build-pipeline-plugin
state:
    description: state of the target, after execution
    returned: success
    type: string
    sample: "present"
'''

from ansible.module_utils.basic import AnsibleModule, to_bytes
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils._text import to_native
import base64
import hashlib
import json
import os
import tempfile
import time


class JenkinsPlugin(object):
    def __init__(self, module):
        # To be able to call fail_json
        self.module = module

        # Shortcuts for the params
        self.params = self.module.params
        self.url = self.params['url']
        self.timeout = self.params['timeout']

        # Crumb
        self.crumb = {}

        if self._csrf_enabled():
            self.crumb = self._get_crumb()

        # Get list of installed plugins
        self._get_installed_plugins()

    def _csrf_enabled(self):
        csrf_data = self._get_json_data(
            "%s/%s" % (self.url, "api/json"), 'CSRF')

        if 'useCrumbs' not in csrf_data:
            self.module.fail_json(
                msg="Required fields not found in the Crumbs response.",
                details=csrf_data)

        return csrf_data['useCrumbs']

    def _get_json_data(self, url, what, **kwargs):
        # Get the JSON data
        r = self._get_url_data(url, what, **kwargs)

        # Parse the JSON data
        try:
            json_data = json.loads(to_native(r.read()))
        except Exception as e:
            self.module.fail_json(
                msg="Cannot parse %s JSON data." % what,
                details=to_native(e))

        return json_data

    def _get_url_data(
            self, url, what=None, msg_status=None, msg_exception=None,
            **kwargs):
        # Compose default messages
        if msg_status is None:
            msg_status = "Cannot get %s" % what

        if msg_exception is None:
            msg_exception = "Retrieval of %s failed." % what

        # Get the URL data
        try:
            response, info = fetch_url(
                self.module, url, timeout=self.timeout, **kwargs)

            if info['status'] != 200:
                self.module.fail_json(msg=msg_status, details=info['msg'])
        except Exception as e:
            self.module.fail_json(msg=msg_exception, details=to_native(e))

        return response

    def _get_crumb(self):
        crumb_data = self._get_json_data(
            "%s/%s" % (self.url, "crumbIssuer/api/json"), 'Crumb')

        if 'crumbRequestField' in crumb_data and 'crumb' in crumb_data:
            ret = {
                crumb_data['crumbRequestField']: crumb_data['crumb']
            }
        else:
            self.module.fail_json(
                msg="Required fields not found in the Crum response.",
                details=crumb_data)

        return ret

    def _get_installed_plugins(self):
        plugins_data = self._get_json_data(
            "%s/%s" % (self.url, "pluginManager/api/json?depth=1"),
            'list of plugins')

        # Check if we got valid data
        if 'plugins' not in plugins_data:
            self.module.fail_json(msg="No valid plugin data found.")

        # Create final list of installed/pined plugins
        self.is_installed = False
        self.is_pinned = False
        self.is_enabled = False

        for p in plugins_data['plugins']:
            if p['shortName'] == self.params['name']:
                self.is_installed = True

                if p['pinned']:
                    self.is_pinned = True

                if p['enabled']:
                    self.is_enabled = True

                break

    def install(self):
        changed = False
        plugin_file = (
            '%s/plugins/%s.jpi' % (
                self.params['jenkins_home'],
                self.params['name']))

        if not self.is_installed and self.params['version'] is None:
            if not self.module.check_mode:
                # Install the plugin (with dependencies)
                install_script = (
                    'd = Jenkins.instance.updateCenter.getPlugin("%s")'
                    '.deploy(); d.get();' % self.params['name'])

                if self.params['with_dependencies']:
                    install_script = (
                        'Jenkins.instance.updateCenter.getPlugin("%s")'
                        '.getNeededDependencies().each{it.deploy()}; %s' % (
                            self.params['name'], install_script))

                script_data = {
                    'script': install_script
                }
                script_data.update(self.crumb)
                data = urlencode(script_data)

                # Send the installation request
                r = self._get_url_data(
                    "%s/scriptText" % self.url,
                    msg_status="Cannot install plugin.",
                    msg_exception="Plugin installation has failed.",
                    data=data)

                hpi_file = '%s/plugins/%s.hpi' % (
                    self.params['jenkins_home'],
                    self.params['name'])

                if os.path.isfile(hpi_file):
                    os.remove(hpi_file)

            changed = True
        else:
            # Check if the plugin directory exists
            if not os.path.isdir(self.params['jenkins_home']):
                self.module.fail_json(
                    msg="Jenkins home directory doesn't exist.")

            md5sum_old = None
            if os.path.isfile(plugin_file):
                # Make the checksum of the currently installed plugin
                md5sum_old = hashlib.md5(
                    open(plugin_file, 'rb').read()).hexdigest()

            if self.params['version'] in [None, 'latest']:
                # Take latest version
                plugin_url = (
                    "%s/latest/%s.hpi" % (
                        self.params['updates_url'],
                        self.params['name']))
            else:
                # Take specific version
                plugin_url = (
                    "{0}/download/plugins/"
                    "{1}/{2}/{1}.hpi".format(
                        self.params['updates_url'],
                        self.params['name'],
                        self.params['version']))

            if (
                    self.params['updates_expiration'] == 0 or
                    self.params['version'] not in [None, 'latest'] or
                    md5sum_old is None):

                # Download the plugin file directly
                r = self._download_plugin(plugin_url)

                # Write downloaded plugin into file if checksums don't match
                if md5sum_old is None:
                    # No previously installed plugin
                    if not self.module.check_mode:
                        self._write_file(plugin_file, r)

                    changed = True
                else:
                    # Get data for the MD5
                    data = r.read()

                    # Make new checksum
                    md5sum_new = hashlib.md5(data).hexdigest()

                    # If the checksum is different from the currently installed
                    # plugin, store the new plugin
                    if md5sum_old != md5sum_new:
                        if not self.module.check_mode:
                            self._write_file(plugin_file, data)

                        changed = True
            else:
                # Check for update from the updates JSON file
                plugin_data = self._download_updates()

                try:
                    sha1_old = hashlib.sha1(open(plugin_file, 'rb').read())
                except Exception as e:
                    self.module.fail_json(
                        msg="Cannot calculate SHA1 of the old plugin.",
                        details=to_native(e))

                sha1sum_old = base64.b64encode(sha1_old.digest())

                # If the latest version changed, download it
                if sha1sum_old != to_bytes(plugin_data['sha1']):
                    if not self.module.check_mode:
                        r = self._download_plugin(plugin_url)
                        self._write_file(plugin_file, r)

                    changed = True

        # Change file attributes if needed
        if os.path.isfile(plugin_file):
            params = {
                'dest': plugin_file
            }
            params.update(self.params)
            file_args = self.module.load_file_common_arguments(params)

            if not self.module.check_mode:
                # Not sure how to run this in the check mode
                changed = self.module.set_fs_attributes_if_different(
                    file_args, changed)
            else:
                # See the comment above
                changed = True

        return changed

    def _download_updates(self):
        updates_filename = 'jenkins-plugin-cache.json'
        updates_dir = os.path.expanduser('~/.ansible/tmp')
        updates_file = "%s/%s" % (updates_dir, updates_filename)
        download_updates = True

        # Check if we need to download new updates file
        if os.path.isfile(updates_file):
            # Get timestamp when the file was changed last time
            ts_file = os.stat(updates_file).st_mtime
            ts_now = time.time()

            if ts_now - ts_file < self.params['updates_expiration']:
                download_updates = False

        updates_file_orig = updates_file

        # Download the updates file if needed
        if download_updates:
            url = "%s/update-center.json" % self.params['updates_url']

            # Get the data
            r = self._get_url_data(
                url,
                msg_status="Remote updates not found.",
                msg_exception="Updates download failed.")

            # Write the updates file
            update_fd, updates_file = tempfile.mkstemp()
            os.write(update_fd, r.read())

            try:
                os.close(update_fd)
            except IOError as e:
                self.module.fail_json(
                    msg="Cannot close the tmp updates file %s." % updates_file,
                    details=to_native(e))

        # Open the updates file
        try:
            f = open(updates_file)
        except IOError as e:
            self.module.fail_json(
                msg="Cannot open temporal updates file.",
                details=to_native(e))

        i = 0
        for line in f:
            # Read only the second line
            if i == 1:
                try:
                    data = json.loads(line)
                except Exception as e:
                    self.module.fail_json(
                        msg="Cannot load JSON data from the tmp updates file.",
                        details=to_native(e))

                break

            i += 1

        # Move the updates file to the right place if we could read it
        if download_updates:
            # Make sure the destination directory exists
            if not os.path.isdir(updates_dir):
                try:
                    os.makedirs(updates_dir, int('0700', 8))
                except OSError as e:
                    self.module.fail_json(
                        msg="Cannot create temporal directory.",
                        details=to_native(e))

            self.module.atomic_move(updates_file, updates_file_orig)

        # Check if we have the plugin data available
        if 'plugins' not in data or self.params['name'] not in data['plugins']:
            self.module.fail_json(
                msg="Cannot find plugin data in the updates file.")

        return data['plugins'][self.params['name']]

    def _download_plugin(self, plugin_url):
        # Download the plugin
        r = self._get_url_data(
            plugin_url,
            msg_status="Plugin not found.",
            msg_exception="Plugin download failed.")

        return r

    def _write_file(self, f, data):
        # Store the plugin into a temp file and then move it
        tmp_f_fd, tmp_f = tempfile.mkstemp()

        if isinstance(data, str):
            os.write(tmp_f_fd, data)
        else:
            os.write(tmp_f_fd, data.read())

        try:
            os.close(tmp_f_fd)
        except IOError as e:
            self.module.fail_json(
                msg='Cannot close the temporal plugin file %s.' % tmp_f,
                details=to_native(e))

        # Move the file onto the right place
        self.module.atomic_move(tmp_f, f)

    def uninstall(self):
        changed = False

        # Perform the action
        if self.is_installed:
            if not self.module.check_mode:
                self._pm_query('doUninstall', 'Uninstallation')

            changed = True

        return changed

    def pin(self):
        return self._pinning('pin')

    def unpin(self):
        return self._pinning('unpin')

    def _pinning(self, action):
        changed = False

        # Check if the plugin is pinned/unpinned
        if (
                action == 'pin' and not self.is_pinned or
                action == 'unpin' and self.is_pinned):

            # Perform the action
            if not self.module.check_mode:
                self._pm_query(action, "%sning" % action.capitalize())

            changed = True

        return changed

    def enable(self):
        return self._enabling('enable')

    def disable(self):
        return self._enabling('disable')

    def _enabling(self, action):
        changed = False

        # Check if the plugin is pinned/unpinned
        if (
                action == 'enable' and not self.is_enabled or
                action == 'disable' and self.is_enabled):

            # Perform the action
            if not self.module.check_mode:
                self._pm_query(
                    "make%sd" % action.capitalize(),
                    "%sing" % action[:-1].capitalize())

            changed = True

        return changed

    def _pm_query(self, action, msg):
        url = "%s/pluginManager/plugin/%s/%s" % (
            self.params['url'], self.params['name'], action)
        data = urlencode(self.crumb)

        # Send the request
        self._get_url_data(
            url,
            msg_status="Plugin not found. %s" % url,
            msg_exception="%s has failed." % msg,
            data=data)


def main():
    # Module arguments
    argument_spec = url_argument_spec()
    argument_spec.update(
        group=dict(default='jenkins'),
        jenkins_home=dict(default='/var/lib/jenkins'),
        mode=dict(default='0644', type='raw'),
        name=dict(required=True),
        owner=dict(default='jenkins'),
        params=dict(type='dict'),
        state=dict(
            choices=[
                'present',
                'absent',
                'pinned',
                'unpinned',
                'enabled',
                'disabled',
                'latest'],
            default='present'),
        timeout=dict(default=30, type="int"),
        updates_expiration=dict(default=86400, type="int"),
        updates_url=dict(default='https://updates.jenkins-ci.org'),
        url=dict(default='http://localhost:8080'),
        url_password=dict(no_log=True),
        version=dict(),
        with_dependencies=dict(default=True, type='bool'),
    )
    # Module settings
    module = AnsibleModule(
        argument_spec=argument_spec,
        add_file_common_args=True,
        supports_check_mode=True,
    )

    # Params was removed
    # https://meetbot.fedoraproject.org/ansible-meeting/2017-09-28/ansible_dev_meeting.2017-09-28-15.00.log.html
    if module.params['params']:
        module.fail_json(msg="The params option to jenkins_plugin was removed in Ansible 2.5"
                         "since it circumvents Ansible's option handling")

    # Force basic authentication
    module.params['force_basic_auth'] = True

    # Convert timeout to float
    try:
        module.params['timeout'] = float(module.params['timeout'])
    except ValueError as e:
        module.fail_json(
            msg='Cannot convert %s to float.' % module.params['timeout'],
            details=to_native(e))

    # Set version to latest if state is latest
    if module.params['state'] == 'latest':
        module.params['state'] = 'present'
        module.params['version'] = 'latest'

    # Create some shortcuts
    name = module.params['name']
    state = module.params['state']

    # Initial change state of the task
    changed = False

    # Instantiate the JenkinsPlugin object
    jp = JenkinsPlugin(module)

    # Perform action depending on the requested state
    if state == 'present':
        changed = jp.install()
    elif state == 'absent':
        changed = jp.uninstall()
    elif state == 'pinned':
        changed = jp.pin()
    elif state == 'unpinned':
        changed = jp.unpin()
    elif state == 'enabled':
        changed = jp.enable()
    elif state == 'disabled':
        changed = jp.disable()

    # Print status of the change
    module.exit_json(changed=changed, plugin=name, state=state)


if __name__ == '__main__':
    main()
