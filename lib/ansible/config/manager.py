# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import atexit
import decimal
import configparser
import functools
import os
import os.path
import sys
import stat
import tempfile
import typing as t

from collections.abc import Mapping, Sequence
from jinja2.nativetypes import NativeEnvironment

from ansible._internal._datatag import _tags
from ansible.errors import AnsibleOptionsError, AnsibleError, AnsibleUndefinedConfigEntry, AnsibleRequiredOptionError
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.module_utils.common.sentinel import Sentinel
from ansible.module_utils.common.text.converters import to_text, to_bytes, to_native
from ansible.module_utils.common.yaml import yaml_load
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.quoting import unquote
from ansible.utils.path import cleanup_tmp_file, makedirs_safe, unfrackpath


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

# config definition fields
GALAXY_SERVER_ADDITIONAL = {
    'api_version': {'default': None, 'choices': [2, 3]},
    'validate_certs': {'cli': [{'name': 'validate_certs'}]},
    'timeout': {'cli': [{'name': 'timeout'}]},
    'token': {'default': None},
}


@t.runtime_checkable
class _EncryptedStringProtocol(t.Protocol):
    """Protocol representing an `EncryptedString`, since it cannot be imported here."""
    # DTFIX-FUTURE: collapse this with the one in collection loader, once we can

    def _decrypt(self) -> str: ...


def _get_config_label(plugin_type: str, plugin_name: str, config: str) -> str:
    """Return a label for the given config."""
    entry = f'{config!r}'

    if plugin_type:
        entry += ' for'

        if plugin_name:
            entry += f' {plugin_name!r}'

        entry += f' {plugin_type} plugin'

    return entry


def ensure_type(value: object, value_type: str | None, origin: str | None = None, origin_ftype: str | None = None) -> t.Any:
    """
    Converts `value` to the requested `value_type`; raises `ValueError` for failed conversions.

    Values for `value_type` are:

    * boolean/bool: Return a `bool` by applying non-strict `bool` filter rules:
      'y', 'yes', 'on', '1', 'true', 't', 1, 1.0, True return True, any other value is False.
    * integer/int: Return an `int`. Accepts any `str` parseable by `int` or numeric value with a zero mantissa (including `bool`).
    * float: Return a `float`. Accepts any `str` parseable by `float` or numeric value (including `bool`).
    * list: Return a `list`. Accepts `list` or `Sequence`. Also accepts, `str`, splitting on ',' while stripping whitespace and unquoting items.
    * none: Return `None`. Accepts only the string "None".
    * path: Return a resolved path. Accepts `str`.
    * temppath/tmppath/tmp: Return a unique temporary directory inside the resolved path specified by the value.
    * pathspec: Return a `list` of resolved paths. Accepts a `list` or `Sequence`. Also accepts `str`, splitting on ':'.
    * pathlist: Return a `list` of resolved paths. Accepts a `list` or `Sequence`. Also accepts `str`, splitting on `,` while stripping whitespace from paths.
    * dictionary/dict: Return a `dict`. Accepts `dict` or `Mapping`.
    * string/str: Return a `str`. Accepts `bool`, `int`, `float`, `complex` or `str`.

    Path resolution ensures paths are `str` with expansion of '{{CWD}}', environment variables and '~'.
    Non-absolute paths are expanded relative to the basedir from `origin`, if specified.

    No conversion is performed if `value_type` is unknown or `value` is `None`.
    When `origin_ftype` is "ini", a `str` result will be unquoted.
    """

    if value is None:
        return None

    original_value = value
    copy_tags = value_type not in ('temppath', 'tmppath', 'tmp')

    value = _ensure_type(value, value_type, origin)

    if copy_tags and value is not original_value:
        if isinstance(value, list):
            value = [AnsibleTagHelper.tag_copy(original_value, item) for item in value]

        value = AnsibleTagHelper.tag_copy(original_value, value)

    if isinstance(value, str) and origin_ftype and origin_ftype == 'ini':
        value = unquote(value)

    return value


