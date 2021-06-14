# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com> 2016
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

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

# Ansible modules can be written in any language.
# The functions available here can be used to do many common tasks,
# to simplify development of Python modules.

import __main__
import atexit
import errno
import datetime
import grp
import fcntl
import locale
import os
import pwd
import platform
import re
import select
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import traceback
import types

from itertools import chain, repeat

try:
    import syslog
    HAS_SYSLOG = True
except ImportError:
    HAS_SYSLOG = False

try:
    from systemd import journal
    # Makes sure that systemd.journal has method sendv()
    # Double check that journal has method sendv (some packages don't)
    has_journal = hasattr(journal, 'sendv')
except ImportError:
    has_journal = False

HAVE_SELINUX = False
try:
    import ansible.module_utils.compat.selinux as selinux
    HAVE_SELINUX = True
except ImportError:
    pass

# Python2 & 3 way to get NoneType
NoneType = type(None)

from ansible.module_utils.compat import selectors

from ._text import to_native, to_bytes, to_text
from ansible.module_utils.common.text.converters import (
    jsonify,
    container_to_bytes as json_dict_unicode_to_bytes,
    container_to_text as json_dict_bytes_to_unicode,
)

from ansible.module_utils.common.arg_spec import ModuleArgumentSpecValidator

from ansible.module_utils.common.text.formatters import (
    lenient_lowercase,
    bytes_to_human,
    human_to_bytes,
    SIZE_RANGES,
)

try:
    from ansible.module_utils.common._json_compat import json
except ImportError as e:
    print('\n{{"msg": "Error: ansible requires the stdlib json: {0}", "failed": true}}'.format(to_native(e)))
    sys.exit(1)


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

    # we may have been able to import md5 but it could still not be available
    try:
        hashlib.md5()
    except ValueError:
        AVAILABLE_HASH_ALGORITHMS.pop('md5', None)
except Exception:
    import sha
    AVAILABLE_HASH_ALGORITHMS = {'sha1': sha.sha}
    try:
        import md5
        AVAILABLE_HASH_ALGORITHMS['md5'] = md5.md5
    except Exception:
        pass

from ansible.module_utils.common._collections_compat import (
    KeysView,
    Mapping, MutableMapping,
    Sequence, MutableSequence,
    Set, MutableSet,
)
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.common.file import (
    _PERM_BITS as PERM_BITS,
    _EXEC_PERM_BITS as EXEC_PERM_BITS,
    _DEFAULT_PERM as DEFAULT_PERM,
    is_executable,
    format_attributes,
    get_flags_from_attributes,
)
from ansible.module_utils.common.sys_info import (
    get_distribution,
    get_distribution_version,
    get_platform_subclass,
)
from ansible.module_utils.pycompat24 import get_exception, literal_eval
from ansible.module_utils.common.parameters import (
    env_fallback,
    remove_values,
    sanitize_keys,
    DEFAULT_TYPE_VALIDATORS,
    PASS_VARS,
    PASS_BOOLS,
)

from ansible.module_utils.errors import AnsibleFallbackNotFound, AnsibleValidationErrorMultiple, UnsupportedError
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
from ansible.module_utils.common.validation import (
    check_missing_parameters,
    safe_eval,
)
from ansible.module_utils.common._utils import get_all_subclasses as _get_all_subclasses
from ansible.module_utils.parsing.convert_bool import BOOLEANS, BOOLEANS_FALSE, BOOLEANS_TRUE, boolean
from ansible.module_utils.common.warnings import (
    deprecate,
    get_deprecation_messages,
    get_warning_messages,
    warn,
)

# Note: When getting Sequence from collections, it matches with strings. If
# this matters, make sure to check for strings before checking for sequencetype
SEQUENCETYPE = frozenset, KeysView, Sequence

PASSWORD_MATCH = re.compile(r'^(?:.+[-_\s])?pass(?:[-_\s]?(?:word|phrase|wrd|wd)?)(?:[-_\s].+)?$', re.I)

imap = map

try:
    # Python 2
    unicode
