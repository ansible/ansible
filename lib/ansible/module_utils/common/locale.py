# Copyright (c), Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils._text import to_native


def get_best_parsable_locale(module, preferences=None):
    '''
        Attempts to return the best possible locale for parsing output in English
        useful for scraping output with i18n tools

        :param module: an AnsibleModule instance
        :param preferences: A list of preferred locales, in order of preference
        :returns: The first matched preferred locale or 'C' which is the default
    '''

    found = 'C'  # default posix, its ascii but always there
    if preferences is None:
        # new POSIX standard or English cause those are messages core team expects
        # yes, the last 2 are the same but some systems are weird
        preferences = ['C.utf8', 'en_US.utf8', 'C', 'POSIX']

    rc, out, err = module.run_command(['locale', '-a'])
    if rc == 0:
        if out:
            available = out.strip().splitlines()
        else:
            module.warn("No output from locale, defaulting to C, rc=%s: %s" % (rc, to_native(err)))
    else:
        module.warn("Unable to get locale information, defaulting to C, rc=%s: %s" % (rc, to_native(err)))

    if available:
        for pref in preferences:
            if pref in available:
                found = pref
                break

    return found
