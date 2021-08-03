# Copyright (c), Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os

from ansible.module_utils._text import to_native

# new POSIX standard or English cause those are messages core team expects
# yes, the last 2 are the same but some systems are weird
PARSABLE_LOCALES = ['C.utf8', 'en_US.utf8', 'C', 'POSIX']

# not only ones, but by default the ones most programs should use,
#  many violate the standard though, so callers should send their own list then
LOCALE_VARS = ['LC_ALL', 'LANG']


def get_best_parsable_locale(module, preferences=None, raise_on_locale=False):
    '''
        Attempts to return the best possible locale for parsing output in English
        useful for scraping output with i18n tools. When this raises an exception
        and the caller wants to continue, it should use the 'C' locale.

        :param module: an AnsibleModule instance
        :param preferences: A list of preferred locales, in order of preference
        :param raise_on_locale: boolean that determines if we raise exception or not
                                due to locale CLI issues
        :returns: The first matched preferred locale or 'C' which is the default
    '''

    found = 'C'  # default posix, its ascii but always there
    try:
        locale = module.get_bin_path("locale")
        if not locale:
            # not using required=true as that forces fail_json
            raise RuntimeWarning("Could not find 'locale' tool")

        available = []

        if preferences is None:
            preferences = PARSABLE_LOCALES

        rc, out, err = module.run_command([locale, '-a'])

        if rc == 0:
            if out:
                available = out.strip().splitlines()
            else:
                raise RuntimeWarning("No output from locale, rc=%s: %s" % (rc, to_native(err)))
        else:
            raise RuntimeWarning("Unable to get locale information, rc=%s: %s" % (rc, to_native(err)))

        if available:
            for pref in preferences:
                if pref in available:
                    found = pref
                    break

    except RuntimeWarning:
        if raise_on_locale:
            raise

    return found


def get_parsable_locale_envvars(module, envvars=None, preferences=None):
    '''
        Optimially set locale vars to best or any of the parsable locales if not already.

        :param module: an AnsibleModule instance
        :param preferences: A list of preferred locales, in order of preference

        :returns: 2 dicts, one with env vars and new values, another with env vars and existing values.
    '''

    def _get_best():
        ''' cache best locale '''
        if not hasattr(_get_best, 'best'):
            _get_best.best = get_best_parsable_locale(module, preferences)
        return _get_best.best

    if envvars is None:
        envvars = LOCALE_VARS

    if preferences is None:
        preferences = PARSABLE_LOCALES

    newvars = {}
    oldvars = {}
    for envvar in envvars:

        if not (envvar.startswith('LC_') or envvar == 'LANG'):
            raise RuntimeWarning("'%s' is not a valid locale related environment variable!" % (envvar))

        if os.environ.get(envvar) in preferences:
            continue

        oldvars[envvar] = os.environ.get(envvar)
        newvars[envvar] = _get_best()

    return newvars, oldvars
