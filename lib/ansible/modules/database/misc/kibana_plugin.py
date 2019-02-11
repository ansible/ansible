#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2016, Thierno IB. BARRY @barryib
# Sponsored by Polyconseil http://polyconseil.fr.
#
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
module: kibana_plugin
short_description: Manage Kibana plugins
description:
    - This module can be used to manage Kibana plugins.
version_added: "2.2"
author: Thierno IB. BARRY (@barryib)
options:
    name:
      description:
      - Name of the plugin to install.
      required: True
    state:
      description:
      - Desired state of a plugin.
      choices: ["present", "absent"]
      default: present
    url:
      description:
      - Set exact URL to download the plugin from.
      - For local file, prefix its absolute path with file://
    timeout:
      description:
      - "Timeout setting: 30s, 1m, 1h etc."
      default: 1m
    plugin_bin:
      description:
      - Location of the Kibana binary.
      default: /opt/kibana/bin/kibana
    plugin_dir:
      description:
      - Your configured plugin directory specified in Kibana.
      default: /opt/kibana/installedPlugins/
    version:
      description:
      - Version of the plugin to be installed.
      - If plugin exists with previous version, plugin will NOT be updated unless C(force) is set to yes.
    force:
      description:
      - Delete and re-install the plugin. Can be useful for plugins update.
      type: bool
      default: 'no'
'''

EXAMPLES = '''
- name: Install Elasticsearch head plugin
  kibana_plugin:
    state: present
    name: elasticsearch/marvel

- name: Install specific version of a plugin
  kibana_plugin:
    state: present
    name: elasticsearch/marvel
    version: '2.3.3'

- name: Uninstall Elasticsearch head plugin
  kibana_plugin:
    state: absent
    name: elasticsearch/marvel
'''

RETURN = '''
cmd:
    description: the launched command during plugin management (install / remove)
    returned: success
    type: str
name:
    description: the plugin name to install or remove
    returned: success
    type: str
url:
    description: the url from where the plugin is installed from
    returned: success
    type: str
timeout:
    description: the timeout for plugin download
    returned: success
    type: str
stdout:
    description: the command stdout
    returned: success
    type: str
stderr:
    description: the command stderr
    returned: success
    type: str
state:
    description: the state for the managed plugin
    returned: success
    type: str
'''

import os
from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule


PACKAGE_STATE_MAP = dict(
    present="--install",
    absent="--remove"
)


def parse_plugin_repo(string):
    elements = string.split("/")

    # We first consider the simplest form: pluginname
    repo = elements[0]

    # We consider the form: username/pluginname
    if len(elements) > 1:
        repo = elements[1]

    # remove elasticsearch- prefix
    # remove es- prefix
    for string in ("elasticsearch-", "es-"):
        if repo.startswith(string):
            return repo[len(string):]

    return repo


def is_plugin_present(plugin_dir, working_dir):
    return os.path.isdir(os.path.join(working_dir, plugin_dir))


def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string


def install_plugin(module, plugin_bin, plugin_name, url, timeout, kibana_version='4.6'):
    if LooseVersion(kibana_version) > LooseVersion('4.6'):
        kibana_plugin_bin = os.path.join(os.path.dirname(plugin_bin), 'kibana-plugin')
        cmd_args = [kibana_plugin_bin, "install"]
        if url:
            cmd_args.append(url)
        else:
            cmd_args.append(plugin_name)
    else:
        cmd_args = [plugin_bin, "plugin", PACKAGE_STATE_MAP["present"], plugin_name]

        if url:
            cmd_args.append("--url %s" % url)

    if timeout:
        cmd_args.append("--timeout %s" % timeout)

    cmd = " ".join(cmd_args)

    if module.check_mode:
        return True, cmd, "check mode", ""

    rc, out, err = module.run_command(cmd)
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    return True, cmd, out, err


def remove_plugin(module, plugin_bin, plugin_name, kibana_version='4.6'):
    if LooseVersion(kibana_version) > LooseVersion('4.6'):
        kibana_plugin_bin = os.path.join(os.path.dirname(plugin_bin), 'kibana-plugin')
        cmd_args = [kibana_plugin_bin, "remove", plugin_name]
    else:
        cmd_args = [plugin_bin, "plugin", PACKAGE_STATE_MAP["absent"], plugin_name]

    cmd = " ".join(cmd_args)

    if module.check_mode:
        return True, cmd, "check mode", ""

    rc, out, err = module.run_command(cmd)
    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    return True, cmd, out, err


def get_kibana_version(module, plugin_bin):
    cmd_args = [plugin_bin, '--version']
    cmd = " ".join(cmd_args)
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg="Failed to get Kibana version : %s" % err)

    return out.strip()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            url=dict(default=None),
            timeout=dict(default="1m"),
            plugin_bin=dict(default="/opt/kibana/bin/kibana", type="path"),
            plugin_dir=dict(default="/opt/kibana/installedPlugins/", type="path"),
            version=dict(default=None),
            force=dict(default="no", type="bool")
        ),
        supports_check_mode=True,
    )

    name = module.params["name"]
    state = module.params["state"]
    url = module.params["url"]
    timeout = module.params["timeout"]
    plugin_bin = module.params["plugin_bin"]
    plugin_dir = module.params["plugin_dir"]
    version = module.params["version"]
    force = module.params["force"]

    changed, cmd, out, err = False, '', '', ''

    kibana_version = get_kibana_version(module, plugin_bin)

    present = is_plugin_present(parse_plugin_repo(name), plugin_dir)

    # skip if the state is correct
    if (present and state == "present" and not force) or (state == "absent" and not present and not force):
        module.exit_json(changed=False, name=name, state=state)

    if version:
        name = name + '/' + version

    if state == "present":
        if force:
            remove_plugin(module, plugin_bin, name)
        changed, cmd, out, err = install_plugin(module, plugin_bin, name, url, timeout, kibana_version)

    elif state == "absent":
        changed, cmd, out, err = remove_plugin(module, plugin_bin, name, kibana_version)

    module.exit_json(changed=changed, cmd=cmd, name=name, state=state, url=url, timeout=timeout, stdout=out, stderr=err)


if __name__ == '__main__':
    main()
