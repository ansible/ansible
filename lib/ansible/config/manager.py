# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import atexit
import decimal
import configparser
import os
import os.path
import sys
import stat
import tempfile

from collections import namedtuple
from collections.abc import Mapping, Sequence
from jinja2.nativetypes import NativeEnvironment

from ansible.errors import AnsibleOptionsError, AnsibleError, AnsibleRequiredOptionError
from ansible.module_utils.common.sentinel import Sentinel
from ansible.module_utils.common.text.converters import to_text, to_bytes, to_native
from ansible.module_utils.common.yaml import yaml_load
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.quoting import unquote
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.path import cleanup_tmp_file, makedirs_safe, unfrackpath

Setting = namedtuple('Setting', 'name value origin type')

INTERNAL_DEFS = {'lookup': ('_terms',)}

GALAXY_SERVER_DEF = [
    ('url', True, 'str'),
    ('username', False, 'str'),
    ('password', False, 'str'),
    ('token', False, 'str'),
    ('auth_url', False, 'str'),
    ('api_version', False, 'int'),
    ('validate_certs', False, 'bool'),
    ('client_id', False, 'str'),
    ('client_secret', False, 'str'),
    ('timeout', False, 'int'),
]

GALAXY_SERVER_ADDITIONAL = {
    'api_version': {'default': None, 'choices': [2, 3]},
    'validate_certs': {'cli': [{'name': 'validate_certs'}]},
    'timeout': {'cli': [{'name': 'timeout'}]},
    'token': {'default': None},
}

def _get_entry(plugin_type, plugin_name, config):
    """Construct entry for requested config."""
    entry = []
    if plugin_type:
        entry.append(f'plugin_type: {plugin_type}')
        if plugin_name:
            entry.append(f'plugin: {plugin_name}')
    entry.append(f'setting: {config}')
    return ' '.join(entry)

def ensure_type(value, value_type, origin=None, origin_ftype=None):
    """Return a configuration variable with casting."""
    if value is None:
        return to_text(value, errors='surrogate_or_strict', nonstring='passthru')

    value_type = value_type.lower() if value_type else None
    basedir = origin if origin and os.path.isabs(origin) and os.path.exists(to_bytes(origin)) else None

    if value_type in ('boolean', 'bool'):
        value = boolean(value, strict=False)
    elif value_type in ('integer', 'int'):
        if not isinstance(value, int):
            try:
                decimal_value = decimal.Decimal(value)
                if decimal_value == int(decimal_value):
                    value = int(decimal_value)
                else:
                    raise ValueError('int')
            except decimal.DecimalException:
                raise ValueError
    elif value_type == 'float':
        if not isinstance(value, float):
            value = float(value)
    elif value_type == 'list':
        if isinstance(value, string_types):
            value = [unquote(x.strip()) for x in value.split(',')]
        elif not isinstance(value, Sequence):
            raise ValueError('list')
    elif value_type == 'none':
        if value == "None":
            value = None
        elif value is not None:
            raise ValueError('None')
    elif value_type == 'path':
        if isinstance(value, string_types):
            value = resolve_path(value, basedir=basedir)
        else:
            raise ValueError('path')
    elif value_type in ('tmp', 'temppath', 'tmppath'):
        if isinstance(value, string_types):
            value = resolve_path(value, basedir=basedir)
            if not os.path.exists(value):
                makedirs_safe(value, 0o700)
            prefix = f'ansible-local-{os.getpid()}'
            value = tempfile.mkdtemp(prefix=prefix, dir=value)
            atexit.register(cleanup_tmp_file, value, warn=True)
        else:
            raise ValueError('temppath')
    elif value_type == 'pathspec':
        if isinstance(value, string_types):
            value = value.split(os.pathsep)
        if isinstance(value, Sequence):
            value = [resolve_path(x, basedir=basedir) for x in value]
        else:
            raise ValueError('pathspec')
    elif value_type == 'pathlist':
        if isinstance(value, string_types):
            value = [x.strip() for x in value.split(',')]
        if isinstance(value, Sequence):
            value = [resolve_path(x, basedir=basedir) for x in value]
        else:
            raise ValueError('pathlist')
    elif value_type in ('dict', 'dictionary'):
        if not isinstance(value, Mapping):
            raise ValueError('dictionary')
    elif value_type in ('str', 'string'):
        if isinstance(value, (string_types, AnsibleVaultEncryptedUnicode, bool, int, float, complex)):
            value = to_text(value, errors='surrogate_or_strict')
            if origin_ftype == 'ini':
                value = unquote(value)
        else:
            raise ValueError('string')
    elif isinstance(value, (string_types, AnsibleVaultEncryptedUnicode)):
        value = to_text(value, errors='surrogate_or_strict')
        if origin_ftype == 'ini':
            value = unquote(value)
    else:
        raise ValueError(f'Invalid type provided: {value_type}')

    return to_text(value, errors='surrogate_or_strict', nonstring='passthru')

