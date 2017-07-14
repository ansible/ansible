# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import tempfile
import yaml

from ansible.config.data import ConfigData, Setting
from ansible.errors import AnsibleOptionsError, AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.quoting import unquote
from ansible.utils.path import unfrackpath
from ansible.utils.path import makedirs_safe


def resolve_path(path):

    if '{{CWD}}' in path: # allow users to force CWD using 'magic' {{CWD}}
        path = path.replace('{{CWD}}', os.getcwd())

    return unfrackpath(path, follow=False)


def get_ini_config(p, entries):
    ''' returns the value of last ini entry found '''
    value = None
    if p is not None:
        for entry in entries:
            try:
                value = p.get(entry.get('section','defaults'), entry.get('key',''), raw=True)
            except:
                pass

    return value


class ConfigManager(object):

    def __init__(self, conf_file=None):

        self.data = ConfigData()

        #FIXME: make dynamic?
        bconfig_def = to_bytes('%s/data/config.yml' % os.path.dirname(__file__))
        if os.path.exists(bconfig_def):
            with open(bconfig_def, 'rb') as config_def:
                self.initial_defs = yaml.safe_load(config_def)
        else:
            raise AnsibleError("Missing base configuration definition file (bad install?): %s" % to_native(bconfig_def))

        ftype = None
        if conf_file is None:
            # set config using ini
            conf_file = self.find_ini_config_file()
            ftype = 'ini'
        else:
            ext = os.path.splitext(conf_file)[-1]
            if ext in ('.ini', '.cfg'):
                ftype = 'ini'
            elif ext in ('.yaml', '.yml'):
                ftype = 'yaml'
            else:
                raise AnsibleOptionsError("Unsupported configuration file extension: \n{0}".format(ext))

        self.parse_config(conf_file, ftype)

    def parse_config(self, cfile, ftype):
        # TODO: take list of files with merge/nomerge

        parser = None
        if cfile:
            if ftype == 'ini':
                parser = configparser.ConfigParser()
                try:
                    parser.read(cfile)
                except configparser.Error as e:
                    raise AnsibleOptionsError("Error reading config file: \n{0}".format(e))
            elif ftype == 'yaml':
                with open(cfile, 'rb') as config_stream:
                    parser = yaml.safe_load(config_stream)
            else:
                raise AnsibleOptionsError("Unsupported configuration file type: \n{0}".format(ftype))

        self.update_config(cfile, self.initial_defs, parser, ftype)

    def update_config(self, configfile, defs, parser, ftype):

        # update the constant for config file
        self.data.update_setting(Setting('CONFIG_FILE', configfile, ''))

        origin = None
        # env and config defs can have several entries, ordered in list from lowest to highest precedence
        for config in self.initial_defs:

            value = None
            # env vars are highest precedence
            if defs[config].get('env'):
                try:
                    for env_var in defs[config]['env']:
                        env_value = os.environ.get(env_var.get('name'), None)
                        if env_value is not None: # only set if env var is defined
                            value = env_value
                            origin = 'env: %s' % env_var.get('name')
                except:
                    sys.stderr.write("Error while loading environment configs for %s\n" % config)

            # try config file entries next
            if value is None and defs[config].get(ftype):
                if ftype == 'ini':
                    # load from ini config
                    try:
                        value = get_ini_config(parser, defs[config]['ini'])
                        origin = configfile
                    except Exception as e:
                        sys.stderr.write("Error while loading ini config %s: %s" % (configfile, str(e)))
                elif ftype == 'yaml':
                    # FIXME: break down key from defs (. notation???)
                    key = 'name'
                    value = parser.get(key)
                    origin = configfile

            # set default if we got here w/o a value
            if value is None:
                value = defs[config].get('default')
                origin = 'default'

            # ensure correct type
            try:
                value = self.ensure_type(value, defs[config].get('value_type'))
            except:
                sys.stderr.write("Unable to set correct type for %s, skipping" %  config)
                continue

            # set the constant
            self.data.update_setting(Setting(config, value, origin))


    def find_ini_config_file(self):
        ''' Load Config File order(first found is used): ENV, CWD, HOME, /etc/ansible '''

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

    def ensure_type(self, value, value_type):
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
        if value_type == 'boolean':
            value = boolean(value, strict=False)

        elif value:
            if value_type == 'integer':
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
                value = resolve_path(value)

            elif value_type == 'tmppath':
                value = resolve_path(value)
                if not os.path.exists(value):
                    makedirs_safe(value, 0o700)
                prefix = 'ansible-local-%s' % os.getpid()
                value = tempfile.mkdtemp(prefix=prefix, dir=value)

            elif value_type == 'pathlist':
                if isinstance(value, string_types):
                    value = [resolve_path(x) for x in value.split(os.pathsep)]

            elif isinstance(value, string_types):
                value = unquote(value)

        return to_text(value, errors='surrogate_or_strict', nonstring='passthru')

