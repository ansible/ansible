# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import atexit
import io
import os
import os.path
import sys
import stat
import tempfile
import traceback
from collections import namedtuple

from ansible.config.data import ConfigData
from ansible.errors import AnsibleOptionsError, AnsibleError
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.common._collections_compat import Mapping, Sequence
from ansible.module_utils.common.yaml import yaml_load
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.quoting import unquote
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils import py3compat
from ansible.utils.path import cleanup_tmp_file, makedirs_safe, unfrackpath


Plugin = namedtuple('Plugin', 'name type')
Setting = namedtuple('Setting', 'name value origin type')

INTERNAL_DEFS = {'lookup': ('_terms',)}


def _get_entry(plugin_type, plugin_name, config):
    ''' construct entry for requested config '''
    entry = ''
    if plugin_type:
        entry += 'plugin_type: %s ' % plugin_type
        if plugin_name:
            entry += 'plugin: %s ' % plugin_name
    entry += 'setting: %s ' % config
    return entry


# FIXME: see if we can unify in module_utils with similar function used by argspec
def ensure_type(value, value_type, origin=None):
    ''' return a configuration variable with casting
    :arg value: The value to ensure correct typing of
    :kwarg value_type: The type of the value.  This can be any of the following strings:
        :boolean: sets the value to a True or False value
        :bool: Same as 'boolean'
        :integer: Sets the value to an integer or raises a ValueType error
        :int: Same as 'integer'
        :float: Sets the value to a float or raises a ValueType error
        :list: Treats the value as a comma separated list.  Split the value
            and return it as a python list.
        :none: Sets the value to None
        :path: Expands any environment variables and tilde's in the value.
        :tmppath: Create a unique temporary directory inside of the directory
            specified by value and return its path.
        :temppath: Same as 'tmppath'
        :tmp: Same as 'tmppath'
        :pathlist: Treat the value as a typical PATH string.  (On POSIX, this
            means colon separated strings.)  Split the value and then expand
            each part for environment variables and tildes.
        :pathspec: Treat the value as a PATH string. Expands any environment variables
            tildes's in the value.
        :str: Sets the value to string types.
        :string: Same as 'str'
    '''

    errmsg = ''
    basedir = None
    if origin and os.path.isabs(origin) and os.path.exists(to_bytes(origin)):
        basedir = origin

    if value_type:
        value_type = value_type.lower()

    if value is not None:
        if value_type in ('boolean', 'bool'):
            value = boolean(value, strict=False)

        elif value_type in ('integer', 'int'):
            value = int(value)

        elif value_type == 'float':
            value = float(value)

        elif value_type == 'list':
            if isinstance(value, string_types):
                value = [unquote(x.strip()) for x in value.split(',')]
            elif not isinstance(value, Sequence):
                errmsg = 'list'

        elif value_type == 'none':
            if value == "None":
                value = None

            if value is not None:
                errmsg = 'None'

        elif value_type == 'path':
            if isinstance(value, string_types):
                value = resolve_path(value, basedir=basedir)
            else:
                errmsg = 'path'

        elif value_type in ('tmp', 'temppath', 'tmppath'):
            if isinstance(value, string_types):
                value = resolve_path(value, basedir=basedir)
                if not os.path.exists(value):
                    makedirs_safe(value, 0o700)
                prefix = 'ansible-local-%s' % os.getpid()
                value = tempfile.mkdtemp(prefix=prefix, dir=value)
                atexit.register(cleanup_tmp_file, value, warn=True)
            else:
                errmsg = 'temppath'

        elif value_type == 'pathspec':
            if isinstance(value, string_types):
                value = value.split(os.pathsep)

            if isinstance(value, Sequence):
                value = [resolve_path(x, basedir=basedir) for x in value]
            else:
                errmsg = 'pathspec'

        elif value_type == 'pathlist':
            if isinstance(value, string_types):
                value = [x.strip() for x in value.split(',')]

            if isinstance(value, Sequence):
                value = [resolve_path(x, basedir=basedir) for x in value]
            else:
                errmsg = 'pathlist'

        elif value_type in ('dict', 'dictionary'):
            if not isinstance(value, Mapping):
                errmsg = 'dictionary'

        elif value_type in ('str', 'string'):
            if isinstance(value, (string_types, AnsibleVaultEncryptedUnicode, bool, int, float, complex)):
                value = unquote(to_text(value, errors='surrogate_or_strict'))
            else:
                errmsg = 'string'

        # defaults to string type
        elif isinstance(value, (string_types, AnsibleVaultEncryptedUnicode)):
            value = unquote(to_text(value, errors='surrogate_or_strict'))

        if errmsg:
            raise ValueError('Invalid type provided for "%s": %s' % (errmsg, to_native(value)))

    return to_text(value, errors='surrogate_or_strict', nonstring='passthru')


# FIXME: see if this can live in utils/path
def resolve_path(path, basedir=None):
    ''' resolve relative or 'variable' paths '''
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


# FIXME: can move to module_utils for use for ini plugins also?
def get_ini_config_value(p, entry):
    ''' returns the value of last ini entry found '''
    value = None
    if p is not None:
        try:
            value = p.get(entry.get('section', 'defaults'), entry.get('key', ''), raw=True)
        except Exception:  # FIXME: actually report issues here
            pass
    return value