def resolve_path(path, basedir=None):
    """Resolve relative or 'variable' paths."""
    if '{{CWD}}' in path:
        path = path.replace('{{CWD}}', os.getcwd())
    return unfrackpath(path, follow=False, basedir=basedir)

def get_config_type(cfile):
    """Determine the type of the configuration file."""
    if cfile is None:
        return None
    ext = os.path.splitext(cfile)[-1]
    if ext in ('.ini', '.cfg'):
        return 'ini'
    elif ext in ('.yaml', '.yml'):
        return 'yaml'
    raise AnsibleOptionsError(f"Unsupported configuration file extension for {cfile}: {to_native(ext)}")

def get_ini_config_value(p, entry):
    """Return the value of the last ini entry found."""
    if p is None:
        return None
    try:
        return p.get(entry.get('section', 'defaults'), entry.get('key', ''), raw=True)
    except Exception:
        return None

def find_ini_config_file(warnings=None):
    """Load INI Config File order(first found is used): ENV, CWD, HOME, /etc/ansible."""
    if warnings is None:
        warnings = set()

    potential_paths = []
    path_from_env = os.getenv("ANSIBLE_CONFIG", Sentinel)
    if path_from_env is not Sentinel:
        path_from_env = unfrackpath(path_from_env, follow=False)
        if os.path.isdir(to_bytes(path_from_env)):
            path_from_env = os.path.join(path_from_env, "ansible.cfg")
        potential_paths.append(path_from_env)

    warn_cmd_public = False
    try:
        cwd = os.getcwd()
        perms = os.stat(cwd)
        cwd_cfg = os.path.join(cwd, "ansible.cfg")
        if perms.st_mode & stat.S_IWOTH:
            if os.path.exists(cwd_cfg):
                warn_cmd_public = True
        else:
            potential_paths.append(to_text(cwd_cfg, errors='surrogate_or_strict'))
    except OSError:
        pass

    potential_paths.append(unfrackpath("~/.ansible.cfg", follow=False))
    potential_paths.append("/etc/ansible/ansible.cfg")

    for path in potential_paths:
        b_path = to_bytes(path)
        if os.path.exists(b_path) and os.access(b_path, os.R_OK):
            break
    else:
        path = None

    if path_from_env != path and warn_cmd_public:
        warnings.add(f"Ansible is being run in a world writable directory ({to_text(cwd)}), ignoring it as an ansible.cfg source. For more information see https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir")

    return path

def _add_base_defs_deprecations(base_defs):
    """Add deprecation source 'ansible.builtin' to deprecations in base.yml."""
    def process(entry):
        if 'deprecated' in entry:
            entry['deprecated']['collection_name'] = 'ansible.builtin'

    for data in base_defs.values():
        process(data)
        for section in ('ini', 'env', 'vars'):
            if section in data:
                for entry in data[section]:
                    process(entry)

