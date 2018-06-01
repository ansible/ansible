# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import tempfile

from collections import namedtuple

from yaml import load as yaml_load
try:
    # use C version if possible for speedup
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

from ansible.config.data import ConfigData
from ansible.errors import AnsibleOptionsError, AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.quoting import unquote
from ansible.utils.path import unfrackpath
from ansible.utils.path import makedirs_safe

Plugin = namedtuple('Plugin', 'name type')
Setting = namedtuple('Setting', 'name value origin type')


# FIXME: see if we can unify in module_utils with similar function used by argspec
def ensure_type(value, value_type, origin=None):
    ''' return a configuration variable with casting
    :arg value: The value to ensure correct typing of
    :kwarg value_type: The type of the value.  This can be any of the following strings:
        :boolean: sets the value to a True or False value
        :integer: Sets the value to an integer or raises a ValueType error
        :float: Sets the value to a float or raises a ValueType error
        :list: Treats the value as a comma separated list.  Split the value
            and return it as a python list.
        :none: Sets the value to None
        :path: Expands any environment variables and tilde's in the value.
        :tmp_path: Create a unique temporary directory inside of the directory
            specified by value and return its path.
        :pathlist: Treat the value as a typical PATH string.  (On POSIX, this
            means colon separated strings.)  Split the value and then expand
            each part for environment variables and tildes.
    '''

    basedir = None
    if origin and os.path.isabs(origin) and os.path.exists(origin):
        basedir = origin

    if value_type:
        value_type = value_type.lower()

    if value_type in ('boolean', 'bool'):
        value = boolean(value, strict=False)

    elif value is not None:
        if value_type in ('integer', 'int'):
            value = int(value)

        elif value_type == 'float':
            value = float(value)

        elif value_type == 'list':
            if isinstance(value, string_types):
                value = [x.strip() for x in value.split(',')]

        elif value_type == 'none':
            if value == "None":
                value = None

        elif value_type == 'path':
            value = resolve_path(value, basedir=basedir)

        elif value_type in ('tmp', 'temppath', 'tmppath'):
            value = resolve_path(value, basedir=basedir)
            if not os.path.exists(value):
                makedirs_safe(value, 0o700)
            prefix = 'ansible-local-%s' % os.getpid()
            value = tempfile.mkdtemp(prefix=prefix, dir=value)

        elif value_type == 'pathspec':
            if isinstance(value, string_types):
                value = value.split(os.pathsep)
            value = [resolve_path(x, basedir=basedir) for x in value]

        elif value_type == 'pathlist':
            if isinstance(value, string_types):
                value = value.split(',')
            value = [resolve_path(x, basedir=basedir) for x in value]

        # defaults to string types
        elif isinstance(value, string_types):
            value = unquote(value)

    return to_text(value, errors='surrogate_or_strict', nonstring='passthru')


# FIXME: see if this can live in utils/path
def resolve_path(path, basedir=None):
    ''' resolve relative or 'varaible' paths '''
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


def find_ini_config_file():
    ''' Load INI Config File order(first found is used): ENV, CWD, HOME, /etc/ansible '''
    # FIXME: eventually deprecate ini configs

    path0 = os.getenv("ANSIBLE_CONFIG", None)
    if path0 is not None:
        path0 = unfrackpath(path0, follow=False)
        if os.path.isdir(path0):
            path0 += "/ansible.cfg"
    try:
        path1 = os.getcwd() + "/ansible.cfg"
    except OSError:
        path1 = None
    path2 = unfrackpath("~/.ansible.cfg", follow=False)
    path3 = "/etc/ansible/ansible.cfg"

    for path in [path0, path1, path2, path3]:
        if path is not None and os.path.exists(path):
            break
    else:
        path = None

    return path


