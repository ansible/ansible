# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com> 2016
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

SIZE_RANGES = {
    'Y': 1 << 80,
    'Z': 1 << 70,
    'E': 1 << 60,
    'P': 1 << 50,
    'T': 1 << 40,
    'G': 1 << 30,
    'M': 1 << 20,
    'K': 1 << 10,
    'B': 1,
}

FILE_ATTRIBUTES = {
    'A': 'noatime',
    'a': 'append',
    'c': 'compressed',
    'C': 'nocow',
    'd': 'nodump',
    'D': 'dirsync',
    'e': 'extents',
    'E': 'encrypted',
    'h': 'blocksize',
    'i': 'immutable',
    'I': 'indexed',
    'j': 'journalled',
    'N': 'inline',
    's': 'zero',
    'S': 'synchronous',
    't': 'notail',
    'T': 'blockroot',
    'u': 'undelete',
    'X': 'compressedraw',
    'Z': 'compresseddirty',
}

# ansible modules can be written in any language.  To simplify
# development of Python modules, the functions available here can
# be used to do many common tasks

import locale
import os
import re
import shlex
import subprocess
import sys
import types
import time
import select
import shutil
import stat
import tempfile
import traceback
import grp
import pwd
import platform
import errno
import datetime
from collections import deque
from collections import Mapping, MutableMapping, Sequence, MutableSequence, Set, MutableSet
from itertools import chain, repeat

try:
    import syslog
    HAS_SYSLOG = True
except ImportError:
    HAS_SYSLOG = False

try:
    from systemd import journal
    has_journal = True
except ImportError:
    has_journal = False

HAVE_SELINUX = False
try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    pass

# Python2 & 3 way to get NoneType
NoneType = type(None)

# Note: When getting Sequence from collections, it matches with strings.  If
# this matters, make sure to check for strings before checking for sequencetype
try:
    from collections.abc import KeysView
    SEQUENCETYPE = (Sequence, frozenset, KeysView)
except:
    SEQUENCETYPE = (Sequence, frozenset)

try:
    import json
    # Detect the python-json library which is incompatible
    # Look for simplejson if that's the case
    try:
        if not isinstance(json.loads, types.FunctionType) or not isinstance(json.dumps, types.FunctionType):
            raise ImportError
    except AttributeError:
        raise ImportError
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        print('\n{"msg": "Error: ansible requires the stdlib json or simplejson module, neither was found!", "failed": true}')
        sys.exit(1)
    except SyntaxError:
        print('\n{"msg": "SyntaxError: probably due to installed simplejson being for a different python version", "failed": true}')
        sys.exit(1)
    else:
        sj_version = json.__version__.split('.')
        if sj_version < ['1', '6']:
            # Version 1.5 released 2007-01-18 does not have the encoding parameter which we need
            print('\n{"msg": "Error: Ansible requires the stdlib json or simplejson >= 1.6.  Neither was found!", "failed": true}')

AVAILABLE_HASH_ALGORITHMS = dict()
try:
    import hashlib

    # python 2.7.9+ and 2.7.0+
    for attribute in ('available_algorithms', 'algorithms'):
        algorithms = getattr(hashlib, attribute, None)
        if algorithms:
            break
    if algorithms is None:
        # python 2.5+
        algorithms = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
    for algorithm in algorithms:
        AVAILABLE_HASH_ALGORITHMS[algorithm] = getattr(hashlib, algorithm)
except ImportError:
    import sha
    AVAILABLE_HASH_ALGORITHMS = {'sha1': sha.sha}
    try:
        import md5
        AVAILABLE_HASH_ALGORITHMS['md5'] = md5.md5
    except ImportError:
        pass

from ansible.module_utils.pycompat24 import get_exception, literal_eval
from ansible.module_utils.six import (
    PY2,
    PY3,
    b,
    binary_type,
    integer_types,
    iteritems,
    string_types,
    text_type,
)
from ansible.module_utils.six.moves import map, reduce, shlex_quote
from ansible.module_utils._text import to_native, to_bytes, to_text
from ansible.module_utils.parsing.convert_bool import BOOLEANS, BOOLEANS_FALSE, BOOLEANS_TRUE, boolean


PASSWORD_MATCH = re.compile(r'^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd)?)(?:[-_\s].+)?$', re.I)

_NUMBERTYPES = tuple(list(integer_types) + [float])

# Deprecated compat.  Only kept in case another module used these names  Using
# ansible.module_utils.six is preferred

NUMBERTYPES = _NUMBERTYPES

imap = map

try:
    # Python 2
    unicode
except NameError:
    # Python 3
    unicode = text_type

try:
    # Python 2.6+
    bytes
except NameError:
    # Python 2.4
    bytes = binary_type

try:
    # Python 2
    basestring
except NameError:
    # Python 3
    basestring = string_types

_literal_eval = literal_eval

# End of deprecated names

# Internal global holding passed in params.  This is consulted in case
# multiple AnsibleModules are created.  Otherwise each AnsibleModule would
# attempt to read from stdin.  Other code should not use this directly as it
# is an internal implementation detail
_ANSIBLE_ARGS = None

FILE_COMMON_ARGUMENTS = dict(
    src=dict(),
    mode=dict(type='raw'),
    owner=dict(),
    group=dict(),
    seuser=dict(),
    serole=dict(),
    selevel=dict(),
    setype=dict(),
    follow=dict(type='bool', default=False),
    # not taken by the file module, but other modules call file so it must ignore them.
    content=dict(no_log=True),
    backup=dict(),
    force=dict(),
    remote_src=dict(),  # used by assemble
    regexp=dict(),  # used by assemble
    delimiter=dict(),  # used by assemble
    directory_mode=dict(),  # used by copy
    unsafe_writes=dict(type='bool'),  # should be available to any module using atomic_move
    attributes=dict(aliases=['attr']),
)

PASSWD_ARG_RE = re.compile(r'^[-]{0,2}pass[-]?(word|wd)?')

# Used for parsing symbolic file perms
MODE_OPERATOR_RE = re.compile(r'[+=-]')
USERS_RE = re.compile(r'[^ugo]')
PERMS_RE = re.compile(r'[^rwxXstugo]')


PERM_BITS = 0o7777       # file mode permission bits
EXEC_PERM_BITS = 0o0111  # execute permission bits
DEFAULT_PERM = 0o0666    # default file permission bits


def get_platform():
    ''' what's the platform?  example: Linux is a platform. '''
    return platform.system()


def get_distribution():
    ''' return the distribution name '''
    if platform.system() == 'Linux':
        try:
            supported_dists = platform._supported_dists + ('arch', 'alpine', 'devuan')
            distribution = platform.linux_distribution(supported_dists=supported_dists)[0].capitalize()
            if not distribution and os.path.isfile('/etc/system-release'):
                distribution = platform.linux_distribution(supported_dists=['system'])[0].capitalize()
                if 'Amazon' in distribution:
                    distribution = 'Amazon'
                else:
                    distribution = 'OtherLinux'
        except:
            # FIXME: MethodMissing, I assume?
            distribution = platform.dist()[0].capitalize()
    else:
        distribution = None
    return distribution


def get_distribution_version():
    ''' return the distribution version '''
    if platform.system() == 'Linux':
        try:
            distribution_version = platform.linux_distribution()[1]
            if not distribution_version and os.path.isfile('/etc/system-release'):
                distribution_version = platform.linux_distribution(supported_dists=['system'])[1]
        except:
            # FIXME: MethodMissing, I assume?
            distribution_version = platform.dist()[1]
    else:
        distribution_version = None
    return distribution_version


def get_all_subclasses(cls):
    '''
    used by modules like Hardware or Network fact classes to retrieve all subclasses of a given class.
    __subclasses__ return only direct sub classes. This one go down into the class tree.
    '''
    # Retrieve direct subclasses
    subclasses = cls.__subclasses__()
    to_visit = list(subclasses)
    # Then visit all subclasses
    while to_visit:
        for sc in to_visit:
            # The current class is now visited, so remove it from list
            to_visit.remove(sc)
            # Appending all subclasses to visit and keep a reference of available class
            for ssc in sc.__subclasses__():
                subclasses.append(ssc)
                to_visit.append(ssc)
    return subclasses


def load_platform_subclass(cls, *args, **kwargs):
    '''
    used by modules like User to have different implementations based on detected platform.  See User
    module for an example.
    '''

    this_platform = get_platform()
    distribution = get_distribution()
    subclass = None

    # get the most specific superclass for this platform
    if distribution is not None:
        for sc in get_all_subclasses(cls):
            if sc.distribution is not None and sc.distribution == distribution and sc.platform == this_platform:
                subclass = sc
    if subclass is None:
        for sc in get_all_subclasses(cls):
            if sc.platform == this_platform and sc.distribution is None:
                subclass = sc
    if subclass is None:
        subclass = cls

    return super(cls, subclass).__new__(subclass)


