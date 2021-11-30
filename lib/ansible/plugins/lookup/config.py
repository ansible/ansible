# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: config
    author: Ansible Core Team
    version_added: "2.5"
    short_description: Lookup current Ansible configuration values
    description:
      - Retrieves the value of an Ansible configuration setting.
      - You can use C(ansible-config list) to see all available settings.
    options:
      _terms:
        description: The key(s) to look up
        required: True
      on_missing:
        description:
            - action to take if term is missing from config
            - Error will raise a fatal error
            - Skip will just ignore the term
            - Warn will skip over it but issue a warning
        default: error
        type: string
        choices: ['error', 'skip', 'warn']
      plugin_type:
        description: the type of the plugin referenced by 'plugin_name' option.
        choices: ['become', 'cache', 'callback', 'cliconf', 'connection', 'httpapi', 'inventory', 'lookup', 'netconf', 'shell', 'vars']
        type: string
        version_added: '2.12'
      plugin_name:
        description: name of the plugin for which you want to retrieve configuration settings.
        type: string
        version_added: '2.12'
"""

EXAMPLES = """
    - name: Show configured default become user
      debug: msg="{{ lookup('config', 'DEFAULT_BECOME_USER')}}"

    - name: print out role paths
      debug:
        msg: "These are the configured role paths: {{lookup('config', 'DEFAULT_ROLES_PATH')}}"

    - name: find retry files, skip if missing that key
      find:
        paths: "{{lookup('config', 'RETRY_FILES_SAVE_PATH')|default(playbook_dir, True)}}"
        patterns: "*.retry"

    - name: see the colors
      debug: msg="{{item}}"
      loop: "{{lookup('config', 'COLOR_OK', 'COLOR_CHANGED', 'COLOR_SKIP', wantlist=True)}}"

    - name: skip if bad value in var
      debug: msg="{{ lookup('config', config_in_var, on_missing='skip')}}"
      var:
        config_in_var: UNKNOWN

    - name: show remote user and port for ssh connection
      debug: msg={{q("config", "remote_user", "port", plugin_type="connection", plugin_name="ssh", on_missing='skip')}}

    - name: show remote_tmp setting for shell (sh) plugin
      debug: msg={{q("config", "remote_tmp", plugin_type="shell", plugin_name="sh")}}
"""

RETURN = """
_raw:
  description:
    - value(s) of the key(s) in the config
  type: raw
"""

import ansible.plugins.loader as plugin_loader

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleLookupError, AnsibleOptionsError
from ansible.module_utils._text import to_native
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase
from ansible.utils.sentinel import Sentinel


class MissingSetting(AnsibleOptionsError):
    pass


def _get_plugin_config(pname, ptype, config, variables):
    try:
        # plugin creates settings on load, this is cached so not too expensive to redo
        loader = getattr(plugin_loader, '%s_loader' % ptype)
        p = loader.get(pname, class_only=True)
        if p is None:
            raise AnsibleLookupError('Unable to load %s plugin "%s"' % (ptype, pname))
        result = C.config.get_config_value(config, plugin_type=ptype, plugin_name=p._load_name, variables=variables)
    except AnsibleLookupError:
        raise
    except AnsibleError as e:
        msg = to_native(e)
        if 'was not defined' in msg:
            raise MissingSetting(msg, orig_exc=e)
        raise e

    return result


def _get_global_config(config):
    try:
        result = getattr(C, config)
        if callable(result):
            raise AnsibleLookupError('Invalid setting "%s" attempted' % config)
    except AttributeError as e:
        raise MissingSetting(to_native(e), orig_exc=e)

    return result


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        missing = self.get_option('on_missing')
        ptype = self.get_option('plugin_type')
        pname = self.get_option('plugin_name')

        if (ptype or pname) and not (ptype and pname):
            raise AnsibleOptionsError('Both plugin_type and plugin_name are required, cannot use one without the other')

        if not isinstance(missing, string_types) or missing not in ['error', 'warn', 'skip']:
            raise AnsibleOptionsError('"on_missing" must be a string and one of "error", "warn" or "skip", not %s' % missing)

        ret = []

        for term in terms:
            if not isinstance(term, string_types):
                raise AnsibleOptionsError('Invalid setting identifier, "%s" is not a string, its a %s' % (term, type(term)))

            result = Sentinel
            try:
                if pname:
                    result = _get_plugin_config(pname, ptype, term, variables)
                else:
                    result = _get_global_config(term)
            except MissingSetting as e:
                if missing == 'error':
                    raise AnsibleLookupError('Unable to find setting %s' % term, orig_exc=e)
                elif missing == 'warn':
                    self._display.warning('Skipping, did not find setting %s' % term)
                elif missing == 'skip':
                    pass  # this is not needed, but added to have all 3 options stated

            if result is not Sentinel:
                ret.append(result)
        return ret
