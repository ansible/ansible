# Copyright 2018, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import contextlib
import copy
import os
import stat
import warnings

import ansible.module_utils.six as six
from ansible.module_utils.six.moves import configparser
from ansible.module_utils.six import StringIO

try:
    from collections import OrderedDict  # NOQA
except ImportError:  # Python < 2.7
    from ordereddict import OrderedDict  # NOQA

__all__ = ['settings', 'with_global_options', 'pop_option']


tower_dir = '/etc/tower/'
user_dir = os.path.expanduser('~')
CONFIG_FILENAME = '.tower_cli.cfg'
CONFIG_OPTIONS = frozenset((
    'host', 'username', 'password', 'verify_ssl', 'format',
    'color', 'verbose', 'description_on', 'certificate',
    'use_token', 'oauth_token'
))


class Parser(configparser.ConfigParser):
    """ConfigParser subclass that doesn't strictly require section
    headers.
    """
    def _read(self, fp, fpname):
        """Read the configuration from the given file.

        If the file lacks any section header, add a [general] section
        header that encompasses the whole thing.
        """
        # Attempt to read the file using the superclass implementation.
        #
        # Check the permissions of the file we are considering reading
        # if the file exists and the permissions expose it to reads from
        # other users, raise a warning
        if os.path.isfile(fpname):
            file_permission = os.stat(fpname)
            if fpname != os.path.join(tower_dir, 'tower_cli.cfg') and (
                (file_permission.st_mode & stat.S_IRGRP) or
                (file_permission.st_mode & stat.S_IROTH)
            ):
                warnings.warn('File {0} readable by group or others.'
                              .format(fpname), RuntimeWarning)
        # If it doesn't work because there's no section header, then
        # create a section header and call the superclass implementation
        # again.
        try:
            return configparser.ConfigParser._read(self, fp, fpname)
        except configparser.MissingSectionHeaderError:
            fp.seek(0)
            string = '[general]\n%s' % fp.read()
            flo = StringIO(string)  # flo == file-like object
            return configparser.ConfigParser._read(self, flo, fpname)


