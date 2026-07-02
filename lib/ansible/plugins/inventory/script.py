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
        - Since 2.19 using a directory as an inventory source will no longer ignore .ini files by default,
          but you can still update the configuration to do so.
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
        :param pretty: Human readable JSON vs machine readable
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


import json
import os
import shlex
import subprocess
import typing as t

from ansible.errors import AnsibleError, AnsibleJSONParserError
from ansible.inventory.data import InventoryData
from ansible.module_utils.datatag import native_type_name
from ansible.module_utils.common.json import get_decoder
from ansible.parsing.dataloader import DataLoader
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible._internal._datatag._tags import TrustedAsTemplate, Origin
from ansible.utils.display import Display
from ansible._internal._json._profiles import _legacy, _inventory_legacy

display = Display()


class InventoryModule(BaseInventoryPlugin):
    """Host inventory parser for ansible using external inventory scripts."""

    NAME = 'script'

    def __init__(self) -> None:
        super(InventoryModule, self).__init__()

        self._hosts: set[str] = set()

    def verify_file(self, path: str) -> bool:
        return super(InventoryModule, self).verify_file(path) and os.access(path, os.X_OK)

    def parse(self, inventory: InventoryData, loader: DataLoader, path: str, cache: bool = False) -> None:
        super(InventoryModule, self).parse(inventory, loader, path)

        self.set_options()

        origin = Origin(description=f'<inventory script output from {path!r}>')

        data, stderr, stderr_help_text = run_command(path, ['--list'], origin)

        try:
            profile_name = detect_profile_name(data)
            decoder = get_decoder(profile_name)
        except Exception as ex:
            raise AnsibleError(
                message="Unable to get JSON decoder for inventory script result.",
                help_text=stderr_help_text,
                # obj will be added by inventory manager
            ) from ex

        try:
            try:
                processed = json.loads(data, cls=decoder)
            except Exception as json_ex:
                AnsibleJSONParserError.handle_exception(json_ex, origin)
        except Exception as ex:
            raise AnsibleError(
                message="Inventory script result could not be parsed as JSON.",
                help_text=stderr_help_text,
                # obj will be added by inventory manager
            ) from ex

        # if no other errors happened, and you want to force displaying stderr, do so now
        if stderr and self.get_option('always_show_stderr'):
            self.display.error(msg=stderr)

        data_from_meta: dict | None = None

        # A "_meta" subelement may contain a variable "hostvars" which contains a hash for each host
        # if this "hostvars" exists at all then do not call --host for each # host.
        # This is for efficiency and scripts should still return data
        # if called with --host for backwards compat with 1.2 and earlier.
        for (group, gdata) in processed.items():
            if group == '_meta':
                data_from_meta = gdata.get('hostvars')

                if not isinstance(data_from_meta, dict):
                    raise TypeError(f"Value contains '_meta.hostvars' which is {native_type_name(data_from_meta)!r} instead of {native_type_name(dict)!r}.")
            else:
                self._parse_group(group, gdata, origin)

        if data_from_meta is None:
            display.deprecated(
                msg="Inventory scripts should always provide 'meta.hostvars'. "
                    "Host variables will be collected by running the inventory script with the '--host' option for each host.",
                version='2.23',
                obj=origin,
            )

        for host in self._hosts:
            if data_from_meta is None:
                got = self.get_host_variables(path, host, origin)
            else:
                got = data_from_meta.get(host, {})

            self._populate_host_vars([host], got)

    def _parse_group(self, group: str, data: t.Any, origin: Origin) -> None:
        """Normalize and ingest host/var information for the named group."""
        group = self.inventory.add_group(group)

        if not isinstance(data, dict):
            original_type = native_type_name(data)
            data = {'hosts': data}
            display.deprecated(
                msg=f"Group {group!r} was converted to {native_type_name(dict)!r} from {original_type!r}.",
                version='2.23',
                obj=origin,
            )
        elif not any(k in data for k in ('hosts', 'vars', 'children')):
            data = {'hosts': [group], 'vars': data}
            display.deprecated(
                msg=f"Treating malformed group {group!r} as the sole host of that group. Variables provided in this manner cannot be templated.",
                version='2.23',
                obj=origin,
            )

        if (data_hosts := data.get('hosts', ...)) is not ...:
            if not isinstance(data_hosts, list):
                raise TypeError(f"Value contains '{group}.hosts' which is {native_type_name(data_hosts)!r} instead of {native_type_name(list)!r}.")

            for hostname in data_hosts:
                self._hosts.add(hostname)
                self.inventory.add_host(hostname, group)

        if (data_vars := data.get('vars', ...)) is not ...:
            if not isinstance(data_vars, dict):
                raise TypeError(f"Value contains '{group}.vars' which is {native_type_name(data_vars)!r} instead of {native_type_name(dict)!r}.")

            for k, v in data_vars.items():
                self.inventory.set_variable(group, k, v)

        if group != '_meta' and isinstance(data, dict) and 'children' in data:
            for child_name in data['children']:
                child_name = self.inventory.add_group(child_name)
                self.inventory.add_child(group, child_name)

    @staticmethod
    def get_host_variables(path: str, host: str, origin: Origin) -> dict:
        """Runs <script> --host <hostname>, to determine additional host variables."""
        origin = origin.replace(description=f'{origin.description} for host {host!r}')

        data, stderr, stderr_help_text = run_command(path, ['--host', host], origin)

        if not data.strip():
            return {}

        try:
            try:
                # Use standard legacy trust inversion here.
                # Unlike the normal inventory output, everything here is considered a variable and thus supports trust (and trust inversion).
                processed = json.loads(data, cls=_legacy.Decoder)
            except Exception as json_ex:
                AnsibleJSONParserError.handle_exception(json_ex, origin)
        except Exception as ex:
            raise AnsibleError(
                message=f"Inventory script result for host {host!r} could not be parsed as JSON.",
                help_text=stderr_help_text,
                # obj will be added by inventory manager
            ) from ex

        return processed


