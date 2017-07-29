#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Mathew Davies <thepixeldeveloper@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: elasticsearch_plugin
short_description: Manage Elasticsearch plugins
description:
    - Manages Elasticsearch plugins.
version_added: "2.0"
author: Mathew Davies (@ThePixelDeveloper)
options:
    name:
        description:
            - Name of the plugin to install. In ES 2.x, the name can be an url or file location
        required: True
    state:
        description:
            - Desired state of a plugin.
        required: False
        choices: ["present", "absent"]
        default: present
    url:
        description:
            - Set exact URL to download the plugin from (Only works for ES 1.x)
        required: False
        default: None
    timeout:
        description:
            - "Timeout setting: 30s, 1m, 1h..."
        required: False
        default: 1m
    plugin_bin:
        description:
            - Location of the plugin binary
        required: False
        default: /usr/share/elasticsearch/bin/plugin
    plugin_dir:
        description:
            - Your configured plugin directory specified in Elasticsearch
        required: False
        default: /usr/share/elasticsearch/plugins/
    proxy_host:
        description:
            - Proxy host to use during plugin installation
        required: False
        default: None
        version_added: "2.1"
    proxy_port:
        description:
            - Proxy port to use during plugin installation
        required: False
        default: None
        version_added: "2.1"
    version:
        description:
            - Version of the plugin to be installed.
              If plugin exists with previous version, it will NOT be updated
        required: False
        default: None
'''

EXAMPLES = '''
# Install Elasticsearch head plugin
- elasticsearch_plugin:
    state: present
    name: mobz/elasticsearch-head

# Install specific version of a plugin
- elasticsearch_plugin:
    state: present
    name: com.github.kzwang/elasticsearch-image
    version: '1.2.0'

# Uninstall Elasticsearch head plugin
- elasticsearch_plugin:
    state: absent
    name: mobz/elasticsearch-head
'''

import os

from ansible.module_utils.basic import AnsibleModule


PACKAGE_STATE_MAP = dict(
    present="install",
    absent="remove"
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

def install_plugin(module, plugin_bin, plugin_name, version, url, proxy_host, proxy_port, timeout):
    cmd_args = [plugin_bin, PACKAGE_STATE_MAP["present"], plugin_name]

    if version:
        plugin_name = plugin_name + '/' + version

    if proxy_host and proxy_port:
        cmd_args.append("-DproxyHost=%s -DproxyPort=%s" % (proxy_host, proxy_port))

    if url:
        cmd_args.append("--url %s" % url)

    if timeout:
        cmd_args.append("--timeout %s" % timeout)

    cmd = " ".join(cmd_args)

    if module.check_mode:
        rc, out, err = 0, "check mode", ""
    else:
        rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    return True, cmd, out, err

def remove_plugin(module, plugin_bin, plugin_name):
    cmd_args = [plugin_bin, PACKAGE_STATE_MAP["absent"], parse_plugin_repo(plugin_name)]

    cmd = " ".join(cmd_args)

    if module.check_mode:
        rc, out, err = 0, "check mode", ""
    else:
        rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg=reason)

    return True, cmd, out, err

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            url=dict(default=None),
            timeout=dict(default="1m"),
            plugin_bin=dict(default="/usr/share/elasticsearch/bin/plugin", type="path"),
            plugin_dir=dict(default="/usr/share/elasticsearch/plugins/", type="path"),
            proxy_host=dict(default=None),
            proxy_port=dict(default=None),
            version=dict(default=None)
        ),
        supports_check_mode=True
    )

    name        = module.params["name"]
    state       = module.params["state"]
    url         = module.params["url"]
    timeout     = module.params["timeout"]
    plugin_bin  = module.params["plugin_bin"]
    plugin_dir  = module.params["plugin_dir"]
    proxy_host  = module.params["proxy_host"]
    proxy_port  = module.params["proxy_port"]
    version     = module.params["version"]

    present = is_plugin_present(parse_plugin_repo(name), plugin_dir)

    # skip if the state is correct
    if (present and state == "present") or (state == "absent" and not present):
        module.exit_json(changed=False, name=name, state=state)

    if state == "present":
        changed, cmd, out, err = install_plugin(module, plugin_bin, name, version, url, proxy_host, proxy_port, timeout)

    elif state == "absent":
        changed, cmd, out, err = remove_plugin(module, plugin_bin, name)

    module.exit_json(changed=changed, cmd=cmd, name=name, state=state, url=url, timeout=timeout, stdout=out, stderr=err)


if __name__ == '__main__':
    main()
