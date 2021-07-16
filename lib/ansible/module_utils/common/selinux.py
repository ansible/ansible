# Copyright (c), Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import errno

try:
    import ansible.module_utils.compat.selinux as selinux
    HAS_SELINUX = True
except ImportError:
    HAS_SELINUX = False

from ansible.module_utils._text import to_native


def do_we_have_selinux():
    return HAS_SELINUX


def is_selinux_enabled():
    ''' determine if we have enabled selinux '''
    if not hasattr(is_selinux_enabled, 'is_enabled'):
        if do_we_have_selinux():
            is_selinux_enabled.is_enabled = (selinux.is_selinux_enabled() == 1)
        else:
            is_selinux_enabled.is_enabled = False

    return is_selinux_enabled.is_enabled


def is_selinux_mls_enabled():
    if not hasattr(is_selinux_mls_enabled, 'is_enabled'):
        if do_we_have_selinux():
            is_selinux_mls_enabled.is_enabled = (selinux.is_selinux_mls_enabled() == 1)
        else:
            is_selinux_mls_enabled.is_enabled = False

    return is_selinux_mls_enabled.is_enabled


def get_selinux_initial_context():
    if not hasattr(get_selinux_initial_context, 'context'):
        get_selinux_initial_context.context = [None, None, None]
        if is_selinux_mls_enabled():
            get_selinux_initial_context.context.append(None)

    return get_selinux_initial_context.context


def get_selinux_default_context(path, mode=0):

    context = get_selinux_initial_context()
    if is_selinux_enabled():
        try:
            ret = selinux.matchpathcon(to_native(path, errors='surrogate_or_strict'), mode)

            if ret[0] != -1:  # only split if valid return
                # Limit split to 4 because the selevel, the last in the list,
                # may contain ':' characters
                context = ret[1].split(':', 3)
        except OSError:
            pass  # no context retrievable, keeps initial

    return context


def get_selinux_context(path):

    context = get_selinux_initial_context()
    if is_selinux_enabled():
        try:
            ret = selinux.lgetfilecon_raw(to_native(path, errors='surrogate_or_strict'))
            if ret[0] != -1:
                # see get_selinux_default_context note
                context = ret[1].split(':', 3)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise OSError('path %s does not exist' % path)
            raise OSError('failed to retrieve selinux context')

    return context