def json_dict_unicode_to_bytes(d, encoding='utf-8', errors='surrogate_or_strict'):
    ''' Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    '''

    if isinstance(d, text_type):
        return to_bytes(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(map(json_dict_unicode_to_bytes, iteritems(d), repeat(encoding), repeat(errors)))
    elif isinstance(d, list):
        return list(map(json_dict_unicode_to_bytes, d, repeat(encoding), repeat(errors)))
    elif isinstance(d, tuple):
        return tuple(map(json_dict_unicode_to_bytes, d, repeat(encoding), repeat(errors)))
    else:
        return d


def json_dict_bytes_to_unicode(d, encoding='utf-8', errors='surrogate_or_strict'):
    ''' Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    '''

    if isinstance(d, binary_type):
        # Warning, can traceback
        return to_text(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(map(json_dict_bytes_to_unicode, iteritems(d), repeat(encoding), repeat(errors)))
    elif isinstance(d, list):
        return list(map(json_dict_bytes_to_unicode, d, repeat(encoding), repeat(errors)))
    elif isinstance(d, tuple):
        return tuple(map(json_dict_bytes_to_unicode, d, repeat(encoding), repeat(errors)))
    else:
        return d


def return_values(obj):
    """ Return native stringified values from datastructures.

    For use with removing sensitive values pre-jsonification."""
    if isinstance(obj, (text_type, binary_type)):
        if obj:
            yield to_native(obj, errors='surrogate_or_strict')
        return
    elif isinstance(obj, SEQUENCETYPE):
        for element in obj:
            for subelement in return_values(element):
                yield subelement
    elif isinstance(obj, Mapping):
        for element in obj.items():
            for subelement in return_values(element[1]):
                yield subelement
    elif isinstance(obj, (bool, NoneType)):
        # This must come before int because bools are also ints
        return
    elif isinstance(obj, NUMBERTYPES):
        yield to_native(obj, nonstring='simplerepr')
    else:
        raise TypeError('Unknown parameter type: %s, %s' % (type(obj), obj))


def _remove_values_conditions(value, no_log_strings, deferred_removals):
    """
    Helper function for :meth:`remove_values`.

    :arg value: The value to check for strings that need to be stripped
    :arg no_log_strings: set of strings which must be stripped out of any values
    :arg deferred_removals: List which holds information about nested
        containers that have to be iterated for removals.  It is passed into
        this function so that more entries can be added to it if value is
        a container type.  The format of each entry is a 2-tuple where the first
        element is the ``value`` parameter and the second value is a new
        container to copy the elements of ``value`` into once iterated.
    :returns: if ``value`` is a scalar, returns ``value`` with two exceptions:
        1. :class:`~datetime.datetime` objects which are changed into a string representation.
        2. objects which are in no_log_strings are replaced with a placeholder
            so that no sensitive data is leaked.
        If ``value`` is a container type, returns a new empty container.

    ``deferred_removals`` is added to as a side-effect of this function.

    .. warning:: It is up to the caller to make sure the order in which value
        is passed in is correct.  For instance, higher level containers need
        to be passed in before lower level containers. For example, given
        ``{'level1': {'level2': 'level3': [True]} }`` first pass in the
        dictionary for ``level1``, then the dict for ``level2``, and finally
        the list for ``level3``.
    """
    if isinstance(value, (text_type, binary_type)):
        # Need native str type
        native_str_value = value
        if isinstance(value, text_type):
            value_is_text = True
            if PY2:
                native_str_value = to_bytes(value, errors='surrogate_or_strict')
        elif isinstance(value, binary_type):
            value_is_text = False
            if PY3:
                native_str_value = to_text(value, errors='surrogate_or_strict')

        if native_str_value in no_log_strings:
            return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
        for omit_me in no_log_strings:
            native_str_value = native_str_value.replace(omit_me, '*' * 8)

        if value_is_text and isinstance(native_str_value, binary_type):
            value = to_text(native_str_value, encoding='utf-8', errors='surrogate_then_replace')
        elif not value_is_text and isinstance(native_str_value, text_type):
            value = to_bytes(native_str_value, encoding='utf-8', errors='surrogate_then_replace')
        else:
            value = native_str_value

    elif isinstance(value, Sequence):
        if isinstance(value, MutableSequence):
            new_value = type(value)()
        else:
            new_value = []  # Need a mutable value
        deferred_removals.append((value, new_value))
        value = new_value

    elif isinstance(value, Set):
        if isinstance(value, MutableSet):
            new_value = type(value)()
        else:
            new_value = set()  # Need a mutable value
        deferred_removals.append((value, new_value))
        value = new_value

    elif isinstance(value, Mapping):
        if isinstance(value, MutableMapping):
            new_value = type(value)()
        else:
            new_value = {}  # Need a mutable value
        deferred_removals.append((value, new_value))
        value = new_value

    elif isinstance(value, tuple(chain(NUMBERTYPES, (bool, NoneType)))):
        stringy_value = to_native(value, encoding='utf-8', errors='surrogate_or_strict')
        if stringy_value in no_log_strings:
            return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
        for omit_me in no_log_strings:
            if omit_me in stringy_value:
                return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'

    elif isinstance(value, datetime.datetime):
        value = value.isoformat()
    else:
        raise TypeError('Value of unknown type: %s, %s' % (type(value), value))

    return value


def remove_values(value, no_log_strings):
    """ Remove strings in no_log_strings from value.  If value is a container
    type, then remove a lot more"""
    deferred_removals = deque()

    no_log_strings = [to_native(s, errors='surrogate_or_strict') for s in no_log_strings]
    new_value = _remove_values_conditions(value, no_log_strings, deferred_removals)

    while deferred_removals:
        old_data, new_data = deferred_removals.popleft()
        if isinstance(new_data, Mapping):
            for old_key, old_elem in old_data.items():
                new_elem = _remove_values_conditions(old_elem, no_log_strings, deferred_removals)
                new_data[old_key] = new_elem
        else:
            for elem in old_data:
                new_elem = _remove_values_conditions(elem, no_log_strings, deferred_removals)
                if isinstance(new_data, MutableSequence):
                    new_data.append(new_elem)
                elif isinstance(new_data, MutableSet):
                    new_data.add(new_elem)
                else:
                    raise TypeError('Unknown container type encountered when removing private values from output')

    return new_value


def heuristic_log_sanitize(data, no_log_values=None):
    ''' Remove strings that look like passwords from log messages '''
    # Currently filters:
    # user:pass@foo/whatever and http://username:pass@wherever/foo
    # This code has false positives and consumes parts of logs that are
    # not passwds

    # begin: start of a passwd containing string
    # end: end of a passwd containing string
    # sep: char between user and passwd
    # prev_begin: where in the overall string to start a search for
    #   a passwd
    # sep_search_end: where in the string to end a search for the sep
    data = to_native(data)

    output = []
    begin = len(data)
    prev_begin = begin
    sep = 1
    while sep:
        # Find the potential end of a passwd
        try:
            end = data.rindex('@', 0, begin)
        except ValueError:
            # No passwd in the rest of the data
            output.insert(0, data[0:begin])
            break

        # Search for the beginning of a passwd
        sep = None
        sep_search_end = end
        while not sep:
            # URL-style username+password
            try:
                begin = data.rindex('://', 0, sep_search_end)
            except ValueError:
                # No url style in the data, check for ssh style in the
                # rest of the string
                begin = 0
            # Search for separator
            try:
                sep = data.index(':', begin + 3, end)
            except ValueError:
                # No separator; choices:
                if begin == 0:
                    # Searched the whole string so there's no password
                    # here.  Return the remaining data
                    output.insert(0, data[0:begin])
                    break
                # Search for a different beginning of the password field.
                sep_search_end = begin
                continue
        if sep:
            # Password was found; remove it.
            output.insert(0, data[end:prev_begin])
            output.insert(0, '********')
            output.insert(0, data[begin:sep + 1])
            prev_begin = begin

    output = ''.join(output)
    if no_log_values:
        output = remove_values(output, no_log_values)
    return output


def bytes_to_human(size, isbits=False, unit=None):

    base = 'Bytes'
    if isbits:
        base = 'bits'
    suffix = ''

    for suffix, limit in sorted(iteritems(SIZE_RANGES), key=lambda item: -item[1]):
        if (unit is None and size >= limit) or unit is not None and unit.upper() == suffix[0]:
            break

    if limit != 1:
        suffix += base[0]
    else:
        suffix = base

    return '%.2f %s' % (float(size) / limit, suffix)


def human_to_bytes(number, default_unit=None, isbits=False):

    '''
    Convert number in string format into bytes (ex: '2K' => 2048) or using unit argument
    ex:
      human_to_bytes('10M') <=> human_to_bytes(10, 'M')
    '''
    m = re.search(r'^\s*(\d*\.?\d*)\s*([A-Za-z]+)?', str(number), flags=re.IGNORECASE)
    if m is None:
        raise ValueError("human_to_bytes() can't interpret following string: %s" % str(number))
    try:
        num = float(m.group(1))
    except:
        raise ValueError("human_to_bytes() can't interpret following number: %s (original input string: %s)" % (m.group(1), number))

    unit = m.group(2)
    if unit is None:
        unit = default_unit

    if unit is None:
        ''' No unit given, returning raw number '''
        return int(round(num))
    range_key = unit[0].upper()
    try:
        limit = SIZE_RANGES[range_key]
    except:
        raise ValueError("human_to_bytes() failed to convert %s (unit = %s). The suffix must be one of %s" % (number, unit, ", ".join(SIZE_RANGES.keys())))

    # default value
    unit_class = 'B'
    unit_class_name = 'byte'
    # handling bits case
    if isbits:
        unit_class = 'b'
        unit_class_name = 'bit'
    # check unit value if more than one character (KB, MB)
    if len(unit) > 1:
        expect_message = 'expect %s%s or %s' % (range_key, unit_class, range_key)
        if range_key == 'B':
            expect_message = 'expect %s or %s' % (unit_class, unit_class_name)

        if unit_class_name in unit.lower():
            pass
        elif unit[1] != unit_class:
            raise ValueError("human_to_bytes() failed to convert %s. Value is not a valid string (%s)" % (number, expect_message))

    return int(round(num * limit))


def is_executable(path):
    '''is the given path executable?

    Limitations:
    * Does not account for FSACLs.
    * Most times we really want to know "Can the current user execute this
      file"  This function does not tell us that, only if an execute bit is set.
    '''
    # These are all bitfields so first bitwise-or all the permissions we're
    # looking for, then bitwise-and with the file's mode to determine if any
    # execute bits are set.
    return ((stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & os.stat(path)[stat.ST_MODE])


def _load_params():
    ''' read the modules parameters and store them globally.

    This function may be needed for certain very dynamic custom modules which
    want to process the parameters that are being handed the module.  Since
    this is so closely tied to the implementation of modules we cannot
    guarantee API stability for it (it may change between versions) however we
    will try not to break it gratuitously.  It is certainly more future-proof
    to call this function and consume its outputs than to implement the logic
    inside it as a copy in your own code.
    '''
    global _ANSIBLE_ARGS
    if _ANSIBLE_ARGS is not None:
        buffer = _ANSIBLE_ARGS
    else:
        # debug overrides to read args from file or cmdline

        # Avoid tracebacks when locale is non-utf8
        # We control the args and we pass them as utf8
        if len(sys.argv) > 1:
            if os.path.isfile(sys.argv[1]):
                fd = open(sys.argv[1], 'rb')
                buffer = fd.read()
                fd.close()
            else:
                buffer = sys.argv[1]
                if PY3:
                    buffer = buffer.encode('utf-8', errors='surrogateescape')
        # default case, read from stdin
        else:
            if PY2:
                buffer = sys.stdin.read()
            else:
                buffer = sys.stdin.buffer.read()
        _ANSIBLE_ARGS = buffer

    try:
        params = json.loads(buffer.decode('utf-8'))
    except ValueError:
        # This helper used too early for fail_json to work.
        print('\n{"msg": "Error: Module unable to decode valid JSON on stdin.  Unable to figure out what parameters were passed", "failed": true}')
        sys.exit(1)

    if PY2:
        params = json_dict_unicode_to_bytes(params)

    try:
        return params['ANSIBLE_MODULE_ARGS']
    except KeyError:
        # This helper does not have access to fail_json so we have to print
        # json output on our own.
        print('\n{"msg": "Error: Module unable to locate ANSIBLE_MODULE_ARGS in json data from stdin.  Unable to figure out what parameters were passed", '
              '"failed": true}')
        sys.exit(1)


def env_fallback(*args, **kwargs):
    ''' Load value from environment '''
    for arg in args:
        if arg in os.environ:
            return os.environ[arg]
    raise AnsibleFallbackNotFound


def _lenient_lowercase(lst):
    """Lowercase elements of a list.

    If an element is not a string, pass it through untouched.
    """
    lowered = []
    for value in lst:
        try:
            lowered.append(value.lower())
        except AttributeError:
            lowered.append(value)
    return lowered


def format_attributes(attributes):
    attribute_list = []
    for attr in attributes:
        if attr in FILE_ATTRIBUTES:
            attribute_list.append(FILE_ATTRIBUTES[attr])
    return attribute_list


def get_flags_from_attributes(attributes):
    flags = []
    for key, attr in FILE_ATTRIBUTES.items():
        if attr in attributes:
            flags.append(key)
    return ''.join(flags)


def _json_encode_fallback(obj):
    if isinstance(obj, Set):
        return list(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError("Cannot json serialize %s" % to_native(obj))


def jsonify(data, **kwargs):
    for encoding in ("utf-8", "latin-1"):
        try:
            return json.dumps(data, encoding=encoding, default=_json_encode_fallback, **kwargs)
        # Old systems using old simplejson module does not support encoding keyword.
        except TypeError:
            try:
                new_data = json_dict_bytes_to_unicode(data, encoding=encoding)
            except UnicodeDecodeError:
                continue
            return json.dumps(new_data, default=_json_encode_fallback, **kwargs)
        except UnicodeDecodeError:
            continue
    raise UnicodeError('Invalid unicode encoding encountered')


class AnsibleFallbackNotFound(Exception):
    pass


class AnsibleModule(object):
    def __init__(self, argument_spec, bypass_checks=False, no_log=False,
                 check_invalid_arguments=True, mutually_exclusive=None, required_together=None,
                 required_one_of=None, add_file_common_args=False, supports_check_mode=False,
                 required_if=None):

        '''
        common code for quickly building an ansible module in Python
        (although you can write modules in anything that can return JSON)
        see library/* for examples
        '''

        self._name = os.path.basename(__file__)  # initialize name until we can parse from options
        self.argument_spec = argument_spec
        self.supports_check_mode = supports_check_mode
        self.check_mode = False
        self.bypass_checks = bypass_checks
        self.no_log = no_log
        self.check_invalid_arguments = check_invalid_arguments
        self.mutually_exclusive = mutually_exclusive
        self.required_together = required_together
        self.required_one_of = required_one_of
        self.required_if = required_if
        self.cleanup_files = []
        self._debug = False
        self._diff = False
        self._socket_path = None
        self._shell = None
        self._verbosity = 0
        # May be used to set modifications to the environment for any
        # run_command invocation
        self.run_command_environ_update = {}
        self._warnings = []
        self._deprecations = []
        self._clean = {}

        self.aliases = {}
        self._legal_inputs = ['_ansible_check_mode', '_ansible_no_log', '_ansible_debug', '_ansible_diff', '_ansible_verbosity',
                              '_ansible_selinux_special_fs', '_ansible_module_name', '_ansible_version', '_ansible_syslog_facility',
                              '_ansible_socket', '_ansible_shell_executable']
        self._options_context = list()

        if add_file_common_args:
            for k, v in FILE_COMMON_ARGUMENTS.items():
                if k not in self.argument_spec:
                    self.argument_spec[k] = v

        self._load_params()
        self._set_fallbacks()

        # append to legal_inputs and then possibly check against them
        try:
            self.aliases = self._handle_aliases()
        except Exception as e:
            # Use exceptions here because it isn't safe to call fail_json until no_log is processed
            print('\n{"failed": true, "msg": "Module alias error: %s"}' % to_native(e))
            sys.exit(1)

        # Save parameter values that should never be logged
        self.no_log_values = set()
        self._handle_no_log_values()

        # check the locale as set by the current environment, and reset to
        # a known valid (LANG=C) if it's an invalid/unavailable locale
        self._check_locale()

        self._check_arguments(check_invalid_arguments)

        # check exclusive early
        if not bypass_checks:
            self._check_mutually_exclusive(mutually_exclusive)

        self._set_defaults(pre=True)

        self._CHECK_ARGUMENT_TYPES_DISPATCHER = {
            'str': self._check_type_str,
            'list': self._check_type_list,
            'dict': self._check_type_dict,
            'bool': self._check_type_bool,
            'int': self._check_type_int,
            'float': self._check_type_float,
            'path': self._check_type_path,
            'raw': self._check_type_raw,
            'jsonarg': self._check_type_jsonarg,
            'json': self._check_type_jsonarg,
            'bytes': self._check_type_bytes,
            'bits': self._check_type_bits,
        }
        if not bypass_checks:
            self._check_required_arguments()
            self._check_argument_types()
            self._check_argument_values()
            self._check_required_together(required_together)
            self._check_required_one_of(required_one_of)
            self._check_required_if(required_if)

        self._set_defaults(pre=False)

        # deal with options sub-spec
        self._handle_options()

        if not self.no_log:
            self._log_invocation()

        # finally, make sure we're in a sane working dir
        self._set_cwd()

    def warn(self, warning):

        if isinstance(warning, string_types):
            self._warnings.append(warning)
            self.log('[WARNING] %s' % warning)
        else:
            raise TypeError("warn requires a string not a %s" % type(warning))

    def deprecate(self, msg, version=None):
        if isinstance(msg, string_types):
            self._deprecations.append({
                'msg': msg,
                'version': version
            })
            self.log('[DEPRECATION WARNING] %s %s' % (msg, version))
        else:
            raise TypeError("deprecate requires a string not a %s" % type(msg))

    def load_file_common_arguments(self, params):
        '''
        many modules deal with files, this encapsulates common
        options that the file module accepts such that it is directly
        available to all modules and they can share code.
        '''

        path = params.get('path', params.get('dest', None))
        if path is None:
            return {}
        else:
            path = os.path.expanduser(os.path.expandvars(path))

        b_path = to_bytes(path, errors='surrogate_or_strict')
        # if the path is a symlink, and we're following links, get
        # the target of the link instead for testing
        if params.get('follow', False) and os.path.islink(b_path):
            b_path = os.path.realpath(b_path)
            path = to_native(b_path)

        mode = params.get('mode', None)
        owner = params.get('owner', None)
        group = params.get('group', None)

        # selinux related options
        seuser = params.get('seuser', None)
        serole = params.get('serole', None)
        setype = params.get('setype', None)
        selevel = params.get('selevel', None)
        secontext = [seuser, serole, setype]

        if self.selinux_mls_enabled():
            secontext.append(selevel)

        default_secontext = self.selinux_default_context(path)
        for i in range(len(default_secontext)):
            if i is not None and secontext[i] == '_default':
                secontext[i] = default_secontext[i]

        attributes = params.get('attributes', None)
        return dict(
            path=path, mode=mode, owner=owner, group=group,
            seuser=seuser, serole=serole, setype=setype,
            selevel=selevel, secontext=secontext, attributes=attributes,
        )

    # Detect whether using selinux that is MLS-aware.
    # While this means you can set the level/range with
    # selinux.lsetfilecon(), it may or may not mean that you
    # will get the selevel as part of the context returned
    # by selinux.lgetfilecon().

    def selinux_mls_enabled(self):
        if not HAVE_SELINUX:
            return False
        if selinux.is_selinux_mls_enabled() == 1:
            return True
        else:
            return False

    def selinux_enabled(self):
        if not HAVE_SELINUX:
            seenabled = self.get_bin_path('selinuxenabled')
            if seenabled is not None:
                (rc, out, err) = self.run_command(seenabled)
                if rc == 0:
                    self.fail_json(msg="Aborting, target uses selinux but python bindings (libselinux-python) aren't installed!")
            return False
        if selinux.is_selinux_enabled() == 1:
            return True
        else:
            return False

    # Determine whether we need a placeholder for selevel/mls
    def selinux_initial_context(self):
        context = [None, None, None]
        if self.selinux_mls_enabled():
            context.append(None)
        return context

    # If selinux fails to find a default, return an array of None
    def selinux_default_context(self, path, mode=0):
        context = self.selinux_initial_context()
        if not HAVE_SELINUX or not self.selinux_enabled():
            return context
        try:
            ret = selinux.matchpathcon(to_native(path, errors='surrogate_or_strict'), mode)
        except OSError:
            return context
        if ret[0] == -1:
            return context
        # Limit split to 4 because the selevel, the last in the list,
        # may contain ':' characters
        context = ret[1].split(':', 3)
        return context

    def selinux_context(self, path):
        context = self.selinux_initial_context()
        if not HAVE_SELINUX or not self.selinux_enabled():
            return context
        try:
            ret = selinux.lgetfilecon_raw(to_native(path, errors='surrogate_or_strict'))
        except OSError as e:
            if e.errno == errno.ENOENT:
                self.fail_json(path=path, msg='path %s does not exist' % path)
            else:
                self.fail_json(path=path, msg='failed to retrieve selinux context')
        if ret[0] == -1:
            return context
        # Limit split to 4 because the selevel, the last in the list,
        # may contain ':' characters
        context = ret[1].split(':', 3)
        return context

    def user_and_group(self, path, expand=True):
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))
        st = os.lstat(b_path)
        uid = st.st_uid
        gid = st.st_gid
        return (uid, gid)

    def find_mount_point(self, path):
        path_is_bytes = False
        if isinstance(path, binary_type):
            path_is_bytes = True

        b_path = os.path.realpath(to_bytes(os.path.expanduser(os.path.expandvars(path)), errors='surrogate_or_strict'))
        while not os.path.ismount(b_path):
            b_path = os.path.dirname(b_path)

        if path_is_bytes:
            return b_path

        return to_text(b_path, errors='surrogate_or_strict')

    def is_special_selinux_path(self, path):
        """
        Returns a tuple containing (True, selinux_context) if the given path is on a
        NFS or other 'special' fs  mount point, otherwise the return will be (False, None).
        """
        try:
            f = open('/proc/mounts', 'r')
            mount_data = f.readlines()
            f.close()
        except:
            return (False, None)
        path_mount_point = self.find_mount_point(path)
        for line in mount_data:
            (device, mount_point, fstype, options, rest) = line.split(' ', 4)

            if path_mount_point == mount_point:
                for fs in self._selinux_special_fs:
                    if fs in fstype:
                        special_context = self.selinux_context(path_mount_point)
                        return (True, special_context)

        return (False, None)

    def set_default_selinux_context(self, path, changed):
        if not HAVE_SELINUX or not self.selinux_enabled():
            return changed
        context = self.selinux_default_context(path)
        return self.set_context_if_different(path, context, False)

    def set_context_if_different(self, path, context, changed, diff=None):

        if not HAVE_SELINUX or not self.selinux_enabled():
            return changed
        cur_context = self.selinux_context(path)
        new_context = list(cur_context)
        # Iterate over the current context instead of the
        # argument context, which may have selevel.

        (is_special_se, sp_context) = self.is_special_selinux_path(path)
        if is_special_se:
            new_context = sp_context
        else:
            for i in range(len(cur_context)):
                if len(context) > i:
                    if context[i] is not None and context[i] != cur_context[i]:
                        new_context[i] = context[i]
                    elif context[i] is None:
                        new_context[i] = cur_context[i]

        if cur_context != new_context:
            if diff is not None:
                if 'before' not in diff:
                    diff['before'] = {}
                diff['before']['secontext'] = cur_context
                if 'after' not in diff:
                    diff['after'] = {}
                diff['after']['secontext'] = new_context

            try:
                if self.check_mode:
                    return True
                rc = selinux.lsetfilecon(to_native(path), ':'.join(new_context))
            except OSError as e:
                self.fail_json(path=path, msg='invalid selinux context: %s' % to_native(e),
                               new_context=new_context, cur_context=cur_context, input_was=context)
            if rc != 0:
                self.fail_json(path=path, msg='set selinux context failed')
            changed = True
        return changed

    def set_owner_if_different(self, path, owner, changed, diff=None, expand=True):
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))
        if owner is None:
            return changed
        orig_uid, orig_gid = self.user_and_group(b_path, expand)
        try:
            uid = int(owner)
        except ValueError:
            try:
                uid = pwd.getpwnam(owner).pw_uid
            except KeyError:
                path = to_text(b_path)
                self.fail_json(path=path, msg='chown failed: failed to look up user %s' % owner)

        if orig_uid != uid:
            if diff is not None:
                if 'before' not in diff:
                    diff['before'] = {}
                diff['before']['owner'] = orig_uid
                if 'after' not in diff:
                    diff['after'] = {}
                diff['after']['owner'] = uid

            if self.check_mode:
                return True
            try:
                os.lchown(b_path, uid, -1)
            except (IOError, OSError) as e:
                path = to_text(b_path)
                self.fail_json(path=path, msg='chown failed: %s' % (to_text(e)))
            changed = True
        return changed

    def set_group_if_different(self, path, group, changed, diff=None, expand=True):
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))
        if group is None:
            return changed
        orig_uid, orig_gid = self.user_and_group(b_path, expand)
        try:
            gid = int(group)
        except ValueError:
            try:
                gid = grp.getgrnam(group).gr_gid
            except KeyError:
                path = to_text(b_path)
                self.fail_json(path=path, msg='chgrp failed: failed to look up group %s' % group)

        if orig_gid != gid:
            if diff is not None:
                if 'before' not in diff:
                    diff['before'] = {}
                diff['before']['group'] = orig_gid
                if 'after' not in diff:
                    diff['after'] = {}
                diff['after']['group'] = gid

            if self.check_mode:
                return True
            try:
                os.lchown(b_path, -1, gid)
            except OSError:
                path = to_text(b_path)
                self.fail_json(path=path, msg='chgrp failed')
            changed = True
        return changed

    def set_mode_if_different(self, path, mode, changed, diff=None, expand=True):
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))
        path_stat = os.lstat(b_path)

        if mode is None:
            return changed

        if not isinstance(mode, int):
            try:
                mode = int(mode, 8)
            except Exception:
                try:
                    mode = self._symbolic_mode_to_octal(path_stat, mode)
                except Exception as e:
                    path = to_text(b_path)
                    self.fail_json(path=path,
                                   msg="mode must be in octal or symbolic form",
                                   details=to_native(e))

                if mode != stat.S_IMODE(mode):
                    # prevent mode from having extra info orbeing invalid long number
                    path = to_text(b_path)
                    self.fail_json(path=path, msg="Invalid mode supplied, only permission info is allowed", details=mode)

        prev_mode = stat.S_IMODE(path_stat.st_mode)

        if prev_mode != mode:

            if diff is not None:
                if 'before' not in diff:
                    diff['before'] = {}
                diff['before']['mode'] = '0%03o' % prev_mode
                if 'after' not in diff:
                    diff['after'] = {}
                diff['after']['mode'] = '0%03o' % mode

            if self.check_mode:
                return True
            # FIXME: comparison against string above will cause this to be executed
            # every time
            try:
                if hasattr(os, 'lchmod'):
                    os.lchmod(b_path, mode)
                else:
                    if not os.path.islink(b_path):
                        os.chmod(b_path, mode)
                    else:
                        # Attempt to set the perms of the symlink but be
                        # careful not to change the perms of the underlying
                        # file while trying
                        underlying_stat = os.stat(b_path)
                        os.chmod(b_path, mode)
                        new_underlying_stat = os.stat(b_path)
                        if underlying_stat.st_mode != new_underlying_stat.st_mode:
                            os.chmod(b_path, stat.S_IMODE(underlying_stat.st_mode))
            except OSError as e:
                if os.path.islink(b_path) and e.errno == errno.EPERM:  # Can't set mode on symbolic links
                    pass
                elif e.errno in (errno.ENOENT, errno.ELOOP):  # Can't set mode on broken symbolic links
                    pass
                else:
                    raise
            except Exception as e:
                path = to_text(b_path)
                self.fail_json(path=path, msg='chmod failed', details=to_native(e),
                               exception=traceback.format_exc())

            path_stat = os.lstat(b_path)
            new_mode = stat.S_IMODE(path_stat.st_mode)

            if new_mode != prev_mode:
                changed = True
        return changed

    def set_attributes_if_different(self, path, attributes, changed, diff=None, expand=True):

        if attributes is None:
            return changed

        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))

        existing = self.get_file_attributes(b_path)

        if existing.get('attr_flags', '') != attributes:
            attrcmd = self.get_bin_path('chattr')
            if attrcmd:
                attrcmd = [attrcmd, '=%s' % attributes, b_path]
                changed = True

                if diff is not None:
                    if 'before' not in diff:
                        diff['before'] = {}
                    diff['before']['attributes'] = existing.get('attr_flags')
                    if 'after' not in diff:
                        diff['after'] = {}
                    diff['after']['attributes'] = attributes

                if not self.check_mode:
                    try:
                        rc, out, err = self.run_command(attrcmd)
                        if rc != 0 or err:
                            raise Exception("Error while setting attributes: %s" % (out + err))
                    except Exception as e:
                        self.fail_json(path=to_text(b_path), msg='chattr failed',
                                       details=to_native(e), exception=traceback.format_exc())
        return changed

    def get_file_attributes(self, path):
        output = {}
        attrcmd = self.get_bin_path('lsattr', False)
        if attrcmd:
            attrcmd = [attrcmd, '-vd', path]
            try:
                rc, out, err = self.run_command(attrcmd)
                if rc == 0:
                    res = out.split()
                    output['attr_flags'] = res[1].replace('-', '').strip()
                    output['version'] = res[0].strip()
                    output['attributes'] = format_attributes(output['attr_flags'])
            except:
                pass
        return output

    @classmethod
    def _symbolic_mode_to_octal(cls, path_stat, symbolic_mode):
        """
        This enables symbolic chmod string parsing as stated in the chmod man-page

        This includes things like: "u=rw-x+X,g=r-x+X,o=r-x+X"
        """

        new_mode = stat.S_IMODE(path_stat.st_mode)

        # Now parse all symbolic modes
        for mode in symbolic_mode.split(','):
            # Per single mode. This always contains a '+', '-' or '='
            # Split it on that
            permlist = MODE_OPERATOR_RE.split(mode)

            # And find all the operators
            opers = MODE_OPERATOR_RE.findall(mode)

            # The user(s) where it's all about is the first element in the
            # 'permlist' list. Take that and remove it from the list.
            # An empty user or 'a' means 'all'.
            users = permlist.pop(0)
            use_umask = (users == '')
            if users == 'a' or users == '':
                users = 'ugo'

            # Check if there are illegal characters in the user list
            # They can end up in 'users' because they are not split
            if USERS_RE.match(users):
                raise ValueError("bad symbolic permission for mode: %s" % mode)

            # Now we have two list of equal length, one contains the requested
            # permissions and one with the corresponding operators.
            for idx, perms in enumerate(permlist):
                # Check if there are illegal characters in the permissions
                if PERMS_RE.match(perms):
                    raise ValueError("bad symbolic permission for mode: %s" % mode)

                for user in users:
                    mode_to_apply = cls._get_octal_mode_from_symbolic_perms(path_stat, user, perms, use_umask)
                    new_mode = cls._apply_operation_to_mode(user, opers[idx], mode_to_apply, new_mode)

        return new_mode

    @staticmethod
    def _apply_operation_to_mode(user, operator, mode_to_apply, current_mode):
        if operator == '=':
            if user == 'u':
                mask = stat.S_IRWXU | stat.S_ISUID
            elif user == 'g':
                mask = stat.S_IRWXG | stat.S_ISGID
            elif user == 'o':
                mask = stat.S_IRWXO | stat.S_ISVTX

            # mask out u, g, or o permissions from current_mode and apply new permissions
            inverse_mask = mask ^ PERM_BITS
            new_mode = (current_mode & inverse_mask) | mode_to_apply
        elif operator == '+':
            new_mode = current_mode | mode_to_apply
        elif operator == '-':
            new_mode = current_mode - (current_mode & mode_to_apply)
        return new_mode

    @staticmethod
    def _get_octal_mode_from_symbolic_perms(path_stat, user, perms, use_umask):
        prev_mode = stat.S_IMODE(path_stat.st_mode)

        is_directory = stat.S_ISDIR(path_stat.st_mode)
        has_x_permissions = (prev_mode & EXEC_PERM_BITS) > 0
        apply_X_permission = is_directory or has_x_permissions

        # Get the umask, if the 'user' part is empty, the effect is as if (a) were
        # given, but bits that are set in the umask are not affected.
        # We also need the "reversed umask" for masking
        umask = os.umask(0)
        os.umask(umask)
        rev_umask = umask ^ PERM_BITS

        # Permission bits constants documented at:
        # http://docs.python.org/2/library/stat.html#stat.S_ISUID
        if apply_X_permission:
            X_perms = {
                'u': {'X': stat.S_IXUSR},
                'g': {'X': stat.S_IXGRP},
                'o': {'X': stat.S_IXOTH},
            }
        else:
            X_perms = {
                'u': {'X': 0},
                'g': {'X': 0},
                'o': {'X': 0},
            }

        user_perms_to_modes = {
            'u': {
                'r': rev_umask & stat.S_IRUSR if use_umask else stat.S_IRUSR,
                'w': rev_umask & stat.S_IWUSR if use_umask else stat.S_IWUSR,
                'x': rev_umask & stat.S_IXUSR if use_umask else stat.S_IXUSR,
                's': stat.S_ISUID,
                't': 0,
                'u': prev_mode & stat.S_IRWXU,
                'g': (prev_mode & stat.S_IRWXG) << 3,
                'o': (prev_mode & stat.S_IRWXO) << 6},
            'g': {
                'r': rev_umask & stat.S_IRGRP if use_umask else stat.S_IRGRP,
                'w': rev_umask & stat.S_IWGRP if use_umask else stat.S_IWGRP,
                'x': rev_umask & stat.S_IXGRP if use_umask else stat.S_IXGRP,
                's': stat.S_ISGID,
                't': 0,
                'u': (prev_mode & stat.S_IRWXU) >> 3,
                'g': prev_mode & stat.S_IRWXG,
                'o': (prev_mode & stat.S_IRWXO) << 3},
            'o': {
                'r': rev_umask & stat.S_IROTH if use_umask else stat.S_IROTH,
                'w': rev_umask & stat.S_IWOTH if use_umask else stat.S_IWOTH,
                'x': rev_umask & stat.S_IXOTH if use_umask else stat.S_IXOTH,
                's': 0,
                't': stat.S_ISVTX,
                'u': (prev_mode & stat.S_IRWXU) >> 6,
                'g': (prev_mode & stat.S_IRWXG) >> 3,
                'o': prev_mode & stat.S_IRWXO},
        }

        # Insert X_perms into user_perms_to_modes
        for key, value in X_perms.items():
            user_perms_to_modes[key].update(value)

        def or_reduce(mode, perm):
            return mode | user_perms_to_modes[user][perm]

        return reduce(or_reduce, perms, 0)

    def set_fs_attributes_if_different(self, file_args, changed, diff=None, expand=True):
        # set modes owners and context as needed
        changed = self.set_context_if_different(
            file_args['path'], file_args['secontext'], changed, diff
        )
        changed = self.set_owner_if_different(
            file_args['path'], file_args['owner'], changed, diff, expand
        )
        changed = self.set_group_if_different(
            file_args['path'], file_args['group'], changed, diff, expand
        )
        changed = self.set_mode_if_different(
            file_args['path'], file_args['mode'], changed, diff, expand
        )
        changed = self.set_attributes_if_different(
            file_args['path'], file_args['attributes'], changed, diff, expand
        )
        return changed

    def set_directory_attributes_if_different(self, file_args, changed, diff=None, expand=True):
        return self.set_fs_attributes_if_different(file_args, changed, diff, expand)

    def set_file_attributes_if_different(self, file_args, changed, diff=None, expand=True):
        return self.set_fs_attributes_if_different(file_args, changed, diff, expand)

    def add_path_info(self, kwargs):
        '''
        for results that are files, supplement the info about the file
        in the return path with stats about the file path.
        '''

        path = kwargs.get('path', kwargs.get('dest', None))
        if path is None:
            return kwargs
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if os.path.exists(b_path):
            (uid, gid) = self.user_and_group(path)
            kwargs['uid'] = uid
            kwargs['gid'] = gid
            try:
                user = pwd.getpwuid(uid)[0]
            except KeyError:
                user = str(uid)
            try:
                group = grp.getgrgid(gid)[0]
            except KeyError:
                group = str(gid)
            kwargs['owner'] = user
            kwargs['group'] = group
            st = os.lstat(b_path)
            kwargs['mode'] = '0%03o' % stat.S_IMODE(st[stat.ST_MODE])
            # secontext not yet supported
            if os.path.islink(b_path):
                kwargs['state'] = 'link'
            elif os.path.isdir(b_path):
                kwargs['state'] = 'directory'
            elif os.stat(b_path).st_nlink > 1:
                kwargs['state'] = 'hard'
            else:
                kwargs['state'] = 'file'
            if HAVE_SELINUX and self.selinux_enabled():
                kwargs['secontext'] = ':'.join(self.selinux_context(path))
            kwargs['size'] = st[stat.ST_SIZE]
        else:
            kwargs['state'] = 'absent'
        return kwargs

    def _check_locale(self):
        '''
        Uses the locale module to test the currently set locale
        (per the LANG and LC_CTYPE environment settings)
        '''
        try:
            # setting the locale to '' uses the default locale
            # as it would be returned by locale.getdefaultlocale()
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            # fallback to the 'C' locale, which may cause unicode
            # issues but is preferable to simply failing because
            # of an unknown locale
            locale.setlocale(locale.LC_ALL, 'C')
            os.environ['LANG'] = 'C'
            os.environ['LC_ALL'] = 'C'
            os.environ['LC_MESSAGES'] = 'C'
        except Exception as e:
            self.fail_json(msg="An unknown error was encountered while attempting to validate the locale: %s" %
                           to_native(e), exception=traceback.format_exc())

    def _handle_aliases(self, spec=None, param=None):
        # this uses exceptions as it happens before we can safely call fail_json
        aliases_results = {}  # alias:canon
        if param is None:
            param = self.params

        if spec is None:
            spec = self.argument_spec
        for (k, v) in spec.items():
            self._legal_inputs.append(k)
            aliases = v.get('aliases', None)
            default = v.get('default', None)
            required = v.get('required', False)
            if default is not None and required:
                # not alias specific but this is a good place to check this
                raise Exception("internal error: required and default are mutually exclusive for %s" % k)
            if aliases is None:
                continue
            if not isinstance(aliases, SEQUENCETYPE) or isinstance(aliases, (binary_type, text_type)):
                raise Exception('internal error: aliases must be a list or tuple')
            for alias in aliases:
                self._legal_inputs.append(alias)
                aliases_results[alias] = k
                if alias in param:
                    param[k] = param[alias]

        return aliases_results

    def _handle_no_log_values(self, spec=None, param=None):
        if spec is None:
            spec = self.argument_spec
        if param is None:
            param = self.params

        # Use the argspec to determine which args are no_log
        for arg_name, arg_opts in spec.items():
            if arg_opts.get('no_log', False):
                # Find the value for the no_log'd param
                no_log_object = param.get(arg_name, None)
                if no_log_object:
                    self.no_log_values.update(return_values(no_log_object))

            if arg_opts.get('removed_in_version') is not None and arg_name in param:
                self._deprecations.append({
                    'msg': "Param '%s' is deprecated. See the module docs for more information" % arg_name,
                    'version': arg_opts.get('removed_in_version')
                })

    def _check_arguments(self, check_invalid_arguments, spec=None, param=None, legal_inputs=None):
        self._syslog_facility = 'LOG_USER'
        unsupported_parameters = set()
        if spec is None:
            spec = self.argument_spec
        if param is None:
            param = self.params
        if legal_inputs is None:
            legal_inputs = self._legal_inputs

        for (k, v) in list(param.items()):

            if k == '_ansible_check_mode' and v:
                self.check_mode = True

            elif k == '_ansible_no_log':
                self.no_log = self.boolean(v)

            elif k == '_ansible_debug':
                self._debug = self.boolean(v)

            elif k == '_ansible_diff':
                self._diff = self.boolean(v)

            elif k == '_ansible_verbosity':
                self._verbosity = v

            elif k == '_ansible_selinux_special_fs':
                self._selinux_special_fs = v

            elif k == '_ansible_syslog_facility':
                self._syslog_facility = v

            elif k == '_ansible_version':
                self.ansible_version = v

            elif k == '_ansible_module_name':
                self._name = v

            elif k == '_ansible_socket':
                self._socket_path = v

            elif k == '_ansible_shell_executable' and v:
                self._shell = v

            elif check_invalid_arguments and k not in legal_inputs:
                unsupported_parameters.add(k)

            # clean up internal params:
            if k.startswith('_ansible_'):
                del self.params[k]

        if unsupported_parameters:
            msg = "Unsupported parameters for (%s) module: %s" % (self._name, ', '.join(sorted(list(unsupported_parameters))))
            if self._options_context:
                msg += " found in %s." % " -> ".join(self._options_context)
            msg += " Supported parameters include: %s" % (', '.join(sorted(spec.keys())))
            self.fail_json(msg=msg)
        if self.check_mode and not self.supports_check_mode:
            self.exit_json(skipped=True, msg="remote module (%s) does not support check mode" % self._name)

    def _count_terms(self, check, param=None):
        count = 0
        if param is None:
            param = self.params
        for term in check:
            if term in param:
                count += 1
        return count

    def _check_mutually_exclusive(self, spec, param=None):
        if spec is None:
            return
        for check in spec:
            count = self._count_terms(check, param)
            if count > 1:
                msg = "parameters are mutually exclusive: %s" % ', '.join(check)
                if self._options_context:
                    msg += " found in %s" % " -> ".join(self._options_context)
                self.fail_json(msg=msg)

    def _check_required_one_of(self, spec, param=None):
        if spec is None:
            return
        for check in spec:
            count = self._count_terms(check, param)
            if count == 0:
                msg = "one of the following is required: %s" % ', '.join(check)
                if self._options_context:
                    msg += " found in %s" % " -> ".join(self._options_context)
                self.fail_json(msg=msg)

    def _check_required_together(self, spec, param=None):
        if spec is None:
            return
        for check in spec:
            counts = [self._count_terms([field], param) for field in check]
            non_zero = [c for c in counts if c > 0]
            if len(non_zero) > 0:
                if 0 in counts:
                    msg = "parameters are required together: %s" % ', '.join(check)
                    if self._options_context:
                        msg += " found in %s" % " -> ".join(self._options_context)
                    self.fail_json(msg=msg)

    def _check_required_arguments(self, spec=None, param=None):
        ''' ensure all required arguments are present '''
        missing = []
        if spec is None:
            spec = self.argument_spec
        if param is None:
            param = self.params
        for (k, v) in spec.items():
            required = v.get('required', False)
            if required and k not in param:
                missing.append(k)
        if len(missing) > 0:
            msg = "missing required arguments: %s" % ", ".join(missing)
            if self._options_context:
                msg += " found in %s" % " -> ".join(self._options_context)
            self.fail_json(msg=msg)

    def _check_required_if(self, spec, param=None):
        ''' ensure that parameters which conditionally required are present '''
        if spec is None:
            return
        if param is None:
            param = self.params
        for sp in spec:
            missing = []
            max_missing_count = 0
            is_one_of = False
            if len(sp) == 4:
                key, val, requirements, is_one_of = sp
            else:
                key, val, requirements = sp

            # is_one_of is True at least one requirement should be
            # present, else all requirements should be present.
            if is_one_of:
                max_missing_count = len(requirements)
                term = 'any'
            else:
                term = 'all'

            if key in param and param[key] == val:
                for check in requirements:
                    count = self._count_terms((check,), param)
                    if count == 0:
                        missing.append(check)
            if len(missing) and len(missing) >= max_missing_count:
                msg = "%s is %s but %s of the following are missing: %s" % (key, val, term, ', '.join(missing))
                if self._options_context:
                    msg += " found in %s" % " -> ".join(self._options_context)
                self.fail_json(msg=msg)

    def _check_argument_values(self, spec=None, param=None):
        ''' ensure all arguments have the requested values, and there are no stray arguments '''
        if spec is None:
            spec = self.argument_spec
        if param is None:
            param = self.params
        for (k, v) in spec.items():
            choices = v.get('choices', None)
            if choices is None:
                continue
            if isinstance(choices, SEQUENCETYPE) and not isinstance(choices, (binary_type, text_type)):
                if k in param:
                    if param[k] not in choices:
                        # PyYaml converts certain strings to bools.  If we can unambiguously convert back, do so before checking
                        # the value.  If we can't figure this out, module author is responsible.
                        lowered_choices = None
                        if param[k] == 'False':
                            lowered_choices = _lenient_lowercase(choices)
                            overlap = BOOLEANS_FALSE.intersection(choices)
                            if len(overlap) == 1:
                                # Extract from a set
                                (param[k],) = overlap

                        if param[k] == 'True':
                            if lowered_choices is None:
                                lowered_choices = _lenient_lowercase(choices)
                            overlap = BOOLEANS_TRUE.intersection(choices)
                            if len(overlap) == 1:
                                (param[k],) = overlap

                        if param[k] not in choices:
                            choices_str = ", ".join([to_native(c) for c in choices])
                            msg = "value of %s must be one of: %s, got: %s" % (k, choices_str, param[k])
                            if self._options_context:
                                msg += " found in %s" % " -> ".join(self._options_context)
                            self.fail_json(msg=msg)
            else:
                msg = "internal error: choices for argument %s are not iterable: %s" % (k, choices)
                if self._options_context:
                    msg += " found in %s" % " -> ".join(self._options_context)
                self.fail_json(msg=msg)

    def safe_eval(self, value, locals=None, include_exceptions=False):

        # do not allow method calls to modules
        if not isinstance(value, string_types):
            # already templated to a datavaluestructure, perhaps?
            if include_exceptions:
                return (value, None)
            return value
        if re.search(r'\w\.\w+\(', value):
            if include_exceptions:
                return (value, None)
            return value
        # do not allow imports
        if re.search(r'import \w+', value):
            if include_exceptions:
                return (value, None)
            return value
        try:
            result = literal_eval(value)
            if include_exceptions:
                return (result, None)
            else:
                return result
        except Exception as e:
            if include_exceptions:
                return (value, e)
            return value

    def _check_type_str(self, value):
        if isinstance(value, string_types):
            return value
        # Note: This could throw a unicode error if value's __str__() method
        # returns non-ascii.  Have to port utils.to_bytes() if that happens
        return str(value)

    def _check_type_list(self, value):
        if isinstance(value, list):
            return value

        if isinstance(value, string_types):
            return value.split(",")
        elif isinstance(value, int) or isinstance(value, float):
            return [str(value)]

        raise TypeError('%s cannot be converted to a list' % type(value))

    def _check_type_dict(self, value):
        if isinstance(value, dict):
            return value

        if isinstance(value, string_types):
            if value.startswith("{"):
                try:
                    return json.loads(value)
                except:
                    (result, exc) = self.safe_eval(value, dict(), include_exceptions=True)
                    if exc is not None:
                        raise TypeError('unable to evaluate string as dictionary')
                    return result
            elif '=' in value:
                fields = []
                field_buffer = []
                in_quote = False
                in_escape = False
                for c in value.strip():
                    if in_escape:
                        field_buffer.append(c)
                        in_escape = False
                    elif c == '\\':
                        in_escape = True
                    elif not in_quote and c in ('\'', '"'):
                        in_quote = c
                    elif in_quote and in_quote == c:
                        in_quote = False
                    elif not in_quote and c in (',', ' '):
                        field = ''.join(field_buffer)
                        if field:
                            fields.append(field)
                        field_buffer = []
                    else:
                        field_buffer.append(c)

                field = ''.join(field_buffer)
                if field:
                    fields.append(field)
                return dict(x.split("=", 1) for x in fields)
            else:
                raise TypeError("dictionary requested, could not parse JSON or key=value")

        raise TypeError('%s cannot be converted to a dict' % type(value))

    def _check_type_bool(self, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, string_types) or isinstance(value, int):
            return self.boolean(value)

        raise TypeError('%s cannot be converted to a bool' % type(value))

    def _check_type_int(self, value):
        if isinstance(value, int):
            return value

        if isinstance(value, string_types):
            return int(value)

        raise TypeError('%s cannot be converted to an int' % type(value))

    def _check_type_float(self, value):
        if isinstance(value, float):
            return value

        if isinstance(value, (binary_type, text_type, int)):
            return float(value)

        raise TypeError('%s cannot be converted to a float' % type(value))

    def _check_type_path(self, value):
        value = self._check_type_str(value)
        return os.path.expanduser(os.path.expandvars(value))

    def _check_type_jsonarg(self, value):
        # Return a jsonified string.  Sometimes the controller turns a json
        # string into a dict/list so transform it back into json here
        if isinstance(value, (text_type, binary_type)):
            return value.strip()
        else:
            if isinstance(value, (list, tuple, dict)):
                return self.jsonify(value)
        raise TypeError('%s cannot be converted to a json string' % type(value))

    def _check_type_raw(self, value):
        return value

    def _check_type_bytes(self, value):
        try:
            self.human_to_bytes(value)
        except ValueError:
            raise TypeError('%s cannot be converted to a Byte value' % type(value))

    def _check_type_bits(self, value):
        try:
            self.human_to_bytes(value, isbits=True)
        except ValueError:
            raise TypeError('%s cannot be converted to a Bit value' % type(value))

    def _handle_options(self, argument_spec=None, params=None):
        ''' deal with options to create sub spec '''
        if argument_spec is None:
            argument_spec = self.argument_spec
        if params is None:
            params = self.params

        for (k, v) in argument_spec.items():
            wanted = v.get('type', None)
            if wanted == 'dict' or (wanted == 'list' and v.get('elements', '') == 'dict'):
                spec = v.get('options', None)
                if spec is None or k not in params or params[k] is None:
                    continue

                self._options_context.append(k)

                if isinstance(params[k], dict):
                    elements = [params[k]]
                else:
                    elements = params[k]

                for param in elements:
                    if not isinstance(param, dict):
                        self.fail_json(msg="value of %s must be of type dict or list of dict" % k)

                    self._set_fallbacks(spec, param)
                    options_aliases = self._handle_aliases(spec, param)

                    self._handle_no_log_values(spec, param)
                    options_legal_inputs = list(spec.keys()) + list(options_aliases.keys())

                    self._check_arguments(self.check_invalid_arguments, spec, param, options_legal_inputs)

                    # check exclusive early
                    if not self.bypass_checks:
                        self._check_mutually_exclusive(v.get('mutually_exclusive', None), param)

                    self._set_defaults(pre=True, spec=spec, param=param)

                    if not self.bypass_checks:
                        self._check_required_arguments(spec, param)
                        self._check_argument_types(spec, param)
                        self._check_argument_values(spec, param)

                        self._check_required_together(v.get('required_together', None), param)
                        self._check_required_one_of(v.get('required_one_of', None), param)
                        self._check_required_if(v.get('required_if', None), param)

                    self._set_defaults(pre=False, spec=spec, param=param)

                    # handle multi level options (sub argspec)
                    self._handle_options(spec, param)
                self._options_context.pop()

    def _check_argument_types(self, spec=None, param=None):
        ''' ensure all arguments have the requested type '''

        if spec is None:
            spec = self.argument_spec
        if param is None:
            param = self.params

        for (k, v) in spec.items():
            wanted = v.get('type', None)
            if k not in param:
                continue

            value = param[k]
            if value is None:
                continue

            if not callable(wanted):
                if wanted is None:
                    # Mostly we want to default to str.
                    # For values set to None explicitly, return None instead as
                    # that allows a user to unset a parameter
                    if param[k] is None:
                        continue
                    wanted = 'str'
                try:
                    type_checker = self._CHECK_ARGUMENT_TYPES_DISPATCHER[wanted]
                except KeyError:
                    self.fail_json(msg="implementation error: unknown type %s requested for %s" % (wanted, k))
            else:
                # set the type_checker to the callable, and reset wanted to the callable's name (or type if it doesn't have one, ala MagicMock)
                type_checker = wanted
                wanted = getattr(wanted, '__name__', to_native(type(wanted)))

            try:
                param[k] = type_checker(value)
            except (TypeError, ValueError) as e:
                self.fail_json(msg="argument %s is of type %s and we were unable to convert to %s: %s" %
                               (k, type(value), wanted, to_native(e)))

    def _set_defaults(self, pre=True, spec=None, param=None):
        if spec is None:
            spec = self.argument_spec
        if param is None:
            param = self.params
        for (k, v) in spec.items():
            default = v.get('default', None)
            if pre is True:
                # this prevents setting defaults on required items
                if default is not None and k not in param:
                    param[k] = default
            else:
                # make sure things without a default still get set None
                if k not in param:
                    param[k] = default

    def _set_fallbacks(self, spec=None, param=None):
        if spec is None:
            spec = self.argument_spec
        if param is None:
            param = self.params

        for (k, v) in spec.items():
            fallback = v.get('fallback', (None,))
            fallback_strategy = fallback[0]
            fallback_args = []
            fallback_kwargs = {}
            if k not in param and fallback_strategy is not None:
                for item in fallback[1:]:
                    if isinstance(item, dict):
                        fallback_kwargs = item
                    else:
                        fallback_args = item
                try:
                    param[k] = fallback_strategy(*fallback_args, **fallback_kwargs)
                except AnsibleFallbackNotFound:
                    continue

    def _load_params(self):
        ''' read the input and set the params attribute.

        This method is for backwards compatibility.  The guts of the function
        were moved out in 2.1 so that custom modules could read the parameters.
        '''
        # debug overrides to read args from file or cmdline
        self.params = _load_params()

    def _log_to_syslog(self, msg):
        if HAS_SYSLOG:
            module = 'ansible-%s' % self._name
            facility = getattr(syslog, self._syslog_facility, syslog.LOG_USER)
            syslog.openlog(str(module), 0, facility)
            syslog.syslog(syslog.LOG_INFO, msg)

    def debug(self, msg):
        if self._debug:
            self.log('[debug] %s' % msg)

    def log(self, msg, log_args=None):

        if not self.no_log:

            if log_args is None:
                log_args = dict()

            module = 'ansible-%s' % self._name
            if isinstance(module, binary_type):
                module = module.decode('utf-8', 'replace')

            # 6655 - allow for accented characters
            if not isinstance(msg, (binary_type, text_type)):
                raise TypeError("msg should be a string (got %s)" % type(msg))

            # We want journal to always take text type
            # syslog takes bytes on py2, text type on py3
            if isinstance(msg, binary_type):
                journal_msg = remove_values(msg.decode('utf-8', 'replace'), self.no_log_values)
            else:
                # TODO: surrogateescape is a danger here on Py3
                journal_msg = remove_values(msg, self.no_log_values)

            if PY3:
                syslog_msg = journal_msg
            else:
                syslog_msg = journal_msg.encode('utf-8', 'replace')

            if has_journal:
                journal_args = [("MODULE", os.path.basename(__file__))]
                for arg in log_args:
                    journal_args.append((arg.upper(), str(log_args[arg])))
                try:
                    journal.send(u"%s %s" % (module, journal_msg), **dict(journal_args))
                except IOError:
                    # fall back to syslog since logging to journal failed
                    self._log_to_syslog(syslog_msg)
            else:
                self._log_to_syslog(syslog_msg)

    def _log_invocation(self):
        ''' log that ansible ran the module '''
        # TODO: generalize a separate log function and make log_invocation use it
        # Sanitize possible password argument when logging.
        log_args = dict()

        for param in self.params:
            canon = self.aliases.get(param, param)
            arg_opts = self.argument_spec.get(canon, {})
            no_log = arg_opts.get('no_log', False)

            if self.boolean(no_log):
                log_args[param] = 'NOT_LOGGING_PARAMETER'
            # try to capture all passwords/passphrase named fields missed by no_log
            elif PASSWORD_MATCH.search(param) and arg_opts.get('type', 'str') != 'bool' and not arg_opts.get('choices', False):
                # skip boolean and enums as they are about 'password' state
                log_args[param] = 'NOT_LOGGING_PASSWORD'
                self.warn('Module did not set no_log for %s' % param)
            else:
                param_val = self.params[param]
                if not isinstance(param_val, (text_type, binary_type)):
                    param_val = str(param_val)
                elif isinstance(param_val, text_type):
                    param_val = param_val.encode('utf-8')
                log_args[param] = heuristic_log_sanitize(param_val, self.no_log_values)

        msg = ['%s=%s' % (to_native(arg), to_native(val)) for arg, val in log_args.items()]
        if msg:
            msg = 'Invoked with %s' % ' '.join(msg)
        else:
            msg = 'Invoked'

        self.log(msg, log_args=log_args)

    def _set_cwd(self):
        try:
            cwd = os.getcwd()
            if not os.access(cwd, os.F_OK | os.R_OK):
                raise Exception()
            return cwd
        except:
            # we don't have access to the cwd, probably because of sudo.
            # Try and move to a neutral location to prevent errors
            for cwd in [os.path.expandvars('$HOME'), tempfile.gettempdir()]:
                try:
                    if os.access(cwd, os.F_OK | os.R_OK):
                        os.chdir(cwd)
                        return cwd
                except:
                    pass
        # we won't error here, as it may *not* be a problem,
        # and we don't want to break modules unnecessarily
        return None

    def get_bin_path(self, arg, required=False, opt_dirs=None):
        '''
        find system executable in PATH.
        Optional arguments:
           - required:  if executable is not found and required is true, fail_json
           - opt_dirs:  optional list of directories to search in addition to PATH
        if found return full path; otherwise return None
        '''
        opt_dirs = [] if opt_dirs is None else opt_dirs

        sbin_paths = ['/sbin', '/usr/sbin', '/usr/local/sbin']
        paths = []
        for d in opt_dirs:
            if d is not None and os.path.exists(d):
                paths.append(d)
        paths += os.environ.get('PATH', '').split(os.pathsep)
        bin_path = None
        # mangle PATH to include /sbin dirs
        for p in sbin_paths:
            if p not in paths and os.path.exists(p):
                paths.append(p)
        for d in paths:
            if not d:
                continue
            path = os.path.join(d, arg)
            if os.path.exists(path) and not os.path.isdir(path) and is_executable(path):
                bin_path = path
                break
        if required and bin_path is None:
            self.fail_json(msg='Failed to find required executable %s in paths: %s' % (arg, os.pathsep.join(paths)))
        return bin_path

    def boolean(self, arg):
        ''' return a bool for the arg '''
        if arg is None:
            return arg

        try:
            return boolean(arg)
        except TypeError as e:
            self.fail_json(msg=to_native(e))

    def jsonify(self, data):
        try:
            return jsonify(data)
        except UnicodeError as e:
            self.fail_json(msg=to_text(e))

    def from_json(self, data):
        return json.loads(data)

    def add_cleanup_file(self, path):
        if path not in self.cleanup_files:
            self.cleanup_files.append(path)

    def do_cleanup_files(self):
        for path in self.cleanup_files:
            self.cleanup(path)

    def _return_formatted(self, kwargs):

        self.add_path_info(kwargs)

        if 'invocation' not in kwargs:
            kwargs['invocation'] = {'module_args': self.params}

        if 'warnings' in kwargs:
            if isinstance(kwargs['warnings'], list):
                for w in kwargs['warnings']:
                    self.warn(w)
            else:
                self.warn(kwargs['warnings'])

        if self._warnings:
            kwargs['warnings'] = self._warnings

        if 'deprecations' in kwargs:
            if isinstance(kwargs['deprecations'], list):
                for d in kwargs['deprecations']:
                    if isinstance(d, SEQUENCETYPE) and len(d) == 2:
                        self.deprecate(d[0], version=d[1])
                    else:
                        self.deprecate(d)
            else:
                self.deprecate(kwargs['deprecations'])

        if self._deprecations:
            kwargs['deprecations'] = self._deprecations

        kwargs = remove_values(kwargs, self.no_log_values)
        print('\n%s' % self.jsonify(kwargs))

    def exit_json(self, **kwargs):
        ''' return from the module, without error '''

        self.do_cleanup_files()
        self._return_formatted(kwargs)
        sys.exit(0)

    def fail_json(self, **kwargs):
        ''' return from the module, with an error message '''

        if 'msg' not in kwargs:
            raise AssertionError("implementation error -- msg to explain the error is required")
        kwargs['failed'] = True

        # add traceback if debug or high verbosity and it is missing
        # Note: badly named as exception, it is really always been 'traceback'
        if 'exception' not in kwargs and sys.exc_info()[2] and (self._debug or self._verbosity >= 3):
            kwargs['exception'] = ''.join(traceback.format_tb(sys.exc_info()[2]))

        self.do_cleanup_files()
        self._return_formatted(kwargs)
        sys.exit(1)

    def fail_on_missing_params(self, required_params=None):
        ''' This is for checking for required params when we can not check via argspec because we
        need more information than is simply given in the argspec.
        '''
        if not required_params:
            return
        missing_params = []
        for required_param in required_params:
            if not self.params.get(required_param):
                missing_params.append(required_param)
        if missing_params:
            self.fail_json(msg="missing required arguments: %s" % ', '.join(missing_params))

    def digest_from_file(self, filename, algorithm):
        ''' Return hex digest of local file for a digest_method specified by name, or None if file is not present. '''
        if not os.path.exists(filename):
            return None
        if os.path.isdir(filename):
            self.fail_json(msg="attempted to take checksum of directory: %s" % filename)

        # preserve old behaviour where the third parameter was a hash algorithm object
        if hasattr(algorithm, 'hexdigest'):
            digest_method = algorithm
        else:
            try:
                digest_method = AVAILABLE_HASH_ALGORITHMS[algorithm]()
            except KeyError:
                self.fail_json(msg="Could not hash file '%s' with algorithm '%s'. Available algorithms: %s" %
                                   (filename, algorithm, ', '.join(AVAILABLE_HASH_ALGORITHMS)))

        blocksize = 64 * 1024
        infile = open(os.path.realpath(filename), 'rb')
        block = infile.read(blocksize)
        while block:
            digest_method.update(block)
            block = infile.read(blocksize)
        infile.close()
        return digest_method.hexdigest()

    def md5(self, filename):
        ''' Return MD5 hex digest of local file using digest_from_file().

        Do not use this function unless you have no other choice for:
            1) Optional backwards compatibility
            2) Compatibility with a third party protocol

        This function will not work on systems complying with FIPS-140-2.

        Most uses of this function can use the module.sha1 function instead.
        '''
        if 'md5' not in AVAILABLE_HASH_ALGORITHMS:
            raise ValueError('MD5 not available.  Possibly running in FIPS mode')
        return self.digest_from_file(filename, 'md5')

    def sha1(self, filename):
        ''' Return SHA1 hex digest of local file using digest_from_file(). '''
        return self.digest_from_file(filename, 'sha1')

    def sha256(self, filename):
        ''' Return SHA-256 hex digest of local file using digest_from_file(). '''
        return self.digest_from_file(filename, 'sha256')

    def backup_local(self, fn):
        '''make a date-marked backup of the specified file, return True or False on success or failure'''

        backupdest = ''
        if os.path.exists(fn):
            # backups named basename.PID.YYYY-MM-DD@HH:MM:SS~
            ext = time.strftime("%Y-%m-%d@%H:%M:%S~", time.localtime(time.time()))
            backupdest = '%s.%s.%s' % (fn, os.getpid(), ext)

            try:
                self.preserved_copy(fn, backupdest)
            except (shutil.Error, IOError) as e:
                self.fail_json(msg='Could not make backup of %s to %s: %s' % (fn, backupdest, to_native(e)))

        return backupdest

    def cleanup(self, tmpfile):
        if os.path.exists(tmpfile):
            try:
                os.unlink(tmpfile)
            except OSError as e:
                sys.stderr.write("could not cleanup %s: %s" % (tmpfile, to_native(e)))

    def preserved_copy(self, src, dest):
        """Copy a file with preserved ownership, permissions and context"""

        # shutil.copy2(src, dst)
        #   Similar to shutil.copy(), but metadata is copied as well - in fact,
        #   this is just shutil.copy() followed by copystat(). This is similar
        #   to the Unix command cp -p.
        #
        # shutil.copystat(src, dst)
        #   Copy the permission bits, last access time, last modification time,
        #   and flags from src to dst. The file contents, owner, and group are
        #   unaffected. src and dst are path names given as strings.

        shutil.copy2(src, dest)

        # Set the context
        if self.selinux_enabled():
            context = self.selinux_context(src)
            self.set_context_if_different(dest, context, False)

        # chown it
        try:
            dest_stat = os.stat(src)
            tmp_stat = os.stat(dest)
            if dest_stat and (tmp_stat.st_uid != dest_stat.st_uid or tmp_stat.st_gid != dest_stat.st_gid):
                os.chown(dest, dest_stat.st_uid, dest_stat.st_gid)
        except OSError as e:
            if e.errno != errno.EPERM:
                raise

        # Set the attributes
        current_attribs = self.get_file_attributes(src)
        current_attribs = current_attribs.get('attr_flags', '')
        self.set_attributes_if_different(dest, current_attribs, True)

    def atomic_move(self, src, dest, unsafe_writes=False):
        '''atomically move src to dest, copying attributes from dest, returns true on success
        it uses os.rename to ensure this as it is an atomic operation, rest of the function is
        to work around limitations, corner cases and ensure selinux context is saved if possible'''
        context = None
        dest_stat = None
        b_src = to_bytes(src, errors='surrogate_or_strict')
        b_dest = to_bytes(dest, errors='surrogate_or_strict')
        if os.path.exists(b_dest):
            try:
                dest_stat = os.stat(b_dest)

                # copy mode and ownership
                os.chmod(b_src, dest_stat.st_mode & PERM_BITS)
                os.chown(b_src, dest_stat.st_uid, dest_stat.st_gid)

                # try to copy flags if possible
                if hasattr(os, 'chflags') and hasattr(dest_stat, 'st_flags'):
                    try:
                        os.chflags(b_src, dest_stat.st_flags)
                    except OSError as e:
                        for err in 'EOPNOTSUPP', 'ENOTSUP':
                            if hasattr(errno, err) and e.errno == getattr(errno, err):
                                break
                        else:
                            raise
            except OSError as e:
                if e.errno != errno.EPERM:
                    raise
            if self.selinux_enabled():
                context = self.selinux_context(dest)
        else:
            if self.selinux_enabled():
                context = self.selinux_default_context(dest)

        creating = not os.path.exists(b_dest)

        try:
            # Optimistically try a rename, solves some corner cases and can avoid useless work, throws exception if not atomic.
            os.rename(b_src, b_dest)
        except (IOError, OSError) as e:
            if e.errno not in [errno.EPERM, errno.EXDEV, errno.EACCES, errno.ETXTBSY, errno.EBUSY]:
                # only try workarounds for errno 18 (cross device), 1 (not permitted),  13 (permission denied)
                # and 26 (text file busy) which happens on vagrant synced folders and other 'exotic' non posix file systems
                self.fail_json(msg='Could not replace file: %s to %s: %s' % (src, dest, to_native(e)),
                               exception=traceback.format_exc())
            else:
                b_dest_dir = os.path.dirname(b_dest)
                # Use bytes here.  In the shippable CI, this fails with
                # a UnicodeError with surrogateescape'd strings for an unknown
                # reason (doesn't happen in a local Ubuntu16.04 VM)
                native_dest_dir = b_dest_dir
                native_suffix = os.path.basename(b_dest)
                native_prefix = b('.ansible_tmp')
                error_msg = None
                tmp_dest_name = None
                try:
                    tmp_dest_fd, tmp_dest_name = tempfile.mkstemp(prefix=native_prefix, dir=native_dest_dir, suffix=native_suffix)
                except (OSError, IOError) as e:
                    error_msg = 'The destination directory (%s) is not writable by the current user. Error was: %s' % (os.path.dirname(dest), to_native(e))
                except TypeError:
                    # We expect that this is happening because python3.4.x and
                    # below can't handle byte strings in mkstemp().  Traceback
                    # would end in something like:
                    #     file = _os.path.join(dir, pre + name + suf)
                    # TypeError: can't concat bytes to str
                    error_msg = ('Failed creating temp file for atomic move.  This usually happens when using Python3 less than Python3.5. '
                                 'Please use Python2.x or Python3.5 or greater.')
                finally:
                    if error_msg:
                        if unsafe_writes:
                            self._unsafe_writes(b_src, b_dest)
                        else:
                            self.fail_json(msg=error_msg, exception=traceback.format_exc())

                if tmp_dest_name:
                    b_tmp_dest_name = to_bytes(tmp_dest_name, errors='surrogate_or_strict')

                    try:
                        try:
                            # close tmp file handle before file operations to prevent text file busy errors on vboxfs synced folders (windows host)
                            os.close(tmp_dest_fd)
                            # leaves tmp file behind when sudo and not root
                            try:
                                shutil.move(b_src, b_tmp_dest_name)
                            except OSError:
                                # cleanup will happen by 'rm' of tempdir
                                # copy2 will preserve some metadata
                                shutil.copy2(b_src, b_tmp_dest_name)

                            if self.selinux_enabled():
                                self.set_context_if_different(
                                    b_tmp_dest_name, context, False)
                            try:
                                tmp_stat = os.stat(b_tmp_dest_name)
                                if dest_stat and (tmp_stat.st_uid != dest_stat.st_uid or tmp_stat.st_gid != dest_stat.st_gid):
                                    os.chown(b_tmp_dest_name, dest_stat.st_uid, dest_stat.st_gid)
                            except OSError as e:
                                if e.errno != errno.EPERM:
                                    raise
                            try:
                                os.rename(b_tmp_dest_name, b_dest)
                            except (shutil.Error, OSError, IOError) as e:
                                if unsafe_writes and e.errno == errno.EBUSY:
                                    self._unsafe_writes(b_tmp_dest_name, b_dest)
                                else:
                                    self.fail_json(msg='Unable to rename file: %s to %s: %s' % (src, dest, to_native(e)),
                                                   exception=traceback.format_exc())
                        except (shutil.Error, OSError, IOError) as e:
                            self.fail_json(msg='Failed to replace file: %s to %s: %s' % (src, dest, to_native(e)),
                                           exception=traceback.format_exc())
                    finally:
                        self.cleanup(b_tmp_dest_name)

        if creating:
            # make sure the file has the correct permissions
            # based on the current value of umask
            umask = os.umask(0)
            os.umask(umask)
            os.chmod(b_dest, DEFAULT_PERM & ~umask)
            try:
                os.chown(b_dest, os.geteuid(), os.getegid())
            except OSError:
                # We're okay with trying our best here.  If the user is not
                # root (or old Unices) they won't be able to chown.
                pass

        if self.selinux_enabled():
            # rename might not preserve context
            self.set_context_if_different(dest, context, False)

    def _unsafe_writes(self, src, dest):
        # sadly there are some situations where we cannot ensure atomicity, but only if
        # the user insists and we get the appropriate error we update the file unsafely
        try:
            out_dest = in_src = None
            try:
                out_dest = open(dest, 'wb')
                in_src = open(src, 'rb')
                shutil.copyfileobj(in_src, out_dest)
            finally:  # assuring closed files in 2.4 compatible way
                if out_dest:
                    out_dest.close()
                if in_src:
                    in_src.close()
        except (shutil.Error, OSError, IOError) as e:
            self.fail_json(msg='Could not write data to file (%s) from (%s): %s' % (dest, src, to_native(e)),
                           exception=traceback.format_exc())

    def _read_from_pipes(self, rpipes, rfds, file_descriptor):
        data = b('')
        if file_descriptor in rfds:
            data = os.read(file_descriptor.fileno(), 9000)
            if data == b(''):
                rpipes.remove(file_descriptor)

        return data

    def _clean_args(self, args):

        if not self._clean:
            # create a printable version of the command for use in reporting later,
            # which strips out things like passwords from the args list
            to_clean_args = args
            if PY2:
                if isinstance(args, text_type):
                    to_clean_args = to_bytes(args)
            else:
                if isinstance(args, binary_type):
                    to_clean_args = to_text(args)
            if isinstance(args, (text_type, binary_type)):
                to_clean_args = shlex.split(to_clean_args)

            clean_args = []
            is_passwd = False
            for arg in (to_native(a) for a in to_clean_args):
                if is_passwd:
                    is_passwd = False
                    clean_args.append('********')
                    continue
                if PASSWD_ARG_RE.match(arg):
                    sep_idx = arg.find('=')
                    if sep_idx > -1:
                        clean_args.append('%s=********' % arg[:sep_idx])
                        continue
                    else:
                        is_passwd = True
                arg = heuristic_log_sanitize(arg, self.no_log_values)
                clean_args.append(arg)
            self._clean = ' '.join(shlex_quote(arg) for arg in clean_args)

        return self._clean

    def run_command(self, args, check_rc=False, close_fds=True, executable=None, data=None, binary_data=False, path_prefix=None, cwd=None,
                    use_unsafe_shell=False, prompt_regex=None, environ_update=None, umask=None, encoding='utf-8', errors='surrogate_or_strict'):
        '''
        Execute a command, returns rc, stdout, and stderr.

        :arg args: is the command to run
            * If args is a list, the command will be run with shell=False.
            * If args is a string and use_unsafe_shell=False it will split args to a list and run with shell=False
            * If args is a string and use_unsafe_shell=True it runs with shell=True.
        :kw check_rc: Whether to call fail_json in case of non zero RC.
            Default False
        :kw close_fds: See documentation for subprocess.Popen(). Default True
        :kw executable: See documentation for subprocess.Popen(). Default None
        :kw data: If given, information to write to the stdin of the command
        :kw binary_data: If False, append a newline to the data.  Default False
        :kw path_prefix: If given, additional path to find the command in.
            This adds to the PATH environment vairable so helper commands in
            the same directory can also be found
        :kw cwd: If given, working directory to run the command inside
        :kw use_unsafe_shell: See `args` parameter.  Default False
        :kw prompt_regex: Regex string (not a compiled regex) which can be
            used to detect prompts in the stdout which would otherwise cause
            the execution to hang (especially if no input data is specified)
        :kw environ_update: dictionary to *update* os.environ with
        :kw umask: Umask to be used when running the command. Default None
        :kw encoding: Since we return native strings, on python3 we need to
            know the encoding to use to transform from bytes to text.  If you
            want to always get bytes back, use encoding=None.  The default is
            "utf-8".  This does not affect transformation of strings given as
            args.
        :kw errors: Since we return native strings, on python3 we need to
            transform stdout and stderr from bytes to text.  If the bytes are
            undecodable in the ``encoding`` specified, then use this error
            handler to deal with them.  The default is ``surrogate_or_strict``
            which means that the bytes will be decoded using the
            surrogateescape error handler if available (available on all
            python3 versions we support) otherwise a UnicodeError traceback
            will be raised.  This does not affect transformations of strings
            given as args.
        :returns: A 3-tuple of return code (integer), stdout (native string),
            and stderr (native string).  On python2, stdout and stderr are both
            byte strings.  On python3, stdout and stderr are text strings converted
            according to the encoding and errors parameters.  If you want byte
            strings on python3, use encoding=None to turn decoding to text off.
        '''
        # used by clean args later on
        self._clean = None

        if not isinstance(args, (list, binary_type, text_type)):
            msg = "Argument 'args' to run_command must be list or string"
            self.fail_json(rc=257, cmd=args, msg=msg)

        shell = False
        if use_unsafe_shell:

            # stringify args for unsafe/direct shell usage
            if isinstance(args, list):
                args = " ".join([shlex_quote(x) for x in args])

            # not set explicitly, check if set by controller
            if executable:
                args = [executable, '-c', args]
            elif self._shell not in (None, '/bin/sh'):
                args = [self._shell, '-c', args]
            else:
                shell = True
        else:
            # ensure args are a list
            if isinstance(args, (binary_type, text_type)):
                # On python2.6 and below, shlex has problems with text type
                # On python3, shlex needs a text type.
                if PY2:
                    args = to_bytes(args, errors='surrogate_or_strict')
                elif PY3:
                    args = to_text(args, errors='surrogateescape')
                args = shlex.split(args)

            # expand shellisms
            args = [os.path.expanduser(os.path.expandvars(x)) for x in args if x is not None]

        prompt_re = None
        if prompt_regex:
            if isinstance(prompt_regex, text_type):
                if PY3:
                    prompt_regex = to_bytes(prompt_regex, errors='surrogateescape')
                elif PY2:
                    prompt_regex = to_bytes(prompt_regex, errors='surrogate_or_strict')
            try:
                prompt_re = re.compile(prompt_regex, re.MULTILINE)
            except re.error:
                self.fail_json(msg="invalid prompt regular expression given to run_command")

        rc = 0
        msg = None
        st_in = None

        # Manipulate the environ we'll send to the new process
        old_env_vals = {}
        # We can set this from both an attribute and per call
        for key, val in self.run_command_environ_update.items():
            old_env_vals[key] = os.environ.get(key, None)
            os.environ[key] = val
        if environ_update:
            for key, val in environ_update.items():
                old_env_vals[key] = os.environ.get(key, None)
                os.environ[key] = val
        if path_prefix:
            old_env_vals['PATH'] = os.environ['PATH']
            os.environ['PATH'] = "%s:%s" % (path_prefix, os.environ['PATH'])

        # If using test-module and explode, the remote lib path will resemble ...
        #   /tmp/test_module_scratch/debug_dir/ansible/module_utils/basic.py
        # If using ansible or ansible-playbook with a remote system ...
        #   /tmp/ansible_vmweLQ/ansible_modlib.zip/ansible/module_utils/basic.py

        # Clean out python paths set by ansiballz
        if 'PYTHONPATH' in os.environ:
            pypaths = os.environ['PYTHONPATH'].split(':')
            pypaths = [x for x in pypaths
                       if not x.endswith('/ansible_modlib.zip') and
                       not x.endswith('/debug_dir')]
            os.environ['PYTHONPATH'] = ':'.join(pypaths)
            if not os.environ['PYTHONPATH']:
                del os.environ['PYTHONPATH']

        if data:
            st_in = subprocess.PIPE

        kwargs = dict(
            executable=executable,
            shell=shell,
            close_fds=close_fds,
            stdin=st_in,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # store the pwd
        prev_dir = os.getcwd()

        # make sure we're in the right working directory
        if cwd and os.path.isdir(cwd):
            cwd = os.path.abspath(os.path.expanduser(cwd))
            kwargs['cwd'] = cwd
            try:
                os.chdir(cwd)
            except (OSError, IOError) as e:
                self.fail_json(rc=e.errno, msg="Could not open %s, %s" % (cwd, to_native(e)),
                               exception=traceback.format_exc())

        old_umask = None
        if umask:
            old_umask = os.umask(umask)

        try:
            if self._debug:
                self.log('Executing: ' + self._clean_args(args))
            cmd = subprocess.Popen(args, **kwargs)

            # the communication logic here is essentially taken from that
            # of the _communicate() function in ssh.py

            stdout = b('')
            stderr = b('')
            rpipes = [cmd.stdout, cmd.stderr]

            if data:
                if not binary_data:
                    data += '\n'
                if isinstance(data, text_type):
                    data = to_bytes(data)
                cmd.stdin.write(data)
                cmd.stdin.close()

            while True:
                rfds, wfds, efds = select.select(rpipes, [], rpipes, 1)
                stdout += self._read_from_pipes(rpipes, rfds, cmd.stdout)
                stderr += self._read_from_pipes(rpipes, rfds, cmd.stderr)
                # if we're checking for prompts, do it now
                if prompt_re:
                    if prompt_re.search(stdout) and not data:
                        if encoding:
                            stdout = to_native(stdout, encoding=encoding, errors=errors)
                        else:
                            stdout = stdout
                        return (257, stdout, "A prompt was encountered while running a command, but no input data was specified")
                # only break out if no pipes are left to read or
                # the pipes are completely read and
                # the process is terminated
                if (not rpipes or not rfds) and cmd.poll() is not None:
                    break
                # No pipes are left to read but process is not yet terminated
                # Only then it is safe to wait for the process to be finished
                # NOTE: Actually cmd.poll() is always None here if rpipes is empty
                elif not rpipes and cmd.poll() is None:
                    cmd.wait()
                    # The process is terminated. Since no pipes to read from are
                    # left, there is no need to call select() again.
                    break

            cmd.stdout.close()
            cmd.stderr.close()

            rc = cmd.returncode
        except (OSError, IOError) as e:
            self.log("Error Executing CMD:%s Exception:%s" % (self._clean_args(args), to_native(e)))
            self.fail_json(rc=e.errno, msg=to_native(e), cmd=self._clean_args(args))
        except Exception as e:
            self.log("Error Executing CMD:%s Exception:%s" % (self._clean_args(args), to_native(traceback.format_exc())))
            self.fail_json(rc=257, msg=to_native(e), exception=traceback.format_exc(), cmd=self._clean_args(args))

        # Restore env settings
        for key, val in old_env_vals.items():
            if val is None:
                del os.environ[key]
            else:
                os.environ[key] = val

        if old_umask:
            os.umask(old_umask)

        if rc != 0 and check_rc:
            msg = heuristic_log_sanitize(stderr.rstrip(), self.no_log_values)
            self.fail_json(cmd=self._clean_args(args), rc=rc, stdout=stdout, stderr=stderr, msg=msg)

        # reset the pwd
        os.chdir(prev_dir)

        if encoding is not None:
            return (rc, to_native(stdout, encoding=encoding, errors=errors),
                    to_native(stderr, encoding=encoding, errors=errors))

        return (rc, stdout, stderr)

    def append_to_file(self, filename, str):
        filename = os.path.expandvars(os.path.expanduser(filename))
        fh = open(filename, 'a')
        fh.write(str)
        fh.close()

    def bytes_to_human(self, size):
        return bytes_to_human(size)

    # for backwards compatibility
    pretty_bytes = bytes_to_human

    def human_to_bytes(self, number, isbits=False):
        return human_to_bytes(number, isbits)

    #
    # Backwards compat
    #

    # In 2.0, moved from inside the module to the toplevel
    is_executable = is_executable


def get_module_path():
    return os.path.dirname(os.path.realpath(__file__))