except NameError:
    # Python 3
    unicode = text_type

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
    # These are things we want. About setting metadata (mode, ownership, permissions in general) on
    # created files (these are used by set_fs_attributes_if_different and included in
    # load_file_common_arguments)
    mode=dict(type='raw'),
    owner=dict(type='str'),
    group=dict(type='str'),
    seuser=dict(type='str'),
    serole=dict(type='str'),
    selevel=dict(type='str'),
    setype=dict(type='str'),
    attributes=dict(type='str', aliases=['attr']),
    unsafe_writes=dict(type='bool', default=False, fallback=(env_fallback, ['ANSIBLE_UNSAFE_WRITES'])),  # should be available to any module using atomic_move
)

PASSWD_ARG_RE = re.compile(r'^[-]{0,2}pass[-]?(word|wd)?')

# Used for parsing symbolic file perms
MODE_OPERATOR_RE = re.compile(r'[+=-]')
USERS_RE = re.compile(r'[^ugo]')
PERMS_RE = re.compile(r'[^rwxXstugo]')

# Used for determining if the system is running a new enough python version
# and should only restrict on our documented minimum versions
_PY3_MIN = sys.version_info[:2] >= (3, 5)
_PY2_MIN = (2, 6) <= sys.version_info[:2] < (3,)
_PY_MIN = _PY3_MIN or _PY2_MIN
if not _PY_MIN:
    print(
        '\n{"failed": true, '
        '"msg": "Ansible requires a minimum of Python2 version 2.6 or Python3 version 3.5. Current version: %s"}' % ''.join(sys.version.splitlines())
    )
    sys.exit(1)


#
# Deprecated functions
#

def get_platform():
    '''
    **Deprecated** Use :py:func:`platform.system` directly.

    :returns: Name of the platform the module is running on in a native string

    Returns a native string that labels the platform ("Linux", "Solaris", etc). Currently, this is
    the result of calling :py:func:`platform.system`.
    '''
    return platform.system()

# End deprecated functions


#
# Compat shims
#

def load_platform_subclass(cls, *args, **kwargs):
    """**Deprecated**: Use ansible.module_utils.common.sys_info.get_platform_subclass instead"""
    platform_cls = get_platform_subclass(cls)
    return super(cls, platform_cls).__new__(platform_cls)


def get_all_subclasses(cls):
    """**Deprecated**: Use ansible.module_utils.common._utils.get_all_subclasses instead"""
    return list(_get_all_subclasses(cls))


# End compat shims


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


def missing_required_lib(library, reason=None, url=None):
    hostname = platform.node()
    msg = "Failed to import the required Python library (%s) on %s's Python %s." % (library, hostname, sys.executable)
    if reason:
        msg += " This is required %s." % reason
    if url:
        msg += " See %s for more info." % url

    msg += (" Please read the module documentation and install it in the appropriate location."
            " If the required library is installed, but Ansible is using the wrong Python interpreter,"
            " please consult the documentation on ansible_python_interpreter")
    return msg


