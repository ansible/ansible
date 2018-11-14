# Copyright 2018, Ansible, Inc.
# Alan Rominger <arominger@ansible.com>
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

import yaml
import click

import ast
import shlex
import functools
import six


from ansible.module_utils.web_infrastructure.ansible_tower import exceptions as exc
from ansible.module_utils.web_infrastructure.ansible_tower.conf import settings

try:
    from collections import OrderedDict  # NOQA
except ImportError:  # Python < 2.7
    from ordereddict import OrderedDict  # NOQA

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# Import simplejson if we have it (Python 2.6), and use json from the
# standard library otherwise.
#
# Note: Python 2.6 does have a JSON library, but it lacks `object_pairs_hook`
# as a keyword argument to `json.loads`, so we still need simplejson on
# Python 2.6.
import sys
if sys.version_info < (2, 7):
    import simplejson as json  # NOQA
else:
    import json  # NOQA


@functools.wraps(click.secho)
def secho(message, **kwargs):
    """A wrapper around click.secho that disables any coloring being used
    if colors have been disabled.
    """
    # If colors are disabled, remove any color or other style data
    # from keyword arguments.
    if not settings.color:
        for key in ('fg', 'bg', 'bold', 'blink'):
            kwargs.pop(key, None)

    # Okay, now call click.secho normally.
    return click.secho(message, **kwargs)


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


def parse_kv(var_string):
    """Similar to the Ansible function of the same name, parses file
    with a key=value pattern and stores information in a dictionary,
    but not as fully featured as the corresponding Ansible code."""
    return_dict = {}

    # Output updates dictionaries, so return empty one if no vals in
    if var_string is None:
        return {}

    # Python 2.6 / shlex has problems handling unicode, this is a fix
    fix_encoding_26 = False
    if sys.version_info < (2, 7) and '\x00' in shlex.split(u'a')[0]:
        fix_encoding_26 = True

    # Also hedge against Click library giving non-string type
    is_unicode = False
    if fix_encoding_26 or not isinstance(var_string, str):
        if isinstance(var_string, six.text_type):
            var_string = var_string.encode('UTF-8')
            is_unicode = True
        else:
            var_string = str(var_string)

    # Use shlex library to split string by quotes, whitespace, etc.
    for token in shlex.split(var_string):

        # Second part of fix to avoid passing shlex unicode in py2.6
        if (is_unicode):
            token = token.decode('UTF-8')
        if fix_encoding_26:
            token = six.text_type(token)
        # Look for key=value pattern, if not, process as raw parameter
        if '=' in token:
            (k, v) = token.split('=', 1)
            # If '=' are unbalanced, then stop and warn user
            if len(k) == 0 or len(v) == 0:
                raise Exception
            # If possible, convert into python data type, for instance "5"->5
            try:
                return_dict[k] = ast.literal_eval(v)
            except Exception:
                return_dict[k] = v
        else:
            # scenario where --extra-vars=42, will throw error
            raise Exception

    return return_dict


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


def process_extra_vars(extra_vars_list, force_json=True):
    """Returns a string that is valid JSON or YAML and contains all the
    variables in every extra_vars_opt inside of extra_vars_list.

    Args:
       parse_kv (bool): whether to allow key=value syntax.
       force_json (bool): if True, always output json.
    """
    # Read from all the different sources and put into dictionary
    extra_vars = {}
    extra_vars_yaml = ""
    for extra_vars_opt in extra_vars_list:
        # Load file content if necessary
        if extra_vars_opt.startswith("@"):
            with open(extra_vars_opt[1:], 'r') as f:
                extra_vars_opt = f.read()
            # Convert text markup to a dictionary conservatively
            opt_dict = string_to_dict(extra_vars_opt, allow_kv=False)
        else:
            # Convert text markup to a dictionary liberally
            opt_dict = string_to_dict(extra_vars_opt, allow_kv=True)
        # Rolling YAML-based string combination
        if any(line.startswith("#") for line in extra_vars_opt.split('\n')):
            extra_vars_yaml += extra_vars_opt + "\n"
        elif extra_vars_opt != "":
            extra_vars_yaml += yaml.dump(
                opt_dict, default_flow_style=False) + "\n"
        # Combine dictionary with cumulative dictionary
        extra_vars.update(opt_dict)

    # Return contents in form of a string
    if not force_json:
        try:
            # Conditions to verify it is safe to return rolling YAML string
            try_dict = yaml.load(extra_vars_yaml)
            assert type(try_dict) is dict
            display.vvvv('Using unprocessed YAML', header='decision', nl=2)
            return extra_vars_yaml.rstrip()
        except Exception:
            display.vvvv('Failed YAML parsing, defaulting to JSON', header='decison', nl=2)
    if extra_vars == {}:
        return ""
    return json.dumps(extra_vars, ensure_ascii=False)


def ordered_dump(data, Dumper=yaml.Dumper, **kws):
    """Expand PyYAML's built-in dumper to support parsing OrderedDict. Return
    a string as parse result of the original data structure, which includes
    OrderedDict.

    Args:
        data: the data structure to be dumped(parsed) which is supposed to
        contain OrderedDict.
        Dumper: the yaml serializer to be expanded and used.
        kws: extra key-value arguments to be passed to yaml.dump.
    """
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())
    OrderedDumper.add_representer(OrderedDict,
                                  _dict_representer)
    return yaml.dump(data, None, OrderedDumper, **kws)