def detect_profile_name(value: str) -> str:
    """
    Detect (optional) JSON profile name from an inventory JSON document.
    Defaults to `inventory_legacy`.
    """
    try:
        data = json.loads(value)
    except Exception as ex:
        raise ValueError('Value could not be parsed as JSON.') from ex

    if not isinstance(data, dict):
        raise TypeError(f'Value is {native_type_name(data)!r} instead of {native_type_name(dict)!r}.')

    if (meta := data.get('_meta', ...)) is ...:
        return _inventory_legacy.Decoder.profile_name

    if not isinstance(meta, dict):
        raise TypeError(f"Value contains '_meta' which is {native_type_name(meta)!r} instead of {native_type_name(dict)!r}.")

    if (profile := meta.get('profile', ...)) is ...:
        return _inventory_legacy.Decoder.profile_name

    if not isinstance(profile, str):
        raise TypeError(f"Value contains '_meta.profile' which is {native_type_name(profile)!r} instead of {native_type_name(str)!r}.")

    if not profile.startswith('inventory_'):
        raise ValueError(f"Non-inventory profile {profile!r} is not allowed.")

    return profile


def run_command(path: str, options: list[str], origin: Origin) -> tuple[str, str, str]:
    """Run an inventory script, normalize and validate output."""
    cmd = [path] + options

    try:
        sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as ex:
        raise AnsibleError(
            message=f"Failed to execute inventory script command {shlex.join(cmd)!r}.",
            # obj will be added by inventory manager
        ) from ex

    stdout_bytes, stderr_bytes = sp.communicate()

    stderr = stderr_bytes.decode(errors='surrogateescape')

    if stderr and not stderr.endswith('\n'):
        stderr += '\n'

    # DTFIX-FUTURE: another use case for the "not quite help text, definitely not message" diagnostic output on errors
    stderr_help_text = f'Standard error from inventory script:\n{stderr}' if stderr.strip() else None

    if sp.returncode != 0:
        raise AnsibleError(
            message=f"Inventory script returned non-zero exit code {sp.returncode}.",
            help_text=stderr_help_text,
            # obj will be added by inventory manager
        )

    try:
        data = stdout_bytes.decode()
    except Exception as ex:
        raise AnsibleError(
            "Inventory script result contained characters that cannot be interpreted as UTF-8.",
            help_text=stderr_help_text,
            # obj will be added by inventory manager
        ) from ex
    else:
        data = TrustedAsTemplate().tag(origin.tag(data))

    return data, stderr, stderr_help_text
