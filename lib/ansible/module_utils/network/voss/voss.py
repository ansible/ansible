# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2018 Extreme Networks Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import json
import re

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.network.common.utils import to_list, ComplexList
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.config import NetworkConfig, ConfigLine

_DEVICE_CONFIGS = {}

DEFAULT_COMMENT_TOKENS = ['#', '!', '/*', '*/', 'echo']

DEFAULT_IGNORE_LINES_RE = set([
    re.compile(r"Preparing to Display Configuration\.\.\.")
])


def get_connection(module):
    if hasattr(module, '_voss_connection'):
        return module._voss_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module._voss_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module._voss_connection


def get_capabilities(module):
    if hasattr(module, '_voss_capabilities'):
        return module._voss_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module._voss_capabilities = json.loads(capabilities)
    return module._voss_capabilities


def get_defaults_flag(module):
    connection = get_connection(module)
    try:
        out = connection.get_defaults_flag()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    return to_text(out, errors='surrogate_then_replace').strip()


def get_config(module, source='running', flags=None):
    flag_str = ' '.join(to_list(flags))

    try:
        return _DEVICE_CONFIGS[flag_str]
    except KeyError:
        connection = get_connection(module)
        try:
            out = connection.get_config(source=source, flags=flags)
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
        cfg = to_text(out, errors='surrogate_then_replace').strip()
        _DEVICE_CONFIGS[flag_str] = cfg
        return cfg


def to_commands(module, commands):
    spec = {
        'command': dict(key=True),
        'prompt': dict(),
        'answer': dict()
    }
    transform = ComplexList(spec, module)
    return transform(commands)


def run_commands(module, commands, check_rc=True):
    connection = get_connection(module)
    try:
        out = connection.run_commands(commands=commands, check_rc=check_rc)
        return out
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def load_config(module, commands):
    connection = get_connection(module)

    try:
        resp = connection.edit_config(commands)
        return resp.get('response')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))


def get_sublevel_config(running_config, module):
    contents = list()
    current_config_contents = list()
    sublevel_config = VossNetworkConfig(indent=0)
    obj = running_config.get_object(module.params['parents'])
    if obj:
        contents = obj._children
    for c in contents:
        if isinstance(c, ConfigLine):
            current_config_contents.append(c.raw)
    sublevel_config.add(current_config_contents, module.params['parents'])
    return sublevel_config


def ignore_line(text, tokens=None):
    for item in (tokens or DEFAULT_COMMENT_TOKENS):
        if text.startswith(item):
            return True
    for regex in DEFAULT_IGNORE_LINES_RE:
        if regex.match(text):
            return True


def voss_parse(lines, indent=None, comment_tokens=None):
    toplevel = re.compile(r'(^interface.*$)|(^router \w+$)|(^router vrf \w+$)')
    exitline = re.compile(r'^exit$')
    entry_reg = re.compile(r'([{};])')

    ancestors = list()
    config = list()
    dup_parent_index = None

    for line in to_native(lines, errors='surrogate_or_strict').split('\n'):
        text = entry_reg.sub('', line).strip()

        cfg = ConfigLine(text)

        if not text or ignore_line(text, comment_tokens):
            continue

        # Handle top level commands
        if toplevel.match(text):
            # Looking to see if we have existing parent
            for index, item in enumerate(config):
                if item.text == text:
                    # This means we have an existing parent with same label
                    dup_parent_index = index
                    break
            ancestors = [cfg]
            config.append(cfg)

        # Handle 'exit' line
        elif exitline.match(text):
            ancestors = list()

            if dup_parent_index is not None:
                # We're working with a duplicate parent
                # Don't need to store exit, just go to next line in config
                dup_parent_index = None
            else:
                cfg._parents = ancestors[:1]
                config.append(cfg)

        # Handle sub-level commands. Only have single sub-level
        elif ancestors:
            cfg._parents = ancestors[:1]
            if dup_parent_index is not None:
                # Update existing entry, since this already exists in config
                config[int(dup_parent_index)].add_child(cfg)
                new_index = dup_parent_index + 1
                config.insert(new_index, cfg)
            else:
                ancestors[0].add_child(cfg)
                config.append(cfg)

        else:
            # Global command, no further special handling needed
            config.append(cfg)
    return config


class VossNetworkConfig(NetworkConfig):

    def load(self, s):
        self._config_text = s
        self._items = voss_parse(s, self._indent)

    def _diff_line(self, other):
        updates = list()
        for item in self.items:
            if str(item) == "exit":
                if updates and updates[-1]._parents:
                    updates.append(item)
            elif item not in other:
                updates.append(item)
        return updates
