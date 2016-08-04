#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to manage elasticsearch shield role
(c) 2016, Thierno IB. BARRY @barryib
Sponsored by Polyconseil http://polyconseil.fr.

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

import os

DOCUMENTATION = '''
---
module: kibana_plugin
short_description: Manage Kibana plugins
description:
    - Manages Kibana plugins.
version_added: "2.2"
author: Thierno IB. BARRY (@barryib)
options:
    name:
        description:
            - Name of the plugin to install
        required: True
    state:
        description:
            - Desired state of a plugin.
        required: False
        choices: ["present", "absent"]
        default: present
    url:
        description:
            - Set exact URL to download the plugin from.
              For local file, prefix its absolute path with file:// 
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
        default: /opt/kibana/bin/kibana
    plugin_dir:
        description:
            - Your configured plugin directory specified in Kibana
        required: False
        default: /opt/kibana/installedPlugins/
    version:
        description:
            - Version of the plugin to be installed.
              If plugin exists with previous version, it will NOT be updated if C(force) is not set to yes
        required: False
        default: None
    force:
        description:
            - Delete and re-install the plugin. Can be useful for plugins update
        required: False
        choices: ["yes", "no"]
        default: no
'''

EXAMPLES = '''
# Install Elasticsearch head plugin
- kibana_plugin: state=present name="elasticsearch/marvel"

# Install specific version of a plugin
- kibana_plugin: state=present name="elasticsearch/marvel" version="2.3.3"

# Uninstall Elasticsearch head plugin
- kibana_plugin: state=absent name="elasticsearch/marvel"
'''

RETURN = '''
cmd:
    description: the launched command during plugin mangement (install / remove)
    returned: success
    type: string
name:
    description: the plugin name to install or remove
    returned: success
    type: string
url:
    description: the url from where the plugin is installed from
    returned: success
    type: string
timeout:
    description: the timout for plugin download
    returned: success
    type: string
stdout:
    description: the command stdout
    returned: success
    type: string
stderr:
    description: the command stderr
    returned: success
    type: string
state:
    description: the state for the managed plugin
    returned: success
    type: string
'''

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

def install_plugin(module, plugin_bin, plugin_name, url, timeout):
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

def remove_plugin(module, plugin_bin, plugin_name):
    cmd_args = [plugin_bin, "plugin", PACKAGE_STATE_MAP["absent"], plugin_name]

    cmd = " ".join(cmd_args)

    if module.check_mode:
        return True, cmd, "check mode", ""
        
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
            plugin_bin=dict(default="/opt/kibana/bin/kibana", type="path"),
            plugin_dir=dict(default="/opt/kibana/installedPlugins/", type="path"),
            version=dict(default=None),
            force=dict(default="no", type="bool")
        ),
        supports_check_mode=True,
    )

    name        = module.params["name"]
    state       = module.params["state"]
    url         = module.params["url"]
    timeout     = module.params["timeout"]
    plugin_bin  = module.params["plugin_bin"]
    plugin_dir  = module.params["plugin_dir"]
    version     = module.params["version"]
    force       = module.params["force"]

    present = is_plugin_present(parse_plugin_repo(name), plugin_dir)

    # skip if the state is correct
    if (present and state == "present" and not force) or (state == "absent" and not present and not force):
        module.exit_json(changed=False, name=name, state=state)

    if (version):
        name = name + '/' + version

    if state == "present":
        if force:
            remove_plugin(module, plugin_bin, name)
        changed, cmd, out, err = install_plugin(module, plugin_bin, name, url, timeout)

    elif state == "absent":
        changed, cmd, out, err = remove_plugin(module, plugin_bin, name)

    module.exit_json(changed=changed, cmd=cmd, name=name, state=state, url=url, timeout=timeout, stdout=out, stderr=err)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
