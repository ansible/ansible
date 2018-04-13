#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2015, Mathew Davies <thepixeldeveloper@googlemail.com>
# (c) 2017, Sam Doran <sdoran@redhat.com>
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
module: elasticsearch_plugin
short_description: Manage Elasticsearch plugins
description:
    - Manages Elasticsearch plugins.
version_added: "2.0"
author:
    - Mathew Davies (@ThePixelDeveloper)
    - Sam Doran (@samdoran)
options:
    name:
        description:
            - Name of the plugin to install. In Eleasticsearch >= 2.0, the name can be an URL or file location.
        required: True
    state:
        description:
            - Desired state of a plugin.
        choices: ["present", "absent"]
        default: present
    url:
        description:
            - Set exact URL to download the plugin from (Only works for ES 1.x)
    timeout:
        description:
            - "Timeout setting: 30s, 1m, 1h..."
            - Only valid for Elasticsearch < 5.0. This option is ignored for Elasticsearch > 5.0.
        default: 1m
    plugin_bin:
        description:
            - Location of the plugin binary. If this file is not found, the default plugin binaries will be used.
            - The default changed in Ansible 2.4 to None.
    plugin_dir:
        description:
            - Your configured plugin directory specified in Elasticsearch
        default: /usr/share/elasticsearch/plugins/
    proxy_host:
        description:
            - Proxy host to use during plugin installation
        version_added: "2.1"
    proxy_port:
        description:
            - Proxy port to use during plugin installation
        version_added: "2.1"
    version:
        description:
            - Version of the plugin to be installed.
              If plugin exists with previous version, it will NOT be updated
'''

EXAMPLES = '''
# Install Elasticsearch Head plugin in Elasticsearch 2.x
- elasticsearch_plugin:
    name: mobz/elasticsearch-head
    state: present

# Install a specific version of Elasticsearch Head in Elasticsearch 2.x
- elasticsearch_plugin:
    name: mobz/elasticsearch-head
    version: 2.0.0

# Uninstall Elasticsearch head plugin in Elasticsearch 2.x
- elasticsearch_plugin:
    name: mobz/elasticsearch-head
    state: absent

# Install a specific plugin in Elasticsearch >= 5.0
- elasticsearch_plugin:
    name: analysis-icu
    state: present
'''

import os

from ansible.module_utils.basic import AnsibleModule


PACKAGE_STATE_MAP = dict(
    present="install",
    absent="remove"
)

PLUGIN_BIN_PATHS = tuple([
    '/usr/share/elasticsearch/bin/elasticsearch-plugin',
    '/usr/share/elasticsearch/bin/plugin'
])


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
    reason = "ERROR: "
    try:
        return string[string.index(reason) + len(reason):].strip()
    except ValueError:
        return string


def install_plugin(module, plugin_bin, plugin_name, version, url, proxy_host, proxy_port, timeout):
    cmd_args = [plugin_bin, PACKAGE_STATE_MAP["present"], plugin_name]

    # Timeout and version are only valid for plugin, not elasticsearch-plugin
    if os.path.basename(plugin_bin) == 'plugin':
        if timeout:
            cmd_args.append("--timeout %s" % timeout)

        if version:
            plugin_name = plugin_name + '/' + version
            cmd_args[2] = plugin_name

    if proxy_host and proxy_port:
        cmd_args.append("-DproxyHost=%s -DproxyPort=%s" % (proxy_host, proxy_port))

    if url:
        cmd_args.append("--url %s" % url)

    cmd = " ".join(cmd_args)

    if module.check_mode:
        rc, out, err = 0, "check mode", ""
    else:
        rc, out, err = module.run_command(cmd)

    if rc != 0:
        reason = parse_error(out)
        module.fail_json(msg='Is %s a valid plugin name?' % plugin_name, err=reason)

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


def get_plugin_bin(module, plugin_bin=None):
    # Use the plugin_bin that was supplied first before trying other options
    valid_plugin_bin = None
    if plugin_bin and os.path.isfile(plugin_bin):
        valid_plugin_bin = plugin_bin

    else:
        # Add the plugin_bin passed into the module to the top of the list of paths to test,
        # testing for that binary name first before falling back to the default paths.
        bin_paths = list(PLUGIN_BIN_PATHS)
        if plugin_bin and plugin_bin not in bin_paths:
            bin_paths.insert(0, plugin_bin)

        # Get separate lists of dirs and binary names from the full paths to the
        # plugin binaries.
        plugin_dirs = list(set([os.path.dirname(x) for x in bin_paths]))
        plugin_bins = list(set([os.path.basename(x) for x in bin_paths]))

        # Check for the binary names in the default system paths as well as the path
        # specified in the module arguments.
        for bin_file in plugin_bins:
            valid_plugin_bin = module.get_bin_path(bin_file, opt_dirs=plugin_dirs)
            if valid_plugin_bin:
                break

    if not valid_plugin_bin:
        module.fail_json(msg='%s does not exist and no other valid plugin installers were found. Make sure Elasticsearch is installed.' % plugin_bin)

    return valid_plugin_bin


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(default="present", choices=PACKAGE_STATE_MAP.keys()),
            url=dict(default=None),
            timeout=dict(default="1m"),
            plugin_bin=dict(type="path"),
            plugin_dir=dict(default="/usr/share/elasticsearch/plugins/", type="path"),
            proxy_host=dict(default=None),
            proxy_port=dict(default=None),
            version=dict(default=None)
        ),
        supports_check_mode=True
    )

    name = module.params["name"]
    state = module.params["state"]
    url = module.params["url"]
    timeout = module.params["timeout"]
    plugin_bin = module.params["plugin_bin"]
    plugin_dir = module.params["plugin_dir"]
    proxy_host = module.params["proxy_host"]
    proxy_port = module.params["proxy_port"]
    version = module.params["version"]

    # Search provided path and system paths for valid binary
    plugin_bin = get_plugin_bin(module, plugin_bin)

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