def _ensure_type(value: object, value_type: str | None, origin: str | None = None) -> t.Any:
    """Internal implementation for `ensure_type`, call that function instead."""
    original_value = value
    basedir = origin if origin and os.path.isabs(origin) and os.path.exists(to_bytes(origin)) else None

    if value_type:
        value_type = value_type.lower()

    match value_type:
        case 'boolean' | 'bool':
            return boolean(value, strict=False)

        case 'integer' | 'int':
            if isinstance(value, int):  # handle both int and bool (which is an int)
                return int(value)

            if isinstance(value, (float, str)):
                try:
                    # use Decimal for all other source type conversions; non-zero mantissa is a failure
                    if (decimal_value := decimal.Decimal(value)) == (int_part := int(decimal_value)):
                        return int_part
                except (decimal.DecimalException, ValueError):
                    pass

        case 'float':
            if isinstance(value, float):
                return value

            if isinstance(value, (int, str)):
                try:
                    return float(value)
                except ValueError:
                    pass

        case 'list':
            if isinstance(value, list):
                return value

            if isinstance(value, str):
                return [unquote(x.strip()) for x in value.split(',')]

            if isinstance(value, Sequence) and not isinstance(value, bytes):
                return list(value)

        case 'none':
            if value == "None":
                return None

        case 'path':
            if isinstance(value, str):
                return resolve_path(value, basedir=basedir)

        case 'temppath' | 'tmppath' | 'tmp':
            if isinstance(value, str):
                value = resolve_path(value, basedir=basedir)

                if not os.path.exists(value):
                    makedirs_safe(value, 0o700)

                prefix = 'ansible-local-%s' % os.getpid()
                value = tempfile.mkdtemp(prefix=prefix, dir=value)
                atexit.register(cleanup_tmp_file, value, warn=True)

                return value

        case 'pathspec':
            if isinstance(value, str):
                value = value.split(os.pathsep)

            if isinstance(value, Sequence) and not isinstance(value, bytes) and all(isinstance(x, str) for x in value):
                return [resolve_path(x, basedir=basedir) for x in value]

        case 'pathlist':
            if isinstance(value, str):
                value = [x.strip() for x in value.split(',')]

            if isinstance(value, Sequence) and not isinstance(value, bytes) and all(isinstance(x, str) for x in value):
                return [resolve_path(x, basedir=basedir) for x in value]

        case 'dictionary' | 'dict':
            if isinstance(value, dict):
                return value

            if isinstance(value, Mapping):
                return dict(value)

        case 'string' | 'str':
            if isinstance(value, str):
                return value

            if isinstance(value, (bool, int, float, complex)):
                return str(value)

            if isinstance(value, _EncryptedStringProtocol):
                return value._decrypt()

        case _:
            # FIXME: define and document a pass-through value_type (None, 'raw', 'object', '', ...) and then deprecate acceptance of unknown types
            return value  # return non-str values of unknown value_type as-is

    raise ValueError(f'Invalid value provided for {value_type!r}: {original_value!r}')


# FIXME: see if this can live in utils/path
def resolve_path(path: str, basedir: str | None = None) -> str:
    """ resolve relative or 'variable' paths """
    if '{{CWD}}' in path:  # allow users to force CWD using 'magic' {{CWD}}
        path = path.replace('{{CWD}}', os.getcwd())

    return unfrackpath(path, follow=False, basedir=basedir)


# FIXME: generic file type?
def get_config_type(cfile):

    ftype = None
    if cfile is not None:
        ext = os.path.splitext(cfile)[-1]
        if ext in ('.ini', '.cfg'):
            ftype = 'ini'
        elif ext in ('.yaml', '.yml'):
            ftype = 'yaml'
        else:
            raise AnsibleOptionsError("Unsupported configuration file extension for %s: %s" % (cfile, to_native(ext)))

    return ftype


