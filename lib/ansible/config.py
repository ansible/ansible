# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
import tempfile

from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types
from ansible.parsing.quoting import unquote
from ansible.utils.path import makedirs_safe


BOOL_TRUE = frozenset(["true", "t", "y", "1", "yes", "on"])


def mk_boolean(value):
    ret = value
    if not isinstance(value, bool):
        if value is None:
            ret = False
        ret = (str(value).lower() in BOOL_TRUE)
    return ret


def shell_expand(path, expand_relative_paths=False, topdir=None):
    '''
    shell_expand is needed as os.path.expanduser does not work
    when path is None, which is the default for ANSIBLE_PRIVATE_KEY_FILE
    '''
    if path:
        path = os.path.expanduser(os.path.expandvars(path))
        if expand_relative_paths and not path.startswith('/'):
            # paths are always 'relative' to the config?
            if topdir:
                path = os.path.join(topdir, path)
            path = os.path.abspath(path)
    return path


def get_config(p, section, key, env_var, default, value_type=None, expand_relative_paths=False, topdir=None):
    ''' return a configuration variable with casting

    :arg p: A ConfigParser object to look for the configuration in
    :arg section: A section of the ini config that should be examined for this section.
    :arg key: The config key to get this config from
    :arg env_var: An Environment variable to check for the config var.  If
        this is set to None then no environment variable will be used.
    :arg default: A default value to assign to the config var if nothing else sets it.
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
    :kwarg expand_relative_paths: for pathlist and path types, if this is set
        to True then also change any relative paths into absolute paths.  The
        default is False.
    '''
    value = _get_config(p, section, key, env_var, default)
    if value_type == 'boolean':
        value = mk_boolean(value)

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
            value = shell_expand(value, expand_relative_paths=expand_relative_paths, topdir=topdir)

        elif value_type == 'tmppath':
            value = shell_expand(value, topdir=topdir)
            if not os.path.exists(value):
                makedirs_safe(value, 0o700)
            prefix = 'ansible-local-%s' % os.getpid()
            value = tempfile.mkdtemp(prefix=prefix, dir=value)

        elif value_type == 'pathlist':
            if isinstance(value, string_types):
                value = [shell_expand(x, expand_relative_paths=expand_relative_paths, topdir=topdir) for x in value.split(os.pathsep)]

        elif isinstance(value, string_types):
            value = unquote(value)

    return to_text(value, errors='surrogate_or_strict', nonstring='passthru')


def _get_config(p, section, key, env_var, default):
    ''' helper function for get_config '''
    value = default

    if p is not None:
        try:
            value = p.get(section, key, raw=True)
        except:
            pass

    if env_var is not None:
        env_value = os.environ.get(env_var, None)
        if env_value is not None:
            value = env_value

    return to_text(value, errors='surrogate_or_strict', nonstring='passthru')