class Settings(object):
    """A class that understands configurations provided to tower-cli through configuration files
    or runtime parameters. A signleton object ``tower_cli.conf.settings`` will be instantiated and used.

    The 5 levels of precedence for settings, listing from least to greatest, are:

        - defaults: Default values provided
        - global: Contents parsed from .ini-formatted file ``/etc/tower/tower_cli.cfg`` if exists.
        - user: Contents parsed from .ini-formatted file ``~/.tower_cli.cfg`` if exists.
        - local: Contents parsed from .ini-formatted file ``.tower_cli.cfg`` if exists in the present working
          directory or any parent directories.
        - environment: Values from magic environment variables.
        - runtime: keyworded arguments provided by ``settings.runtime_values`` context manager.

    Note that .ini configuration file should follow the specified format in order to be correctly parsed:

    .. code-block:: bash

       [general]
       <configuration name 1> = <value 1>
       <configuration name 2> = <value 2>
       ...

    """
    _parser_names = ['runtime', 'environment', 'local', 'user', 'global', 'defaults']

    @staticmethod
    def _new_parser(defaults=None):
        if defaults:
            p = Parser(defaults=defaults)
        else:
            p = Parser()
        p.add_section('general')
        return p

    def __init__(self):
        """Create the settings object, and read from appropriate files as
        well as from `sys.argv`.
        """
        self._cache = {}

        # Initialize the data dictionary for the default level
        # precedence (that is, the bottom of the totem pole).
        defaults = {}
        for key in CONFIG_OPTIONS:
            defaults[key] = ''
        defaults.update({
            'color': 'true',
            'format': 'human',
            'host': '127.0.0.1',
            'verify_ssl': 'true',
            'verbose': 'false',
            'description_on': 'false',
            'use_token': 'false',
        })
        self._defaults = self._new_parser(defaults=defaults)

        # environment variables as defaults
        self._environment = self._new_parser(defaults=config_from_environment())

        # If there is a global settings file, initialize it.
        self._global = self._new_parser()
        if os.path.isdir(tower_dir):
            # Sanity check: Try to get a list of files in `/etc/tower/`.
            #
            # The default Tower installation caused `/etc/tower/` to have
            # extremely restrictive permissions, since it has its own user
            # and group and has a chmod of 0750.
            #
            # This makes it very easy for a user to fall into the mistake
            # of writing a config file under sudo which they then cannot read,
            # which could lead to difficult-to-troubleshoot situations.
            #
            # Therefore, check for that particular problem and give a warning
            # if we're in that situation.
            try:
                os.listdir(tower_dir)
            except OSError:
                warnings.warn('/etc/tower/ is present, but not readable with '
                              'current permissions. Any settings defined in '
                              '/etc/tower/tower_cli.cfg will not be honored.',
                              RuntimeWarning)

            # If there is a global settings file for Tower CLI, read in its
            # contents.
            self._global.read(os.path.join(tower_dir, 'tower_cli.cfg'))

        # Initialize a parser for the user settings file.
        self._user = self._new_parser()

        # If there is a user settings file, read it into the parser object.
        user_filename = os.path.join(user_dir, CONFIG_FILENAME)
        self._user.read(user_filename)

        # Initialize a parser for the local settings file.
        self._local = self._new_parser()

        # If there is a local settings file in the current working directory
        # or any parent, read it into the parser object.
        local_dir = os.getcwd()
        local_dirs = [local_dir] if local_dir not in (user_dir, tower_dir) else []

        # Loop while there are 2 parts to local_dir
        while os.path.split(local_dir)[1]:

            # Switch to parent of this directory
            local_dir, dummy = os.path.split(local_dir)

            # Sanity check: if this directory corresponds to our global or
            # user directory, skip it.
            if local_dir not in (user_dir, tower_dir):
                local_dirs = [local_dir] + local_dirs

        # Iterate over each potential local config file and attempt to read
        # it (most won't exist, which is fine).
        for local_dir in local_dirs:
            local_filename = os.path.join(local_dir, CONFIG_FILENAME)
            self._local.read(local_filename)

        # Put a stubbed runtime parser in.
        self._runtime = self._new_parser()

    def __getattr__(self, key):
        """Return the approprate value, intelligently type-casted in the
        case of numbers or booleans.
        """
        # Sanity check: Have I cached this value? If so, return that.
        if key in self._cache:
            return self._cache[key]

        # Run through each of the parsers and check for a value. Whenever
        # we actually find a value, try to determine the correct type for it
        # and cache and return a value of that type.
        for parser in self._parsers:
            # Get the value from this parser; if it's None, then this
            # key isn't present and we move on to the next one.
            try:
                value = parser.get('general', key)
            except configparser.NoOptionError:
                continue

            # We have a value; it may or may not be a string, though, so
            # try to return it as an int, float, or boolean (in that order)
            # before falling back to the string value.
            type_method = ('getint', 'getfloat', 'getboolean')
            for tm in type_method:
                try:
                    value = getattr(parser, tm)('general', key)
                    break
                except ValueError:
                    pass

            # Write the value to the cache, so we don't have to do this lookup
            # logic on subsequent requests.
            self._cache[key] = value
            return self._cache[key]

        # If we got here, that means that the attribute wasn't found, and
        # also that there is no default; raise an exception.
        raise AttributeError('No setting exists: %s.' % key.lower())

    @property
    def _parsers(self):
        """Return a tuple of all parsers, in order.

        This is referenced at runtime, to avoid gleefully ignoring the
        `runtime_values` context manager.
        """
        return tuple([getattr(self, '_%s' % i) for i in self._parser_names])

    def set_or_reset_runtime_param(self, key, value):
        """Maintains the context of the runtime settings for invoking
        a command.

        This should be called by a click.option callback, and only
        called once for each setting for each command invocation.

        If the setting exists, it follows that the runtime settings are
        stale, so the entire runtime settings are reset.
        """
        if self._runtime.has_option('general', key):
            self._runtime = self._new_parser()

        if value is None:
            return
        settings._runtime.set('general', key.replace('tower_', ''),
                              six.text_type(value))

    @contextlib.contextmanager
    def runtime_values(self, **kwargs):
        """
        =====API DOCS=====
        Context manager that temporarily override runtime level configurations.

        :param kwargs: Keyword arguments specifying runtime configuration settings.
        :type kwargs: arbitrary keyword arguments
        :returns: N/A

        :Example:

        >>> import tower_cli
        >>> from tower_cli.conf import settings
        >>> with settings.runtime_values(username='user', password='pass'):
        >>>     print(tower_cli.get_resource('credential').list())

        =====API DOCS=====
        """

        # Coerce all values to strings (to be coerced back by configparser
        # later) and defenestrate any None values.
        for k, v in copy.copy(kwargs).items():
            # If the value is None, just get rid of it.
            if v is None:
                kwargs.pop(k)
                continue

            # Remove these keys from the cache, if they are present.
            self._cache.pop(k, None)

            # Coerce values to strings.
            kwargs[k] = six.text_type(v)

        # Replace the `self._runtime` INI parser with a new one, using
        # the context manager's kwargs as the "defaults" (there can never
        # be anything other than defaults, but that isn't a problem for our
        # purposes because we're using our own precedence system).
        #
        # Ensure that everything is put back to rights at the end of the
        # context manager call.
        old_runtime_parser = self._runtime
        try:
            self._runtime = Parser(defaults=kwargs)
            self._runtime.add_section('general')
            yield self
        finally:
            # Revert the runtime configparser object.
            self._runtime = old_runtime_parser

            # Remove the keys from the cache again, since the settings
            # have been reverted.
            for key in kwargs:
                self._cache.pop(k, None)


