# Copyright (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    name: script
    version_added: "2.4"
    short_description: Executes an inventory script that returns JSON
    options:
      always_show_stderr:
        description: Toggle display of stderr even when script was successful
        version_added: "2.5.1"
        default: True
        type: boolean
        ini:
           - section: inventory_plugin_script
             key: always_show_stderr
        env:
           - name: ANSIBLE_INVENTORY_PLUGIN_SCRIPT_STDERR
    description:
        - The source provided must be an executable that returns Ansible inventory JSON
        - The source must accept C(--list) and C(--host <hostname>) as arguments.
          C(--host) will only be used if no C(_meta) key is present.
          This is a performance optimization as the script would be called one additional time per host otherwise.
    notes:
        - Enabled in configuration by default.
        - The plugin does not cache results because external inventory scripts are responsible for their own caching.
        - To write your own inventory script see (R(Developing dynamic inventory,developing_inventory) from the documentation site.
        - To find the scripts that used to be part of the code release, go to U(https://github.com/ansible-community/contrib-scripts/).
'''

EXAMPLES = r'''# fmt: code

### simple bash script

   #!/usr/bin/env bash

   if [ "$1" == "--list" ]; then
   cat<<EOF
   {
     "bash_hosts": {
       "hosts": [
         "myhost.domain.com",
         "myhost2.domain.com"
       ],
       "vars": {
         "host_test": "test-value"
       }
     },
     "_meta": {
       "hostvars": {
         "myhost.domain.com": {
           "host_specific_test_var": "test-value"
         }
       }
     }
   }
   EOF
   elif [ "$1" == "--host" ]; then
     # this should not normally be called by Ansible as we return _meta above
     if [ "$2" == "myhost.domain.com" ]; then
        echo '{"_meta": {hostvars": {"myhost.domain.com": {"host_specific-test_var": "test-value"}}}}'
     else
        echo '{"_meta": {hostvars": {}}}'
     fi
   else
     echo "Invalid option: use --list or --host <hostname>"
     exit 1
   fi


### python example with ini config

    #!/usr/bin/env python
    """
    # ansible_inventory.py
    """
    import argparse
    import json
    import os.path
    import sys
    from configparser import ConfigParser
    from inventories.custom import MyInventoryAPI

    def load_config() -> ConfigParser:
        cp = ConfigParser()
        config_file = os.path.expanduser("~/.config/ansible_inventory_script.cfg")
        cp.read(config_file)
        if not cp.has_option('DEFAULT', 'namespace'):
            raise ValueError("Missing configuration option: DEFAULT -> namespace")
        return cp


    def get_api_data(namespace: str, pretty=False) -> str:
        """
        :param namespace: parameter for our custom api
        :param pretty: Human redable JSON vs machine readable
        :return: JSON string
        """
        found_data = list(MyInventoryAPI(namespace))
        hostvars = {}
        data = { '_meta': { 'hostvars': {}},}

        groups = found_data['groups'].keys()
        for group in groups:
            groups[group]['hosts'] = found_data[groups].get('host_list', [])
            if group not in data:
                data[group] = {}
            data[group]['hosts'] = found_data[groups].get('host_list', [])
            data[group]['vars'] = found_data[groups].get('info', [])
            data[group]['children'] = found_data[group].get('subgroups', [])

        for host_data in found_data['hosts']:
            for name in host_data.items():
                # turn info into vars
                data['_meta'][name] = found_data[name].get('info', {})
                # set ansible_host if possible
                if 'address' in found_data[name]:
                    data[name]['_meta']['ansible_host'] = found_data[name]['address']
        data['_meta']['hostvars'] = hostvars

        return json.dumps(data, indent=pretty)

    if __name__ == '__main__':

        arg_parser = argparse.ArgumentParser( description=__doc__, prog=__file__)
        arg_parser.add_argument('--pretty', action='store_true', default=False, help="Pretty JSON")
        mandatory_options = arg_parser.add_mutually_exclusive_group()
        mandatory_options.add_argument('--list', action='store', nargs="*", help="Get inventory JSON from our API")
        mandatory_options.add_argument('--host', action='store',
                                       help="Get variables for specific host, not used but kept for compatibility")

        try:
            config = load_config()
            namespace = config.get('DEFAULT', 'namespace')

            args = arg_parser.parse_args()
            if args.host:
                print('{"_meta":{}}')
                sys.stderr.write('This script already provides _meta via --list, so this option is really ignored')
            elif len(args.list) >= 0:
                print(get_api_data(namespace, args.pretty))
            else:
                raise ValueError("Valid options are --list or --host <HOSTNAME>")

        except ValueError:
            raise

'''


import os
import subprocess

from collections.abc import Mapping

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.basic import json_dict_bytes_to_unicode
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.utils.display import Display

display = Display()


class InventoryModule(BaseInventoryPlugin):
    ''' Host inventory parser for ansible using external inventory scripts. '''

    NAME = 'script'

    def __init__(self):

        super(InventoryModule, self).__init__()

        self._hosts = set()

    def verify_file(self, path):
        ''' Verify if file is usable by this plugin, base does minimal accessibility check '''

        valid = super(InventoryModule, self).verify_file(path)

        if valid:
            # not only accessible, file must be executable and/or have shebang
            shebang_present = False
            try:
                with open(path, 'rb') as inv_file:
                    initial_chars = inv_file.read(2)
                    if initial_chars.startswith(b'#!'):
                        shebang_present = True
            except Exception:
                pass

            if not os.access(path, os.X_OK) and not shebang_present:
                valid = False

        return valid

    def parse(self, inventory, loader, path, cache=None):

        super(InventoryModule, self).parse(inventory, loader, path)
        self.set_options()

        # Support inventory scripts that are not prefixed with some
        # path information but happen to be in the current working
        # directory when '.' is not in PATH.
        cmd = [path, "--list"]

        try:
            try:
                sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                raise AnsibleParserError("problem running %s (%s)" % (' '.join(cmd), to_native(e)))
            (stdout, stderr) = sp.communicate()

            path = to_native(path)
            err = to_native(stderr or "")

            if err and not err.endswith('\n'):
                err += '\n'

            if sp.returncode != 0:
                raise AnsibleError("Inventory script (%s) had an execution error: %s " % (path, err))

            # make sure script output is unicode so that json loader will output unicode strings itself
            try:
                data = to_text(stdout, errors="strict")
            except Exception as e:
                raise AnsibleError("Inventory {0} contained characters that cannot be interpreted as UTF-8: {1}".format(path, to_native(e)))

            try:
                processed = self.loader.load(data, json_only=True)
            except Exception as e:
                raise AnsibleError("failed to parse executable inventory script results from {0}: {1}\n{2}".format(path, to_native(e), err))

            # if no other errors happened and you want to force displaying stderr, do so now
            if stderr and self.get_option('always_show_stderr'):
                self.display.error(msg=to_text(err))

            if not isinstance(processed, Mapping):
                raise AnsibleError("failed to parse executable inventory script results from {0}: needs to be a json dict\n{1}".format(path, err))

            group = None
            data_from_meta = None

            # A "_meta" subelement may contain a variable "hostvars" which contains a hash for each host
            # if this "hostvars" exists at all then do not call --host for each # host.
            # This is for efficiency and scripts should still return data
            # if called with --host for backwards compat with 1.2 and earlier.
            for (group, gdata) in processed.items():
                if group == '_meta':
                    if 'hostvars' in gdata:
                        data_from_meta = gdata['hostvars']
                else:
                    self._parse_group(group, gdata)

            for host in self._hosts:
                got = {}
                if data_from_meta is None:
                    got = self.get_host_variables(path, host)
                else:
                    try:
                        got = data_from_meta.get(host, {})
                    except AttributeError as e:
                        raise AnsibleError("Improperly formatted host information for %s: %s" % (host, to_native(e)), orig_exc=e)

                self._populate_host_vars([host], got)

        except Exception as e:
            raise AnsibleParserError(to_native(e))

    def _parse_group(self, group, data):

        group = self.inventory.add_group(group)

        if not isinstance(data, dict):
            data = {'hosts': data}
        # is not those subkeys, then simplified syntax, host with vars
        elif not any(k in data for k in ('hosts', 'vars', 'children')):
            data = {'hosts': [group], 'vars': data}

        if 'hosts' in data:
            if not isinstance(data['hosts'], list):
                raise AnsibleError("You defined a group '%s' with bad data for the host list:\n %s" % (group, data))

            for hostname in data['hosts']:
                self._hosts.add(hostname)
                self.inventory.add_host(hostname, group)

        if 'vars' in data:
            if not isinstance(data['vars'], dict):
                raise AnsibleError("You defined a group '%s' with bad data for variables:\n %s" % (group, data))

            for k, v in data['vars'].items():
                self.inventory.set_variable(group, k, v)

        if group != '_meta' and isinstance(data, dict) and 'children' in data:
            for child_name in data['children']:
                child_name = self.inventory.add_group(child_name)
                self.inventory.add_child(group, child_name)

    def get_host_variables(self, path, host):
        """ Runs <script> --host <hostname>, to determine additional host variables """

        cmd = [path, "--host", host]
        try:
            sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise AnsibleError("problem running %s (%s)" % (' '.join(cmd), e))
        (out, stderr) = sp.communicate()

        if sp.returncode != 0:
            raise AnsibleError("Inventory script (%s) had an execution error: %s" % (path, to_native(stderr)))

        if out.strip() == '':
            return {}
        try:
            return json_dict_bytes_to_unicode(self.loader.load(out, file_name=path))
        except ValueError:
            raise AnsibleError("could not parse post variable response: %s, %s" % (cmd, out))