def find_ini_config_file(warnings=None):
    """ Load INI Config File order(first found is used): ENV, CWD, HOME, /etc/ansible """
    # FIXME: eventually deprecate ini configs

    if warnings is None:
        # Note: In this case, warnings does nothing
        warnings = set()

    potential_paths = []

    # A value that can never be a valid path so that we can tell if ANSIBLE_CONFIG was set later
    # We can't use None because we could set path to None.
    # Environment setting
    path_from_env = os.getenv("ANSIBLE_CONFIG", Sentinel)
    if path_from_env is not Sentinel:
        path_from_env = unfrackpath(path_from_env, follow=False)
        if os.path.isdir(to_bytes(path_from_env)):
            path_from_env = os.path.join(path_from_env, "ansible.cfg")
        potential_paths.append(path_from_env)

    # Current working directory
    warn_cmd_public = False
    try:
        cwd = os.getcwd()
        perms = os.stat(cwd)
        cwd_cfg = os.path.join(cwd, "ansible.cfg")
        if perms.st_mode & stat.S_IWOTH:
            # Working directory is world writable so we'll skip it.
            # Still have to look for a file here, though, so that we know if we have to warn
            if os.path.exists(cwd_cfg):
                warn_cmd_public = True
        else:
            potential_paths.append(to_text(cwd_cfg, errors='surrogate_or_strict'))
    except OSError:
        # If we can't access cwd, we'll simply skip it as a possible config source
        pass

    # Per user location
    potential_paths.append(unfrackpath("~/.ansible.cfg", follow=False))

    # System location
    potential_paths.append("/etc/ansible/ansible.cfg")

    for path in potential_paths:
        b_path = to_bytes(path)
        if os.path.exists(b_path) and os.access(b_path, os.R_OK):
            break
    else:
        path = None

    # Emit a warning if all the following are true:
    # * We did not use a config from ANSIBLE_CONFIG
    # * There's an ansible.cfg in the current working directory that we skipped
    if path_from_env != path and warn_cmd_public:
        warnings.add(u"Ansible is being run in a world writable directory (%s),"
                     u" ignoring it as an ansible.cfg source."
                     u" For more information see"
                     u" https://docs.ansible.com/ansible/devel/reference_appendices/config.html#cfg-in-world-writable-dir"
                     % to_text(cwd))

    return path


def _add_base_defs_deprecations(base_defs):
    """Add deprecation source 'ansible.builtin' to deprecations in base.yml"""
    def process(entry):
        if 'deprecated' in entry:
            entry['deprecated']['collection_name'] = 'ansible.builtin'

    for dummy, data in base_defs.items():
        process(data)
        for section in ('ini', 'env', 'vars'):
            if section in data:
                for entry in data[section]:
                    process(entry)


