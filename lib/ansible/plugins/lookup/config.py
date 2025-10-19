# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: config
    author: Ansible Core Team
    version_added: "2.5"
    short_description: Display the 'resolved' Ansible option values.
    description:
      - Retrieves the value of an Ansible configuration setting, resolving all sources, from defaults, ansible.cfg, environment,
        CLI, and variables, but not keywords.
      - The values returned assume the context of the current host or C(inventory_hostname).
      - You can use C(ansible-config list) to see the global available settings, add C(-t all) to also show plugin options.
    options:
      _terms:
        description: The option(s) to look up.
        required: True
      on_missing:
        description: Action to take if term is missing from config
        default: error
        type: string
        choices:
            error: Issue an error message and raise fatal signal
            warn:  Issue a warning message and continue
            skip:  Silently ignore
      plugin_type:
        description: The type of the plugin referenced by 'plugin_name' option.
        choices: ['become', 'cache', 'callback', 'cliconf', 'connection', 'httpapi', 'inventory', 'lookup', 'netconf', 'shell', 'vars']
        type: string
        version_added: '2.12'
      plugin_name:
        description: The name of the plugin for which you want to retrieve configuration settings.
        type: string
        version_added: '2.12'
      show_origin:
        description: Set this to return what configuration subsystem the value came from
                     (defaults, config file, environment, CLI, or variables).
        type: bool
        version_added: '2.16'
    notes:
      - Be aware that currently this lookup cannot take keywords nor delegation into account,
        so for options that support keywords or are affected by delegation, it is at best a good guess or approximation.
"""

EXAMPLES = """
    - name: Show configured default become user
      ansible.builtin.debug: msg="{{ lookup('ansible.builtin.config', 'DEFAULT_BECOME_USER')}}"

    - name: print out role paths
      ansible.builtin.debug:
        msg: "These are the configured role paths: {{lookup('ansible.builtin.config', 'DEFAULT_ROLES_PATH')}}"

    - name: find retry files, skip if missing that key
      ansible.builtin.find:
        paths: "{{lookup('ansible.builtin.config', 'RETRY_FILES_SAVE_PATH')|default(playbook_dir, True)}}"
        patterns: "*.retry"

    - name: see the colors
      ansible.builtin.debug: msg="{{item}}"
      loop: "{{lookup('ansible.builtin.config', 'COLOR_OK', 'COLOR_CHANGED', 'COLOR_SKIP', wantlist=True)}}"

    - name: skip if bad value in var
      ansible.builtin.debug: msg="{{ lookup('ansible.builtin.config', config_in_var, on_missing='skip')}}"
      var:
        config_in_var: UNKNOWN

    - name: show remote user and port for ssh connection
      ansible.builtin.debug: msg={{q("ansible.builtin.config", "remote_user", "port", plugin_type="connection", plugin_name="ssh", on_missing='skip')}}

    - name: show remote_tmp setting for shell (sh) plugin
      ansible.builtin.debug: msg={{q("ansible.builtin.config", "remote_tmp", plugin_type="shell", plugin_name="sh")}}
"""

RETURN = """
_raw:
  description:
    - A list of value(s) of the key(s) in the config if show_origin is false (default)
    - Optionally, a list of 2 element lists (value, origin) if show_origin is true
  type: raw
"""

import ansible.plugins.loader as plugin_loader

from ansible import constants as C
from ansible.module_utils.common.sentinel import Sentinel
from ansible.errors import AnsibleError, AnsibleUndefinedConfigEntry
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        missing = self.get_option('on_missing')
        ptype = self.get_option('plugin_type')
        pname = self.get_option('plugin_name')
        show_origin = self.get_option('show_origin')

        if (ptype or pname) and not (ptype and pname):
            raise AnsibleError('Both plugin_type and plugin_name are required, cannot use one without the other.')

        ret = []

        for term in terms:
            if not isinstance(term, str):
                raise AnsibleError(f'Invalid setting identifier, {term!r} is not a {str}, its a {type(term)}.')

            result = Sentinel
            origin = None

            # plugin creates settings on load, we ensure that happens here
            if pname:
                # this is cached so not too expensive
                loader = getattr(plugin_loader, f'{ptype}_loader')
                p = loader.get(pname, class_only=True)
                if p is None:
                    raise AnsibleError(f"Unable to load {ptype} plugin {pname!r}.")
            try:
                result, origin = C.config.get_config_value_and_origin(term, plugin_type=ptype, plugin_name=pname, variables=variables)
            except AnsibleUndefinedConfigEntry as e:
                match missing:
                    case 'error':
                        raise
                    case 'skip':
                        pass
                    case 'warn':
                        self._display.error_as_warning(msg=f"Skipping {term}.", exception=e)
                    case _:
                        raise AnsibleError(f"Invalid option for error handling, missing must be error, warn or skip, got: {missing}.") from e

            if result is not Sentinel:
                if show_origin:
                    ret.append([result, origin])
                else:
                    ret.append(result)
        return ret