def find_ini_config_file(warnings=None):
    ''' Load INI Config File order(first found is used): ENV, CWD, HOME, /etc/ansible '''
    # FIXME: eventually deprecate ini configs

    if warnings is None:
        # Note: In this case, warnings does nothing
        warnings = set()

    # A value that can never be a valid path so that we can tell if ANSIBLE_CONFIG was set later
    # We can't use None because we could set path to None.
    SENTINEL = object

    potential_paths = []

    # Environment setting
    path_from_env = os.getenv("ANSIBLE_CONFIG", SENTINEL)
    if path_from_env is not SENTINEL:
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
    '''Add deprecation source 'ansible.builtin' to deprecations in base.yml'''
    def process(entry):
        if 'deprecated' in entry:
            entry['deprecated']['collection_name'] = 'ansible.builtin'

    for dummy, data in base_defs.items():
        process(data)
        for section in ('ini', 'env', 'vars'):
            if section in data:
                for entry in data[section]:
                    process(entry)


class ConfigManager(object):

    DEPRECATED = []
    WARNINGS = set()

    def __init__(self, conf_file=None, defs_file=None):

        self._base_defs = {}
        self._plugins = {}
        self._parsers = {}

        self._config_file = conf_file
        self.data = ConfigData()

        self._base_defs = self._read_config_yaml_file(defs_file or ('%s/base.yml' % os.path.dirname(__file__)))
        _add_base_defs_deprecations(self._base_defs)

        if self._config_file is None:
            # set config using ini
            self._config_file = find_ini_config_file(self.WARNINGS)

        # consume configuration
        if self._config_file:
            # initialize parser and read config
            self._parse_config_file()

        # update constants
        self.update_config_data()

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
        ''' return flat configuration settings from file(s) '''
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
        ''' Load YAML Config Files in order, check merge flags, keep origin of settings'''
        pass

    def get_plugin_options(self, plugin_type, name, keys=None, variables=None, direct=None):

        options = {}
        defs = self.get_configuration_definitions(plugin_type, name)
        for option in defs:
            options[option] = self.get_config_value(option, plugin_type=plugin_type, plugin_name=name, keys=keys, variables=variables, direct=direct)

        return options

    def get_plugin_vars(self, plugin_type, name):

        pvars = []
        for pdef in self.get_configuration_definitions(plugin_type, name).values():
            if 'vars' in pdef and pdef['vars']:
                for var_entry in pdef['vars']:
                    pvars.append(var_entry['name'])
        return pvars

    def get_configuration_definition(self, name, plugin_type=None, plugin_name=None):

        ret = {}
        if plugin_type is None:
            ret = self._base_defs.get(name, None)
        elif plugin_name is None:
            ret = self._plugins.get(plugin_type, {}).get(name, None)
        else:
            ret = self._plugins.get(plugin_type, {}).get(plugin_name, {}).get(name, None)

        return ret

    def get_configuration_definitions(self, plugin_type=None, name=None, ignore_private=False):
        ''' just list the possible settings, either base or for specific plugins or plugin '''

        ret = {}
        if plugin_type is None:
            ret = self._base_defs
        elif name is None:
            ret = self._plugins.get(plugin_type, {})
        else:
            ret = self._plugins.get(plugin_type, {}).get(name, {})

        if ignore_private:
            for cdef in list(ret.keys()):
                if cdef.startswith('_'):
                    del ret[cdef]

        return ret

    def _loop_entries(self, container, entry_list):
        ''' repeat code for value entry assignment '''

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
                # inline vault variables should be converted to a text string
                if isinstance(temp_value, AnsibleVaultEncryptedUnicode):
                    temp_value = to_text(temp_value, errors='surrogate_or_strict')

                value = temp_value
                origin = name

                # deal with deprecation of setting source, if used
                if 'deprecated' in entry:
                    self.DEPRECATED.append((entry['name'], entry['deprecated']))

        return value, origin

    def get_config_value(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None, direct=None):
        ''' wrapper '''

        try:
            value, _drop = self.get_config_value_and_origin(config, cfile=cfile, plugin_type=plugin_type, plugin_name=plugin_name,
                                                            keys=keys, variables=variables, direct=direct)
        except AnsibleError:
            raise
        except Exception as e:
            raise AnsibleError("Unhandled exception when retrieving %s:\n%s" % (config, to_native(e)), orig_exc=e)
        return value

    def get_config_value_and_origin(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None, direct=None):
        ''' Given a config key figure out the actual value and report on the origin of the settings '''
        if cfile is None:
            # use default config
            cfile = self._config_file

        # Note: sources that are lists listed in low to high precedence (last one wins)
        value = None
        origin = None

        defs = self.get_configuration_definitions(plugin_type, plugin_name)
        if config in defs:

            aliases = defs[config].get('aliases', [])

            # direct setting via plugin arguments, can set to None so we bypass rest of processing/defaults
            direct_aliases = []
            if direct:
                direct_aliases = [direct[alias] for alias in aliases if alias in direct]
            if direct and config in direct:
                value = direct[config]
                origin = 'Direct'
            elif direct and direct_aliases:
                value = direct_aliases[0]
                origin = 'Direct'

            else:
                # Use 'variable overrides' if present, highest precedence, but only present when querying running play
                if variables and defs[config].get('vars'):
                    value, origin = self._loop_entries(variables, defs[config]['vars'])
                    origin = 'var: %s' % origin

                # use playbook keywords if you have em
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
                    value, origin = self._loop_entries(py3compat.environ, defs[config]['env'])
                    origin = 'env: %s' % origin

                # try config file entries next, if we have one
                if self._parsers.get(cfile, None) is None:
                    self._parse_config_file(cfile)

                if value is None and cfile is not None:
                    ftype = get_config_type(cfile)
                    if ftype and defs[config].get(ftype):
                        if ftype == 'ini':
                            # load from ini config
                            try:  # FIXME: generalize _loop_entries to allow for files also, most of this code is dupe
                                for ini_entry in defs[config]['ini']:
                                    temp_value = get_ini_config_value(self._parsers[cfile], ini_entry)
                                    if temp_value is not None:
                                        value = temp_value
                                        origin = cfile
                                        if 'deprecated' in ini_entry:
                                            self.DEPRECATED.append(('[%s]%s' % (ini_entry['section'], ini_entry['key']), ini_entry['deprecated']))
                            except Exception as e:
                                sys.stderr.write("Error while loading ini config %s: %s" % (cfile, to_native(e)))
                        elif ftype == 'yaml':
                            # FIXME: implement, also , break down key from defs (. notation???)
                            origin = cfile

                # set default if we got here w/o a value
                if value is None:
                    if defs[config].get('required', False):
                        if not plugin_type or config not in INTERNAL_DEFS.get(plugin_type, {}):
                            raise AnsibleError("No setting was provided for required configuration %s" %
                                               to_native(_get_entry(plugin_type, plugin_name, config)))
                    else:
                        value = defs[config].get('default')
                        origin = 'default'
                        # skip typing as this is a templated default that will be resolved later in constants, which has needed vars
                        if plugin_type is None and isinstance(value, string_types) and (value.startswith('{{') and value.endswith('}}')):
                            return value, origin

            # ensure correct type, can raise exceptions on mismatched types
            try:
                value = ensure_type(value, defs[config].get('type'), origin=origin)
            except ValueError as e:
                if origin.startswith('env:') and value == '':
                    # this is empty env var for non string so we can set to default
                    origin = 'default'
                    value = ensure_type(defs[config].get('default'), defs[config].get('type'), origin=origin)
                else:
                    raise AnsibleOptionsError('Invalid type for configuration option %s: %s' %
                                              (to_native(_get_entry(plugin_type, plugin_name, config)), to_native(e)))

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
                    raise AnsibleOptionsError('Invalid value "%s" for configuration option "%s", valid values are: %s' %
                                              (value, to_native(_get_entry(plugin_type, plugin_name, config)), defs[config]['choices']))

            # deal with deprecation of the setting
            if 'deprecated' in defs[config] and origin != 'default':
                self.DEPRECATED.append((config, defs[config].get('deprecated')))
        else:
            raise AnsibleError('Requested entry (%s) was not defined in configuration.' % to_native(_get_entry(plugin_type, plugin_name, config)))

        return value, origin

    def initialize_plugin_configuration_definitions(self, plugin_type, name, defs):

        if plugin_type not in self._plugins:
            self._plugins[plugin_type] = {}

        self._plugins[plugin_type][name] = defs

    def update_config_data(self, defs=None, configfile=None):
        ''' really: update constants '''

        if defs is None:
            defs = self._base_defs

        if configfile is None:
            configfile = self._config_file

        if not isinstance(defs, dict):
            raise AnsibleOptionsError("Invalid configuration definition type: %s for %s" % (type(defs), defs))

        # update the constant for config file
        self.data.update_setting(Setting('CONFIG_FILE', configfile, '', 'string'))

        origin = None
        # env and config defs can have several entries, ordered in list from lowest to highest precedence
        for config in defs:
            if not isinstance(defs[config], dict):
                raise AnsibleOptionsError("Invalid configuration definition '%s': type is %s" % (to_native(config), type(defs[config])))

            # get value and origin
            try:
                value, origin = self.get_config_value_and_origin(config, configfile)
            except Exception as e:
                # Printing the problem here because, in the current code:
                # (1) we can't reach the error handler for AnsibleError before we
                #     hit a different error due to lack of working config.
                # (2) We don't have access to display yet because display depends on config
                #     being properly loaded.
                #
                # If we start getting double errors printed from this section of code, then the
                # above problem #1 has been fixed.  Revamp this to be more like the try: except
                # in get_config_value() at that time.
                sys.stderr.write("Unhandled error:\n %s\n\n" % traceback.format_exc())
                raise AnsibleError("Invalid settings supplied for %s: %s\n" % (config, to_native(e)), orig_exc=e)

            # set the constant
            self.data.update_setting(Setting(config, value, origin, defs[config].get('type', 'string')))