class ConfigManager:
    DEPRECATED = []
    WARNINGS = set()

    def __init__(self, conf_file=None, defs_file=None):
        self._base_defs = {}
        self._plugins = {}
        self._parsers = {}
        self._config_file = conf_file

        self._base_defs = self._read_config_yaml_file(defs_file or f'{os.path.dirname(__file__)}/base.yml')
        _add_base_defs_deprecations(self._base_defs)

        if self._config_file is None:
            self._config_file = find_ini_config_file(self.WARNINGS)

        if self._config_file:
            self._parse_config_file()

        self._base_defs['CONFIG_FILE'] = {'default': None, 'type': 'path'}

    def load_galaxy_server_defs(self, server_list):
        def server_config_def(section, key, required, option_type):
            config_def = {
                'description': f'The {key} of the {section} Galaxy server',
                'ini': [{'section': f'galaxy_server.{section}', 'key': key}],
                'env': [{'name': f'ANSIBLE_GALAXY_SERVER_{section.upper()}_{key.upper()}'}],
                'required': required,
                'type': option_type,
            }
            if key in GALAXY_SERVER_ADDITIONAL:
                config_def.update(GALAXY_SERVER_ADDITIONAL[key])
                if key == 'timeout' and 'default' not in config_def:
                    config_def['default'] = self.get_config_value('GALAXY_SERVER_TIMEOUT')
            return config_def

        if server_list:
            for server_key in server_list:
                if server_key:
                    defs = {k: server_config_def(server_key, k, req, value_type) for k, req, value_type in GALAXY_SERVER_DEF}
                    self.initialize_plugin_configuration_definitions('galaxy_server', server_key, defs)

    def template_default(self, value, variables):
        if isinstance(value, string_types) and value.startswith('{{') and value.endswith('}}') and variables is not None:
            try:
                t = NativeEnvironment().from_string(value)
                value = t.render(variables)
            except Exception:
                pass
        return value

    def _read_config_yaml_file(self, yml_file):
        yml_file = to_bytes(yml_file)
        if os.path.exists(yml_file):
            with open(yml_file, 'rb') as config_def:
                return yaml_load(config_def) or {}
        raise AnsibleError(f"Missing base YAML definition file (bad install?): {to_native(yml_file)}")

    def _parse_config_file(self, cfile=None):
        if cfile is None:
            cfile = self._config_file

        ftype = get_config_type(cfile)
        if cfile is not None:
            if ftype == 'ini':
                self._parsers[cfile] = configparser.ConfigParser(inline_comment_prefixes=(';',))
                with open(to_bytes(cfile), 'rb') as f:
                    try:
                        cfg_text = to_text(f.read(), errors='surrogate_or_strict')
                    except UnicodeError as e:
                        raise AnsibleOptionsError(f"Error reading config file({cfile}) because the config file was not utf8 encoded: {to_native(e)}")
                try:
                    self._parsers[cfile].read_string(cfg_text)
                except configparser.Error as e:
                    raise AnsibleOptionsError(f"Error reading config file ({cfile}): {to_native(e)}")
            else:
                raise AnsibleOptionsError(f"Unsupported configuration file type: {to_native(ftype)}")

    def get_plugin_options(self, plugin_type, name, keys=None, variables=None, direct=None):
        options = {}
        defs = self.get_configuration_definitions(plugin_type=plugin_type, name=name)
        for option in defs:
            options[option] = self.get_config_value(option, plugin_type=plugin_type, plugin_name=name, keys=keys, variables=variables, direct=direct)
        return options

    def get_plugin_vars(self, plugin_type, name):
        pvars = []
        for pdef in self.get_configuration_definitions(plugin_type=plugin_type, name=name).values():
            if 'vars' in pdef and pdef['vars']:
                pvars.extend(var_entry['name'] for var_entry in pdef['vars'])
        return pvars

    def get_plugin_options_from_var(self, plugin_type, name, variable):
        options = []
        for option_name, pdef in self.get_configuration_definitions(plugin_type=plugin_type, name=name).items():
            if 'vars' in pdef and pdef['vars']:
                options.extend(option_name for var_entry in pdef['vars'] if variable == var_entry['name'])
        return options

    def get_configuration_definition(self, name, plugin_type=None, plugin_name=None):
        if plugin_type is None:
            return self._base_defs.get(name)
        elif plugin_name is None:
            return self._plugins.get(plugin_type, {}).get(name)
        else:
            return self._plugins.get(plugin_type, {}).get(plugin_name, {}).get(name)

    def has_configuration_definition(self, plugin_type, name):
        return plugin_type in self._plugins and name in self._plugins[plugin_type]

    def get_configuration_definitions(self, plugin_type=None, name=None, ignore_private=False):
        ret = self._base_defs if plugin_type is None else self._plugins.get(plugin_type, {}) if name is None else self._plugins.get(plugin_type, {}).get(name, {})
        if ignore_private:
            ret = {k: v for k, v in ret.items() if not k.startswith('_')}
        return ret

    def _loop_entries(self, container, entry_list):
        value = None
        origin = None
        for entry in entry_list:
            name = entry.get('name')
            try:
                temp_value = container.get(name, None)
            except UnicodeEncodeError:
                self.WARNINGS.add(f'value for config entry {to_text(name)} contains invalid characters, ignoring...')
                continue
            if temp_value is not None:
                if isinstance(temp_value, AnsibleVaultEncryptedUnicode):
                    temp_value = to_text(temp_value, errors='surrogate_or_strict')
                value = temp_value
                origin = name
                if 'deprecated' in entry:
                    self.DEPRECATED.append((entry['name'], entry['deprecated']))
        return value, origin

    def get_config_value(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None, direct=None):
        try:
            value, _ = self.get_config_value_and_origin(config, cfile=cfile, plugin_type=plugin_type, plugin_name=plugin_name, keys=keys, variables=variables, direct=direct)
        except AnsibleError:
            raise
        except Exception as e:
            raise AnsibleError(f"Unhandled exception when retrieving {config}:\n{to_native(e)}", orig_exc=e)
        return value

    def get_config_value_and_origin(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None, direct=None):
        if cfile is None:
            cfile = self._config_file

        if config == 'CONFIG_FILE':
            return cfile, ''

        value = None
        origin = None
        origin_ftype = None

        defs = self.get_configuration_definitions(plugin_type=plugin_type, name=plugin_name)
        if config in defs:
            aliases = defs[config].get('aliases', [])

            if direct:
                if config in direct:
                    value = direct[config]
                    origin = 'Direct'
                else:
                    direct_aliases = [direct[alias] for alias in aliases if alias in direct]
                    if direct_aliases:
                        value = direct_aliases[0]
                        origin = 'Direct'

            if value is None and