class ConfigManager(object):

    UNABLE = {}
    DEPRECATED = []

    def __init__(self, conf_file=None, defs_file=None):

        self._base_defs = {}
        self._plugins = {}
        self._parsers = {}

        self._config_file = conf_file
        self.data = ConfigData()

        if defs_file is None:
            # Create configuration definitions from source
            b_defs_file = to_bytes('%s/base.yml' % os.path.dirname(__file__))
        else:
            b_defs_file = to_bytes(defs_file)

        # consume definitions
        if os.path.exists(b_defs_file):
            with open(b_defs_file, 'rb') as config_def:
                self._base_defs = yaml_load(config_def, Loader=SafeLoader)
        else:
            raise AnsibleError("Missing base configuration definition file (bad install?): %s" % to_native(b_defs_file))

        if self._config_file is None:
            # set config using ini
            self._config_file = find_ini_config_file()

        # consume configuration
        if self._config_file:
            if os.path.exists(self._config_file):
                # initialize parser and read config
                self._parse_config_file()

        # update constants
        self.update_config_data()

    def _parse_config_file(self, cfile=None):
        ''' return flat configuration settings from file(s) '''
        # TODO: take list of files with merge/nomerge

        if cfile is None:
            cfile = self._config_file

        ftype = get_config_type(cfile)
        if cfile is not None:
            if ftype == 'ini':
                self._parsers[cfile] = configparser.ConfigParser()
                try:
                    self._parsers[cfile].read(cfile)
                except configparser.Error as e:
                    raise AnsibleOptionsError("Error reading config file (%s): %s" % (cfile, to_native(e)))
            # FIXME: this should eventually handle yaml config files
            # elif ftype == 'yaml':
            #     with open(cfile, 'rb') as config_stream:
            #         self._parsers[cfile] = yaml.safe_load(config_stream)
            else:
                raise AnsibleOptionsError("Unsupported configuration file type: %s" % to_native(ftype))

    def _find_yaml_config_files(self):
        ''' Load YAML Config Files in order, check merge flags, keep origin of settings'''
        pass

    def get_plugin_options(self, plugin_type, name, keys=None, variables=None):

        options = {}
        defs = self.get_configuration_definitions(plugin_type, name)
        for option in defs:
            options[option] = self.get_config_value(option, plugin_type=plugin_type, plugin_name=name, keys=keys, variables=variables)

        return options

    def get_plugin_vars(self, plugin_type, name):

        pvars = []
        for pdef in self.get_configuration_definitions(plugin_type, name).values():
            if 'vars' in pdef and pdef['vars']:
                for var_entry in pdef['vars']:
                    pvars.append(var_entry['name'])
        return pvars

    def get_configuration_definitions(self, plugin_type=None, name=None):
        ''' just list the possible settings, either base or for specific plugins or plugin '''

        ret = {}
        if plugin_type is None:
            ret = self._base_defs
        elif name is None:
            ret = self._plugins.get(plugin_type, {})
        else:
            ret = self._plugins.get(plugin_type, {}).get(name, {})

        return ret

    def _loop_entries(self, container, entry_list):
        ''' repeat code for value entry assignment '''

        value = None
        origin = None
        for entry in entry_list:
            name = entry.get('name')
            temp_value = container.get(name, None)
            if temp_value is not None:  # only set if env var is defined
                value = temp_value
                origin = name

                # deal with deprecation of setting source, if used
                if 'deprecated' in entry:
                    self.DEPRECATED.append((entry['name'], entry['deprecated']))

        return value, origin

    def get_config_value(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None):
        ''' wrapper '''

        try:
            value, _drop = self.get_config_value_and_origin(config, cfile=cfile, plugin_type=plugin_type, plugin_name=plugin_name,
                                                            keys=keys, variables=variables)
        except Exception as e:
            raise AnsibleError("Invalid settings supplied for %s: %s" % (config, to_native(e)))
        return value

    def get_config_value_and_origin(self, config, cfile=None, plugin_type=None, plugin_name=None, keys=None, variables=None):
        ''' Given a config key figure out the actual value and report on the origin of the settings '''

        if cfile is None:
            # use default config
            cfile = self._config_file

        # Note: sources that are lists listed in low to high precedence (last one wins)
        value = None
        origin = None
        defs = {}
        if plugin_type is None:
            defs = self._base_defs
        elif plugin_name is None:
            defs = self._plugins[plugin_type]
        else:
            defs = self._plugins[plugin_type][plugin_name]

        if config in defs:
            # Use 'variable overrides' if present, highest precedence, but only present when querying running play
            if variables and defs[config].get('vars'):
                value, origin = self._loop_entries(variables, defs[config]['vars'])
                origin = 'var: %s' % origin

            # use playbook keywords if you have em
            if value is None and keys:
                value, origin = self._loop_entries(keys, defs[config]['keywords'])
                origin = 'keyword: %s' % origin

            # env vars are next precedence
            if value is None and defs[config].get('env'):
                value, origin = self._loop_entries(os.environ, defs[config]['env'])
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
                    entry = ''
                    if plugin_type:
                        entry += 'plugin_type: %s ' % plugin_type
                        if plugin_name:
                            entry += 'plugin: %s ' % plugin_name
                    entry += 'setting: %s ' % config
                    raise AnsibleError("No setting was provided for required configuration %s" % (entry))
                else:
                    value = defs[config].get('default')
                    origin = 'default'
                    # skip typing as this is a temlated default that will be resolved later in constants, which has needed vars
                    if plugin_type is None and isinstance(value, string_types) and (value.startswith('{{') and value.endswith('}}')):
                        return value, origin

            # ensure correct type, can raise exceptoins on mismatched types
            value = ensure_type(value, defs[config].get('type'), origin=origin)

            # deal with deprecation of the setting
            if 'deprecated' in defs[config] and origin != 'default':
                self.DEPRECATED.append((config, defs[config].get('deprecated')))
        else:
            raise AnsibleError('Requested option %s was not defined in configuration' % to_native(config))

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
                # when building constants.py we ignore invalid configs
                # CLI takes care of warnings once 'display' is loaded
                self.UNABLE[config] = to_text(e)
                continue

            # set the constant
            self.data.update_setting(Setting(config, value, origin, defs[config].get('type', 'string')))