def config_from_environment():
    """Read tower-cli config values from the environment if present, being
    careful not to override config values that were explicitly passed in.
    """
    kwargs = {}
    for k in CONFIG_OPTIONS:
        env = 'TOWER_' + k.upper()
        v = os.getenv(env, None)
        if v is not None:
            kwargs[k] = v
    return kwargs


def supports_oauth():
    # Import here to avoid a circular import
    from ansible.module_utils.web_infrastructure.ansible_tower.api import client
    try:
        resp = client.head('/o/')
    except exceptions.NotFound:
        return False
    return resp.ok


class OrderedDict(OrderedDict):
    """OrderedDict subclass that nonetheless uses the basic dictionary
    __repr__ method.
    """
    def __repr__(self):
        """Print a repr that resembles dict's repr, but preserves
        key order.
        """
        return '{' + ', '.join(['%r: %r' % (k, v)
                                for k, v in self.items()]) + '}'


def string_to_dict(var_string, allow_kv=True, require_dict=True):
    """Returns a dictionary given a string with yaml or json syntax.
    If data is not present in a key: value format, then it return
    an empty dictionary.

    Attempts processing string by 3 different methods in order:
        1. as JSON      2. as YAML      3. as custom key=value syntax
    Throws an error if all of these fail in the standard ways."""
    # try:
    #     # Accept all valid "key":value types of json
    #     return_dict = json.loads(var_string)
    #     assert type(return_dict) is dict
    # except (TypeError, AttributeError, ValueError, AssertionError):
    try:
        # Accept all JSON and YAML
        return_dict = yaml.load(var_string)
        if require_dict:
            assert type(return_dict) is dict
    except (AttributeError, yaml.YAMLError, AssertionError):
        # if these fail, parse by key=value syntax
        try:
            assert allow_kv
            return_dict = parse_kv(var_string)
        except Exception:
            raise exc.TowerCLIError(
                'failed to parse some of the extra '
                'variables.\nvariables: \n%s' % var_string
            )
    return return_dict


# The primary way to interact with settings is to simply hit the
# already constructed settings object.
settings = Settings()
