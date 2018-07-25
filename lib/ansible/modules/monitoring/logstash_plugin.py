#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Loic Blot <loic.blot@unix-experience.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: logstash_plugin
short_description: Manage Logstash plugins
description:
    - Manages Logstash plugins.
version_added: "2.3"
author: Loic Blot (@nerzhul)
options:
    name:
        description:
            - Install plugin with that name.
        required: True
    state:
        description:
            - Apply plugin state.
        choices: ["present", "absent"]
        default: present
    plugin_bin:
        description:
            - Specify logstash-plugin to use for plugin management.
        default: /usr/share/logstash/bin/logstash-plugin
    proxy_host:
        description:
            - Proxy host to use during plugin installation.
    proxy_port:
        description:
            - Proxy port to use during plugin installation.
    version:
        description:
            - Specify plugin Version of the plugin to install.
              If plugin exists with previous version, it will NOT be updated.
'''

EXAMPLES = '''
- name: Install Logstash beats input plugin
  logstash_plugin:
    state: present
    name: logstash-input-beats

- name: Install specific version of a plugin
  logstash_plugin:
    state: present
    name: logstash-input-syslog
    version: '3.2.0'

- name: Uninstall Logstash plugin
  logstash_plugin:
    state: absent
    name: logstash-filter-multiline
'''

from ansible.module_utils.basic import AnsibleModule


PACKAGE_STATE_MAP = dict(
    present="install",
    absent="remove"
)


def is_plugin_present(module, plugin_bin, plugin_name):
    cmd_args = [plugin_bin, "list", plugin_name]
    rc, out, err = module.run_command(" ".join(cmd_args))
    return rc == 0


def parse_error(string):
    reason = "reason: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string


def install_plugin(module, plugin_bin, plugin_name, version, proxy_host, proxy_port):
    cmd_args = [plugin_bin, PACKAGE_STATE_MAP["present"], plugin_name]

    if version:
        cmd_args.append("--version %s" % version)

    if proxy_host and proxy_port:
        cmd_args.append("-DproxyHost=%s -DproxyPort=%s" % (proxy_host, proxy_port))

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
    cmd_args = [plugin_bin, PACKAGE_STATE_MAP["absent"], plugin_name]

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
            plugin_bin=dict(default="/usr/share/logstash/bin/logstash-plugin", type="path"),
            proxy_host=dict(default=None),
            proxy_port=dict(default=None),
            version=dict(default=None)
        ),
        supports_check_mode=True
    )

    name = module.params["name"]
    state = module.params["state"]
    plugin_bin = module.params["plugin_bin"]
    proxy_host = module.params["proxy_host"]
    proxy_port = module.params["proxy_port"]
    version = module.params["version"]

    present = is_plugin_present(module, plugin_bin, name)

    # skip if the state is correct
    if (present and state == "present") or (state == "absent" and not present):
        module.exit_json(changed=False, name=name, state=state)

    if state == "present":
        changed, cmd, out, err = install_plugin(module, plugin_bin, name, version, proxy_host, proxy_port)
    elif state == "absent":
        changed, cmd, out, err = remove_plugin(module, plugin_bin, name)

    module.exit_json(changed=changed, cmd=cmd, name=name, state=state, stdout=out, stderr=err)


if __name__ == '__main__':
    main()