class ConfigManager:

    DEPRECATED = []  # type: list[tuple[str, dict[str, str]]]
    WARNINGS = set()  # type: set[str]

    _errors: list[tuple[str, Exception]]

    def __init__(self, conf_file=None, defs_file=None):
        self._get_ini_config_value = functools.cache(self._get_ini_config_value)

        self._base_defs = {}
        self._plugins = {}
        self._parsers = {}

        self._config_file = conf_file

        self._base_defs = self._read_config_yaml_file(defs_file or ('%s/base.yml' % os.path.dirname(__file__)))
        _add_base_defs_deprecations(self._base_defs)

        if self._config_file is None:
            # set config using ini
            self._config_file = find_ini_config_file(self.WARNINGS)

        # consume configuration
        if self._config_file:
            # initialize parser and read config
            self._parse_config_file()

        self._errors = []
        """Deferred errors that will be turned into warnings."""

        # ensure we always have config def entry
        self._base_defs['CONFIG_FILE'] = {'default': None, 'type': 'path'}

    def load_galaxy_server_defs(self, server_list):

        def server_config_def(section, key, required, option_type):
            config_def = {
                'description': 'The %s of the %s Galaxy server' % (key, section),
                'ini': [
                    {
                        'section': 'galaxy_server.%s' % section,
                        'key': key,
                    }
                ],
                'env': [
                    {'name': 'ANSIBLE_GALAXY_SERVER_%s_%s' % (section.upper(), key.upper())},
                ],
                'required': required,
                'type': option_type,
            }
            if key in GALAXY_SERVER_ADDITIONAL:
                config_def.update(GALAXY_SERVER_ADDITIONAL[key])
                # ensure we always have a default timeout
                if key == 'timeout' and 'default' not in config_def:
                    config_def['default'] = self.get_config_value('GALAXY_SERVER_TIMEOUT')

            return config_def

        if server_list:
            for server_key in server_list:
                if not server_key:
                    # To filter out empty strings or non truthy values as an empty server list env var is equal to [''].
                    continue

                # Config definitions are looked up dynamically based on the C.GALAXY_SERVER_LIST entry. We look up the
                # section [galaxy_server.<server>] for the values url, username, password, and token.
                defs = dict((k, server_config_def(server_key, k, req, value_type)) for k, req, value_type in GALAXY_SERVER_DEF)
                self.initialize_plugin_configuration_definitions('galaxy_server', server_key, defs)

    def template_default(self, value, variables, key_name: str = '<unknown>'):
        if isinstance(value, str) and (value.startswith('{{') and value.endswith('}}')) and variables is not None:
            # template default values if possible
            # NOTE: cannot use is_template due to circular dep
            try:
                # FIXME: This really should be using an immutable sandboxed native environment, not just native environment
                template = NativeEnvironment().from_string(value)
                value = template.render(variables)
            except Exception as ex:
                self._errors.append((f'Failed to template default for config {key_name}.', ex))
        return value

    def _read_config_yaml_file(self, yml_file):
        # TODO: handle relative paths as relative to the directory containing the current playbook instead of CWD
        # Currently this is only used with absolute paths to the `ansible/config` directory
        yml_file = to_bytes(yml_file)
        if os.path.exists(yml_file):
            with open(yml_file, 'rb') as config_def:
                return yaml_load(config_def) or {}
        raise AnsibleError(
            "Missing base YAML definition file (bad install?): %s" % to_native(yml_file))

    def _parse_config_file(self, cfile=None):
        """ return flat configuration settings from file(s) """
        # TODO: take list of files with merge/nomerge

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
                        raise AnsibleOptionsError("Error reading config file(%s) because the config file was not utf8 encoded: %s" % (cfile, to_native(e)))
                try:
                    self._parsers[cfile].read_string(cfg_text)
                except configparser.Error as e:
                    raise AnsibleOptionsError("Error reading config file (%s): %s" % (cfile, to_native(e)))
            # FIXME: this should eventually handle yaml config files
            # elif ftype == 'yaml':
            #     with open(cfile, 'rb') as config_stream:
            #         self._parsers[cfile] = yaml_load(config_stream)
            else:
                raise AnsibleOptionsError("Unsupported configuration file type: %s" % to_native(ftype))

    def _find_yaml_config_files(self):
        """ Load YAML Config Files in order, check merge flags, keep origin of settings"""
        pass

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
                for var_entry in pdef['vars']:
                    pvars.append(var_entry['name'])
        return pvars

    def get_plugin_options_from_var(self, plugin_type, name, variable):

        options = []
        for option_name, pdef in self.get_configuration_definitions(plugin_type=plugin_type, name=name).items():
            if 'vars' in pdef and pdef['vars']:
                for var_entry in pdef['vars']:
                    if variable == var_entry['name']:
                        options.append(option_name)
        return options

    def get_configuration_definition(self, name, plugin_type=None, plugin_name=None):

        ret = {}
        if plugin_type is None:
            ret = self._base_defs.get(name, None)
        elif plugin_name is None:
            ret = self._plugins.get(plugin_type, {}).get(name, None)
        else:
            ret = self._plugins.get(plugin_type, {}).get(plugin_name, {}).get(name, None)

        return ret

    def has_configuration_definition(self, plugin_type, name):

        has = False
        if plugin_type in self._plugins:
            has = (name in self._plugins[plugin_type])

        return has

    def get_configuration_definitions(self, plugin_type=None, name=None, ignore_private=False):
        """ just list the possible settings, either base or for specific plugins or plugin """

        ret = {}
        if plugin_type is None:
            ret = self._base_defs
        elif name is None:
            ret = self._plugins.get(plugin_type, {})
        else:
            ret = self._plugins.get(plugin_type, {}).get(name, {})

        if ignore_private:  # ignore 'test' config entries, they should not change runtime behaviors
            for cdef in list(ret.keys()):
                if cdef.startswith('_Z_'):
                    del ret[cdef]
        return ret

    def _loop_entries(self, container, entry_list):
        """ repeat code for value entry assignment """

        value = None
        origin = None
        for entry in entry_list:
            name = entry.get('name')
            try:
                temp_value = container.get(name, None)
            except UnicodeEncodeError:
                self.WARNINGS.add(u'value for config entry {0} contains invalid characters, ignoring...'.format(to_text(name)))
                continue
            if temp_value is not None:  # only set if entry is defined in container
                value = temp_value
                origin = name

                # deal with deprecation of setting source, if used
                if 'deprecated' in entry:
                    self.DEPRECATED.append((entry['name'], entry['deprecated']))

        return value, origin

    def get_config_value(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None, direct=None):
        """ wrapper """

        try:
            value, _drop = self.get_config_value_and_origin(config, cfile=cfile, plugin_type=plugin_type, plugin_name=plugin_name,
                                                            keys=keys, variables=variables, direct=direct)
        except AnsibleError:
            raise
        except Exception as ex:
            raise AnsibleError(f"Unhandled exception when retrieving {config!r}.") from ex
        return value

    def get_config_default(self, config: str, plugin_type: str | None = None, plugin_name: str | None = None) -> t.Any:
        """Return the default value for the specified configuration."""
        return self.get_configuration_definitions(plugin_type, plugin_name)[config]['default']

    def get_config_value_and_origin(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None, direct=None):
        """ Given a config key figure out the actual value and report on the origin of the settings """
        if cfile is None:
            # use default config
            cfile = self._config_file

        if config == 'CONFIG_FILE':
            return cfile, ''

        # Note: sources that are lists listed in low to high precedence (last one wins)
        value = None
        origin = None
        origin_ftype = None

        defs = self.get_configuration_definitions(plugin_type=plugin_type, name=plugin_name)
        if config in defs:

            aliases = defs[config].get('aliases', [])

            # direct setting via plugin arguments, can set to None so we bypass rest of processing/defaults
            if direct:
                if config in direct:
                    value = direct[config]
                    origin = 'Direct'
                else:
                    direct_aliases = [direct[alias] for alias in aliases if alias in direct]
                    if direct_aliases:
                        value = direct_aliases[0]
                        origin = 'Direct'

            if value is None and variables and defs[config].get('vars'):
                # Use 'variable overrides' if present, highest precedence, but only present when querying running play
                value, origin = self._loop_entries(variables, defs[config]['vars'])
                origin = 'var: %s' % origin

            # use playbook keywords if you have em
            if value is None and defs[config].get('keyword') and keys:
                value, origin = self._loop_entries(keys, defs[config]['keyword'])
                origin = 'keyword: %s' % origin

            # automap to keywords
            # TODO: deprecate these in favor of explicit keyword above
            if value is None and keys:
                if config in keys:
                    value = keys[config]
                    keyword = config

                elif aliases:
                    for alias in aliases:
                        if alias in keys:
                            value = keys[alias]
                            keyword = alias
                            break

                if value is not None:
                    origin = 'keyword: %s' % keyword

            if value is None and 'cli' in defs[config]:
                # avoid circular import .. until valid
                from ansible import context
                value, origin = self._loop_entries(context.CLIARGS, defs[config]['cli'])
                origin = 'cli: %s' % origin

            # env vars are next precedence
            if value is None and defs[config].get('env'):
                value, origin = self._loop_entries(os.environ, defs[config]['env'])
                value = _tags.TrustedAsTemplate().tag(value)
                origin = 'env: %s' % origin

            # try config file entries next, if we have one
            if self._parsers.get(cfile, None) is None:
                self._parse_config_file(cfile)

            # attempt to read from config file
            if value is None and cfile is not None:
                ftype = get_config_type(cfile)
                if ftype and defs[config].get(ftype):
                    try:
                        for entry in defs[config][ftype]:
                            # load from config
                            if ftype == 'ini':
                                temp_value = self._get_ini_config_value(cfile, entry.get('section', 'defaults'), entry['key'])
                            elif ftype == 'yaml':
                                raise AnsibleError('YAML configuration type has not been implemented yet')
                            else:
                                raise AnsibleError('Invalid configuration file type: %s' % ftype)

                            if temp_value is not None:
                                # set value and origin
                                value = temp_value
                                origin = cfile
                                origin_ftype = ftype
                                if 'deprecated' in entry:
                                    if ftype == 'ini':
                                        self.DEPRECATED.append(('[%s]%s' % (entry['section'], entry['key']), entry['deprecated']))
                                    else:
                                        raise AnsibleError('Unimplemented file type: %s' % ftype)

                    except Exception as e:
                        sys.stderr.write("Error while loading config %s: %s" % (cfile, to_native(e)))

            # set default if we got here w/o a value
            if value is None:
                if defs[config].get('required', False):
                    if not plugin_type or config not in INTERNAL_DEFS.get(plugin_type, {}):
                        raise AnsibleRequiredOptionError(f"Required config {_get_config_label(plugin_type, plugin_name, config)} not provided.")
                else:
                    origin = 'default'
                    value = self.template_default(defs[config].get('default'), variables, key_name=_get_config_label(plugin_type, plugin_name, config))

            try:
                # ensure correct type, can raise exceptions on mismatched types
                value = ensure_type(value, defs[config].get('type'), origin=origin, origin_ftype=origin_ftype)
            except ValueError as ex:
                if origin.startswith('env:') and value == '':
                    # this is empty env var for non string so we can set to default
                    origin = 'default'
                    value = ensure_type(defs[config].get('default'), defs[config].get('type'), origin=origin, origin_ftype=origin_ftype)
                else:
                    raise AnsibleOptionsError(f'Config {_get_config_label(plugin_type, plugin_name, config)} from {origin!r} has an invalid value.') from ex

            # deal with restricted values
            if value is not None and 'choices' in defs[config] and defs[config]['choices'] is not None:
                invalid_choices = True  # assume the worst!
                if defs[config].get('type') == 'list':
                    # for a list type, compare all values in type are allowed
                    invalid_choices = not all(choice in defs[config]['choices'] for choice in value)
                else:
                    # these should be only the simple data types (string, int, bool, float, etc) .. ignore dicts for now
                    invalid_choices = value not in defs[config]['choices']

                if invalid_choices:

                    if isinstance(defs[config]['choices'], Mapping):
                        valid = ', '.join([to_text(k) for k in defs[config]['choices'].keys()])
                    elif isinstance(defs[config]['choices'], str):
                        valid = defs[config]['choices']
                    elif isinstance(defs[config]['choices'], Sequence):
                        valid = ', '.join([to_text(c) for c in defs[config]['choices']])
                    else:
                        valid = defs[config]['choices']

                    raise AnsibleOptionsError(f'Invalid value {value!r} for config {_get_config_label(plugin_type, plugin_name, config)}.',
                                              help_text=f'Valid values are: {valid}')

            # deal with deprecation of the setting
            if 'deprecated' in defs[config] and origin != 'default':
                self.DEPRECATED.append((config, defs[config].get('deprecated')))
        else:
            raise AnsibleUndefinedConfigEntry(f'No config definition exists for {_get_config_label(plugin_type, plugin_name, config)}.')

        if not _tags.Origin.is_tagged_on(value):
            value = _tags.Origin(description=f'<Config {origin}>').tag(value)

        return value, origin

    def initialize_plugin_configuration_definitions(self, plugin_type, name, defs):

        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}

        self._plugins[plugin_type][name] = defs

    def _get_ini_config_value(self, config_file: str, section: str, option: str) -> t.Any:
        """
        Fetch `option` from the specified `section`.
        Returns `None` if the specified `section` or `option` are not present.
        Origin and TrustedAsTemplate tags are applied to returned values.

        CAUTION: Although INI sourced configuration values are trusted for templating, that does not automatically mean they will be templated.
                 It is up to the code consuming configuration values to apply templating if required.
        """
        parser = self._parsers[config_file]
        value = parser.get(section, option, raw=True, fallback=None)

        if value is not None:
            value = self._apply_tags(value, section, option)

        return value

    def _apply_tags(self, value: str, section: str, option: str) -> t.Any:
        """Apply origin and trust to the given `value` sourced from the stated `section` and `option`."""
        description = f'section {section!r} option {option!r}'
        origin = _tags.Origin(path=self._config_file, description=description)
        tags = [origin, _tags.TrustedAsTemplate()]
        value = AnsibleTagHelper.tag(value, tags)

        return value

    @staticmethod
    def get_deprecated_msg_from_config(dep_docs, include_removal=False, collection_name=None):

        removal = ''
        if include_removal:
            if 'removed_at_date' in dep_docs:
                removal = f"Will be removed in a release after {dep_docs['removed_at_date']}\n\t"
            elif collection_name:
                removal = f"Will be removed in: {collection_name} {dep_docs['removed_in']}\n\t"
            else:
                removal = f"Will be removed in: Ansible {dep_docs['removed_in']}\n\t"

        # TODO: choose to deprecate either singular or plural
        alt = dep_docs.get('alternatives', dep_docs.get('alternative', 'none'))
        return f"Reason: {dep_docs['why']}\n\t{removal}Alternatives: {alt}"