class AnsibleModule(object):
    def __init__(self, argument_spec, bypass_checks=False, no_log=False,
                 mutually_exclusive=None, required_together=None,
                 required_one_of=None, add_file_common_args=False,
                 supports_check_mode=False, required_if=None, required_by=None):

        '''
        Common code for quickly building an ansible module in Python
        (although you can write modules with anything that can return JSON).

        See :ref:`developing_modules_general` for a general introduction
        and :ref:`developing_program_flow_modules` for more detailed explanation.
        '''

        self._name = os.path.basename(__file__)  # initialize name until we can parse from options
        self.argument_spec = argument_spec
        self.supports_check_mode = supports_check_mode
        self.check_mode = False
        self.bypass_checks = bypass_checks
        self.no_log = no_log

        self.mutually_exclusive = mutually_exclusive
        self.required_together = required_together
        self.required_one_of = required_one_of
        self.required_if = required_if
        self.required_by = required_by
        self.cleanup_files = []
        self._debug = False
        self._diff = False
        self._socket_path = None
        self._shell = None
        self._syslog_facility = 'LOG_USER'
        self._verbosity = 0
        # May be used to set modifications to the environment for any
        # run_command invocation
        self.run_command_environ_update = {}
        self._clean = {}
        self._string_conversion_action = ''

        self.aliases = {}
        self._legal_inputs = []
        self._options_context = list()
        self._tmpdir = None

        if add_file_common_args:
            for k, v in FILE_COMMON_ARGUMENTS.items():
                if k not in self.argument_spec:
                    self.argument_spec[k] = v

        # Save parameter values that should never be logged
        self.no_log_values = set()

        # check the locale as set by the current environment, and reset to
        # a known valid (LANG=C) if it's an invalid/unavailable locale
        self._check_locale()

        self._load_params()
        self._set_internal_properties()

        self.validator = ModuleArgumentSpecValidator(self.argument_spec,
                                                     self.mutually_exclusive,
                                                     self.required_together,
                                                     self.required_one_of,
                                                     self.required_if,
                                                     self.required_by,
                                                     )

        self.validation_result = self.validator.validate(self.params)
        self.params.update(self.validation_result.validated_parameters)
        self.no_log_values.update(self.validation_result._no_log_values)

        try:
            error = self.validation_result.errors[0]
        except IndexError:
            error = None

        # Fail for validation errors, even in check mode
        if error:
            msg = self.validation_result.errors.msg
            if isinstance(error, UnsupportedError):
                msg = "Unsupported parameters for ({name}) {kind}: {msg}".format(name=self._name, kind='module', msg=msg)

            self.fail_json(msg=msg)

        if self.check_mode and not self.supports_check_mode:
            self.exit_json(skipped=True, msg="remote module (%s) does not support check mode" % self._name)

        # This is for backwards compatibility only.
        self._CHECK_ARGUMENT_TYPES_DISPATCHER = DEFAULT_TYPE_VALIDATORS

        if not self.no_log:
            self._log_invocation()

        # selinux state caching
        self._selinux_enabled = None
        self._selinux_mls_enabled = None
        self._selinux_initial_context = None

        # finally, make sure we're in a sane working dir
        self._set_cwd()

    @property
    def tmpdir(self):
        # if _ansible_tmpdir was not set and we have a remote_tmp,
        # the module needs to create it and clean it up once finished.
        # otherwise we create our own module tmp dir from the system defaults
        if self._tmpdir is None:
            basedir = None

            if self._remote_tmp is not None:
                basedir = os.path.expanduser(os.path.expandvars(self._remote_tmp))

            if basedir is not None and not os.path.exists(basedir):
                try:
                    os.makedirs(basedir, mode=0o700)
                except (OSError, IOError) as e:
                    self.warn("Unable to use %s as temporary directory, "
                              "failing back to system: %s" % (basedir, to_native(e)))
                    basedir = None
                else:
                    self.warn("Module remote_tmp %s did not exist and was "
                              "created with a mode of 0700, this may cause"
                              " issues when running as another user. To "
                              "avoid this, create the remote_tmp dir with "
                              "the correct permissions manually" % basedir)

            basefile = "ansible-moduletmp-%s-" % time.time()
            try:
                tmpdir = tempfile.mkdtemp(prefix=basefile, dir=basedir)
            except (OSError, IOError) as e:
                self.fail_json(
                    msg="Failed to create remote module tmp path at dir %s "
                        "with prefix %s: %s" % (basedir, basefile, to_native(e))
                )
            if not self._keep_remote_files:
                atexit.register(shutil.rmtree, tmpdir)
            self._tmpdir = tmpdir

        return self._tmpdir

    def warn(self, warning):
        warn(warning)
        self.log('[WARNING] %s' % warning)

    def deprecate(self, msg, version=None, date=None, collection_name=None):
        if version is not None and date is not None:
            raise AssertionError("implementation error -- version and date must not both be set")
        deprecate(msg, version=version, date=date, collection_name=collection_name)
        # For compatibility, we accept that neither version nor date is set,
        # and treat that the same as if version would haven been set
        if date is not None:
            self.log('[DEPRECATION WARNING] %s %s' % (msg, date))
        else:
            self.log('[DEPRECATION WARNING] %s %s' % (msg, version))

    def load_file_common_arguments(self, params, path=None):
        '''
        many modules deal with files, this encapsulates common
        options that the file module accepts such that it is directly
        available to all modules and they can share code.

        Allows to overwrite the path/dest module argument by providing path.
        '''

        if path is None:
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
        if self._selinux_mls_enabled is None:
            self._selinux_mls_enabled = HAVE_SELINUX and selinux.is_selinux_mls_enabled() == 1

        return self._selinux_mls_enabled

    def selinux_enabled(self):
        if self._selinux_enabled is None:
            self._selinux_enabled = HAVE_SELINUX and selinux.is_selinux_enabled() == 1

        return self._selinux_enabled

    # Determine whether we need a placeholder for selevel/mls
    def selinux_initial_context(self):
        if self._selinux_initial_context is None:
            self._selinux_initial_context = [None, None, None]
            if self.selinux_mls_enabled():
                self._selinux_initial_context.append(None)

        return self._selinux_initial_context

    # If selinux fails to find a default, return an array of None
    def selinux_default_context(self, path, mode=0):
        context = self.selinux_initial_context()
        if not self.selinux_enabled():
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
        if not self.selinux_enabled():
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
        '''
            Takes a path and returns it's mount point

        :param path: a string type with a filesystem path
        :returns: the path to the mount point as a text type
        '''

        b_path = os.path.realpath(to_bytes(os.path.expanduser(os.path.expandvars(path)), errors='surrogate_or_strict'))
        while not os.path.ismount(b_path):
            b_path = os.path.dirname(b_path)

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
        except Exception:
            return (False, None)

        path_mount_point = self.find_mount_point(path)

        for line in mount_data:
            (device, mount_point, fstype, options, rest) = line.split(' ', 4)
            if to_bytes(path_mount_point) == to_bytes(mount_point):
                for fs in self._selinux_special_fs:
                    if fs in fstype:
                        special_context = self.selinux_context(path_mount_point)
                        return (True, special_context)

        return (False, None)

    def set_default_selinux_context(self, path, changed):
        if not self.selinux_enabled():
            return changed
        context = self.selinux_default_context(path)
        return self.set_context_if_different(path, context, False)

    def set_context_if_different(self, path, context, changed, diff=None):

        if not self.selinux_enabled():
            return changed

        if self.check_file_absent_if_check_mode(path):
            return True

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

        if owner is None:
            return changed

        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))

        if self.check_file_absent_if_check_mode(b_path):
            return True

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

        if group is None:
            return changed

        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))

        if self.check_file_absent_if_check_mode(b_path):
            return True

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

        if mode is None:
            return changed

        b_path = to_bytes(path, errors='surrogate_or_strict')
        if expand:
            b_path = os.path.expanduser(os.path.expandvars(b_path))

        if self.check_file_absent_if_check_mode(b_path):
            return True

        path_stat = os.lstat(b_path)

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
                if os.path.islink(b_path) and e.errno in (
                    errno.EACCES,  # can't access symlink in sticky directory (stat)
                    errno.EPERM,  # can't set mode on symbolic links (chmod)
                    errno.EROFS,  # can't set mode on read-only filesystem
                ):
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

        if self.check_file_absent_if_check_mode(b_path):
            return True

        existing = self.get_file_attributes(b_path, include_version=False)

        attr_mod = '='
        if attributes.startswith(('-', '+')):
            attr_mod = attributes[0]
            attributes = attributes[1:]

        if existing.get('attr_flags', '') != attributes or attr_mod == '-':
            attrcmd = self.get_bin_path('chattr')
            if attrcmd:
                attrcmd = [attrcmd, '%s%s' % (attr_mod, attributes), b_path]
                changed = True

                if diff is not None:
                    if 'before' not in diff:
                        diff['before'] = {}
                    diff['before']['attributes'] = existing.get('attr_flags')
                    if 'after' not in diff:
                        diff['after'] = {}
                    diff['after']['attributes'] = '%s%s' % (attr_mod, attributes)

                if not self.check_mode:
                    try:
                        rc, out, err = self.run_command(attrcmd)
                        if rc != 0 or err:
                            raise Exception("Error while setting attributes: %s" % (out + err))
                    except Exception as e:
                        self.fail_json(path=to_text(b_path), msg='chattr failed',
                                       details=to_native(e), exception=traceback.format_exc())
        return changed

    def get_file_attributes(self, path, include_version=True):
        output = {}
        attrcmd = self.get_bin_path('lsattr', False)
        if attrcmd:
            flags = '-vd' if include_version else '-d'
            attrcmd = [attrcmd, flags, path]
            try:
                rc, out, err = self.run_command(attrcmd)
                if rc == 0:
                    res = out.split()
                    attr_flags_idx = 0
                    if include_version:
                        attr_flags_idx = 1
                        output['version'] = res[0].strip()
                    output['attr_flags'] = res[attr_flags_idx].replace('-', '').strip()
                    output['attributes'] = format_attributes(output['attr_flags'])
            except Exception:
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

    def check_file_absent_if_check_mode(self, file_path):
        return self.check_mode and not os.path.exists(file_path)

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
            if self.selinux_enabled():
                kwargs['secontext'] = ':'.join(self.selinux_context(path))
            kwargs['size'] = st[stat.ST_SIZE]
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

    def _set_internal_properties(self, argument_spec=None, module_parameters=None):
        if argument_spec is None:
            argument_spec = self.argument_spec
        if module_parameters is None:
            module_parameters = self.params

        for k in PASS_VARS:
            # handle setting internal properties from internal ansible vars
            param_key = '_ansible_%s' % k
            if param_key in module_parameters:
                if k in PASS_BOOLS:
                    setattr(self, PASS_VARS[k][0], self.boolean(module_parameters[param_key]))
                else:
                    setattr(self, PASS_VARS[k][0], module_parameters[param_key])

                # clean up internal top level params:
                if param_key in self.params:
                    del self.params[param_key]
            else:
                # use defaults if not already set
                if not hasattr(self, PASS_VARS[k][0]):
                    setattr(self, PASS_VARS[k][0], PASS_VARS[k][1])

    def safe_eval(self, value, locals=None, include_exceptions=False):
        return safe_eval(value, locals, include_exceptions)

    def _load_params(self):
        ''' read the input and set the params attribute.

        This method is for backwards compatibility.  The guts of the function
        were moved out in 2.1 so that custom modules could read the parameters.
        '''
        # debug overrides to read args from file or cmdline
        self.params = _load_params()

    def _log_to_syslog(self, msg):
        if HAS_SYSLOG:
            try:
                module = 'ansible-%s' % self._name
                facility = getattr(syslog, self._syslog_facility, syslog.LOG_USER)
                syslog.openlog(str(module), 0, facility)
                syslog.syslog(syslog.LOG_INFO, msg)
            except TypeError as e:
                self.fail_json(
                    msg='Failed to log to syslog (%s). To proceed anyway, '
                        'disable syslog logging by setting no_target_syslog '
                        'to True in your Ansible config.' % to_native(e),
                    exception=traceback.format_exc(),
                    msg_to_log=msg,
                )

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
                    if HAS_SYSLOG:
                        # If syslog_facility specified, it needs to convert
                        #  from the facility name to the facility code, and
                        #  set it as SYSLOG_FACILITY argument of journal.send()
                        facility = getattr(syslog,
                                           self._syslog_facility,
                                           syslog.LOG_USER) >> 3
                        journal.send(MESSAGE=u"%s %s" % (module, journal_msg),
                                     SYSLOG_FACILITY=facility,
                                     **dict(journal_args))
                    else:
                        journal.send(MESSAGE=u"%s %s" % (module, journal_msg),
                                     **dict(journal_args))
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
            no_log = arg_opts.get('no_log', None)

            # try to proactively capture password/passphrase fields
            if no_log is None and PASSWORD_MATCH.search(param):
                log_args[param] = 'NOT_LOGGING_PASSWORD'
                self.warn('Module did not set no_log for %s' % param)
            elif self.boolean(no_log):
                log_args[param] = 'NOT_LOGGING_PARAMETER'
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
        except Exception:
            # we don't have access to the cwd, probably because of sudo.
            # Try and move to a neutral location to prevent errors
            for cwd in [self.tmpdir, os.path.expandvars('$HOME'), tempfile.gettempdir()]:
                try:
                    if os.access(cwd, os.F_OK | os.R_OK):
                        os.chdir(cwd)
                        return cwd
                except Exception:
                    pass
        # we won't error here, as it may *not* be a problem,
        # and we don't want to break modules unnecessarily
        return None

    def get_bin_path(self, arg, required=False, opt_dirs=None):
        '''
        Find system executable in PATH.

        :param arg: The executable to find.
        :param required: if executable is not found and required is ``True``, fail_json
        :param opt_dirs: optional list of directories to search in addition to ``PATH``
        :returns: if found return full path; otherwise return None
        '''

        bin_path = None
        try:
            bin_path = get_bin_path(arg=arg, opt_dirs=opt_dirs)
        except ValueError as e:
            if required:
                self.fail_json(msg=to_text(e))
            else:
                return bin_path

        return bin_path

    def boolean(self, arg):
        '''Convert the argument to a boolean'''
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

        warnings = get_warning_messages()
        if warnings:
            kwargs['warnings'] = warnings

        if 'deprecations' in kwargs:
            if isinstance(kwargs['deprecations'], list):
                for d in kwargs['deprecations']:
                    if isinstance(d, SEQUENCETYPE) and len(d) == 2:
                        self.deprecate(d[0], version=d[1])
                    elif isinstance(d, Mapping):
                        self.deprecate(d['msg'], version=d.get('version'), date=d.get('date'),
                                       collection_name=d.get('collection_name'))
                    else:
                        self.deprecate(d)  # pylint: disable=ansible-deprecated-no-version
            else:
                self.deprecate(kwargs['deprecations'])  # pylint: disable=ansible-deprecated-no-version

        deprecations = get_deprecation_messages()
        if deprecations:
            kwargs['deprecations'] = deprecations

        kwargs = remove_values(kwargs, self.no_log_values)
        print('\n%s' % self.jsonify(kwargs))

    def exit_json(self, **kwargs):
        ''' return from the module, without error '''

        self.do_cleanup_files()
        self._return_formatted(kwargs)
        sys.exit(0)

    def fail_json(self, msg, **kwargs):
        ''' return from the module, with an error message '''

        kwargs['failed'] = True
        kwargs['msg'] = msg

        # Add traceback if debug or high verbosity and it is missing
        # NOTE: Badly named as exception, it really always has been a traceback
        if 'exception' not in kwargs and sys.exc_info()[2] and (self._debug or self._verbosity >= 3):
            if PY2:
                # On Python 2 this is the last (stack frame) exception and as such may be unrelated to the failure
                kwargs['exception'] = 'WARNING: The below traceback may *not* be related to the actual failure.\n' +\
                                      ''.join(traceback.format_tb(sys.exc_info()[2]))
            else:
                kwargs['exception'] = ''.join(traceback.format_tb(sys.exc_info()[2]))

        self.do_cleanup_files()
        self._return_formatted(kwargs)
        sys.exit(1)

    def fail_on_missing_params(self, required_params=None):
        if not required_params:
            return
        try:
            check_missing_parameters(self.params, required_params)
        except TypeError as e:
            self.fail_json(msg=to_native(e))

    def digest_from_file(self, filename, algorithm):
        ''' Return hex digest of local file for a digest_method specified by name, or None if file is not present. '''
        b_filename = to_bytes(filename, errors='surrogate_or_strict')

        if not os.path.exists(b_filename):
            return None
        if os.path.isdir(b_filename):
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
        infile = open(os.path.realpath(b_filename), 'rb')
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
        current_attribs = self.get_file_attributes(src, include_version=False)
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
                self.fail_json(msg='Could not replace file: %s to %s: %s' % (src, dest, to_native(e)), exception=traceback.format_exc())
            else:
                # Use bytes here.  In the shippable CI, this fails with
                # a UnicodeError with surrogateescape'd strings for an unknown
                # reason (doesn't happen in a local Ubuntu16.04 VM)
                b_dest_dir = os.path.dirname(b_dest)
                b_suffix = os.path.basename(b_dest)
                error_msg = None
                tmp_dest_name = None
                try:
                    tmp_dest_fd, tmp_dest_name = tempfile.mkstemp(prefix=b'.ansible_tmp', dir=b_dest_dir, suffix=b_suffix)
                except (OSError, IOError) as e:
                    error_msg = 'The destination directory (%s) is not writable by the current user. Error was: %s' % (os.path.dirname(dest), to_native(e))
                except TypeError:
                    # We expect that this is happening because python3.4.x and
                    # below can't handle byte strings in mkstemp().
                    # Traceback would end in something like:
                    #     file = _os.path.join(dir, pre + name + suf)
                    # TypeError: can't concat bytes to str
                    error_msg = ('Failed creating tmp file for atomic move.  This usually happens when using Python3 less than Python3.5. '
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
                                # cleanup will happen by 'rm' of tmpdir
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
                                    self.fail_json(msg='Unable to make %s into to %s, failed final rename from %s: %s' %
                                                       (src, dest, b_tmp_dest_name, to_native(e)), exception=traceback.format_exc())
                        except (shutil.Error, OSError, IOError) as e:
                            if unsafe_writes:
                                self._unsafe_writes(b_src, b_dest)
                            else:
                                self.fail_json(msg='Failed to replace file: %s to %s: %s' % (src, dest, to_native(e)), exception=traceback.format_exc())
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

    def _restore_signal_handlers(self):
        # Reset SIGPIPE to SIG_DFL, otherwise in Python2.7 it gets ignored in subprocesses.
        if PY2 and sys.platform != 'win32':
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    def run_command(self, args, check_rc=False, close_fds=True, executable=None, data=None, binary_data=False, path_prefix=None, cwd=None,
                    use_unsafe_shell=False, prompt_regex=None, environ_update=None, umask=None, encoding='utf-8', errors='surrogate_or_strict',
                    expand_user_and_vars=True, pass_fds=None, before_communicate_callback=None, ignore_invalid_cwd=True):
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
            This adds to the PATH environment variable so helper commands in
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
        :kw expand_user_and_vars: When ``use_unsafe_shell=False`` this argument
            dictates whether ``~`` is expanded in paths and environment variables
            are expanded before running the command. When ``True`` a string such as
            ``$SHELL`` will be expanded regardless of escaping. When ``False`` and
            ``use_unsafe_shell=False`` no path or variable expansion will be done.
        :kw pass_fds: When running on Python 3 this argument
            dictates which file descriptors should be passed
            to an underlying ``Popen`` constructor. On Python 2, this will
            set ``close_fds`` to False.
        :kw before_communicate_callback: This function will be called
            after ``Popen`` object will be created
            but before communicating to the process.
            (``Popen`` object will be passed to callback as a first argument)
        :kw ignore_invalid_cwd: This flag indicates whether an invalid ``cwd``
            (non-existent or not a directory) should be ignored or should raise
            an exception.
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
                args = b" ".join([to_bytes(shlex_quote(x), errors='surrogate_or_strict') for x in args])
            else:
                args = to_bytes(args, errors='surrogate_or_strict')

            # not set explicitly, check if set by controller
            if executable:
                executable = to_bytes(executable, errors='surrogate_or_strict')
                args = [executable, b'-c', args]
            elif self._shell not in (None, '/bin/sh'):
                args = [to_bytes(self._shell, errors='surrogate_or_strict'), b'-c', args]
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

            # expand ``~`` in paths, and all environment vars
            if expand_user_and_vars:
                args = [to_bytes(os.path.expanduser(os.path.expandvars(x)), errors='surrogate_or_strict') for x in args if x is not None]
            else:
                args = [to_bytes(x, errors='surrogate_or_strict') for x in args if x is not None]

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
            path = os.environ.get('PATH', '')
            old_env_vals['PATH'] = path
            if path:
                os.environ['PATH'] = "%s:%s" % (path_prefix, path)
            else:
                os.environ['PATH'] = path_prefix

        # If using test-module.py and explode, the remote lib path will resemble:
        #   /tmp/test_module_scratch/debug_dir/ansible/module_utils/basic.py
        # If using ansible or ansible-playbook with a remote system:
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
            preexec_fn=self._restore_signal_handlers,
        )
        if PY3 and pass_fds:
            kwargs["pass_fds"] = pass_fds
        elif PY2 and pass_fds:
            kwargs['close_fds'] = False

        # store the pwd
        prev_dir = os.getcwd()

        # make sure we're in the right working directory
        if cwd:
            if os.path.isdir(cwd):
                cwd = to_bytes(os.path.abspath(os.path.expanduser(cwd)), errors='surrogate_or_strict')
                kwargs['cwd'] = cwd
                try:
                    os.chdir(cwd)
                except (OSError, IOError) as e:
                    self.fail_json(rc=e.errno, msg="Could not chdir to %s, %s" % (cwd, to_native(e)),
                                   exception=traceback.format_exc())
            elif not ignore_invalid_cwd:
                self.fail_json(msg="Provided cwd is not a valid directory: %s" % cwd)

        old_umask = None
        if umask:
            old_umask = os.umask(umask)

        try:
            if self._debug:
                self.log('Executing: ' + self._clean_args(args))
            cmd = subprocess.Popen(args, **kwargs)
            if before_communicate_callback:
                before_communicate_callback(cmd)

            # the communication logic here is essentially taken from that
            # of the _communicate() function in ssh.py

            stdout = b''
            stderr = b''
            try:
                selector = selectors.DefaultSelector()
            except (IOError, OSError):
                # Failed to detect default selector for the given platform
                # Select PollSelector which is supported by major platforms
                selector = selectors.PollSelector()

            selector.register(cmd.stdout, selectors.EVENT_READ)
            selector.register(cmd.stderr, selectors.EVENT_READ)
            if os.name == 'posix':
                fcntl.fcntl(cmd.stdout.fileno(), fcntl.F_SETFL, fcntl.fcntl(cmd.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)
                fcntl.fcntl(cmd.stderr.fileno(), fcntl.F_SETFL, fcntl.fcntl(cmd.stderr.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)

            if data:
                if not binary_data:
                    data += '\n'
                if isinstance(data, text_type):
                    data = to_bytes(data)
                cmd.stdin.write(data)
                cmd.stdin.close()

            while True:
                events = selector.select(1)
                for key, event in events:
                    b_chunk = key.fileobj.read()
                    if b_chunk == b(''):
                        selector.unregister(key.fileobj)
                    if key.fileobj == cmd.stdout:
                        stdout += b_chunk
                    elif key.fileobj == cmd.stderr:
                        stderr += b_chunk
                # if we're checking for prompts, do it now
                if prompt_re:
                    if prompt_re.search(stdout) and not data:
                        if encoding:
                            stdout = to_native(stdout, encoding=encoding, errors=errors)
                        return (257, stdout, "A prompt was encountered while running a command, but no input data was specified")
                # only break out if no pipes are left to read or
                # the pipes are completely read and
                # the process is terminated
                if (not events or not selector.get_map()) and cmd.poll() is not None:
                    break
                # No pipes are left to read but process is not yet terminated
                # Only then it is safe to wait for the process to be finished
                # NOTE: Actually cmd.poll() is always None here if no selectors are left
                elif not selector.get_map() and cmd.poll() is None:
                    cmd.wait()
                    # The process is terminated. Since no pipes to read from are
                    # left, there is no need to call select() again.
                    break

            cmd.stdout.close()
            cmd.stderr.close()
            selector.close()

            rc = cmd.returncode
        except (OSError, IOError) as e:
            self.log("Error Executing CMD:%s Exception:%s" % (self._clean_args(args), to_native(e)))
            self.fail_json(rc=e.errno, stdout=b'', stderr=b'', msg=to_native(e), cmd=self._clean_args(args))
        except Exception as e:
            self.log("Error Executing CMD:%s Exception:%s" % (self._clean_args(args), to_native(traceback.format_exc())))
            self.fail_json(rc=257, stdout=b'', stderr=b'', msg=to_native(e), exception=traceback.format_exc(), cmd=self._clean_args(args))

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

    @staticmethod
    def get_buffer_size(fd):
        try:
            # 1032 == FZ_GETPIPE_SZ
            buffer_size = fcntl.fcntl(fd, 1032)
        except Exception:
            try:
                # not as exact as above, but should be good enough for most platforms that fail the previous call
                buffer_size = select.PIPE_BUF
            except Exception:
                buffer_size = 9000  # use sane default JIC

        return buffer_size


def get_module_path():
    return os.path.dirname(os.path.realpath(__file__))
