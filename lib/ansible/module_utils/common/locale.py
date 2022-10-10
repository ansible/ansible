# Copyright (c), Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils._text import to_native


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
            # new POSIX standard or English cause those are messages core team expects
            # yes, the last 2 are the same but some systems are weird
            preferences = ['C.utf8', 'C.UTF-8', 'en_US.utf8', 'en_US.UTF-8', 'C', 'POSIX']

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

    except RuntimeWarning as e:
        if raise_on_locale:
            raise
        else:
            module.debug('Failed to get locale information: %s' % to_native(e))

    module.debug('Matched preferred locale to: %s' % found)

    return found
